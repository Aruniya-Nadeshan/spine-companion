"""Console helpers.

The Windows console often uses a legacy code page (cp1252) that cannot show characters such as
"≥" or "°" that appear in the source texts. Printing them would crash a command in the middle of a
report. configure_console() makes printing replace such characters with "?" instead.
"""
import sys


def configure_console():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
