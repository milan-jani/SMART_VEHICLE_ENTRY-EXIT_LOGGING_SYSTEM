import cv2
import requests
import time

API_KEY = "be5b13c29a83097837f0a4983efc62a5e1bb6d98"

def capture_with_preview(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise Exception("❌ Camera not found.")

    print("📸 Press 'h' to capture photo and detect number plate")
    print("❌ Press 'q' to quit")

    plate_number, filename = None, None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        cv2.imshow("Live Preview", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('h'):
            filename = f"images/capture_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"🖼️ Saved {filename}")

            # API call
            with open(filename, 'rb') as img_file:
                response = requests.post(
                    'https://api.platerecognizer.com/v1/plate-reader/',
                    files=dict(upload=img_file),
                    headers={'Authorization': f'Token {API_KEY}'}
                )
            result = response.json()

            if result.get("results"):
                plate_number = result["results"][0]["plate"].upper()
                print("✅ Detected Plate:", plate_number)
                break
            else:
                print("❌ No plate detected.")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return plate_number, filename
