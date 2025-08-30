import asyncio
from aiohttp import web

# rooms = { room_code: { 'peers': { username: ws }, 'saved': bool } }
rooms = {}

def delete_room(room_code):
    del rooms[room_code]
    print(f"[SERVER] ROOM_DELETED {room_code}")

async def remove_room_after_timeout(room_code, timeout=3600):
    """Deletes a room after 'timeout' seconds if it's not saved."""
    await asyncio.sleep(timeout)
    room = rooms.get(room_code)
    if room:
        print(f"[SERVER] ROOM_TIMEOUT {room_code}")
        delete_room(room_code)

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
                print(f"[{peer_addr}] {data}")

                parts = data.split(" ")
                cmd = parts[0].upper()

                if cmd == "CREATE" and len(parts) >= 3:
                    room_code, username = parts[1], parts[2].replace(' ','_')
                    if room_code in rooms:
                        msg = f"ROOM_TAKEN {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')
                    else:
                        rooms[room_code] = {"peers": {username: ws}, "saved": False}
                        msg = f"ROOM_CREATED {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')
                        # auto-remove after 1h
                        asyncio.create_task(remove_room_after_timeout(room_code))

                elif cmd == "JOIN" and len(parts) >= 3:
                    room_code, username = parts[1], parts[2]
                    if room_code not in rooms:
                        msg = f"ROOM_INEXISTENT {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')
                    else:
                        room = rooms[room_code]
                        room["peers"][username] = ws
                        msg = f"JOIN_ROOM {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')

                        # if atleast 2 people are in it, mark the room as "saved": it's up for deletion in 1 hour
                        if len(room["peers"]) >= 2:
                            room["saved"] = True

                        # notify the peers
                        if len(room["peers"]) >= 2:
                            peers = list(room["peers"].items())
                            for i, (uname, sock) in enumerate(peers):
                                other_uname, other_sock = peers[1 - i]
                                other_ip, other_port = other_sock._req.transport.get_extra_info('peername')
                                msg = f"PEER {other_uname} {other_ip}:{other_port}"
                                await sock.send_str(msg)
                                print(f'[SERVER] {msg}')

                else:
                    await ws.send_str("ERROR invalid command")

    finally:
        # clean-up if the host disconnects
        print(f"[SERVER] Peer {peer_addr} disconnected")
        if room_code and username:
            room = rooms.get(room_code)
            if room:
                if username in room["peers"]:
                    del room["peers"][username]
                # if the room isn't "saved", delete it
                if not room["saved"] and not room["peers"]:
                    delete_room(room_code)

    return ws

app = web.Application()
app.router.add_get("/", websocket_handler)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)
