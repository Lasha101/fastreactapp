# backend/celery_worker.py

import os
import time
from typing import Optional
import tempfile

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
    accept_content=['json', 'pickle'], # Add pickle to handle bytes
    task_serializer='pickle',
    result_serializer='json',
    task_track_started=True,
)

logger = get_task_logger(__name__)


# --- MODIFICATION START ---
@task_revoked.connect
def on_task_revoked(request, terminated, signum, expired, **kwargs):
    """
    Handler to log when a task is revoked.
    Cleanup is now handled entirely within the task's 'finally' block.
    """
    # The 'request' object here is a 'Request' class, not the task context.
    # We can get the task ID directly from it.
    logger.warning(
        f"Task {request.id} was revoked. "
        f"Terminated: {terminated}, Signal: {signum}, Expired: {expired}"
    )
# --- MODIFICATION END ---


@celery_app.task(bind=True, name='tasks.extract_document_data')
def extract_document_data(self, file_content: bytes, original_filename: str, content_type: str, destination: Optional[str], user_id: int):
    """
    Celery task to perform OCR, parse results, and save them to the database.
    """
    gcs_source_uri = None
    google_operation_name = None
    file_path = None

    try:
        # Create a temporary file inside the worker container to store the content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"-{original_filename}") as temp_file:
            temp_file.write(file_content)
            file_path = temp_file.name

        self.update_state(state='PROGRESS', meta={'status': 'Uploading to cloud...'})
        google_operation_name, gcs_source_uri = ocr_service.start_async_ocr_extraction(file_path, content_type)

        logger.info(f"Task {self.request.id} started Google operation {google_operation_name}")
        self.update_state(state='PROGRESS', meta={'status': 'Processing document...'})
        
        while True:
            if self.request.is_revoked():
                logger.warning(f"Task {self.request.id} is revoked during processing loop.")
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
            
            time.sleep(10)

    except Exception as e:
        logger.error(f"Error in Celery task {self.request.id}: {e}", exc_info=True)
        raise e
    finally:
        logger.info(f"Cleaning up resources for task {self.request.id}.")
        if self.request.is_revoked() and google_operation_name:
             ocr_service.cancel_google_ocr_operation(google_operation_name)
        if gcs_source_uri:
            ocr_service._delete_from_gcs(gcs_source_uri)
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")