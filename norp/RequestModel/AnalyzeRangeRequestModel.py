from pydantic import BaseModel
from fastapi import Form

class AnalyzeRangeRequestModel(BaseModel):
    start_time: int
    end_time: int

    @classmethod
    def as_form(
        cls,
        start_time: int = Form(...),
        end_time: int = Form(...),
    ) -> "AnalyzeRangeRequestModel":
        return cls(start_time=start_time, end_time=end_time)
