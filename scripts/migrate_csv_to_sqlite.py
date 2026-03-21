import os
import csv
import sqlite3
from datetime import datetime
import sys

# Ensure this script runs relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.api.db_sqlite import get_db_connection, init_db

CSV_PATH = os.path.join(BASE_DIR, 'data', 'visitors.csv')

def run_migration():
    print(f"Starting migration from {CSV_PATH} to SQLite database...")
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        print("Migration skipped.")
        return

    # Ensure DB and tables exist
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    migrated_count = 0
    error_count = 0

    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                # Map CSV columns to SQLite schema
                vehicle_no = row.get('Vehicle Number', '').strip()
                visitor_name = row.get('Visitor Name', '').strip()
                phone = row.get('Phone Number', '').strip()
                purpose = row.get('Purpose of Visit', '').strip()
                in_time = row.get('In Time', '').strip()
                out_time = row.get('Out Time', '').strip()
                image_path = row.get('Image Path', '').strip()
                
                # If there's no vehicle number or in_time, skip the row
                if not vehicle_no or not in_time:
                    print(f"Warning: Skipping incomplete row -> {row}")
                    error_count += 1
                    continue
                
                # Determine status
                status = 'exited' if out_time and out_time != 'N/A' and out_time != '-' else 'inside'
                if out_time in ('N/A', '-'):
                    out_time = ''
                    
                # We don't have visitor_type in the old CSV, so default to 'visitor'
                # (You can manually update frequent visitors to 'regular' later)
                visitor_type = 'visitor'

                cursor.execute('''
                    INSERT INTO visits (
                        vehicle_no, visitor_name, phone, purpose, 
                        in_time, out_time, vehicle_image_path, visitor_type, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vehicle_no, visitor_name, phone, purpose, 
                    in_time, out_time, image_path, visitor_type, status
                ))
                
                migrated_count += 1
                
            except Exception as e:
                print(f"Error migrating row {row}: {e}")
                error_count += 1

    conn.commit()
    conn.close()

    print("\n--- Migration Complete ---")
    print(f"Successfully migrated records: {migrated_count}")
    print(f"Skipped/Errors: {error_count}")
    print("You can now safely delete or archive visitors.csv")

if __name__ == "__main__":
    run_migration()
