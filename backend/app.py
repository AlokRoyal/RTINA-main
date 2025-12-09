# RTINA Traffic System - FastAPI Main Server
# backend/app.py


import sqlite3
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import json
from typing import Dict, List
from datetime import datetime
import asyncio
import logging
from pathlib import Path


from .config import ALLOWED_ORIGINS, API_HOST, API_PORT, FRONTEND_DIR, INTERSECTIONS
from .database import db
from .video_processor import video_processor
from .pathfinding import pathfinder


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="RTINA - Traffic Navigation System",
    description="Real-Time IoT-based Traffic Navigation and Route Suggestion",
    version="1.0.0"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global variables for WebSocket management
connected_clients: List[WebSocket] = []
active_routes: Dict[int, Dict] = {}  # Journey ID -> Route info
pending_route_changes: Dict[int, Dict] = {}  # Journey ID -> Pending change request


# ======================== UTILITY FUNCTIONS ========================


async def broadcast_traffic_update():
    """Broadcast traffic updates to all connected clients"""
    traffic_data = db.get_latest_traffic_all_intersections()
    
    message = {
        'type': 'traffic_update',
        'timestamp': datetime.now().isoformat(),
        'data': traffic_data
    }
    
    # Remove disconnected clients
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    
    for client in disconnected:
        connected_clients.remove(client)


async def check_route_congestion(route_path: List[int]):
    """Check if any intersection in route has high congestion"""
    traffic_data = db.get_latest_traffic_all_intersections()
    
    for intersection_id in route_path:
        if intersection_id in traffic_data:
            if traffic_data[intersection_id]['congestion_percentage'] >= 80:
                return True
    return False


# ======================== API ENDPOINTS ========================


@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve frontend dashboard"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>RTINA - Traffic Navigation System</h1><p>Frontend not found</p>")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }


@app.get("/api/intersections")
async def get_all_intersections():
    """Get all intersections with current traffic data"""
    intersections = pathfinder.get_all_intersections_info()
    return {
        'success': True,
        'count': len(intersections),
        'data': intersections
    }


@app.get("/api/intersections/{intersection_id}")
async def get_intersection(intersection_id: int):
    """Get specific intersection details"""
    intersection = db.get_intersection_by_id(intersection_id)
    if not intersection:
        raise HTTPException(status_code=404, detail="Intersection not found")
    
    traffic_data = db.get_latest_traffic_all_intersections()
    if intersection_id in traffic_data:
        intersection.update(traffic_data[intersection_id])
    
    return {'success': True, 'data': intersection}


@app.get("/api/traffic/all")
async def get_all_traffic():
    """Get current traffic for all intersections"""
    traffic_data = db.get_latest_traffic_all_intersections()
    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'data': traffic_data
    }


@app.get("/api/traffic/history/{intersection_id}")
async def get_traffic_history(intersection_id: int, hours: int = 1):
    """Get traffic history for intersection"""
    history = db.get_traffic_history(intersection_id, hours)
    return {
        'success': True,
        'intersection_id': intersection_id,
        'hours': hours,
        'data': history
    }


@app.post("/api/routes/shortest")
async def calculate_shortest_route(source: int, destination: int):
    """Calculate shortest distance route"""
    result = pathfinder.find_shortest_route(source, destination)
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Save route to database
    route_id = db.save_route(
        source, destination, 'shortest',
        result['path'],
        result['distance_km'],
        result['estimated_time_minutes']
    )
    
    result['route_id'] = route_id
    return {'success': True, 'data': result}


@app.post("/api/routes/fastest")
async def calculate_fastest_route(source: int, destination: int, avoid_congestion: bool = True):
    """Calculate fastest route (with option to avoid congestion)"""
    result = pathfinder.find_fastest_route(source, destination, avoid_congestion)
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Save route to database
    route_id = db.save_route(
        source, destination,
        'fastest_congestion_aware' if avoid_congestion else 'fastest',
        result['path'],
        result['distance_km'],
        result['estimated_time_minutes']
    )
    
    result['route_id'] = route_id
    return {'success': True, 'data': result}


@app.get("/api/roads")
async def get_road_network():
    """Get all road connections"""
    roads = pathfinder.get_road_connections()
    return {
        'success': True,
        'count': len(roads),
        'data': roads
    }


