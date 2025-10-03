from aiortc import MediaStreamTrack
from av import VideoFrame, AudioFrame
import cv2
import numpy as np
import sounddevice as sd



class VideoChannelTrack(MediaStreamTrack):
    kind = "video"
    def __init__(self, width=640, height=480):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.width = width
        self.height = height
        self.enabled = True

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to read camera")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        if not self.enabled:
            # Send black frame if disabled
            video_frame = VideoFrame(width=self.width, height=self.height)
        return video_frame

    # Turn camera off/on
    def turn_off(self):
        if hasattr(self, 'video_track'):
            self.enabled = False

    def turn_on(self):
        if hasattr(self, 'video_track'):
            self.enabled = True

class AudioChannelTrack(MediaStreamTrack):
    kind = "audio"
    def __init__(self, samplerate=48000, channels=1, blocksize=1024):
        super().__init__()
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.enabled = True

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        data = sd.rec(self.blocksize, samplerate=self.samplerate, channels=self.channels, dtype='int16')
        sd.wait()
        frame = AudioFrame.from_ndarray(data, layout="mono")
        frame.pts = pts
        frame.time_base = time_base
        if not self.enabled:
            frame.planes[0].update(np.zeros_like(frame.planes[0]))
        return frame


    # Mute/unmute yourself
    def mute(self):
        if hasattr(self, 'audio_track'):
            self.enabled = False

    def unmute(self):
        if hasattr(self, 'audio_track'):
            self.enabled = True

