# 🚀 CRUD - Dynamic PostgreSQL CRUD App

[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

A **full-featured dynamic CRUD project** for PostgreSQL.  
This app automatically generates **CRUD APIs** for every table in your database,  
with both **web** and **desktop** interfaces for easy data management. The project includes:

- **Backend:** FastAPI server that dynamically creates CRUD endpoints for each database table.
- **Web UI:** JavaScript-based web interface for viewing and managing tables and records.
- **Desktop UI:** PyQt6 desktop interface with similar features for local management.


## ✨ Features

- **Dynamic Table Connection:** Works with any PostgreSQL database and any number of tables.
- **Automatic API Generation:** CRUD endpoints are created for every table.
- **Simple & Fast UI:** Both web and desktop interfaces allow you to select tables and manage records.
- **Add, Edit, Delete Records:** Full CRUD operations supported.
- **Column Type & Primary Key Display:** See data types and primary keys for each column.
- **Web Sorting:** Sort data easily in the web interface.
- **CORS Support:** Seamless frontend-backend connection.


## 📁 Project Structure
```
CRUD/
 ├─ .gitignore
 ├─ LICENSE
 ├─ README.md
 ├─ backend/                # FastAPI server and database utilities
 │   ├─ main.py
 │   ├─ utils.py
 │   ├─ inspectors.py
 │   ├─ requirements.txt
 │   └─ exit_uvicorn.txt
 ├─ desktop/                # PyQt6 desktop UI
 │   ├─ main.py
 │   └─ requirements.txt
 ├─ web/                    # JavaScript web UI
 │   └─ index.html
 └─ docs/                   # Documentation and styles
     ├─ index.html
     ├─ style.css
     ├─ script.js
     └─ todo.md
```


## ⚡ Quick Start

### 1. Setup project environment
Create a `.env` file with your PostgreSQL info:
```env
DBNAME=your_db_name
USER=your_db_user
PASSWORD=your_db_password
HOST=your_db_ip
SCHEMA=public
```

Create and activate a virtual environment:

**Windows**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```


### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```


### 3. Desktop UI
```bash
cd desktop
pip install -r requirements.txt
python main.py
```


### 4. Web UI
Just open `web/index.html` in your browser.


## 🛠️ API Documentation

- `GET /api/tables` → List all tables  
- `GET /api/tables/{table}/schema` → Get columns & types  
- `GET /api/tables/{table}` → Fetch records  
- `POST /api/tables/{table}` → Add record  
- `PUT /api/tables/{table}/{pk}` → Update record  
- `DELETE /api/tables/{table}/{pk}` → Delete record  

**Example Request**
```bash
curl http://127.0.0.1:8000/api/tables
```


## 📜 License
This project is licensed under the **MIT License**.  
See [LICENSE](LICENSE) for details.


## 💡 Contribution
Contributions are welcome!  
If you have any **ideas, suggestions, or bug reports**, please open an issue or submit a PR.  

---

👨‍💻 Created by *Mahdi Mohammadiha* — © 2025 CRUD Project
