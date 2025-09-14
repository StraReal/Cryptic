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

@web.middleware
async def log_status(request, handler):
    # chiama l'handler originale
    response = await handler(request)
    # stampa lo status di qualunque web.Response
    print(f"[SERVER] HTTP {request.method} {request.path} -> {response.status}")
    return response

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
    room_code=request.query['room-code']
    client_name=request.query['name']
    room_pass=request.query['pass']
    owneruser= Users(client_name, peerip)

    if room_code not in rooms.keys():
        rooms[room_code]=Rooms(room_code, room_pass, owneruser)
        return web.Response(status=200)
    else:
        return web.Response(body="Room Name not available in this server",status=406, content_type="text/plain")

async def join_room(request):
    """
        Method to check if there is an existing room with the given room code. If the room with the given code exists then returns 
        the ip and username of all the other users in the room.
    """
    peerip=request.remote
    room_code=request.query['room-code']
    client_name=request.query['name']
    room_pass=request.query['pass'] 
    newuser=Users(client_name, peerip)

    if room_code in rooms.keys():
        if rooms[room_code].is_existing_user(newuser): ## Check if the user is already a registered user. Useful when an alredy registered user want to retrieve ips of all other connected cliens.
            if rooms[room_code].getclientnos()<2:
                return web.Response(body="[Warn]:There are no other user in the room.", status= 425 , content_type="text/plain")
            return web.Response(body=json.dumps(rooms[room_code].getotherclients(peerip), default=userencoder, indent=2), status=200, content_type='application/json')

        match rooms[room_code].addclient(newuser, room_pass):
            case 1:
                if rooms[room_code].getclientnos()<2:
                    return web.Response(body="[Warn]:There are no other user in the room.", status= 425 , content_type="text/plain")
                return web.Response(body=json.dumps(rooms[room_code].getotherclients(peerip), default=userencoder, indent=2),status=200, content_type='application/json')
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

async def lockroom(request):
    """
        Locks the room so no more clients can connect to the room.
    """
    peerip=request.remote
    room_code=request.query['room-code']
    client_name=request.query['name']
    newuser=Users(client_name, peerip)

    if rooms[room_code].lockroom(newuser):
        return web.Response(status=200)
    else:
        return web.Response(status=406)

async def unlockroom(request):
    """
        Unlocks the room so no more clients can connect to the room.
    """
    peerip=request.remote
    room_code=request.query['room-code']
    client_name=request.query['name']
    newuser=Users(client_name, peerip)


    if rooms[room_code].unlockroom(newuser):
        return web.Response(status=200)
    else:
        return web.Response(status=406)

async def change_password(request):
    """
        Change password to enter a room. Only acceptable from the cretor of the room.
        If the previous password matches with the provided password only then changes the password for this room.
    """
    peerip=request.remote
    room_code=request.query['room-code']
    client_name=request.query['name']
    room_pass=request.query['pass'] 
    new_pass=request.query['new_pass']
    newuser=Users(client_name, peerip)

    if rooms[room_code].changepassword(newuser, room_pass, new_pass):
        return web.Response(body=new_pass,status=200, content_type='text/plain')
    return web.Response(status=406)

async def leave_room(request):
    """
        Removes the specific user(identified by their ip) from the room
    """
    peerip=request.remote
    room_code=request.query['room-code']
    
    rooms[room_code].dropclient(peerip)
    return web.Response(status=200)

if __name__ == "__main__":
    app = web.Application(middlewares=[log_status])
    app.router.add_get('/', index)   # Homepage → website.html
    app.router.add_static('/static/', path='static', name='static')
    app.router.add_get('/room/new', new_room)
    app.router.add_get('/room/join', join_room)
    app.router.add_get('/room/lock', lockroom)
    app.router.add_get('/room/unlock', unlockroom)
    app.router.add_get('/room/change/password', change_password)
    app.router.add_get('/room/leave', leave_room)
    web.run_app(app, host="0.0.0.0", port=5000)

