"""Independent Log and Review access contracts."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=1024)


class ReviewLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=1024)
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip() or any(ord(character) < 32 for character in value):
            raise ValueError("Reviewer name is required.")
        return value.strip()


class AccessSession(BaseModel):
    authenticated: bool
    name: str


class LogoutResult(BaseModel):
    authenticated: bool
