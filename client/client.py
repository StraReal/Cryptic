import random
import socket
import json
import os
import string
import sys
import threading
import time
import requests
import tkinter as tk
from tkinter import filedialog

# public_key, private_key = rsa.newkeys(1024)   # not used
public_partner = None

CONFIG_FILE = "config.json"

peer_ip = None
peer_port = None
my_port = None
connected = False
received = False
last_seen = None
name = None

def cmd_sendfile(sock, *args):
    """Open a file dialog and send the selected file to the peer over UDP."""
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select a file")
    root.destroy()
    try:
        with open(path, "rb") as f:
            data = f.read()
        sock.sendto(data, (peer_ip, peer_port))
    except Exception as e:
        print(f"Couldn't send file: {e}")

def cmd_quit(*args):
    """Exit the program."""
    print("Quitting...")
    sys.exit()

commands = {
    "sendfile": cmd_sendfile,
    "quit": cmd_quit,
}

# --- Load existing config ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

try:
    my_ip = requests.get("https://api.ipify.org").text
except requests.exceptions.ConnectionError as e:
    print('Error occurred retrieving IP:', e)
    sys.exit(1)

def save_config():
    """Save the current configuration to disk."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def signaling_client(cmd, roomcode, url, username):
    """
    Replaces the old WebSocket signaling with HTTP requests.
    It creates or joins a room and retrieves peer info if available.
    """
    global my_port

    if cmd.upper() == "CREATE":
        r = requests.get(
            url + "/room/new",
            params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
        )
        if r.status_code == 200:
            # Server returns status string with peer address in it, same parsing as before
            my_port = r.json()["status"].split(" ")[2].split(":")[1]
            print(f"Room {roomcode} created")
            # Wait for a peer to join before returning socket
            while True:
                time.sleep(2)
                rr = requests.get(url + "/rooms")
                rooms = rr.json()
                if roomcode in rooms and len(rooms[roomcode]["peers"]) >= 2:
                    # Someone joined, get their address
                    rr2 = requests.get(
                        url + "/room/join",
                        params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
                    )
                    data = rr2.json()
                    for uname, addr in data["peers"].items():
                        if uname != username:
                            sock = udp_start(addr.split(":"), username, my_port)
                            return sock
        else:
            print("Error creating room:", r.text)
            return 1

    elif cmd.upper() == "JOIN":
        r = requests.get(
            url + "/room/join",
            params={"room_code": roomcode, "username": username, "peer_ip": my_ip}
        )
        if r.status_code == 404:
            print(f"Room {roomcode} doesn't exist.")
            return 1
        if r.status_code == 200:
            my_port = r.json()["status"].split(" ")[2].split(":")[1]
            print(f"Room {roomcode} exists. Joining...")
            peers = r.json()["peers"]
            for uname, addr in peers.items():
                if uname != username:
                    sock = udp_start(addr.split(":"), username, my_port)
                    return sock
        else:
            print("Error joining room:", r.text)
            return 1

def udp_listener(sock):
    """Listens for incoming UDP packets and prints them."""
    global connected, received, last_seen
    connected = False
    received = False
    while not connected:
        try:
            m, addr = sock.recvfrom(1024)
            received = True
            if 'CONFIRMRECEIVED' in m.decode():
                connected = True
        except ConnectionResetError:
            pass
    last_seen = time.time()
    while True:
        try:
            msg, addr = sock.recvfrom(1024)
        except ConnectionResetError:
            print("Peer disconnected!")
            sys.exit()
        if msg.decode() == "#PING":
            sock.sendto(b"#PONG", addr)
        elif msg.decode() == "#PONG":
            last_seen = time.time()
        if not msg.decode().startswith('#'):
            print(msg.decode())

def check_timeout(sock, timeout=10):
    """Send PING and exit if peer doesn't respond within timeout seconds."""
    global last_seen, peer_ip, peer_port
    while True:
        time.sleep(1)
        sock.sendto(b"#PING", (peer_ip, peer_port))
        if time.time() - last_seen > timeout:
            print("Peer disconnected!")
            sys.exit()

def udp_start(peer_addr, my_name, my_port):
    """
    Start the UDP handshake with the peer.
    peer_addr: list [ip, port]
    my_name: local peer name
    """
    global connected, peer_ip, peer_port
    peer_ip, peer_port = peer_addr
    peer_port = int(peer_port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", int(my_port)))
    print(f"[UDP] Listening on {my_port}")

    t = threading.Thread(target=udp_listener, args=(sock,), daemon=True)
    t.start()
    print('Connecting...')
    i = 0
    while not connected:
        if not received:
            msg = f"HELLO from {my_name} #{i}".encode()
            i += 1
        else:
            msg = b"CONFIRMRECEIVED"
            connected = True
        sock.sendto(msg, (peer_ip, peer_port))
        print(msg.decode(), (peer_ip, peer_port))
        time.sleep(0.5)
    print('Succesfully connected')
    return sock

def sending_messages(sock):
    """Read console input and send messages or commands."""
    global peer_ip, peer_port, name
    while True:
        msg = input("")
        print("\033[F\033[K", end="")
        if not msg.startswith('/'):
            print(f"(YOU) {msg}")
            full_msg = f"[{name}]: {msg}"
            sock.sendto(full_msg.encode(), (peer_ip, peer_port))
        else:
            parts = msg[1:].split()
            cmd = parts[0].lower()
            args = parts[1:]
            if cmd in commands:
                commands[cmd](sock, *args)
            else:
                print(f"Unknown command: {cmd}")

def get_server_info():
    """
    Get the signaling server base URL from the user.
    Allows using saved values or changing them.
    """
    if "server_url" in config:
        print("Where do you want to connect?")
        print("(0) Saved server")
        print("(00) See saved server")
        print("(1) Change server")
        choice = input("Enter number: ").strip()

        while True:
            if choice == "0":
                server_url = config["server_url"]
                break
            elif choice == '00':
                print(f'Saved URL: {config["server_url"]}')
                choice = input("Enter number: ").strip()
            elif choice == "1":
                server_url = input("Enter URL of your Signaling Server: ").strip()
                config["server_url"] = server_url
                save_config()
                break
    else:
        server_url = input("Enter URL of your Signaling Server: ").strip()
        config["server_url"] = server_url
        save_config()

    return server_url

def generate_session_code(length=6):
    """Generate a random uppercase alphanumeric code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def open_connection():
    global public_partner, SERVER_URL, my_port, name
    SERVER_URL = get_server_info()
    name = input("What username do you want to use?\n")
    while True:
        choice = input("Do you want to create a room (0) or join one (1)?\n")
        if choice == '0':
            session_code = generate_session_code()
            print("Session code:", session_code)
            sock = None
            while sock is None:
                sock = signaling_client('CREATE', session_code, SERVER_URL, name)
            return sock
        elif choice == '1':
            session_code = input("Enter room code:\n")
            sock = None
            while sock is None:
                sock = signaling_client('JOIN', session_code, SERVER_URL, name)
                if sock == 1:
                    break
            if sock == 1:
                continue
            return sock

def main():
    sock = open_connection()
    threading.Thread(target=check_timeout, args=(sock,), daemon=True).start()
    sending_messages(sock)

if __name__=='__main__':
    main()
