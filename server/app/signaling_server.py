import asyncio
from aiohttp import web
import pathlib
from aiortc import RTCPeerConnection, RTCSessionDescription
import json

# rooms = { room_code: { 'peers': { username: { "addr": peer_addr, "pc": RTCPeerConnection } }, 'saved': bool } }
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
    if room and not room["saved"]:
        print(f"[SERVER] ROOM_TIMEOUT {room_code}")
        delete_room(room_code)

# ----------------------  HTTP ENDPOINTS  ----------------------

async def create_room(request: web.Request):
    params = request.rel_url.query
    room_code = params.get("room_code")
    username = params.get("username")
    peer_ip = params.get("peer_ip")
    peer_port = params.get("peer_port")

    if not room_code or not username or not peer_ip or not peer_port:
        return web.json_response({"error": "missing parameters"}, status=400)

    peer_addr = f"{peer_ip}:{peer_port}"

    if room_code in rooms:
        msg = f"ROOM_TAKEN {room_code} {peer_addr}"
        print(f"[SERVER] {msg}")
        return web.json_response({"error": msg}, status=409)

    rooms[room_code] = {"peers": {username: {"addr": peer_addr, "pc": None}}, "saved": False}
    msg = f"ROOM_CREATED {room_code} {peer_addr}"
    print(f"[SERVER] {msg}")

    # auto-remove after 1 hour
    asyncio.create_task(remove_room_after_timeout(room_code))

    return web.json_response({"status": msg})

async def join_room(request: web.Request):
    params = request.rel_url.query
    room_code = params.get("room_code")
    username = params.get("username")
    peer_ip = params.get("peer_ip")
    peer_port = params.get("peer_port")

    if not room_code or not username or not peer_ip or not peer_port:
        return web.json_response({"error": "missing parameters"}, status=400)

    peer_addr = f"{peer_ip}:{peer_port}"

    if room_code not in rooms:
        msg = f"ROOM_INEXISTENT {room_code} {peer_addr}"
        print(f"[SERVER] {msg}")
        return web.json_response({"error": msg}, status=404)

    room = rooms[room_code]
    room["peers"][username] = {"addr": peer_addr, "pc": None}
    msg = f"JOIN_ROOM {room_code} {peer_addr}"
    print(f"[SERVER] {msg}")

    # mark room as saved if at least 2 peers
    if len(room["peers"]) >= 2:
        room["saved"] = True

    # return list of peers
    return web.json_response({
        "status": msg,
        "peers": {u: info["addr"] for u, info in room["peers"].items()}
    })

async def list_rooms(request: web.Request):
    return web.json_response({
        code: {"peers": list(info["peers"].keys()), "saved": info["saved"]}
        for code, info in rooms.items()
    })

# ----------------------  WebRTC SIGNALLING  ----------------------

async def offer(request: web.Request):
    """
    Endpoint to receive SDP offer from client and return SDP answer.
    Expect JSON: { "room_code": str, "username": str, "sdp": str, "type": str }
    """
    data = await request.json()
    room_code = data.get("room_code")
    username = data.get("username")
    sdp = data.get("sdp")
    type_ = data.get("type")

    if not room_code or not username or not sdp or not type_:
        return web.json_response({"error": "missing parameters"}, status=400)

    if room_code not in rooms or username not in rooms[room_code]["peers"]:
        return web.json_response({"error": "room or user not found"}, status=404)

    pc = RTCPeerConnection()
    rooms[room_code]["peers"][username]["pc"] = pc

    # Set remote description (offer)
    offer_desc = RTCSessionDescription(sdp=sdp, type=type_)
    await pc.setRemoteDescription(offer_desc)

    # Create and set local description (answer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print(f"[SERVER] SDP answer created for {username} in room {room_code}")
    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

# ----------------------  SERVER SETUP  ----------------------

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/room/new", create_room)
app.router.add_get("/room/join", join_room)
app.router.add_get("/rooms", list_rooms)
app.router.add_post("/offer", offer)
app.router.add_static('/static/', path='static', name='static')

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)
