from fastapi import FastAPI
from models import Movietop
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Movie API", description="API для информации о фильмах")

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

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Movie API!"}

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
            <img src="https://avatars.mds.yandex.net/get-altay/226077/2a000001624c61a61a164a00d5e128a9dd2e/orig" alt="ИТМО">
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8165,
        reload=True  
    )