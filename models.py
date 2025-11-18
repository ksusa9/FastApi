from pydantic import BaseModel
from typing import Optional

class Movietop(BaseModel):
    id: int
    name: str
    cost: int
    director: str
    description: Optional[str] = None
    is_oscar_winner: Optional[bool] = False
    poster_url: Optional[str] = None
    description_file_url: Optional[str] = None

class User(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfile(BaseModel):
    username: str
    full_name: Optional[str] = None
    login_time: str
    last_activity: str
    session_expires: str
    login_history: list
    movies_count: int
    movies: list

class LoginHistory(BaseModel):
    login_time: str
    ip_address: str

class NewMovie(BaseModel):
    name: str
    director: str
    cost: int
    is_oscar_winner: bool
    description: Optional[str] = None