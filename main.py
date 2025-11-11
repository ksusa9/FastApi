# main.py (исправленная версия)
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import shutil
import os
import jwt
from datetime import datetime, timedelta
from models import Movietop, User, LoginRequest, Token

# Конфигурация JWT
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Создаем папки для загрузки файлов
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/descriptions", exist_ok=True)

app = FastAPI(title="Movie API", description="API для управления фильмами")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Security scheme для JWT
security = HTTPBearer()

# База данных пользователей
users_db = {
    "admin": "password123",
    "user": "user123",
    "alice": "alice2024"
}

# База данных фильмов
movies_db = [
    Movietop(id=1, name="Зеленая миля", cost=60000000, director="Фрэнк Дарабонт"),
    Movietop(id=2, name="Побег из Шоушенка", cost=25000000, director="Фрэнк Дарабонт"),
    Movietop(id=3, name="Форрест Гамп", cost=55000000, director="Роберт Земекис"),
    Movietop(id=4, name="Список Шиндлера", cost=22000000, director="Стивен Спилберг"),
    Movietop(id=5, name="Крестный отец", cost=6000000, director="Фрэнсис Форд Коппола"),
    Movietop(id=6, name="Начало", cost=160000000, director="Кристофер Нолан"),
    Movietop(id=7, name="Леон", cost=16000000, director="Люк Бессон"),
    Movietop(id=8, name="Король Лев", cost=45000000, director="Роджер Аллерс"),
    Movietop(id=9, name="Темный рыцарь", cost=185000000, director="Кристофер Нолан"),
    Movietop(id=10, name="Бойцовский клуб", cost=63000000, director="Дэвид Финчер")
]

