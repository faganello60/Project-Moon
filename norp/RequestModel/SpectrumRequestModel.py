import json

from fastapi import Form
from pydantic import AliasChoices, BaseModel, Field, field_validator


class SpectrumRequestModel(BaseModel):
    frequencies: list[str]
    fluxes: list[float] = Field(validation_alias=AliasChoices("fluxes", "flux"))
    frequencies_to_remove: list[str] = []

    @field_validator("frequencies", "fluxes", "frequencies_to_remove", mode="before")
    @classmethod
    def parse_list_fields(cls, value):
        if isinstance(value, str):
            return json.loads(value)

        return value

    @classmethod
    def as_form(
        cls,
        frequencies: str = Form(...),
        fluxes: str = Form(...),
        frequencies_to_remove: str = Form("[]"),
    ) -> "SpectrumRequestModel":
        return cls(
            frequencies=frequencies,
            fluxes=fluxes,
            frequencies_to_remove=frequencies_to_remove,
        )
