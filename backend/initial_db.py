import logging
from database import engine, SessionLocal
import models
import crud
import schemas
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating initial database tables...")
    # The checkfirst=True is still a good safety measure
    models.Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Database tables created.")

    db = SessionLocal()
    # Check if admin user exists and create one if not
    admin_user = crud.get_user_by_username(db, username="admin")
    if not admin_user:
        logger.info("Admin user not found, creating one...")
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
        if not ADMIN_PASSWORD:
            logger.warning("ADMIN_PASSWORD environment variable not set. Admin user not created.")
        else:
            admin = schemas.UserCreate(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                phone_number="1234567890",
                user_name="admin",
                password=ADMIN_PASSWORD
            )
            crud.create_user(db=db, user=admin, role="admin", token=None)
            logger.info("Admin user created.")
    else:
        logger.info("Admin user already exists.")
    db.close()

if __name__ == "__main__":
    init_db()