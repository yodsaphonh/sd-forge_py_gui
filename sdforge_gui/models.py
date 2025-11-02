"""Domain models shared between the GUI and the Stable Diffusion client."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LoraInfo:
    """Metadata returned by the API for an available LoRA."""

    name: str
    alias: Optional[str] = None
    path: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.alias and self.alias.lower() != self.name.lower():
            return f"{self.alias} ({self.name})"
        return self.name

    @property
    def prompt_name(self) -> str:
        return self.alias or self.name


@dataclass
class LoraSelection:
    """Represents a LoRA selection made by the user."""

    name: str
    alias: Optional[str] = None
    weight: float = 1.0

    def prompt_tag(self) -> str:
        weight_str = f"{self.weight:.2f}".rstrip("0").rstrip(".")
        if not weight_str:
            weight_str = "1"
        return f"<lora:{self.alias or self.name}:{weight_str}>"

    def to_script_args(self) -> list[object]:
        return [self.name, float(self.weight)]


@dataclass
class GenerationRequest:
    """Represents parameters for a text-to-image request."""

    prompt: str = ""
    negative_prompt: str = ""
    steps: int = 20
    sampler: str = "Euler a"
    scheduler: Optional[str] = None
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 512
    batch_size: int = 1
    batch_count: int = 1
    seed: int = -1
    subseed: Optional[int] = None
    clip_skip: Optional[int] = None
    checkpoint: Optional[str] = None
    vae: Optional[str] = None
    text_encoder: Optional[str] = None
    gpu_weights_mb: Optional[int] = None
    loras: List[LoraSelection] = field(default_factory=list)
    additional_options: Dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, object]:
        prompt_segments: list[str] = []
        if self.prompt:
            prompt_segments.append(self.prompt)
        if self.loras:
            lora_tags = " ".join(selection.prompt_tag() for selection in self.loras)
            prompt_segments.append(lora_tags)

        payload: Dict[str, object] = {
            "prompt": "\n".join(segment for segment in prompt_segments if segment),
            "negative_prompt": self.negative_prompt,
            "steps": self.steps,
            "sampler_name": self.sampler,
            "cfg_scale": self.cfg_scale,
            "width": self.width,
            "height": self.height,
            "batch_size": self.batch_size,
            "n_iter": self.batch_count,
            "seed": self.seed,
        }
        if self.scheduler:
            payload["scheduler"] = self.scheduler
        if self.subseed is not None:
            payload["subseed"] = self.subseed
        if self.clip_skip is not None:
            payload.setdefault("override_settings", {})["CLIP_stop_at_last_layers"] = self.clip_skip
        if self.checkpoint:
            payload["override_settings"] = payload.get("override_settings", {})
            payload["override_settings"]["sd_model_checkpoint"] = self.checkpoint
        if self.vae:
            payload.setdefault("override_settings", {})["sd_vae"] = self.vae
        if self.text_encoder:
            payload.setdefault("override_settings", {})["sd_text_encoder"] = self.text_encoder
        if self.gpu_weights_mb is not None:
            payload.setdefault("override_settings", {})["gpu_weights_limit_mb"] = self.gpu_weights_mb
        if self.loras:
            payload.setdefault("alwayson_scripts", {})["LoRA"] = {
                "args": [selection.to_script_args() for selection in self.loras]
            }
        payload.setdefault("override_settings", {}).update(self.additional_options)
        return payload
