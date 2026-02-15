"""
AudioCapture - Captures audio from Voicemeeter using FFmpeg.

Streams audio chunks that can be sent to clients via WebSocket.
"""

import asyncio
import base64
import subprocess
from typing import AsyncGenerator, Optional


class AudioCapture:
    """
    Captures audio from Voicemeeter Out B1 using FFmpeg.

    Audio is captured as MP3 chunks for efficient
    streaming to web clients.
    """

    # VB-Cable device name as shown by FFmpeg
    DEVICE_NAME = "Voicemeeter Out B1 (VB-Audio Voicemeeter VAIO)"

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running and self._process is not None

    def start(self) -> None:
        """Start capturing audio from Voicemeeter."""
        if self._is_running:
            return

        # FFmpeg command to capture from VB-Cable and output MP3 chunks
        # Using MP3 for broad browser compatibility
        cmd = [
            "ffmpeg",
            "-f", "dshow",                          # DirectShow input (Windows)
            "-i", f"audio={self.DEVICE_NAME}",      # Voicemeeter as input
            "-ac", "2",                             # Stereo
            "-ar", "44100",                         # 44.1kHz sample rate
            "-b:a", "128k",                         # 128kbps bitrate
            "-f", "mp3",                            # MP3 output format
            "-fflags", "+nobuffer",                 # Reduce latency
            "-flags", "+low_delay",                 # Low delay mode
            "-flush_packets", "1",                  # Flush packets immediately
            "pipe:1"                                # Output to stdout
        ]

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Suppress FFmpeg logs
            bufsize=0  # Unbuffered
        )
        self._is_running = True
        print(f"[AudioCapture] Started capturing from {self.DEVICE_NAME}")

    def stop(self) -> None:
        """Stop capturing audio."""
        self._is_running = False

        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        print("[AudioCapture] Stopped")

    async def read_chunk(self, chunk_size: int = 4096) -> Optional[str]:
        """
        Read a chunk of audio data.

        Returns:
            Base64-encoded audio chunk, or None if not running
        """
        if not self._process or not self._process.stdout:
            return None

        loop = asyncio.get_event_loop()

        try:
            # Read in a thread to avoid blocking
            chunk = await loop.run_in_executor(
                None,
                self._process.stdout.read,
                chunk_size
            )

            if chunk:
                return base64.b64encode(chunk).decode("utf-8")
            return None

        except Exception as e:
            print(f"[AudioCapture] Error reading chunk: {e}")
            return None

    async def stream_chunks(self, chunk_size: int = 4096) -> AsyncGenerator[str, None]:
        """
        Async generator that yields audio chunks.

        Yields:
            Base64-encoded audio chunks
        """
        while self._is_running:
            chunk = await self.read_chunk(chunk_size)
            if chunk:
                yield chunk
            else:
                # Small delay if no data available
                await asyncio.sleep(0.01)


# Singleton instance for the application
audio_capture = AudioCapture()
