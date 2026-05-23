"""Smoke tests — package imports cleanly and version is set."""
import cmapss_rul


def test_version_set() -> None:
    assert cmapss_rul.__version__
    assert isinstance(cmapss_rul.__version__, str)


def test_api_imports() -> None:
    from cmapss_rul.api.main import app
    assert app is not None


def test_audit_logger_imports() -> None:
    from cmapss_rul.governance.audit_logger import AuditLogger
    assert AuditLogger is not None
