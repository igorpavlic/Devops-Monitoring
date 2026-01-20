"""
Standalone metrics exporter for Flask parking application.
Runs as a sidecar container - no modifications to app.py required.
"""

from prometheus_client import start_http_server, Gauge, Counter, Histogram
import requests
import time
import os
import threading

# Configuration
APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', '15'))

# Prometheus metrics
app_up = Gauge('parking_app_up', 'Application availability (1=up, 0=down)')
app_response_time = Histogram(
    'parking_app_response_time_seconds',
    'Response time of health check',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
health_check_total = Counter(
    'parking_app_health_checks_total',
    'Total health checks performed',
    ['status']
)

# Application-specific metrics (scraped from app)
parking_spots_total = Gauge('parking_spots_total', 'Total parking spots')
parking_spots_occupied = Gauge('parking_spots_occupied', 'Occupied parking spots')
parking_spots_free = Gauge('parking_spots_free', 'Free parking spots')
parking_occupancy_ratio = Gauge('parking_occupancy_ratio', 'Parking occupancy ratio (0-1)')


def check_health():
    """Perform health check against the main application."""
    try:
        start_time = time.time()
        response = requests.get(f'{APP_URL}/', timeout=10)
        response_time = time.time() - start_time
        
        app_response_time.observe(response_time)
        
        if response.status_code == 200:
            app_up.set(1)
            health_check_total.labels(status='success').inc()
            
            # Parse parking stats from response if possible
            parse_parking_stats(response.text)
        else:
            app_up.set(0)
            health_check_total.labels(status='error').inc()
            
    except requests.exceptions.RequestException as e:
        app_up.set(0)
        health_check_total.labels(status='error').inc()
        print(f"Health check failed: {e}")


def parse_parking_stats(html_content):
    """
    Extract parking statistics from the index page.
    This is a simple parser - adjust based on your actual HTML structure.
    """
    try:
        # Simple parsing - looks for patterns in the HTML
        # Adjust these based on your actual index.html template
        import re
        
        # Example: looking for "Zauzeto: X" and "Slobodno: Y" patterns
        occupied_match = re.search(r'occupied[_\-]?count["\s:>]+(\d+)', html_content, re.IGNORECASE)
        free_match = re.search(r'(not[_\-]?occupied|free)[_\-]?count["\s:>]+(\d+)', html_content, re.IGNORECASE)
        
        # Alternative: count based on common patterns
        occupied = html_content.lower().count('zauzeto') or 0
        
        if occupied_match:
            occ = int(occupied_match.group(1))
            parking_spots_occupied.set(occ)
            
        if free_match:
            free = int(free_match.group(2) if free_match.lastindex >= 2 else free_match.group(1))
            parking_spots_free.set(free)
            
        # If we have both, calculate total and ratio
        if occupied_match and free_match:
            total = occ + free
            parking_spots_total.set(total)
            if total > 0:
                parking_occupancy_ratio.set(occ / total)
                
    except Exception as e:
        print(f"Could not parse parking stats: {e}")


def metrics_collector():
    """Background thread that collects metrics periodically."""
    while True:
        check_health()
        time.sleep(SCRAPE_INTERVAL)


if __name__ == '__main__':
    print(f"Starting metrics exporter on port {METRICS_PORT}")
    print(f"Monitoring application at {APP_URL}")
    
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    
    # Start background collector
    collector_thread = threading.Thread(target=metrics_collector, daemon=True)
    collector_thread.start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)
