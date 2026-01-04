"""Project-level configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

CONFIG_FILENAME = ".air780e.json"


def default_config_path(base: Path | None = None) -> Path:
    """Return the path where the project config is stored."""
    base_path = base or Path.cwd()
    return base_path / CONFIG_FILENAME


class ProjectConfig(BaseModel):
    """Typed configuration stored per project."""

    serial_port: str = Field(..., description="Serial device path for this project")

    model_config = {"frozen": True, "str_strip_whitespace": True}

    @model_validator(mode="after")
    def validate_serial_port(self) -> "ProjectConfig":
        if not self.serial_port:
            raise ValueError("serial_port must not be empty")
        return self

    def save(self, path: Path) -> Path:
        """Persist the config to disk, creating parents as needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(), indent=2) + "\n")
        return path

    @classmethod
    def load(cls, path: Path) -> "ProjectConfig":
        data = json.loads(path.read_text())
        return cls(**data)


__all__ = ["ProjectConfig", "ValidationError", "default_config_path"]
