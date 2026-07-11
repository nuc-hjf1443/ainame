"""Smoke test for Alibaba Cloud Bailian/DashScope image generation API.

Environment variables:
  DASHSCOPE_API_KEY or ALIBABA_BAILIAN_API_KEY or AIGC_API_KEY
  BAILIAN_IMAGE_MODEL, default: wan2.7-image
  BAILIAN_PAYLOAD_MODE, default: dashscope-multimodal
    project: {"prompt": "...", "model": "..."}
    dashscope: {"model": "...", "input": {"prompt": "..."}, "parameters": {...}}
    dashscope-multimodal: {"model": "...", "input": {"messages": [...]}}
    openai-image: {"model": "...", "prompt": "...", "size": "1024x1024", "n": 1}
    openai-chat: {"model": "...", "messages": [...]}
  BAILIAN_IMAGE_ENDPOINT or AIGC_WAN_IMAGE_URL or AIGC_API_BASE_URL + AIGC_SUBMIT_PATH
  BAILIAN_TASK_ENDPOINT or AIGC_API_BASE_URL + AIGC_FETCH_PATH_TEMPLATE
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent if BACKEND_DIR.name == "ainamebackend" else BACKEND_DIR
DEFAULT_MODEL = "wan2.7-image"
DEFAULT_IMAGE_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DEFAULT_TASK_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
MODEL_PRESETS = {
    "wan2.7-image": {"payload_mode": "dashscope-multimodal", "size": "1K"},
    "wan2.7-image-pro": {"payload_mode": "dashscope-multimodal", "size": "1K"},
    "wan2.6-t2i": {"payload_mode": "dashscope-multimodal", "size": "1280*1280"},
}
LEGACY_MODELS = {
    "wan2.6-image": {"payload_mode": "dashscope-multimodal", "size": "1024*1024"},
    "wanx-v1": {"payload_mode": "dashscope", "size": "1024*1024"},
}
SUPPORTED_MODELS = {**MODEL_PRESETS, **LEGACY_MODELS}


def load_dotenv() -> None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#") or "=" not in value:
            continue
        key, raw = value.split("=", 1)
        key = key.strip()
        raw = raw.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = raw


def get_api_key() -> str:
    api_key = (
        os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("ALIBABA_BAILIAN_API_KEY")
        or os.getenv("AIGC_API_KEY")
        or ""
    ).strip()
    if not api_key:
        raise RuntimeError("Missing API key. Set DASHSCOPE_API_KEY, ALIBABA_BAILIAN_API_KEY, or AIGC_API_KEY.")
    return api_key


def get_submit_url() -> str:
    if os.getenv("BAILIAN_IMAGE_ENDPOINT"):
        return os.getenv("BAILIAN_IMAGE_ENDPOINT", "").strip()

    wan_image_url = os.getenv("AIGC_WAN_IMAGE_URL", "").strip()
    if wan_image_url:
        return wan_image_url

    base_url = os.getenv("AIGC_API_BASE_URL", "").strip()
    submit_path = os.getenv("AIGC_SUBMIT_PATH", "/submit").strip()
    if base_url:
        return base_url.rstrip("/") + "/" + submit_path.lstrip("/")
    return DEFAULT_IMAGE_ENDPOINT


def get_task_url() -> str:
    if os.getenv("BAILIAN_TASK_ENDPOINT"):
        return os.getenv("BAILIAN_TASK_ENDPOINT", "").strip()

    base_url = os.getenv("AIGC_API_BASE_URL", "").strip()
    fetch_path = os.getenv("AIGC_FETCH_PATH_TEMPLATE", "/task/{task_id}").strip()
    if base_url:
        return base_url.rstrip("/") + "/" + fetch_path.lstrip("/")
    return DEFAULT_TASK_ENDPOINT


def parse_task_id(data: dict[str, Any]) -> str:
    if data.get("choices") and isinstance(data["choices"], list):
        return str(data.get("id") or data.get("created") or "sync_chat_completion")

    if data.get("data") and isinstance(data["data"], list):
        return str(data.get("created") or "sync_image_generation")

    output = data.get("output") or {}
    task_id = output.get("task_id") or data.get("task_id") or data.get("id") or data.get("request_id")
    return str(task_id or "stream_image_generation")


def parse_task_status(data: dict[str, Any]) -> str:
    output = data.get("output") or {}
    return str(output.get("task_status") or data.get("status") or "UNKNOWN")


def parse_image_url(data: dict[str, Any]) -> str | None:
    if data.get("data") and isinstance(data["data"], list) and data["data"]:
        first = data["data"][0]
        if isinstance(first, dict):
            return first.get("url") or first.get("image_url")

    output = data.get("output") or {}
    choices = output.get("choices") or []
    if choices and isinstance(choices[0], dict):
        message = choices[0].get("message") or {}
        content = message.get("content") or []
        for item in content:
            if isinstance(item, dict):
                image = item.get("image") or item.get("image_url")
                if isinstance(image, str):
                    return image
                if isinstance(image, dict):
                    return image.get("url")
    results = output.get("results") or []
    if results and isinstance(results[0], dict):
        return results[0].get("url") or results[0].get("image_url")
    return output.get("url") or output.get("image_url") or data.get("url") or data.get("image_url")


def parse_response_payload(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    if not stripped:
        return {}
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    last_data: dict[str, Any] = {}
    for line in stripped.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        data = json.loads(raw)
        if parse_image_url(data):
            return data
        last_data = data
    return last_data


def parse_chat_content(data: dict[str, Any]) -> str | None:
    choices = data.get("choices") or []
    if choices and isinstance(choices[0], dict):
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
    return None


async def submit_task(
    client: httpx.AsyncClient,
    api_key: str,
    endpoint: str,
    model: str,
    prompt: str,
    payload_mode: str,
    image_urls: list[str],
    size: str,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if payload_mode == "dashscope":
        headers["X-DashScope-Async"] = "enable"
        payload = {
            "model": model,
            "input": {"prompt": prompt},
            "parameters": {
                "size": size,
                "n": 1,
            },
        }
    elif payload_mode == "dashscope-multimodal":
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "n": 1,
                "size": size,
                "watermark": False,
            },
        }
        if model.startswith("wan2.7-"):
            payload["parameters"]["thinking_mode"] = False
    elif payload_mode == "openai-image":
        payload = {
            "model": model,
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        }
    elif payload_mode == "openai-chat":
        content = [{"type": "text", "text": prompt}]
        content.extend({"type": "image_url", "image_url": {"url": image_url}} for image_url in image_urls)
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": content},
            ],
        }
    else:
        payload = {
            "prompt": prompt,
            "model": model,
        }

    if payload_mode == "dashscope-multimodal":
        response = await client.post(endpoint, headers=headers, json=payload)
        print(f"submit_status_code={response.status_code}")
        if response.status_code >= 400:
            print(f"submit_response={response.text}")
        response.raise_for_status()
        data = parse_response_payload(response.text)
        image_url = parse_image_url(data)
        if image_url:
            print(f"image_url={image_url}")
        task_id = parse_task_id(data)
        print(f"task_id={task_id}")
        print(f"submit_task_status={parse_task_status(data)}")
        return task_id

    response = await client.post(endpoint, headers=headers, json=payload)
    print(f"submit_status_code={response.status_code}")
    if response.status_code >= 400:
        print(f"submit_response={response.text}")
    response.raise_for_status()
    data = response.json()
    image_url = parse_image_url(data)
    if image_url:
        print(f"image_url={image_url}")
    chat_content = parse_chat_content(data)
    if chat_content:
        print(f"chat_content={chat_content[:300]}")
    task_id = parse_task_id(data)
    print(f"task_id={task_id}")
    print(f"submit_task_status={parse_task_status(data)}")
    return task_id


async def poll_task(client: httpx.AsyncClient, api_key: str, endpoint_template: str, task_id: str) -> None:
    headers = {"Authorization": f"Bearer {api_key}"}
    task_url = endpoint_template.format(task_id=task_id)

    for attempt in range(1, 13):
        await asyncio.sleep(5)
        response = await client.get(task_url, headers=headers)
        print(f"poll_attempt={attempt} status_code={response.status_code}")
        if response.status_code >= 400:
            print(f"poll_response={response.text}")
        response.raise_for_status()
        data = response.json()
        status = parse_task_status(data)
        print(f"task_status={status}")

        if status in {"SUCCEEDED", "SUCCESS", "COMPLETED"}:
            print(f"image_url={parse_image_url(data) or ''}")
            return
        if status in {"FAILED", "FAILURE", "CANCELED", "CANCELLED"}:
            raise RuntimeError(f"Bailian task failed: {data}")

    print("task_status=TIMEOUT")
    print("The API accepted the task, but no final image was returned within 60 seconds.")


async def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Test Alibaba Cloud Bailian image generation API.")
    parser.add_argument("--model", choices=sorted(SUPPORTED_MODELS), default=os.getenv("BAILIAN_IMAGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--prompt", default="A tiny golden bean mascot logo, clean white background, minimal style")
    parser.add_argument("--submit-url", default=get_submit_url())
    parser.add_argument("--task-url", default=get_task_url())
    parser.add_argument("--image-url", action="append", default=[])
    parser.add_argument("--size", default=os.getenv("BAILIAN_IMAGE_SIZE"))
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--all-models", action="store_true", help="Run the prompt against the three recommended models.")
    parser.add_argument(
        "--payload-mode",
        choices=["project", "dashscope", "dashscope-multimodal", "openai-image", "openai-chat"],
        default=os.getenv("BAILIAN_PAYLOAD_MODE"),
    )
    parser.add_argument("--no-poll", action="store_true")
    args = parser.parse_args()

    if args.list_models:
        print("recommended_models=" + ",".join(MODEL_PRESETS))
        print("legacy_models=" + ",".join(LEGACY_MODELS))
        return

    api_key = get_api_key()
    models = list(MODEL_PRESETS) if args.all_models else [args.model]

    async with httpx.AsyncClient(timeout=30) as client:
        for model in models:
            preset = SUPPORTED_MODELS[model]
            payload_mode = args.payload_mode or preset["payload_mode"]
            size = args.size or preset["size"]
            print(f"model={model}")
            print(f"payload_mode={payload_mode}")
            print(f"size={size}")
            print(f"submit_url={args.submit_url}")
            task_id = await submit_task(
                client,
                api_key,
                args.submit_url,
                model,
                args.prompt,
                payload_mode,
                args.image_url,
                size,
            )
            if not args.no_poll and payload_mode != "dashscope-multimodal":
                await poll_task(client, api_key, args.task_url, task_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
