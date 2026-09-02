from pydantic import BaseModel, ConfigDict, Field


class AdminLoginRequest(BaseModel):
    email: str = Field(..., description="Admin email address")
    password: str = Field(..., description="Admin password")


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_id: str
    email: str
    role: str


class AdminLoginResponse(BaseModel):
    token: str
    admin: AdminUserResponse
