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
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel

import os
import sys
import json
import time
import random
import string
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog
import requests
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
import stun


class CrypticClient:
    CONFIG_FILE = "config.json"

    def __init__(self):
        # Peer state
        self.private_port = 31825
        self.public_partner = None
        self.peer_ip = None
        self.peer_port = None
        self.connected = False
        self.received = False
        self.last_seen = None
        self.name = None
        self.config = {}

        # aiortc objects
        self.pc = None
        self.channel = None

        # Load config
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                self.config = json.load(f)

        # Retrieve public IP using STUN
        self.my_ip, self.my_port, self.nat_type = self.get_stun()
        print(f"[STUN] Public IP detected: {self.my_ip}, External Port: {self.my_port}, NAT type: {self.nat_type}")

        # Commands
        self.commands = {
            "sendfile": self.cmd_sendfile,
            "quit": self.cmd_quit,
        }

    @staticmethod
    def get_stun():
        my_ip, my_port = None, None
        attempt = 1
        while None in (my_ip, my_port):
            print(f"Contacting STUN server... (attempt {attempt})")
            nat_type, external_ip, external_port = stun.get_ip_info()
            my_ip = external_ip
            my_port = external_port
            attempt += 1
        return my_ip, my_port, nat_type

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
            # Send file over data channel
            self.channel.send(data)
        except Exception as e:
            print(f"Couldn't send file: {e}")

    def cmd_quit(self, *args):
        print("Quitting...")
        sys.exit()

    # ---------- Signaling ----------
    async def signaling_client(self, cmd, roomcode, url, username):
        """WebRTC version of signaling_client"""
        self.pc = RTCPeerConnection()
        self.channel = self.pc.createDataChannel("chat")
        self.channel.on("open", lambda: print("[WebRTC] Data channel opened"))
        self.channel.on("message", self.on_message)

        if cmd.upper() == "CREATE":
            r = requests.get(
                url + "/room/new",
                params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip, "peer_port": self.my_port}
            )
            if r.status_code != 200:
                print("Error creating room:", r.text)
                return None

            print(f"Room {roomcode} created. Waiting for peers...")

            while True:
                await asyncio.sleep(2)
                rr = requests.get(url + "/rooms")
                rooms = rr.json()
                if roomcode in rooms and len(rooms[roomcode]["peers"]) >= 2:
                    rr2 = requests.get(
                        url + "/room/join",
                        params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip, "peer_port": self.my_port}
                    )
                    data = rr2.json()
                    for uname, addr in data["peers"].items():
                        if uname != username:
                            await self.connect_peer(addr)
                            return self.channel

        elif cmd.upper() == "JOIN":
            r = requests.get(
                url + "/room/join",
                params={"room_code": roomcode, "username": username, "peer_ip": self.my_ip, "peer_port": self.my_port}
            )
            if r.status_code == 404:
                print(f"Room {roomcode} doesn't exist.")
                return None
            if r.status_code == 200:
                peers = r.json()["peers"]
                for uname, addr in peers.items():
                    if uname != username:
                        await self.connect_peer(addr)
                        return self.channel
            else:
                print("Error joining room:", r.text)
                return None

    async def connect_peer(self, addr):
        """Perform WebRTC handshake with peer via signaling server."""
        ip, port = addr.split(":")
        port = int(port)

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # Send offer to signaling server
        r = requests.post(
            f"http://{ip}:{port}/offer",
            json={"sdp": self.pc.localDescription.sdp, "type": self.pc.localDescription.type}
        )
        answer = r.json()
        await self.pc.setRemoteDescription(
            RTCSessionDescription(sdp=answer["sdp"], type=answer["type"])
        )
        self.connected = True
        self.last_seen = time.time()
        print("[WebRTC] Peer connected!")

    # ---------- Messaging ----------
    def on_message(self, msg):
        if isinstance(msg, bytes):
            print("[FILE] Received bytes:", len(msg))
        else:
            print(msg)

    async def sending_messages_async(self):
        """Read console input and send messages or commands."""
        while True:
            msg = await asyncio.to_thread(input, "")
            if not msg.startswith('/'):
                print(f"(YOU) {msg}")
                full_msg = f"[{self.name}]: {msg}"
                self.channel.send(full_msg)
            else:
                parts = msg[1:].split()
                cmd = parts[0].lower()
                args = parts[1:]
                if cmd in self.commands:
                    self.commands[cmd](self.channel, *args)
                else:
                    print(f"Unknown command: {cmd}")

    # ---------- Timeout ----------
    async def check_timeout_async(self, timeout=10):
        while True:
            await asyncio.sleep(1)
            if self.connected and (time.time() - self.last_seen > timeout):
                print("Peer disconnected!")
                sys.exit()

    # ---------- Server info ----------
    def get_server_info(self):
        if "server_url" in self.config:
            print("Where do you want to connect?")
            print("(0) Saved server")
            print("(00) See saved server")
            print("(1) Change server")
            choice = input("Enter number: ").strip()
            while True:
                if choice == "0":
                    return self.config["server_url"]
                elif choice == '00':
                    print(f'Saved URL: {self.config["server_url"]}')
                    choice = input("Enter number: ").strip()
                elif choice == "1":
                    server_url = input("Enter URL of your Signaling Server: ").strip()
                    self.config["server_url"] = server_url
                    self.save_config()
                    return server_url
        else:
            server_url = input("Enter URL of your Signaling Server: ").strip()
            self.config["server_url"] = server_url
            self.save_config()
            return server_url

    def generate_session_code(self, length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # ---------- Open connection ----------
    async def open_connection_async(self):
        SERVER_URL = self.get_server_info()
        self.name = input("What username do you want to use?\n")
        while True:
            choice = input("Do you want to create a room (0) or join one (1)?\n")
            if choice == '0':
                session_code = self.generate_session_code()
                print("Session code:", session_code)
                channel = None
                while channel is None:
                    channel = await self.signaling_client('CREATE', session_code, SERVER_URL, self.name)
                return channel
            elif choice == '1':
                session_code = input("Enter room code:\n")
                channel = None
                while channel is None:
                    channel = await self.signaling_client('JOIN', session_code, SERVER_URL, self.name)
                    if channel is None:
                        break
                if channel is None:
                    continue
                return channel

    # ---------- Main ----------
    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        await self.open_connection_async()
        await asyncio.gather(
            self.sending_messages_async(),
            self.check_timeout_async()
        )


if __name__ == '__main__':
    client = CrypticClient()
    client.run()