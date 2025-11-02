"""HTTP client for interacting with the Stable Diffusion Forge API."""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class GeneratedImage:
    """Container describing an image returned by the API."""

    data: bytes
    seed: int
    info: Dict[str, Any]


class StableDiffusionAPIError(RuntimeError):
    """Exception raised when the Stable Diffusion Forge API returns an error."""


class StableDiffusionClient:
    """A thin wrapper around the Stable Diffusion Forge HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:7860") -> None:
        self.base_url = base_url.rstrip("/")

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
            raise StableDiffusionAPIError(response.text)
        return response.json()

    # --- metadata endpoints --------------------------------------------
    def list_checkpoints(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-models")
        return [item.get("title", item.get("model_name")) for item in data]

    def list_vaes(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-vae")
        return [item.get("model_name", item.get("title")) for item in data]

    def list_text_encoders(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/sd-embeddings")
        return list(data.keys())

    def list_samplers(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/samplers")
        return [item.get("name") for item in data]

    def list_schedulers(self) -> List[str]:
        data = self._request("GET", "/sdapi/v1/schedulers")
        return [item.get("name") for item in data]

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
