import sqlite3
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlite3 import Connection, Cursor

app = FastAPI()


# Модель User
class User(BaseModel):
    id: int
    username: str
    email: str


DATABASE = "users.db"


def get_db_connection() -> Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/create_user", response_model=User)
def create_user(user: User):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, email)
                VALUES (?, ?)
            """, (user.username, user.email))
            conn.commit()
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User with this username or email already exists")

    return {**user.dict(), "id": user_id}


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {**dict(row)}


@app.get("/users", response_model=List[User])
def get_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
