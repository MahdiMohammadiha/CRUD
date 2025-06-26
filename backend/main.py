from fastapi import FastAPI, HTTPException
from os import getenv
from dotenv import load_dotenv
from inspectors import PostgresInspector
from utils import export_schema_summary
import psycopg2.extras


# Load .env variables
load_dotenv()

# FastAPI application
app = FastAPI()

# Default schema name
SCHEMA = getenv("SCHEMA", "public")

# Global PostgresInspector instance (shared)
inspector: PostgresInspector | None = None


def check_connection():
    if not inspector or not inspector.conn:
        raise HTTPException(status_code=500, detail="Database not connected")


# Run once when the app starts
@app.on_event("startup")
def startup():
    global inspector
    inspector = PostgresInspector(
        dbname=getenv("DBNAME"),
        user=getenv("USER"),
        password=getenv("PASSWORD"),
        host=getenv("HOST"),
    )
    inspector.connect()


# Run once when the app shuts down
@app.on_event("shutdown")
def shutdown():
    global inspector
    if inspector:
        inspector.close()
        inspector = None


# Root endpoint: returns table + column summary
@app.get("/")
def root():
    check_connection()
    data = export_schema_summary(inspector, SCHEMA)
    return data


# List all tables with their API paths
@app.get("/api/tables")
def list_tables():
    check_connection()
    tables = inspector.get_tables(schema=SCHEMA)
    return [{"table": table, "api": f"/api/tables/{table}"} for table in tables]


# Get all rows from a specific table (max 100)
@app.get("/api/tables/{table_name}")
def get_table_data(table_name: str):
    check_connection()
    try:
        cur = inspector.cursor
        cur.execute(f'SELECT * FROM "{SCHEMA}"."{table_name}" LIMIT 100')
        rows = cur.fetchall()
        return rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Get column metadata for a specific table
@app.get("/api/tables/{table_name}/schema")
def get_table_schema(table_name: str):
    check_connection()
    tables = inspector.get_tables(schema=SCHEMA)
    if table_name not in tables:
        raise HTTPException(status_code=404, detail="Table not found")
    columns = inspector.get_columns(table_name)
    return columns
