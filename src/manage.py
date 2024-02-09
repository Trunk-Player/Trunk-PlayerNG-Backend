#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import gevent.monkey

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunkplayer_ng.settings")
    try:
        gevent.monkey.patch_all()
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    gevent.monkey.patch_all()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
