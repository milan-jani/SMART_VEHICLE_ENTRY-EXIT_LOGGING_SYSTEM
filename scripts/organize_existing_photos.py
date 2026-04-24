import os
import shutil
from datetime import datetime

def organize_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    print(f"Organizing files in: {folder_path}")
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    for filename in files:
        if filename == ".gitkeep": continue
        
        file_path = os.path.join(folder_path, filename)
        
        # Get creation time (fallback to modification time if ctime not reliable)
        mtime = os.path.getmtime(file_path)
        date_str = datetime.fromtimestamp(mtime).strftime("%d-%m-%Y")
        
        target_dir = os.path.join(folder_path, date_str)
        os.makedirs(target_dir, exist_ok=True)
        
        target_path = os.path.join(target_dir, filename)
        
        try:
            shutil.move(file_path, target_path)
            print(f"  Moved: {filename} -> {date_str}/")
        except Exception as e:
            print(f"  Error moving {filename}: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Organize Vehicle Photos
    organize_folder(os.path.join(base_dir, "data", "photos"))
    
    # Organize ID Cards
    organize_folder(os.path.join(base_dir, "data", "id_cards"))
    
    print("\nOrganization complete!")
