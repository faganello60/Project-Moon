from pydantic import BaseModel
from fastapi import Form

class RemoveBGNoiseRequestModel(BaseModel):
    start_time: int
    end_time: int
    pre_flare_start: int
    pre_flare_end: int

    @classmethod
    def as_form(
        cls,
        start_time: int = Form(...),
        end_time: int = Form(...),
        pre_flare_start: int = Form(...),
        pre_flare_end: int = Form(...),
    ) -> "RemoveBGNoiseRequestModel":
        return cls(
            start_time=start_time,
            end_time=end_time,
            pre_flare_start=pre_flare_start,
            pre_flare_end=pre_flare_end,
        )
