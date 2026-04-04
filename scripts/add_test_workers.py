"""
Add Test Workers / Regular Users
Run this script to add some sample vehicles to the `regular_users` (whitelist) table.
You can use these plate numbers to test the 'Worker/Regular' entry flow.
Find any car image on Google with these numbers, or just type it in manually for testing.
"""
import sys
import os

# Add the project root to the python path so we can import the app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.api.db_sqlite import mark_regular_user, get_all_regular_users

def add_test_data():
    print("--- Adding Test Workers to Whitelist ---")
    
    # List of dummy workers (you can change these to match test images you have)
    test_workers = [
        {"plate": "DL7CQ1939", "name": "Ramesh Driver", "phone": "9876543210", "flat": "Staff"},
        {"plate": "MH01AB1234", "name": "Suresh Worker", "phone": "9998887776", "flat": "Admin"},
        {"plate": "KA05XYZ99", "name": "Priya Maid", "phone": "1112223334", "flat": "Maintenance"},
        {"plate": "UP14BT0001", "name": "Security Chief", "phone": "0000000000", "flat": "Security"},
        {"plate": "RJ14CV0002", "name": "VIP Manager", "phone": "1231231234", "flat": "Management"}
    ]
    
    for worker in test_workers:
        success = mark_regular_user(worker["plate"], worker["name"], worker["phone"], worker["flat"])
        if success:
            print(f"[SUCCESS] Added Worker: {worker['name']} ({worker['plate']})")
        else:
            print(f"[ERROR] Failed to add: {worker['plate']}")
            
    print("\n--- Current Regular Users in Database ---")
    users = get_all_regular_users()
    for u in users:
        print(f"Plate: {u['vehicle_no']} | Name: {u['user_name']} | Phone: {u['phone']}")

if __name__ == "__main__":
    add_test_data()
    print("\nDone! Now restart the backend server and try detecting one of these plates.")
