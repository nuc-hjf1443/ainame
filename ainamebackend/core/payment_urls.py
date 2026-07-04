from fastapi import Request

import settings


def alipay_notify_url(request: Request) -> str:
    return settings.ALIPAY_NOTIFY_URL or str(request.url_for("alipay_notify"))


def alipay_return_url(request: Request) -> str:
    return settings.ALIPAY_RETURN_URL or str(request.url_for("alipay_return"))
