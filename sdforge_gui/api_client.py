"""HTTP client for interacting with the Stable Diffusion Forge API."""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests

from .models import LoraInfo

logger = logging.getLogger(__name__)


@dataclass
class GeneratedImage:
    """Container describing an image returned by the API."""

    data: bytes
    seed: int
    info: Dict[str, Any]


class StableDiffusionAPIError(RuntimeError):
    """Exception raised when the Stable Diffusion Forge API returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class StableDiffusionClient:
    """A thin wrapper around the Stable Diffusion Forge HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:7860") -> None:
        self.base_url = base_url

    @property
    def base_url(self) -> str:
        return self._base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        if not value:
            raise ValueError("Base URL cannot be empty")
        self._base_url = value.rstrip("/")

    # --- helper methods -------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        logger.debug("Request %s %s", method, path)
        response = requests.request(method, self._url(path), json=json, params=params, timeout=120)
        if not response.ok:
            logger.error("API request failed (%s): %s", response.status_code, response.text)
            raise StableDiffusionAPIError(response.text, status_code=response.status_code)
        return response.json()

    # --- metadata endpoints --------------------------------------------
    def _coerce_strings(self, values: Iterable[Any]) -> List[str]:
        result: List[str] = []
        for value in values:
            if value is None:
                continue
            if not isinstance(value, str):
                value = str(value)
            trimmed = value.strip()
            if trimmed:
                result.append(trimmed)
        return result

    def _extract_names(self, items: Sequence[Any], *keys: str) -> List[str]:
        names: List[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            for key in keys:
                value = item.get(key)
                if value:
                    names.append(str(value))
                    break
        return self._coerce_strings(names)

    def list_checkpoints(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-models")
        if isinstance(data, list):
            return self._extract_names(data, "title", "model_name", "filename", "name")
        return []

    def list_vaes(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-vae")
        if isinstance(data, list):
            return self._extract_names(data, "model_name", "title", "filename", "name")
        return []

    def list_text_encoders(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-embeddings")
        names: List[str] = []
        if isinstance(data, dict):
            for key in ("loaded", "skipped"):
                group = data.get(key, {})
                if isinstance(group, dict):
                    names.extend(group.keys())
        elif isinstance(data, list):
            names.extend(item for item in data if isinstance(item, str))
        return self._coerce_strings(sorted(set(names)))

    def list_samplers(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/samplers")
        if isinstance(data, list):
            return self._extract_names(data, "name", "title")
        return []

    def list_schedulers(self) -> List[str]:
        try:
            data = self._request("GET", "/sdapi/v1/schedulers")
        except StableDiffusionAPIError as error:
            if error.status_code == 404:
                logger.info("Schedulers endpoint unavailable; returning empty list")
                return []
            raise
        if isinstance(data, list):
            return self._extract_names(data, "name", "title")
        return []

    def list_loras(self) -> List[LoraInfo]:
        data = self._request("GET", "/sdapi/v1/loras")
        results: List[LoraInfo] = []
        if isinstance(data, list):
            seen: set[str] = set()
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name") or entry.get("model_name") or entry.get("alias")
                if not name:
                    continue
                normalized = str(name).strip()
                if not normalized:
                    continue
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                alias = entry.get("alias")
                path = entry.get("path") or entry.get("model_path")
                results.append(
                    LoraInfo(
                        name=normalized,
                        alias=str(alias).strip() if isinstance(alias, str) and alias.strip() else None,
                        path=str(path).strip() if isinstance(path, str) and path.strip() else None,
                    )
                )
        return results

    def get_options(self) -> Dict[str, Any]:
        data = self._request("GET", "/sdapi/v1/options")
        if isinstance(data, dict):
            return data
        logger.warning("Unexpected payload for /options endpoint: %s", type(data))
        return {}

    # --- generation -----------------------------------------------------
    def text_to_image(self, payload: Dict[str, Any]) -> List[GeneratedImage]:
        """Trigger a txt2img generation request and return resulting images."""

        data = self._request("POST", "/sdapi/v1/txt2img", json=payload)
        image_list: List[str] = list(data.get("images", []))
        result: List[GeneratedImage] = []
        info = data.get("info")
        if isinstance(info, str):
            try:
                info = json.loads(info)
            except Exception:  # pragma: no cover - best effort decoding
                info = {"raw": info}
        if not isinstance(info, dict):
            info = {}

        seeds = info.get("all_seeds")
        if not isinstance(seeds, list):
            seeds = [payload.get("seed", -1)] * max(1, len(image_list))

        for index, image_base64 in enumerate(image_list):
            image_bytes = base64.b64decode(image_base64.split(",")[-1])
            seed = seeds[index] if index < len(seeds) else payload.get("seed", -1)
            result.append(GeneratedImage(data=image_bytes, seed=seed, info=info))
        return result

    # --- progress -------------------------------------------------------
    def get_progress(self) -> Dict[str, Any]:
        return self._request("GET", "/sdapi/v1/progress", params={"skip_current_image": True})
