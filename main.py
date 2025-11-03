from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from models import Movietop, NewMovie, User, LoginRequest
import os
import uvicorn
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

app = FastAPI(title="Movie API", description="API для информации о фильмах")

os.makedirs("uploads/descriptions", exist_ok=True)
os.makedirs("uploads/covers", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Хранилище сессий в памяти (в продакшене используйте Redis или БД)
sessions: Dict[str, dict] = {}

# Валидные пользователи (в продакшене храните в БД с хешированными паролями)
valid_users = {
    "admin": "password123",
    "user": "user123",
    "test": "test123"
}

movietop_list = [
    Movietop(name="Побег из Шоушенка", id=1, cost=25000000, director="Фрэнк Дарабонт"),
    Movietop(name="Крестный отец", id=2, cost=6000000, director="Фрэнсис Форд Коппола"),
    Movietop(name="Темный рыцарь", id=3, cost=185000000, director="Кристофер Нолан"),
    Movietop(name="Крестный отец 2", id=4, cost=13000000, director="Фрэнсис Форд Коппола"),
    Movietop(name="12 разгневанных мужчин", id=5, cost=350000, director="Сидни Люмет"),
    Movietop(name="Список Шиндлера", id=6, cost=22000000, director="Стивен Спилберг"),
    Movietop(name="Властелин колец: Возвращение короля", id=7, cost=94000000, director="Питер Джексон"),
    Movietop(name="Криминальное чтиво", id=8, cost=8000000, director="Квентин Тарантино"),
    Movietop(name="Властелин колец: Братство кольца", id=9, cost=93000000, director="Питер Джексон"),
    Movietop(name="Хороший, плохой, злой", id=10, cost=1200000, director="Серджио Леоне")
]

new_movies = []

# Зависимость для проверки аутентификации
def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session_data = sessions.get(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Проверяем не истекла ли сессия
    if datetime.now() > session_data["expires_at"]:
        del sessions[session_token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Продлеваем сессию на 2 минуты
    sessions[session_token]["expires_at"] = datetime.now() + timedelta(minutes=2)
    sessions[session_token]["last_activity"] = datetime.now()
    
    return session_data

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Movie API!"}

# Маршрут для входа в систему
@app.post("/login")
async def login(response: Response, login_data: LoginRequest):
    # Проверяем учетные данные
    if login_data.username not in valid_users or valid_users[login_data.username] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Генерируем уникальный session token
    session_token = str(uuid.uuid4())
    
    # Создаем данные сессии
    now = datetime.now()
    session_data = {
        "username": login_data.username,
        "created_at": now,
        "last_activity": now,
        "expires_at": now + timedelta(minutes=2)
    }
    
    # Сохраняем сессию
    sessions[session_token] = session_data
    
    # Устанавливаем безопасный HTTP-only cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # В продакшене установите True для HTTPS
        samesite="lax",
        max_age=120  # 2 минуты в секундах
    )
    
    return {"message": "Login successful", "username": login_data.username}

# Защищенный маршрут для получения информации о пользователе
@app.get("/user")
async def get_user_profile(user_data: dict = Depends(get_current_user)):
    # Формируем информацию о профиле
    profile_info = {
        "username": user_data["username"],
        "session_info": {
            "created_at": user_data["created_at"].isoformat(),
            "last_activity": user_data["last_activity"].isoformat(),
            "expires_at": user_data["expires_at"].isoformat(),
            "session_duration_minutes": 2
        },
        "movies": [movie.dict() for movie in movietop_list]
    }
    
    return profile_info

# Маршрут для выхода из системы
@app.post("/logout")
async def logout(response: Response, user_data: dict = Depends(get_current_user)):
    session_token = None
    for token, data in sessions.items():
        if data["username"] == user_data["username"]:
            session_token = token
            break
    
    if session_token:
        del sessions[session_token]
    
    # Удаляем cookie
    response.delete_cookie("session_token")
    
    return {"message": "Logout successful"}

@app.get("/study", response_class=HTMLResponse)
async def get_study_info_html():
    study_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Учебное заведение</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .card { background: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            img { max-width: 300px; border-radius: 8px; margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Брянский Государственный Инженерно-Технологический Университет</h1>
            <p><strong> Местоположение:</strong> Брянск, Россия</p>
            <p><strong> Специализация:</strong> Программная инженерия</p>
            <img src="https://avatars.mds.yandex.net/get-altay/226077/2a000001624c61a61a164a00d5e128a9dd2e/orig" alt="Университет">
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=study_html)

@app.get("/movietop/{movie_id}")
async def get_movie_by_id(movie_id: int):
    for movie in movietop_list:
        if movie.id == movie_id:
            return movie.dict()
    raise HTTPException(status_code=404, detail="Фильм не найден")

@app.get("/add-movie", response_class=HTMLResponse)
async def add_movie_form():
    form_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Добавить фильм</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; }
            input, textarea, select { width: 300px; padding: 8px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Добавить новый фильм</h1>
        <form action="/add-movie" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label>Название фильма:</label>
                <input type="text" name="title" required>
            </div>
            <div class="form-group">
                <label>Описание фильма:</label>
                <textarea name="description" rows="4" required></textarea>
            </div>
            <div class="form-group">
                <label>Бюджет фильма ($):</label>
                <input type="number" name="budget" required>
            </div>
            <div class="form-group">
                <label>Опубликован:</label>
                <select name="is_published">
                    <option value="true">Да</option>
                    <option value="false">Нет</option>
                </select>
            </div>
            <div class="form-group">
                <label>Обложка фильма:</label>
                <input type="file" name="cover_image" accept="image/*">
            </div>
            <div class="form-group">
                <label>Файл описания (txt):</label>
                <input type="file" name="description_file" accept=".txt">
            </div>
            <button type="submit">Добавить фильм</button>
        </form>
        
        <div style="margin-top: 30px;">
            <a href="/movies">Посмотреть все фильмы</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=form_html)

@app.post("/add-movie")
async def add_movie(
    title: str = Form(...),
    description: str = Form(...),
    budget: int = Form(...),
    is_published: bool = Form(...),
    cover_image: UploadFile = File(None),
    description_file: UploadFile = File(None)
):
    
    cover_filename = None
    if cover_image:
        cover_filename = f"cover_{len(new_movies) + 1}.jpg"
        cover_path = f"uploads/covers/{cover_filename}"
        with open(cover_path, "wb") as buffer:
            content = await cover_image.read()
            buffer.write(content)
    
    description_filename = None
    if description_file:
        description_filename = f"desc_{len(new_movies) + 1}.txt"
        description_path = f"uploads/descriptions/{description_filename}"
        with open(description_path, "wb") as buffer:
            content = await description_file.read()
            buffer.write(content)
    
    new_movie = {
        "id": len(new_movies) + 1,
        "title": title,
        "description": description,
        "budget": budget,  
        "is_published": is_published,
        "cover_image": cover_filename,
        "description_file": description_filename
    }
    
    new_movies.append(new_movie)
    
    return {"message": "Фильм добавлен!", "movie": new_movie}

@app.get("/movies", response_class=HTMLResponse)
async def show_movies():
    movies_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Все фильмы</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            .movie-card { 
                border: 1px solid #ddd; 
                padding: 20px; 
                margin: 10px 0; 
                border-radius: 8px;
            }
            .movie-cover { max-width: 200px; }
            .add-link { display: block; margin: 20px 0; }
            .budget { color: #28a745; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Все фильмы</h1>
        <a href="/add-movie" class="add-link">+ Добавить новый фильм</a>
    """
    movies_html += "<h2>Топ фильмы:</h2>"
    for movie in movietop_list:
        movies_html += f"""
        <div class="movie-card">
            <h3>{movie.name}</h3>
            <p><strong>Режиссер:</strong> {movie.director}</p>
            <p><strong>Бюджет:</strong> <span class="budget">{movie.cost:,} $</span></p>
        </div>
        """
    
    if new_movies:
        movies_html += "<h2>Добавленные фильмы:</h2>"
        for movie in new_movies:
            cover_html = ""
            if movie["cover_image"]:
                cover_html = f'<img src="/uploads/covers/{movie["cover_image"]}" class="movie-cover" alt="Обложка">'
            
            movies_html += f"""
            <div class="movie-card">
                {cover_html}
                <h3>{movie['title']}</h3>
                <p><strong>Описание:</strong> {movie['description']}</p>
                <p><strong>Бюджет:</strong> <span class="budget">{movie['budget']:,} $</span></p>
                <p><strong>Опубликован:</strong> {'Да' if movie['is_published'] else 'Нет'}</p>
                <p><strong>ID:</strong> {movie['id']}</p>
            </div>
            """
    
    movies_html += """
    </body>
    </html>
    """
    return HTMLResponse(content=movies_html)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8165,
        reload=True  
    )