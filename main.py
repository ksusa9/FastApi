from fastapi import FastAPI
from models import Movietop
import uvicorn

app = FastAPI(title="Movie API", description="API для информации о фильмах")

# Данные об учебном заведении
study_data = {
    "name": "Национальный исследовательский университет ИТМО",
    "location": "Санкт-Петербург, Россия",
    "specialization": "Информационные технологии и фотоника",
    "photo_url": "https://upload.wikimedia.org/wikipedia/ru/thumb/4/4f/Itmo_logo_2021.png/300px-Itmo_logo_2021.png"
}

# Создаем экземпляры Movietop с топ-10 фильмами
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

@app.get("/study")
async def get_study_info():
    """Возвращает информацию об учебном заведении"""
    return study_data

@app.get("/movietop")
async def get_movietop():
    """Возвращает топ-10 фильмов в формате JSON"""
    return [movie.dict() for movie in movietop_list]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8165,
        reload=True  # Автоматическая перезагрузка при изменениях
    )