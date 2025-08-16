from fastapi import FastAPI, HTTPException, Request, Body
from os import getenv
from dotenv import load_dotenv
from inspectors import PostgresInspector
from utils import export_schema_summary
from fastapi.middleware.cors import CORSMiddleware


# Load environment variables from .env
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Dynamic PostgreSQL CRUD API",
    description="Auto-generated CRUD endpoints for any PostgreSQL schema.",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
SCHEMA: str = getenv("SCHEMA", "public")  # Default schema name
inspector = None  # Shared DB inspector instance


def check_connection() -> None:
    """
    Ensure that the global inspector is connected.
    Raises HTTP 500 if not connected.
    """
    if not inspector or not inspector.conn:
        raise HTTPException(status_code=500, detail="Database not connected")


# Application lifecycle events
@app.on_event("startup")
def startup() -> None:
    """
    Initialize global PostgresInspector and connect to the database
    when the FastAPI app starts.
    """
    global inspector
    inspector = PostgresInspector(
        dbname=getenv("DBNAME"),
        user=getenv("USER"),
        password=getenv("PASSWORD"),
        host=getenv("HOST"),
    )
    inspector.connect()


@app.on_event("shutdown")
def shutdown() -> None:
    """
    Close the database connection when the app shuts down.
    """
    global inspector
    if inspector:
        inspector.close()
        inspector = None


# ======================== API Endpoints ========================


@app.get("/api/tables")
def list_tables() -> list[dict[str, str]]:
    """
    List all tables in the configured schema.

    Returns:
        List of dicts containing:
        - table: Table name
        - api: Endpoint URL for accessing the table
    """
    check_connection()
    tables = inspector.get_tables(schema=SCHEMA)
    return [{"table": table, "api": f"/api/tables/{table}"} for table in tables]


@app.get("/api/tables/schema")
def get_database_schema() -> list:
    """
    Get database schema summary including tables and columns.
    """
    check_connection()
    return export_schema_summary(inspector, SCHEMA)


@app.get("/api/tables/{table_name}")
def get_table_data(table_name: str) -> list[tuple]:
    """
    Fetch up to 100 rows from the specified table.

    Args:
        table_name: Name of the table.

    Returns:
        List of rows (each row as a tuple).
    """
    check_connection()
    try:
        cur = inspector.cursor
        cur.execute(f'SELECT * FROM "{SCHEMA}"."{table_name}" LIMIT 100')
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tables/{table_name}")
def insert_row(table_name: str, data: dict = Body(...)) -> tuple:
    """
    Insert a new row into the specified table.

    Args:
        table_name: Target table.
        data: JSON object containing column-value pairs.

    Returns:
        The inserted row.
    """
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
def update_row(
    table_name: str, row_id: str, request: Request, data: dict = Body(...)
) -> tuple:
    """
    Update an existing row in the specified table.

    Args:
        table_name: Target table.
        row_id: Value of the primary key for the row to update.
        data: JSON object containing updated column-value pairs.

    Returns:
        The updated row.
    """
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
def delete_row(table_name: str, row_id: str) -> tuple:
    """
    Delete a row by its primary key.

    Args:
        table_name: Target table.
        row_id: Value of the primary key.

    Returns:
        The deleted row.
    """
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


@app.get("/api/tables/{table_name}/schema")
def get_table_schema(table_name: str) -> list[tuple[str, str]]:
    """
    Get metadata for all columns in a table.

    Args:
        table_name: Target table.

    Returns:
        List of (column_name, data_type) tuples.
    """
    check_connection()
    tables = inspector.get_tables(schema=SCHEMA)
    if table_name not in tables:
        raise HTTPException(status_code=404, detail="Table not found")
    return inspector.get_columns(table_name, schema=SCHEMA)


@app.get("/api/tables/{table_name}/pk")
def get_table_pk(table_name: str) -> str | None:
    """
    Get the primary key column name for a table.

    Args:
        table_name: Target table.

    Returns:
        Primary key column name or None.
    """
    check_connection()
    return inspector.get_primary_key(table_name, schema=SCHEMA)
