from __future__ import annotations

import time
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class HttpError(Exception):
    pass


def polite_delay(seconds: float = 1.0) -> None:
    time.sleep(seconds)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(HttpError),
)
def get(url: str, *, timeout: float = 20.0, headers: Optional[dict] = None) -> requests.Response:
    h = {**DEFAULT_HEADERS, **(headers or {})}
    try:
        resp = requests.get(url, headers=h, timeout=timeout)
    except requests.RequestException as exc:
        raise HttpError(str(exc))
    if resp.status_code >= 400:
        raise HttpError(f"GET {url} failed: {resp.status_code}")
    return resp


