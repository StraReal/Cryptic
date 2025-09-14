import random
import socket
import json
import os
import string
import sys
import time
import requests
import argparse
from contextlib import redirect_stdout, redirect_stderr

# Global variables
CONFIG_FILE = "config.json"
peer_ip = None
peer_port = None
my_port = None
my_ip = None  # Initialize as None
name = None
SERVER_URL = None

# --- Load existing config ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

def debug_print(message, debug=False):
    """Print debug message to stderr if debug mode is enabled."""
    if debug:
        print(f"DEBUG: {message}", file=sys.stderr)

def get_my_ip(debug=False):
    """Get the public IP address."""
    global my_ip
    if my_ip is None:
        try:
            my_ip = requests.get("https://api.ipify.org").text
            debug_print(f"Detected local IP as {my_ip}", debug)
        except requests.exceptions.RequestException as e:
            debug_print(f'Error retrieving IP: {e}', debug)
            # Fallback to local IP if public IP detection fails
            try:
                # Create a dummy socket to get local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                my_ip = s.getsockname()[0]
                s.close()
                debug_print(f"Using fallback local IP: {my_ip}", debug)
            except Exception as e:
                debug_print(f"Fallback IP detection also failed: {e}", debug)
                my_ip = "127.0.0.1"  # Last resort fallback
                debug_print(f"Using localhost as fallback: {my_ip}", debug)
    return my_ip

def save_config():
    """Save the current configuration to disk."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def create_room(roomcode, url, username, debug=False):
    """
    Create a room and return connection details.
    """
    global my_port
    
    debug_print(f"Attempting to create room {roomcode} at {url}", debug)
    
    # Ensure we have an IP address
    ip = get_my_ip(debug)
    debug_print(f"Using IP: {ip}", debug)
    
    try:
        r = requests.get(
            url + "/room/new",
            params={"room_code": roomcode, "username": username, "peer_ip": ip},
            timeout=10
        )
        debug_print(f"Server response status: {r.status_code}", debug)
        debug_print(f"Server response body: {r.text}", debug)
        
        if r.status_code == 200:
            try:
                response_data = r.json()
                debug_print(f"Parsed JSON response: {response_data}", debug)
                
                # Extract port from status message
                status = response_data.get("status", "")
                debug_print(f"Status message: {status}", debug)
                
                # Check if the status indicates room creation
                if "ROOM_CREATED" in status:
                    # Extract the IP:port part which is the last part of the status
                    parts = status.split()
                    if len(parts) >= 3:
                        ip_port = parts[-1]  # Get the last part (IP:port)
                        if ":" in ip_port:
                            my_ip, my_port = ip_port.split(":")
                            debug_print(f"Extracted my_ip: {my_ip}, my_port: {my_port}", debug)
                            
                            return {
                                "status": "room_created",
                                "room_code": roomcode,
                                "my_port": my_port,
                                "my_ip": my_ip,
                                "message": f"Room {roomcode} created successfully"
                            }
                
                # Fallback: try to find IP:port pattern anywhere in the status
                import re
                ip_port_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)'
                match = re.search(ip_port_pattern, status)
                if match:
                    my_ip = match.group(1)
                    my_port = match.group(2)
                    debug_print(f"Extracted using regex - my_ip: {my_ip}, my_port: {my_port}", debug)
                    
                    return {
                        "status": "room_created",
                        "room_code": roomcode,
                        "my_port": my_port,
                        "my_ip": my_ip,
                        "message": f"Room {roomcode} created successfully"
                    }
                
                # If we can't parse the status, return an error
                return {"error": f"Could not parse port from status: {status}"}
                
            except json.JSONDecodeError as e:
                debug_print(f"Failed to parse JSON response: {e}", debug)
                return {"error": f"Invalid JSON response: {r.text}"}
        else:
            return {"error": f"Server returned status {r.status_code}: {r.text}"}
            
    except requests.exceptions.RequestException as e:
        debug_print(f"Request exception: {e}", debug)
        return {"error": f"Connection error: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description='P2P Room Creator')
    parser.add_argument('--server-url', required=True, help='Signaling server URL')
    parser.add_argument('--room-code', help='Room code (will generate if not provided)')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    # Initialize IP before creating room
    get_my_ip(args.debug)
    
    # Create room
    result = create_room(
        args.room_code or ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
        args.server_url,
        args.username,
        args.debug
    )
    
    # Only print the JSON result to stdout
    print(json.dumps(result))

if __name__=='__main__':
    main()