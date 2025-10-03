# Cryptic

Cryptic is a peer-to-peer (P2P) instant messaging application built with privacy as a core principle. Unlike mainstream chat apps that rely on central servers to handle messages, Cryptic enables direct communication between users.

---

## Project Overview

Cryptic is designed to be an actually private chatting platform. Messages are sent directly between peers, without passing through a central server. A lightweight signaling server is used only to facilitate the initial connection. This architecture allows users to communicate securely while minimizing potential points of surveillance or data collection.

Cryptic is open source and fully self-hostable, making it suitable for anyone who values privacy and wants full control over their communication infrastructure.

---

## Technical Details

- **Peer-to-peer messaging**: Once a connection is established, all messages travel directly between clients.  
- **webRTC with aioRTC**: Cryptic uses WebRTC to establish P2P connections, specifically the aioRTC library, which facilitates it.
- **Signaling Server**: The signaling server is only used to exchange connection information between peers. Messages never pass through it. You can use the provided public server or host your own.  

---

## Security & Modifications

- Cryptic mitigates the risks of modified clients, but it cannot enforce rules on modified servers.  
- Anyone can use a modified client or connect to a signaling server other than the publicly available one(s).  
- Full self-hosting is supported for users who want complete control over both client and server.  

---

## Getting Started

### Using the Client

1. Switch to the client folder:
```bash
cd client
```
2. Install the dependencies:
```bash
pip install -r requirements.txt
```
Since Tkinter is used, if you're running the code on Linux you're gonna need to install it separately from Python
3. Run the client:
```bash
python client.py
```
4. Select the signaling server you'll be using (use signalingserverdomain.download for a publicly hosted one).
5. Choose any display name and either create or join a room using a 6-character room code, just press enter for the password to not have one.

### Hosting a Signaling Server

Use the Dockerfile in the 'server' folder to build and run your own signaling server.

The server should be ready to facilitate P2P connections immediately.

Optionally, you can use the public signaling server at https://signalingserverdomain.download if you don’t want to host your own.

Links
Join our Discord server: https://discord.gg/tuX9hkvFC2

Public signaling server: https://signalingserverdomain.download


---

