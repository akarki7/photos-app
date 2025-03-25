from django.db import connection
from django.db.utils import OperationalError, DatabaseError
import logging

logger = logging.getLogger("django")


class DatabaseHealthChecker:
    """
    Wrapper class to check PostgreSQL database connection health.
    """

    @staticmethod
    def check_health():
        """
        Checks if the database connection is healthy by executing a simple query.

        Returns:
            dict: A dictionary with status information
        """
        try:
            # Execute a simple query to check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            logger.info("Database health check: OK")
            return {"status": "healthy"}

        except (OperationalError, DatabaseError) as e:
            error_message = str(e)
            logger.error(f"Database health check failed: {error_message}")
            return {"status": "unhealthy", "error": error_message}
