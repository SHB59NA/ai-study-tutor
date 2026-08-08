MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


class UploadValidationError(ValueError):
    """Raised when an uploaded study document fails public-demo safety checks."""


def validate_pdf_upload(filename: str, data: bytes) -> None:
    """Validate a PDF before parsing or indexing it.

    The public demo intentionally accepts one modest-sized PDF per browser
    session. This protects the Space from accidental oversized uploads and
    rejects files that merely use a .pdf extension without a PDF signature.
    """
    if not filename or not filename.lower().endswith(".pdf"):
        raise UploadValidationError("Only PDF files are supported.")

    if not data:
        raise UploadValidationError("The uploaded PDF is empty.")

    if len(data) > MAX_PDF_BYTES:
        raise UploadValidationError(
            "The uploaded PDF is too large. Please use a file that is 20 MB or smaller."
        )

    if not data.startswith(b"%PDF-"):
        raise UploadValidationError(
            "The uploaded file does not appear to be a valid PDF."
        )
