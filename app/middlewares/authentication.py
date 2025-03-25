# mixins/jwt_mixin.py
import jwt
from django.conf import settings
from django.contrib import auth
from django.http import JsonResponse
from app.exceptions import (
    AuthenticationCredentialsNotProvidedException,
    InvalidOrExpiredTokenException,
)
import logging


logger = logging.getLogger("django")


class JWTMixin:
    def verify_jwt_token(self, token):
        try:
            payload = jwt.decode(
                token,
                settings.SIMPLE_JWT["SIGNING_KEY"],
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]],
            )
            logger.info("Token decoded and verified")
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidOrExpiredTokenException("Token has expired.")
        except jwt.InvalidTokenError:
            raise InvalidOrExpiredTokenException("Invalid token.")

    def get_token_from_request(self, request):
        auth_header = request.headers.get("Authorization", None)
        if auth_header:
            parts = auth_header.split()
            if (
                parts[0].lower() == settings.SIMPLE_JWT["AUTH_HEADER_TYPES"][0].lower()
                and len(parts) == 2
            ):
                return parts[1]
        return None


class JWTAuthMiddleware(JWTMixin):
    EXCLUDED_PATHS = [
        "/favicon.ico",
        "/static/",
        "/api/docs",
        "/api/token",
        "/api/redoc",
        "/api/schema",
        "/api/users/register"
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            try:
                logger.info("Token Validation Started")
                token = self.get_token_from_request(request)
                if not token:
                    raise AuthenticationCredentialsNotProvidedException()

                payload = self.verify_jwt_token(token)
                print(payload)
                if not payload:
                    raise InvalidOrExpiredTokenException()

                request.session['user'] = payload
                logger.info(f"Token has been verified for user {payload}")

            except AuthenticationCredentialsNotProvidedException as e:
                request.session.flush()
                logger.error("Authentication Credentials Not provided")
                return JsonResponse({"error": str(e)}, status=401)
            except InvalidOrExpiredTokenException as e:
                request.session.flush()
                logger.error("Invired or Expired Token")
                return JsonResponse({"error": str(e)}, status=401)

        response = self.get_response(request)
        return response
