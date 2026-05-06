import os
import pyodbc
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

app = FastAPI(title="Submission Service")

SCHEMA_NAME = "aleksandr_submission"


def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


class SubmissionCreate(BaseModel):
    title: str
    artist: str
    status: Optional[str] = "pending"


@app.get("/")
def root():
    return {"service": "Submission Service", "status": "running"}


@app.post("/init")
def init_database():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{SCHEMA_NAME}')
        EXEC('CREATE SCHEMA {SCHEMA_NAME}');
        """)

        cursor.execute(f"""
        IF OBJECT_ID('{SCHEMA_NAME}.submissions', 'U') IS NULL
        CREATE TABLE {SCHEMA_NAME}.submissions (
            id INT IDENTITY(1,1) PRIMARY KEY,
            title NVARCHAR(255) NOT NULL,
            artist NVARCHAR(255) NOT NULL,
            status NVARCHAR(50) NOT NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
        """)

        cursor.execute(f"""
        IF NOT EXISTS (SELECT 1 FROM {SCHEMA_NAME}.submissions)
        INSERT INTO {SCHEMA_NAME}.submissions (title, artist, status)
        VALUES
        ('Sunset Over Vilnius', 'John Doe', 'pending'),
        ('Blue Ocean', 'Jane Smith', 'approved'),
        ('Abstract Dreams', 'Alex Turner', 'rejected');
        """)

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Submission schema, table and stub data created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submissions")
def get_submissions():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, title, artist, status, created_at
        FROM {SCHEMA_NAME}.submissions
        ORDER BY id;
        """)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "title": row.title,
                "artist": row.artist,
                "status": row.status,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submissions/{submission_id}")
def get_submission_by_id(submission_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, title, artist, status, created_at
        FROM {SCHEMA_NAME}.submissions
        WHERE id = ?;
        """, submission_id)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")

        return {
            "id": row.id,
            "title": row.title,
            "artist": row.artist,
            "status": row.status,
            "created_at": str(row.created_at)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submissions/status/{status}")
def get_submissions_by_status(status: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, title, artist, status, created_at
        FROM {SCHEMA_NAME}.submissions
        WHERE status = ?
        ORDER BY id;
        """, status)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "title": row.title,
                "artist": row.artist,
                "status": row.status,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submissions")
def create_submission(submission: SubmissionCreate):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        INSERT INTO {SCHEMA_NAME}.submissions (title, artist, status)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?);
        """, submission.title, submission.artist, submission.status)

        new_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "message": "Submission created",
            "id": new_id,
            "title": submission.title,
            "artist": submission.artist,
            "status": submission.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))