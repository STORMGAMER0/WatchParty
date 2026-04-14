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
  const audioElementsRef = useRef<Map<string, HTMLMediaElement>>(new Map());
  const syncTimeoutsRef = useRef<number[]>([]);

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
      isSpeaking: participant.isSpeaking,
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
          setIsInVoice(false);
          setIsVoiceConnecting(false);
          setIsMuted(false);
          setLocalIsSpeaking(false);
          setPeers([]);
          roomRef.current = null;
        });
    },
    [attachRemoteAudioTrack, cleanupAudioElements, clearScheduledSyncs, removeParticipantAudio, syncParticipants]
  );

  const joinVoice = useCallback(async () => {
    if (!roomCode || isVoiceConnecting || isInVoice) {
      return;
    }

    setIsVoiceConnecting(true);

    try {
      const response = await api.post<VoiceTokenResponse>(`/rooms/${roomCode}/voice-token`);
      const { token, url } = response.data;

      const room = new Room();
      registerRoomListeners(room);

      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true);

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
      setIsVoiceConnecting(false);
    }
  }, [attachRemoteAudioTrack, isInVoice, isVoiceConnecting, onError, registerRoomListeners, roomCode, syncParticipants]);

  const leaveVoice = useCallback(async () => {
    const room = roomRef.current;
    clearScheduledSyncs();
    cleanupAudioElements();

    if (room) {
      await room.disconnect();
    }

    roomRef.current = null;
    setIsInVoice(false);
    setIsVoiceConnecting(false);
    setIsMuted(false);
    setLocalIsSpeaking(false);
    setPeers([]);
  }, [cleanupAudioElements, clearScheduledSyncs]);

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
      if (roomRef.current) {
        void roomRef.current.disconnect();
        roomRef.current = null;
      }
      clearScheduledSyncs();
      cleanupAudioElements();
    };
  }, [cleanupAudioElements, clearScheduledSyncs]);

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
