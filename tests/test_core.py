from pathlib import Path
from types import SimpleNamespace

import pytest

from order_number_lens.core import (
    OCRLine, PassResult, collect_images, evaluate_passes, extract_candidates,
    extract_lines, flag_batch_duplicates,
)


def test_label_and_long_number_same_line():
    result = extract_candidates([OCRLine("订单号：１２３４５６７８９０１２", 0.94)])
    assert result.candidates == ("123456789012",)


def test_label_and_long_number_next_line():
    result = extract_candidates([OCRLine("Order No:", 0.9), OCRLine("1234 5678 9012 3456", 0.8)])
    assert result.candidates == ("1234567890123456",)
    assert result.best_score == 0.8


def test_unlabeled_phone_number_is_not_silently_used():
    result = extract_candidates([OCRLine("Phone 13912345678", 0.99)])
    assert result.candidates == ()


def test_no_partial_capture_of_too_long_number():
    result = extract_candidates([OCRLine("Order No: " + "1" * 26, 0.9)])
    assert result.candidates == ()


def test_agreement_is_only_candidate_not_verified():
    item = PassResult(("123456789012",), ("Order No 123456789012",), 0.9)
    output = evaluate_passes(item, item, expected_length=12)
    assert output["status"] == "consistent_candidate"
    assert "verify" in output["reason"]


def test_missing_digit_or_disagreement_requires_review():
    a = PassResult(("123456789012",), (), 0.9)
    b = PassResult(("12345678012",), (), 0.8)
    output = evaluate_passes(a, b, expected_length=12)
    assert output["status"] == "review_needed"
    assert output["candidate"] is None


def test_expected_length_rejects_short_candidate():
    a = PassResult(("1234567890",), (), 0.9)
    output = evaluate_passes(a, a, expected_length=12)
    assert output["candidate"] is None


def test_extract_lines_from_rapidocr_shape():
    lines = extract_lines(SimpleNamespace(txts=("Order No", "123456789012"), scores=(0.9, 0.8)))
    assert lines[1].text == "123456789012"


def test_duplicate_batch_candidate_requires_review():
    rows = [{"candidate": "123", "status": "consistent_candidate", "reason": "ok"},
            {"candidate": "123", "status": "consistent_candidate", "reason": "ok"}]
    flag_batch_duplicates(rows)
    assert all(row["status"] == "review_needed" for row in rows)


def test_collect_images_nonrecursive_and_deduplicated(tmp_path: Path):
    image = tmp_path / "a.png"
    image.write_bytes(b"not opened here")
    nested = tmp_path / "child"
    nested.mkdir()
    (nested / "b.png").write_bytes(b"not opened here")
    assert collect_images([tmp_path, image]) == [image.resolve()]
    with pytest.raises(ValueError, match="Not a supported image"):
        collect_images([nested / "missing"])
