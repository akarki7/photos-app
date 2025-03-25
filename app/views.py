from rest_framework.views import APIView
from rest_framework.response import Response
import logging

# Import the DatabaseHealthChecker
from .db_checker import DatabaseHealthChecker

logger = logging.getLogger("django")


class HealthView(APIView):
    def get(self, request, format=None):
        # Check API health
        api_status = {"status": "healthy"}
        
        # Check database health
        db_status = DatabaseHealthChecker.check_health()
        
        # Construct the complete response
        data = {
            "api": api_status["status"],
            "database": db_status["status"]
        }
        
        # Add any error details if present
        if db_status["status"] == "unhealthy" and "error" in db_status:
            data["database_error"] = db_status["error"]
        
        logger.info(f"Health Check: API: {api_status['status']}, DB: {db_status['status']}")
        
        # Determine HTTP status code based on health
        status_code = 200 if all(value == "healthy" for value in [api_status["status"], db_status["status"]]) else 503
        
        return Response(data, status=status_code)