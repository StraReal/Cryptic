import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription

def read_multiline_json(prompt):
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return json.loads("".join(lines))  # join without newlines

async def run_offer():
    pc = RTCPeerConnection()
    channel = pc.createDataChannel("chat")

    @channel.on("message")
    def on_message(msg):
        print("Peer:", msg)

    @pc.on("iceconnectionstatechange")
    def on_ice_state():
        print("ICE state:", pc.iceConnectionState)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # print JSON in a single line
    offer_json = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    print("\nSend this offer to the other peer:")
    print(json.dumps(offer_json, separators=(',', ':')))  # single-line JSON

    # read answer
    answer_json = read_multiline_json("\nPaste the answer JSON here (finish with empty line):")
    answer = RTCSessionDescription(sdp=answer_json["sdp"], type=answer_json["type"])
    await pc.setRemoteDescription(answer)

    await asyncio.Future()

async def run_answer():
    pc = RTCPeerConnection()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(msg):
            print("Peer:", msg)

    @pc.on("iceconnectionstatechange")
    def on_ice_state():
        print("ICE state:", pc.iceConnectionState)

    # read offer
    offer_json = read_multiline_json("Paste the offer JSON here (finish with empty line):")
    offer = RTCSessionDescription(sdp=offer_json["sdp"], type=offer_json["type"])
    await pc.setRemoteDescription(offer)

    # create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # print JSON in a single line
    answer_json = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    print("\nSend this answer back to the offerer:")
    print(json.dumps(answer_json, separators=(',', ':')))  # single-line JSON

    await asyncio.Future()

async def main():
    choice = input("Enter 0 to create an offer, 1 to answer an offer: ")
    if choice == "0":
        await run_offer()
    else:
        await run_answer()

asyncio.run(main())
