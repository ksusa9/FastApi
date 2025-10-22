from pydantic import BaseModel
from typing import Optional

class Movietop(BaseModel):
    name: str
    id: int
    cost: int
    director: str

class NewMovie(BaseModel):
    title: str
    description: str
    budget: int  
    is_published: bool