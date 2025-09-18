import asyncio
import json
import logging
import os
import sys
from aiortc import RTCPeerConnection, RTCSessionDescription
import websockets

logging.basicConfig(level=logging.INFO)

CONFIG_FILE = "config.json"

def to_websocket_url(url):
    """
    Convert any http(s) URL to a ws(s) URL and ensure it ends with '/ws'.
    """
    scheme, rest = url.split("://", 1)
    ws_scheme = "wss" if scheme == "https" else "ws"
    # Remove trailing slashes and always append '/ws'
    return f"{ws_scheme}://{rest.rstrip('/')}/ws"

class ChatClient:
    def __init__(self):
        self.config = {}
        self.name = None
        self.room = None
        self.password = ""
        self.create = False
        self.load_config()
        self.pc = RTCPeerConnection()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

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
                break
            elif choice == "1":
                self.create = False
                self.room = input("Enter the 6-character room code to join:\n").strip().upper()
                if len(self.room) != 6:
                    print("Room code must be exactly 6 characters.")
                    continue
                self.password = input("Enter password:\n").strip()
                break

        await self.ws.send(json.dumps({
            "type": "join",
            "room": self.room,
            "from": self.name,
            "password": self.password,
            "create": self.create
        }))

        # Wait for the server's joined/error message
        async for raw in self.ws:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if data.get("type") == "error":
                print("Server error:", data.get("message"))
                await self.ws.close()
                return None
            elif data.get("type") == "joined":
                print(f"Joined room {data.get('room')}")
                return data  #pass the full message back to run()

    async def async_input_loop(self, channel):
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, sys.stdin.readline)
            if not msg:
                break
            msg = msg.strip()
            if msg.lower() in ("exit", "quit"):
                await self.ws.send(json.dumps({"type": "bye", "from": self.name}))
                await self.ws.close()
                await self.pc.close()
                break
            channel.send(f"[{self.name}] {msg}")

    async def run(self):
        server_url = self.get_server_info()
        await self.connect_server(server_url)

        # Join the room and get the server's joined data
        joined_data = await self.join_room()
        print(joined_data)
        if not joined_data:
            return

        # handle local data channel
        channel = self.pc.createDataChannel("chat")

        @channel.on("open")
        def on_open():
            logging.info("DataChannel open — start typing messages")
            asyncio.create_task(self.async_input_loop(channel))
            channel.send('Hi peer!')

        @self.pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(msg):
                print(msg)

        @self.pc.on("iceconnectionstatechange")
        def on_ice_state():
            print("ICE state:", self.pc.iceConnectionState)

        # If we are the offerer, create and send the offer immediately
        if joined_data.get("offerer"):
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            await self.ws.send(json.dumps({
                "type": "offer",
                "room": self.room,
                "from": self.name,
                "sdp": self.pc.localDescription.sdp,
                "sdpType": self.pc.localDescription.type
            }))

        # Main message loop
        async for raw in self.ws:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            t = data.get("type")

            # handle incoming offer from another peer
            if t == "offer" and data.get("from") != self.name and data.get("room") == self.room:
                offer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdpType"])
                await self.pc.setRemoteDescription(offer_desc)
                answer = await self.pc.createAnswer()
                await self.pc.setLocalDescription(answer)
                await self.ws.send(json.dumps({
                    "type": "answer",
                    "room": self.room,
                    "from": self.name,
                    "sdp": self.pc.localDescription.sdp,
                    "sdpType": self.pc.localDescription.type
                }))

            # handle incoming answer for our offer
            elif t == "answer" and data.get("from") != self.name and data.get("room") == self.room:
                answer_desc = RTCSessionDescription(sdp=data["sdp"], type=data["sdpType"])
                await self.pc.setRemoteDescription(answer_desc)

            # handle BYE
            elif t == "bye":
                logging.info("Peer said BYE — exiting")
                break

        await self.pc.close()


if __name__ == "__main__":
    try:
        asyncio.run(ChatClient().run())
    except KeyboardInterrupt:
        pass
