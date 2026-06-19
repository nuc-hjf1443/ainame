import uuid

import httpx

import settings


class AigcTaskResult:
    def __init__(self, task_id: str, status: str, image_url: str | None = None):
        self.task_id = task_id
        self.status = status
        self.image_url = image_url


def _aigc_configured() -> bool:
    return bool(settings.AIGC_API_BASE_URL and settings.AIGC_API_KEY)


def normalize_aigc_status(status: str | None) -> str:
    value = (status or "").strip().upper()
    if value in {"SUCCESS", "SUCCEEDED", "COMPLETED", "COMPLETE", "FINISHED"}:
        return "SUCCESS"
    if value in {"FAILED", "FAILURE", "ERROR", "CANCELED", "CANCELLED"}:
        return "FAILED"
    if value in {"PENDING", "QUEUED", "SUBMITTED"}:
        return "PENDING"
    return "PROCESSING"


async def submit_visual_task(prompt: str) -> AigcTaskResult:
    if not _aigc_configured():
        return AigcTaskResult(task_id=f"mock_{uuid.uuid4().hex}", status="PROCESSING")

    url = settings.AIGC_API_BASE_URL.rstrip("/") + settings.AIGC_SUBMIT_PATH
    headers = {"Authorization": f"Bearer {settings.AIGC_API_KEY}"}
    payload = {"prompt": prompt}

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
