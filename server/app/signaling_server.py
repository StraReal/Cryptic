import asyncio
import copy
from aiohttp import web
import pathlib
from user import Users
from user import userencoder
from rooms import Rooms
from typing import Dict
import json

# rooms is a hashtable keeping track of all the room ids and the client's that are connected to this room
# rooms = { room_code: {Rooms} }
rooms: Dict[str, Rooms]={}

def delete_room(room_code:str):
    del rooms[room_code]
    print(f"[SERVER] ROOM_DELETED {room_code}")

BASE_DIR = pathlib.Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"

async def index(_):
    return web.FileResponse(INDEX_FILE)

async def remove_room_after_timeout(room_code, timeout=3600):
    """Deletes a room after 'timeout' seconds if it's not saved."""
    await asyncio.sleep(timeout)
    room = rooms.get(room_code)
    if room:
        print(f"[SERVER] ROOM_TIMEOUT {room_code}")
        delete_room(room_code)


async def new_room(request):
    """
        Method to create a new room with the given code if that code is not already taken.
        If a room already exists with the same code then return 'Not Allowed' for the request.
    """
    peerip=request.remote
    room_name=request.query['room-name']
    client_name=request.query['name']
    room_pass=request.query['pass']
    owneruser= Users(client_name, peerip)

    if room_name not in rooms.keys():
        rooms[room_name]=Rooms(room_name, room_pass, owneruser)
        return web.Response(status=200)
    else:
        return web.Response(body="Room Name not available in this server",status=406, content_type="text/plain")

async def join_room(request):
    """
        Method to check if there is an existing room with the given room code. If the room with the given code exists then returns 
        the ip and username of all the other users in the room.
    """
    peerip=request.remote
    room_name=request.query['room-name']
    client_name=request.query['name']
    room_pass=request.query['pass'] 
    newuser=Users(client_name, peerip)

    if room_name in rooms.keys():
        existing_users=copy.deepcopy(rooms[room_name]) ## take the list of other existing users in the same room
        match rooms[room_name].addclient(newuser, room_pass):
            case 1: 
                return web.Response(body=json.dumps(existing_users, default=userencoder, indent=2),status=200, content_type='application/json')
            case -1:
                return web.Response(body="[Error]:Username already taken", status=409, content_type='text/plain')
            case -2:
                return web.Response(body="[Error]:Same ip as another user", status=409, content_type='text/plain')
            case -3:
                return web.Response(body="[Error]:Password not valid", status=403, content_type='text/plain')
            case -4:
                return web.Response(body="[Error]:No longer accepting new users in the room", status=406, content_type='text/plain')
        return web.Response(status=500)
    else:
        return web.Response(status=404)

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/', index)   # Homepage → website.html
    app.router.add_static('/static/', path='static', name='static')
    app.router.add_get('/room/new', new_room)
    app.router.add_get('/room/join', join_room)
    web.run_app(app, host="0.0.0.0", port=5000)

