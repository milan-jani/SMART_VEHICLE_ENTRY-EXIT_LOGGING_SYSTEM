import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Assuming the data directory is at the root of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'smart_gate.db')

def get_db_connection() -> sqlite3.Connection:
    """Gets a connection to the SQLite database, ensuring thread safety if needed."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # Added timeout and check_same_thread for better Docker/FastAPI performance
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create visits table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_no TEXT NOT NULL,
        visitor_name TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        purpose TEXT DEFAULT '',
        in_time TEXT NOT NULL,
        out_time TEXT DEFAULT '',
        vehicle_image_path TEXT DEFAULT '',
        id_card_image_path TEXT DEFAULT '',
        visitor_type TEXT DEFAULT 'unknown',
        status TEXT DEFAULT 'inside'
    )
    ''')

    # Create indexes for fast querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_visits_vehicle_no ON visits(vehicle_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_visits_status ON visits(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_visits_in_time ON visits(in_time)')

    # Create regular_users table (whitelist)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS regular_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_no TEXT UNIQUE NOT NULL,
        user_name TEXT DEFAULT '',
        flat_no TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        id_type TEXT DEFAULT '',
        id_number TEXT DEFAULT '',
        id_card_front_path TEXT DEFAULT '',
        id_card_back_path TEXT DEFAULT '',
        dob TEXT DEFAULT '',
        address_street TEXT DEFAULT '',
        address_city TEXT DEFAULT '',
        address_state TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create staff table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        emp_code TEXT UNIQUE,
        department TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        room_no TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    
    # Initialize staff data
    init_staff_data_internal(cursor)
    conn.commit()
    
    # --- Phase 5: Kiosk fields migration ---
    # Safely add new columns if they don't exist (ALTER TABLE won't fail on existing)
    new_columns = [
        ("id_type", "TEXT DEFAULT ''"),
        ("id_number", "TEXT DEFAULT ''"),
        ("id_card_front_path", "TEXT DEFAULT ''"),
        ("id_card_back_path", "TEXT DEFAULT ''"),
        ("address_street", "TEXT DEFAULT ''"),
        ("address_city", "TEXT DEFAULT ''"),
        ("address_state", "TEXT DEFAULT ''"),
        ("dob", "TEXT DEFAULT ''"),
        ("person_to_meet", "TEXT DEFAULT ''"),
        ("flat_no", "TEXT DEFAULT ''"),
        ("num_persons", "INTEGER DEFAULT 1"),
        ("vehicle_type", "TEXT DEFAULT ''"),
        ("company", "TEXT DEFAULT ''"),
        ("expected_duration", "TEXT DEFAULT ''"),
        ("remarks", "TEXT DEFAULT ''"),
        ("address", "TEXT DEFAULT ''"),
    ]
    
    for col_name, col_def in new_columns:
        try:
            cursor.execute(f'ALTER TABLE visits ADD COLUMN {col_name} {col_def}')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
    # Safely add new columns to regular_users if they don't exist
    regular_new_columns = [
        ("id_type", "TEXT DEFAULT ''"),
        ("id_number", "TEXT DEFAULT ''"),
        ("id_card_front_path", "TEXT DEFAULT ''"),
        ("id_card_back_path", "TEXT DEFAULT ''"),
        ("dob", "TEXT DEFAULT ''"),
        ("address_street", "TEXT DEFAULT ''"),
        ("address_city", "TEXT DEFAULT ''"),
        ("address_state", "TEXT DEFAULT ''")
    ]
    
    for col_name, col_def in regular_new_columns:
        try:
            cursor.execute(f'ALTER TABLE regular_users ADD COLUMN {col_name} {col_def}')
        except sqlite3.OperationalError:
            pass # Column already exists
    
    conn.commit()
    conn.close()

# --- CRUD Operations for Visits ---

def create_visit(vehicle_no: str, image_path: str = "", visitor_type: str = "unknown") -> Optional[int]:
    """Creates a new visit record (entry). Returns the new visit ID."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO visits (vehicle_no, vehicle_image_path, in_time, visitor_type, status)
        VALUES (?, ?, ?, ?, 'inside')
    ''', (vehicle_no, image_path, in_time, visitor_type))
    
    visit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return visit_id

def close_visit(vehicle_no: str) -> bool:
    """Marks the latest open visit for a vehicle as 'exited'."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update the most recent 'inside' visit for this vehicle
    cursor.execute('''
        UPDATE visits 
        SET out_time = ?, status = 'exited'
        WHERE id = (
            SELECT id FROM visits
            WHERE vehicle_no = ? AND status = 'inside'
            ORDER BY in_time DESC LIMIT 1
        )
    ''', (out_time, vehicle_no))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_visit_details(visit_id: int, name: str, phone: str, purpose: str, id_card_path: str = "") -> bool:
    """Updates visitor details for a specific visit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE visits
        SET visitor_name = ?, phone = ?, purpose = ?, id_card_image_path = ?
        WHERE id = ?
    ''', (name, phone, purpose, id_card_path, visit_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_latest_visit_details_by_vehicle(vehicle_no: str, name: str, phone: str, purpose: str) -> bool:
    """Compatibility function: Updates details for the latest open visit of a vehicle."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Subquery to find the ID of the latest 'inside' visit for this vehicle
    cursor.execute('''
        UPDATE visits
        SET visitor_name = ?, phone = ?, purpose = ?
        WHERE id = (
            SELECT id FROM visits 
            WHERE vehicle_no = ? AND status = 'inside' 
            ORDER BY in_time DESC LIMIT 1
        )
    ''', (name, phone, purpose, vehicle_no))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# --- Query Operations for Visits ---

def get_all_visits(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves all visits, ordered by entry time descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM visits 
        ORDER BY in_time DESC LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_open_visits() -> List[Dict[str, Any]]:
    """Retrieves all currently 'inside' visits."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT * FROM visits WHERE status = 'inside' ORDER BY in_time DESC''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def find_open_visit_by_vehicle(vehicle_no: str) -> Optional[Dict[str, Any]]:
    """Finds an open ('inside') visit for a specific vehicle."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM visits 
        WHERE vehicle_no = ? AND status = 'inside' 
        ORDER BY in_time DESC LIMIT 1
    ''', (vehicle_no,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

# --- Regular Users (Whitelist) Operations ---

def is_regular_user(vehicle_no: str) -> bool:
    """Checks if a vehicle is in the regular users whitelist."""
    return get_regular_user(vehicle_no) is not None

def get_regular_user(vehicle_no: str) -> Optional[Dict[str, Any]]:
    """Retrieves regular user details if they exist in the whitelist."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM regular_users WHERE vehicle_no = ?', (vehicle_no,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def mark_regular_user(
        vehicle_no: str, 
        name: str = "", 
        phone: str = "", 
        flat_no: str = "",
        id_type: str = "",
        id_number: str = "",
        id_card_front_path: str = "",
        id_card_back_path: str = "",
        dob: str = "",
        address_street: str = "",
        address_city: str = "",
        address_state: str = ""
    ) -> bool:
    """Adds or updates a vehicle in the regular users whitelist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Use REPLACE to update if vehicle_no already exists (since it's UNIQUE)
    cursor.execute('''
        INSERT OR REPLACE INTO regular_users (
            vehicle_no, user_name, phone, flat_no, 
            id_type, id_number, id_card_front_path, id_card_back_path, 
            dob, address_street, address_city, address_state, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        vehicle_no, name, phone, flat_no, 
        id_type, id_number, id_card_front_path, id_card_back_path, 
        dob, address_street, address_city, address_state, created_at
    ))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_all_regular_users() -> List[Dict[str, Any]]:
    """Retrieves all regular users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM regular_users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_regular_user(vehicle_no: str) -> bool:
    """Removes a vehicle from the regular users whitelist."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM regular_users WHERE vehicle_no = ?', (vehicle_no,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# --- Dashboard & Statistics ---

def get_stats() -> Dict[str, Any]:
    """Calculates summary statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        "total_entries": 0,
        "currently_inside": 0,
        "unique_vehicles": 0,
        "regular_visits": 0,
        "visitor_visits": 0
    }
    
    # Total Entries
    cursor.execute('SELECT COUNT(*) FROM visits')
    stats["total_entries"] = cursor.fetchone()[0]
    
    # Currently Inside
    cursor.execute("SELECT COUNT(*) FROM visits WHERE status = 'inside'")
    stats["open_entries"] = cursor.fetchone()[0]
    
    # Exited
    cursor.execute("SELECT COUNT(*) FROM visits WHERE status = 'exited'")
    stats["closed_entries"] = cursor.fetchone()[0]
    
    # Unique Vehicles
    cursor.execute('SELECT COUNT(DISTINCT vehicle_no) FROM visits')
    stats["unique_vehicles"] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def delete_visit(visit_id: int) -> bool:
    """Deletes a visit record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM visits WHERE id = ?', (visit_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# --- Phase 5: Kiosk-specific operations ---

def update_kiosk_visit_details(vehicle_no: str, details: Dict[str, Any]) -> bool:
    """Updates all kiosk visitor details for the latest open visit of a vehicle."""
    vehicle_no = vehicle_no.strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build SET clause dynamically from provided details
    allowed_fields = [
        'visitor_name', 'phone', 'purpose', 'id_type', 'id_number',
        'id_card_front_path', 'id_card_back_path', 'address_street',
        'address_city', 'address_state', 'address', 'dob',
        'person_to_meet', 'flat_no', 'num_persons', 'vehicle_type',
        'company', 'expected_duration', 'remarks'
    ]
    
    set_parts = []
    values = []
    for field in allowed_fields:
        if field in details:
            set_parts.append(f"{field} = ?")
            values.append(details[field])
    
    if not set_parts:
        conn.close()
        return False
    
    set_clause = ", ".join(set_parts)
    values.append(vehicle_no)
    
    cursor.execute(f'''
        UPDATE visits
        SET {set_clause}
        WHERE id = (
            SELECT id FROM visits 
            WHERE vehicle_no = ? AND status = 'inside' 
            ORDER BY in_time DESC LIMIT 1
        )
    ''', values)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def init_staff_data_internal(cursor):
    """Internal helper to seed staff data."""
    cursor.execute("SELECT COUNT(*) FROM staff")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        staff_list = [
            ("Milan Jani", "442", "ICT Department", "9876543210", "milanjani707@gmail.com", "MA115"),
            ("Rajesh Kumar", "101", "Administration", "9988776655", "rajesh.admin@example.com", "MB001"),
            ("Sneha Patel", "205", "Human Resources", "9123456789", "sneha.hr@example.com", "MA158"),
            ("Amit Shah", "330", "Security", "9555554444", "amit.security@example.com", "G001"),
            ("Priya Sharma", "445", "ICT Department", "9666667777", "priya.ict@example.com", "MA116")
        ]
        cursor.executemany('''
            INSERT INTO staff (name, emp_code, department, phone, email, room_no, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [(s[0], s[1], s[2], s[3], s[4], s[5], now) for s in staff_list])

def search_staff(query: str):
    """Searches for staff by name or department."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_query = f"%{query}%"
    cursor.execute("""
        SELECT name, emp_code, department, email, room_no 
        FROM staff 
        WHERE name LIKE ? OR department LIKE ? OR emp_code LIKE ?
        LIMIT 5
    """, (search_query, search_query, search_query))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize the DB schema when this module is imported
init_db()
