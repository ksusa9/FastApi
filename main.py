from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import shutil
import os
import jwt
import uuid
from datetime import datetime, timedelta
from models import Movietop, User, LoginRequest, Token, UserProfile, LoginHistory, NewMovie

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SESSION_EXPIRE_MINUTES = 2  

os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/descriptions", exist_ok=True)

app = FastAPI(title="Movie API", description="API для управления фильмами")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

security = HTTPBearer()

users_db = {
    "admin": {
        "password": "password123",
        "full_name": "Администратор Системы",
        "login_history": []
    },
    "user": {
        "password": "user123", 
        "full_name": "Обычный Пользователь",
        "login_history": []
    }
}

sessions_db = {}
jwt_tokens_db = {}

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

BASE_STYLES = """
body { font-family: Arial, sans-serif; margin: 20px; }
.container { max-width: 800px; margin: 0 auto; }
.nav { margin: 20px 0; text-align: center; }
.nav a { margin: 0 10px; text-decoration: none; color: #007bff; }
.form-group { margin: 10px 0; }
input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
button { background: #4CAF50; color: white; padding: 10px; border: none; cursor: pointer; }
.card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
.movie-poster { max-width: 200px; margin: 10px 0; }
"""

def validate_cookie_session(session_token: str) -> Optional[dict]:
    if session_token not in sessions_db:
        return None
    
    session_data = sessions_db[session_token]
    
    if datetime.now() > session_data["expires_at"]:
        del sessions_db[session_token]
        return None
    
    session_data["expires_at"] = datetime.now() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    session_data["last_activity"] = datetime.now()
    sessions_db[session_token] = session_data
    
    return session_data

def add_login_history(username: str, request: Request):
    if username in users_db:
        login_record = LoginHistory(
            login_time=datetime.now().isoformat(),
            ip_address=request.client.host if request.client else "unknown"
        )
        users_db[username]["login_history"].append(login_record)
        if len(users_db[username]["login_history"]) > 10:
            users_db[username]["login_history"] = users_db[username]["login_history"][-10:]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return f"""
    <html><head><title>Фильмы</title><style>{BASE_STYLES}</style></head>
    <body><div class="container">
        <h1>Коллекция фильмов</h1>
        <div class="nav">
            <a href="/">Главная</a>
            <a href="/movies">Фильмы</a>
            <a href="/user">Профиль</a>
            <a href="/cookie-login">Cookie Вход</a>
            <a href="/jwt-login-form">JWT Вход</a>
            <a href="/add-film-protected">Добавить фильм</a>
            <a href="/study">Об учебе</a>
        </div>
    </div></body></html>
    """

@app.get("/cookie-login", response_class=HTMLResponse)
async def cookie_login_form():
    return f"""
    <html><head><title>Вход</title><style>{BASE_STYLES}</style></head>
    <body><div class="container">
        <h1>Вход (Cookie)</h1>
        <div class="nav">
            <a href="/">Главная</a>
            <a href="/user">Профиль</a>
        </div>
        <div class="card">
            <form action="/cookie-login" method="post">
                <div class="form-group"><input type="text" name="username" placeholder="Логин" value="admin" required></div>
                <div class="form-group"><input type="password" name="password" placeholder="Пароль" value="password123" required></div>
                <button type="submit">Войти</button>
            </form>
        </div>
        <p>Тестовые: admin/password123, user/user123</p>
    </div></body></html>
    """

@app.post("/cookie-login")
async def cookie_login(response: Response, request: Request, username: str = Form(...), password: str = Form(...)):
    if username not in users_db or users_db[username]["password"] != password:
        raise HTTPException(status_code=401, detail="Неверные данные")
    
    session_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    
    add_login_history(username, request)
    
    sessions_db[session_token] = {
        "username": username,
        "login_time": datetime.now(),
        "expires_at": expires_at,
        "last_activity": datetime.now()
    }
    
    response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=120)
    return {"message": "Успешный вход", "username": username}

@app.get("/user")
async def get_user_profile(request: Request):
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    
    session_data = validate_cookie_session(session_token)
    if not session_data:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    
    username = session_data["username"]
    user_data = users_db[username]
    
    user_profile = UserProfile(
        username=username,
        full_name=user_data.get("full_name"),
        login_time=session_data["login_time"].isoformat(),
        last_activity=session_data["last_activity"].isoformat(),
        session_expires=session_data["expires_at"].isoformat(),
        login_history=user_data["login_history"],
        movies_count=len(movies_db),
        movies=[movie.dict() for movie in movies_db]
    )
    
    return user_profile

