"""Pytest fixtures and hooks shared across the test suite.

QSettings isolation is applied at conftest import time, before pytest collects
any test modules. Several zxlive modules (notably ``zxlive.settings``) write to
QSettings at import time, so any later setup (e.g., an autouse fixture) would
already have allowed those writes to mutate the developer or CI machine's
persistent zxlive configuration.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings


def _probe_default_path(fmt: QSettings.Format) -> str:
    """Return the base path Qt would use by default for ``fmt`` under UserScope.

    PySide6 does not expose ``QSettings.path()``, so we construct a throwaway
    QSettings (no file is created) and strip the ``<org>/<app>.ext`` suffix
    from its fileName.
    """
    probe = QSettings(fmt, QSettings.Scope.UserScope,
                      "zxlive-conftest-probe", "zxlive-conftest-probe")
    return str(Path(probe.fileName()).parent.parent)


# ``zxlive`` constructs ``QSettings("zxlive", "zxlive")`` without specifying a
# format, which uses ``NativeFormat`` regardless of ``setDefaultFormat`` in
# PySide6. Redirect both formats so no zxlive write can land in the real user
# config no matter which format the production code (or any future code) picks.
_ORIGINAL_FORMAT = QSettings.defaultFormat()
_ORIGINAL_NATIVE_PATH = _probe_default_path(QSettings.Format.NativeFormat)
_ORIGINAL_INI_PATH = _probe_default_path(QSettings.Format.IniFormat)

_QSETTINGS_TMPDIR = tempfile.TemporaryDirectory(prefix="zxlive-test-qsettings-")

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.NativeFormat, QSettings.Scope.UserScope,
                  _QSETTINGS_TMPDIR.name)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                  _QSETTINGS_TMPDIR.name)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore the original QSettings state and remove the temp directory."""
    QSettings.setDefaultFormat(_ORIGINAL_FORMAT)
    QSettings.setPath(QSettings.Format.NativeFormat, QSettings.Scope.UserScope,
                      _ORIGINAL_NATIVE_PATH)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                      _ORIGINAL_INI_PATH)
    _QSETTINGS_TMPDIR.cleanup()
