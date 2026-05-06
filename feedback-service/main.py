import os
import pyodbc
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

app = FastAPI(title="Feedback Service")

SCHEMA_NAME = "aleksandr_feedback"


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


class FeedbackCreate(BaseModel):
    submission_id: int
    reviewer_name: str
    comment: str
    rating: Optional[int] = 5


@app.get("/")
def root():
    return {"service": "Feedback Service", "status": "running"}


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
        IF OBJECT_ID('{SCHEMA_NAME}.feedbacks', 'U') IS NULL
        CREATE TABLE {SCHEMA_NAME}.feedbacks (
            id INT IDENTITY(1,1) PRIMARY KEY,
            submission_id INT NOT NULL,
            reviewer_name NVARCHAR(255) NOT NULL,
            comment NVARCHAR(500) NOT NULL,
            rating INT NOT NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
        """)

        cursor.execute(f"""
        IF NOT EXISTS (SELECT 1 FROM {SCHEMA_NAME}.feedbacks)
        INSERT INTO {SCHEMA_NAME}.feedbacks (submission_id, reviewer_name, comment, rating)
        VALUES
        (1, 'Gallery Curator', 'Strong composition and good use of color.', 5),
        (2, 'Art Reviewer', 'Interesting concept, but needs more detail.', 4),
        (3, 'Exhibition Manager', 'Not suitable for the current gallery theme.', 3);
        """)

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Feedback schema, table and stub data created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedbacks")
def get_feedbacks():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, submission_id, reviewer_name, comment, rating, created_at
        FROM {SCHEMA_NAME}.feedbacks
        ORDER BY id;
        """)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "submission_id": row.submission_id,
                "reviewer_name": row.reviewer_name,
                "comment": row.comment,
                "rating": row.rating,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedbacks/{feedback_id}")
def get_feedback_by_id(feedback_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, submission_id, reviewer_name, comment, rating, created_at
        FROM {SCHEMA_NAME}.feedbacks
        WHERE id = ?;
        """, feedback_id)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Feedback not found")

        return {
            "id": row.id,
            "submission_id": row.submission_id,
            "reviewer_name": row.reviewer_name,
            "comment": row.comment,
            "rating": row.rating,
            "created_at": str(row.created_at)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedbacks/submission/{submission_id}")
def get_feedbacks_by_submission(submission_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, submission_id, reviewer_name, comment, rating, created_at
        FROM {SCHEMA_NAME}.feedbacks
        WHERE submission_id = ?
        ORDER BY id;
        """, submission_id)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "submission_id": row.submission_id,
                "reviewer_name": row.reviewer_name,
                "comment": row.comment,
                "rating": row.rating,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedbacks")
def create_feedback(feedback: FeedbackCreate):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        INSERT INTO {SCHEMA_NAME}.feedbacks (submission_id, reviewer_name, comment, rating)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?);
        """, feedback.submission_id, feedback.reviewer_name, feedback.comment, feedback.rating)

        new_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "message": "Feedback created",
            "id": new_id,
            "submission_id": feedback.submission_id,
            "reviewer_name": feedback.reviewer_name,
            "comment": feedback.comment,
            "rating": feedback.rating
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))