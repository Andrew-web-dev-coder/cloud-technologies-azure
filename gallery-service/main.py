import os
import pyodbc
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

app = FastAPI(title="Gallery Service")

SCHEMA_NAME = "aleksandr_gallery"


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


class GalleryCreate(BaseModel):
    name: str
    location: str
    schedule: Optional[str] = "Monday-Friday 10:00-18:00"


@app.get("/")
def root():
    return {"service": "Gallery Service", "status": "running"}


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
        IF OBJECT_ID('{SCHEMA_NAME}.galleries', 'U') IS NULL
        CREATE TABLE {SCHEMA_NAME}.galleries (
            id INT IDENTITY(1,1) PRIMARY KEY,
            name NVARCHAR(255) NOT NULL,
            location NVARCHAR(255) NOT NULL,
            schedule NVARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
        """)

        cursor.execute(f"""
        IF NOT EXISTS (SELECT 1 FROM {SCHEMA_NAME}.galleries)
        INSERT INTO {SCHEMA_NAME}.galleries (name, location, schedule)
        VALUES
        ('Modern Art Gallery', 'Vilnius', 'Monday-Friday 10:00-18:00'),
        ('Classic Art Hall', 'Kaunas', 'Tuesday-Saturday 11:00-19:00'),
        ('Student Digital Gallery', 'Online', '24/7');
        """)

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Gallery schema, table and stub data created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/galleries")
def get_galleries():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, name, location, schedule, created_at
        FROM {SCHEMA_NAME}.galleries
        ORDER BY id;
        """)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "name": row.name,
                "location": row.location,
                "schedule": row.schedule,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/galleries/{gallery_id}")
def get_gallery_by_id(gallery_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, name, location, schedule, created_at
        FROM {SCHEMA_NAME}.galleries
        WHERE id = ?;
        """, gallery_id)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Gallery not found")

        return {
            "id": row.id,
            "name": row.name,
            "location": row.location,
            "schedule": row.schedule,
            "created_at": str(row.created_at)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/galleries/location/{location}")
def get_galleries_by_location(location: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        SELECT id, name, location, schedule, created_at
        FROM {SCHEMA_NAME}.galleries
        WHERE location = ?
        ORDER BY id;
        """, location)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "name": row.name,
                "location": row.location,
                "schedule": row.schedule,
                "created_at": str(row.created_at)
            })

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/galleries")
def create_gallery(gallery: GalleryCreate):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
        INSERT INTO {SCHEMA_NAME}.galleries (name, location, schedule)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?);
        """, gallery.name, gallery.location, gallery.schedule)

        new_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "message": "Gallery created",
            "id": new_id,
            "name": gallery.name,
            "location": gallery.location,
            "schedule": gallery.schedule
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))