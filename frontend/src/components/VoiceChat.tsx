import { useVoiceStore } from '../stores/voiceStore';

interface VoiceChatProps {
  isInVoice: boolean;
  isMuted: boolean;
  onJoin: () => void;
  onLeave: () => void;
  onToggleMute: () => void;
}

/**
 * Voice chat controls component.
 *
 * Displays:
 * - Join/Leave button
 * - Mute/Unmute button (when in voice)
 * - Speaking indicators for peers
 */
export default function VoiceChat({
  isInVoice,
  isMuted,
  onJoin,
  onLeave,
  onToggleMute,
}: VoiceChatProps) {
  const { peers } = useVoiceStore();

  return (
    <div className="p-4 border-b border-gray-700/50">
      <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
        Voice Chat
        {isInVoice && (
          <span className="text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full">
            Connected
          </span>
        )}
      </h2>

      {/* Voice Controls */}
      <div className="flex gap-2 mb-3">
        {!isInVoice ? (
          <button
            onClick={onJoin}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg transition flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15.536a5 5 0 001.414 1.414m2.828-9.9a9 9 0 0112.728 0"
              />
            </svg>
            Join Voice
          </button>
        ) : (
          <>
            <button
              onClick={onToggleMute}
              className={`flex-1 px-4 py-2 rounded-lg transition flex items-center justify-center gap-2 ${
                isMuted
                  ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400'
                  : 'bg-gray-700 hover:bg-gray-600 text-white'
              }`}
            >
              {isMuted ? (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                    />
                  </svg>
                  Muted
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                  Mic On
                </>
              )}
            </button>
            <button
              onClick={onLeave}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition"
              title="Leave voice chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"
                />
              </svg>
            </button>
          </>
        )}
      </div>

      {/* Peers in Voice */}
      {isInVoice && peers.size > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 uppercase tracking-wide">In Voice</p>
          {Array.from(peers.values()).map((peer) => (
            <div
              key={peer.userId}
              className={`flex items-center gap-2 px-2 py-1.5 rounded-lg transition ${
                peer.isSpeaking ? 'bg-green-500/10' : 'bg-gray-800/50'
              }`}
            >
              <div className="relative">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    peer.isSpeaking
                      ? 'bg-green-500'
                      : 'bg-gradient-to-br from-blue-500 to-purple-500'
                  }`}
                >
                  <span className="text-sm font-medium text-white">
                    {peer.username[0]?.toUpperCase() || '?'}
                  </span>
                </div>
                {peer.isSpeaking && (
                  <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-gray-800 rounded-full animate-pulse" />
                )}
              </div>
              <span className="text-sm text-gray-300 truncate">{peer.username}</span>
              {peer.isSpeaking && (
                <svg
                  className="w-4 h-4 text-green-400 ml-auto"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {isInVoice && peers.size === 0 && (
        <p className="text-sm text-gray-500 text-center py-2">
          Waiting for others to join voice...
        </p>
      )}
    </div>
  );
}
