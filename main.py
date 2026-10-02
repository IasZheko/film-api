from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Film-Watchlist API")

# Erlaubt später der Handy-Web-App, die API aufzurufen (Bonus-Aufgabe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class MovieIn(BaseModel):
    """Daten, die der Client beim Anlegen/Ändern schickt."""
    title: str = Field(min_length=1, examples=["Inception"])
    genre: str = Field(examples=["Sci-Fi"])
    year: int = Field(ge=1888, le=2100, examples=[2010])
    watched: bool = False
    rating: Optional[int] = Field(default=None, ge=1, le=10)


class Movie(MovieIn):
    """Film inklusive vom Server vergebener ID."""
    id: int


# "Datenbank": einfache Liste im Arbeitsspeicher (geht bei Neustart verloren)
movies: list[Movie] = [
    Movie(id=1, title="Inception", genre="Sci-Fi", year=2010, watched=True, rating=9),
    Movie(id=2, title="Das Boot", genre="Drama", year=1981, watched=False),
]
next_id = 3


@app.get("/", include_in_schema=False)
def index():
    """Liefert die Handy-Web-App (index.html) unter der Hauptadresse aus."""
    return FileResponse(Path(__file__).parent / "index.html")


def find_movie(movie_id: int) -> Movie:
    for movie in movies:
        if movie.id == movie_id:
            return movie
    raise HTTPException(status_code=404, detail="Film nicht gefunden")


@app.get("/movies", response_model=list[Movie])
def list_movies(genre: Optional[str] = None, watched: Optional[bool] = None):
    """Alle Filme, optional gefiltert nach Genre und/oder gesehen."""
    result = movies
    if genre is not None:
        result = [m for m in result if m.genre.lower() == genre.lower()]
    if watched is not None:
        result = [m for m in result if m.watched == watched]
    return result


@app.get("/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: int):
    return find_movie(movie_id)


@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED)
def create_movie(data: MovieIn):
    global next_id
    movie = Movie(id=next_id, **data.model_dump())
    next_id += 1
    movies.append(movie)
    return movie


@app.put("/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: int, data: MovieIn):
    movie = find_movie(movie_id)
    updated = Movie(id=movie.id, **data.model_dump())
    movies[movies.index(movie)] = updated
    return updated


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int):
    movies.remove(find_movie(movie_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