@app.post("/api/traffic/update")
async def update_traffic(data: dict):
    """
    Update traffic congestion for an intersection
    
    Expected JSON:
    {
        "intersection_name": "High Court Square",
        "congestion": 75,
        "vehicle_count": 45
    }
    """
    try:
        intersection_name = data.get("intersection_name")
        new_congestion = data.get("congestion", 0)
        new_vehicle_count = data.get("vehicle_count", 0)
        
        if not intersection_name:
            return {
                "status": "error",
                "message": "intersection_name is required"
            }
        
        # Get intersection by name
        intersections = pathfinder.get_all_intersections_info()
        intersection_id = None
        
        for intersection in intersections:
            if intersection.get('name') == intersection_name:
                intersection_id = intersection.get('id')
                break
        
        if not intersection_id:
            return {
                "status": "error",
                "message": f"Intersection '{intersection_name}' not found"
            }
        
        # Update traffic data in database
        db.update_traffic_data(
            intersection_id,
            new_congestion,
            new_vehicle_count
        )
        
        # Broadcast update to all connected WebSocket clients
        await broadcast_traffic_update()
        
        return {
            "status": "success",
            "message": f"Updated {intersection_name}",
            "intersection_name": intersection_name,
            "intersection_id": intersection_id,
            "congestion": new_congestion,
            "vehicles": new_vehicle_count,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error updating traffic: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/journey/start")
async def start_journey(route_id: int, route_path: List[int]):
    """Start a journey on a route"""
    journey_id = route_id  # Simplified for prototype
    
    active_routes[journey_id] = {
        'route_id': route_id,
        'path': route_path,
        'start_time': datetime.now().isoformat(),
        'status': 'in_progress'
    }
    
    return {
        'success': True,
        'journey_id': journey_id,
        'data': active_routes[journey_id]
    }


@app.post("/api/journey/{journey_id}/respond-route-change")
async def respond_to_route_change(journey_id: int, accept: bool):
    """User response to route change suggestion"""
    if journey_id not in pending_route_changes:
        raise HTTPException(status_code=404, detail="No pending route change")
    
    change_request = pending_route_changes.pop(journey_id)
    
    return {
        'success': True,
        'response': 'accepted' if accept else 'rejected',
        'data': change_request
    }


# ======================== WEBSOCKET ENDPOINTS ========================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time traffic updates"""
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"✓ WebSocket client connected. Total: {len(connected_clients)}")
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
            
            # Wait before next update
            await asyncio.sleep(15)  # 15-second update interval
            
            # Send traffic update
            await broadcast_traffic_update()
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info(f"✓ WebSocket client disconnected. Total: {len(connected_clients)}")


# ======================== VIDEO PROCESSING STARTUP ========================


@app.on_event("startup")
async def startup_event():
    """Initialize video processing on startup"""
    logger.info("Starting RTINA Traffic System...")
    
    # Configure videos to process (these should exist in backend/videos/)
    videos_config = {
        'intersection_1.mp4': 1,
        'intersection_2.mp4': 2,
        'intersection_3.mp4': 3,
        'intersection_4.mp4': 4,
        'intersection_5.mp4': 5,
    }
    
    # Check if videos exist
    available_videos = {}
    from pathlib import Path
    videos_dir = Path(__file__).parent / "videos"
    
    for video_name, intersection_id in videos_config.items():
        video_path = videos_dir / video_name
        if video_path.exists():
            available_videos[video_name] = intersection_id
            logger.info(f"✓ Found video: {video_name}")
        else:
            logger.warning(f"✗ Video not found: {video_path}")
    
    # Start video processing if videos are available
    if available_videos:
        logger.info(f"Starting processing for {len(available_videos)} videos...")
        video_processor.start_video_processing(available_videos)
    else:
        logger.warning("No videos found in backend/videos/ directory")
        logger.info("Please place your intersection videos there:")
        logger.info("  - intersection_1.mp4")
        logger.info("  - intersection_2.mp4")
        logger.info("  - intersection_3.mp4")
        logger.info("  - intersection_4.mp4")
        logger.info("  - intersection_5.mp4")
    
    logger.info(f"✓ RTINA running on http://{API_HOST}:{API_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RTINA Traffic System...")
    video_processor.stop_video_processing()
    db.close()
    logger.info("✓ System shutdown complete")


# ======================== ERROR HANDLERS ========================


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Error: {exc}")
    return {
        'success': False,
        'error': str(exc),
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )