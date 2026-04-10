from pydantic import BaseModel

# Login Schema
class Login(BaseModel):
    email: str
    password: str


# Register Admin Schema (optional but good)
class AdminCreate(BaseModel):
    name: str
    email: str
    password: str