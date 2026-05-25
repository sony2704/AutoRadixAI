"""
Core Exception Hierarchy for AutoRadixAI
"""
from __future__ import annotations

from fastapi import status


class AutoRadixException(Exception):
    """Base exception for all AutoRadixAI errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "AUTORADIX_ERROR"

    def __init__(self, detail: str, error_code: str | None = None) -> None:
        self.detail = detail
        if error_code:
            self.error_code = error_code
        super().__init__(detail)


class FileNotSupportedError(AutoRadixException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    error_code = "FILE_NOT_SUPPORTED"


class DICOMParseError(AutoRadixException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "DICOM_PARSE_ERROR"


class DICOMCorruptedError(AutoRadixException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "DICOM_CORRUPTED"


class StudyNotFoundError(AutoRadixException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "STUDY_NOT_FOUND"


class SeriesNotFoundError(AutoRadixException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "SERIES_NOT_FOUND"


class ModelNotFoundError(AutoRadixException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "MODEL_NOT_FOUND"


class InferenceError(AutoRadixException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "INFERENCE_ERROR"


class InferenceTimeoutError(AutoRadixException):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    error_code = "INFERENCE_TIMEOUT"


class StorageError(AutoRadixException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "STORAGE_ERROR"


class AnonymizationError(AutoRadixException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "ANONYMIZATION_ERROR"


class AuthenticationError(AutoRadixException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AutoRadixException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "AUTHORIZATION_ERROR"


class ValidationError(AutoRadixException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
