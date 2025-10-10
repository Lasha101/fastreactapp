# backend/ocr_service.py

import re
import os
import json
from datetime import datetime
from google.cloud import vision, storage
from fastapi import HTTPException
import logging
from typing import Tuple, Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Google Cloud Clients ---
# Initialize clients once and reuse them.
# Credentials will be picked up from the GOOGLE_APPLICATION_CREDENTIALS env var.
try:
    vision_client = vision.ImageAnnotatorClient()
    storage_client = storage.Client()
except Exception as e:
    logger.error(f"Could not initialize Google Cloud clients: {e}")
    # You might want to handle this more gracefully
    vision_client = None
    storage_client = None

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

def _upload_to_gcs(file_path: str, destination_blob_name: str) -> str:
    """Uploads a file to the GCS bucket."""
    if not GCS_BUCKET_NAME or not storage_client:
        raise ValueError("GCS_BUCKET_NAME environment variable not set or storage client not initialized.")
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"

def _delete_from_gcs(gcs_uri: str):
    """Deletes a file from the GCS bucket."""
    if not gcs_uri.startswith(f"gs://{GCS_BUCKET_NAME}/"):
        logger.error(f"Cannot delete blob: URI '{gcs_uri}' is not in the configured bucket.")
        return
    try:
        if not storage_client:
            logger.error("Storage client not initialized, cannot delete GCS blob.")
            return
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob_name = gcs_uri.replace(f"gs://{GCS_BUCKET_NAME}/", "")
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Successfully deleted blob: {gcs_uri}")
    except Exception as e:
        logger.error(f"Failed to delete blob {gcs_uri}: {e}")

def start_async_ocr_extraction(file_path: str, content_type: str) -> Tuple[str, str]:
    """
    Starts an asynchronous OCR job for a multi-page document.
    It uploads the file to GCS and triggers the batch annotation.
    """
    if not vision_client:
        raise RuntimeError("Google Vision client is not initialized.")
        
    if not content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only multi-page PDF files are supported for batch processing.")

    # Create a unique name for the file in the GCS bucket
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_filename = f"uploads/{timestamp}-{os.path.basename(file_path)}"

    # 1. Upload the file to GCS
    try:
        gcs_source_uri = _upload_to_gcs(file_path, unique_filename)
        logger.info(f"File uploaded to GCS at: {gcs_source_uri}")
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        raise HTTPException(status_code=500, detail=f"Could not upload file to cloud storage: {e}")

    # 2. Configure and start the async OCR request
    gcs_destination_uri = f"gs://{GCS_BUCKET_NAME}/results/{unique_filename}-"
    mime_type = 'application/pdf'
    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)
    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(gcs_destination=gcs_destination, batch_size=5) # Group results for 5 pages into one JSON

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature],
        input_config=input_config,
        output_config=output_config
    )

    operation = vision_client.async_batch_annotate_files(requests=[async_request])
    logger.info(f"Started Google Vision async operation: {operation.operation.name}")

    # Return both the operation name (to track progress) and the original GCS URI (to delete later)
    return operation.operation.name, gcs_source_uri

def get_async_ocr_results(operation_name: str) -> dict:
    """
    Checks the status of a long-running OCR operation and returns the results if complete.
    """
    if not vision_client or not storage_client:
        raise RuntimeError("Google Cloud clients are not initialized.")
        
    logger.info(f"Checking operation status: {operation_name}")
    # This uses the default operations client from the vision_client
    operation_client = vision_client.transport.operations_client
    operation = operation_client.get_operation(name=operation_name)

    if not operation.done:
        return {"status": "PROCESSING"}

    if operation.error.message:
        logger.error(f"Operation failed: {operation.error.message}")
        return {"status": "FAILURE", "error": operation.error.message}

    # --- If done, process the results from GCS ---
    # The response is embedded in the operation metadata for file annotation
    from google.cloud.vision_v1.types import AsyncBatchAnnotateFilesResponse
    response = AsyncBatchAnnotateFilesResponse.from_json(operation.response.value)
    destination_uri = response.output_config.gcs_destination.uri
    
    prefix = destination_uri.replace(f"gs://{GCS_BUCKET_NAME}/", "")
    
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob_list = list(bucket.list_blobs(prefix=prefix)) # Get all result files

    results = []
    # Loop through all result files generated by Google Vision
    for blob in blob_list:
        json_string = blob.download_as_string()
        response_json = json.loads(json_string)
        
        for page_num_in_blob, page_response in enumerate(response_json['responses']):
            page_context = page_response.get('context', {})
            # Vision API gives page numbers starting from 1
            actual_page_num = page_context.get('page_number', page_num_in_blob + 1)
            try:
                if page_response.get('error'):
                    raise ValueError(page_response['error']['message'])
                
                full_text = page_response.get('fullTextAnnotation', {}).get('text', '')
                if not full_text:
                    raise ValueError("No text detected on page.")

                parsed_data = _parse_french_id_card_text(full_text)
                
                # Calculate an average confidence score for the page
                total_confidence = 0
                symbol_count = 0
                for page in page_response.get('fullTextAnnotation', {}).get('pages', []):
                    for block in page.get('blocks', []):
                        for paragraph in block.get('paragraphs', []):
                            for word in paragraph.get('words', []):
                                for symbol in word.get('symbols', []):
                                    total_confidence += symbol.get('confidence', 0)
                                    symbol_count += 1
                
                average_confidence = (total_confidence / symbol_count) if symbol_count > 0 else 0.0
                parsed_data['confidence_score'] = round(average_confidence, 4)

                results.append({"page_number": actual_page_num, "data": parsed_data, "status": "SUCCESS"})
            except Exception as e:
                logger.warning(f"Failed to parse page {actual_page_num}: {e}")
                results.append({"page_number": actual_page_num, "error": str(e), "status": "FAILURE"})
    
    # --- Clean up the result files from GCS after processing ---
    for blob in blob_list:
        blob.delete()
        
    return {"status": "SUCCESS", "results": results}


