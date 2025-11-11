# models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Movietop(BaseModel):
    id: int
    name: str
    cost: int
    director: str
    description: Optional[str] = None
    is_oscar_winner: Optional[bool] = False
    poster_url: Optional[str] = None

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
    login_time: str
    last_activity: str
    session_expires: str
    movies_count: int
    movies: list[Movietop]