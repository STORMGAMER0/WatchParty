import { useState, useRef, useEffect, ReactNode } from 'react';
import { useVoiceStore } from '../stores/voiceStore';

type TabType = 'text' | 'voice';

interface ChatTabsProps {
  // Voice props
  isInVoice: boolean;
  isMuted: boolean;
  onJoinVoice: () => void;
  onLeaveVoice: () => void;
  onToggleMute: () => void;
  // Text chat content (passed as children or render prop)
  children: ReactNode;
}

/**
 * Tabbed interface for Text Chat and Voice Chat.
 *
 * - Text tab: Shows chat messages and input
 * - Voice tab: Shows join button (when not connected) or controls + peers (when connected)
 */
export default function ChatTabs({
  isInVoice,
  isMuted,
  onJoinVoice,
  onLeaveVoice,
  onToggleMute,
  children,
}: ChatTabsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('text');
  const { peers } = useVoiceStore();

  return (
    <div className="flex flex-col h-full">
      {/* Tab Headers */}
      <div className="flex border-b border-gray-700/50">
        <button
          onClick={() => setActiveTab('text')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition flex items-center justify-center gap-2 ${
            activeTab === 'text'
              ? 'text-white border-b-2 border-blue-500 bg-gray-800/30'
              : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/20'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          Text
        </button>
        <button
          onClick={() => setActiveTab('voice')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition flex items-center justify-center gap-2 ${
            activeTab === 'voice'
              ? 'text-white border-b-2 border-blue-500 bg-gray-800/30'
              : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/20'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
          Voice
          {isInVoice && (
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          )}
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'text' ? (
          // Text Chat Tab - render children (the chat messages and input)
          <div className="h-full flex flex-col">{children}</div>
        ) : (
          // Voice Chat Tab
          <div className="h-full flex flex-col">
            {!isInVoice ? (
              // Not in voice - show join button centered
              <div className="flex-1 flex flex-col items-center justify-center p-6">
                <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mb-4">
                  <svg
                    className="w-10 h-10 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                </div>
                <h3 className="text-white font-medium mb-2">Voice Chat</h3>
                <p className="text-gray-400 text-sm text-center mb-6">
                  Join voice to talk with others in the room
                </p>
                <button
                  onClick={onJoinVoice}
                  className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg transition flex items-center gap-2 font-medium"
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
              </div>
            ) : (
              // In voice - show controls and peers
              <div className="flex-1 flex flex-col p-4">
                {/* Connected Status */}
                <div className="flex items-center justify-center gap-2 mb-4 py-2 bg-green-500/10 rounded-lg">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-green-400 text-sm font-medium">Connected to Voice</span>
                </div>

                {/* Controls */}
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={onToggleMute}
                    className={`flex-1 px-4 py-3 rounded-lg transition flex items-center justify-center gap-2 ${
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
                    onClick={onLeaveVoice}
                    className="px-4 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"
                      />
                    </svg>
                    Leave
                  </button>
                </div>

                {/* Peers in Voice */}
                <div className="flex-1 overflow-y-auto">
                  <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">
                    In Voice ({peers.size + 1})
                  </p>

                  {/* Show yourself first */}
                  <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-blue-500/10 mb-2">
                    <div className="relative">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-blue-500">
                        <span className="text-sm font-medium text-white">You</span>
                      </div>
                      {!isMuted && (
                        <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 border-2 border-gray-800 rounded-full" />
                      )}
                    </div>
                    <span className="text-sm text-gray-300">You</span>
                    {isMuted && (
                      <svg className="w-4 h-4 text-red-400 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                      </svg>
                    )}
                  </div>

                  {/* Other peers */}
                  {Array.from(peers.values()).map((peer) => (
                    <div
                      key={peer.userId}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-lg transition mb-1 ${
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

                  {peers.size === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4">
                      Waiting for others to join voice...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
