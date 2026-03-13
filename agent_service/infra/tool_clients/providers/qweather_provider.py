"""QWeather (和风天气) provider for get_weather tool."""

from __future__ import annotations

import gzip
import json
import os
import urllib.parse
import urllib.request
from typing import Any

from domain.tools.types import ToolResult
from infra.tool_clients.provider_base import ProviderConfig, ProviderResult, ResultType, ToolProvider


def _http_get_json(url: str, timeout: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req_headers = {"User-Agent": "agent-service/0.1", "Accept-Encoding": "gzip"}
    if headers:
        req_headers.update(headers)
    last_err: Exception | None = None
    for _ in range(2):
        req = urllib.request.Request(url, headers=req_headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if (resp.headers.get("Content-Encoding") or "").lower() == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("http_get_json_failed")


class QWeatherProvider(ToolProvider):
    """QWeather (和风天气) API provider for weather queries."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_key = os.getenv("QWEATHER_API_KEY", "").strip()
        self.api_host = os.getenv("QWEATHER_API_HOST", "").strip()
        self.geo_host = os.getenv("QWEATHER_GEO_HOST", "").strip()
        self.timeout = config.timeout

    def _lookup_city_id(self, city: str) -> str | None:
        base_host = self.geo_host or "geoapi.qweather.com"
        url = f"https://{base_host}/geo/v2/city/lookup?" + urllib.parse.urlencode({"location": city})
        headers = {"X-QW-Api-Key": self.api_key}
        body = _http_get_json(url, timeout=self.timeout, headers=headers)
        loc = body.get("location") or []
        if not loc:
            return None
        return str(loc[0].get("id") or "") or None

    def _get_now(self, city_id: str) -> dict[str, Any]:
        base_host = self.api_host or "devapi.qweather.com"
        url = f"https://{base_host}/v7/weather/now?" + urllib.parse.urlencode({"location": city_id})
        headers = {"X-QW-Api-Key": self.api_key}
        return _http_get_json(url, timeout=self.timeout, headers=headers)

    def _get_3d(self, city_id: str) -> dict[str, Any]:
        base_host = self.api_host or "devapi.qweather.com"
        url = f"https://{base_host}/v7/weather/3d?" + urllib.parse.urlencode({"location": city_id})
        headers = {"X-QW-Api-Key": self.api_key}
        return _http_get_json(url, timeout=self.timeout, headers=headers)

    def execute(self, **kwargs) -> ProviderResult:
        """Fetch weather for the given city."""
        if not self.api_key:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="qweather_api_key_missing",
            )

        city = kwargs.get("city", "")
        if not city:
            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error="missing_city",
            )

        try:
            city_id = self._lookup_city_id(city)
            if not city_id:
                return ProviderResult(
                    ok=False,
                    data=None,
                    provider_name=self.config.name,
                    error="city_not_found",
                )

            now_data = self._get_now(city_id)
            daily_data = self._get_3d(city_id)

            now = now_data.get("now", {})
            dailies = daily_data.get("daily") or []
            today = dailies[0] if len(dailies) > 0 else {}
            tomorrow = dailies[1] if len(dailies) > 1 else {}

            text = (
                f"{city}当前：{now.get('text', '未知')}，{now.get('temp', '-')}°C（体感{now.get('feelsLike', '-')}°C），"
                f"湿度{now.get('humidity', '-')}%，风{now.get('windDir', '-')}{now.get('windScale', '-')}级。"
                f"今日预报：{today.get('textDay', '-')}，{today.get('tempMin', '-')}~{today.get('tempMax', '-')}°C；"
                f"明日预报：{tomorrow.get('textDay', '-')}，{tomorrow.get('tempMin', '-')}~{tomorrow.get('tempMax', '-')}°C。"
            )

            result = ToolResult(
                ok=True,
                text=text,
                raw={
                    "provider": "qweather",
                    "city": city,
                    "city_id": city_id,
                    "now": now,
                    "daily_3d": dailies[:3],
                    "update_time": now_data.get("updateTime"),
                    "fx_link": now_data.get("fxLink"),
                },
            )

            return ProviderResult(
                ok=True,
                data=result,
                provider_name=self.config.name,
                result_type=ResultType.SUMMARIZED,
            )

        except Exception as e:
            error_str = str(e)
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                error_code = "timeout"
            else:
                error_code = f"qweather_error:{e}"

            return ProviderResult(
                ok=False,
                data=None,
                provider_name=self.config.name,
                error=error_code,
            )

    def health_check(self) -> bool:
        """Check if QWeather API key is available."""
        return bool(self.api_key)
