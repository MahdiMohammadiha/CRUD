from fastapi import FastAPI
from os import getenv
from dotenv import load_dotenv
from utils import export_schema_summary
from inspectors import PostgresInspector


app = FastAPI()
API_ROOT = "/"


@app.get(API_ROOT)
def root():
    load_dotenv()
    with PostgresInspector(
        dbname = getenv("DBNAME"),
        user = getenv("USER"),
        password = getenv("PASSWORD"),
        host = getenv("HOST")
    ) as inspector:
        data = export_schema_summary(inspector, getenv("SCHEMA"))

    return data
