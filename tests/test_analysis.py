import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.analysis import analyze_image, extract_json, combine_with_date


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


class TestAnalyzeImage:
    def _make_mock_response(self, content: str):
        choice = MagicMock()
        choice.message.content = content
        choice.message.reasoning_content = None
        return MagicMock(choices=[choice])

    def _write_image(self, data: bytes = b"\x89PNG\r\n\x1a\n"):
        f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        f.write(data)
        f.close()
        return f.name

    def test_valid_json(self):
        resp = self._make_mock_response('{"length_min": 35, "start_time": "08:15", "end_time": "08:50", "start_pos": "A", "end_pos": "B", "bike_id": "TRE00410", "serial": "SN123456"}')
        with patch("app.analysis.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = resp
            result = analyze_image(self._write_image())
        assert result["length_min"] == 35
        assert result["bike_id"] == "TRE00410"

    def test_backtick_wrapped_json(self):
        resp = self._make_mock_response('```\n{"length_min": 42, "start_time": "09:00", "end_time": "09:30", "start_pos": "X", "end_pos": "Y", "bike_id": "TRE00411", "serial": "SN123457"}\n```')
        with patch("app.analysis.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = resp
            result = analyze_image(self._write_image())
        assert result["length_min"] == 42

    def test_empty_choices_raises(self):
        resp = MagicMock(choices=[])
        with patch("app.analysis.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = resp
            with pytest.raises(ValueError, match="No choices"):
                analyze_image(self._write_image())

    def test_empty_content_raises(self):
        choice = MagicMock()
        choice.message.content = None
        choice.message.reasoning_content = None
        resp = MagicMock(choices=[choice])
        with patch("app.analysis.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = resp
            with pytest.raises(ValueError, match="empty content"):
                analyze_image(self._write_image())

    def test_invalid_json_raises(self):
        resp = self._make_mock_response("not json at all")
        with patch("app.analysis.OpenAI") as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = resp
            with pytest.raises(ValueError, match="JSON parse failed"):
                analyze_image(self._write_image())