@app.post("/cookie-logout")
async def cookie_logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Успешный выход"}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    if token not in jwt_tokens_db:
        raise HTTPException(status_code=401, detail="Token is not active")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or jwt_tokens_db[token] != username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        if token in jwt_tokens_db:
            del jwt_tokens_db[token]
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/jwt-login", response_model=Token)
async def login_jwt(login_data: LoginRequest, request: Request):
    if login_data.username not in users_db or users_db[login_data.username]["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    
    add_login_history(login_data.username, request)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": login_data.username}, expires_delta=access_token_expires)
    
    jwt_tokens_db[access_token] = login_data.username
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/jwt-login-form", response_class=HTMLResponse)
async def login_jwt_form():
    return f"""
    <html><head><title>JWT Вход</title><style>{BASE_STYLES}</style>
    <script>
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('jwt_username');
        
        async function login() {{
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/jwt-login', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{username, password}})
            }});
            
            if (response.ok) {{
                const data = await response.json();
                localStorage.setItem('jwt_token', data.access_token);
                localStorage.setItem('jwt_username', username);
                alert('Авторизация успешна!');
                window.location.href = '/add-film-protected';
            }} else {{
                alert('Ошибка авторизации: неверный логин или пароль');
            }}
        }}
    </script></head>
    <body><div class="container">
        <h1>JWT Вход</h1>
        <div class="nav"><a href="/">Главная</a></div>
        <div class="card">
            <input type="text" id="username" placeholder="Логин" value="admin">
            <input type="password" id="password" placeholder="Пароль" value="password123">
            <button onclick="login()">Войти</button>
        </div>
        <p>Тестовые: admin/password123, user/user123</p>
    </div></body></html>
    """

@app.get("/add-film-protected", response_class=HTMLResponse)
async def add_film_protected_form():
    return f"""
    <html><head><title>Добавить фильм</title><style>{BASE_STYLES}</style>
    <script>
        function checkAuth() {{
            const token = localStorage.getItem('jwt_token');
            const username = localStorage.getItem('jwt_username');
            
            if (token && username) {{
                document.getElementById('filmForm').style.display = 'block';
                document.getElementById('needAuth').style.display = 'none';
            }} else {{
                document.getElementById('filmForm').style.display = 'none';
                document.getElementById('needAuth').style.display = 'block';
            }}
        }}
        
        async function addFilm() {{
            const token = localStorage.getItem('jwt_token');
            if (!token) {{
                alert('Сначала войдите в систему');
                window.location.href = '/jwt-login-form';
                return;
            }}
            
            const name = document.getElementById('name').value;
            const director = document.getElementById('director').value;
            const cost = document.getElementById('cost').value;
            
            if (!name || !director || !cost) {{
                alert('Заполните все обязательные поля');
                return;
            }}
            
            const formData = new FormData();
            formData.append('name', name);
            formData.append('director', director);
            formData.append('cost', cost);
            formData.append('is_oscar_winner', document.getElementById('is_oscar_winner').checked);
            
            const poster = document.getElementById('poster').files[0];
            if (poster) formData.append('poster', poster);
            
            const descriptionFile = document.getElementById('description_file').files[0];
            if (descriptionFile) formData.append('description_file', descriptionFile);
            
            try {{
                const response = await fetch('/add-film', {{
                    method: 'POST',
                    headers: {{'Authorization': 'Bearer ' + token}},
                    body: formData
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    alert('Фильм "' + result.movie.name + '" успешно добавлен!');
                    document.getElementById('name').value = '';
                    document.getElementById('director').value = '';
                    document.getElementById('cost').value = '';
                    document.getElementById('is_oscar_winner').checked = false;
                    document.getElementById('poster').value = '';
                    document.getElementById('description_file').value = '';
                }} else {{
                    const error = await response.json();
                    alert('Ошибка: ' + error.detail);
                }}
            }} catch (error) {{
                alert('Ошибка сети: ' + error.message);
            }}
        }}
        
        window.onload = checkAuth;
    </script></head>
    <body><div class="container">
        <h1>Добавить фильм</h1>
        <div class="nav">
            <a href="/">Главная</a>
            <a href="/movies">Фильмы</a>
            <a href="/jwt-login-form">Вход</a>
        </div>
        
        <div id="needAuth" class="card" style="background: #f8d7da;">
            <h3>Требуется авторизация</h3>
            <p>Для добавления фильмов необходимо войти в систему</p>
            <button onclick="location.href='/jwt-login-form'" style="background: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">
                Перейти к авторизации
            </button>
        </div>
        
        <div class="card" id="filmForm" style="display: none;">
            <h3>Данные фильма</h3>
            <input type="text" id="name" placeholder="Название" required>
            <input type="text" id="director" placeholder="Режиссер" required>
            <input type="number" id="cost" placeholder="Бюджет" required>
            <div class="form-group">
                <label><input type="checkbox" id="is_oscar_winner"> Лауреат Оскара</label>
            </div>
            <div class="form-group">
                <label>Файл описания:</label>
                <input type="file" id="description_file" accept=".txt,.pdf,.doc,.docx">
            </div>
            <div class="form-group">
                <label>Обложка фильма:</label>
                <input type="file" id="poster" accept="image/*">
            </div>
            <button onclick="addFilm()">Добавить фильм</button>
        </div>
    </div></body></html>
    """

@app.post("/add-film")
async def add_film_protected(
    name: str = Form(...),
    director: str = Form(...),
    cost: int = Form(...),
    is_oscar_winner: bool = Form(False),
    description_file: UploadFile = File(None),
    poster: UploadFile = File(None),
    username: str = Depends(verify_token)
):
    try:
        new_id = max([movie.id for movie in movies_db]) + 1 if movies_db else 1
        
        poster_url = None
        if poster and poster.filename:
            poster_filename = f"{new_id}_{poster.filename}"
            poster_path = f"uploads/images/{poster_filename}"
            with open(poster_path, "wb") as buffer:
                shutil.copyfileobj(poster.file, buffer)
            poster_url = f"/uploads/images/{poster_filename}"
        
        description_file_url = None
        description_text = None
        
        if description_file and description_file.filename:
            desc_filename = f"{new_id}_{description_file.filename}"
            desc_path = f"uploads/descriptions/{desc_filename}"
            with open(desc_path, "wb") as buffer:
                content = await description_file.read()
                buffer.write(content)
            description_file_url = f"/uploads/descriptions/{desc_filename}"
            
            if description_file.filename.lower().endswith('.txt'):
                try:
                    description_text = content.decode('utf-8')
                except UnicodeDecodeError:
                    description_text = "Не удалось прочитать файл описания"
            else:
                description_text = f"Файл: {description_file.filename}"
        
        new_movie = Movietop(
            id=new_id,
            name=name,
            cost=cost,
            director=director,
            description=description_text,
            is_oscar_winner=is_oscar_winner,
            poster_url=poster_url,
            description_file_url=description_file_url
        )
        
        movies_db.append(new_movie)
        
        return {
            "message": "Фильм добавлен", 
            "movie": new_movie.dict(),
            "added_by": username
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении фильма: {str(e)}")

@app.get("/study", response_class=HTMLResponse)
async def get_study_info():
    return f"""
    <html><head><title>Об учебе</title><style>{BASE_STYLES}</style></head>
    <body><div class="container">
        <h1>Об учебе</h1>
        <div class="nav"><a href="/">Главная</a></div>
        <div class="card">
            <h2>БГИТУ - Брянский государственный инженерно-технологический университет</h2>
            <img src="https://avatars.mds.yandex.net/get-altay/226077/2a000001624c61a61a164a00d5e128a9dd2e/orig" 
                alt="БГИТУ" 
                style="max-width: 100%; height: auto; border-radius: 10px; margin: 15px 0;">
            <p><strong>Факультет:</strong> Инженерно-Экономический</p>
            <p><strong>Курс:</strong> 2 курс</p>
            <p><strong>Специализация:</strong> Программная инженерия</p>
            <p><strong>Год основания вуза:</strong> 1930</p>
            <p><strong>Местоположение:</strong> Брянск, Россия</p>
        </div>
    </div></body></html>
    """

@app.get("/movietop/{movie_name}")
async def get_movie(movie_name: str):
    for movie in movies_db:
        if movie.name.lower() == movie_name.lower():
            return movie
    raise HTTPException(status_code=404, detail="Фильм не найден")

@app.get("/movies", response_class=HTMLResponse)
async def get_all_movies():
    movies_html = ""
    for movie in movies_db:
        poster_html = f'<img src="{movie.poster_url}" class="movie-poster">' if movie.poster_url else ''
        oscar_badge = ' 🏆' if movie.is_oscar_winner else ''
        
        description_html = ""
        if movie.description_file_url:
            filename = movie.description_file_url.split('/')[-1]
            description_html = f'<p><a href="{movie.description_file_url}" download>📎 Скачать описание ({filename})</a></p>'
        elif movie.description:
            description_html = f'<p>Описание: {movie.description}</p>'
        
        movies_html += f"""
        <div class="card">
            <h3>{movie.name}{oscar_badge}</h3>
            {poster_html}
            <p>Режиссер: {movie.director}</p>
            <p>Бюджет: ${movie.cost:,}</p>
            {description_html}
        </div>
        """
    
    return f"""
    <html><head><title>Все фильмы</title><style>{BASE_STYLES}</style></head>
    <body><div class="container">
        <h1>Все фильмы</h1>
        <div class="nav"><a href="/">Главная</a></div>
        {movies_html}
    </div></body></html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8165, reload=True)