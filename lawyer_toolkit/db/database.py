import sqlite3
import pathlib
import os

DB_DIR = pathlib.Path(__file__).parent
DB_PATH = DB_DIR / "lawyer.db"

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        case_number TEXT,
        case_type TEXT,
        status TEXT,
        last_session TEXT,
        next_session TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

def add_client(name, phone=None, email=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (name, phone, email, notes)
        VALUES (?, ?, ?, ?)
    """, (name, phone, email, notes))
    conn.commit()
    client_id = cursor.lastrowid
    conn.close()
    return client_id

def get_all_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_client_by_id(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_client(client_id, name, phone=None, email=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE clients
        SET name = ?, phone = ?, email = ?, notes = ?
        WHERE id = ?
    """, (name, phone, email, notes, client_id))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()

def add_case(client_id, case_number=None, case_type=None, status=None, last_session=None, next_session=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cases (client_id, case_number, case_type, status, last_session, next_session, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (client_id, case_number, case_type, status, last_session, next_session, notes))
    conn.commit()
    case_id = cursor.lastrowid
    conn.close()
    return case_id

def get_cases(case_type=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM cases WHERE 1=1"
    params = []
    
    if case_type:
        query += " AND case_type = ?"
        params.append(case_type)
        
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_cases_by_client(client_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_case(case_id, case_number=None, case_type=None, status=None, last_session=None, next_session=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cases
        SET case_number = ?, case_type = ?, status = ?, last_session = ?, next_session = ?, notes = ?
        WHERE id = ?
    """, (case_number, case_type, status, last_session, next_session, notes, case_id))
    conn.commit()
    conn.close()

def delete_case(case_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    conn.close()

def get_client_case_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, COUNT(ca.id) as case_count 
        FROM clients c 
        LEFT JOIN cases ca ON c.id = ca.client_id 
        GROUP BY c.id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
