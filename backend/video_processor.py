# RTINA Traffic System - Video Processor (FIXED - Relative Imports)
# backend/video_processor.py

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from ultralytics import YOLO
from .config import (
    VIDEOS_DIR, YOLO_MODEL, YOLO_CONFIDENCE_THRESHOLD, VEHICLE_CLASSES,
    VIDEO_SNAPSHOT_INTERVAL, VIDEO_RESIZE_WIDTH, VIDEO_RESIZE_HEIGHT,
    MAX_CONCURRENT_VIDEOS, MIN_VEHICLE_DISTANCE, INTERSECTIONS
)
from .database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Process videos with YOLOv8 for vehicle detection"""
    
    def __init__(self):
        """Initialize YOLO model"""
        logger.info("Loading YOLOv8 model...")
        self.model = YOLO(YOLO_MODEL)
        self.model.overrides.update({
            'conf': YOLO_CONFIDENCE_THRESHOLD,
            'iou': 0.4,
            'device': 'cpu'
        })
        logger.info("✓ YOLOv8 model loaded successfully")
        
        self.active_videos = {}
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_VIDEOS)
        self.video_threads = {}
        self.stop_flags = {}
    
    def extract_frame_at_timestamp(self, video_path: Path, timestamp_seconds: int) -> Optional[np.ndarray]:
        """Extract single frame from video at specific timestamp"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Cannot open video: {video_path}")
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp_seconds * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame = cv2.resize(frame, (VIDEO_RESIZE_WIDTH, VIDEO_RESIZE_HEIGHT))
                return frame
            return None
            
        except Exception as e:
            logger.error(f"Error extracting frame: {e}")
            return None
    
    def detect_vehicles_in_frame(self, frame: np.ndarray) -> Tuple[int, List[Dict]]:
        """Detect vehicles in frame using YOLOv8"""
        try:
            results = self.model(frame, verbose=False)
            
            detections = []
            vehicle_count = 0
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    if class_id in VEHICLE_CLASSES:
                        confidence = float(box.conf[0])
                        
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        detection = {
                            'bbox': (x1, y1, x2, y2),
                            'confidence': confidence,
                            'class': class_id,
                            'class_name': self.get_class_name(class_id)
                        }
                        detections.append(detection)
                        vehicle_count += 1
            
            return vehicle_count, detections
            
        except Exception as e:
            logger.error(f"Error in vehicle detection: {e}")
            return 0, []
    
    def filter_incoming_vehicles(self, detections: List[Dict], frame_height: int) -> List[Dict]:
        """Filter to keep only incoming vehicles (bottom half of frame)"""
        incoming = []
        threshold = frame_height * 0.6
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            vehicle_center_y = (y1 + y2) / 2
            
            if vehicle_center_y > threshold:
                incoming.append(det)
        
        return incoming
    
    def remove_duplicate_detections(self, detections: List[Dict]) -> List[Dict]:
        """Remove duplicate detections"""
        filtered = []
        
        for det in detections:
            is_duplicate = False
            x1, y1, x2, y2 = det['bbox']
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            for existing in filtered:
                ex1, ey1, ex2, ey2 = existing['bbox']
                ex_center_x = (ex1 + ex2) / 2
                ex_center_y = (ey1 + ey2) / 2
                
                distance = np.sqrt((center_x - ex_center_x)**2 + (center_y - ex_center_y)**2)
                
                if distance < MIN_VEHICLE_DISTANCE:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(det)
        
        return filtered
    
    def process_video_frame(self, video_path: Path, timestamp: int, intersection_id: int) -> Dict:
        """Process single frame from video and return traffic metrics"""
        try:
            frame = self.extract_frame_at_timestamp(video_path, timestamp)
            if frame is None:
                return {'error': 'Failed to extract frame'}
            
            total_vehicles, detections = self.detect_vehicles_in_frame(frame)
            incoming_vehicles = self.filter_incoming_vehicles(detections, frame.shape[0])
            incoming_vehicles = self.remove_duplicate_detections(incoming_vehicles)
            incoming_count = len(incoming_vehicles)
            
            intersection_capacity = INTERSECTIONS[intersection_id]['capacity']
            congestion_percentage = (incoming_count / intersection_capacity) * 100
            congestion_percentage = min(100, congestion_percentage)
            
            db.add_traffic_data(intersection_id, incoming_count, congestion_percentage)
            
            result = {
                'intersection_id': intersection_id,
                'timestamp': datetime.now().isoformat(),
                'incoming_vehicles': incoming_count,
                'total_detections': total_vehicles,
                'congestion_percentage': round(congestion_percentage, 2),
                'capacity': intersection_capacity,
                'status': 'high' if congestion_percentage >= 80 else 'medium' if congestion_percentage >= 50 else 'low'
            }
            
            logger.info(f"Intersection {intersection_id}: {incoming_count} vehicles, {result['congestion_percentage']}% congestion")
            return result
            
        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            return {'error': str(e)}
    
    def process_video_loop(self, video_name: str, intersection_id: int, 
                          process_callback=None, interval: int = VIDEO_SNAPSHOT_INTERVAL):
        """Continuously process video frames at regular intervals"""
        video_path = VIDEOS_DIR / video_name
        
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return
        
        logger.info(f"Starting continuous processing of {video_name} (Intersection {intersection_id})")
        
        timestamp = 0
        max_duration = 30
        self.stop_flags[video_name] = False
        
        try:
            while not self.stop_flags.get(video_name, False):
                result = self.process_video_frame(video_path, timestamp, intersection_id)
                
                if process_callback:
                    process_callback(result)
                
                timestamp += interval
                
                if timestamp >= max_duration:
                    timestamp = 0
                    logger.info(f"Video {video_name} looping...")
                
                import time
                time.sleep(interval - 1)
                
        except Exception as e:
            logger.error(f"Error in video loop: {e}")
    
    def start_video_processing(self, videos_config: Dict[str, int], 
                              process_callback=None):
        """Start processing multiple videos"""
        logger.info(f"Starting video processing for {len(videos_config)} videos")
        
        for video_name, intersection_id in videos_config.items():
            thread = threading.Thread(
                target=self.process_video_loop,
                args=(video_name, intersection_id, process_callback),
                daemon=True
            )
            thread.start()
            self.video_threads[video_name] = thread
            logger.info(f"✓ Started processing {video_name}")
    
    def stop_video_processing(self, video_name: str = None):
        """Stop processing video(s)"""
        if video_name:
            self.stop_flags[video_name] = True
            logger.info(f"Stopped processing {video_name}")
        else:
            for name in self.stop_flags:
                self.stop_flags[name] = True
            logger.info("Stopped all video processing")
    
    def get_class_name(self, class_id: int) -> str:
        """Get COCO class name from ID"""
        classes = {
            2: 'Car',
            3: 'Motorcycle',
            5: 'Bus',
            7: 'Truck'
        }
        return classes.get(class_id, 'Unknown')
    
    def __del__(self):
        """Cleanup"""
        self.executor.shutdown(wait=False)


# Initialize global processor
video_processor = VideoProcessor()
