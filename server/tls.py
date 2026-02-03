"""TLS certificate/key utilities.

HeardDat does not ship with per-install TLS private keys in the repository.
For development and prototype usage, we generate a self-signed certificate at
runtime if none exists (best-effort).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_self_signed_cert(
    cert_file: Path,
    key_file: Path,
    *,
    common_name: str = "localhost",
    days_valid: int = 3650,
) -> bool:
    """Ensure a self-signed certificate/key exists on disk.

    Returns True if cert/key exist (or were created), otherwise False.
    """

    if cert_file.exists() and key_file.exists():
        return True

    cert_file.parent.mkdir(parents=True, exist_ok=True)

    openssl = shutil.which("openssl")
    if not openssl:
        logger.warning("OpenSSL not found; TLS will remain disabled.")
        return False

    # `-nodes` = do not encrypt the private key file on disk.
    # This is acceptable for the current prototype because TLS is optional and
    # the key is generated per-install (not committed to source control).
    cmd = [
        openssl,
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-keyout",
        str(key_file),
        "-out",
        str(cert_file),
        "-days",
        str(days_valid),
        "-subj",
        f"/CN={common_name}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.warning("Failed to generate TLS certificate via openssl: %s", exc)
        return False

    return cert_file.exists() and key_file.exists()

