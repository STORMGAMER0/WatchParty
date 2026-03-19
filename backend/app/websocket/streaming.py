import asyncio

from app.browser.audio import audio_capture
from app.browser.manager import browser_manager
from app.websocket.events import BrowserAudioEvent, BrowserFrameEvent
from app.websocket.manager import manager

# Track screenshot streaming tasks per room
_screenshot_tasks: dict[str, asyncio.Task] = {}
# Track audio streaming tasks per room
_audio_tasks: dict[str, asyncio.Task] = {}
# Track which room is currently using audio (only one can use VB-Cable at a time)
_audio_room: str | None = None


def start_screenshot_stream(room_code: str) -> None:
    """Start sending screenshots to all clients in a room using Playwright."""
    if room_code in _screenshot_tasks:
        return

    task = asyncio.create_task(_screenshot_loop(room_code))
    _screenshot_tasks[room_code] = task
    print(f"[Screenshot] Started Playwright screenshot streaming for room {room_code}")


def stop_screenshot_stream(room_code: str) -> None:
    """Stop sending screenshots for a room."""
    task = _screenshot_tasks.pop(room_code, None)
    if task:
        task.cancel()
        print(f"[Screenshot] Stopped streaming for room {room_code}")


async def _screenshot_loop(room_code: str) -> None:
    """Continuously capture and broadcast screenshots using Playwright."""
    print(f"[Screenshot] Broadcast loop started for room {room_code}")
    frame_count = 0
    target_fps = 20
    frame_interval = 1.0 / target_fps

    try:
        while True:
            loop_start = asyncio.get_event_loop().time()

            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Screenshot] Session not running for room {room_code}")
                break

            try:
                frame = await session.screenshot()
                url = await session.get_current_url()

                frame_count += 1

                frame_event = BrowserFrameEvent(frame=frame, url=url)
                await manager.broadcast_to_room(
                    room_code,
                    frame_event.model_dump(mode="json"),
                )

                if frame_count % 100 == 0:
                    print(f"[Screenshot] Broadcast {frame_count} frames for room {room_code}")
            except Exception as exc:
                print(f"[Screenshot] Error: {exc}")

            elapsed = asyncio.get_event_loop().time() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                await asyncio.sleep(0.001)
    except asyncio.CancelledError:
        pass


def start_audio_stream(room_code: str) -> None:
    """Start sending audio to all clients in a room."""
    global _audio_room

    if _audio_room is not None:
        print(f"[Audio] Cannot start for {room_code} - audio already in use by {_audio_room}")
        return

    if room_code in _audio_tasks:
        return

    _audio_room = room_code
    audio_capture.start()

    task = asyncio.create_task(_audio_loop(room_code))
    _audio_tasks[room_code] = task
    print(f"[Audio] Started streaming for room {room_code}")


def stop_audio_stream(room_code: str) -> None:
    """Stop sending audio for a room."""
    global _audio_room

    task = _audio_tasks.pop(room_code, None)
    if task:
        task.cancel()

    if _audio_room == room_code:
        audio_capture.stop()
        _audio_room = None
        print(f"[Audio] Stopped streaming for room {room_code}")


async def _audio_loop(room_code: str) -> None:
    """Continuously capture and broadcast audio chunks."""
    print(f"[Audio] Loop started for room {room_code}")
    chunk_count = 0

    try:
        async for chunk in audio_capture.stream_chunks(chunk_size=4096):
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                print(f"[Audio] Session ended for room {room_code}")
                break

            chunk_count += 1
            if chunk_count % 100 == 0:
                print(f"[Audio] Sent {chunk_count} chunks for room {room_code}")

            audio_event = BrowserAudioEvent(audio=chunk)
            await manager.broadcast_to_room(
                room_code,
                audio_event.model_dump(mode="json"),
            )
    except asyncio.CancelledError:
        pass
