from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2)
    chronic_conditions: list[Literal["diabetes", "hypertension"]] = Field(min_length=1)


class PatientResponse(PatientCreate):
    id: int


class MeasurementCreate(BaseModel):
    type: Literal["glucose", "blood_pressure"]
    glucose_mg_dl: int | None = Field(default=None, ge=20, le=600)
    systolic: int | None = Field(default=None, ge=50, le=300)
    diastolic: int | None = Field(default=None, ge=30, le=200)

    @model_validator(mode="after")
    def validate_payload(self) -> "MeasurementCreate":
        if self.type == "glucose" and self.glucose_mg_dl is None:
            raise ValueError("glucose_mg_dl is required for glucose measurements")
        if self.type == "blood_pressure" and (
            self.systolic is None or self.diastolic is None
        ):
            raise ValueError("systolic and diastolic are required for blood pressure measurements")
        return self


class MeasurementResponse(MeasurementCreate):
    id: int
    patient_id: int
    taken_at: datetime
