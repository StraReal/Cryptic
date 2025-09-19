import json
import logging
from aiohttp import web
import pathlib

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()

BASE_DIR = pathlib.Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"

# rooms:
# {
#   room_code: {
#       "peers": set(ws),
#       "names": {ws: username},
#       "host_ws": ws,
#       "host_user": username,
#       "password": str
#   }
# }
rooms = {}


@routes.get('/ws')
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    current_room = None
    current_name = None

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception as e:
                    logging.warning("Invalid JSON: %s", e)
                    continue

                t = data.get("type")

                if t == "join":
                    room_code = data.get("room")
                    username = data.get("from")
                    password = hash(data.get("password", ""))
                    create = bool(data.get("create", False))

                    if create:
                        # ---- CREATE ROOM ----
                        if room_code in rooms:
                            await ws.send_str(json.dumps({
                                "type": "error",
                                "message": "Room already exists"
                            }))
                            continue
                        rooms[room_code] = {
                            "peers": {ws},
                            "names": {ws: username},
                            "host_ws": ws,
                            "host_user": username,
                            "password": password
                        }
                        current_room = room_code
                        current_name = username
                        logging.info("Room %s created by %s", room_code, username)
                        # confirm to the host that room is created
                        await ws.send_str(json.dumps({
                            "type": "created",
                            "room": room_code
                        }))

                    else:
                        # ---- JOIN ROOM ----
                        room = rooms.get(room_code)
                        if not room:
                            await ws.send_str(json.dumps({
                                "type": "error",
                                "message": "Room not found"
                            }))
                            continue
                        if room["password"] != password:
                            await ws.send_str(json.dumps({
                                "type": "error",
                                "message": "Incorrect password"
                            }))
                            continue

                        room["peers"].add(ws)
                        room["names"][ws] = username
                        current_room = room_code
                        current_name = username
                        host_user = room.get("host_user")
                        logging.info("%s joined room %s", username, room_code)

                        # tell the joining user they joined successfully
                        await ws.send_str(json.dumps({
                            "type": "joined",
                            "room": room_code,
                            "user": host_user
                        }))

                        # tell the host that someone joined, also an offer request
                        host_ws = room.get("host_ws")
                        if host_ws and not host_ws.closed:
                            await host_ws.send_str(json.dumps({
                                "type": "gotjoined",
                                "room": room_code,
                                "user": username
                            }))

                elif t in ("offer", "answer", "ice", "bye"):
                    if current_room and current_room in rooms:
                        room = rooms[current_room]
                        # if message has a "to", relay only to that peer
                        target_name = data.get("to")
                        if target_name:
                            target_ws = None
                            for peer_ws, name in room["names"].items():
                                if name == target_name:
                                    target_ws = peer_ws
                                    break
                            if target_ws and not target_ws.closed:
                                payload = dict(data)
                                payload["from"] = current_name
                                payload["room"] = current_room
                                logging.info("Relaying %s from %s to %s in room %s",
                                             t, current_name, target_name, current_room)
                                await target_ws.send_str(json.dumps(payload))
                        else:
                            # otherwise send only to the host
                            host_ws = room.get("host_ws")
                            if host_ws and host_ws is not ws and not host_ws.closed:
                                payload = dict(data)
                                payload["from"] = current_name
                                payload["room"] = current_room
                                logging.info("Relaying %s from %s to host in room %s",
                                             t, current_name, current_room)
                                await host_ws.send_str(json.dumps(payload))
                else:
                    logging.warning("Unknown message type: %s", t)

            elif msg.type == web.WSMsgType.ERROR:
                logging.error('ws connection closed with exception %s', ws.exception())

    finally:
        if current_room and current_room in rooms:
            room = rooms[current_room]
            room["peers"].discard(ws)
            room["names"].pop(ws, None)
            # if host disconnects or room empty -> delete room
            if ws is room.get("host_ws") or not room["peers"]:
                del rooms[current_room]
                logging.info("Room %s deleted (host left or empty)", current_room)
            else:
                logging.info("%s left room %s", current_name, current_room)

    return ws


async def index(request: web.Request):
    return web.FileResponse(INDEX_FILE)


app = web.Application()
app.add_routes(routes)
app.router.add_static('/static/', path='static', name='static')
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)

if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=5000)
