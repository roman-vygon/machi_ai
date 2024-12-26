from pydantic import BaseModel, Field


class EstablishmentCount(BaseModel, validate_assignment=True):
    working: int = Field(ge=0, strict=True)