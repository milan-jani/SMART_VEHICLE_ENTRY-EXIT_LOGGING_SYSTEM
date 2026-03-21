import os
import requests
import sys

def download_file(url, local_path):
    print(f"Downloading YOLOv8 License Plate Model from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            downloaded = 0
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total_size) if total_size > 0 else 0
                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} bytes")
                sys.stdout.flush()
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"\nError downloading file: {e}")
        return False

if __name__ == "__main__":
    # Standard YOLOv8 License Plate Model from public GitHub repo mentioned in research
    model_url = "https://github.com/Muhammad-Zeerak-Khan/Automatic-License-Plate-Recognition-using-YOLOv8/raw/main/license_plate_detector.pt"
    
    project_root = os.path.join(os.path.dirname(__file__), "..")
    models_dir = os.path.join(project_root, "app", "device", "models")
    model_path = os.path.join(models_dir, "license_plate_detector.pt")
    
    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
    else:
        download_file(model_url, model_path)
