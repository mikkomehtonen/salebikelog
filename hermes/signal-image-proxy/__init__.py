import json
import mimetypes
import os
from pathlib import Path

import requests


BACKEND_URL = os.environ.get(
    "BIKE_TRIP_BACKEND_URL",
    "http://127.0.0.1:8000/api/trips/upload",
)

FORWARD_SCHEMA = {
    "name": "forward_bike_trip_image",
    "description": "Send an image file to the city bike backend upload endpoint.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Local filesystem path to the image attachment.",
            }
        },
        "required": ["image_path"],
        "additionalProperties": False,
    },
}


def forward_bike_trip_image(args: dict, **kwargs) -> str:
    image_path = args.get("image_path", "")
    path = Path(image_path)

    if not image_path:
        return json.dumps({
            "ok": False,
            "error": "image_path missing",
            "extra_kwargs": list(kwargs.keys()),
        }, ensure_ascii=False)

    if not path.exists():
        return json.dumps({
            "ok": False,
            "error": f"file does not exist: {image_path}",
            "extra_kwargs": list(kwargs.keys()),
        }, ensure_ascii=False)

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "application/octet-stream"

    try:
        with path.open("rb") as f:
            response = requests.post(
                BACKEND_URL,
                files={"file": (path.name, f, mime_type)},
                timeout=180,
            )

        response.raise_for_status()

        return json.dumps({
            "ok": True,
            "status_code": response.status_code,
            "backend_response": response.json(),
        }, ensure_ascii=False)

    except requests.HTTPError as e:
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text if e.response is not None else str(e)

        return json.dumps({
            "ok": False,
            "status_code": e.response.status_code if e.response is not None else None,
            "error": body,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": str(e),
        }, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(
        name="forward_bike_trip_image",
        toolset="signal-image",
        schema=FORWARD_SCHEMA,
        handler=forward_bike_trip_image,
    )
