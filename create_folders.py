import os
from pathlib import Path

# Choose your project location
PROJECT_PATH = r"D:\traffic-project"

print("=" * 60)
print("RTINA Traffic System - Folder Structure Creator")
print("=" * 60)

# Create main project folder
try:
    Path(PROJECT_PATH).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created project root: {PROJECT_PATH}\n")
except Exception as e:
    print(f"✗ Error creating project root: {e}")
    exit(1)

# Define all folders to create
folders = [
    "backend",
    "backend\\videos",
    "backend\\data",
    "frontend",
    "frontend\\assets",
    "data",
    "docs",
    "logs"
]

print("Creating subdirectories...\n")

# Create each folder
for folder in folders:
    folder_path = Path(PROJECT_PATH) / folder
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {folder}")
    except Exception as e:
        print(f"  ✗ {folder} - Error: {e}")

print("\n" + "=" * 60)
print("FOLDER STRUCTURE CREATED:")
print("=" * 60)

# Display the created structure
def print_tree(path, prefix="", is_last=True):
    """Print folder structure in tree format"""
    try:
        items = sorted(os.listdir(path))
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        
        for i, dir_name in enumerate(dirs):
            is_last_item = i == len(dirs) - 1
            print(f"{prefix}{'└── ' if is_last_item else '├── '}{dir_name}/")
            
            extension = "    " if is_last_item else "│   "
            print_tree(os.path.join(path, dir_name), prefix + extension, is_last_item)
    except PermissionError:
        pass

print(f"\n{Path(PROJECT_PATH).name}/")
print_tree(PROJECT_PATH)

print("\n" + "=" * 60)
print("✓ ALL FOLDERS CREATED SUCCESSFULLY!")
print("=" * 60)

print(f"""
Next Steps:

1. Copy Python files to: {PROJECT_PATH}\\backend\\
   - config.py
   - database.py
   - video_processor.py
   - pathfinding.py
   - app.py
   - requirements.txt
   - environment.yml

2. Copy data files to: {PROJECT_PATH}\\data\\
   - nagpur_roads.json

3. Copy frontend files to: {PROJECT_PATH}\\frontend\\
   - index.html
   - style.css
   - script.js

4. Place your 5 MP4 videos in: {PROJECT_PATH}\\backend\\videos\\
   - intersection_1.mp4
   - intersection_2.mp4
   - intersection_3.mp4
   - intersection_4.mp4
   - intersection_5.mp4

5. Create Anaconda environment:
   cd {PROJECT_PATH}
   conda env create -f environment.yml

6. Activate and run:
   conda activate rtina-env
   python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

7. Open in browser:
   http://localhost:8000
""")

input("\nPress Enter to close...")