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
import stun  # STUN for public IP detection

class CrypticClient:
    CONFIG_FILE = "config.json"

    def __init__(self):
        # Peer state
        self.public_partner = None
        self.peer_ip = None
        self.peer_port = None
        self.my_port = None
        self.connected = False
        self.received = False
        self.last_seen = None
        self.name = None
        self.config = {}

        # Load config
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                self.config = json.load(f)

        # Retrieve public IP using STUN
        nat_type, external_ip, external_port = stun.get_ip_info()
        self.my_ip = external_ip
        self.my_port = external_port  # default port suggested by NAT
        print(f"[STUN] Public IP detected: {self.my_ip}, External Port: {self.my_port}, NAT type: {nat_type}")

        # Commands
        self.commands = {
            "sendfile": self.cmd_sendfile,
            "quit": self.cmd_quit,
        }

    # ---------- Config ----------
    def save_config(self):
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    # ---------- Commands ----------
    def cmd_sendfile(self, sock, *args):
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(title="Select a file")
        root.destroy()
        try:
            with open(path, "rb") as f:
                data = f.read()
            sock.sendto(data, (self.peer_ip, self.peer_port))
        except Exception as e:
            print(f"Couldn't send file: {e}")

    def cmd_quit(self, *args):
        print("Quitting...")
        sys.exit()

    # ---------- Signaling ----------
    def signaling_client(self, cmd, roomcode, url, username):
        if cmd.upper() == "CREATE":
            r = requests.get(
                url + "/room/new",
                params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip}
            )
            if r.status_code == 200:
                self.my_port = r.json()["status"].split(" ")[2].split(":")[1]
                print(f"Room {roomcode} created")
                while True:
                    time.sleep(2)
                    rr = requests.get(url + "/rooms")
                    rooms = rr.json()
                    if roomcode in rooms and len(rooms[roomcode]["peers"]) >= 2:
                        rr2 = requests.get(
                            url + "/room/join",
                            params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip}
                        )
                        data = rr2.json()
                        for uname, addr in data["peers"].items():
                            if uname != username:
                                sock = self.udp_start(addr.split(":"), username, self.my_port)
                                return sock
            else:
                print("Error creating room:", r.text)
                return None

        elif cmd.upper() == "JOIN":
            r = requests.get(
                url + "/room/join",
                params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip}
            )
            if r.status_code == 404:
                print(f"Room {roomcode} doesn't exist.")
                return None
            if r.status_code == 200:
                self.my_port = r.json()["status"].split(" ")[2].split(":")[1]
                print(f"Room {roomcode} exists. Joining...")
                peers = r.json()["peers"]
                for uname, addr in peers.items():
                    if uname != username:
                        sock = self.udp_start(addr.split(":"), username, self.my_port)
                        return sock
            else:
                print("Error joining room:", r.text)
                return None

    # ---------- UDP ----------
    def udp_listener(self, sock):
        """Listen for incoming UDP packets."""
        self.connected = False
        self.received = False
        while not self.connected:
            try:
                m, addr = sock.recvfrom(1024)
                self.received = True
                if 'CONFIRMRECEIVED' in m.decode():
                    self.connected = True
            except ConnectionResetError:
                pass
        self.last_seen = time.time()
        while True:
            try:
                msg, addr = sock.recvfrom(1024)
            except ConnectionResetError:
                print("Peer disconnected!")
                sys.exit()
            if msg.decode() == "#PING":
                sock.sendto(b"#PONG", addr)
            elif msg.decode() == "#PONG":
                self.last_seen = time.time()
            if not msg.decode().startswith('#'):
                print(msg.decode())

    def check_timeout(self, sock, timeout=10):
        """Send PING periodically and disconnect if timeout."""
        while True:
            time.sleep(1)
            sock.sendto(b"#PING", (self.peer_ip, self.peer_port))
            if time.time() - self.last_seen > timeout:
                print("Peer disconnected!")
                sys.exit()

    def udp_start(self, peer_addr, my_name, my_port):
        """Start UDP handshake with peer."""
        self.peer_ip, self.peer_port = peer_addr
        self.peer_port = int(self.peer_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", int(my_port)))
        print(f"[UDP] Listening on {my_port}")

        t = threading.Thread(target=self.udp_listener, args=(sock,), daemon=True)
        t.start()

        print('Connecting...')
        i = 0
        while not self.connected:
            if not self.received:
                msg = f"HELLO from {my_name} #{i}".encode()
                i += 1
            else:
                msg = b"CONFIRMRECEIVED"
                self.connected = True
            sock.sendto(msg, (self.peer_ip, self.peer_port))
            print(msg.decode(), (self.peer_ip, self.peer_port))
            time.sleep(0.5)

        print('Successfully connected')
        return sock

    # ---------- Messaging ----------
    def sending_messages(self, sock):
        """Read console input and send messages or commands."""
        while True:
            msg = input("")
            print("\033[F\033[K", end="")
            if not msg.startswith('/'):
                print(f"(YOU) {msg}")
                full_msg = f"[{self.name}]: {msg}"
                sock.sendto(full_msg.encode(), (self.peer_ip, self.peer_port))
            else:
                parts = msg[1:].split()
                cmd = parts[0].lower()
                args = parts[1:]
                if cmd in self.commands:
                    self.commands[cmd](sock, *args)
                else:
                    print(f"Unknown command: {cmd}")

    # ---------- Server info ----------
    def get_server_info(self):
        """Get signaling server URL from user or saved config."""
        if "server_url" in self.config:
            print("Where do you want to connect?")
            print("(0) Saved server")
            print("(00) See saved server")
            print("(1) Change server")
            choice = input("Enter number: ").strip()
            while True:
                if choice == "0":
                    server_url = self.config["server_url"]
                    break
                elif choice == '00':
                    print(f'Saved URL: {self.config["server_url"]}')
                    choice = input("Enter number: ").strip()
                elif choice == "1":
                    server_url = input("Enter URL of your Signaling Server: ").strip()
                    self.config["server_url"] = server_url
                    self.save_config()
                    break
        else:
            server_url = input("Enter URL of your Signaling Server: ").strip()
            self.config["server_url"] = server_url
            self.save_config()
        return server_url

    def generate_session_code(self, length=6):
        """Generate a random uppercase alphanumeric session code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # ---------- Open connection ----------
    def open_connection(self):
        SERVER_URL = self.get_server_info()
        self.name = input("What username do you want to use?\n")
        while True:
            choice = input("Do you want to create a room (0) or join one (1)?\n")
            if choice == '0':
                session_code = self.generate_session_code()
                print("Session code:", session_code)
                sock = None
                while sock is None:
                    sock = self.signaling_client('CREATE', session_code, SERVER_URL, self.name)
                return sock
            elif choice == '1':
                session_code = input("Enter room code:\n")
                sock = None
                while sock is None:
                    sock = self.signaling_client('JOIN', session_code, SERVER_URL, self.name)
                    if sock is None:
                        break
                if sock is None:
                    continue
                return sock

    # ---------- Main ----------
    def run(self):
        sock = self.open_connection()
        threading.Thread(target=self.check_timeout, args=(sock,), daemon=True).start()
        self.sending_messages(sock)


if __name__ == '__main__':
    client = CrypticClient()
    client.run()
    
# This is a comment