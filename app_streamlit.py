# RTINA Traffic System - Streamlit Interface with Real Google Maps
# Save as: app_streamlit_google_maps.py
# Run: streamlit run app_streamlit_google_maps.py

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import json
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="RTINA - Traffic Navigation",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .traffic-high {
        background: #ffebee;
        border-left: 4px solid #e74c3c;
        padding: 10px;
        border-radius: 5px;
    }
    .traffic-medium {
        background: #fff3e0;
        border-left: 4px solid #f39c12;
        padding: 10px;
        border-radius: 5px;
    }
    .traffic-low {
        background: #e8f5e9;
        border-left: 4px solid #34a853;
        padding: 10px;
        border-radius: 5px;
    }
    .instruction-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .selected-route {
        background: #fff8e1;
        border-left: 4px solid #fbc02d;
        padding: 12px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE = "http://localhost:8001"
GOOGLE_API_KEY = "AIzaSyAzaEhtwxxycoUapr0uqY41j-RQj5o_gSo"

# Initialize session state
if 'source_point' not in st.session_state:
    st.session_state.source_point = None
if 'destination_point' not in st.session_state:
    st.session_state.destination_point = None
if 'calculate_route' not in st.session_state:
    st.session_state.calculate_route = False
if 'route_result' not in st.session_state:
    st.session_state.route_result = None

# Title
st.markdown("# 🚗 RTINA - Real-Time Traffic Navigation System")
st.markdown("Intelligent traffic management using AI-powered vehicle detection")

# Sidebar
with st.sidebar:
    st.header("🎮 Route Planner")
    
    # Get intersections
    try:
        response = requests.get(f"{API_BASE}/api/intersections")
        intersections_data = response.json()['data']
        intersections_dict = {i['name']: i['id'] for i in intersections_data}
        intersections_list = list(intersections_dict.keys())
    except:
        st.error("❌ Cannot connect to backend API")
        st.info("Make sure FastAPI is running on port 8001")
        st.stop()
    
    st.markdown("### 📍 Route Selection Method")
    selection_method = st.radio(
        "Choose how to select route:",
        ["📝 Dropdown Selection", "🗺️ Click on Map"],
        horizontal=False
    )
    
    st.markdown("---")
    
    if selection_method == "📝 Dropdown Selection":
        st.markdown("### Select Points Manually:")
        
        source_name = st.selectbox(
            "📍 Select Start Point",
            intersections_list,
            key="source_dropdown"
        )
        st.session_state.source_point = source_name
        
        destination_name = st.selectbox(
            "📍 Select Destination",
            [x for x in intersections_list if x != source_name],
            key="destination_dropdown"
        )
        st.session_state.destination_point = destination_name
    
    else:  # Click on map
        st.markdown("### Instructions:")
        st.markdown("""
        <div class="instruction-box">
        1. <b>Click on START location</b> on the map
        2. <b>Click on DESTINATION</b> on the map
        3. <b>Select Route Type</b> below
        4. <b>Click Calculate</b> to see route
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Selected Points:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.source_point:
                st.success(f"✅ Start: {st.session_state.source_point}")
            else:
                st.info("⏳ Start: Not selected")
        with col2:
            if st.session_state.destination_point:
                st.success(f"✅ Destination: {st.session_state.destination_point}")
            else:
                st.info("⏳ Destination: Not selected")
        
        if st.button("🔄 Clear Selection", use_container_width=True):
            st.session_state.source_point = None
            st.session_state.destination_point = None
            st.rerun()
    
    # Route type selection
    st.markdown("---")
    st.markdown("**Route Type:**")
    route_type = st.radio(
        "Choose route optimization",
        ["Shortest Distance", "Fastest (Avoid Traffic)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Calculate button
    if st.session_state.source_point and st.session_state.destination_point:
        if st.button("🗺️ Calculate Route", use_container_width=True, type="primary"):
            st.session_state.calculate_route = True
    else:
        st.button("🗺️ Calculate Route", use_container_width=True, disabled=True)
        st.warning("⚠️ Please select both start and destination points first")
    
    # Traffic Status Section
    st.markdown("---")
    st.header("🚦 Traffic Status")
    
    try:
        response = requests.get(f"{API_BASE}/api/traffic/all")
        traffic_data = response.json()['data']
        
        for int_id, traffic in traffic_data.items():
            status = traffic['status'].upper()
            icon = "🟢" if status == "LOW" else "🟡" if status == "MEDIUM" else "🔴"
            
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{traffic['name']}**")
                with col2:
                    st.markdown(f"{traffic['vehicle_count']} vehicles")
                with col3:
                    st.markdown(f"{icon}")
                
                congestion = traffic['congestion_percentage']
                st.progress(congestion / 100, text=f"{congestion:.0f}%")
    except Exception as e:
        st.warning(f"⚠️ Unable to fetch traffic data: {str(e)}")

# Main content area
tab1, tab2, tab3 = st.tabs(["🗺️ Route Map", "📊 Traffic Analytics", "ℹ️ System Status"])

with tab1:
    st.subheader("🗺️ Interactive Traffic Map - Nagpur City")
    
    # Create Google Maps-style Folium map
    m = folium.Map(
        location=[21.145, 79.088],
        zoom_start=13,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google",
        prefer_canvas=True
    )
    
    # Add intersection markers
    try:
        response = requests.get(f"{API_BASE}/api/intersections")
        intersections = response.json()['data']
        
        for intersection in intersections:
            status = intersection.get('status', 'low')
            
            # Determine marker color based on selection
            if intersection['name'] == st.session_state.source_point:
                color = "blue"
                icon_symbol = "S"
                prefix = "📍 START"
            elif intersection['name'] == st.session_state.destination_point:
                color = "red"
                icon_symbol = "D"
                prefix = "🎯 DESTINATION"
            else:
                color = "green" if status == "low" else "orange" if status == "medium" else "red"
                icon_symbol = "info-sign"
                prefix = "📌"
            
            icon = folium.Icon(color=color, icon="info-sign", prefix="fa")
            
            popup_text = f"""
            <b>{prefix} {intersection['name']}</b><br>
            Vehicles: {intersection['vehicle_count']}<br>
            Congestion: {intersection['congestion']:.1f}%<br>
            Capacity: {intersection['capacity']}<br>
            Status: {status.upper()}
            """
            
            folium.Marker(
                location=[intersection['lat'], intersection['lon']],
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=f"{intersection['name']} - {intersection['vehicle_count']} vehicles",
                icon=icon
            ).add_to(m)
            
            # Add traffic density circles
            circle_color = "green" if status == "low" else "orange" if status == "medium" else "red"
            folium.Circle(
                location=[intersection['lat'], intersection['lon']],
                radius=intersection['congestion'] * 50,
                popup=f"{intersection['name']}: {intersection['congestion']:.0f}%",
                color=circle_color,
                fill=True,
                fillColor=circle_color,
                fillOpacity=0.3,
                weight=2
            ).add_to(m)
        
        # Display map
        map_data = st_folium(m, width=1400, height=600)
        
        # Handle map clicks for point selection
        if map_data and map_data.get('last_clicked'):
            clicked_lat = map_data['last_clicked']['lat']
            clicked_lon = map_data['last_clicked']['lng']
            
            # Find nearest intersection
            min_distance = float('inf')
            nearest_intersection = None
            
            for intersection in intersections:
                dist = ((intersection['lat'] - clicked_lat)**2 + 
                       (intersection['lon'] - clicked_lon)**2)**0.5
                if dist < min_distance:
                    min_distance = dist
                    nearest_intersection = intersection['name']
            
            if min_distance < 0.01:
                if not st.session_state.source_point:
                    st.session_state.source_point = nearest_intersection
                    st.success(f"✅ Start point set to: {nearest_intersection}")
                    st.rerun()
                elif not st.session_state.destination_point and nearest_intersection != st.session_state.source_point:
                    st.session_state.destination_point = nearest_intersection
                    st.success(f"✅ Destination set to: {nearest_intersection}")
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading map: {e}")
    
    # Route calculation results
    if st.session_state.calculate_route and st.session_state.source_point and st.session_state.destination_point:
        st.markdown("---")
        st.subheader("📍 Calculated Route")
        
        try:
            source_id = intersections_dict[st.session_state.source_point]
            destination_id = intersections_dict[st.session_state.destination_point]
            
            if route_type == "Shortest Distance":
                endpoint = f"{API_BASE}/api/routes/shortest?source={source_id}&destination={destination_id}"
            else:
                endpoint = f"{API_BASE}/api/routes/fastest?source={source_id}&destination={destination_id}&avoid_congestion=true"
            
            response = requests.post(endpoint)
            
            if response.status_code == 200:
                route_data = response.json()['data']
                st.session_state.route_result = route_data
                
                # Display route metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📏 Distance", f"{route_data['distance_km']} km")
                with col2:
                    st.metric("⏱️ Est. Time", f"{route_data['estimated_time_minutes']} min")
                with col3:
                    st.metric("🛣️ Intersections", len(route_data['intersections']))
                with col4:
                    avg_congestion = sum([item['congestion'] for item in route_data.get('congestion_levels', [])]) / len(route_data.get('congestion_levels', [1]))
                    st.metric("📊 Avg Congestion", f"{avg_congestion:.0f}%")
                
                # Route details box
                st.markdown("""
                <div class="selected-route">
                <b>✅ Route Successfully Calculated!</b><br>
                Route Type: {}<br>
                Distance: {} km<br>
                Estimated Time: {} minutes
                </div>
                """.format(route_type, route_data['distance_km'], route_data['estimated_time_minutes']), 
                unsafe_allow_html=True)
                
                # Route path
                st.markdown("**Route Path:**")
                route_path = " → ".join(route_data['intersections'])
                st.info(route_path)
                
                # Congestion levels on route
                if 'congestion_levels' in route_data:
                    st.markdown("**Congestion Levels Along Route:**")
                    congestion_cols = st.columns(len(route_data['congestion_levels']))
                    
                    for idx, item in enumerate(route_data['congestion_levels']):
                        congestion = item['congestion']
                        status_icon = "🔴" if congestion >= 80 else "🟡" if congestion >= 50 else "🟢"
                        
                        with congestion_cols[idx]:
                            st.metric(
                                item['intersection'],
                                f"{congestion:.0f}%",
                                delta=status_icon,
                                delta_color="off"
                            )
                    
                    # Detailed congestion breakdown
                    st.markdown("**Detailed Breakdown:**")
                    for item in route_data['congestion_levels']:
                        congestion = item['congestion']
                        status = "🔴 High ⚠️" if congestion >= 80 else "🟡 Medium ⚡" if congestion >= 50 else "🟢 Low ✅"
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['intersection']}**")
                        with col2:
                            st.markdown(f"{congestion:.0f}%")
                        st.progress(congestion / 100)
            else:
                st.error(f"❌ Error calculating route: {response.text}")
        
        except Exception as e:
            st.error(f"❌ Error calculating route: {str(e)}")

with tab2:
    st.subheader("📊 Traffic Analytics Dashboard")
    
    try:
        response = requests.get(f"{API_BASE}/api/traffic/all")
        traffic_data = response.json()['data']
        
        # Create dataframe
        df_data = []
        for int_id, traffic in traffic_data.items():
            df_data.append({
                'Intersection': traffic['name'],
                'Vehicles': traffic['vehicle_count'],
                'Congestion %': traffic['congestion_percentage'],
                'Capacity': traffic.get('capacity', 0),
                'Status': traffic['status'].upper()
            })
        
        df = pd.DataFrame(df_data)
        
        # Display table
        st.markdown("**Traffic Status Table:**")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Statistics cards
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚗 Total Vehicles", int(df['Vehicles'].sum()))
        with col2:
            st.metric("📊 Avg Congestion", f"{df['Congestion %'].mean():.1f}%")
        with col3:
            high_congestion = len(df[df['Status'] == 'HIGH'])
            st.metric("🔴 High Traffic", high_congestion)
        with col4:
            total_capacity = int(df['Capacity'].sum())
            st.metric("🚦 Total Capacity", total_capacity)
        
        # Charts
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vehicle Count by Intersection**")
            st.bar_chart(df.set_index('Intersection')['Vehicles'])
        
        with col2:
            st.markdown("**Congestion % by Intersection**")
            st.bar_chart(df.set_index('Intersection')['Congestion %'])
    
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

with tab3:
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Backend Status")
        try:
            response = requests.get(f"{API_BASE}/api/health")
            health = response.json()
            st.success(f"✅ API Status: {health['status']}")
            st.info(f"Version: {health['version']}")
        except:
            st.error("❌ Backend API not responding")
    
    with col2:
        st.markdown("### ⚙️ System Configuration")
        st.info("""
        **Vehicle Detection:** YOLOv8 Nano
        
        **Database:** SQLite
        
        **Update Interval:** 15 seconds
        
        **Congestion Threshold:** 80%
        
        **Pathfinding:** A* Algorithm
        
        **Map Provider:** Google Maps
        """)
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📖 How to Use RTINA")
    st.markdown("""
    1. **Select Points** - Use dropdown OR click directly on Google Maps
    2. **Choose Route Type** - Pick "Shortest Distance" or "Fastest Route"
    3. **Calculate Route** - Click the calculate button
    4. **View Results** - See route path and congestion levels
    5. **Monitor Traffic** - Track real-time updates in sidebar
    6. **Analytics** - Check detailed stats and charts
    
    **Key Features:**
    - 🚗 Real-time vehicle detection using YOLOv8 AI
    - 🗺️ Interactive Google Maps with live traffic data
    - 📊 Complete traffic analytics and charts
    - 🛣️ Intelligent route optimization (A* algorithm)
    - 🚦 Congestion-aware navigation
    - ⚠️ Real-time traffic alerts (80%+ congestion)
    - 📱 Mobile-responsive design
    """)
    
    st.markdown("---")
    st.markdown("### 👥 Project Information")
    st.markdown("""
    **System:** RTINA (Real-Time IoT-based Traffic Navigation)
    
    **Tech Stack:** Python • FastAPI • YOLOv8 • Streamlit • Google Maps
    
    **Purpose:** Smart city traffic management and optimization
    
    **Status:** ✅ Fully Operational
    
    **Location:** Nagpur, India (5 major intersections)
    
    **Version:** 3.0 (Google Maps Integration)
    """)

# Footer with auto-refresh
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.checkbox("🔄 Auto-refresh every 15 seconds"):
        time.sleep(15)
        st.rerun()

with col2:
    st.info("💡 Tip: Use Google Maps or dropdown to plan routes efficiently")

st.markdown("""
---
<div style='text-align: center; margin-top: 20px; padding: 20px; background: #f0f2f6; border-radius: 10px;'>
    <p style='color: #666; font-size: 12px; margin: 5px 0;'>
        <b>RTINA Traffic Navigation System</b> v3.0
    </p>
    <p style='color: #999; font-size: 11px; margin: 5px 0;'>
        Powered by FastAPI • YOLOv8 • Streamlit • Google Maps API
    </p>
    <p style='color: #999; font-size: 11px;'>
        Real-Time IoT-based Traffic Navigation for Smart Cities
    </p>
</div>
""", unsafe_allow_html=True)