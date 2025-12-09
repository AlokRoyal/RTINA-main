# RTINA Traffic System - Automated Setup Script
# Save as: setup.py
# Run: python setup.py

import os
import sys
from pathlib import Path
import shutil
import subprocess

class RTINASetup:
    def __init__(self, project_path="C:\\traffic-project"):
        self.project_path = Path(project_path)
        self.backend_path = self.project_path / "backend"
        self.frontend_path = self.project_path / "frontend"
        self.data_path = self.project_path / "data"
        self.videos_path = self.backend_path / "videos"
        
    def print_header(self, text):
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60 + "\n")
    
    def print_step(self, step_num, text):
        print(f"\n[STEP {step_num}] {text}")
        print("-" * 50)
    
    def create_folders(self):
        """Create all necessary folder structure"""
        self.print_step(1, "Creating Folder Structure")
        
        folders = [
            self.project_path,
            self.backend_path,
            self.backend_path / "data",
            self.videos_path,
            self.frontend_path,
            self.frontend_path / "assets",
            self.data_path,
            self.project_path / "docs",
            self.project_path / "logs"
        ]
        
        for folder in folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created: {folder}")
            except Exception as e:
                print(f"✗ Failed to create {folder}: {e}")
                return False
        
        print("\n✓ All folders created successfully!")
        return True
    
    def create_init_files(self):
        """Create __init__.py files"""
        self.print_step(2, "Creating Python Package Files")
        
        init_files = [
            self.backend_path / "__init__.py",
            self.frontend_path / "__init__.py",
            self.data_path / "__init__.py"
        ]
        
        for init_file in init_files:
            try:
                if not init_file.exists():
                    init_file.write_text("")
                    print(f"✓ Created: {init_file}")
            except Exception as e:
                print(f"✗ Failed to create {init_file}: {e}")
        
        return True
    
    def create_config_file(self):
        """Create config.py if missing"""
        self.print_step(3, "Creating Configuration File")
        
        config_path = self.backend_path / "config.py"
        
        if config_path.exists():
            print("✓ config.py already exists, skipping")
            return True
        
        config_content = '''# RTINA Traffic System - Configuration
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
VIDEOS_DIR = BACKEND_DIR / "videos"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'data' / 'traffic.db'}"

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

YOLO_MODEL = "yolov8n.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_DEVICE = "cpu"
VEHICLE_CLASSES = [2, 3, 5, 7]

VIDEO_SNAPSHOT_INTERVAL = 15
VIDEO_FRAME_SKIP = 10
VIDEO_RESIZE_WIDTH = 640
VIDEO_RESIZE_HEIGHT = 480
MAX_CONCURRENT_VIDEOS = 5

CONGESTION_THRESHOLD = 80
ROUTE_UPDATE_TIMEOUT = 3

INTERSECTIONS = {
    1: {"name": "High Court Square", "lat": 21.1458, "lon": 79.0882, "capacity": 70, "road_width": 4},
    2: {"name": "Sitabuldi Junction", "lat": 21.1490, "lon": 79.0820, "capacity": 50, "road_width": 3.5},
    3: {"name": "Sadar Junction", "lat": 21.1550, "lon": 79.0900, "capacity": 45, "road_width": 3},
    4: {"name": "Seminary Hills", "lat": 21.1400, "lon": 79.0750, "capacity": 60, "road_width": 4},
    5: {"name": "Ramdaspeth", "lat": 21.1520, "lon": 79.0950, "capacity": 40, "road_width": 2},
}

ROAD_EDGES = [
    (1, 2, 0.8, 3), (2, 1, 0.8, 3),
    (1, 4, 1.2, 5), (4, 1, 1.2, 5),
    (2, 3, 0.9, 4), (3, 2, 0.9, 4),
    (2, 5, 1.1, 4), (5, 2, 1.1, 4),
    (3, 5, 0.7, 3), (5, 3, 0.7, 3),
    (1, 3, 1.5, 6), (3, 1, 1.5, 6),
    (4, 5, 1.3, 5), (5, 4, 1.3, 5),
]

ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8000", "http://127.0.0.1:8000"]

print(f"✓ Configuration loaded from: {BASE_DIR}")
'''
        
        try:
            config_path.write_text(config_content)
            print(f"✓ Created: {config_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to create config.py: {e}")
            return False
    
    def display_next_steps(self):
        """Display next steps for user"""
        self.print_header("✓ SETUP COMPLETE!")
        
        print("""
Next Steps:

1. COPY YOUR PYTHON FILES:
   Copy these files to the specified folders:
   
   To: C:\\traffic-project\\backend\\
   - config.py (or use the auto-generated one)
   - database.py
   - video_processor.py
   - pathfinding.py
   - app.py
   - requirements.txt
   
   To: C:\\traffic-project\\
   - environment.yml
   
   To: C:\\traffic-project\\frontend\\
   - index.html
   - style.css
   - script.js
   
   To: C:\\traffic-project\\data\\
   - nagpur_roads.json

2. PLACE YOUR VIDEOS:
   Place 5 MP4 videos (30sec, 720p+) in:
   C:\\traffic-project\\backend\\videos\\
   
   Files should be named:
   - intersection_1.mp4
   - intersection_2.mp4
   - intersection_3.mp4
   - intersection_4.mp4
   - intersection_5.mp4
   
   (Or run: python -m make_dummy_videos.py)

3. INSTALL ANACONDA ENVIRONMENT:
   Open Anaconda Prompt and run:
   
   cd C:\\traffic-project
   conda env create -f environment.yml
   
   (Wait 10-15 minutes for installation)

4. START THE SERVER:
   In Anaconda Prompt:
   
   conda activate rtina-env
   python -m uvicorn backend.app:app --reload
   
   Or with full options:
   
   python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

5. ACCESS DASHBOARD:
   Open your browser:
   
   http://localhost:8000

Current Project Location:
""")
        print(f"  {self.project_path}\n")
        
        print("Folder Structure Created:")
        self.print_tree(self.project_path, "", 0)
    
    def print_tree(self, path, prefix, depth, max_depth=3):
        """Print directory tree"""
        if depth > max_depth:
            return
        
        try:
            items = sorted(os.listdir(path))
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            
            for i, dir_name in enumerate(dirs):
                is_last = i == len(dirs) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{dir_name}/")
                
                next_prefix = prefix + ("    " if is_last else "│   ")
                self.print_tree(os.path.join(path, dir_name), next_prefix, depth + 1, max_depth)
        except PermissionError:
            pass
    
    def run(self):
        """Run complete setup"""
        self.print_header("RTINA TRAFFIC SYSTEM - AUTOMATED SETUP")
        
        print(f"Project Location: {self.project_path}\n")
        
        # Step 1: Create folders
        if not self.create_folders():
            print("\n✗ Setup failed at folder creation")
            return False
        
        # Step 2: Create init files
        if not self.create_init_files():
            print("\n✗ Setup failed at __init__.py creation")
            return False
        
        # Step 3: Create config file
        if not self.create_config_file():
            print("\n✗ Setup failed at config.py creation")
            return False
        
        # Display next steps
        self.display_next_steps()
        
        print("\n" + "="*60)
        print("  Setup completed successfully!")
        print("="*60 + "\n")
        
        return True

if __name__ == "__main__":
    # You can customize the project path here
    project_path = "C:\\traffic-project"
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    
    setup = RTINASetup(project_path)
    success = setup.run()
    
    if not success:
        sys.exit(1)
    
    input("Press Enter to close this window...")