from app.core.config import settings
from app.fingerprint.base import FingerprintProvider
from app.fingerprint.mock import MockFingerprintProvider
from app.fingerprint.dataset import DatasetFingerprintProvider
from app.fingerprint.usb_scanner import UsbScannerProvider
from app.fingerprint.encryption import biometric_cipher

_provider_instance: FingerprintProvider | None = None


def get_fingerprint_provider() -> FingerprintProvider:
    """Factory function returning active FingerprintProvider based on environment configuration."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = settings.FINGERPRINT_PROVIDER.lower()
    if provider_name == "mock":
        _provider_instance = MockFingerprintProvider()
    elif provider_name == "dataset":
        _provider_instance = DatasetFingerprintProvider()
    elif provider_name == "usb":
        _provider_instance = UsbScannerProvider()
    else:
        _provider_instance = MockFingerprintProvider()

    return _provider_instance


__all__ = [
    "FingerprintProvider",
    "MockFingerprintProvider",
    "DatasetFingerprintProvider",
    "UsbScannerProvider",
    "biometric_cipher",
    "get_fingerprint_provider",
]
