import random
import socket
import json
import os
import string
import sys
import threading
import asyncio
import time
from socket import socket
import stun
from aiohttp import ClientSession, WSMsgType
import tkinter as tk
from tkinter import filedialog
#import rsa

#public_key, private_key = rsa.newkeys(1024)
public_partner = None

CONFIG_FILE = "config.json"

def get_external_address():
    nat_type, external_ip, external_port = stun.get_ip_info(stun_host="stun.l.google.com", stun_port=19302)
    print("NAT Type:", nat_type)
    print("External IP:", external_ip)
    print("External Port:", external_port)
    return external_ip, external_port

my_ip, my_port = get_external_address()

def cmd_sendfile(sock, *args):
    # Creating a hidden root
    root = tk.Tk()
    root.withdraw()  # Hides the main window

    # Directly open the dialogue
    path = filedialog.askopenfilename(title="Select a file")

    root.destroy()  # Closes the hidden root
    try:
        with open(path, "rb") as f:
            data = f.read()
        # manda tutto il contenuto via socket
        sock.sendto(data, (peer_ip, peer_port))
    except Exception as e:
        print(f"Couldn't send file: {e}")
def cmd_quit(*args):
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

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

async def create_room(server_url, room_code: str, room_name: str,  username: str, password: str) -> socket | bool:
    my_addr = (my_ip, my_port)
    params = {
        "room-code": room_code,
        "room-name": room_name,
        "address": my_addr,
        "name": username,
        "pass": password
    }
    async with ClientSession() as session:
        async with session.get(f"{server_url}/room/new", params=params) as resp:
            if resp.status == 200:
                print(f"Room '{room_name}' with code {room_code} created!")
                sock = await wait_for_peer(
                    server_url=server_url,
                    room_code=room_code,
                    username=username,
                    password=password,
                    my_addr=my_addr
                )
                return sock
            else:
                text = await resp.text()
                print(f"Error creating room: {resp.status} {text}")
                return False

async def join_room(server_url, room_code: str, username: str, password: str) -> socket | bool:
    params = {"room-code": room_code, "name": username, "pass": password}
    async with ClientSession() as session:
        async with session.get(f"{server_url}/room/join", params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(data)
                print(f"Successfully joined room {room_code}")
                peer_name, peer_addr = ('Peer', '127.0.0.1')
                sock = udp_start(peer_addr.split(":"), username, my_port)
                return sock
            text = await resp.text()
            print(f"Error joining room: {resp.status} {text}")
            return False

async def wait_for_peer(server_url: str,
                        room_code: str,
                        username: str,
                        password: str,
                        my_addr: tuple,
                        poll_interval: float = 2.0) -> socket | None:
    """
    Do polling with /room/join until it receives a peer
    After receiving one, launch udp_start to connect to them
    """
    params = {"room-code": room_code, "name": username, "pass": password}

    while True:
        async with ClientSession() as session:
            async with session.get(f"{server_url}/room/join", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("Data received from server:", data)

                    # get ip, port and name
                    peer_ip   = data["ip"]
                    peer_port = int(data["port"])
                    peer_name = data["name"]

                    print(f"Got peer {peer_name}")
                    sock = udp_start((peer_ip, peer_port), username, my_port)
                    return sock

                elif resp.status == 425:
                    # 425 = server says "still no other peer"
                    # wait and retry
                    await asyncio.sleep(poll_interval)
                    continue

                else:
                    text = await resp.text()
                    print(f"Error joining room: {resp.status} {text}")
                    return None

def udp_listener(sock):
    global connected, received, last_seen
    """Listens for incoming UDP packets and prints"""
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
            return msg.decode()

def udp_start(peer_addr, my_name, my_port):
    global connected, peer_ip, peer_port
    """
    Starts-up listener and sends HELLO packets to peer.
    peer_addr: tuple (ip, port)
    my_name: name of local peer (to identify themselves)
    """
    peer_ip, peer_port = peer_addr
    peer_port = int(peer_port)

    # creates local UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", int(my_port)))
    print(f"[UDP] Listening on {my_port}")

    # starts listener on a separate thread
    t = threading.Thread(target=udp_listener, args=(sock,))
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

def check_timeout(sock, timeout=10):
    global last_seen, peer_ip, peer_port
    while True:
        time.sleep(1)  # check each second
        sock.sendto(b"#PING", (peer_ip, peer_port))
        if time.time() - last_seen > timeout:
            print("Peer disconnected!")
            sys.exit()

def sending_messages(sock):
    global peer_ip, peer_port, name
    while True:
        msg = input("")  # get message from the console
        print("\033[F\033[K", end="")
        if not msg.startswith('/'):
            print(f"(YOU) {msg}")
            full_msg = f"[{name}]: {msg}"
            sock.sendto(full_msg.encode(), (peer_ip, peer_port))
            return full_msg
        else:
            parts = msg[1:].split()  # removes '/' and separates
            cmd = parts[0].lower()  # command name
            args = parts[1:]  # command-line arguments
            if cmd in commands:
                commands[cmd](sock, *args)  # call the function
            else:
                print(f"Unknown command: {cmd}")


def get_server_info():
    """
    Get the signaling server URL and port from the user.
    Allows using saved values or changing them.
    """
    if "server_url" in config:
        # Saved server exists
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
                # Change server IP
                server_url = input("Enter URL of your Signaling Server: ").strip()
                config["server_url"] = server_url
                save_config()
                break
    else:
        # No saved server, ask directly
        server_url = input("Enter URL of your Signaling Server: ").strip()
        config["server_url"] = server_url
        save_config()

    return server_url

def generate_session_code(length=6):
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
            sock = asyncio.run(
                create_room(SERVER_URL, session_code,
                            room_name='Roomie', username=name, password='')
            )
            print(sock)
            return sock
        elif choice == '1':
            session_code = input("Enter room code:\n")
            sock = None
            while sock is None:
                print(create_room(SERVER_URL, session_code, room_name='Roomie', username=name, password=''))
                if sock == 1:
                    break
            if sock == 1:
                continue
            return sock

def main():
    sock = open_connection() # open_connection returns None in case of timeout with SS
    # timeout thread
    threading.Thread(target=check_timeout, args=(sock, )).start()
    sending_messages(sock)

if __name__=='__main__':
    main()