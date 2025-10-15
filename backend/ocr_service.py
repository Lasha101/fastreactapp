# backend/ocr_service.py - FIXED PROTOBUF ISSUE

import re
import os
import json
from datetime import datetime, timezone
from google.cloud import vision, storage
from google.api_core import exceptions
from fastapi import HTTPException
import logging
from typing import Tuple, Optional, Dict

# Use a specific logger for this module
logger = logging.getLogger("ocr_service")
logger.setLevel(logging.INFO)

# --- Google Cloud Clients ---
vision_client = None
storage_client = None
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

try:
    logger.info("--- [GCP] Initializing Google Cloud clients... ---")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.error("🔴 [GCP] CRITICAL: GOOGLE_APPLICATION_CREDENTIALS environment variable is NOT SET.")
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable must be set.")
    
    vision_client = vision.ImageAnnotatorClient()
    storage_client = storage.Client()
    logger.info("✅ [GCP] Google Cloud clients initialized successfully.")
    
    if not GCS_BUCKET_NAME:
        logger.warning("🟡 [GCP] WARNING: GCS_BUCKET_NAME environment variable is not set.")
    else:
        logger.info(f"✅ [GCP] Using GCS Bucket: {GCS_BUCKET_NAME}")

except Exception as e:
    logger.error(f"🔴 [GCP] FAILED to initialize Google Cloud clients: {e}")
    # The application can still run, but OCR features will fail.

def _upload_to_gcs(file_path: str, destination_blob_name: str) -> str:
    """Uploads a file to the GCS bucket."""
    logger.info(f"--- [GCS] Attempting to upload '{os.path.basename(file_path)}' to gs://{GCS_BUCKET_NAME}/{destination_blob_name} ---")
    if not GCS_BUCKET_NAME or not storage_client:
        logger.error("🔴 [GCS] Upload failed: GCS_BUCKET_NAME is not set or storage client is not initialized.")
        raise ValueError("GCS bucket or storage client not configured.")
    
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        logger.info(f"✅ [GCS] Successfully uploaded file. URI: {gcs_uri}")
        return gcs_uri
    except exceptions.NotFound:
        logger.error(f"🔴 [GCS] Upload failed: Bucket '{GCS_BUCKET_NAME}' not found.")
        raise
    except Exception as e:
        logger.error(f"🔴 [GCS] An unexpected error occurred during upload: {e}")
        raise

def _delete_from_gcs(gcs_uri: str):
    """Deletes a file from the GCS bucket."""
    logger.info(f"--- [GCS] Attempting to delete blob: {gcs_uri} ---")
    if not GCS_BUCKET_NAME or not storage_client:
        logger.error("🔴 [GCS] Delete failed: GCS not configured.")
        return
    if not gcs_uri.startswith(f"gs://{GCS_BUCKET_NAME}/"):
        logger.error(f"🔴 [GCS] Cannot delete blob: URI '{gcs_uri}' is not in the configured bucket.")
        return
        
    try:
        blob_name = gcs_uri.replace(f"gs://{GCS_BUCKET_NAME}/", "")
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"✅ [GCS] Successfully deleted blob: {gcs_uri}")
    except Exception as e:
        logger.error(f"🔴 [GCS] Failed to delete blob {gcs_uri}: {e}")

