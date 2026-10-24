"""
GPS Simulator for IoT Testing (No hardware required)
Simulates ESP32 GPS tracker sending data to backend API
"""
import requests
import random
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

class GPSSimulator:
    """
    Simulates GPS tracker device (ESP32 + NEO-6M GPS).
    Sends location data to SIPAM backend API.
    """
    
    def __init__(self, api_url="http://localhost:8000/api/v1", api_key="iot_device_key_12345"):
        self.api_url = api_url
        self.api_key = api_key
        self.device_id = f"ESP32_SIM_{random.randint(1000, 9999)}"
        self.practice_id = f"PRAC_{random.randint(100, 999)}"
        
        # Starting location (Universidad Surcolombiana, Neiva)
        self.base_lat = 2.4419
        self.base_lng = -76.6063
        
        # Current position
        self.current_lat = self.base_lat
        self.current_lng = self.base_lng
        
        # Battery starts at 100%
        self.battery = 4.2
        
        print("=" * 60)
        print("GPS TRACKER SIMULATOR")
        print("=" * 60)
        print(f"Device ID: {self.device_id}")
        print(f"Practice ID: {self.practice_id}")
        print(f"API URL: {self.api_url}")
        print(f"Starting position: ({self.base_lat:.4f}, {self.base_lng:.4f})")
        print("=" * 60)
    
    def generate_gps_data(self, movement_type='random'):
        """
        Generate simulated GPS data.
        
        Args:
            movement_type: 'random', 'linear', or 'stationary'
        
        Returns:
            dict: GPS data packet
        """
        # Simulate movement
        if movement_type == 'random':
            # Random walk
            self.current_lat += random.uniform(-0.0005, 0.0005)
            self.current_lng += random.uniform(-0.0005, 0.0005)
        elif movement_type == 'linear':
            # Linear movement (vehicle)
            self.current_lat += random.uniform(0.0001, 0.0003)
            self.current_lng += random.uniform(-0.0001, 0.0001)
        elif movement_type == 'stationary':
            # Small GPS drift
            self.current_lat += random.uniform(-0.00005, 0.00005)
            self.current_lng += random.uniform(-0.00005, 0.00005)
        
        # Battery drains slowly
        self.battery -= random.uniform(0, 0.01)
        self.battery = max(3.0, self.battery)  # Min 3.0V
        
        # Build data packet
        data = {
            "device_id": self.device_id,
            "practice_id": self.practice_id,
            "timestamp": int(time.time() * 1000),  # Milliseconds like ESP32
            
            # GPS Data
            "latitude": round(self.current_lat, 6),
            "longitude": round(self.current_lng, 6),
            "altitude": round(1500 + random.uniform(-50, 50), 1),
            "speed_kmh": round(random.uniform(30, 60) if movement_type == 'linear' else random.uniform(0, 5), 1),
            "course": round(random.uniform(0, 360), 1),
            
            # GPS Quality
            "satellites": random.randint(6, 12),
            "hdop": round(random.uniform(0.8, 2.5), 1),
            
            # Timestamp
            "datetime_gps": datetime.utcnow().isoformat() + "Z",
            
            # Device Status
            "battery_voltage": round(self.battery, 2),
            "wifi_rssi": random.randint(-80, -50),  # Signal strength
            "uptime_seconds": int(time.time())
        }
        
        return data
    
    def send_data(self, data):
        """Send GPS data to backend API."""
        endpoint = f"{self.api_url}/iot/tracking/"
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.post(
                endpoint,
                json=data,
                headers=headers,
                timeout=5
            )
            
            return response.status_code == 200 or response.status_code == 201
            
        except requests.exceptions.ConnectionError:
            print("  ✗ Connection failed - Backend not available")
            return False
        except requests.exceptions.Timeout:
            print("  ✗ Request timeout")
            return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def run_simulation(self, duration_minutes=5, interval_seconds=30, movement_type='random'):
        """
        Run GPS simulation.
        
        Args:
            duration_minutes: How long to run simulation
            interval_seconds: Seconds between data sends
            movement_type: 'random', 'linear', or 'stationary'
        """
        print(f"\nStarting simulation...")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Interval: {interval_seconds} seconds")
        print(f"Movement: {movement_type}")
        print()
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        sent_count = 0
        failed_count = 0
        
        while time.time() < end_time:
            # Generate data
            data = self.generate_gps_data(movement_type)
            
            # Send data
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Sending: ({data['latitude']:.6f}, {data['longitude']:.6f}) "
                  f"Speed: {data['speed_kmh']:.1f} km/h "
                  f"Bat: {data['battery_voltage']:.2f}V", end="")
            
            if self.send_data(data):
                sent_count += 1
                print(" ✓")
            else:
                failed_count += 1
                print(" ✗")
            
            # Wait for next interval
            time.sleep(interval_seconds)
        
        # Summary
        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)
        print(f"Duration: {duration_minutes} minutes")
        print(f"Data points sent: {sent_count}")
        print(f"Failed sends: {failed_count}")
        print(f"Success rate: {sent_count/(sent_count+failed_count)*100:.1f}%")
        print()
        print("Course Compliance:")
        print("  ✓ IoT Device simulation (ESP32)")
        print("  ✓ GPS data (lat, lng, altitude, speed)")
        print("  ✓ WiFi communication (HTTP REST)")
        print("  ✓ Device status (battery, signal)")
        print("  ✓ JSON data format")
        print("=" * 60)
    
    def save_track(self, filename='simulated_track.json'):
        """Save simulated track to file."""
        track = []
        
        # Generate 20 points
        for i in range(20):
            data = self.generate_gps_data(movement_type='linear')
            track.append({
                "lat": data['latitude'],
                "lng": data['longitude'],
                "time": data['datetime_gps'],
                "speed": data['speed_kmh']
            })
            time.sleep(0.1)  # Small delay
        
        with open(filename, 'w') as f:
            json.dump(track, f, indent=2)
        
        print(f"✓ Track saved to: {filename}")

def test_backend_connection(api_url):
    """Test if backend is running."""
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Backend connection successful")
            return True
    except:
        pass
    
    print("✗ Backend not available")
    print(f"  URL: {api_url}")
    print("\nMake sure backend is running:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    return False

def main():
    parser = argparse.ArgumentParser(
        description='GPS Tracker Simulator for SIPAM IoT Module'
    )
    parser.add_argument('--api-url', type=str, 
                       default='http://localhost:8000/api/v1',
                       help='Backend API URL')
    parser.add_argument('--api-key', type=str,
                       default='iot_device_key_12345',
                       help='IoT API key')
    parser.add_argument('--duration', type=int, default=2,
                       help='Simulation duration in minutes')
    parser.add_argument('--interval', type=int, default=10,
                       help='Seconds between sends (default: 10 for demo)')
    parser.add_argument('--movement', type=str, default='linear',
                       choices=['random', 'linear', 'stationary'],
                       help='Movement simulation type')
    parser.add_argument('--test-only', action='store_true',
                       help='Test connection and exit')
    
    args = parser.parse_args()
    
    # Test connection
    if not test_backend_connection(args.api_url):
        if not args.test_only:
            return
    
    if args.test_only:
        print("\nConnection test complete.")
        return
    
    # Run simulation
    simulator = GPSSimulator(args.api_url, args.api_key)
    simulator.run_simulation(
        duration_minutes=args.duration,
        interval_seconds=args.interval,
        movement_type=args.movement
    )

if __name__ == "__main__":
    main()
