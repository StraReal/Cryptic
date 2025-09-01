import random
import socket
import json
import os
import string
import sys
import threading
import asyncio
import time
import requests
from aiohttp import ClientSession, WSMsgType
#import rsa

#public_key, private_key = rsa.newkeys(1024)
public_partner = None

CONFIG_FILE = "config.json"

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

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

async def signaling_client(cmd, roomcode, url, username):
    global my_port
    async with ClientSession() as session:
        async with session.ws_connect(url) as ws:
            await ws.send_str(f"{cmd} room{roomcode} {username} {my_ip}")

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    if msg.data.startswith("ROOM_CREATED"):
                        my_port = msg.data.split(" ")[2].split(':')[1]
                        print(f"Room {roomcode} created")
                    elif msg.data.startswith("JOIN_ROOM"):
                        my_port = msg.data.split(" ")[2].split(':')[1]
                        print(f"Room {roomcode} exists. Joining...")
                    elif msg.data.startswith("PEER"):
                        # here the server gave you the ip:port of the other peer
                        _, peer_name, peer_addr = msg.data.split(" ", 2)
                        sock = udp_start(peer_addr.split(":"), username, my_port)
                        return sock
                    elif msg.data.startswith("ROOM_INEXISTENT"):
                        # here the server gave you the ip:port of the other peer
                        print(f"Room {roomcode} doesn't exist.")
                        return 1

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

def check_timeout(sock, timeout=10):
    global last_seen, peer_ip, peer_port
    while True:
        time.sleep(1)  # check each second
        sock.sendto(b"#PING", (peer_ip, peer_port))
        if time.time() - last_seen > timeout:
            print("Peer disconnected!")
            sys.exit()

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
    global peer_ip, peer_port, name
    """Send messages to peer until /quit"""
    while True:
        msg = input("")  # get message from the console
        if msg.lower() == "/quit":
            print("Quitting...")
            break
        print("\033[F\033[K", end="")
        print(f"(YOU) {msg}")
        full_msg = f"[{name}]: {msg}"
        sock.sendto(full_msg.encode(), (peer_ip, peer_port))


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
                server_url = config["server_url"]+'/ws'
                break
            elif choice == '00':
                print(f'Saved URL: {config["server_url"]}')
                choice = input("Enter number: ").strip()
            elif choice == "1":
                # Change server IP
                server_url = input("Enter URL of your Signaling Server: ").strip()+'/ws'
                config["server_url"] = server_url[:-3]
                save_config()
                break
    else:
        # No saved server, ask directly
        server_url = input("Enter URL of your Signaling Server: ").strip()+'/ws'
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
            sock = None
            while sock is None:
                sock = asyncio.run(signaling_client('CREATE', session_code, SERVER_URL, name))
            return sock
        elif choice == '1':
            session_code = input("Enter room code:\n")
            sock = None
            while sock is None:
                sock = asyncio.run(signaling_client('JOIN', session_code, SERVER_URL, name))
                if sock == 1:
                    break
            if sock == 1:
                continue
            return sock

def main():
    sock = open_connection() # open_connection returns None in case of timeout with SS
    # timeout thread
    threading.Thread(target=check_timeout, args=(sock, ), daemon=True).start()
    sending_messages(sock)

if __name__=='__main__':
    main()