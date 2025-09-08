# Cryptic

Cryptic is a peer-to-peer (P2P) instant messaging application built with privacy as a core principle. Unlike mainstream chat apps that rely on central servers to handle messages, Cryptic enables direct communication between users.

---

## Project Overview

Cryptic is designed to be an actually private chatting platform. Messages are sent directly between peers, without passing through a central server. A lightweight signaling server is used only to facilitate the initial connection. This architecture allows users to communicate securely while minimizing potential points of surveillance or data collection.

Cryptic is open source and fully self-hostable, making it suitable for anyone who values privacy and wants full control over their communication infrastructure.

---

## Technical Details

- **Peer-to-peer messaging**: Once a connection is established, all messages travel directly between clients.  
- **WebRTC and UDP Hole Punching**: Cryptic uses WebRTC to establish P2P connections even when users are behind NATs. UDP hole punching allows peers to open direct communication channels through firewalls and NAT routers.  
- **Signaling Server**: The signaling server is only used to exchange connection information between peers. Messages never pass through it. You can use the provided public server or host your own.  

---

## Security & Modifications

- Cryptic mitigates the risks of modified clients, but it cannot enforce rules on modified servers.  
- Anyone can use a modified client or connect to a signaling server other than the publicly available one(s).  
- Full self-hosting is supported for users who want complete control over both client and server.  

---

## Getting Started

### Using the Client

1. Install the dependencies:

```bash
pip install -r client/requirements.txt
