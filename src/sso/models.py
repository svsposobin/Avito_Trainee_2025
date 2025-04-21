from pydantic import BaseModel, EmailStr


class UserEmail(BaseModel):
    email: EmailStr
