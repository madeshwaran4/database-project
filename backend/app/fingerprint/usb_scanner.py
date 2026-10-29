from typing import Tuple
from app.fingerprint.base import FingerprintProvider


class UsbScannerProvider(FingerprintProvider):
    """Hardware USB Biometric Reader Stub (SecuGen Hamster, DigitalPersona U.are.U, Futronic).
    Contains clear vendor SDK integration hooks and instructions.
    """

    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        # TODO: Initialize vendor SDK library (e.g. ctypes.CDLL("sgfplib.dll") or libdpfp.so)
        # Example SecuGen flow:
        # self.sgfplib = ctypes.CDLL("sgfplib.dll")
        # self.sgfplib.SGFPM_Create(...)
        # self.sgfplib.SGFPM_Init(...)
        # self.sgfplib.SGFPM_OpenDevice(...)

    def capture(self) -> bytes:
        """Capture live biometric scan from hardware scanner.
        TODO (Hardware Deployment):
        1. Call vendor capture API:
           buffer = ctypes.create_string_buffer(image_width * image_height)
           err = self.sgfplib.SGFPM_GetImage(device_handle, buffer)
        2. Validate image quality:
           quality = ctypes.c_ulong()
           self.sgfplib.SGFPM_GetImageQuality(device_handle, width, height, buffer, ctypes.byref(quality))
           if quality.value < 60: raise LowQualityBiometricError()
        3. Return raw image byte buffer.
        """
        raise NotImplementedError(
            "Hardware USB Biometric Reader is not attached in this environment. "
            "Set FINGERPRINT_PROVIDER=mock or FINGERPRINT_PROVIDER=dataset in .env for software emulation."
        )

    def extract_template(self, image: bytes) -> bytes:
        """Extract ANSI-INCITS 378 or ISO/IEC 19794-2 biometric minutiae template.
        TODO:
        template_buffer = ctypes.create_string_buffer(MAX_TEMPLATE_SIZE)
        self.sgfplib.SGFPM_CreateTemplate(device_handle, fingerprint_info, image, template_buffer)
        return template_buffer.raw
        """
        raise NotImplementedError("Vendor SDK required for hardware template extraction.")

    def match(self, template_a: bytes, template_b: bytes) -> Tuple[bool, float]:
        """Hardware SDK 1:1 biometric minutiae matching function.
        TODO:
        matched = ctypes.c_bool()
        score = ctypes.c_int()
        self.sgfplib.SGFPM_MatchTemplate(device_handle, template_a, template_b, security_level, ctypes.byref(matched))
        return matched.value, float(score.value)
        """
        raise NotImplementedError("Vendor SDK required for hardware template matching.")
