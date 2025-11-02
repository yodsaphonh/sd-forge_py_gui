"""Tag completion utilities for prompt editors."""
from __future__ import annotations

import csv
import gzip
import json
import os
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import TextIO


def _iter_default_search_paths() -> Iterator[Path]:
    """Yield directories that may contain tag completion data."""

    env_path = os.getenv("SDFORGE_TAGCOMPLETE_PATH")
    if env_path:
        for entry in env_path.split(os.pathsep):
            candidate = Path(entry).expanduser()
            if candidate.is_dir():
                yield candidate

    root = Path(__file__).resolve().parent
    data_dir = root / "data" / "tagcomplete"
    if data_dir.is_dir():
        yield data_dir

    project_root = root.parent
    candidates = [
        project_root / "tagcomplete",
        project_root / "data" / "tagcomplete",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            yield candidate


class TagRepository:
    """Loads tags compatible with the a1111 tag autocomplete format."""

    def __init__(self, search_paths: Sequence[Path] | None = None) -> None:
        self._search_paths = list(search_paths) if search_paths else list(_iter_default_search_paths())
        self._tags: list[str] = []
        self.reload()

    # ------------------------------------------------------------------
    @property
    def tags(self) -> list[str]:
        return self._tags

    # ------------------------------------------------------------------
    def reload(self) -> None:
        seen: set[str] = set()
        aggregated: list[str] = []

        for base_path in self._search_paths:
            if not base_path.is_dir():
                continue
            for file_path in sorted(base_path.rglob("*")):
                if not file_path.is_file():
                    continue
                for tag in self._load_file(file_path):
                    normalized = tag.strip()
                    if not normalized:
                        continue
                    lowered = normalized.lower()
                    if lowered in seen:
                        continue
                    seen.add(lowered)
                    aggregated.append(normalized)

        aggregated.sort(key=str.lower)
        self._tags = aggregated

    # ------------------------------------------------------------------
    def _load_file(self, path: Path) -> Iterable[str]:
        suffix = path.suffix.lower()
        if suffix == ".json":
            yield from self._load_json(path)
        elif suffix == ".csv":
            yield from self._load_csv(path)
        elif suffix == ".txt":
            yield from self._load_txt(path)
        elif suffix == ".gz":
            yield from self._load_compressed(path)

    # ------------------------------------------------------------------
    def _load_compressed(self, path: Path) -> Iterable[str]:
        nested_suffix = path.stem.split(".")[-1].lower()
        with gzip.open(path, mode="rt", encoding="utf-8", newline="") as handle:
            if nested_suffix == "csv":
                yield from self._load_csv(handle)
            elif nested_suffix == "json":
                yield from self._load_json(handle)
            else:
                for line in handle:
                    tag = line.strip()
                    if tag:
                        yield tag

    # ------------------------------------------------------------------
    def _load_json(self, source: Path | TextIO | Iterable[str]) -> Iterable[str]:
        if isinstance(source, Path):
            raw = source.read_text(encoding="utf-8")
        elif hasattr(source, "read"):
            raw = source.read()
        else:
            raw = "".join(source)

        data = json.loads(raw)
        if isinstance(data, Mapping):
            for key, value in data.items():
                if isinstance(key, str):
                    yield key
                if isinstance(value, str):
                    yield value
                elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    for entry in value:
                        if isinstance(entry, str):
                            yield entry
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            for entry in data:
                if isinstance(entry, str):
                    yield entry
        elif isinstance(data, str):
            yield data

    # ------------------------------------------------------------------
    def _load_csv(self, source: Path | TextIO) -> Iterable[str]:
        if isinstance(source, Path):
            handle = source.open("r", encoding="utf-8", newline="")
            close_handle = True
        else:
            handle = source
            close_handle = False

        try:
            reader = csv.reader(handle)
            try:
                first_row = next(reader)
            except StopIteration:
                return

            normalized_headers = [cell.strip().lower() for cell in first_row]
            has_header = any(header in {"tag", "name", "aliases", "alias"} for header in normalized_headers)

            if has_header:
                headers = normalized_headers
            else:
                headers = []
                yield from self._consume_csv_row(first_row, 0, None)

            if headers:
                tag_index = 0
                alias_index: int | None = None
                for idx, header in enumerate(headers):
                    if header in {"tag", "name"}:
                        tag_index = idx
                    if header in {"alias", "aliases"}:
                        alias_index = idx
            else:
                tag_index = 0
                alias_index = None

            for row in reader:
                yield from self._consume_csv_row(row, tag_index, alias_index)
        finally:
            if close_handle:
                handle.close()

    def _consume_csv_row(
        self, row: Sequence[str], tag_index: int, alias_index: int | None
    ) -> Iterator[str]:
        if not row:
            return
        if tag_index < len(row):
            tag = row[tag_index].strip()
            if tag:
                yield tag
        if alias_index is not None and alias_index < len(row):
            aliases = row[alias_index]
            for alias in _split_aliases(aliases):
                yield alias

    # ------------------------------------------------------------------
    def _load_txt(self, path: Path) -> Iterable[str]:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                tag = line.strip()
                if not tag:
                    continue
                if "," in tag:
                    tag = tag.split(",", 1)[0].strip()
                yield tag


def _split_aliases(value: str) -> Iterator[str]:
    for part in value.replace(";", ",").split(","):
        stripped = part.strip()
        if stripped:
            yield stripped