def cancel_google_ocr_operation(operation_name: str):
    """Requests cancellation of a Google Vision API operation."""
    try:
        if not vision_client:
            logger.error("Vision client not initialized, cannot cancel operation.")
            return
        logger.info(f"Requesting cancellation for operation: {operation_name}")
        vision_client.transport.operations_client.cancel_operation(name=operation_name)
    except Exception as e:
        logger.error(f"Failed to send cancellation request for operation {operation_name}: {e}")

def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Helper to parse and format date string."""
    if not date_str:
        return None
    try:
        # Assuming format DD.MM.YYYY or DD/MM/YYYY
        cleaned_date_str = date_str.replace('.', '/')
        dt_obj = datetime.strptime(cleaned_date_str, '%d/%m/%Y')
        return dt_obj.strftime('%Y-%m-%d')
    except ValueError:
        logger.warning(f"Could not parse date string: {date_str}")
        return None

def _parse_french_id_card_text(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Parses raw OCR text from a French ID card to extract structured data.
    This parser is an educated guess and may need significant refinement
    based on the quality and format of your specific document scans.
    """
    data = {
        "first_name": None,
        "last_name": None,
        "passport_number": None,
        "birth_date": None,
        "delivery_date": None,
        "expiration_date": None,
        "nationality": "FRANCAISE", # Default for French ID
    }

    # Normalize text for easier regex matching
    text_lines = [line.strip() for line in raw_text.split('\n')]
    full_text_single_line = ' '.join(text_lines)

    # --- Regex for common fields ---
    # Passport Number (ID Card Number) - often 12 digits for CNIe
    id_match = re.search(r'(\b\d{2}[A-Z\d]{2}\s?\d{5}\b)', full_text_single_line)
    if id_match:
        data["passport_number"] = id_match.group(1).replace(" ", "")

    # Last Name (Nom)
    last_name_match = re.search(r'Nom\s*[:\s]+\s*([A-Z\s\'-]+)', raw_text, re.IGNORECASE)
    if last_name_match:
        data["last_name"] = last_name_match.group(1).strip()

    # First Name (Prénoms)
    first_name_match = re.search(r'Prénom\(s\)\s*[:\s]+\s*([A-Z\s\'-]+)', raw_text, re.IGNORECASE)
    if first_name_match:
        data["first_name"] = first_name_match.group(1).strip()

    # Birth Date (Né(e) le)
    birth_date_match = re.search(r'Né\(e\)\s+le\s+(\d{2}[./]\d{2}[./]\d{4})', raw_text, re.IGNORECASE)
    if birth_date_match:
        data["birth_date"] = _parse_date(birth_date_match.group(1))

    # --- Regex for dates based on proximity ---
    # Often dates appear in a sequence: DD.MM.YYYY - DD.MM.YYYY
    date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
    all_dates = re.findall(date_pattern, full_text_single_line)
    if len(all_dates) >= 2:
        # A common pattern is Delivery Date then Expiry Date
        data["delivery_date"] = _parse_date(all_dates[0])
        data["expiration_date"] = _parse_date(all_dates[1])


    # --- Fallback using Machine Readable Zone (MRZ) if present ---
    # Example MRZ: IDFRA<LASTNAME><<FIRSTNAME<<<<<<<<<<<<<
    mrz_line = None
    for line in text_lines:
        if line.startswith('IDFRA'):
            mrz_line = line.replace(' ', '')
            break
    
    if mrz_line:
        if not data["passport_number"]:
             # Extract from first part of MRZ if available
             pass # MRZ format varies, add logic if needed.

        # MRZ parsing is complex, this is a simplified example
        parts = mrz_line[5:].split('<<')
        if len(parts) >= 2:
            if not data["last_name"]:
                data["last_name"] = parts[0].replace('<', ' ').strip()
            if not data["first_name"]:
                data["first_name"] = parts[1].replace('<', ' ').strip()

    # Final validation check
    if not all([data["last_name"], data["first_name"], data["birth_date"], data["passport_number"]]):
        missing_fields = [k for k, v in data.items() if v is None and k in ["last_name", "first_name", "birth_date", "passport_number"]]
        raise ValueError(f"Could not parse all required fields. Missing: {', '.join(missing_fields)}.")
        
    return data