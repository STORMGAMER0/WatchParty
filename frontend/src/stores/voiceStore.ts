import { create } from 'zustand';

/**
 * Represents a peer in the voice chat.
 * Each peer has their own RTCPeerConnection and audio stream.
 */
export interface VoicePeer {
  userId: number;
  username: string;
  connection: RTCPeerConnection;
  stream: MediaStream | null; // Their audio stream (what we hear)
  isSpeaking: boolean;
}

interface VoiceState {
  // Are we currently in voice chat?
  isInVoice: boolean;

  // Our local audio stream (our microphone)
  localStream: MediaStream | null;

  // Are we muted?
  isMuted: boolean;

  // Map of peer connections: oderId -> VoicePeer
  peers: Map<number, VoicePeer>;

  // Actions
  setIsInVoice: (isInVoice: boolean) => void;
  setLocalStream: (stream: MediaStream | null) => void;
  setIsMuted: (isMuted: boolean) => void;
  toggleMute: () => void;
  addPeer: (userId: number, username: string, connection: RTCPeerConnection) => void;
  removePeer: (userId: number) => void;
  setPeerStream: (userId: number, stream: MediaStream) => void;
  setPeerSpeaking: (userId: number, isSpeaking: boolean) => void;
  reset: () => void;
}

export const useVoiceStore = create<VoiceState>((set, get) => ({
  isInVoice: false,
  localStream: null,
  isMuted: false,
  peers: new Map(),

  setIsInVoice: (isInVoice) => set({ isInVoice }),

  setLocalStream: (stream) => set({ localStream: stream }),

  setIsMuted: (isMuted) => {
    const { localStream } = get();
    // Actually mute/unmute the audio tracks
    if (localStream) {
      localStream.getAudioTracks().forEach((track) => {
        track.enabled = !isMuted;
      });
    }
    set({ isMuted });
  },

  toggleMute: () => {
    const { isMuted, setIsMuted } = get();
    setIsMuted(!isMuted);
  },

  addPeer: (userId, username, connection) => {
    const { peers } = get();
    const newPeers = new Map(peers);
    newPeers.set(userId, {
      userId,
      username,
      connection,
      stream: null,
      isSpeaking: false,
    });
    set({ peers: newPeers });
  },

  removePeer: (userId) => {
    const { peers } = get();
    const peer = peers.get(userId);
    if (peer) {
      // Close the RTCPeerConnection
      peer.connection.close();
    }
    const newPeers = new Map(peers);
    newPeers.delete(userId);
    set({ peers: newPeers });
  },

  setPeerStream: (userId, stream) => {
    const { peers } = get();
    const peer = peers.get(userId);
    if (peer) {
      const newPeers = new Map(peers);
      newPeers.set(userId, { ...peer, stream });
      set({ peers: newPeers });
    }
  },

  setPeerSpeaking: (userId, isSpeaking) => {
    const { peers } = get();
    const peer = peers.get(userId);
    if (peer) {
      const newPeers = new Map(peers);
      newPeers.set(userId, { ...peer, isSpeaking });
      set({ peers: newPeers });
    }
  },

  reset: () => {
    const { localStream, peers } = get();
    // Stop local stream tracks
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }
    // Close all peer connections
    peers.forEach((peer) => peer.connection.close());
    set({
      isInVoice: false,
      localStream: null,
      isMuted: false,
      peers: new Map(),
    });
  },
}));
