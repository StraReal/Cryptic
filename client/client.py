from rooms import ChatClient
import asyncio

if __name__ == "__main__":
    client = ChatClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass
