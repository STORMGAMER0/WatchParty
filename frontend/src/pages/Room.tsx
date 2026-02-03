import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api';
import Spinner from '../components/Spinner';
import { toast } from '../components/Toast';
import BrowserView from '../components/BrowserView';

interface Message {
  id: number;
  user_id: number;
  username: string;
  content: string;
  created_at: string;
  isSystem?: boolean;
}

interface Participant {
  id: number;
  user_id: number;
  username: string;
  joined_at: string;
}

interface RoomData {
  id: number;
  room_code: string;
  title: string;
  host_id: number;
  host_username: string;
  participants: Participant[];
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export default function Room() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [room, setRoom] = useState<RoomData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [error, setError] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [isLeaving, setIsLeaving] = useState(false);

  // Browser state
  const [browserFrame, setBrowserFrame] = useState<string | null>(null);
  const [browserUrl, setBrowserUrl] = useState('');
  const [isBrowserRunning, setIsBrowserRunning] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load room data and message history
  useEffect(() => {
    const loadRoom = async () => {
      try {
        const [roomRes, messagesRes] = await Promise.all([
          api.get(`/rooms/${roomCode}`),
          api.get(`/rooms/${roomCode}/messages`),
        ]);
        setRoom(roomRes.data);
        setMessages(messagesRes.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load room');
      }
    };
    loadRoom();
  }, [roomCode]);

  // Connect to WebSocket
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token || !roomCode) return;

