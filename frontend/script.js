// RTINA Traffic System - Frontend JavaScript
// frontend/script.js

// ======================== GLOBAL STATE ========================

const state = {
    intersections: [],
    currentTraffic: {},
    currentRoute: null,
    journeyActive: false,
    journeyId: null,
    routeResponse: null,
    wsConnected: false
};

// ======================== MAP INITIALIZATION ========================

let map;
let markers = {};
let routePolyline = null;

function initMap() {
    // Center on Nagpur, India
    const nagpurCenter = [21.1458, 79.0882];
    
    map = L.map('map', {
        center: nagpurCenter,
        zoom: 13,
        zoomControl: true,
        scrollWheelZoom: true,
        doubleClickZoom: true
    });
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 10
    }).addTo(map);
    
    // Load intersections
    loadIntersections();
    
    console.log('✓ Map initialized');
}

// ======================== DATA LOADING ========================

async function loadIntersections() {
    try {
        const response = await fetch('/api/intersections');
        const data = await response.json();
        
        state.intersections = data.data;
        
        // Add markers to map
        state.intersections.forEach(intersection => {
            addIntersectionMarker(intersection);
            updateIntersectionSelect(intersection);
        });
        
        // Update traffic list
        updateTrafficList();
        
        console.log(`✓ Loaded ${state.intersections.length} intersections`);
    } catch (error) {
        console.error('Error loading intersections:', error);
        showToast('Error loading intersections', 'error');
    }
}