def start_async_ocr_extraction(file_path: str, content_type: str) -> Tuple[str, str]:
    logger.info(f"--- [Vision] Starting async OCR extraction for '{os.path.basename(file_path)}' ---")
    if not vision_client:
        logger.error("🔴 [Vision] Cannot start OCR: Google Vision client is not initialized.")
        raise RuntimeError("Google Vision client is not initialized.")
        
    if not content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only multi-page PDF files are supported for batch processing.")

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    unique_filename = f"uploads/{timestamp}-{os.path.basename(file_path)}"

    # 1. Upload to GCS
    gcs_source_uri = _upload_to_gcs(file_path, unique_filename)

    # 2. Configure and start OCR request
    gcs_destination_uri = f"gs://{GCS_BUCKET_NAME}/results/{unique_filename}-"
    logger.info(f"[Vision] Setting OCR output destination to: {gcs_destination_uri}")
    
    mime_type = 'application/pdf'
    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)
    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(gcs_destination=gcs_destination, batch_size=5)

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature],
        input_config=input_config,
        output_config=output_config
    )

    logger.info("[Vision] Sending async_batch_annotate_files request to Google...")
    operation = vision_client.async_batch_annotate_files(requests=[async_request])
    logger.info(f"✅ [Vision] Started Google Vision async operation. Name: {operation.operation.name}")
    return operation.operation.name, gcs_source_uri

def get_async_ocr_results(operation_name: str) -> dict:
    if not vision_client or not storage_client:
        raise RuntimeError("Google Cloud clients are not initialized.")
        
    logger.info(f"--- [Vision] Checking operation status for: {operation_name} ---")
    operation_client = vision_client.transport.operations_client
    operation = operation_client.get_operation(name=operation_name)

    if not operation.done:
        logger.info("[Vision] Operation is still processing...")
        return {"status": "PROCESSING"}

    if operation.error.message:
        logger.error(f"🔴 [Vision] Operation failed: {operation.error.message}")
        return {"status": "FAILURE", "error": operation.error.message}

    logger.info("✅ [Vision] Operation complete. Processing results from GCS...")
    
    response = operation.metadata
    
    gcs_destination_uri = None
    
    try:
        if hasattr(operation, 'metadata'):
            metadata = operation.metadata
            if hasattr(metadata, 'output_config'):
                gcs_destination_uri = metadata.output_config.gcs_destination.uri
    except Exception as e:
        logger.warning(f"Could not extract destination from metadata: {e}")
    
    # --- CHANGE START ---
    # This block is updated to correctly find the prefix for ALL result files.
    if not gcs_destination_uri:
        logger.info("Using fallback method to determine GCS destination")
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        prefix_to_search = "results/uploads/"
        blobs = list(bucket.list_blobs(prefix=prefix_to_search))
        if not blobs:
            logger.error("No result blobs found in GCS")
            return {"status": "FAILURE", "error": "No OCR results found in storage"}
        
        blobs.sort(key=lambda x: x.time_created, reverse=True)
        most_recent_blob = blobs[0]
        blob_name = most_recent_blob.name
        
        # This new logic reliably finds the correct common prefix for all result files
        # by splitting on the 'output-' part of the filename.
        if 'output-' in blob_name:
            prefix = blob_name.rsplit('output-', 1)[0]
        else:
            # This is a safety net in case a result file doesn't match the expected pattern.
            logger.warning(f"Could not determine a common prefix from blob name: {blob_name}")
            prefix = blob_name
    else:
        prefix = gcs_destination_uri.replace(f"gs://{GCS_BUCKET_NAME}/", "")
    
    logger.info(f"[GCS] Listing result blobs with prefix: '{prefix}'")
    # --- CHANGE END ---
    
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob_list = list(bucket.list_blobs(prefix=prefix))
    logger.info(f"[GCS] Found {len(blob_list)} result blob(s) for this document.")

    results = []
    for blob in blob_list:
        logger.info(f"[GCS] Downloading and parsing result blob: {blob.name}")
        json_string = blob.download_as_string()
        response_json = json.loads(json_string)
        
        for page_response in response_json.get('responses', []):
            page_context = page_response.get('context', {})
            actual_page_num = page_context.get('page_number', 'N/A')
            try:
                if page_response.get('error'):
                    raise ValueError(page_response['error']['message'])
                
                full_text = page_response.get('fullTextAnnotation', {}).get('text', '')
                if not full_text:
                    raise ValueError("No text detected on page.")

                parsed_data = _parse_passport_text(full_text)
                
                total_confidence, symbol_count = 0, 0
                for page in page_response.get('fullTextAnnotation', {}).get('pages', []):
                    for block in page.get('blocks', []):
                        for paragraph in block.get('paragraphs', []):
                            for word in paragraph.get('words', []):
                                for symbol in word.get('symbols', []):
                                    total_confidence += symbol.get('confidence', 0)
                                    symbol_count += 1
                
                average_confidence = (total_confidence / symbol_count) if symbol_count > 0 else 0.0
                parsed_data['confidence_score'] = round(average_confidence, 4)
                logger.info(f"✅ Parsed page {actual_page_num} successfully. Confidence: {average_confidence:.2%}")
                results.append({"page_number": actual_page_num, "data": parsed_data, "status": "SUCCESS"})
            except Exception as e:
                logger.warning(f"🟡 Failed to parse page {actual_page_num}: {e}")
                results.append({"page_number": actual_page_num, "error": str(e), "status": "FAILURE"})
    
    logger.info(f"--- [GCS] Cleaning up {len(blob_list)} result blobs... ---")
    for blob in blob_list:
        blob.delete()
        
    return {"status": "SUCCESS", "results": results}

