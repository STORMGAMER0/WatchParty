import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Participant,
  Room,
  RoomEvent,
  Track,
  type RemoteParticipant,
  type RemoteTrack,
} from 'livekit-client';

import { api } from '../services/api';

export interface VoicePeer {
  userId: string;
  username: string;
  isSpeaking: boolean;
  isMuted: boolean;
}

interface VoiceTokenResponse {
  token: string;
  url: string;
  room_name: string;
}

interface UseVoiceChatProps {
  roomCode: string;
  onError?: (message: string) => void;
}

export function useVoiceChat({ roomCode, onError }: UseVoiceChatProps) {
  const roomRef = useRef<Room | null>(null);
  const pendingRoomRef = useRef<Room | null>(null);
  const audioElementsRef = useRef<Map<string, HTMLMediaElement>>(new Map());
  const syncTimeoutsRef = useRef<number[]>([]);
  const isJoiningRef = useRef(false);
  const joinAttemptRef = useRef(0);

  const [isVoiceConnecting, setIsVoiceConnecting] = useState(false);
  const [isInVoice, setIsInVoice] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [localIsSpeaking, setLocalIsSpeaking] = useState(false);
  const [peers, setPeers] = useState<VoicePeer[]>([]);

  const removeParticipantAudio = useCallback((participantIdentity: string) => {
    const audioElement = audioElementsRef.current.get(participantIdentity);
    if (!audioElement) {
      return;
    }

    audioElement.pause();
    audioElement.srcObject = null;
    audioElement.remove();
    audioElementsRef.current.delete(participantIdentity);
  }, []);

  const cleanupAudioElements = useCallback(() => {
    audioElementsRef.current.forEach((audioElement) => {
      audioElement.pause();
      audioElement.srcObject = null;
      audioElement.remove();
    });
    audioElementsRef.current.clear();
  }, []);

  const attachRemoteAudioTrack = useCallback(
    (track: RemoteTrack, participant: RemoteParticipant) => {
      if (track.kind !== Track.Kind.Audio) {
        return;
      }

      removeParticipantAudio(participant.identity);

      const element = track.attach();
      element.autoplay = true;
      element.style.display = 'none';
      document.body.appendChild(element);
      audioElementsRef.current.set(participant.identity, element);
    },
    [removeParticipantAudio]
  );

  const attachExistingRemoteAudio = useCallback(
    (room: Room) => {
      room.remoteParticipants.forEach((participant) => {
        participant.trackPublications.forEach((publication) => {
          if (
            publication.track &&
            publication.track.kind === Track.Kind.Audio &&
            !audioElementsRef.current.has(participant.identity)
          ) {
            attachRemoteAudioTrack(publication.track as RemoteTrack, participant);
          }
        });
      });
    },
    [attachRemoteAudioTrack]
  );

  const syncParticipants = useCallback((room: Room) => {
    attachExistingRemoteAudio(room);

    const remotePeers = Array.from(room.remoteParticipants.values()).map((participant) => ({
      userId: participant.identity,
      username: participant.name || participant.identity,
      isSpeaking: participant.isSpeaking && participant.isMicrophoneEnabled,
      isMuted: !participant.isMicrophoneEnabled,
    }));

    setPeers(remotePeers);
    setIsMuted(!room.localParticipant.isMicrophoneEnabled);
    setLocalIsSpeaking(room.localParticipant.isSpeaking);
  }, [attachExistingRemoteAudio]);

  const clearScheduledSyncs = useCallback(() => {
    syncTimeoutsRef.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
    syncTimeoutsRef.current = [];
  }, []);

  const resetVoiceState = useCallback(() => {
    setIsInVoice(false);
    setIsVoiceConnecting(false);
    setIsMuted(false);
    setLocalIsSpeaking(false);
    setPeers([]);
  }, []);

  const disconnectRoom = useCallback(async (room: Room | null) => {
    if (!room) {
      return;
    }

    try {
      await room.disconnect();
    } catch {
      // Best-effort cleanup; we'll reset local state either way.
    }
  }, []);

  const scheduleParticipantSyncs = useCallback(
    (room: Room) => {
      clearScheduledSyncs();

      const delays = [0, 250, 1000, 3000];
      syncTimeoutsRef.current = delays.map((delay) =>
        window.setTimeout(() => {
          syncParticipants(room);
        }, delay)
      );
    },
    [clearScheduledSyncs, syncParticipants]
  );

  const registerRoomListeners = useCallback(
    (room: Room) => {
      const sync = () => syncParticipants(room);

      room
        .on(RoomEvent.ParticipantConnected, sync)
        .on(RoomEvent.ParticipantActive, sync)
        .on(RoomEvent.ParticipantDisconnected, (participant: RemoteParticipant) => {
          removeParticipantAudio(participant.identity);
          sync();
        })
        .on(RoomEvent.Connected, sync)
        .on(RoomEvent.SignalConnected, sync)
        .on(RoomEvent.ConnectionStateChanged, sync)
        .on(RoomEvent.TrackPublished, sync)
        .on(RoomEvent.ActiveSpeakersChanged, (speakers: Participant[]) => {
          setLocalIsSpeaking(speakers.some((speaker) => speaker.identity === room.localParticipant.identity));
          sync();
        })
        .on(RoomEvent.LocalTrackPublished, sync)
        .on(RoomEvent.TrackMuted, sync)
        .on(RoomEvent.TrackUnmuted, sync)
        .on(
          RoomEvent.TrackSubscribed,
          (track: RemoteTrack, _publication, participant: RemoteParticipant) => {
            attachRemoteAudioTrack(track, participant);
            sync();
          }
        )
        .on(
          RoomEvent.TrackUnsubscribed,
          (track: RemoteTrack, _publication, participant: RemoteParticipant) => {
            if (track.kind === Track.Kind.Audio) {
              track.detach();
              removeParticipantAudio(participant.identity);
            }
            sync();
          }
        )
        .on(RoomEvent.Disconnected, () => {
          clearScheduledSyncs();
          cleanupAudioElements();
          if (roomRef.current === room) {
            roomRef.current = null;
          }
          if (pendingRoomRef.current === room) {
            pendingRoomRef.current = null;
          }
          isJoiningRef.current = false;
          resetVoiceState();
          roomRef.current = null;
        });
    },
    [attachRemoteAudioTrack, cleanupAudioElements, clearScheduledSyncs, removeParticipantAudio, resetVoiceState, syncParticipants]
  );

  const joinVoice = useCallback(async () => {
    if (!roomCode || isJoiningRef.current || isInVoice) {
      return;
    }

    isJoiningRef.current = true;
    setIsVoiceConnecting(true);
    const attemptId = joinAttemptRef.current + 1;
    joinAttemptRef.current = attemptId;
    let room: Room | null = null;

    try {
      await disconnectRoom(pendingRoomRef.current);
      pendingRoomRef.current = null;

      const response = await api.post<VoiceTokenResponse>(`/rooms/${roomCode}/voice-token`);
      const { token, url } = response.data;

      room = new Room();
      pendingRoomRef.current = room;
      registerRoomListeners(room);

      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true);

      if (joinAttemptRef.current !== attemptId) {
        await disconnectRoom(room);
        return;
      }

      pendingRoomRef.current = null;
      roomRef.current = room;
      setIsInVoice(true);
      syncParticipants(room);
      scheduleParticipantSyncs(room);

      room.remoteParticipants.forEach((participant) => {
        participant.trackPublications.forEach((publication) => {
          if (publication.track && publication.track.kind === Track.Kind.Audio) {
            attachRemoteAudioTrack(publication.track as RemoteTrack, participant);
          }
        });
      });
    } catch (error: any) {
      const detail =
        error?.response?.data?.detail ||
        error?.message ||
        'Could not join voice chat.';
      onError?.(detail);
    } finally {
      if (pendingRoomRef.current === room) {
        pendingRoomRef.current = null;
      }
      if (joinAttemptRef.current === attemptId) {
        isJoiningRef.current = false;
        setIsVoiceConnecting(false);
      }
    }
  }, [attachRemoteAudioTrack, disconnectRoom, isInVoice, onError, registerRoomListeners, roomCode, scheduleParticipantSyncs, syncParticipants]);

  const leaveVoice = useCallback(async () => {
    const room = pendingRoomRef.current ?? roomRef.current;
    isJoiningRef.current = false;
    joinAttemptRef.current += 1;
    clearScheduledSyncs();
    cleanupAudioElements();

    pendingRoomRef.current = null;
    roomRef.current = null;
    await disconnectRoom(room);
    resetVoiceState();
  }, [cleanupAudioElements, clearScheduledSyncs, disconnectRoom, resetVoiceState]);

  const toggleMute = useCallback(async () => {
    const room = roomRef.current;
    if (!room) {
      return;
    }

    const nextEnabled = !room.localParticipant.isMicrophoneEnabled;

    try {
      await room.localParticipant.setMicrophoneEnabled(nextEnabled);
      syncParticipants(room);
    } catch (error) {
      onError?.('Could not update microphone state.');
    }
  }, [onError, syncParticipants]);

  useEffect(() => {
    return () => {
      isJoiningRef.current = false;
      joinAttemptRef.current += 1;
      const room = pendingRoomRef.current ?? roomRef.current;
      pendingRoomRef.current = null;
      roomRef.current = null;
      if (room) {
        void disconnectRoom(room);
      }
      clearScheduledSyncs();
      cleanupAudioElements();
    };
  }, [cleanupAudioElements, clearScheduledSyncs, disconnectRoom]);

  return {
    isVoiceConnecting,
    isInVoice,
    isMuted,
    localIsSpeaking,
    peers,
    joinVoice,
    leaveVoice,
    toggleMute,
  };
}
