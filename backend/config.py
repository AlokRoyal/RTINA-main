# RTINA Traffic System - Configuration File
# backend/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ==================== PROJECT PATHS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
VIDEOS_DIR = BACKEND_DIR / "videos"

# Create directories if they don't exist
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ==================== DATABASE CONFIGURATION ====================
DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'data' / 'traffic.db'}"
SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite:///") if "sqlite" in DATABASE_URL else DATABASE_URL

# ==================== API CONFIGURATION ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
RELOAD = os.getenv("RELOAD", "True").lower() == "true"

# ==================== YOLOV8 CONFIGURATION ====================
YOLO_MODEL = "yolov8n.pt"  # Nano model - fastest
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_IOU_THRESHOLD = 0.4
YOLO_DEVICE = "cpu"  # Use "cuda" if GPU available
VEHICLE_CLASSES = [2, 3, 5, 7]  # COCO classes: car, motorcycle, bus, truck

# ==================== VIDEO PROCESSING CONFIGURATION ====================
VIDEO_SNAPSHOT_INTERVAL = 15  # Extract frame every 15 seconds
VIDEO_FRAME_SKIP = 10  # Process every 10th frame for speed
VIDEO_RESIZE_WIDTH = 640
VIDEO_RESIZE_HEIGHT = 480
MAX_CONCURRENT_VIDEOS = 5  # Process max 5 videos in parallel

# ==================== TRAFFIC CONFIGURATION ====================
CONGESTION_THRESHOLD = 80  # Percentage - Alert user if >= 80%
ROUTE_UPDATE_TIMEOUT = 3  # Seconds - Wait 3s for user response
MIN_VEHICLE_DISTANCE = 30  # Pixels - Minimum distance between detected vehicles

# ==================== INTERSECTION CONFIGURATION ====================
# Each intersection has name, lat, lon, max_capacity (based on road width)
INTERSECTIONS = {
    1: {
        "name": "High Court Square",
        "lat": 21.1458,
        "lon": 79.0882,
        "capacity": 70,  # 4-lane highway
        "road_width": 4,
        "description": "Main 4-lane intersection"
    },
    2: {
        "name": "Sitabuldi Junction",
        "lat": 21.1490,
        "lon": 79.0820,
        "capacity": 50,  # 3.5-lane road
        "road_width": 3.5,
        "description": "3.5-lane road segment"
    },
    3: {
        "name": "Sadar Junction",
        "lat": 21.1550,
        "lon": 79.0900,
        "capacity": 45,  # 3-lane road
        "road_width": 3,
        "description": "3-lane residential area"
    },
    4: {
        "name": "Seminary Hills",
        "lat": 21.1400,
        "lon": 79.0750,
        "capacity": 60,  # 4-lane road
        "road_width": 4,
        "description": "4-lane suburban road"
    },
    5: {
        "name": "Ramdaspeth",
        "lat": 21.1520,
        "lon": 79.0950,
        "capacity": 40,  # 2-lane road
        "road_width": 2,
        "description": "2-lane local road"
    }
}

# ==================== ROAD NETWORK EDGES ====================
# Connects intersections with distances (km) and typical travel times (minutes)
ROAD_EDGES = [
    # (from_intersection, to_intersection, distance_km, avg_time_minutes)
    (1, 2, 0.8, 3),
    (2, 1, 0.8, 3),
    (1, 4, 1.2, 5),
    (4, 1, 1.2, 5),
    (2, 3, 0.9, 4),
    (3, 2, 0.9, 4),
    (2, 5, 1.1, 4),
    (5, 2, 1.1, 4),
    (3, 5, 0.7, 3),
    (5, 3, 0.7, 3),
    (1, 3, 1.5, 6),
    (3, 1, 1.5, 6),
    (4, 5, 1.3, 5),
    (5, 4, 1.3, 5),
]

# ==================== WEBSOCKET CONFIGURATION ====================
WEBSOCKET_UPDATE_INTERVAL = 15  # Send updates every 15 seconds
WEBSOCKET_BROADCAST_ALL = True  # Broadcast to all connected clients

# ==================== LOGGING CONFIGURATION ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "traffic.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ==================== CORS CONFIGURATION ====================
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
]

# ==================== A* PATHFINDING CONFIGURATION ====================
HEURISTIC_WEIGHT = 1.0  # Weight for heuristic (1.0 = A*, > 1.0 = weighted A*)
CONGESTION_WEIGHT = 0.3  # Weight for congestion in fastest route calculation

# ==================== ENVIRONMENT SPECIFICS ====================
print(f"✓ Project initialized from: {BASE_DIR}")
print(f"✓ Database: {DATABASE_URL}")
print(f"✓ Videos folder: {VIDEOS_DIR}")
print(f"✓ API running on: {API_HOST}:{API_PORT}")
