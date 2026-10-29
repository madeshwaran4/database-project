import hashlib
from typing import Tuple
from app.fingerprint.base import FingerprintProvider
from app.core.config import settings


class MockFingerprintProvider(FingerprintProvider):
    """Deterministic fake matching provider for fast, reliable unit and integration tests."""

    def __init__(self, match_threshold: float | None = None):
        self.threshold = match_threshold if match_threshold is not None else settings.FINGERPRINT_MATCH_THRESHOLD

    def capture(self) -> bytes:
        """Returns a deterministic dummy fingerprint sample."""
        return b"MOCK_FINGERPRINT_SAMPLE_STANDARD_V1"

    def extract_template(self, image: bytes) -> bytes:
        """Generate a deterministic normalized minutiae template from raw image bytes.
        Prefixes with 'TEMPL:' + sha256 of image.
        """
        if not image:
            raise ValueError("Fingerprint image bytes cannot be empty.")
        hasher = hashlib.sha256(image)
        return f"TEMPL:{hasher.hexdigest()}".encode("utf-8")

    def match(self, template_a: bytes, template_b: bytes) -> Tuple[bool, float]:
        """Compares two templates.
        Identical templates return 100.0 score (Match).
        Templates with same prefix group return high score.
        Different templates return 10.0 score (Mismatch).
        """
        if not template_a or not template_b:
            return False, 0.0

        if template_a == template_b:
            return True, 100.0

        # Check for partial resemblance (e.g., test simulated minutiae overlap)
        str_a = template_a.decode("utf-8", errors="ignore")
        str_b = template_b.decode("utf-8", errors="ignore")

        # Allow test hooks where templates ending in '_MATCH' or starting with matching group match
        if ":" in str_a and ":" in str_b:
            hash_a = str_a.split(":", 1)[1]
            hash_b = str_b.split(":", 1)[1]
            # Common prefix matching score simulation
            common_len = 0
            for ca, cb in zip(hash_a, hash_b):
                if ca == cb:
                    common_len += 1
                else:
                    break
            score = (common_len / max(len(hash_a), 1)) * 100.0
            return score >= self.threshold, score

        return False, 0.0
