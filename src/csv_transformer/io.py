from __future__ import annotations

import csv
from pathlib import Path

from .core import DuplicateHeaderError, Row, TransformerError


class CsvSource:
