import asyncio
import json
import logging
import os
import sys
from aiortc import RTCPeerConnection, RTCSessionDescription
import websockets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64
import shlex
import tkinter as tk
from tkinter import filedialog

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

# serialize public key to send it
def serialize_public_key(pubkey):
    return pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

logging.basicConfig(level=logging.INFO)

CONFIG_FILE = "config.json"

def to_websocket_url(url):
    """
    Convert any http(s) URL to a ws(s) URL and ensure it ends with '/ws'.
    """
    scheme, rest = url.split("://", 1)
    ws_scheme = "wss" if scheme == "https" else "ws"
    return f"{ws_scheme}://{rest.rstrip('/')}/ws"

# Async input helper
async def aio_input():
    return await asyncio.to_thread(input, "> ")

class ChatClient:
    def __init__(self):
        self.config = {}
        self.name = None
        self.room = None
        self.password = ""
        self.create = False
        self.ishost = False  # Set True for host
        self.load_config()
        self.peers = {}       # peer_id -> RTCPeerConnection
        self.channels = {}    # peer_id -> DataChannel
        self.keys = {}
        self.channel_open = False
        self.ws = None
        self.rsapriv, self.rsapub = generate_rsa_keys()
        self.commands = {
            "sendfile": self.cmd_sendfile
        }
        self.host_id = None
        self.msgcount = 0

    # -----------------------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    async def cmd_sendfile(self, *args):
        print('Function not implemented yet')
        pass

    def encrypt_message(self, peer_id, plaintext):
        fernet = Fernet(self.keys[peer_id])
        token = fernet.encrypt(plaintext.encode())  # returns base64 bytes
        return token.decode("ascii")  # JSON-friendly string

    def decrypt_message(self, peer_id, token):
        fernet = Fernet(self.keys[peer_id])
        return fernet.decrypt(token.encode("ascii")).decode("utf-8")

    async def listen_server(self):
        async for raw in self.ws:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            t = data.get("type")
            if t == "error":
                print("Server error:", data.get("message"))
            elif t == "created":
                print(f"Room {data.get('room')} created")
            # Setup connections
            elif t == "gotjoined":
                if self.ishost:
                    user = data.get("user")
                    print(f"{user} joined the room")
                    # Connect to all peers in room
                    new_peer = user
                    if new_peer:
                        logging.info("Received offer_request for %s — creating PEER connection", new_peer)
                        await self.setup_host_peer(new_peer)
            elif t == 'joined':
                host_id = data.get("user")
                print(f"Joined room {data.get('room')} (host: {host_id})")
                await self.setup_client_peer(host_id)

            elif t in ("offer", "answer"):
                sender = data.get("from")
                if sender != self.name:
                    await self.handle_signaling(sender, data)

            elif t == "bye":
                logging.info("Peer said BYE — exiting")
                break

        # Close all connections
        for pc in self.peers.values():
            await pc.close()

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
                elif choice == "00":
                    print(f'Saved URL: {self.config["server_url"]}')
                    choice = input("Enter number: ").strip()
                elif choice == "1":
                    server_url = input("Enter server URL: ").strip()
                    self.config["server_url"] = server_url
                    self.save_config()
                    return server_url
        else:
            server_url = input("Enter WebSocket URL: ").strip()
            self.config["server_url"] = server_url
            self.save_config()
            return server_url

    async def connect_server(self, url):
        self.ws = await websockets.connect(to_websocket_url(url))

    # -----------------------------
    async def join_room(self):
        self.name = input("What username do you want to use?\n")
        while True:
            choice = input("Do you want to create a room (0) or join one (1)?\n")
            if choice == "0":
                self.create = True
                self.room = input("Enter a 6-character room code to create:\n").strip().upper()
                if len(self.room) != 6:
                    print("Room code must be exactly 6 characters.")
                    continue
                self.password = input("Enter password:\n").strip()
                self.ishost = True
                break
            elif choice == "1":
                self.create = False
                self.room = input("Enter the 6-character room code to join:\n").strip().upper()
                if len(self.room) != 6:
                    print("Room code must be exactly 6 characters.")
                    continue
                self.password = input("Enter password:\n").strip()
                self.ishost = False
                break

        await self.ws.send(json.dumps({
            "type": "join",
            "room": self.room,
            "from": self.name,
            "password": self.password,
            "create": self.create
        }))
        return

    # -----------------------------
    async def async_input_loop(self):
        loop = asyncio.get_event_loop()
        while True:
            msg = self.msgcount
            if self.ishost:
                for other_id, ch in self.channels.items():
                    encrypted = self.encrypt_message(other_id, f"[{self.name}] {msg}")
                    ch.send(encrypted)
            else:
                encrypted = self.encrypt_message(self.host_id, f"[{self.name}] {msg}")
                self.channels[self.host_id].send(encrypted)
            self.msgcount += 1

    # -----------------------------
    async def run(self):
        server_url = self.get_server_info()
        await self.connect_server(server_url)
        await self.join_room()
        await self.listen_server()
        # -----------------------------

    # -----------------------------
    # Host setup
    async def setup_host_peer(self, peer_id):
        if peer_id in self.peers:
            logging.info("setup_host_peer: pc for %s already exists", peer_id)
            return
        pc = RTCPeerConnection()
        self.peers[peer_id] = pc
        channel = pc.createDataChannel("chat")
        self.channels[peer_id] = channel

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(msg):
                # Relay to all other peers
                plaintext = self.decrypt_message(peer_id, msg)
                print(plaintext)
                for other_id, ch in self.channels.items():
                    if other_id != peer_id:
                        ch.send(self.encrypt_message(other_id, plaintext))

        @channel.on("open")
        def on_open():
            logging.info(f"Channel open with {peer_id}")
            if not self.channel_open:
                asyncio.create_task(self.async_input_loop())
            channel.send(self.encrypt_message(peer_id, f"{self.name} is hosting the room"))
            self.channel_open = True

        @pc.on("iceconnectionstatechange")
        def on_ice_state():
            logging.info(f"ICE state with {peer_id}: {pc.iceConnectionState}")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await self.ws.send(json.dumps({
            "type": "offer",
            "room": self.room,
            "from": self.name,
            "to": peer_id,
            "sdp": pc.localDescription.sdp,
            "sdpType": pc.localDescription.type,
            "pubKey": serialize_public_key(self.rsapub).decode("ascii")
        }))
    # -----------------------------
    # Client setup
    async def setup_client_peer(self, host_id):
        self.host_id = host_id
        pc = RTCPeerConnection()
        self.peers[host_id] = pc
        channel = pc.createDataChannel("chat")
        self.channels[host_id] = channel
        key = Fernet.generate_key()
        self.keys[host_id] = key

        @channel.on("open")
        def on_open():
            logging.info("DataChannel open to host — start typing messages")
            asyncio.create_task(self.async_input_loop())
            channel.send(self.encrypt_message(host_id, f"{self.name} joined the room"))

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(msg):
                plaintext = self.decrypt_message(host_id, msg)
                print(plaintext)

        @pc.on("iceconnectionstatechange")
        def on_ice_state():
            logging.info(f"ICE state with host: {pc.iceConnectionState}")
    # -----------------------------
    async def handle_signaling(self, peer_id, data):
        pc = self.peers.get(peer_id)
        if not pc:
            logging.warning(f"No PC found for {peer_id}")
            return

        t = data["type"]
        if t == "offer":
            offer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdpType"])
            peer_pubkey_bytes = data["pubKey"].encode("ascii")
            peer_rsapub = serialization.load_pem_public_key(peer_pubkey_bytes)

            # encrypt it with peer's RSA public key
            encrypted_key = peer_rsapub.encrypt(
                self.keys[peer_id],
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Base64 encode to send via JSON/WebSocket
            encrypted_key_b64 = base64.b64encode(encrypted_key).decode("ascii")

            await pc.setRemoteDescription(offer_desc)
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            await self.ws.send(json.dumps({
                "type": "answer",
                "room": self.room,
                "from": self.name,
                "to": peer_id,
                "sdp": pc.localDescription.sdp,
                "sdpType": pc.localDescription.type,
                "fernetKey": encrypted_key_b64
            }))
        elif t == "answer":
            answer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdpType"])
            encrypted_key_bytes = base64.b64decode(data["fernetKey"])
            fernet_key = self.rsapriv.decrypt(
                encrypted_key_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # now create a Fernet object for this peer
            self.keys[peer_id] = fernet_key
            await pc.setRemoteDescription(answer_desc)

# -----------------------------
if __name__ == "__main__":
    try:
        asyncio.run(ChatClient().run())
    except KeyboardInterrupt:
        pass

