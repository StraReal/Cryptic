import asyncio
from aiohttp import web

rooms = {}  # { room_code: { username: ws } }

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    peer_ip, peer_port = request.transport.get_extra_info('peername')
    peer_addr = f"{peer_ip}:{peer_port}"

    username = None
    room_code = None

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = msg.data.strip()
                print(f"[SERVER] Received: {data} from {peer_addr}")

                parts = data.split(" ")
                cmd = parts[0].upper()

                if cmd == "CREATE" and len(parts) >= 3:
                    room_code, username = parts[1], parts[2]
                    if room_code in rooms:
                        await ws.send_str(f"ERROR Room {room_code} already exists")
                    else:
                        rooms[room_code] = {username: ws}
                        await ws.send_str(f"ROOM_CREATED {room_code}")
                        print(f"[SERVER] Room {room_code} created by {username}")

                elif cmd == "JOIN" and len(parts) >= 3:
                    room_code, username = parts[1], parts[2]
                    if room_code not in rooms:
                        await ws.send_str(f"ERROR Room {room_code} doesn't exist")
                        print(rooms)
                    else:
                        # add peer to room
                        rooms[room_code][username] = ws
                        await ws.send_str(f"JOINED {room_code}")
                        print(f"[SERVER] {username} è entrato in {room_code}")

                        # se ci sono almeno due peer → scambio info
                        if len(rooms[room_code]) >= 2:
                            peers = list(rooms[room_code].items())
                            for i, (uname, sock) in enumerate(peers):
                                other_uname, other_sock = peers[1 - i]
                                # prendi IP e porta dell'altro peer
                                other_ip, other_port = other_sock._req.transport.get_extra_info('peername')
                                await sock.send_str(f"PEER {other_uname} {other_ip}:{other_port}")

                else:
                    await ws.send_str("ERROR invalid command")

    finally:
        # clean-up if peer disconnects
        if room_code and username:
            if room_code in rooms and username in rooms[room_code]:
                del rooms[room_code][username]
                if not rooms[room_code]:
                    del rooms[room_code]
        print(f"[SERVER] Peer {peer_addr} disconnected")

    return ws

app = web.Application()
app.router.add_get("/", websocket_handler)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)
