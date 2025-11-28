# app/csv_utils.py
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "visitors.csv")
CSV_HEADER = ["Vehicle_No", "Visitor_Name", "Phone", "Purpose", "In_Time", "Out_Time", "Image_Path"]

def ensure_csv():
    path = os.path.abspath(CSV_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)

def append_entry(vehicle_no, image_path, in_time, name="", phone="", purpose="", out_time=""):
    ensure_csv()
    with open(os.path.abspath(CSV_PATH), "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([vehicle_no, name, phone, purpose, in_time, out_time, image_path])

def read_all_rows():
    ensure_csv()
    with open(os.path.abspath(CSV_PATH), "r", newline="") as f:
        reader = list(csv.reader(f))
    return reader  # includes header as first row

def find_last_open_entry(vehicle_no):
    """
    Return (index_in_list, row) of last row with vehicle_no and empty Out_Time.
    Index refers to position in the list returned by read_all_rows() (0 = header).
    If none found, returns (None, None)
    """
    rows = read_all_rows()
    # skip header:
    for idx in range(len(rows)-1, 0, -1):
        row = rows[idx]
        if len(row) >= 6 and row[0] == vehicle_no and (row[5] == "" or row[5] is None):
            return idx, row
    return None, None

def update_out_time(vehicle_no, out_time):
    idx, row = find_last_open_entry(vehicle_no)
    if idx is None:
        return False
    rows = read_all_rows()
    rows[idx][5] = out_time
    # write back all rows
    with open(os.path.abspath(CSV_PATH), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return True

def update_visitor_details_for_last(vehicle_no, name, phone, purpose):
    idx, row = find_last_open_entry(vehicle_no)
    if idx is None:
        return False
    rows = read_all_rows()
    rows[idx][1] = name
    rows[idx][2] = phone
    rows[idx][3] = purpose
    with open(os.path.abspath(CSV_PATH), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return True
