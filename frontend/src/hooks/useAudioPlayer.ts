import { useCallback, useEffect, useRef } from 'react';

/**
 * Hook for playing streamed audio chunks received via WebSocket.
 * Uses MediaSource Extensions (MSE) to handle MP3 streaming.
 */
export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaSourceRef = useRef<MediaSource | null>(null);
  const sourceBufferRef = useRef<SourceBuffer | null>(null);
  const queueRef = useRef<ArrayBuffer[]>([]);
  const isInitializedRef = useRef(false);

  // Initialize the audio element and MediaSource
  const initialize = useCallback(() => {
    if (isInitializedRef.current) return;

    // Create audio element
    const audio = new Audio();
    audio.autoplay = true;
    audioRef.current = audio;

    // Create MediaSource
    const mediaSource = new MediaSource();
    mediaSourceRef.current = mediaSource;

    // Connect audio to MediaSource
    audio.src = URL.createObjectURL(mediaSource);

    mediaSource.addEventListener('sourceopen', () => {
      try {
        // MP3 MIME type
        const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
        sourceBufferRef.current = sourceBuffer;

        // Process queued chunks when buffer is ready
        sourceBuffer.addEventListener('updateend', () => {
          processQueue();
        });

        isInitializedRef.current = true;
        console.log('[AudioPlayer] Initialized');

        // Process any chunks that arrived before initialization
        processQueue();
      } catch (err) {
        console.error('[AudioPlayer] Failed to initialize:', err);
      }
    });

    mediaSource.addEventListener('sourceended', () => {
      console.log('[AudioPlayer] Source ended');
    });

    mediaSource.addEventListener('error', (e) => {
      console.error('[AudioPlayer] MediaSource error:', e);
    });
  }, []);

  // Process the queue of audio chunks
  const processQueue = useCallback(() => {
    const sourceBuffer = sourceBufferRef.current;
    if (!sourceBuffer || sourceBuffer.updating || queueRef.current.length === 0) {
      return;
    }

    const chunk = queueRef.current.shift();
    if (chunk) {
      try {
        sourceBuffer.appendBuffer(chunk);
      } catch (err) {
        console.error('[AudioPlayer] Error appending buffer:', err);
        // Re-queue the chunk if it failed
        queueRef.current.unshift(chunk);
      }
    }
  }, []);

  // Add a new audio chunk (base64 encoded)
  const addChunk = useCallback((base64Chunk: string) => {
    // Initialize on first chunk
    if (!isInitializedRef.current) {
      initialize();
    }

    // Decode base64 to ArrayBuffer
    const binaryString = atob(base64Chunk);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // Add to queue
    queueRef.current.push(bytes.buffer);

    // Try to process immediately
    processQueue();
  }, [initialize, processQueue]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if (mediaSourceRef.current && mediaSourceRef.current.readyState === 'open') {
        try {
          mediaSourceRef.current.endOfStream();
        } catch (e) {
          // Ignore errors during cleanup
        }
      }
      isInitializedRef.current = false;
      queueRef.current = [];
    };
  }, []);

  // Reset the player (e.g., when browser stops)
  const reset = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    if (mediaSourceRef.current && mediaSourceRef.current.readyState === 'open') {
      try {
        mediaSourceRef.current.endOfStream();
      } catch (e) {
        // Ignore
      }
    }
    audioRef.current = null;
    mediaSourceRef.current = null;
    sourceBufferRef.current = null;
    queueRef.current = [];
    isInitializedRef.current = false;
    console.log('[AudioPlayer] Reset');
  }, []);

  return { addChunk, reset };
}