# Базовые CSS стили
BASE_STYLES = """
body { font-family: Arial, sans-serif; margin: 20px; }
.container { max-width: 800px; margin: 0 auto; }
.nav { margin: 20px 0; text-align: center; }
.nav a { margin: 0 10px; text-decoration: none; color: #007bff; }
.form-group { margin: 10px 0; }
input, textarea { width: 100%; padding: 8px; margin: 5px 0; box-sizing: border-box; }
button { background: #4CAF50; color: white; padding: 10px; border: none; cursor: pointer; }
.card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
.movie-poster { max-width: 200px; max-height: 300px; margin: 10px 0; }
"""

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Функция для проверки JWT токена
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# 1. Конечная точка для логина с JWT
@app.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    if login_data.username not in users_db or users_db[login_data.username] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": login_data.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# HTML форма для логина с JWT
@app.get("/login-form", response_class=HTMLResponse)
async def login_form():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход в систему (JWT)</title>
        <style>{BASE_STYLES}</style>
        <script>
            async function login() {{
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                const response = await fetch('/login', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{username, password}})
                }});
                
                if (response.ok) {{
                    const data = await response.json();
                    localStorage.setItem('jwt_token', data.access_token);
                    alert('Токен получен и сохранен!');
                    window.location.href = '/add-film-protected';
                }} else {{
                    alert('Ошибка авторизации!');
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Вход в систему (JWT)</h1>
            
            <div class="nav">
                <a href="/">Главная</a>
                <a href="/movies">Фильмы</a>
                <a href="/add-film-protected">Добавить фильм</a>
            </div>

            <div class="card">
                <div class="form-group">
                    <label>Имя пользователя:</label>
                    <input type="text" id="username" value="admin">
                </div>
                <div class="form-group">
                    <label>Пароль:</label>
                    <input type="password" id="password" value="password123">
                </div>
                <button onclick="login()" style="width: 100%">Войти</button>
            </div>

            <div class="card">
                <h3>Тестовые пользователи:</h3>
                <p>admin / password123</p>
                <p>user / user123</p>
                <p>alice / alice2024</p>
            </div>
        </div>
    </body>
    </html>
    """

# Защищенная форма для добавления фильмов
@app.get("/add-film-protected", response_class=HTMLResponse)
async def add_film_protected_form():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Добавить фильм (JWT)</title>
        <style>{BASE_STYLES}</style>
        <script>
            async function addFilm() {{
                let token = document.getElementById('auth-token').value;
                if (!token) {{
                    token = localStorage.getItem('jwt_token');
                    if (token) document.getElementById('auth-token').value = token;
                }}
                
                if (!token) {{
                    alert('Сначала получите токен на странице входа!');
                    return;
                }}
                
                const formData = new FormData();
                formData.append('name', document.getElementById('name').value);
                formData.append('director', document.getElementById('director').value);
                formData.append('cost', document.getElementById('cost').value);
                formData.append('description', document.getElementById('description').value);
                formData.append('is_oscar_winner', document.getElementById('is_oscar_winner').checked);
                
                const posterFile = document.getElementById('poster').files[0];
                if (posterFile) formData.append('poster', posterFile);
                
                try {{
                    const response = await fetch('/add-film', {{
                        method: 'POST',
                        headers: {{'Authorization': `Bearer ${{token}}`}},
                        body: formData
                    }});
                    
                    if (response.ok) {{
                        alert('Фильм успешно добавлен!');
                        document.querySelector('form').reset();
                    }} else {{
                        const error = await response.json();
                        alert('Ошибка: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Ошибка сети');
                }}
            }}
            
            window.onload = function() {{
                const savedToken = localStorage.getItem('jwt_token');
                if (savedToken) {{
                    document.getElementById('auth-token').value = savedToken;
                }}
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Добавить фильм (JWT)</h1>
            
            <div class="nav">
                <a href="/">Главная</a>
                <a href="/movies">Фильмы</a>
                <a href="/login-form">Вход</a>
            </div>

            <div class="card">
                <h3>🔐 Аутентификация</h3>
                <div class="form-group">
                    <label>JWT Токен:</label>
                    <input type="text" id="auth-token" placeholder="Токен будет подставлен автоматически">
                </div>
            </div>

            <div class="card">
                <h3>📝 Данные фильма</h3>
                <form onsubmit="event.preventDefault(); addFilm();">
                    <div class="form-group">
                        <label>Название:</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label>Режиссер:</label>
                        <input type="text" id="director" required>
                    </div>
                    <div class="form-group">
                        <label>Бюджет:</label>
                        <input type="number" id="cost" required>
                    </div>
                    <div class="form-group">
                        <label>Описание:</label>
                        <textarea id="description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label><input type="checkbox" id="is_oscar_winner"> Лауреат Оскара</label>
                    </div>
                    <div class="form-group">
                        <label>Обложка:</label>
                        <input type="file" id="poster" accept="image/*">
                    </div>
                    <button type="submit" style="width: 100%">Добавить фильм</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

# Защищенный endpoint для добавления фильмов
@app.post("/add-film")
async def add_film_protected(
    name: str = Form(...),
    director: str = Form(...),
    cost: int = Form(...),
    description: str = Form(None),
    is_oscar_winner: bool = Form(False),
    poster: UploadFile = File(None),
    username: str = Depends(verify_token)
):
    new_id = max([movie.id for movie in movies_db]) + 1 if movies_db else 1
    
    poster_url = None
    if poster and poster.filename:
        # Создаем безопасное имя файла
        file_extension = poster.filename.split('.')[-1]
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        poster_filename = f"{new_id}_{safe_name.replace(' ', '_')}.{file_extension}"
        poster_path = f"uploads/images/{poster_filename}"
        
        # Сохраняем файл
        with open(poster_path, "wb") as buffer:
            shutil.copyfileobj(poster.file, buffer)
        poster_url = f"/uploads/images/{poster_filename}"
    
    new_movie = Movietop(
        id=new_id,
        name=name,
        cost=cost,
        director=director,
        description=description,
        is_oscar_winner=is_oscar_winner,
        poster_url=poster_url
    )
    
    movies_db.append(new_movie)
    return {
        "message": "Фильм успешно добавлен", 
        "movie": new_movie,
        "added_by": username
    }

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie Collection</title>
        <style>{BASE_STYLES}</style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Коллекция фильмов</h1>
            
            <div class="nav">
                <a href="/">Главная</a>
                <a href="/movies">Все фильмы</a>
                <a href="/login-form">Вход JWT</a>
                <a href="/add-film-protected">Добавить фильм</a>
                <a href="/study">Учебное заведение</a>
            </div>
            
            <div class="card">
                <h2>Добро пожаловать!</h2>
                <p>Система управления фильмами с JWT аутентификацией.</p>
                <p><strong>Функции:</strong></p>
                <ul>
                    <li>Просмотр коллекции фильмов</li>
                    <li>JWT аутентификация</li>
                    <li>Защищенное добавление фильмов</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

# Страница учебного заведения
@app.get("/study", response_class=HTMLResponse)
async def get_study_info():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>{BASE_STYLES}
            .university-photo {{
                max-width: 100%;
                height: auto;
                border-radius: 10px;
                margin: 20px 0;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .photo-caption {{
                text-align: center;
                color: #666;
                font-style: italic;
                margin-top: -10px;
                margin-bottom: 20px;
            }}</style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Учебное заведение</h1>
            
            <div class="nav">
                <a href="/">Главная</a>
                <a href="/movies">Фильмы</a>
                <a href="/login-form">Вход</a>
            </div>

            <div class="card">
                <h2>Брянский Государственный Инженерно-Технологический Университет</h2>
                <p><strong>Институт:</strong> Инженерно-экономический </p>
                <p><strong>Курс:</strong> 2 курс</p>
                <p><strong>Специализация:</strong> Програмная инженерия</p>
                <img src="https://avatars.mds.yandex.net/get-altay/226077/2a000001624c61a61a164a00d5e128a9dd2e/orig" alt="Главное здание Университета БГИТУ" 
                class="university-photo">
            </div>
        </div>
    </body>
    </html>
    """

# Поиск фильма по названию
@app.get("/movietop/{movie_name}")
async def get_movie(movie_name: str):
    for movie in movies_db:
        if movie.name.lower() == movie_name.lower():
            return movie
    raise HTTPException(status_code=404, detail="Фильм не найден")

# Страница всех фильмов с фото - ИСПРАВЛЕННАЯ ВЕРСИЯ
@app.get("/movies", response_class=HTMLResponse)
async def get_all_movies():
    movies_html = ""
    for movie in movies_db:
        # Проверяем есть ли фото и правильно ли отображаем
        poster_html = ""
        if movie.poster_url:
            poster_html = f'<img src="{movie.poster_url}" class="movie-poster" alt="{movie.name}">'
        else:
            poster_html = '<p>📷 Нет обложки</p>'
        
        oscar_icon = "🏆" if movie.is_oscar_winner else ""
        
        movies_html += f"""
        <div class="card">
            <h3>{movie.name} {oscar_icon}</h3>
            {poster_html}
            <p><strong>Режиссер:</strong> {movie.director}</p>
            <p><strong>Бюджет:</strong> ${movie.cost:,}</p>
            <p><strong>Описание:</strong> {movie.description or 'Нет описания'}</p>
            <p><strong>ID:</strong> {movie.id}</p>
            <p><strong>URL фото:</strong> {movie.poster_url or 'Нет фото'}</p>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Все фильмы</title>
        <style>{BASE_STYLES}</style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Все фильмы</h1>
            <div class="nav">
                <a href="/">Главная</a>
                <a href="/add-film-protected">Добавить фильм</a>
                <a href="/login-form">Вход</a>
            </div>
            {movies_html}
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8165, reload=True)