import asyncio
from aiohttp import web
import pathlib
import json

# rooms = { room_code: { 'peers': { username: { "addr": peer_addr, "offer": None, "answer": None } }, 'saved': bool } }
rooms = {}

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
        del rooms[room_code]

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
        return web.json_response({"error": f"ROOM_TAKEN {room_code}"}, status=409)

    rooms[room_code] = {
        "peers": {username: {"addr": peer_addr, "offer": None, "answer": None}},
        "saved": False
    }
    print(f"[SERVER] ROOM_CREATED {room_code} by {username}")
    asyncio.create_task(remove_room_after_timeout(room_code))
    return web.json_response({"status": f"ROOM_CREATED {room_code}"})

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
        return web.json_response({"error": "ROOM_INEXISTENT"}, status=404)

    room = rooms[room_code]
    room["peers"][username] = {"addr": peer_addr, "offer": None, "answer": None}
    if len(room["peers"]) >= 2:
        room["saved"] = True

    print(f"[SERVER] JOIN_ROOM {room_code} by {username}")
    return web.json_response({
        "status": f"JOIN_ROOM {room_code}",
        "peers": {u: info["addr"] for u, info in room["peers"].items()}
    })

async def list_rooms(request: web.Request):
    return web.json_response({
        code: {"peers": list(info["peers"].keys()), "saved": info["saved"]}
        for code, info in rooms.items()
    })

# ----------------------  P2P SIGNALING ----------------------

async def offer(request: web.Request):
    """
    Receives SDP offer from a client and forwards it to the other peer.
    Expects JSON: { "room_code": str, "username": str, "sdp": str, "type": str }
    Returns JSON: { "sdp": answer_sdp, "type": answer_type }
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

    room = rooms[room_code]
    # Find the other peer
    other_peers = [u for u in room["peers"] if u != username]
    if not other_peers:
        return web.json_response({"error": "no other peer yet"}, status=409)

    other_username = other_peers[0]

    # Store the offer from the sender
    room["peers"][username]["offer"] = {"sdp": sdp, "type": type_}

    # Wait until the other peer has submitted their answer
    # (in practice, in a real app you would push this async via websocket or long-polling)
    for _ in range(50):  # wait max ~5 seconds
        answer = room["peers"][other_username].get("answer")
        if answer:
            # clean up stored offer/answer
            room["peers"][username]["offer"] = None
            room["peers"][other_username]["answer"] = None
            return web.json_response(answer)
        await asyncio.sleep(0.1)

    return web.json_response({"error": "timeout waiting for answer"}, status=504)

async def answer(request: web.Request):
    """
    Receives SDP answer from the second peer.
    Expects JSON: { "room_code": str, "username": str, "sdp": str, "type": str }
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

    room = rooms[room_code]
    room["peers"][username]["answer"] = {"sdp": sdp, "type": type_}
    return web.json_response({"status": "answer received"})

# ----------------------  SERVER SETUP ----------------------

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/room/new", create_room)
app.router.add_get("/room/join", join_room)
app.router.add_get("/rooms", list_rooms)
app.router.add_post("/offer", offer)
app.router.add_post("/answer", answer)
app.router.add_static('/static/', path='static', name='static')

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=5000)
