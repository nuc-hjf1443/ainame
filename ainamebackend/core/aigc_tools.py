import asyncio
import json
import logging
import uuid

import httpx

import settings


logger = logging.getLogger(__name__)
TRANSIENT_HTTP_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.WriteError,
    httpx.WriteTimeout,
)
WAN_MULTIMODAL_MODELS = {"wan2.7-image-pro", "wan2.7-image", "wan2.6-image", "wan2.6-t2i"}
TEXT_TO_IMAGE_ASYNC_MODELS = {"wanx-v1", "wanx2.1-t2i-turbo", "wanx2.1-t2i-plus", "wan2.2-t2i-flash", "wan2.2-t2i-plus", "wan2.5-t2i-preview"}


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


def _extract_dashscope_image_url(data: dict) -> str | None:
    output = data.get("output") or {}
    results = output.get("results") or []
    if results and isinstance(results[0], dict):
        return results[0].get("url") or results[0].get("image_url")
    data_items = data.get("data") or []
    if data_items and isinstance(data_items[0], dict):
        return data_items[0].get("url") or data_items[0].get("image_url")
    return output.get("url") or output.get("image_url") or data.get("url") or data.get("image_url")


def _extract_task_id(data: dict) -> str | None:
    output = data.get("output") or {}
    return output.get("task_id") or data.get("task_id") or data.get("id") or data.get("request_id")


def _extract_task_status(data: dict) -> str | None:
    output = data.get("output") or {}
    return output.get("task_status") or data.get("task_status") or data.get("status")


def _wan_multimodal_parameters(image_model: str) -> dict:
    if image_model == "wan2.6-t2i":
        size = "1280*1280"
    elif image_model.startswith("wan2.7-"):
        size = "1K"
    else:
        size = "1024*1024"

    parameters = {
        "n": 1,
        "size": size,
        "watermark": False,
    }
    if image_model.startswith("wan2.7-"):
        parameters["thinking_mode"] = False
    return parameters


def _parse_wan_response_payload(raw_text: str) -> dict:
    stripped = raw_text.strip()
    if not stripped:
        return {}
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    last_data: dict = {}
    for line in stripped.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        last_data = json.loads(raw)
        if _extract_wan_image_url(last_data):
            return last_data
    return last_data


def is_transient_aigc_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current:
        if isinstance(current, TRANSIENT_HTTP_ERRORS):
            return True
        message = str(current).lower()
        if "incomplete chunked read" in message or "peer closed connection" in message:
            return True
        current = current.__cause__ or current.__context__
    return False


def visual_error_message(exc: BaseException) -> str:
    if is_transient_aigc_error(exc):
        return "视觉生成服务连接中断，请稍后刷新状态或重新生成"
    return str(exc) or "视觉生成失败，请稍后重试"


async def _submit_wan_image_task_once(prompt: str, image_model: str) -> AigcTaskResult:
    headers = {
        "Authorization": f"Bearer {settings.AIGC_API_KEY}",
        "Content-Type": "application/json",
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
        "parameters": _wan_multimodal_parameters(image_model),
    }
    timeout = httpx.Timeout(settings.AIGC_GENERATION_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(settings.AIGC_WAN_IMAGE_URL, headers=headers, json=payload)
        response.raise_for_status()
        request_id = response.headers.get("X-Request-Id") or f"wan_{uuid.uuid4().hex}"
        data = _parse_wan_response_payload(response.text)
        image_url = _extract_wan_image_url(data)
        if image_url:
            return AigcTaskResult(task_id=request_id, status="SUCCESS", image_url=image_url)
        task_id = _extract_task_id(data)
        if task_id:
            return AigcTaskResult(task_id=task_id, status=normalize_aigc_status(_extract_task_status(data)))

    raise ValueError("Wan image generation response missing image URL")


async def _submit_wan_image_task(prompt: str, image_model: str) -> AigcTaskResult:
    attempts = settings.AIGC_NETWORK_RETRY_ATTEMPTS
    for attempt in range(1, attempts + 1):
        try:
            return await _submit_wan_image_task_once(prompt, image_model)
        except Exception as exc:
            if not is_transient_aigc_error(exc) or attempt >= attempts:
                if is_transient_aigc_error(exc):
                    raise RuntimeError(visual_error_message(exc)) from exc
                raise
            logger.warning(
                "Wan image generation stream interrupted; retrying attempt %s/%s",
                attempt,
                attempts,
                exc_info=True,
            )
            await asyncio.sleep(min(2.0, 0.6 * attempt))

    raise RuntimeError("视觉生成服务连接中断，请稍后刷新状态或重新生成")


async def _submit_dashscope_image_task_once(prompt: str, image_model: str) -> AigcTaskResult:
    headers = {
        "Authorization": f"Bearer {settings.AIGC_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": image_model,
        "input": {"prompt": prompt},
        "parameters": {
            "n": 1,
            "size": "1024*1024",
        },
    }
    async with httpx.AsyncClient(timeout=settings.AIGC_TIMEOUT_SECONDS) as client:
        response = await client.post(settings.AIGC_IMAGE_SYNTHESIS_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    task_id = _extract_task_id(data)
    if not task_id:
        raise ValueError("DashScope image generation response missing task_id")
    return AigcTaskResult(
        task_id=task_id,
        status=normalize_aigc_status(_extract_task_status(data)),
        image_url=_extract_dashscope_image_url(data),
    )


async def _submit_dashscope_image_task(prompt: str, image_model: str) -> AigcTaskResult:
    attempts = settings.AIGC_NETWORK_RETRY_ATTEMPTS
    for attempt in range(1, attempts + 1):
        try:
            return await _submit_dashscope_image_task_once(prompt, image_model)
        except Exception as exc:
            if not is_transient_aigc_error(exc) or attempt >= attempts:
                if is_transient_aigc_error(exc):
                    raise RuntimeError(visual_error_message(exc)) from exc
                raise
            logger.warning(
                "DashScope image generation request interrupted; retrying attempt %s/%s",
                attempt,
                attempts,
                exc_info=True,
            )
            await asyncio.sleep(min(2.0, 0.6 * attempt))

    raise RuntimeError("视觉生成服务连接中断，请稍后刷新状态或重新生成")


async def submit_visual_task(prompt: str, image_model: str) -> AigcTaskResult:
    if not _aigc_configured():
        return AigcTaskResult(task_id=f"mock_{uuid.uuid4().hex}", status="PROCESSING")

    if image_model in WAN_MULTIMODAL_MODELS:
        return await _submit_wan_image_task(prompt, image_model)
    if image_model in TEXT_TO_IMAGE_ASYNC_MODELS:
        return await _submit_dashscope_image_task(prompt, image_model)

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

    if settings.AIGC_API_BASE_URL:
        path = settings.AIGC_FETCH_PATH_TEMPLATE.format(task_id=task_id)
        url = settings.AIGC_API_BASE_URL.rstrip("/") + path
    else:
        url = settings.AIGC_TASK_URL_TEMPLATE.format(task_id=task_id)
    headers = {"Authorization": f"Bearer {settings.AIGC_API_KEY}"}

    async with httpx.AsyncClient(timeout=settings.AIGC_TIMEOUT_SECONDS) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    status = normalize_aigc_status(_extract_task_status(data))
    image_url = _extract_dashscope_image_url(data)
    return AigcTaskResult(task_id=task_id, status=status, image_url=image_url)
