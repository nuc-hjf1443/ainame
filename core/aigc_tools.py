import json
import uuid

import httpx

import settings


class AigcTaskResult:
    def __init__(self, task_id: str, status: str, image_url: str | None = None):
        self.task_id = task_id
        self.status = status
        self.image_url = image_url


def _aigc_configured() -> bool:
    return bool(
        settings.AIGC_API_KEY
        and (settings.AIGC_API_BASE_URL or settings.AIGC_WAN_IMAGE_URL)
    )


def normalize_aigc_status(status: str | None) -> str:
    value = (status or "").strip().upper()
    if value in {"SUCCESS", "SUCCEEDED", "COMPLETED", "COMPLETE", "FINISHED"}:
        return "SUCCESS"
    if value in {"FAILED", "FAILURE", "ERROR", "CANCELED", "CANCELLED"}:
        return "FAILED"
    if value in {"PENDING", "QUEUED", "SUBMITTED"}:
        return "PENDING"
    return "PROCESSING"


def _extract_wan_image_url(data: dict) -> str | None:
    output = data.get("output") or {}
    choices = output.get("choices") or []
    for choice in choices:
        message = choice.get("message") or {}
        for item in message.get("content") or []:
            if not isinstance(item, dict):
                continue
            image = item.get("image") or item.get("image_url")
            if isinstance(image, str):
                return image
            if isinstance(image, dict) and image.get("url"):
                return image["url"]
    return None


async def _submit_wan_image_task(prompt: str, image_model: str) -> AigcTaskResult:
    headers = {
        "Authorization": f"Bearer {settings.AIGC_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable",
    }
    payload = {
        "model": image_model,
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
            "size": "1024*1024",
            "enable_interleave": True,
            "stream": True,
        },
    }
    timeout = httpx.Timeout(settings.AIGC_GENERATION_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", settings.AIGC_WAN_IMAGE_URL, headers=headers, json=payload) as response:
            response.raise_for_status()
            request_id = response.headers.get("X-Request-Id") or f"wan_{uuid.uuid4().hex}"
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw or raw == "[DONE]":
                    continue
                image_url = _extract_wan_image_url(json.loads(raw))
                if image_url:
                    return AigcTaskResult(task_id=request_id, status="SUCCESS", image_url=image_url)

    raise ValueError("Wan image generation response missing image URL")


async def submit_visual_task(prompt: str, image_model: str) -> AigcTaskResult:
    if not _aigc_configured():
        return AigcTaskResult(task_id=f"mock_{uuid.uuid4().hex}", status="PROCESSING")

    if image_model == "wan2.6-image":
        return await _submit_wan_image_task(prompt, image_model)

    url = settings.AIGC_API_BASE_URL.rstrip("/") + settings.AIGC_SUBMIT_PATH
    headers = {"Authorization": f"Bearer {settings.AIGC_API_KEY}"}
    payload = {
        "prompt": prompt,
        "model": image_model,
    }

    async with httpx.AsyncClient(timeout=settings.AIGC_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    task_id = data.get("task_id") or data.get("id")
    if not task_id:
        raise ValueError("AIGC submit response missing task_id")
    return AigcTaskResult(task_id=task_id, status=normalize_aigc_status(data.get("status")))


async def fetch_visual_task(task_id: str) -> AigcTaskResult:
    if task_id.startswith("mock_") or not _aigc_configured():
        return AigcTaskResult(task_id=task_id, status="PROCESSING")

    path = settings.AIGC_FETCH_PATH_TEMPLATE.format(task_id=task_id)
    url = settings.AIGC_API_BASE_URL.rstrip("/") + path
    headers = {"Authorization": f"Bearer {settings.AIGC_API_KEY}"}

    async with httpx.AsyncClient(timeout=settings.AIGC_TIMEOUT_SECONDS) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    status = normalize_aigc_status(data.get("status"))
    image_url = data.get("image_url") or data.get("url")
    return AigcTaskResult(task_id=task_id, status=status, image_url=image_url)
