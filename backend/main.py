from fastapi import FastAPI, HTTPException, Request, Body
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


# List all tables with their API paths
@app.get("/api/tables")
def list_tables():
    check_connection()
    tables = inspector.get_tables(schema=SCHEMA)
    return [{"table": table, "api": f"/api/tables/{table}"} for table in tables]


# Returns table + column summary
@app.get("/api/tables/schema")
def get_database_schema():
    check_connection()
    data = export_schema_summary(inspector, SCHEMA)
    return data


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


from fastapi import Body


@app.post("/api/tables/{table_name}")
def insert_row(table_name: str, data: dict = Body(...)):
    check_connection()

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail="Request body must be a JSON object"
        )

    try:
        columns = list(data.keys())
        values = list(data.values())

        placeholders = ", ".join(["%s"] * len(values))
        col_names = ", ".join(f'"{col}"' for col in columns)

        query = f'INSERT INTO "{SCHEMA}"."{table_name}" ({col_names}) VALUES ({placeholders}) RETURNING *'

        cur = inspector.cursor
        cur.execute(query, values)
        inserted = cur.fetchone()
        inspector.conn.commit()

        return inserted

    except Exception as e:
        inspector.conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/tables/{table_name}/{row_id}")
def update_row(table_name: str, row_id: str, request: Request, data: dict = Body(...)):
    check_connection()

    pk_column = inspector.get_primary_key(table_name, SCHEMA)
    if not pk_column:
        raise HTTPException(status_code=400, detail="Primary key not found")

    try:
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400, detail="Request body must be a JSON object"
            )

        columns = list(data.keys())
        values = list(data.values())

        assignments = ", ".join(f'"{col}" = %s' for col in columns)
        query = f"""
            UPDATE "{SCHEMA}"."{table_name}"
            SET {assignments}
            WHERE "{pk_column}" = %s
            RETURNING *
            """

        cur = inspector.cursor
        cur.execute(query, values + [row_id])
        updated = cur.fetchone()
        inspector.conn.commit()

        if not updated:
            raise HTTPException(status_code=404, detail="Record not found")

        return updated

    except Exception as e:
        inspector.conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/tables/{table_name}/{row_id}")
def delete_row(table_name: str, row_id: str):
    check_connection()

    pk_column = inspector.get_primary_key(table_name, SCHEMA)
    if not pk_column:
        raise HTTPException(status_code=400, detail="Primary key not found")

    try:
        query = f"""
            DELETE FROM "{SCHEMA}"."{table_name}"
            WHERE "{pk_column}" = %s
            RETURNING *
        """

        cur = inspector.cursor
        cur.execute(query, (row_id,))
        deleted = cur.fetchone()
        inspector.conn.commit()

        if not deleted:
            raise HTTPException(status_code=404, detail="Record not found")

        return deleted

    except Exception as e:
        inspector.conn.rollback()
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
