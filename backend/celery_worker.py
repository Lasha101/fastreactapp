# # backend/celery_worker.py

# import os
# from dotenv import load_dotenv
# load_dotenv()
# import time
# from typing import Optional
# import tempfile
# import base64
# import ocr_service
# import crud
# import schemas
# from database import SessionLocal
# from celery import Celery, Task
# from celery.signals import task_revoked
# from celery.utils.log import get_task_logger

# # --- Celery Configuration ---
# # CHANGE THIS
# CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
# CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# celery_app = Celery(
#     "tasks",
#     broker=CELERY_BROKER_URL,
#     backend=CELERY_RESULT_BACKEND
# )
# celery_app.conf.update(
#     accept_content=['json'],
#     task_serializer='json',
#     result_serializer='json',
#     task_track_started=True,
# )

# logger = get_task_logger(__name__)


# # --- MODIFICATION START ---
# @task_revoked.connect
# def on_task_revoked(request, terminated, signum, expired, **kwargs):
#     """
#     Handler to log when a task is revoked.
#     Cleanup is now handled entirely within the task's 'finally' block.
#     """
#     # The 'request' object here is a 'Request' class, not the task context.
#     # We can get the task ID directly from it.
#     logger.warning(
#         f"Task {request.id} was revoked. "
#         f"Terminated: {terminated}, Signal: {signum}, Expired: {expired}"
#     )
# # --- MODIFICATION END ---


# @celery_app.task(bind=True, name='tasks.extract_document_data')
# def extract_document_data(self, file_content: bytes, original_filename: str, content_type: str, destination: Optional[str], user_id: int):
#     """
#     Celery task to perform OCR, parse results, and save them to the database.
#     """
#     gcs_source_uri = None
#     google_operation_name = None
#     file_path = None

#     try:
#         # Decode the Base64 string back into bytes
#         file_content = base64.b64decode(file_content)

#         # Create a temporary file inside the worker container to store the content
#         with tempfile.NamedTemporaryFile(delete=False, suffix=f"-{original_filename}") as temp_file:
#             temp_file.write(file_content)
#             file_path = temp_file.name

#         self.update_state(state='PROGRESS', meta={'status': 'Uploading to cloud...'})
#         google_operation_name, gcs_source_uri = ocr_service.start_async_ocr_extraction(file_path, content_type)

#         logger.info(f"Task {self.request.id} started Google operation {google_operation_name}")
#         self.update_state(state='PROGRESS', meta={'status': 'Processing document...'})
        
#         while True:
#             if self.is_revoked():
#                 logger.warning(f"Task {self.request.id} is revoked during processing loop.")
#                 return {'status': 'CANCELLED', 'detail': 'Task was cancelled by user.'}

#             result = ocr_service.get_async_ocr_results(google_operation_name)
            
#             if result['status'] == 'SUCCESS':
#                 logger.info(f"Google operation {google_operation_name} succeeded.")
                
#                 self.update_state(state='PROGRESS', meta={'status': 'Saving results to database...'})
                
#                 db = SessionLocal()
#                 success_count = 0
#                 failures = []
#                 try:
#                     for page_result in result.get('results', []):
#                         if page_result.get('status') == 'SUCCESS':
#                             passport_data = schemas.PassportCreate(
#                                 **page_result['data'],
#                                 destination=destination 
#                             )
#                             crud.create_user_passport(db=db, passport=passport_data, user_id=user_id)
#                             success_count += 1
#                         else:
#                             failures.append({
#                                 "page": page_result.get('page_number', 'N/A'),
#                                 "error": page_result.get('error', 'Unknown parsing error')
#                             })
#                 finally:
#                     db.close()

#                 final_status = {
#                     'status': 'COMPLETE',
#                     'filename': original_filename,
#                     'successful_pages': success_count,
#                     'failed_pages': failures
#                 }
#                 return final_status

#             elif result['status'] == 'FAILURE':
#                 logger.error(f"Google operation {google_operation_name} failed: {result.get('error')}")
#                 raise Exception(f"Google Vision API Error: {result.get('error', 'Unknown error')}")
            
#             time.sleep(10)

#     except Exception as e:
#         logger.error(f"Error in Celery task {self.request.id}: {e}", exc_info=True)
#         raise e
#     finally:
#         logger.info(f"Cleaning up resources for task {self.request.id}.")
#         if self.is_revoked() and google_operation_name:
#              ocr_service.cancel_google_ocr_operation(google_operation_name)
#         if gcs_source_uri:
#             ocr_service._delete_from_gcs(gcs_source_uri)
#         if file_path and os.path.exists(file_path):
#             os.remove(file_path)
#             logger.info(f"Cleaned up temporary file: {file_path}")




# backend/celery_worker.py - CORRECTED VERSION

import os
from dotenv import load_dotenv
load_dotenv()
import time
from typing import Optional
import tempfile
import base64
import ocr_service
import crud
import schemas
from database import SessionLocal
from celery import Celery
from celery.contrib.abortable import AbortableTask
from celery.signals import task_revoked
from celery.utils.log import get_task_logger

