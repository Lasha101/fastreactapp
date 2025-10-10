# backend/celery_worker.py

import os
import time
from typing import Optional

import ocr_service
import crud
import schemas
from database import SessionLocal
from celery import Celery, Task
from celery.signals import task_revoked
from celery.utils.log import get_task_logger

# --- Celery Configuration ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)
celery_app.conf.update(
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    task_track_started=True, # Important for getting task state
)

logger = get_task_logger(__name__)


@task_revoked.connect
def on_task_revoked(request, terminated, signum, expired, **kwargs):
    """
    Handler to clean up resources when a task is revoked.
    """
    # The task's state is stored in its request context
    info = request.properties.get('root_id') # A way to access state, but can be complex
    logger.warning(f"Task {request.id} revoked. Manual cleanup may be required if resources are not in task state.")
    # More robust cleanup is handled in the task's finally block.


@celery_app.task(bind=True, name='tasks.extract_document_data')
def extract_document_data(self, file_path: str, original_filename: str, content_type: str, destination: Optional[str], user_id: int):
    """
    Celery task to perform OCR, parse results, and save them to the database.
    """
    gcs_source_uri = None
    google_operation_name = None

    try:
        # 1. Start the async job on Google Vision
        self.update_state(state='PROGRESS', meta={'status': 'Uploading to cloud...'})
        google_operation_name, gcs_source_uri = ocr_service.start_async_ocr_extraction(file_path, content_type)

        logger.info(f"Task {self.request.id} started Google operation {google_operation_name}")
        self.update_state(state='PROGRESS', meta={'status': 'Processing document...'})
        
        # 2. Poll for the result from Google
        while True:
            if self.is_revoked():
                logger.warning(f"Task {self.request.id} is revoked. Cancelling Google operation.")
                # The 'finally' block will handle the cleanup
                return {'status': 'CANCELLED', 'detail': 'Task was cancelled by user.'}

            result = ocr_service.get_async_ocr_results(google_operation_name)
            
            if result['status'] == 'SUCCESS':
                logger.info(f"Google operation {google_operation_name} succeeded.")
                
                self.update_state(state='PROGRESS', meta={'status': 'Saving results to database...'})
                
                # 3. Process results and save to DB
                db = SessionLocal()
                success_count = 0
                failures = []
                try:
                    for page_result in result.get('results', []):
                        if page_result.get('status') == 'SUCCESS':
                            passport_data = schemas.PassportCreate(
                                **page_result['data'],
                                destination=destination # Apply the same destination to all passports in this file
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
            
            # If still processing, wait before polling again
            time.sleep(10)

    except Exception as e:
        logger.error(f"Error in Celery task {self.request.id}: {e}", exc_info=True)
        # This will mark the task as FAILED and store the exception
        self.update_state(state='FAILURE', meta={'status': str(e)})
        # Re-raise the exception to ensure Celery records it as a failure
        raise e
    finally:
        # 4. Cleanup all resources
        logger.info(f"Cleaning up resources for task {self.request.id}.")
        # Cancel the Google operation if it's still running
        if self.is_revoked() and google_operation_name:
             ocr_service.cancel_google_ocr_operation(google_operation_name)
        # Delete the uploaded file from GCS
        if gcs_source_uri:
            ocr_service._delete_from_gcs(gcs_source_uri)
        # Delete the temporary local file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")