import asyncio

from app.browser.audio import audio_capture
from app.browser.manager import browser_manager
from app.utils.logger import get_logger
from app.websocket.events import BrowserAudioEvent, BrowserFrameEvent
from app.websocket.manager import manager

logger = get_logger(__name__)

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
    logger.info(
        "screenshot_stream_started",
        status="started",
        room_code=room_code,
    )


def stop_screenshot_stream(room_code: str) -> None:
    """Stop sending screenshots for a room."""
    task = _screenshot_tasks.pop(room_code, None)
    if task:
        task.cancel()
        logger.info(
            "screenshot_stream_stopped",
            status="stopped",
            room_code=room_code,
        )


async def _screenshot_loop(room_code: str) -> None:
    """Continuously capture and broadcast screenshots using Playwright."""
    logger.info(
        "screenshot_loop_started",
        status="running",
        room_code=room_code,
    )
    frame_count = 0
    target_fps = 20
    frame_interval = 1.0 / target_fps

    try:
        while True:
            loop_start = asyncio.get_event_loop().time()

            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                logger.info(
                    "screenshot_loop_ended",
                    status="session_not_running",
                    room_code=room_code,
                )
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
                    logger.info(
                        "screenshot_frames_broadcast",
                        status="running",
                        room_code=room_code,
                        frame_count=frame_count,
                    )
            except Exception as exc:
                logger.exception(
                    "screenshot_loop_error",
                    status="error",
                    room_code=room_code,
                    error=str(exc),
                )

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
        logger.warning(
            "audio_stream_unavailable",
            status="already_in_use",
            room_code=room_code,
            active_room=_audio_room,
        )
        return

    if room_code in _audio_tasks:
        return

    _audio_room = room_code
    audio_capture.start()

    task = asyncio.create_task(_audio_loop(room_code))
    _audio_tasks[room_code] = task
    logger.info(
        "audio_stream_started",
        status="started",
        room_code=room_code,
    )


def stop_audio_stream(room_code: str) -> None:
    """Stop sending audio for a room."""
    global _audio_room

    task = _audio_tasks.pop(room_code, None)
    if task:
        task.cancel()

    if _audio_room == room_code:
        audio_capture.stop()
        _audio_room = None
        logger.info(
            "audio_stream_stopped",
            status="stopped",
            room_code=room_code,
        )


async def _audio_loop(room_code: str) -> None:
    """Continuously capture and broadcast audio chunks."""
    logger.info(
        "audio_loop_started",
        status="running",
        room_code=room_code,
    )
    chunk_count = 0

    try:
        async for chunk in audio_capture.stream_chunks(chunk_size=4096):
            session = browser_manager.get_session(room_code)
            if not session or not session.is_running:
                logger.info(
                    "audio_loop_ended",
                    status="session_not_running",
                    room_code=room_code,
                )
                break

            chunk_count += 1
            if chunk_count % 100 == 0:
                logger.info(
                    "audio_chunks_broadcast",
                    status="running",
                    room_code=room_code,
                    chunk_count=chunk_count,
                )

            audio_event = BrowserAudioEvent(audio=chunk)
            await manager.broadcast_to_room(
                room_code,
                audio_event.model_dump(mode="json"),
            )
    except asyncio.CancelledError:
        pass
