from app.websocket.events import (
    EventType,
    VoiceAnswerEvent,
    VoiceIceCandidateEvent,
    VoiceJoinEvent,
    VoiceLeaveEvent,
    VoiceOfferEvent,
)
from app.websocket.manager import Connection, manager

from .common import send_error


async def handle_voice_event(connection: Connection, data: dict) -> None:
    """Handle WebRTC signaling messages forwarded over the websocket."""
    event_type = data.get("event")

    if event_type == EventType.VOICE_JOIN:
        voice_join_event = VoiceJoinEvent(
            user_id=connection.user_id,
            username=connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code,
            voice_join_event.model_dump(mode="json"),
        )
    elif event_type == EventType.VOICE_LEAVE:
        voice_leave_event = VoiceLeaveEvent(
            user_id=connection.user_id,
            username=connection.username,
        )
        await manager.broadcast_to_room(
            connection.room_code,
            voice_leave_event.model_dump(mode="json"),
        )
    elif event_type == EventType.VOICE_OFFER:
        await _forward_voice_offer(connection, data)
    elif event_type == EventType.VOICE_ANSWER:
        await _forward_voice_answer(connection, data)
    elif event_type == EventType.VOICE_ICE_CANDIDATE:
        await _forward_voice_ice_candidate(connection, data)


async def _forward_voice_offer(connection: Connection, data: dict) -> None:
    target_user_id = data.get("to_user_id")
    sdp = data.get("sdp")

    if not target_user_id or not sdp:
        await send_error(connection, "Missing to_user_id or sdp in voice_offer")
        return

    target_connection = manager.get_connection_by_user_id(
        connection.room_code,
        target_user_id,
    )
    if not target_connection:
        await send_error(connection, "Target user not found in room")
        return

    voice_offer_event = VoiceOfferEvent(
        from_user_id=connection.user_id,
        to_user_id=target_user_id,
        sdp=sdp,
    )
    await manager.send_personal(
        target_connection,
        voice_offer_event.model_dump(mode="json"),
    )


async def _forward_voice_answer(connection: Connection, data: dict) -> None:
    target_user_id = data.get("to_user_id")
    sdp = data.get("sdp")

    if not target_user_id or not sdp:
        await send_error(connection, "Missing to_user_id or sdp in voice_answer")
        return

    target_connection = manager.get_connection_by_user_id(
        connection.room_code,
        target_user_id,
    )
    if not target_connection:
        await send_error(connection, "Target user not found in room")
        return

    voice_answer_event = VoiceAnswerEvent(
        from_user_id=connection.user_id,
        to_user_id=target_user_id,
        sdp=sdp,
    )
    await manager.send_personal(
        target_connection,
        voice_answer_event.model_dump(mode="json"),
    )


async def _forward_voice_ice_candidate(connection: Connection, data: dict) -> None:
    target_user_id = data.get("to_user_id")
    candidate = data.get("candidate")

    if not target_user_id:
        await send_error(connection, "Missing to_user_id in voice_ice_candidate")
        return

    target_connection = manager.get_connection_by_user_id(
        connection.room_code,
        target_user_id,
    )
    if not target_connection:
        return

    voice_ice_event = VoiceIceCandidateEvent(
        from_user_id=connection.user_id,
        to_user_id=target_user_id,
        candidate=candidate or "",
    )
    await manager.send_personal(
        target_connection,
        voice_ice_event.model_dump(mode="json"),
    )
