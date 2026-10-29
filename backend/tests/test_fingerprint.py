import pytest
from app.fingerprint.encryption import biometric_cipher
from app.fingerprint.mock import MockFingerprintProvider
from app.fingerprint.dataset import DatasetFingerprintProvider


def test_biometric_encryption_decryption():
    sample_template = b"ISO_19794_MINUTIAE_SAMPLE_BYTE_DATA_12345"
    encrypted = biometric_cipher.encrypt_template(sample_template)
    assert encrypted != sample_template
    assert len(encrypted) > len(sample_template)

    decrypted = biometric_cipher.decrypt_template(encrypted)
    assert decrypted == sample_template


def test_mock_fingerprint_match():
    provider = MockFingerprintProvider(match_threshold=40.0)
    image_a = b"USER_ALICE_FINGERPRINT_SCAN_001"
    template_a1 = provider.extract_template(image_a)
    template_a2 = provider.extract_template(image_a)

    is_match, score = provider.match(template_a1, template_a2)
    assert is_match is True
    assert score == 100.0


def test_mock_fingerprint_non_match():
    provider = MockFingerprintProvider(match_threshold=40.0)
    template_a = provider.extract_template(b"IMAGE_A_11111")
    template_b = provider.extract_template(b"IMAGE_B_99999")

    is_match, score = provider.match(template_a, template_b)
    assert is_match is False
    assert score < 40.0


def test_dataset_fingerprint_provider():
    provider = DatasetFingerprintProvider(match_threshold=50.0)
    img = b"RAW_SAMPLE_IMAGE_DATA"
    tmpl_1 = provider.extract_template(img)
    tmpl_2 = provider.extract_template(img)
    matched, score = provider.match(tmpl_1, tmpl_2)
    assert matched is True
    assert score == 100.0
