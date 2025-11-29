import threading, time, webbrowser
from datetime import datetime
import app.csv_utils as csv_utils
import app.server as server
from app.api import capture_with_preview

def main():
    plate_number, image_path = capture_with_preview(camera_index=0)  # or 1/2 if needed
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not plate_number:
        print(" No plate detected, exiting...")
        return

    idx, row = csv_utils.find_last_open_entry(plate_number)

    if idx is None:
        # New entry -> In_Time save + form show
        csv_utils.append_entry(plate_number, image_path, now_time)
        server.plate_number = plate_number

        server.app.run(host="0.0.0.0", port=5000, debug=False)

    else:
        # Existing open entry -> Out_Time fill
        csv_utils.update_out_time(plate_number, now_time)
        print(f"[EXIT] Vehicle {plate_number} exited at {now_time}")

if __name__ == "__main__":
    main()
