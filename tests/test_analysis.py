import json
import pytest

from app.analysis import extract_json, combine_with_date


class TestExtractJson:
    def test_plain_json(self):
        raw = '{"length_min": 35, "start_time": "08:15", "end_time": "08:50", "start_pos": "A", "end_pos": "B", "bike_id": "TRE00410", "serial": "SN123456"}'
        result = extract_json(raw)
        assert result["length_min"] == 35
        assert result["bike_id"] == "TRE00410"

    def test_strips_backticks(self):
        raw = '```json\n{"length_min": 35, "start_time": "08:15", "end_time": "08:50", "start_pos": "A", "end_pos": "B", "bike_id": "TRE00410", "serial": "SN123456"}\n```'
        result = extract_json(raw)
        assert result["length_min"] == 35

    def test_strips_backticks_no_lang(self):
        raw = '```\n{"length_min": 35, "start_time": "08:15", "end_time": "08:50", "start_pos": "A", "end_pos": "B", "bike_id": "TRE00410", "serial": "SN123456"}\n```'
        result = extract_json(raw)
        assert result["length_min"] == 35

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            extract_json("not valid json {")

    def test_whitespace_stripping(self):
        raw = '  \n  {"length_min": 35, "start_time": "08:15", "end_time": "08:50", "start_pos": "A", "end_pos": "B", "bike_id": "TRE00410", "serial": "SN123456"}  \n  '
        result = extract_json(raw)
        assert result["length_min"] == 35


class TestCombineWithDate:
    def test_produces_iso_format(self):
        result = combine_with_date("08:15")
        assert "T08:15:00" in result
        assert "Europe/Helsinki" in result or "+03:00" in result

    def test_different_times(self):
        result = combine_with_date("23:59")
        assert "T23:59:00" in result

    def test_zero_time(self):
        result = combine_with_date("00:00")
        assert "T00:00:00" in result
