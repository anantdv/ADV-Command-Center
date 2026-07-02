from app.schemas.common import CamelModel
from pydantic import Field


class CurrentUser(CamelModel):
    user: str
    full_name: str
    roles: list[str]
    company: str
    company_currency: str = "INR"
    allowed_companies: list[str]
    timezone: str
    language: str


class LoginRequest(CamelModel):
    username: str
    password: str


class LoginResult(CamelModel):
    user: str
    full_name: str
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    message: str = "Authentication delegated to Frappe"
