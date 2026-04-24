import os
import shutil
import hashlib

def get_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def safe_move_or_delete(src, dest_dir, archived_dir):
    if not os.path.exists(src): return
    
    filename = os.path.basename(src)
    dest_path = os.path.join(dest_dir, filename)
    
    # If same file exists in destination (like docs/), check MD5
    if os.path.exists(dest_path):
        try:
            if get_md5(src) == get_md5(dest_path):
                print(f"[DELETE DUPLICATE] {src} is same as {dest_path}")
                # Move to a duplicates folder inside archive to be 100% safe
                dup_dir = os.path.join(archived_dir, "duplicates")
                os.makedirs(dup_dir, exist_ok=True)
                # If target also exists in duplicates, append index
                target = os.path.join(dup_dir, filename)
                if os.path.exists(target):
                    target = os.path.join(dup_dir, f"dup_{filename}")
                shutil.move(src, target)
                return
        except Exception as e:
            print(f"[ERROR] Could not compare {src}: {e}")
            
    # Move to archived folder if not a core file
    os.makedirs(archived_dir, exist_ok=True)
    target = os.path.join(archived_dir, filename)
    if os.path.exists(target):
        target = os.path.join(archived_dir, f"new_{filename}")
    shutil.move(src, target)
    print(f"[MOVED] {src} -> {target}")

# Define paths
ROOT = r"d:\PROJECTS\Smart_vehicle_entry-exit_logging_system"
ARCHIVE = os.path.join(ROOT, "archived_legacy_tests")
DATA_PHOTOS = os.path.join(ROOT, "data", "photos")
DATA_ID = os.path.join(ROOT, "data", "id_cards")
DOCS = os.path.join(ROOT, "docs")

# Ensure DATA folders exist
os.makedirs(DATA_PHOTOS, exist_ok=True)
os.makedirs(DATA_ID, exist_ok=True)

# 1. Clean Root Files
root_files_to_archive = [
    "2.0.0", "4.10.0", "old_id_scan.py", "pip_install_log.txt", 
    "scan_image.py", "test_id_cam.py", "test_kiosk_ui.bat", "test_ocr.py",
    "PROJECT_ORGANIZATION.md", "QUICK_START.md", "dev_mode.bat", "dev_mode.sh"
]

docs_candidates = [
    "ARCHITECTURE.md", "CONTINUOUS_MONITORING.md", "DASHBOARD_REFRESH_GUIDE.md",
    "FIX_ENTRY_EXIT_LOGIC.md", "MIGRATION_GUIDE.md", "REFACTORING_SUMMARY.md", "TESTING_CHECKLIST.md"
]

for f in root_files_to_archive:
    safe_move_or_delete(os.path.join(ROOT, f), DATA_PHOTOS, os.path.join(ARCHIVE, "root_items"))

for f in docs_candidates:
    safe_move_or_delete(os.path.join(ROOT, f), DOCS, os.path.join(ARCHIVE, "docs_redundant"))

# 2. Clean App Legacy
app_legacy = ["api.py", "anpr.py", "camera.py", "config.py"]
for f in app_legacy:
    safe_move_or_delete(os.path.join(ROOT, "app", f), os.path.join(ROOT, "app", "device"), os.path.join(ARCHIVE, "app_legacy"))

# 3. Move git_ANPR
git_anpr_path = os.path.join(ROOT, "git_ANPR")
if os.path.exists(git_anpr_path):
    try:
        shutil.move(git_anpr_path, os.path.join(ARCHIVE, "git_ANPR"))
        print("[MOVED] git_ANPR folder to archive")
    except Exception as e:
        print(f"[ERROR] Moving git_ANPR: {e}")

# 4. Organize Images
for img_folder in ["images", "tests"]:
    src_folder = os.path.join(ROOT, img_folder)
    if os.path.exists(src_folder):
        for f in os.listdir(src_folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                src_file = os.path.join(src_folder, f)
                # For images, we just move them to data/photos
                # If name conflict, rename
                dest_file = os.path.join(DATA_PHOTOS, f)
                if os.path.exists(dest_file):
                    dest_file = os.path.join(DATA_PHOTOS, f"from_{img_folder}_{f}")
                shutil.move(src_file, dest_file)
                print(f"[IMAGE MOVED] {src_file} -> {dest_file}")
        
        # Check if folder is now empty and remove
        try:
            if not os.listdir(src_folder):
                os.rmdir(src_folder)
                print(f"[REMOVED EMPTY FOLDER] {img_folder}")
        except:
            pass

print("\nCleanup Complete!")
