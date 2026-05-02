import base64
import json
import logging
from datetime import datetime, time
from typing import Any, cast
from zoneinfo import ZoneInfo

from openai import OpenAI

from .config import LM_STUDIO_MODEL, LM_STUDIO_URL

logger = logging.getLogger(__name__)

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "length_min": {"type": "integer"},
        "start_time": {"type": "string"},
        "end_time": {"type": "string"},
        "start_pos": {"type": "string"},
        "end_pos": {"type": "string"},
        "bike_id": {"type": "string"},
        "serial": {"type": "string"},
    },
    "required": [
        "length_min",
        "start_time",
        "end_time",
        "start_pos",
        "end_pos",
        "bike_id",
        "serial",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a bike trip data extractor. "
    "Analyze the uploaded image of a city bike trip summary screen and extract the data as JSON. "
    "The image shows a trip summary with duration (i.e. length_min), start/end times, start/end locations, "
    "bike ID, and serial number. "
    "Return times as HH:MM only. "
    "Do not invent a date. "
    "Return ONLY valid JSON with these fields: "
    "length_min, start_time, end_time, start_pos, end_pos, bike_id, serial."
)


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return cast("dict[str, Any]", json.loads(text))


def analyze_image(image_path: str) -> dict[str, Any]:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    client = OpenAI(base_url=str(LM_STUDIO_URL), api_key="lm-studio")

    response = client.chat.completions.create(
        model=str(LM_STUDIO_MODEL),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the trip data from this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}",
                        },
                    },
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "bike_trip_data",
                "schema": JSON_SCHEMA,
            },
        },
        temperature=0,
    )

    if not response.choices:
        msg = f"No choices in response: {response!r}"
        raise ValueError(msg)

    message = response.choices[0].message

    raw = message.content or getattr(message, "reasoning_content", None)
    logger.debug("Model response: %s", raw)

    if not raw:
        msg = (
            f"Model returned empty content and no reasoning_content. "
            f"Full message: {message!r}. Full response: {response!r}"
        )
        raise ValueError(msg)

    raw = raw.strip()

    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        return cast("dict[str, Any]", json.loads(raw))
    except Exception as e:
        msg = f"JSON parse failed. Raw content was: {raw!r}. Full message: {message!r}"
        raise ValueError(msg) from e


def combine_with_date(time_str: str) -> str:
    """Combine a HH:MM time string with today's date, returning ISO 8601."""
    hour, minute = map(int, time_str.split(":"))
    dt = datetime.combine(
        datetime.now(tz=ZoneInfo("Europe/Helsinki")).date(),
        time(hour, minute),
        tzinfo=ZoneInfo("Europe/Helsinki"),
    )
    return dt.isoformat()