    setConnectionStatus('connecting');
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/ws/${roomCode}?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);

      if (data.event === 'chat_message') {
        setMessages((prev) => [
          ...prev,
          {
            id: data.message_id || Date.now(),
            user_id: data.user_id,
            username: data.username,
            content: data.content,
            created_at: data.timestamp,
          },
        ]);
      } else if (data.event === 'user_joined') {
        // Add system message
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now(),
            user_id: 0,
            username: 'System',
            content: `${data.username} joined the room`,
            created_at: data.timestamp,
            isSystem: true,
          },
        ]);
        // Refresh participants
        api.get(`/rooms/${roomCode}`).then((res) => setRoom(res.data));
      } else if (data.event === 'user_left') {
        // Add system message
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now(),
            user_id: 0,
            username: 'System',
            content: `${data.username} left the room`,
            created_at: data.timestamp,
            isSystem: true,
          },
        ]);
        // Refresh participants
        api.get(`/rooms/${roomCode}`).then((res) => setRoom(res.data));
      } else if (data.event === 'room_closed') {
        toast.info('Room has been closed by the host');
        navigate('/dashboard');
      }
      // Browser events
      else if (data.event === 'browser_frame') {
        setBrowserFrame(data.frame);
        setBrowserUrl(data.url);
        setIsBrowserRunning(true);  // React optimizes if value unchanged
      } else if (data.event === 'browser_url_changed') {
        setBrowserUrl(data.url);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [roomCode, navigate]);

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !wsRef.current || connectionStatus !== 'connected') return;

    wsRef.current.send(
      JSON.stringify({
        event: 'chat_message',
        content: newMessage,
      })
    );
    setNewMessage('');
  };

  const leaveRoom = async () => {
    setIsLeaving(true);
    try {
      await api.post(`/rooms/${roomCode}/leave`);
      navigate('/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to leave room');
      setIsLeaving(false);
    }
  };

  const copyRoomCode = () => {
    if (roomCode) {
      navigator.clipboard.writeText(roomCode);
      toast.success('Room code copied!');
    }
  };

  // Browser control functions
  const sendBrowserCommand = (event: string, data: Record<string, unknown> = {}) => {
    if (!wsRef.current || connectionStatus !== 'connected') return;
    wsRef.current.send(JSON.stringify({ event, ...data }));
  };

  const startBrowser = () => {
    sendBrowserCommand('browser_start');
    setIsBrowserRunning(true);
  };

  const stopBrowser = () => {
    sendBrowserCommand('browser_stop');
    setIsBrowserRunning(false);
    setBrowserFrame(null);
    setBrowserUrl('');
  };

  const navigateBrowser = (url: string) => {
    sendBrowserCommand('browser_navigate', { url });
  };

  const clickBrowser = (x: number, y: number) => {
    sendBrowserCommand('browser_click', { x, y });
  };

  const typeBrowser = (text: string) => {
    sendBrowserCommand('browser_type', { text });
  };

  const keypressBrowser = (key: string) => {
    sendBrowserCommand('browser_keypress', { key });
  };

  const scrollBrowser = (deltaX: number, deltaY: number) => {
    sendBrowserCommand('browser_scroll', { deltaX, deltaY });
  };

  if (error && !room) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center bg-gray-800/50 p-8 rounded-2xl border border-gray-700/50 max-w-md">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!room) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="text-gray-400 mt-4">Loading room...</p>
        </div>
      </div>
    );
  }

  const isHost = room.host_id === user?.id;

  const statusColors = {
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    disconnected: 'bg-red-500',
  };

  const statusText = {
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
  };

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700/50 px-4 py-3 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-400 hover:text-white transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold text-white">{room.title}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <code className="text-sm text-gray-400 font-mono">{room.room_code}</code>
              <button
                onClick={copyRoomCode}
                className="text-gray-500 hover:text-gray-300 transition"
                title="Copy room code"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${statusColors[connectionStatus]} ${connectionStatus === 'connecting' ? 'animate-pulse' : ''}`}></span>
            <span className="text-gray-400 hidden sm:block">{statusText[connectionStatus]}</span>
          </div>

          <button
            onClick={leaveRoom}
            disabled={isLeaving}
            className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition flex items-center gap-2"
          >
            {isLeaving ? (
              <Spinner size="sm" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            )}
            <span className="hidden sm:block">{isHost ? 'Close Room' : 'Leave'}</span>
          </button>
        </div>
      </header>

      {/* Main Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Browser View */}
        <div className="flex-1">
          <BrowserView
            frame={browserFrame}
            currentUrl={browserUrl}
            isHost={isHost}
            isRunning={isBrowserRunning}
            onStart={startBrowser}
            onStop={stopBrowser}
            onNavigate={navigateBrowser}
            onClick={clickBrowser}
            onType={typeBrowser}
            onKeyPress={keypressBrowser}
            onScroll={scrollBrowser}
          />
        </div>

        {/* Sidebar */}
        <div className="w-80 bg-gray-800/50 backdrop-blur-sm flex flex-col border-l border-gray-700/50">
          {/* Participants */}
          <div className="p-4 border-b border-gray-700/50">
            <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Participants
              <span className="text-gray-500 text-sm font-normal">({room.participants.length}/6)</span>
            </h2>
            <div className="space-y-2">
              {room.participants.map((p) => (
                <div key={p.id} className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-white">
                        {p.username[0].toUpperCase()}
                      </span>
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-gray-800 rounded-full"></span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-gray-300 text-sm truncate block">
                      {p.username}
                      {p.user_id === user?.id && (
                        <span className="text-gray-500 ml-1">(you)</span>
                      )}
                    </span>
                  </div>
                  {p.user_id === room.host_id && (
                    <span className="text-xs text-yellow-500 bg-yellow-500/10 px-2 py-0.5 rounded-full">
                      Host
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Chat */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="p-4 pb-2 border-b border-gray-700/50">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Chat
              </h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-8">No messages yet. Say hi!</p>
              ) : (
                messages.map((msg) => (
                  msg.isSystem ? (
                    <div key={msg.id} className="flex items-center gap-2 py-1">
                      <div className="flex-1 h-px bg-gray-700"></div>
                      <span className="text-xs text-gray-500 px-2">{msg.content}</span>
                      <div className="flex-1 h-px bg-gray-700"></div>
                    </div>
                  ) : (
                    <div key={msg.id} className="group">
                      <div className="flex items-baseline gap-2">
                        <span className={`font-medium text-sm ${msg.user_id === user?.id ? 'text-blue-400' : 'text-purple-400'}`}>
                          {msg.username}
                        </span>
                        <span className="text-gray-600 text-xs opacity-0 group-hover:opacity-100 transition">
                          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-gray-300 text-sm mt-0.5 break-words">{msg.content}</p>
                    </div>
                  )
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <form onSubmit={sendMessage} className="p-4 border-t border-gray-700/50">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder={connectionStatus === 'connected' ? 'Type a message...' : 'Reconnecting...'}
                  disabled={connectionStatus !== 'connected'}
                  className="flex-1 px-4 py-2.5 bg-gray-900/50 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={connectionStatus !== 'connected' || !newMessage.trim()}
                  className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed rounded-lg text-white transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
