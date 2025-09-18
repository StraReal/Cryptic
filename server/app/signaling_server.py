import json
import logging
from aiohttp import web
import pathlib

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()

BASE_DIR = pathlib.Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"

# rooms: { room_code: { "peers": set(ws), "names": {ws: username}, "password": str,
#                        "pending_offer": dict, "pending_answer": dict } }
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
                        if room_code in rooms:
                            await ws.send_str(json.dumps({"type": "error",
                                                          "message": "Room already exists"}))
                            continue
                        rooms[room_code] = {
                            "peers": {ws},
                            "names": {ws: username},
                            "password": password,
                            "pending_offer": None,
                            "pending_answer": None
                        }
                        current_room = room_code
                        current_name = username
                        logging.info("Room %s created by %s", room_code, username)
                        await ws.send_str(json.dumps({"type": "joined", "room": room_code, "offerer": True }))
                    else:
                        room = rooms.get(room_code)
                        if not room:
                            await ws.send_str(json.dumps({"type": "error",
                                                          "message": "Room not found"}))
                            continue
                        if room["password"] != password:
                            await ws.send_str(json.dumps({"type": "error",
                                                          "message": "Incorrect password"}))
                            continue
                        room["peers"].add(ws)
                        room["names"][ws] = username
                        current_room = room_code
                        current_name = username
                        logging.info("%s joined room %s", username, room_code)
                        await ws.send_str(json.dumps({"type": "joined", "room": room_code, "offerer": False }))

                        # send pending offer if it exists
                        if room.get("pending_offer"):
                            await ws.send_str(json.dumps(room["pending_offer"]))

                        # send pending answer if it exists (rare, but just in case)
                        if room.get("pending_answer"):
                            await ws.send_str(json.dumps(room["pending_answer"]))

                elif t in ("offer", "answer", "ice", "bye"):
                    if current_room and current_room in rooms:
                        room = rooms[current_room]

                        # store pending offer/answer for late joiners
                        if t == "offer":
                            room["pending_offer"] = dict(data)
                        elif t == "answer":
                            room["pending_answer"] = dict(data)

                        for peer in list(room["peers"]):
                            if peer is not ws and not peer.closed:
                                payload = dict(data)
                                payload["from"] = current_name
                                payload["room"] = current_room
                                if t in ("offer", "answer"):
                                    logging.info("Relaying %s from %s to %s in room %s",
                                                 t, current_name,
                                                 room["names"].get(peer, "<unknown>"),
                                                 current_room)
                                await peer.send_str(json.dumps(payload))
                else:
                    logging.warning("Unknown message type: %s", t)

            elif msg.type == web.WSMsgType.ERROR:
                logging.error('ws connection closed with exception %s', ws.exception())

    finally:
        if current_room and current_room in rooms:
            room = rooms[current_room]
            room["peers"].discard(ws)
            room["names"].pop(ws, None)
            # clear pending offer/answer if room is empty
            if not room["peers"]:
                del rooms[current_room]
                logging.info("Room %s deleted (empty)", current_room)
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
