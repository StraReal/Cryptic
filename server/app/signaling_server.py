import asyncio
from aiohttp import web
import pathlib

# rooms = { room_code: { 'peers': { username: peer_addr }, 'saved': bool } }
rooms = {}

def delete_room(room_code: str):
    """Remove a room from memory."""
    del rooms[room_code]
    print(f"[SERVER] ROOM_DELETED {room_code}")

BASE_DIR = pathlib.Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"

async def index(request: web.Request):
    return web.FileResponse(INDEX_FILE)

async def remove_room_after_timeout(room_code: str, timeout: int = 3600):
    """Deletes a room after 'timeout' seconds if it is not marked as saved."""
    await asyncio.sleep(timeout)
    room = rooms.get(room_code)
    if room:
        print(f"[SERVER] ROOM_TIMEOUT {room_code}")
        delete_room(room_code)

# ----------------------  HTTP ENDPOINTS  ----------------------

async def create_room(request: web.Request):
    """
    Create a new room.
    Parameters: room_code, username, peer_ip (via GET or POST).
    """
    params = request.rel_url.query
    room_code = params.get("room_code")
    username = params.get("username")
    peer_ip   = params.get("peer_ip")

    if not room_code or not username or not peer_ip:
        return web.json_response({"error": "missing parameters"}, status=400)

    peer_port = request.transport.get_extra_info('peername')[1]
    peer_addr = f"{peer_ip}:{peer_port}"

    if room_code in rooms:
        msg = f"ROOM_TAKEN {room_code} {peer_addr}"
        print(f"[SERVER] {msg}")
        return web.json_response({"error": msg}, status=409)

    rooms[room_code] = {"peers": {username: peer_addr}, "saved": False}
    msg = f"ROOM_CREATED {room_code} {peer_addr}"
    print(f"[SERVER] {msg}")

    # auto-remove after 1 hour
    asyncio.create_task(remove_room_after_timeout(room_code))

    return web.json_response({"status": msg})

async def join_room(request: web.Request):
    """
    Join an existing room.
    Parameters: room_code, username, peer_ip
    """
    params = request.rel_url.query
    room_code = params.get("room_code")
    username = params.get("username")
    peer_ip   = params.get("peer_ip")

    if not room_code or not username or not peer_ip:
        return web.json_response({"error": "missing parameters"}, status=400)

    peer_port = request.transport.get_extra_info('peername')[1]
    peer_addr = f"{peer_ip}:{peer_port}"

    if room_code not in rooms:
        msg = f"ROOM_INEXISTENT {room_code} {peer_addr}"
        print(f"[SERVER] {msg}")
        return web.json_response({"error": msg}, status=404)

    room = rooms[room_code]
    room["peers"][username] = peer_addr
    msg = f"JOIN_ROOM {room_code} {peer_addr}"
    print(f"[SERVER] {msg}")

    # if there are at least 2 peers → mark room as "saved"
    if len(room["peers"]) >= 2:
        room["saved"] = True

    # return list of peers (username → address) so the client knows who is inside
    return web.json_response({
        "status": msg,
        "peers": room["peers"]
    })

async def list_rooms(request: web.Request):
    """Return a list of active rooms (for debugging/monitoring)."""
    return web.json_response({
        code: {"peers": list(info["peers"].keys()), "saved": info["saved"]}
        for code, info in rooms.items()
    })

# ----------------------  SERVER SETUP  ----------------------

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/room/new", create_room)
app.router.add_get("/room/join", join_room)
app.router.add_get("/rooms", list_rooms)  # debug/monitoring
app.router.add_static('/static/', path='static', name='static')

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)
