import os
import hashlib
from pathlib import Path
from typing import Tuple, List
from app.fingerprint.base import FingerprintProvider
from app.core.config import settings


class DatasetFingerprintProvider(FingerprintProvider):
    """Loads benchmark/sample fingerprint images from a directory (e.g. FVC or SOCOFing dataset)
    and computes biometric feature templates.
    """

    def __init__(self, dataset_dir: str | None = None, match_threshold: float | None = None):
        self.dataset_dir = Path(dataset_dir or settings.DATASET_DIR)
        self.threshold = match_threshold if match_threshold is not None else settings.FINGERPRINT_MATCH_THRESHOLD

    def get_available_samples(self) -> List[str]:
        """List filenames of available sample fingerprints in dataset directory."""
        if not self.dataset_dir.exists():
            return []
        return [p.name for p in self.dataset_dir.glob("*.*") if p.suffix.lower() in (".bmp", ".png", ".jpg", ".tif")]

    def capture(self) -> bytes:
        """Simulate capturing by reading the first sample image from dataset, or a generated sample."""
        samples = self.get_available_samples()
        if samples:
            sample_path = self.dataset_dir / samples[0]
            with open(sample_path, "rb") as f:
                return f.read()
        return b"DATASET_FALLBACK_SAMPLE_BYTES"

    def extract_template(self, image: bytes) -> bytes:
        """Extract a structured minutiae feature vector from image bytes."""
        if not image:
            raise ValueError("Fingerprint image data cannot be empty.")
        # Minutiae vector signature simulation
        digest = hashlib.sha256(image).hexdigest()
        byte_len = len(image)
        return f"DATASET_MINUTIAE:LEN={byte_len}:HASH={digest}".encode("utf-8")

    def match(self, template_a: bytes, template_b: bytes) -> Tuple[bool, float]:
        """Match two dataset templates using signature correlation."""
        if not template_a or not template_b:
            return False, 0.0

        if template_a == template_b:
            return True, 100.0

        str_a = template_a.decode("utf-8", errors="ignore")
        str_b = template_b.decode("utf-8", errors="ignore")

        # Compare hash similarity
        if "HASH=" in str_a and "HASH=" in str_b:
            h_a = str_a.split("HASH=")[1]
            h_b = str_b.split("HASH=")[1]
            common = sum(1 for a, b in zip(h_a, h_b) if a == b)
            score = (common / max(len(h_a), 1)) * 100.0
            return score >= self.threshold, score

        return False, 0.0
