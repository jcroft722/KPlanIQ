from app.core.database import recreate_tables
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting database recreation...")
    try:
        recreate_tables()
        logger.info("Database recreation completed successfully!")
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise 