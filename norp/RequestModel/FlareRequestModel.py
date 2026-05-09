import json

from fastapi import Form
from pydantic import BaseModel, field_validator


class FlareRequestModel(BaseModel):
    flare_start: int
    flare_end: int
    background_averages: dict[str, float]

    @field_validator("background_averages", mode="before")
    @classmethod
    def parse_background_averages(cls, value):
        if isinstance(value, str):
            value = json.loads(value)

        if not isinstance(value, dict):
            raise ValueError("background_averages must be a dictionary.")

        return value

    @classmethod
    def as_form(
        cls,
        flare_start: int = Form(...),
        flare_end: int = Form(...),
        background_averages: str = Form(...),
    ) -> "FlareRequestModel":
        return cls(
            flare_start=flare_start,
            flare_end=flare_end,
            background_averages=background_averages,
        )
