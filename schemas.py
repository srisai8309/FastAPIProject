from pydantic import BaseModel, EmailStr, Field

class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
class StudentResponse(BaseModel):
    id: int
    name: str
    user_id: int
class StudentListResponse(BaseModel):
    students: list[StudentResponse]
    page: int
    limit: int
    total: int
class MessageResponse(BaseModel):
    message: str
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
