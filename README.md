# py-csv-transformer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Turns repetitive CSV cleanup into a short, typed pipeline — rename columns, fill defaults, cast values, filter rows, drop junk, in one pass.

## 🚀 Overview

Most CSV work is the same five operations repeated with small variations. `py-csv-transformer` models each operation as a typed step, chains them in a `Transformer`, and reports what happened: how many rows survived, how many were dropped, and which columns changed. Files stream in chunks, so large exports don't blow up memory.

## ✨ Features

- **Typed step protocol:** every transform implements one `apply(row) -> row | None`; returning `None` drops the row
- **Built-in steps:** `ColumnMapper`, `DefaultValueFiller`, `ExpressionCast`, `RowFilter`, `ColumnDropper`
- **Header safety:** duplicate headers raise immediately instead of silently corrupting data
- **Pipeline report:** counts of kept/dropped rows plus the exact set of touched columns
- **Streaming reader:** `read_stream(chunk_size=...)` yields fixed-size chunks for huge files
- **Multiple sinks:** CSV or JSONL output with UTF-8 by default
- **Zero dependencies:** standard library only (openpyxl not required)

## 🚧 Structure

```
py-csv-transformer/
├── src/csv_transformer/
│   ├── __init__.py
│   ├── core.py
│   └── io.py
├── tests/
│   ├── test_core.py
│   └── test_io.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

### For Development

```bash
git clone https://github.com/supremeloki/py-csv-transformer.git
cd py-csv-transformer
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from csv_transformer import (
    ColumnMapper, ColumnDropper, DefaultValueFiller,
    ExpressionCast, RowFilter, Transformer,
)

transformer = Transformer()
transformer.add_step(ColumnMapper({"nm": "name"}))
transformer.add_step(DefaultValueFiller({"role": "user"}, {"name", "role"}))
transformer.add_step(ExpressionCast({"qty": "int"}, {"qty"}))
transformer.add_step(RowFilter(lambda r: r["qty"] > 0))
transformer.add_step(ColumnDropper({"internal_id"}))

result = transformer.run(rows)
print(result.dropped_count)
print(sorted(result.touched_columns))
```

### File to file

```python
from pathlib import Path
from csv_transformer.io import run_file

written, dropped = run_file(
    Path("raw.csv"), Path("clean.csv"),
    lambda: [ColumnMapper({"nm": "name"})],
)
```

## 🔧 Error Handling

```text
TransformerError
├── UnknownColumnError      # default/cast references a missing column
└── DuplicateHeaderError    # source has repeated header names
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style)
- Zero comments — names carry the meaning
- `ruff` clean

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi**

---

⭐ Star this repo if you find it useful!
