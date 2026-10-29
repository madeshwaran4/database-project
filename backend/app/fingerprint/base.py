from abc import ABC, abstractmethod
from typing import Tuple


class FingerprintProvider(ABC):
    """Abstract interface for biometric fingerprint acquisition, template extraction, and matching."""

    @abstractmethod
    def capture(self) -> bytes:
        """Capture raw biometric fingerprint image/sample bytes from reader or mock device."""
        pass

    @abstractmethod
    def extract_template(self, image: bytes) -> bytes:
        """Extract proprietary or standardized minutiae template from raw fingerprint image bytes."""
        pass

    @abstractmethod
    def match(self, template_a: bytes, template_b: bytes) -> Tuple[bool, float]:
        """Compare two minutiae templates.
        Returns:
            Tuple[bool, float]: (is_match, similarity_score)
        """
        pass
