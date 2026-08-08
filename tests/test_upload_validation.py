import pytest

from app.upload_validation import MAX_PDF_BYTES, UploadValidationError, validate_pdf_upload


def test_valid_pdf_signature_is_accepted():
    validate_pdf_upload("notes.pdf", b"%PDF-1.7\nminimal test content")


def test_non_pdf_extension_is_rejected():
    with pytest.raises(UploadValidationError, match="Only PDF files"):
        validate_pdf_upload("notes.txt", b"%PDF-1.7\ncontent")


def test_empty_pdf_is_rejected():
    with pytest.raises(UploadValidationError, match="empty"):
        validate_pdf_upload("notes.pdf", b"")


def test_fake_pdf_is_rejected():
    with pytest.raises(UploadValidationError, match="valid PDF"):
        validate_pdf_upload("notes.pdf", b"This is not really a PDF")


def test_oversized_pdf_is_rejected():
    oversized = b"%PDF-" + (b"0" * MAX_PDF_BYTES)
    with pytest.raises(UploadValidationError, match="20 MB or smaller"):
        validate_pdf_upload("large.pdf", oversized)