function addIntersectionMarker(intersection) {
    const { id, name, lat, lon, congestion, status } = intersection;
    
    // Create custom marker
    const markerElement = document.createElement('div');
    markerElement.className = `intersection-marker ${status || 'low'}`;
    markerElement.innerHTML = id;
    markerElement.title = name;
    
    const marker = L.marker([lat, lon], {
        icon: L.divIcon({
            html: markerElement.outerHTML,
            className: 'intersection-marker-wrapper',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        })
    }).addTo(map);
    
    // Add popup
    const popupContent = `
        <div class="marker-popup">
            <h6>${name}</h6>
            <p><strong>ID:</strong> ${id}</p>
            <p><strong>Vehicles:</strong> ${intersection.vehicle_count || 0}</p>
            <p><strong>Congestion:</strong> ${(congestion || 0).toFixed(1)}%</p>
            <p><strong>Status:</strong> <span class="status-badge status-${status}">${status}</span></p>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    markers[id] = { marker, intersection };
}

function updateIntersectionSelect(intersection) {
    const { id, name } = intersection;
    
    const sourceSelect = document.getElementById('sourceSelect');
    const destSelect = document.getElementById('destinationSelect');
    
    const option = `<option value="${id}">${name}</option>`;
    
    sourceSelect.insertAdjacentHTML('beforeend', option);
    destSelect.insertAdjacentHTML('beforeend', option);
}

function updateTrafficList() {
    const trafficList = document.getElementById('trafficList');
    trafficList.innerHTML = '';
    
    state.intersections.forEach(intersection => {
        const { id, name, vehicle_count, congestion, status } = intersection;
        
        const itemHTML = `
            <div class="traffic-item">
                <h6><i class="fas fa-map-pin"></i> ${name}</h6>
                <p>Vehicles: <strong>${vehicle_count || 0}</strong></p>
                <p>Congestion: <strong>${(congestion || 0).toFixed(1)}%</strong></p>
                <span class="status-badge status-${status}">
                    <i class="fas fa-circle"></i> ${status}
                </span>
            </div>
        `;
        
        trafficList.insertAdjacentHTML('beforeend', itemHTML);
    });
}

// ======================== ROUTE CALCULATION ========================

document.getElementById('calculateBtn')?.addEventListener('click', async () => {
    const source = document.getElementById('sourceSelect').value;
    const destination = document.getElementById('destinationSelect').value;
    const routeType = document.querySelector('input[name="routeType"]:checked').value;
    
    if (!source || !destination) {
        showToast('Please select both source and destination', 'warning');
        return;
    }
    
    if (source === destination) {
        showToast('Source and destination cannot be the same', 'warning');
        return;
    }
    
    try {
        const endpoint = routeType === 'shortest' 
            ? `/api/routes/shortest?source=${source}&destination=${destination}`
            : `/api/routes/fastest?source=${source}&destination=${destination}&avoid_congestion=true`;
        
        const response = await fetch(endpoint, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            state.currentRoute = data.data;
            displayRoute(data.data);
            showToast(`${routeType} route calculated successfully`, 'success');
        } else {
            showToast(data.error || 'Error calculating route', 'error');
        }
    } catch (error) {
        console.error('Error calculating route:', error);
        showToast('Error calculating route', 'error');
    }
});

function displayRoute(route) {
    // Clear previous route
    if (routePolyline) {
        map.removeLayer(routePolyline);
    }
    
    const { path, intersections, distance_km, estimated_time_minutes } = route;
    
    // Draw route on map
    const coordinates = path.map(id => {
        const int = state.intersections.find(i => i.id === id);
        return [int.lat, int.lon];
    });
    
    routePolyline = L.polyline(coordinates, {
        color: '#1f8ef1',
        weight: 4,
        opacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round'
    }).addTo(map);
    
    // Fit map to route
    map.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });
    
    // Show route panel
    const routePanel = document.getElementById('routePanel');
    document.getElementById('routePath').textContent = intersections.join(' → ');
    document.getElementById('routeIntersections').textContent = intersections.length;
    routePanel.style.display = 'block';
    
    // Show journey info
    const journeySection = document.querySelector('.journey-section');
    document.getElementById('journeyDistance').textContent = distance_km;
    document.getElementById('journeyTime').textContent = estimated_time_minutes;
    document.getElementById('journeyType').textContent = route.route_type.replace('_', ' ').toUpperCase();
    journeySection.style.display = 'block';
}

// ======================== JOURNEY MANAGEMENT ========================

document.getElementById('startJourneyBtn')?.addEventListener('click', async () => {
    if (!state.currentRoute) {
        showToast('Please calculate a route first', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/journey/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                route_id: state.currentRoute.route_id,
                route_path: state.currentRoute.path
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.journeyActive = true;
            state.journeyId = data.journey_id;
            showToast('Journey started!', 'success');
            monitorJourney();
        } else {
            showToast(data.error || 'Error starting journey', 'error');
        }
    } catch (error) {
        console.error('Error starting journey:', error);
        showToast('Error starting journey', 'error');
    }
});

async function monitorJourney() {
    if (!state.journeyActive || !state.currentRoute) return;
    
    // Check for congestion on current route every 15 seconds
    const checkCongestion = async () => {
        try {
            const trafficData = await fetch('/api/traffic/all').then(r => r.json());
            
            let hasHighCongestion = false;
            state.currentRoute.path.forEach(intId => {
                if (trafficData.data[intId]?.congestion_percentage >= 80) {
                    hasHighCongestion = true;
                }
            });
            
            if (hasHighCongestion) {
                showCongestionAlert();
            }
            
            if (state.journeyActive) {
                setTimeout(checkCongestion, 15000); // Check every 15 seconds
            }
        } catch (error) {
            console.error('Error monitoring journey:', error);
        }
    };
    
    checkCongestion();
}

function showCongestionAlert() {
    const alert = document.getElementById('congestionAlert');
    alert.style.display = 'block';
    
    document.getElementById('yesChangeRoute').onclick = async () => {
        try {
            const response = await fetch(`/api/journey/${state.journeyId}/respond-route-change`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ accept: true })
            });
            
            if (response.ok) {
                showToast('Route change request sent', 'info');
                alert.style.display = 'none';
                // Recalculate route here if needed
            }
        } catch (error) {
            console.error('Error accepting route change:', error);
        }
    };
    
    document.getElementById('noContinue').onclick = () => {
        showToast('Continuing on current route', 'info');
        alert.style.display = 'none';
    };
    
    // Auto-hide after 3 seconds if no response
    setTimeout(() => {
        if (alert.style.display !== 'none') {
            showToast('Continuing on current route (timeout)', 'info');
            alert.style.display = 'none';
        }
    }, 3000);
}

// ======================== WEBSOCKET REAL-TIME UPDATES ========================

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('✓ WebSocket connected');
        state.wsConnected = true;
        updateConnectionStatus(true);
        
        // Send ping to keep connection alive
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    };
    
    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'traffic_update') {
                updateTrafficData(message.data);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
    
    ws.onclose = () => {
        console.log('✗ WebSocket disconnected');
        state.wsConnected = false;
        updateConnectionStatus(false);
        
        // Attempt reconnection after 5 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            initWebSocket();
        }, 5000);
    };
}

function updateTrafficData(trafficData) {
    // Update state
    state.currentTraffic = trafficData;
    
    // Update markers and list
    Object.entries(trafficData).forEach(([intId, traffic]) => {
        const intersection = state.intersections.find(i => i.id == intId);
        if (intersection) {
            intersection.vehicle_count = traffic.vehicle_count;
            intersection.congestion = traffic.congestion_percentage;
            intersection.status = traffic.status;
        }
        
        // Update marker color
        if (markers[intId]) {
            updateMarkerStyle(intId, traffic.status);
        }
    });
    
    // Update traffic list
    updateTrafficList();
}

function updateMarkerStyle(intId, status) {
    const markerElement = document.querySelector(`[data-marker-id="${intId}"]`);
    if (markerElement) {
        markerElement.className = `intersection-marker ${status}`;
    }
}

function updateConnectionStatus(connected) {
    const dot = document.getElementById('connectionDot');
    const text = document.getElementById('connectionText');
    
    if (connected) {
        dot.className = 'status-dot connected';
        text.textContent = 'Connected';
    } else {
        dot.className = 'status-dot disconnected';
        text.textContent = 'Disconnected';
    }
}

// ======================== TOAST NOTIFICATIONS ========================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; gap: 12px; align-items: center;">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// ======================== INITIALIZATION ========================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing RTINA Traffic Navigation System...');
    
    initMap();
    initWebSocket();
    
    console.log('✓ System ready');
});
