from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit_start: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=200)
