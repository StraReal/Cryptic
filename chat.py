import random
import socket
import json
import os
import string
import sys
import threading
import asyncio
import time

from aiohttp import ClientSession, WSMsgType
import uuid
import rsa
import stun

public_key, private_key = rsa.newkeys(1024)
public_partner = None

SERVER_PORT = 5000 # port of signaling server
CONFIG_FILE = "config.json"
MAX_CHUNK = 115

# --- Carica config esistente ---
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

async def signaling_client(cmd, roomcode, url, username):
    async with ClientSession() as session:
        async with session.ws_connect(url) as ws:
            # esempio: Peer A crea stanza
            await ws.send_str(f"{cmd} room{roomcode} {username}")

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    print("Received from server:", msg.data)

                    if msg.data.startswith("PEER"):
                        # qui il server ti ha dato IP:porta dell'altro peer
                        _, peer_name, peer_addr = msg.data.split(" ", 2)
                        udp_start(peer_addr.split(":"), username)

def udp_listener(sock):
    """Listens for incoming UDP packets and prints"""
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[UDP] Received from {addr}: {data.decode()}")

def udp_start(peer_addr, my_name):
    """
    Avvia listener e manda pacchetti HELLO al peer.
    peer_addr: tuple (ip, port)
    my_name: nome del peer locale (per identificarsi)
    """
    peer_ip, peer_port = peer_addr
    peer_port = int(peer_port)

    # crea socket UDP locale
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 0))  # 0 = porta scelta dal sistema
    my_port = sock.getsockname()[1]
    print(f"[UDP] Listening on {my_port}")

    # avvia thread listener
    threading.Thread(target=udp_listener, args=(sock,), daemon=True).start()

    # manda più pacchetti al peer
    for i in range(10):
        msg = f"HELLO from {my_name} #{i}".encode()
        sock.sendto(msg, (peer_ip, peer_port))
        print(f"[UDP] Sent to {peer_ip}:{peer_port}: {msg}")
        time.sleep(0.5)

    return sock

def get_server_info():
    """
    Get the signaling server URL and port from the user.
    Allows using saved values or changing them.
    """
    if "server_url" in config:
        # Saved server exists
        print("Where do you want to connect?")
        print("(0) Saved server")
        print("(1) Change server")
        choice = input("Enter number: ").strip()

        if choice == "0":
            server_url = config["server_url"]
            server_port = config.get("server_port", SERVER_PORT)

            # Ask if the user wants to change the port
            change_port = input(f"Current port is {server_port}. Change port? (y/n): ").lower().strip()
            if change_port == "y":
                port_input = input(f"Enter new port [{SERVER_PORT}]: ").strip()
                server_port = int(port_input) if port_input else SERVER_PORT
                config["server_port"] = server_port
                save_config()

        elif choice == "1":
            # Change server IP
            server_url = input("Enter URL of your Signaling Server: ").strip()
            port_input = input(f"Enter port [{SERVER_PORT}]: ").strip()
            server_port = int(port_input) if port_input else SERVER_PORT
            config["server_url"] = server_url
            config["server_port"] = server_port
            save_config()
        else:
            print("Invalid choice, using saved server by default.")
            server_url = config["server_url"]
            server_port = config.get("server_port", SERVER_PORT)

    else:
        # No saved server, ask directly
        server_url = input("Enter URL of your Signaling Server: ").strip()
        port_input = input(f"Enter port [{SERVER_PORT}]: ").strip()
        server_port = int(port_input) if port_input else SERVER_PORT
        config["server_url"] = server_url
        config["server_port"] = server_port
        save_config()

    return server_url, server_port

def generate_session_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def open_connection():
    global public_partner, SERVER_URL, SERVER_PORT
    SERVER_URL, SERVER_PORT = get_server_info()
    name = input("What username do you want to connect with? (No spaces allowed)\n")
    choice = input("Do you want to create a room (0) or join one (1)?\n")
    if choice == '0':
        session_code = generate_session_code()
        print("Session code:", session_code)
        asyncio.run(signaling_client('CREATE', session_code, SERVER_URL, name))
        print(f"Connected to signaling server as {name}")
    elif choice == '1':
        session_code = input("Enter room code:\n")
        asyncio.run(signaling_client('JOIN', session_code, SERVER_URL, name))
        print(f"Connected to signaling server as {name}")

def main():
    running = True
    open_connection()
    while running:
        msg = input('')




if __name__=='__main__':
    main()