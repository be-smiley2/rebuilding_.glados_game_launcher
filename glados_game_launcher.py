#!/usr/bin/env python3
"""Entry point for the refactored GLaDOS game launcher."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from glados_launcher import ApertureEnrichmentCenterGUI
from glados_launcher.config import FIRST_RUN_FLAG


def main() -> None:
    """Main entry point for the Aperture Science Enrichment Center."""
    try:
        print("Initializing Aperture Science Enrichment Center...")

        show_welcome = False
        if not FIRST_RUN_FLAG.exists():
            show_welcome = True
            try:
                FIRST_RUN_FLAG.touch()
            except Exception:
                pass

        print("Starting GUI...")
        center = ApertureEnrichmentCenterGUI()

        if show_welcome:
            def show_welcome_dialog() -> None:
                welcome = messagebox.askyesno(
                    "Aperture Science Enrichment Center",
                    "Welcome to the Aperture Science Enrichment Center!\n\n"
                    "This advanced game management system will scan your computer\n"
                    "for test subjects (games) and provide intelligent analysis.\n\n"
                    "GLaDOS: 'Hello. I am GLaDOS. Let's begin testing.'\n\n"
                    "Would you like to initiate the scanning protocols now?",
                )

                if welcome:
                    center.add_commentary("GLaDOS", "Initiating welcome scan protocol...")
                    center.run_smart_scan()

            center.root.after(1000, show_welcome_dialog)

        print("Launching application...")
        center.run()

    except Exception as exc:  # pragma: no cover - last resort error handling
        print(f"Critical error: {exc}")
        try:
            import traceback

            traceback.print_exc()

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Critical System Failure",
                f"Failed to initialize Aperture Science systems:\n{exc}\n\nCheck console for details.",
            )
            root.destroy()
        except Exception:
            print("Failed to show error dialog. Check console output.")


if __name__ == "__main__":
    main()
