"""
Standalone metrics exporter for Flask parking application.

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
    Parse parking statistics from the table:
    columns: ID | Etaza | Sekcija | Je Okupirano (True/False)
    """
    try:
        import re

        # Match table rows and extract the last <td> value (True/False)
        # Example row:
        # <tr> ... <td>False</td> </tr>
        values = re.findall(
            r"<tr>\s*(?:<td>.*?</td>\s*){3}<td>\s*(True|False)\s*</td>\s*</tr>",
            html_content,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not values:
            # fallback: count occurrences of <td>True</td> / <td>False</td>
            true_count = len(re.findall(r"<td>\s*True\s*</td>", html_content, flags=re.IGNORECASE))
            false_count = len(re.findall(r"<td>\s*False\s*</td>", html_content, flags=re.IGNORECASE))
        else:
            true_count = sum(1 for v in values if v.lower() == "true")
            false_count = sum(1 for v in values if v.lower() == "false")

        occupied = true_count
        free = false_count
        total = occupied + free

        parking_spots_occupied.set(occupied)
        parking_spots_free.set(free)
        parking_spots_total.set(total)
        if total > 0:
            parking_occupancy_ratio.set(occupied / total)

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