def cancel_google_ocr_operation(operation_name: str):
    try:
        if not vision_client:
            logger.error("🔴 [Vision] Vision client not initialized, cannot cancel operation.")
            return
        logger.info(f"--- [Vision] Requesting cancellation for operation: {operation_name} ---")
        vision_client.transport.operations_client.cancel_operation(name=operation_name)
        logger.info(f"✅ [Vision] Cancellation request sent for {operation_name}.")
    except Exception as e:
        logger.error(f"🔴 [Vision] Failed to send cancellation request for {operation_name}: {e}")

def _parse_date_from_mrz(date_str: str) -> Optional[str]:
    """Parses a YYMMDD date string from MRZ and returns YYYY-MM-DD."""
    if not date_str or len(date_str) != 6:
        return None
    try:
        year = int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])

        current_year_short = datetime.now().year % 100
        # Add a 10 year buffer for expiry dates in the future
        if year > current_year_short + 10:
            year += 1900
        else:
            year += 2000

        return datetime(year, month, day).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        logger.warning(f"Could not parse MRZ date string: {date_str}")
        return None

def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Helper to parse and format date string."""
    if not date_str:
        return None
    try:
        cleaned_date_str = date_str.replace('.', '/').replace(' ', '/')
        dt_obj = datetime.strptime(cleaned_date_str, '%d/%m/%Y')
        return dt_obj.strftime('%Y-%m-%d')
    except ValueError:
        logger.warning(f"Could not parse date string: {date_str}")
        return None

def _parse_passport_text(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Parses raw OCR text from a passport to extract structured data.
    It prioritizes parsing the Machine-Readable Zone (MRZ) for accuracy.
    This version includes improved MRZ line detection and more robust fallbacks.
    """
    data = {
        "first_name": None, "last_name": None, "passport_number": None,
        "birth_date": None, "delivery_date": None, "expiration_date": None,
        "nationality": "FRANCAISE",
    }
    
    raw_text_lines = raw_text.split('\n')
    text_lines = [line.strip() for line in raw_text_lines]
    
    # --- STAGE 1: Attempt to parse the MRZ (most reliable) ---
    mrz_line1_index = -1

    # Find the first MRZ line (starts with P<)
    for i, line in enumerate(text_lines):
        cleaned_line = line.replace(' ', '').replace('«', '<')
        if cleaned_line.startswith('P<') and len(cleaned_line) > 30: # Use a lenient length check
            mrz_line1_index = i
            break
            
    # If the first line is found, the second line should be immediately after it
    if mrz_line1_index != -1 and mrz_line1_index + 1 < len(text_lines):
        logger.info(f"Found potential MRZ Line 1 at index {mrz_line1_index}.")
        line1 = text_lines[mrz_line1_index].replace(' ', '').replace('«', '<')
        line2 = text_lines[mrz_line1_index + 1].replace(' ', '').replace('«', '<')
        
        # Clean up line 2, which may have extra chars from OCR
        line2 = re.sub(r'[^A-Z0-9<]', '', line2)
        
        # Pad lines if they are too short from OCR errors
        line1 = line1.ljust(44, '<')
        line2 = line2.ljust(44, '<')

        # --- Parse Line 2 ---
        passport_number_mrz = line2[0:9].replace('<', '').strip()
        nationality_mrz = line2[10:13].strip()
        birth_date_mrz = _parse_date_from_mrz(line2[13:19])
        expiration_date_mrz = _parse_date_from_mrz(line2[21:27])
        
        if passport_number_mrz: data["passport_number"] = passport_number_mrz
        if nationality_mrz: data["nationality"] = nationality_mrz
        if birth_date_mrz: data["birth_date"] = birth_date_mrz
        if expiration_date_mrz: data["expiration_date"] = expiration_date_mrz
        logger.info(f"MRZ Line 2 Parsed: PN={data['passport_number']}, Nat={data['nationality']}, DoB={data['birth_date']}, Exp={data['expiration_date']}")

        # --- Parse Line 1 ---
        name_part = line1[5:44]
        parts = name_part.split('<<')
        if len(parts) >= 1:
            last_name_mrz = parts[0].replace('<', ' ').strip()
            if last_name_mrz: data["last_name"] = last_name_mrz
        if len(parts) >= 2:
            first_name_mrz = parts[1].replace('<', ' ').strip()
            if first_name_mrz: data["first_name"] = first_name_mrz
        logger.info(f"MRZ Line 1 Parsed: Last={data['last_name']}, First={data['first_name']}")

    # --- STAGE 2: Use regex on the visual part as a fallback or to supplement ---
    if not data["passport_number"]:
        # Fallback for number, supporting both new and old formats
        match = re.search(r'\b([A-Z]{2}\d{7}|\d{2}[A-Z]{2}\d{5})\b', raw_text.replace(" ", ""))
        if match:
            data["passport_number"] = match.group(1)

    # Search for keywords line by line as a more robust fallback
    for idx, line in enumerate(raw_text_lines):
        line_lower = line.lower()
        if not data["last_name"] and ('nom' in line_lower or 'surname' in line_lower):
            value = re.sub(r'(nom|surname|/|\s|:)*', '', line, flags=re.IGNORECASE)
            if len(value) > 1: data["last_name"] = value.strip()
        
        if not data["first_name"] and ('prénom' in line_lower or 'given name' in line_lower):
            value = re.sub(r'(prénom\(s\)|prénom|given name\(s\)|given name|/|\s|:)*', '', line, flags=re.IGNORECASE)
            if len(value) > 1: data["first_name"] = value.strip()
        
        if not data["birth_date"] and ('naissance' in line_lower or 'birth' in line_lower):
            match = re.search(r'(\d{2}[./\s]\d{2}[./\s]\d{4})', line)
            if match: data["birth_date"] = _parse_date(match.group(1))

        if not data["delivery_date"] and ('délivrance' in line_lower or 'issue' in line_lower):
            match = re.search(r'(\d{2}[./\s]\d{2}[./\s]\d{4})', line)
            if match: data["delivery_date"] = _parse_date(match.group(1))

        if not data["expiration_date"] and ('expiration' in line_lower or 'expiry' in line_lower):
            match = re.search(r'(\d{2}[./\s]\d{2}[./\s]\d{4})', line)
            if match: data["expiration_date"] = _parse_date(match.group(1))

    # --- STAGE 3: Final validation ---
    required_fields = ["last_name", "first_name", "birth_date", "passport_number"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        missing_list = ', '.join([field.replace('_', ' ').title() for field in missing_fields])
        logger.warning(f"Missing required fields after parsing: {missing_list}")
        raise ValueError(
            f"Could not extract required fields from document. Missing: {missing_list}. "
            f"This may be due to poor image quality or unsupported document format."
        )
        
    return data