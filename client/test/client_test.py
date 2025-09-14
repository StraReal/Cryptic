# peer_app.py
import random
import socket
import json
import os
import string
import sys
import threading
import time
import requests

# --- CONFIG ---
CONFIG_FILE = "config.json"
SERVER_URL = None
name = None
room_code = None

# --- Load saved server (optional) ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    SERVER_URL = config.get("server_url")

# --- Parse arguments from Electron ---
if len(sys.argv) < 4:
    print(json.dumps({
        "error": "Usage: python peer_app.py <server_url> <room_code> <username>"
    }))
    sys.exit(1)

SERVER_URL = sys.argv[1]
room_code = sys.argv[2]
name = sys.argv[3]

# --- Save server URL if new ---
if "server_url" not in locals() or not SERVER_URL:
    config["server_url"] = SERVER_URL
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# --- Get public IP ---
try:
    my_ip = requests.get("https://api.ipify.org").text
except Exception as e:
    print(json.dumps({"error": f"Failed to get IP: {e}"}))
    sys.exit(1)

# --- Generate session code if needed ---
def generate_session_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- Signaling Client (HTTP only, no GUI) ---
def signaling_client(cmd, roomcode, url, username):
    global my_port, peer_ip, peer_port

    if cmd.upper() == "CREATE":
        r = requests.get(
            url + "/room/new",
            params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
        )
        if r.status_code != 200:
            print(json.dumps({"error": f"Create failed: {r.text}"}))
            sys.exit(1)
        
        my_port = r.json()["status"].split(" ")[2].split(":")[1]
        print(json.dumps({"status": f"Room {roomcode} created", "my_port": my_port}))
        
        # Wait for peer
        while True:
            time.sleep(2)
            rr = requests.get(url + "/rooms")
            rooms = rr.json()
            if roomcode in rooms and len(rooms[roomcode]["peers"]) >= 2:
                rr2 = requests.get(
                    url + "/room/join",
                    params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
                )
                data = rr2.json()
                for uname, addr in data["peers"].items():
                    if uname != username:
                        peer_ip, peer_port = addr.split(":")
                        peer_port = int(peer_port)
                        return udp_start()

    elif cmd.upper() == "JOIN":
        r = requests.get(
            url + "/room/join",
            params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
        )
        if r.status_code == 404:
            print(json.dumps({"error": f"Room {roomcode} doesn't exist."}))
            sys.exit(1)
        if r.status_code != 200:
            print(json.dumps({"error": f"Join failed: {r.text}"}))
            sys.exit(1)

        my_port = r.json()["status"].split(" ")[2].split(":")[1]
        peers = r.json()["peers"]
        for uname, addr in peers.items():
            if uname != username:
                peer_ip, peer_port = addr.split(":")
                peer_port = int(peer_port)
                return udp_start()

    print(json.dumps({"error": "Unknown command"}))
    sys.exit(1)

# --- UDP Connection Setup ---
def udp_start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", int(my_port)))
    
    # Send HELLO
    i = 0
    connected = False
    while not connected:
        msg = f"HELLO from {name} #{i}".encode()
        sock.sendto(msg, (peer_ip, peer_port))
        i += 1
        time.sleep(0.5)
        try:
            sock.settimeout(1)
            m, addr = sock.recvfrom(1024)
            if b"CONFIRMRECEIVED" in m:
                connected = True
        except socket.timeout:
            continue
    
    print(json.dumps({"status": "Connected to peer!", "peer_ip": peer_ip, "peer_port": peer_port}))
    
    # Start listener thread
    def udp_listener():
        global last_seen
        last_seen = time.time()
        while True:
            try:
                msg, addr = sock.recvfrom(1024)
                if msg.decode() == "#PING":
                    sock.sendto(b"#PONG", addr)
                elif msg.decode() == "#PONG":
                    last_seen = time.time()
                else:
                    # Forward message to Electron via stdout
                    print(json.dumps({
                        "type": "message",
                        "from": "peer",
                        "content": msg.decode()
                    }))
            except Exception:
                break

    threading.Thread(target=udp_listener, daemon=True).start()

    # Start timeout checker
    def check_timeout():
        while True:
            time.sleep(1)
            sock.sendto(b"#PING", (peer_ip, peer_port))
            if time.time() - last_seen > 10:
                print(json.dumps({"type": "disconnected", "reason": "Peer timed out"}))
                sys.exit(1)

    threading.Thread(target=check_timeout, daemon=True).start()

    return sock

# --- File Sending (no GUI!) ---
def send_file(file_path):
    """Send file over UDP — called by Electron later"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (peer_ip, peer_port))
        print(json.dumps({
            "type": "file_sent",
            "filename": os.path.basename(file_path),
            "status": "success"
        }))
    except Exception as e:
        print(json.dumps({
            "type": "file_sent",
            "filename": os.path.basename(file_path),
            "status": "error",
            "error": str(e)
        }))

# --- Main Logic ---
if __name__ == '__main__':
    cmd = sys.argv[4] if len(sys.argv) > 4 else "JOIN"  # default JOIN

    if cmd == "CREATE" or cmd == "JOIN":
        signaling_client(cmd, room_code, SERVER_URL, name)
        # Now we are connected — wait for messages or commands
    else:
        print(json.dumps({"error": "Invalid command. Use CREATE or JOIN"}))
        sys.exit(1)

    # Wait forever — we'll receive messages via stdout
    # And we'll accept commands via stdin later (see below)
    while True:
        time.sleep(1)
        

import sys
import json

def read_commands():
    while True:
        try:
            line = sys.stdin.readline().strip()
            if not line:
                continue
            cmd = json.loads(line)
            if cmd["action"] == "sendfile":
                send_file(cmd["path"])
            elif cmd["action"] == "quit":
                print(json.dumps({"type": "quitting"}))
                sys.exit(0)
        except Exception as e:
            print(json.dumps({"type": "error", "message": f"Bad command: {str(e)}"}))

threading.Thread(target=read_commands, daemon=True).start()