from user import Users
from asyncio import Lock

class Rooms:
    def __init__ (self, code, password, headuser: Users):
        self._room_code=code
        self._password=password
        self._owner=headuser
        self._clients=[]
        self._clients.append(headuser)
        self._count=0
        self._locked=False
        self._lock=Lock() ## mutex lock primitive for shared state during async functions

    def addclient(self, newuser: Users, provided_password: str) -> int:
        """
            This methods checks if the request to join the room can be fullfilled.
            This method ensures there are no user of the same name in the same room.
            Return types:
             1-> success
            -1-> Username not available 
            -2-> Same ip of an existing user
            -3-> Password not valid
            -4-> Room is locked so no new user is allowed to join the room
        """
        if self._locked==True: #If the room is locked return without adding the newclient to the room
            return -4
        if self._password!=provided_password:
            return -3
        for i in self._clients:
            if i.getname()==newuser.getname():
                return -1
            elif i.getipaddr()==newuser.getipaddr():
                return -2
        self._clients.append(newuser)
        return 1

    def lockroom(self, requesteduser: Users)->bool:
        """
            Locks the room so more users can join the room. It checks if the user is the owner of the room.
            Otherwise return False.
        """
        if self._owner.getipaddr()==requesteduser.getipaddr():
            self._locked=True
            return True
        return False

    def unlockroom(self, requesteduser)->bool:
        """
            Unlocks the room so more users can join the room. It checks if the user is the owner of the room.
            Otherwise return False.
        """
        if self._owner.getipaddr()==requesteduser.getipaddr():
            self._locked=False
            return True
        return False

    def matchpassword(self, password)->bool:
        """
            Compare the password equivalency.
        """
        return self._password==password

    def changepassword(self, requestuser:Users, old_password, new_password)-> bool:
        """
            This method ensures only the original owner can change the password for joining the room 
            when provided with the correct old password.
        """
        if self._owner.getipaddr()==requestuser.getipaddr() and self._password==old_password:
            self._password=new_password
            return True 
        return False
    
    def is_existing_user(self, requestuser: Users)-> bool:
        """
            This method checks if the coming request from an existing user or not.
            This method handles a different scenario compared to the checks in the addclient() method.
        """
        for val in self._clients:
            if val.getname()==requestuser.getname() and val.getipaddr()==requestuser.getipaddr():
                return True
        return False

    def dropclient(self, peerip:str):
        """
            Drop a specific user from the room identified by their ip address.
        """
        idx=-1
        for i, client  in enumerate(self._clients):
            if client.getipaddr()==peerip:
                idx=i
        del self._clients[idx]


    def getclientnos(self):
        return len(self._clients)

    def getotherclients(self, peerip:str):
        """
            Get all the client info except the your ownself
        """
        for i,val in enumerate(self._clients):
            if val.getipaddr()==peerip:
                return self._clients[0:i]+self._clients[i+1:]
