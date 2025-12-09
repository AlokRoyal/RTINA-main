# RTINA Traffic System - Pathfinding (FIXED - Relative Imports)
# backend/pathfinding.py

import networkx as nx
from typing import List, Dict, Tuple, Optional
from math import radians, cos, sin, asin, sqrt
from .config import INTERSECTIONS, ROAD_EDGES, CONGESTION_WEIGHT
from .database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficPathfinder:
    """A* pathfinding for traffic navigation with congestion awareness"""
    
    def __init__(self):
        """Initialize the road network graph"""
        self.graph = nx.DiGraph()
        self.build_graph()
        logger.info("✓ Pathfinder initialized with Nagpur road network")
    
    def build_graph(self):
        """Build directed graph from intersections and roads"""
        for int_id, int_data in INTERSECTIONS.items():
            self.graph.add_node(
                int_id,
                name=int_data['name'],
                lat=int_data['lat'],
                lon=int_data['lon'],
                capacity=int_data['capacity']
            )
        
        for from_int, to_int, distance, time in ROAD_EDGES:
            self.graph.add_edge(
                from_int,
                to_int,
                distance=distance,
                time=time,
                congestion=0
            )
    
    def get_node_coordinates(self, node: int) -> Tuple[float, float]:
        """Get latitude and longitude of a node"""
        data = self.graph.nodes[node]
        return data['lat'], data['lon']
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance between two points on earth (in km)"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371
        return c * r
    
    def update_congestion_levels(self):
        """Update congestion levels for all edges from current traffic data"""
        traffic_data = db.get_latest_traffic_all_intersections()
        
        for edge in self.graph.edges(data=True):
            from_node, to_node = edge[0], edge[1]
            
            if to_node in traffic_data:
                congestion = traffic_data[to_node]['congestion_percentage']
                self.graph[from_node][to_node]['congestion'] = congestion
    
    def get_edge_weight_distance(self, u: int, v: int, d: Dict) -> float:
        """Weight function for shortest distance route"""
        return d['distance']
    
    def get_edge_weight_fastest(self, u: int, v: int, d: Dict) -> float:
        """Weight function for fastest route"""
        base_weight = d['distance']
        congestion = d.get('congestion', 0)
        congestion_penalty = (congestion / 100) * 0.1 * base_weight
        return base_weight + congestion_penalty
    
    def get_edge_weight_congestion_aware(self, u: int, v: int, d: Dict) -> float:
        """Weight function for congestion-aware fastest route"""
        base_weight = d['distance']
        congestion = d.get('congestion', 0)
        
        if congestion >= 80:
            congestion_penalty = base_weight * 2
        elif congestion >= 50:
            congestion_penalty = base_weight * 1.5
        else:
            congestion_penalty = base_weight * (congestion / 100)
        
        return base_weight + congestion_penalty
    
    def find_shortest_route(self, start: int, end: int) -> Dict:
        """Find shortest distance route"""
        try:
            if start not in self.graph or end not in self.graph:
                return {'error': 'Invalid intersection IDs'}
            
            if start == end:
                return {'error': 'Start and end are the same'}
            
            path = nx.shortest_path(
                self.graph,
                start,
                end,
                weight=self.get_edge_weight_distance
            )
            
            distance = sum(
                self.graph[path[i]][path[i+1]]['distance']
                for i in range(len(path)-1)
            )
            
            time = sum(
                self.graph[path[i]][path[i+1]]['time']
                for i in range(len(path)-1)
            )
            
            return {
                'success': True,
                'route_type': 'shortest',
                'path': path,
                'distance_km': round(distance, 2),
                'estimated_time_minutes': int(time),
                'intersections': [INTERSECTIONS[node]['name'] for node in path]
            }
            
        except nx.NetworkXNoPath:
            return {'error': 'No path found between intersections'}
        except Exception as e:
            logger.error(f"Error in shortest route: {e}")
            return {'error': str(e)}
    
    def find_fastest_route(self, start: int, end: int, avoid_congestion: bool = True) -> Dict:
        """Find fastest route"""
        try:
            if start not in self.graph or end not in self.graph:
                return {'error': 'Invalid intersection IDs'}
            
            if start == end:
                return {'error': 'Start and end are the same'}
            
            self.update_congestion_levels()
            
            if avoid_congestion:
                weight_func = self.get_edge_weight_congestion_aware
                route_type = 'fastest_congestion_aware'
            else:
                weight_func = self.get_edge_weight_fastest
                route_type = 'fastest'
            
            path = nx.shortest_path(
                self.graph,
                start,
                end,
                weight=weight_func
            )
            
            distance = sum(
                self.graph[path[i]][path[i+1]]['distance']
                for i in range(len(path)-1)
            )
            
            time = sum(
                self.graph[path[i]][path[i+1]]['time']
                for i in range(len(path)-1)
            )
            
            congestion_levels = []
            for node in path:
                traffic_data = db.get_latest_traffic_all_intersections()
                if node in traffic_data:
                    congestion_levels.append({
                        'intersection': INTERSECTIONS[node]['name'],
                        'congestion': traffic_data[node]['congestion_percentage']
                    })
            
            return {
                'success': True,
                'route_type': route_type,
                'path': path,
                'distance_km': round(distance, 2),
                'estimated_time_minutes': int(time),
                'intersections': [INTERSECTIONS[node]['name'] for node in path],
                'congestion_levels': congestion_levels
            }
            
        except nx.NetworkXNoPath:
            return {'error': 'No path found between intersections'}
        except Exception as e:
            logger.error(f"Error in fastest route: {e}")
            return {'error': str(e)}
    
    def get_all_intersections_info(self) -> List[Dict]:
        """Get info about all intersections"""
        intersections = []
        traffic_data = db.get_latest_traffic_all_intersections()
        
        for int_id, int_data in INTERSECTIONS.items():
            info = {
                'id': int_id,
                'name': int_data['name'],
                'lat': int_data['lat'],
                'lon': int_data['lon'],
                'capacity': int_data['capacity'],
                'road_width': int_data['road_width']
            }
            
            if int_id in traffic_data:
                info['vehicle_count'] = traffic_data[int_id]['vehicle_count']
                info['congestion'] = traffic_data[int_id]['congestion_percentage']
                info['status'] = traffic_data[int_id]['status']
            else:
                info['vehicle_count'] = 0
                info['congestion'] = 0
                info['status'] = 'unknown'
            
            intersections.append(info)
        
        return intersections
    
    def get_road_connections(self) -> List[Dict]:
        """Get all road connections"""
        connections = []
        for from_int, to_int, distance, time in ROAD_EDGES:
            connections.append({
                'from_intersection': from_int,
                'to_intersection': to_int,
                'distance_km': distance,
                'estimated_time_minutes': time,
                'from_name': INTERSECTIONS[from_int]['name'],
                'to_name': INTERSECTIONS[to_int]['name']
            })
        return connections


# Initialize global pathfinder
pathfinder = TrafficPathfinder()
