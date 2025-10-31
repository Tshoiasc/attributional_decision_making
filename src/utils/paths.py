"""Utilities for resolving resource and output paths across environments."""

from __future__ import annotations

import os
import platform
import sys
from functools import lru_cache
from typing import Tuple


_APP_SUPPORT_DIR_NAME = "PsychExperiment"


def _norm_join(base: str, *parts: str) -> str:
    clean_parts = [part for part in parts if part]
    return os.path.normpath(os.path.join(base, *clean_parts))


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


@lru_cache(maxsize=1)
def bundle_dir() -> str:
    """Return the directory that contains bundled resources."""

    if _is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return _norm_join(os.path.dirname(__file__), "..", "..")


@lru_cache(maxsize=1)
def runtime_dir() -> str:
    """Return the directory where the executable/script resides."""

    if _is_frozen():
        return os.path.dirname(sys.executable)
    return bundle_dir()


@lru_cache(maxsize=1)
def user_data_dir() -> str:
    """Return a writable user-level directory for experiment data."""

    system = sys.platform
    if system.startswith("win"):
        base = os.environ.get("APPDATA") or _norm_join(os.path.expanduser("~"), "AppData", "Roaming")
    elif system == "darwin":
        base = _norm_join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or _norm_join(os.path.expanduser("~"), ".local", "share")
    return _norm_join(base, _APP_SUPPORT_DIR_NAME)


def resource_path(*parts: str) -> str:
    """Resolve a bundled resource path."""

    return _norm_join(bundle_dir(), *parts)


def resolve_output_directory(configured: str) -> Tuple[str, bool]:
    """Resolve the configured export directory to an absolute writable path.

    Returns a tuple of (path, is_fallback) where is_fallback indicates
    whether the user-level directory was used because the preferred
    location was not writable.
    """

    if os.path.isabs(configured):
        if _ensure_directory(configured):
            return configured, False
        fallback_root = user_data_dir()
        fallback = _norm_join(fallback_root, os.path.basename(configured))
        _ensure_directory(fallback)
        return fallback, True

    preferred = _norm_join(runtime_dir(), configured)
    if _ensure_directory(preferred):
        return preferred, False

    fallback_root = user_data_dir()
    fallback = _norm_join(fallback_root, configured)
    _ensure_directory(fallback)
    return fallback, True


def runtime_file(*parts: str) -> str:
    """Return a path relative to the runtime directory."""

    return _norm_join(runtime_dir(), *parts)


def _ensure_directory(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, ".write_test")
        with open(test_file, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(test_file)
        return True
    except OSError:
        return False


