import base64
import json
from datetime import date
from openai import OpenAI
from .config import LM_STUDIO_MODEL, LM_STUDIO_URL


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "duration": {"type": "integer"},
        "start_time": {"type": "string"},
        "end_time": {"type": "string"},
        "start_pos": {"type": "string"},
        "end_pos": {"type": "string"},
        "bike_id": {"type": "string"},
        "serial": {"type": "string"},
    },
    "required": [
        "duration",
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
    "The image shows a trip summary with duration, start/end times, start/end locations, "
    "bike ID, and serial number. "
    "Use today's date when combining with the extracted time to form full ISO 8601 timestamps. "
    "Return ONLY valid JSON matching the schema. Do not include any other text."
)


def analyze_image(image_path: str):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")

    response = client.chat.completions.create(
        model=LM_STUDIO_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the trip data from this image.",
                    },
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

    raw = response.choices[0].message.content
    return json.loads(raw)


def combine_with_date(time_str: str) -> str:
    today = date.today().isoformat()
    return f"{today}T{time_str}:00"
