import asyncio
from aiohttp import web

rooms = {}  # { room_code: { username: ws } }

async def remove_room_after_timeout(room_code, timeout=3600):
    """Deletes a room after 'timeout' seconds."""
    await asyncio.sleep(timeout)
    if room_code in rooms:
        print(f"[SERVER] Room {room_code} expired after {timeout} seconds")
        del rooms[room_code]

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
                    room_code, username = parts[1], parts[2]
                    if room_code in rooms:
                        msg = f"ROOM_TAKEN {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')
                    else:
                        rooms[room_code] = {username: ws}
                        msg = f"ROOM_CREATED {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')


                elif cmd == "JOIN" and len(parts) >= 3:
                    room_code, username = parts[1], parts[2]
                    if room_code not in rooms:
                        msg = f"ROOM_INEXISTENT {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')
                    else:
                        rooms[room_code][username] = ws
                        msg = f"JOIN_ROOM {room_code} {peer_addr}"
                        await ws.send_str(msg)
                        print(f'[SERVER] {msg}')

                        # if there's atleast two peers connected
                        if len(rooms[room_code]) >= 2:
                            peers = list(rooms[room_code].items())
                            for i, (uname, sock) in enumerate(peers):
                                other_uname, other_sock = peers[1 - i]
                                # get IP and port of other peer
                                other_ip, other_port = other_sock._req.transport.get_extra_info('peername')
                                msg = f"PEER {other_uname} {other_ip}:{other_port}"
                                await sock.send_str(msg)
                                print(f'[SERVER] {msg}')

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
