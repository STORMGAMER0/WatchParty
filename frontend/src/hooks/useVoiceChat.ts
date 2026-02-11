import { useCallback, useRef, useEffect } from 'react';
import { useVoiceStore } from '../stores/voiceStore';

/**
 * Configuration for WebRTC connections.
 *
 * iceServers: STUN servers help peers discover their public IP addresses.
 * We use Google's free STUN servers. For production, you might add TURN
 * servers as fallback for peers behind strict NATs.
 */
const RTC_CONFIG: RTCConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
};

interface UseVoiceChatProps {
  /** Current user's ID */
  userId: number;
  /** WebSocket reference for signaling */
  wsRef: React.RefObject<WebSocket | null>;
  /** Called when a voice event is received that we need to handle */
  onError?: (message: string) => void;
}

/**
 * Hook that manages WebRTC voice chat.
 *
 * This handles:
 * 1. Getting microphone access
 * 2. Creating/managing peer connections (one per other user)
 * 3. Signaling (sending/receiving SDP offers, answers, ICE candidates)
 * 4. Audio playback (playing received audio streams)
 */
export function useVoiceChat({ userId, wsRef, onError }: UseVoiceChatProps) {
  const {
    isInVoice,
    localStream,
    isMuted,
    peers,
    setIsInVoice,
    setLocalStream,
    toggleMute,
    addPeer,
    removePeer,
    setPeerStream,
    setPeerSpeaking,
    reset,
  } = useVoiceStore();

  // Track which users are in voice chat (for creating connections)
  const voiceUsersRef = useRef<Set<number>>(new Set());

  // Audio elements for playing peer streams
  const audioElementsRef = useRef<Map<number, HTMLAudioElement>>(new Map());

  /**
   * Send a signaling message through WebSocket.
   */
  const sendSignal = useCallback(
    (event: string, data: Record<string, unknown>) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ event, ...data }));
      }
    },
    [wsRef]
  );

  /**
   * Create a new RTCPeerConnection for a specific peer.
   *
   * This sets up all the event handlers for:
   * - ICE candidate gathering (finding ways to connect)
   * - Track reception (receiving their audio)
   * - Connection state changes
   */
  const createPeerConnection = useCallback(
    (peerId: number, peerUsername: string): RTCPeerConnection => {
      console.log(`[Voice] Creating peer connection for user ${peerId}`);

      const pc = new RTCPeerConnection(RTC_CONFIG);

      // When we find a new ICE candidate, send it to the peer
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          console.log(`[Voice] Sending ICE candidate to user ${peerId}`);
          sendSignal('voice_ice_candidate', {
            to_user_id: peerId,
            candidate: JSON.stringify(event.candidate),
          });
        }
      };

      // When we receive their audio track
      pc.ontrack = (event) => {
        console.log(`[Voice] Received audio track from user ${peerId}`);
        const [remoteStream] = event.streams;
        setPeerStream(peerId, remoteStream);

        // Create an audio element to play their audio
        let audioEl = audioElementsRef.current.get(peerId);
        if (!audioEl) {
          audioEl = new Audio();
          audioEl.autoplay = true;
          audioElementsRef.current.set(peerId, audioEl);
        }
        audioEl.srcObject = remoteStream;

        // Set up speaking detection using audio analysis
        setupSpeakingDetection(peerId, remoteStream);
      };

      // Monitor connection state
      pc.onconnectionstatechange = () => {
        console.log(`[Voice] Connection state with ${peerId}: ${pc.connectionState}`);
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          // Could implement reconnection logic here
          console.warn(`[Voice] Connection with ${peerId} ${pc.connectionState}`);
        }
      };

      // Add our local audio tracks to the connection
      if (localStream) {
        localStream.getTracks().forEach((track) => {
          pc.addTrack(track, localStream);
        });
      }

      // Store the peer connection
      addPeer(peerId, peerUsername, pc);

      return pc;
    },
    [localStream, sendSignal, addPeer, setPeerStream]
  );

  /**
   * Set up audio analysis to detect when a peer is speaking.
   * Uses Web Audio API to analyze volume levels.
   */
  const setupSpeakingDetection = useCallback(
    (peerId: number, stream: MediaStream) => {
      try {
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;

        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        let speakingTimeout: ReturnType<typeof setTimeout> | null = null;

        const checkVolume = () => {
          // Stop if peer was removed
          if (!useVoiceStore.getState().peers.has(peerId)) {
            audioContext.close();
            return;
          }

          analyser.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;

          // Threshold for "speaking" - adjust as needed
          const isSpeaking = average > 20;

          if (isSpeaking) {
            setPeerSpeaking(peerId, true);
            if (speakingTimeout) clearTimeout(speakingTimeout);
            speakingTimeout = setTimeout(() => {
              setPeerSpeaking(peerId, false);
            }, 300);
          }

          requestAnimationFrame(checkVolume);
        };

        checkVolume();
      } catch (err) {
        console.warn('[Voice] Could not set up speaking detection:', err);
      }
    },
    [setPeerSpeaking]
  );

  /**
   * Join voice chat.
   *
   * 1. Get microphone access
   * 2. Broadcast that we're joining
   * 3. Wait for existing users to send us offers
   */
  const joinVoice = useCallback(async () => {
    try {
      console.log('[Voice] Joining voice chat...');

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });

      setLocalStream(stream);
      setIsInVoice(true);
      voiceUsersRef.current.add(userId);

      // Broadcast that we're joining - other users will send us offers
      sendSignal('voice_join', {});

      console.log('[Voice] Joined voice chat, waiting for peers...');
    } catch (err) {
      console.error('[Voice] Failed to get microphone:', err);
      onError?.('Could not access microphone. Please check permissions.');
    }
  }, [userId, sendSignal, setLocalStream, setIsInVoice, onError]);

  /**
   * Leave voice chat.
   *
   * 1. Broadcast that we're leaving
   * 2. Close all peer connections
   * 3. Stop microphone
   */
  const leaveVoice = useCallback(() => {
    console.log('[Voice] Leaving voice chat...');

    // Broadcast that we're leaving
    sendSignal('voice_leave', {});

    // Clean up audio elements
    audioElementsRef.current.forEach((audio) => {
      audio.srcObject = null;
    });
    audioElementsRef.current.clear();

    // Clear voice users
    voiceUsersRef.current.clear();

    // Reset all state and close connections
    reset();

    console.log('[Voice] Left voice chat');
  }, [sendSignal, reset]);

  /**
   * Handle incoming voice_join event.
   *
   * When another user joins, WE need to:
   * 1. Create a peer connection for them
   * 2. Create an SDP offer
   * 3. Send the offer to them
   */
  const handleVoiceJoin = useCallback(
    async (fromUserId: number, fromUsername: string) => {
      // Ignore our own join event
      if (fromUserId === userId) return;

      // Only handle if we're in voice chat
      if (!isInVoice) return;

      console.log(`[Voice] User ${fromUsername} (${fromUserId}) joined voice`);
      voiceUsersRef.current.add(fromUserId);

      // Create peer connection and send offer
      const pc = createPeerConnection(fromUserId, fromUsername);

      try {
        // Create SDP offer
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        console.log(`[Voice] Sending offer to user ${fromUserId}`);
        sendSignal('voice_offer', {
          to_user_id: fromUserId,
          sdp: JSON.stringify(pc.localDescription),
        });
      } catch (err) {
        console.error(`[Voice] Failed to create offer for ${fromUserId}:`, err);
      }
    },
    [userId, isInVoice, createPeerConnection, sendSignal]
  );

  /**
   * Handle incoming voice_leave event.
   */
  const handleVoiceLeave = useCallback(
    (fromUserId: number) => {
      if (fromUserId === userId) return;

      console.log(`[Voice] User ${fromUserId} left voice`);
      voiceUsersRef.current.delete(fromUserId);

      // Clean up audio element
      const audioEl = audioElementsRef.current.get(fromUserId);
      if (audioEl) {
        audioEl.srcObject = null;
        audioElementsRef.current.delete(fromUserId);
      }

      // Remove peer connection
      removePeer(fromUserId);
    },
    [userId, removePeer]
  );

  /**
   * Handle incoming voice_offer event.
   *
   * When we receive an offer:
   * 1. Create a peer connection (if we don't have one)
   * 2. Set the remote description (their offer)
   * 3. Create and send an answer
   */
  const handleVoiceOffer = useCallback(
    async (fromUserId: number, sdp: string) => {
      console.log(`[Voice] Received offer from user ${fromUserId}`);

      // Get or create peer connection
      let pc = peers.get(fromUserId)?.connection;
      if (!pc) {
        pc = createPeerConnection(fromUserId, `User ${fromUserId}`);
      }

      try {
        const offer = JSON.parse(sdp);
        await pc.setRemoteDescription(new RTCSessionDescription(offer));

        // Create answer
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        console.log(`[Voice] Sending answer to user ${fromUserId}`);
        sendSignal('voice_answer', {
          to_user_id: fromUserId,
          sdp: JSON.stringify(pc.localDescription),
        });
      } catch (err) {
        console.error(`[Voice] Failed to handle offer from ${fromUserId}:`, err);
      }
    },
    [peers, createPeerConnection, sendSignal]
  );

  /**
   * Handle incoming voice_answer event.
   *
   * When we receive an answer to our offer:
   * Set the remote description (their answer)
   */
  const handleVoiceAnswer = useCallback(
    async (fromUserId: number, sdp: string) => {
      console.log(`[Voice] Received answer from user ${fromUserId}`);

      const pc = peers.get(fromUserId)?.connection;
      if (!pc) {
        console.warn(`[Voice] No connection found for user ${fromUserId}`);
        return;
      }

      try {
        const answer = JSON.parse(sdp);
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
        console.log(`[Voice] Connection established with user ${fromUserId}`);
      } catch (err) {
        console.error(`[Voice] Failed to handle answer from ${fromUserId}:`, err);
      }
    },
    [peers]
  );

  /**
   * Handle incoming voice_ice_candidate event.
   *
   * Add the ICE candidate to the peer connection.
   * This helps establish the best network path between peers.
   */
  const handleVoiceIceCandidate = useCallback(
    async (fromUserId: number, candidateStr: string) => {
      const pc = peers.get(fromUserId)?.connection;
      if (!pc) {
        console.warn(`[Voice] No connection found for ICE from user ${fromUserId}`);
        return;
      }

      try {
        if (candidateStr) {
          const candidate = JSON.parse(candidateStr);
          await pc.addIceCandidate(new RTCIceCandidate(candidate));
          console.log(`[Voice] Added ICE candidate from user ${fromUserId}`);
        }
      } catch (err) {
        console.error(`[Voice] Failed to add ICE candidate from ${fromUserId}:`, err);
      }
    },
    [peers]
  );

  /**
   * Handle WebSocket messages related to voice chat.
   * Call this from your main WebSocket message handler.
   */
  const handleVoiceMessage = useCallback(
    (data: Record<string, unknown>) => {
      const event = data.event as string;

      switch (event) {
        case 'voice_join':
          handleVoiceJoin(data.user_id as number, data.username as string);
          break;
        case 'voice_leave':
          handleVoiceLeave(data.user_id as number);
          break;
        case 'voice_offer':
          handleVoiceOffer(data.from_user_id as number, data.sdp as string);
          break;
        case 'voice_answer':
          handleVoiceAnswer(data.from_user_id as number, data.sdp as string);
          break;
        case 'voice_ice_candidate':
          handleVoiceIceCandidate(data.from_user_id as number, data.candidate as string);
          break;
      }
    },
    [handleVoiceJoin, handleVoiceLeave, handleVoiceOffer, handleVoiceAnswer, handleVoiceIceCandidate]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isInVoice) {
        leaveVoice();
      }
    };
  }, []);

  return {
    // State
    isInVoice,
    isMuted,
    peers,

    // Actions
    joinVoice,
    leaveVoice,
    toggleMute,
    handleVoiceMessage,
  };
}
