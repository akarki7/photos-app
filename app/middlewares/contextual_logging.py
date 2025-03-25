import logging
import json
import time


logger = logging.getLogger("django")


class RequestResponseLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exclude_paths = ["/api/docs/"]

    def __call__(self, request):
        response = self.process_request(request)
        response = response or self.get_response(request)
        response = self.process_response(request, response)
        return response

    def process_request(self, request):
        if any(request.path.startswith(path) for path in self.exclude_paths):
            # Skip logging for excluded paths
            return None

        request.start_time = time.time()

        # Get the client's IP address
        client_ip = request.META.get("REMOTE_ADDR")

        # Log the incoming request
        request_log = {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "query_parameters": request.GET.dict(),
            "client_ip": client_ip,
        }
        logger.info(f"Incoming Request: {json.dumps(request_log)}")

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            end_time = time.time()
            execution_time = end_time - request.start_time

            # Get the client's IP address
            client_ip = request.META.get("REMOTE_ADDR")

            response_log = {
                "status_code": response.status_code,
                "headers": dict(response.items()),
                "execution_time": f"{execution_time:.6f} seconds",
                "client_ip": client_ip,
            }
            logger.info(f"Outgoing Response: {json.dumps(response_log)}")

            response["X-Execution-Time"] = str(execution_time)

        return response
