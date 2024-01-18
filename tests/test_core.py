import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from csv_transformer import (
    ColumnDropper,
    ColumnMapper,
    DefaultValueFiller,
    DuplicateHeaderError,
    ExpressionCast,
    RowFilter,
    Transformer,
    TransformerError,
    UnknownColumnError,
)


def row(**kwargs):
    return dict(kwargs)


def test_column_mapper_renames():
    mapper = ColumnMapper({"old_name": "new_name"})
    assert mapper.apply(row(old_name="1", keep="x")) == {"new_name": "1", "keep": "x"}


def test_column_mapper_duplicate_detection():
    mapper = ColumnMapper({"a": "b"})
    with pytest.raises(DuplicateHeaderError):
        mapper.apply(row(a="1", b="2"))


def test_default_filler_sets_missing_only():
    filler = DefaultValueFiller({"status": "active"}, {"name", "status"})
    result = filler.apply(row(name="n", status="paused"))
    assert result == {"name": "n", "status": "paused"}
    assert filler.apply(row(name="n"))["status"] == "active"


def test_default_filler_unknown_column_raises():
    with pytest.raises(UnknownColumnError):
        DefaultValueFiller({"ghost": "x"}, {"name"})


def test_expression_cast_int_and_upper():
    cast = ExpressionCast({"age": "int", "city": "upper"}, {"age", "city"})
    result = cast.apply(row(age="42", city="tehran"))
    assert result["age"] == 42
    assert result["city"] == "TEHRAN"


def test_expression_cast_failure_is_typed():
    cast = ExpressionCast({"age": "int"}, {"age"})
    with pytest.raises(TransformerError, match="cast failed"):
        cast.apply(row(age="abc"))


def test_row_filter_drops_non_matching():
    flt = RowFilter(lambda r: int(r["qty"]) > 5)
    assert flt.apply(row(qty="10")) is not None
    assert flt.apply(row(qty="3")) is None


def test_column_dropper_removes_keys():
    dropper = ColumnDropper({"internal_id"})
    assert dropper.apply(row(name="n", internal_id="9")) == {"name": "n"}


def test_transformer_pipeline_full_run():
    transformer = Transformer()
    transformer.add_step(ColumnMapper({"nm": "name"}))
    transformer.add_step(DefaultValueFiller({"role": "user"}, {"name", "role"}))
    transformer.add_step(RowFilter(lambda r: r["name"] != "skip"))
    transformer.add_step(ColumnDropper({"tmp"}))

    rows = [row(nm="a", tmp="t"), row(nm="skip", tmp="t"), row(nm="b")]
    result = transformer.run(rows)

    assert result.dropped_count == 1
    assert len(result.rows) == 2
    assert all("tmp" not in r for r in result.rows)
    assert all(r["role"] == "user" for r in result.rows)
    assert "name" in result.touched_columns


def test_transformer_empty_steps_returns_copy():
    transformer = Transformer()
    source = [row(a="1")]
    result = transformer.run(source)
    assert result.rows == [{"a": "1"}]
    source[0]["a"] = "changed"
    assert result.rows[0]["a"] == "1"