# --- Celery Configuration ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)
celery_app.conf.update(
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    task_track_started=True,
)

logger = get_task_logger(__name__)


@task_revoked.connect
def on_task_revoked(request, terminated, signum, expired, **kwargs):
    """
    Handler to log when a task is revoked.
    Cleanup is handled within the task's 'finally' block.
    """
    logger.warning(
        f"Task {request.id} was revoked. "
        f"Terminated: {terminated}, Signal: {signum}, Expired: {expired}"
    )


# FIX: Use AbortableTask as base class to enable revocation checking
@celery_app.task(bind=True, base=AbortableTask, name='tasks.extract_document_data')
def extract_document_data(self, file_content: bytes, original_filename: str, content_type: str, destination: Optional[str], user_id: int):
    """
    Celery task to perform OCR, parse results, and save them to the database.
    
    Uses AbortableTask to properly support cancellation via is_aborted().
    """
    gcs_source_uri = None
    google_operation_name = None
    file_path = None
    was_cancelled = False

    try:
        # Decode the Base64 string back into bytes
        file_content = base64.b64decode(file_content)

        # Create a temporary file inside the worker container to store the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"-{original_filename}") as temp_file:
            temp_file.write(file_content)
            file_path = temp_file.name

        # FIX: Check for early cancellation using is_aborted()
        if self.is_aborted():
            was_cancelled = True
            logger.warning(f"Task {self.request.id} was cancelled before OCR started.")
            return {'status': 'CANCELLED', 'detail': 'Task was cancelled by user.'}

        self.update_state(state='PROGRESS', meta={'status': 'Uploading to cloud...'})
        google_operation_name, gcs_source_uri = ocr_service.start_async_ocr_extraction(file_path, content_type)

        logger.info(f"Task {self.request.id} started Google operation {google_operation_name}")
        self.update_state(state='PROGRESS', meta={'status': 'Processing document...'})
        
        # Add timeout protection to prevent infinite loops
        max_poll_attempts = 120  # 10 minutes with 5-second intervals
        poll_count = 0
        
        while poll_count < max_poll_attempts:
            # FIX: Check cancellation using is_aborted()
            if self.is_aborted():
                was_cancelled = True
                logger.warning(f"Task {self.request.id} was cancelled during processing loop.")
                return {'status': 'CANCELLED', 'detail': 'Task was cancelled by user.'}

            result = ocr_service.get_async_ocr_results(google_operation_name)
            
            if result['status'] == 'SUCCESS':
                logger.info(f"Google operation {google_operation_name} succeeded.")
                
                self.update_state(state='PROGRESS', meta={'status': 'Saving results to database...'})
                
                db = SessionLocal()
                success_count = 0
                failures = []
                try:
                    for page_result in result.get('results', []):
                        if page_result.get('status') == 'SUCCESS':
                            passport_data = schemas.PassportCreate(
                                **page_result['data'],
                                destination=destination 
                            )
                            crud.create_user_passport(db=db, passport=passport_data, user_id=user_id)
                            success_count += 1
                        else:
                            failures.append({
                                "page": page_result.get('page_number', 'N/A'),
                                "error": page_result.get('error', 'Unknown parsing error')
                            })
                finally:
                    db.close()

                final_status = {
                    'status': 'COMPLETE',
                    'filename': original_filename,
                    'successful_pages': success_count,
                    'failed_pages': failures
                }
                return final_status

            elif result['status'] == 'FAILURE':
                logger.error(f"Google operation {google_operation_name} failed: {result.get('error')}")
                raise Exception(f"Google Vision API Error: {result.get('error', 'Unknown error')}")
            
            poll_count += 1
            time.sleep(5)
        
        # Handle timeout scenario
        logger.error(f"Task {self.request.id} timed out after {max_poll_attempts} polling attempts.")
        raise Exception("OCR processing timed out. The operation may still be running on Google's servers.")

    except Exception as e:
        logger.error(f"Error in Celery task {self.request.id}: {e}", exc_info=True)
        # Don't re-raise if task was cancelled
        if was_cancelled or self.is_aborted():
            return {'status': 'CANCELLED', 'detail': 'Task was cancelled during error handling.'}
        raise e
    finally:
        logger.info(f"Cleaning up resources for task {self.request.id}.")
        
        # Always check current cancellation status in cleanup
        is_currently_cancelled = self.is_aborted() or was_cancelled
        
        # Cancel Google operation if task was cancelled
        if is_currently_cancelled and google_operation_name:
            logger.info(f"Task was cancelled, cancelling Google operation {google_operation_name}")
            ocr_service.cancel_google_ocr_operation(google_operation_name)
        
        # Always clean up GCS source file
        if gcs_source_uri:
            try:
                ocr_service._delete_from_gcs(gcs_source_uri)
            except Exception as cleanup_error:
                logger.error(f"Failed to delete GCS source file {gcs_source_uri}: {cleanup_error}")
        
        # Always clean up local temp file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to delete temp file {file_path}: {cleanup_error}")
