class Users:
    """
        Users class represents an user connected to a particular room.
        Users are identifiable with their unique public ip and the username in the room.
    """
    def __init__(self, username, ipaddr):
        self._username=username
        self._ipaddr=ipaddr

    def getname(self):
        return self._username

    def getipaddr(self):
        return self._ipaddr

    def isnameequal(self, name):
        return self._username==name

    def toJSON(self):
        return {
                "username": self._username,
                "ip": self._ipaddr
        }

def userencoder(obj):
    """
        Default encoder for the Class Users class
    """
    if isinstance(obj, Users):
        return {
            "username": obj.getname(), 
            "ip": obj.getipaddr()
        }
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

