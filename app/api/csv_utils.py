"""
CSV Utilities
All CSV read/write operations for vehicle logging
"""
import csv
import os
from typing import List, Tuple, Optional, Dict

# CSV file path - now using data/visitors.csv at project root
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "visitors.csv")
CSV_HEADER = ["Vehicle_No", "Visitor_Name", "Phone", "Purpose", "In_Time", "Out_Time", "Image_Path"]


def ensure_csv():
    """
    Ensure CSV file exists with proper headers
    Creates the file and directory if they don't exist
    """
    path = os.path.abspath(CSV_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def append_entry(
    vehicle_no: str,
    image_path: str,
    in_time: str,
    name: str = "",
    phone: str = "",
    purpose: str = "",
    out_time: str = ""
) -> None:
    """
    Append a new vehicle entry to the CSV
    
    Args:
        vehicle_no: Vehicle number plate
        image_path: Path to captured image
        in_time: Entry timestamp
        name: Visitor name (optional)
        phone: Visitor phone (optional)
        purpose: Visit purpose (optional)
        out_time: Exit timestamp (optional)
    """
    ensure_csv()
    with open(os.path.abspath(CSV_PATH), "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([vehicle_no, name, phone, purpose, in_time, out_time, image_path])


def read_all_rows() -> List[List[str]]:
    """
    Read all rows from CSV including header
    
    Returns:
        List of rows (first row is header)
    """
    ensure_csv()
    with open(os.path.abspath(CSV_PATH), "r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    return reader


def find_last_open_entry(vehicle_no: str) -> Tuple[Optional[int], Optional[List[str]]]:
    """
    Find the last entry for a vehicle with no exit time
    
    Args:
        vehicle_no: Vehicle number to search for
    
    Returns:
        Tuple of (row_index, row_data) or (None, None) if not found
        Index refers to position in the list (0 = header)
    """
    rows = read_all_rows()
    # Search backwards from end, skip header
    for idx in range(len(rows) - 1, 0, -1):
        row = rows[idx]
        if len(row) >= 6 and row[0] == vehicle_no and (row[5] == "" or row[5] is None):
            return idx, row
    return None, None


def update_out_time(vehicle_no: str, out_time: str) -> bool:
    """
    Update the exit time for the last open entry of a vehicle
    
    Args:
        vehicle_no: Vehicle number
        out_time: Exit timestamp
    
    Returns:
        True if successful, False if no open entry found
    """
    idx, row = find_last_open_entry(vehicle_no)
    if idx is None:
        return False
    
    rows = read_all_rows()
    rows[idx][5] = out_time
    
    # Write back all rows
    with open(os.path.abspath(CSV_PATH), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    return True


def update_visitor_details_for_last(
    vehicle_no: str,
    name: str,
    phone: str,
    purpose: str
) -> bool:
    """
    Update visitor details for the last open entry
    
    Args:
        vehicle_no: Vehicle number
        name: Visitor name
        phone: Visitor phone
        purpose: Visit purpose
    
    Returns:
        True if successful, False if no open entry found
    """
    idx, row = find_last_open_entry(vehicle_no)
    if idx is None:
        return False
    
    rows = read_all_rows()
    rows[idx][1] = name
    rows[idx][2] = phone
    rows[idx][3] = purpose
    
    with open(os.path.abspath(CSV_PATH), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    return True


def get_vehicle_stats() -> Dict:
    """
    Calculate statistics about vehicle entries
    
    Returns:
        Dictionary with various statistics
    """
    rows = read_all_rows()
    
    total_entries = len(rows) - 1  # Exclude header
    open_entries = 0
    closed_entries = 0
    unique_vehicles = set()
    
    for row in rows[1:]:  # Skip header
        if len(row) >= 7:
            unique_vehicles.add(row[0])
            if row[5] == "" or row[5] is None:
                open_entries += 1
            else:
                closed_entries += 1
    
    return {
        "total_entries": total_entries,
        "open_entries": open_entries,
        "closed_entries": closed_entries,
        "unique_vehicles": len(unique_vehicles)
    }
