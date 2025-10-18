"""Aperture Science Enrichment Center launcher package."""

from .dependencies import ensure_dependencies

ensure_dependencies()

from .app import ApertureLauncherGUI, main

__all__ = ["ApertureLauncherGUI", "main"]
