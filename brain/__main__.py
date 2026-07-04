"""Allow python -m brain to invoke CLI."""

from brain.cli import main
import sys

sys.exit(main())
