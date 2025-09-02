This project allows people to directly connect without exchanging messages by making them pass through a centralized server using UDP Hole Punching, establishing a direct P2P connection.

To do this you need a signaling server (for which the code is already in the repo); it doesn't receive the messages sent by the users but just helps establish a connection (look into UDP Hole Punching to understand what it's doing)

The users can then connect by exchanging a 6-char room code, which can either need a password or not.

I'll probably make a signaling server available to anyone to use, but until then, and even then for your extra safety, you'll need to have a signaling server of your own, which can then be used by as many people as you want, all they'll need is its URL.

To be able to chat, run the client.py script in the client folder and enter the URL of the signaling server you'll be using.
Then you can create a room or join one. 

I was thinking of creating accounts, but that goes against the idea of a decentralized chatting service.

Check this website out, which you can also use as signaling server: https://signalingserverdomain.download

There isn't a team behind this, so I have to rely on people to keep this project going, but I would gladly form a team if anyone was up for it. My discord is in my account.

Each room has a life-span of 1 hour. It works this way because checking if a room is still open would mean knowing how long two people have been chatting for, and rooms can't be up forever.
