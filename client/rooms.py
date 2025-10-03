import asyncio
import json
import logging
import os
from aiortc import RTCPeerConnection, RTCSessionDescription
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
import base64
import shlex
import sys
import websockets
import tkinter as tk
from tkinter import filedialog
import tempfile
import math, uuid
import media

CONFIG_FILE = "config.json"
CHUNK_SIZE = 8000

def generate_rsa_keys():
    """
    Generate a new RSA private/public key pair.

    Returns:
        tuple: (private_key, public_key)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_public_key(pubkey):
    """
    Serialize an RSA public key to PEM format.

    Args:
        pubkey: The RSA public key object.

    Returns:
        bytes: The serialized public key in PEM format.
    """
    return pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def to_websocket_url(url):
    """
    Convert an HTTP/HTTPS URL to a WebSocket URL.

    Args:
        url (str): The HTTP or HTTPS URL.

    Returns:
        str: The corresponding ws:// or wss:// URL.
    """
    scheme, rest = url.split("://", 1)
    ws_scheme = "wss" if scheme == "https" else "ws"
    return f"{ws_scheme}://{rest.rstrip('/')}/ws"

def get_file_path(filename, file_bytes):
    """
    Save raw bytes as a temporary file and return the path.

    Args:
        filename (str): Name of the file to create.
        file_bytes (bytes): Raw binary content.

    Returns:
        str: Path to the saved temporary file.
    """
    tmp_dir = tempfile.gettempdir()
    filepath = os.path.join(tmp_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    return filepath

class ChatClient:
    """
    A peer-to-peer chat client that uses WebRTC for real-time communication
    and RSA/Fernet encryption for secure messaging.
    """

    def __init__(self):
        """
        Initialize the chat client and load configuration.
        """
        self.config = {}
        self.name = None
        self.room = None
        self.password = ""
        self.create = False
        self.ishost = False  # True if this client is the host
        self.load_config()
        self.peers = {}       # peer_id -> RTCPeerConnection
        self.channels = {}    # peer_id -> DataChannel
        self.chunk_buffers = {} # peer_id -> list of chunks
        self.keys = {}
        self.channel_open = False
        self.ws = None
        self.rsapriv, self.rsapub = generate_rsa_keys()
        self.commands = {
            "sendfile": self.cmd_sendfile
        }
        self.host_id = None
        self.default_server = "signalingserverdomain.download"

    def load_config(self):
        """
        Load configuration from the CONFIG_FILE if it exists.
        """
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        """
        Save the current configuration to the CONFIG_FILE.
        """
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def cmd_sendfile(self, *args):
        """
        Command handler: /sendfile
        Opens a file picker dialog and sends the selected file to peers.
        """
        # Open file picker invisibly
        root = tk.Tk()
        root.withdraw()  # hide the main window
        root.attributes("-topmost", True)
        filepath = filedialog.askopenfilename(title="Select file")
        root.destroy()

        if not filepath:
            print("No file selected.")
            return

        # Read the file in binary
        with open(filepath, "rb") as f:
            data = f.read()

        asyncio.create_task(self.send_message("file", data, filename=os.path.basename(filepath)))

    def encrypt_message(self, peer_id, plaintext):
        """
        Encrypt a message using the Fernet key for a peer.

        Args:
            peer_id (str): ID of the peer.
            plaintext (str): The plaintext message.

        Returns:
            str: The encrypted message (base64 string).
        """
        fernet = Fernet(self.keys[peer_id])
        token = fernet.encrypt(plaintext.encode())
        return token.decode("ascii")

    def decrypt_message(self, peer_id, token):
        """
        Decrypt a message using the Fernet key for a peer.

        Args:
            peer_id (str): ID of the peer.
            token (str): Base64-encoded ciphertext.

        Returns:
            str: The decrypted plaintext.
        """
        fernet = Fernet(self.keys[peer_id])
        return fernet.decrypt(token.encode("ascii")).decode("utf-8")

    async def listen_server(self):
        """
        Listen for messages from the signaling server and handle events.
        """
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
                    print(f"{user} is joining the room")
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
        """
        Retrieve or update the server URL from the configuration or user input.
        Always ensures the URL starts with 'https://'.

        Args:
            default_server (str): The fallback/default server URL.

        Returns:
            str: The chosen server URL with 'https://' prefix.
        """

        def ensure_https(url: str) -> str:
            url = url.strip()
            # Find if there's a scheme (like http:// or ftp://) and remove it
            if "://" in url:
                url = url.split("://", 1)[1]
            # Prepend https://
            return "https://" + url

        saved_server = self.config.get("server_url")

        if saved_server:
            print("Where do you want to connect?")
            print(f"(0) Default server ({self.default_server})")
            print(f"(1) Saved server   ({saved_server})")
            print("(2) Change server")
            while True:
                choice = input("Enter number: ").strip()
                if choice == "0":
                    return ensure_https(self.default_server)
                elif choice == "1":
                    return ensure_https(saved_server)
                elif choice == "2":
                    server_url = input("Enter server URL: ").strip()
                    self.config["server_url"] = ensure_https(server_url)
                    self.save_config()
                    return self.config["server_url"]
        else:
            print("Where do you want to connect?")
            print(f"(0) Default server ({self.default_server})")
            print("(1) Custom server")
            while True:
                choice = input("Enter number: ").strip()
                if choice == "0":
                    return ensure_https(self.default_server)
                elif choice == "1":
                    server_url = input("Enter server URL: ").strip()
                    self.config["server_url"] = ensure_https(server_url)
                    self.save_config()
                    return self.config["server_url"]

    async def connect_server(self, url):
        """
        Connect to the signaling server via WebSocket.

        Args:
            url (str): The server URL.
        """
        self.ws = await websockets.connect(to_websocket_url(url))

    async def join_room(self):
        """
        Prompt the user to create or join a room and send the join request.
        """
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

    async def async_input_loop(self):
        """
        Asynchronous loop to read user input and send messages or execute commands.
        """
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, sys.stdin.readline)
            if not msg:
                break
            msg = msg.strip()
            if msg.startswith('/'):
                parts = shlex.split(msg)  # ["/command", "arg1", "arg2", ...]
                cmd = parts[0][1:]
                args = parts[1:]
                if cmd in self.commands:
                    self.commands[cmd](*args)
                    continue

            # Build the message
            text_payload = f"[{self.name}] {msg}"
            await self.send_message("text", text_payload.encode("utf-8"))

    async def send_message(self, msg_type, content: bytes, filename=None):
        """
        Send a message (text or file), automatically chunking if needed.
        Universal approach: everything is base64-encoded first.
        content must already be bytes.
        """
        # Base64 encode entire content
        full_b64 = base64.b64encode(content).decode("ascii")
        total_len = len(full_b64)
        chunk_total = math.ceil(total_len / CHUNK_SIZE)
        msg_id = str(uuid.uuid4())
        for i in range(chunk_total):
            start = i * CHUNK_SIZE
            end = start + CHUNK_SIZE
            chunk_content = full_b64[start:end]

            chunk_payload = {
                "type": msg_type,
                "msg_id": msg_id,
                "chunk_index": i,
                "chunk_total": chunk_total,
                "content": chunk_content
            }
            if filename:
                chunk_payload["name"] = filename

            json_payload = json.dumps(chunk_payload)

            if self.ishost:
                for other_id, ch in self.channels.items():
                    ch.send(self.encrypt_message(other_id, json_payload))
            else:
                self.channels[self.host_id].send(self.encrypt_message(self.host_id, json_payload))

    def _reconstruct_chunks(self, peer_id, msg_id):
        """
        Reconstruct chunks from message ID but DO NOT decode.
        Returns a dict like:
        {"type": "text" or "file", "content": <base64 string>, "name": optional}
        Assumes all expected chunks are present in the buffer.
        """
        peer_buf = self.chunk_buffers.get(peer_id, {})
        chunks = peer_buf.get(msg_id)
        if not chunks:
            return None
        try:
            # Ensure we have unique chunk_index -> chunk mapping (ignore duplicate arrivals)
            idx_map = {}
            for c in chunks:
                idx = c.get("chunk_index", 0)
                # prefer the first received chunk for a particular index
                if idx not in idx_map:
                    idx_map[idx] = c

            # Build ordered list by index
            ordered = [idx_map[i] for i in sorted(idx_map.keys())]

            combined = {"type": ordered[0].get("type", "text")}

            # Join base64 fragments in order WITHOUT decoding
            b64_full = "".join(chunk["content"] for chunk in ordered)
            combined["content"] = b64_full

            if combined["type"] == "file":
                # preserve original filename if present
                combined["name"] = ordered[0].get("name", "unknown")

            # Cleanup buffer for this msg_id
            peer_buf.pop(msg_id, None)
            if not peer_buf:
                self.chunk_buffers.pop(peer_id, None)
            return combined
        except Exception as e:
            print(f"Error reconstructing chunks for {peer_id} msg_id {msg_id}: {e}")
            # attempt best-effort cleanup
            try:
                peer_buf.pop(msg_id, None)
                if not peer_buf:
                    self.chunk_buffers.pop(peer_id, None)
            except Exception:
                pass
            return None

    def handle_message(self, peer_id, msg):
        """
        Handle a received encrypted message from a peer, including numeric chunked messages.
        The reconstructor returns base64 content only; decoding happens here.
        """
        content = None
        filename = None
        try:
            decrypted = self.decrypt_message(peer_id, msg)
        except Exception as e:
            print(f"Failed to decrypt message from {peer_id}: {e}")
            return

        try:
            data = json.loads(decrypted)
        except json.JSONDecodeError:
            print(f"Invalid JSON message from {peer_id}")
            return

        msg_id = data.get("msg_id")
        chunk_total = int(data.get("chunk_total", 1))

        # If a msg_id is present we treat it as chunked (even if chunk_total == 1).
        if msg_id:
            # Ensure buffer structures exist
            if peer_id not in self.chunk_buffers:
                self.chunk_buffers[peer_id] = {}
            if msg_id not in self.chunk_buffers[peer_id]:
                self.chunk_buffers[peer_id][msg_id] = []

            # Avoid storing exact duplicate chunk objects (same index + content)
            incoming_index = data.get("chunk_index", 0)
            existing = self.chunk_buffers[peer_id][msg_id]
            duplicate = False
            for ex in existing:
                if ex.get("chunk_index") == incoming_index and ex.get("content") == data.get("content"):
                    duplicate = True
                    break
            if not duplicate:
                existing.append(data)

            # If we haven't got all pieces yet, wait
            if len({c.get("chunk_index") for c in self.chunk_buffers[peer_id][msg_id]}) < chunk_total:
                return

            # All chunks present -> reconstruct (reconstructor will clean up buffer)
            reconstructed = self._reconstruct_chunks(peer_id, msg_id)
            if reconstructed is None:
                print(f"Failed to reconstruct message from {peer_id} msg_id {msg_id}")
                return
            final = reconstructed
        else:
            # No msg_id -- treat as a single, self-contained message (content is base64)
            final = data

        # Now decode the base64 content (reconstructor returned base64 string)
        b64_content = final.get("content", "")
        try:
            raw_bytes = base64.b64decode(b64_content)
        except Exception as e:
            print(f"Failed to base64-decode content from {peer_id}: {e}")
            return

        msg_type = final.get("type", "text")
        if msg_type == "text":
            try:
                content = raw_bytes
                print(content.decode("utf-8"))
            except Exception as e:
                # If decoding fails, show a hex preview instead of crashing
                print(f"(text decode error) raw bytes from {peer_id}: {raw_bytes[:64].hex()}... ({e})")
                return
        elif msg_type == "file":
            content = raw_bytes
            filename = final.get("name", "unknown")
            try:
                filepath = get_file_path(filename, raw_bytes)
                print('file:///' + filepath.replace("\\", "/"))
            except Exception as e:
                print(f"Failed to save file from {peer_id}: {e}")
        else:
            print(f"Unknown message type from {peer_id}: {msg_type}")

        # Relay unchanged original encrypted message if host
        if self.ishost:
            for other_id, ch in self.channels.items():
                if other_id != peer_id:
                    try:
                        asyncio.create_task(self.send_message(msg_type, content, filename))
                    except Exception as e:
                        print(f"Failed to relay message to {other_id}: {e}")

    async def run(self):
        """
        Main entry point: connect to the server, join a room, and listen for events.
        """
        server_url = self.get_server_info()
        print(server_url)
        await self.connect_server(server_url)
        await self.join_room()
        await self.listen_server()

    async def setup_host_peer(self, peer_id):
        """
        Set up a new peer connection when hosting.

        Args:
            peer_id (str): The ID of the joining peer.
        """
        if peer_id in self.peers:
            logging.info("setup_host_peer: pc for %s already exists", peer_id)
            return
        pc = RTCPeerConnection()
        self.peers[peer_id] = pc
        channel = pc.createDataChannel("chat")
        self.channels[peer_id] = channel
        self.add_media_tracks(pc, peer_id)

        @pc.on("connectionstatechange")
        def on_connection_state():
            logging.info(f"Connection state: {pc.connectionState}")

        @pc.on("icecandidate")
        def on_icecandidate(candidate):
            if candidate:
                logging.info(f"Discovered candidate: {candidate}")

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(msg):
                self.handle_message(peer_id, msg)

        @channel.on("open")
        def on_open():
            logging.info(f"Channel open with {peer_id}")
            if not self.channel_open:
                asyncio.create_task(self.async_input_loop())
            asyncio.create_task(self.send_message('text', f"{self.name} is hosting the room".encode("utf-8")))
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

    async def setup_client_peer(self, host_id):
        """
        Set up the peer connection as a client joining a host.

        Args:
            host_id (str): ID of the host peer.
        """
        self.host_id = host_id
        pc = RTCPeerConnection()
        self.peers[host_id] = pc
        channel = pc.createDataChannel("chat")
        self.channels[host_id] = channel
        key = Fernet.generate_key()
        self.keys[host_id] = key
        self.add_media_tracks(pc, host_id)

        @channel.on("open")
        def on_open():
            asyncio.create_task(self.async_input_loop())
            asyncio.create_task(self.send_message('text', f"{self.name} joined the room".encode("utf-8")))

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(msg):
                self.handle_message(host_id, msg)

        @pc.on("iceconnectionstatechange")
        def on_ice_state():
            logging.info(f"ICE state with host: {pc.iceConnectionState}")

    def add_media_tracks(self, pc, peer_id):
        video_track = media.VideoChannelTrack()
        audio_track = media.AudioChannelTrack()
        pc.addTrack(video_track)
        pc.addTrack(audio_track)
        self.peers[peer_id]['video'] = video_track
        self.peers[peer_id]['audio'] = audio_track

    async def handle_signaling(self, peer_id, data):
        """
        Handle signaling messages (offer/answer) for WebRTC connection setup.

        Args:
            peer_id (str): ID of the peer sending the signaling message.
            data (dict): Signaling message data.
        """
        pc = self.peers.get(peer_id)
        if not pc:
            logging.warning(f"No PC found for {peer_id}")
            return

        t = data["type"]
        if t == "offer":
            offer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdpType"])
            peer_pubkey_bytes = data["pubKey"].encode("ascii")
            peer_rsapub = serialization.load_pem_public_key(peer_pubkey_bytes)

            # Encrypt the Fernet key with the peer's RSA public key
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

            # Create a Fernet key for this peer
            self.keys[peer_id] = fernet_key
            await pc.setRemoteDescription(answer_desc)


