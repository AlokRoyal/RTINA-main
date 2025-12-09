# RTINA Traffic System - Database (FIXED - Relative Imports)
# backend/database.py


import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from .config import (
    BACKEND_DIR, INTERSECTIONS, ROAD_EDGES, DATABASE_URL
)


DATABASE_PATH = BACKEND_DIR / "data" / "traffic.db"


class TrafficDatabase:
    """SQLite database for traffic management"""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intersections (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    capacity INTEGER NOT NULL,
                    road_width REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roads (
                    id INTEGER PRIMARY KEY,
                    from_intersection INTEGER NOT NULL,
                    to_intersection INTEGER NOT NULL,
                    distance_km REAL NOT NULL,
                    avg_time_minutes INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(from_intersection) REFERENCES intersections(id),
                    FOREIGN KEY(to_intersection) REFERENCES intersections(id),
                    UNIQUE(from_intersection, to_intersection)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_data (
                    id INTEGER PRIMARY KEY,
                    intersection_id INTEGER NOT NULL,
                    vehicle_count INTEGER NOT NULL,
                    congestion_percentage REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(intersection_id) REFERENCES intersections(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY,
                    source_intersection INTEGER NOT NULL,
                    destination_intersection INTEGER NOT NULL,
                    route_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    total_distance_km REAL NOT NULL,
                    estimated_time_minutes INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_intersection) REFERENCES intersections(id),
                    FOREIGN KEY(destination_intersection) REFERENCES intersections(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS journeys (
                    id INTEGER PRIMARY KEY,
                    route_id INTEGER NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'in_progress',
                    route_changes INTEGER DEFAULT 0,
                    FOREIGN KEY(route_id) REFERENCES routes(id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_intersection ON traffic_data(intersection_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_journeys_status ON journeys(status)')
            
            conn.commit()
            self.populate_initial_data()
            print("✓ Database initialized successfully")
            
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            conn.rollback()
    
    def populate_initial_data(self):
        """Populate initial intersection and road data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM intersections")
            if cursor.fetchone()[0] > 0:
                return
            
            for int_id, int_data in INTERSECTIONS.items():
                cursor.execute('''
                    INSERT INTO intersections 
                    (id, name, latitude, longitude, capacity, road_width, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int_id,
                    int_data["name"],
                    int_data["lat"],
                    int_data["lon"],
                    int_data["capacity"],
                    int_data["road_width"],
                    int_data["description"]
                ))
            
            for from_int, to_int, dist, time in ROAD_EDGES:
                cursor.execute('''
                    INSERT INTO roads 
                    (from_intersection, to_intersection, distance_km, avg_time_minutes)
                    VALUES (?, ?, ?, ?)
                ''', (from_int, to_int, dist, time))
            
            conn.commit()
            print("✓ Initial data populated")
            
        except sqlite3.IntegrityError:
            print("✓ Data already exists")
            conn.rollback()
        except Exception as e:
            print(f"✗ Error populating data: {e}")
            conn.rollback()
    
    def add_traffic_data(self, intersection_id: int, vehicle_count: int, congestion_percentage: float):
        """Add traffic data point"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO traffic_data 
                (intersection_id, vehicle_count, congestion_percentage)
                VALUES (?, ?, ?)
            ''', (intersection_id, vehicle_count, congestion_percentage))
            conn.commit()
            return True
        except Exception as e:
            print(f"✗ Error adding traffic data: {e}")
            conn.rollback()
            return False
    
    def update_traffic_data(self, intersection_id: int, congestion: float, vehicle_count: int):
        """Update traffic data for an intersection"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO traffic_data 
                (intersection_id, vehicle_count, congestion_percentage, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (intersection_id, vehicle_count, congestion, datetime.now()))
            
            conn.commit()
            print(f"✓ Traffic updated for intersection {intersection_id}: {congestion}% congestion, {vehicle_count} vehicles")
            return True
        except Exception as e:
            print(f"✗ Error updating traffic: {e}")
            conn.rollback()
            return False
    
    def get_latest_traffic_all_intersections(self) -> Dict[int, Dict]:
        """Get latest traffic data for all intersections"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT i.id, i.name, i.latitude, i.longitude, i.capacity,
                       t.vehicle_count, t.congestion_percentage, t.timestamp
                FROM intersections i
                LEFT JOIN (
                    SELECT * FROM traffic_data 
                    WHERE id IN (
                        SELECT MAX(id) FROM traffic_data GROUP BY intersection_id
                    )
                ) t ON i.id = t.intersection_id
                ORDER BY i.id
            ''')
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    "id": row[0],
                    "name": row[1],
                    "lat": row[2],
                    "lon": row[3],
                    "capacity": row[4],
                    "vehicle_count": row[5] if row[5] is not None else 0,
                    "congestion_percentage": row[6] if row[6] is not None else 0.0,
                    "congestion": row[6] if row[6] is not None else 0.0,
                    "timestamp": row[7],
                    "status": "high" if (row[6] and row[6] >= 80) else "medium" if (row[6] and row[6] >= 50) else "low"
                }
            return result
            
        except Exception as e:
            print(f"✗ Error fetching traffic data: {e}")
            return {}
    
    def get_traffic_history(self, intersection_id: int, hours: int = 1) -> List[Dict]:
        """Get traffic history for specific intersection"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            since = datetime.now() - timedelta(hours=hours)
            cursor.execute('''
                SELECT timestamp, vehicle_count, congestion_percentage
                FROM traffic_data
                WHERE intersection_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (intersection_id, since.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"✗ Error fetching history: {e}")
            return []
    
    def save_route(self, source_id: int, dest_id: int, route_type: str, 
                   path: List[int], distance: float, time: int) -> int:
        """Save calculated route"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO routes 
                (source_intersection, destination_intersection, route_type, path, 
                 total_distance_km, estimated_time_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (source_id, dest_id, route_type, json.dumps(path), distance, time))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"✗ Error saving route: {e}")
            conn.rollback()
            return -1
    
    def get_intersection_by_id(self, intersection_id: int) -> Optional[Dict]:
        """Get intersection details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, name, latitude, longitude, capacity, road_width, description
                FROM intersections
                WHERE id = ?
            ''', (intersection_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"✗ Error fetching intersection: {e}")
            return None
    
    def get_all_intersections(self) -> List[Dict]:
        """Get all intersections"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, name, latitude, longitude, capacity, road_width, description
                FROM intersections
                ORDER BY id
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"✗ Error fetching intersections: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None



# Initialize global database instance
db = TrafficDatabase()