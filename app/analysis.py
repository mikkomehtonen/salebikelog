import base64
import json
import ollama
from datetime import date
from .config import OLLAMA_MODEL


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

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": "Extract the trip data from this image.",
                "images": [image_data],
            },
        ],
        format=JSON_SCHEMA,
        options={
            "temperature": 0,
        },
    )

    raw = response["message"]["content"]
    return json.loads(raw)


def combine_with_date(time_str: str) -> str:
    today = date.today().isoformat()
    return f"{today}T{time_str}:00"
