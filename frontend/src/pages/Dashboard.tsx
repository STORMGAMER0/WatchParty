import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { api } from '../services/api';
import Spinner from '../components/Spinner';

interface Room {
  id: number;
  room_code: string;
  title: string;
  host_id: number;
  is_active: boolean;
  created_at: string;
}

export default function Dashboard() {
  const { user, logout, loadUser } = useAuthStore();
  const [rooms, setRooms] = useState<Room[]>([]);
  const [newRoomTitle, setNewRoomTitle] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const init = async () => {
      try {
        await loadUser();
        await fetchRooms();
      } catch (err) {
        console.error('Init error:', err);
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  const fetchRooms = async () => {
    try {
      const response = await api.get('/rooms');
      setRooms(response.data);
    } catch (err) {
      console.error('Failed to fetch rooms:', err);
    }
  };

  const createRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsCreating(true);
    try {
      const response = await api.post('/rooms', { title: newRoomTitle });
      setNewRoomTitle('');
      navigate(`/room/${response.data.room_code}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create room');
    } finally {
      setIsCreating(false);
    }
  };

  const joinRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post(`/rooms/${joinCode}/join`);
      navigate(`/room/${joinCode}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join room');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const copyRoomCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setSuccess('Room code copied!');
    setTimeout(() => setSuccess(''), 2000);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="text-gray-400 mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white">Watch Party</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.username?.[0]?.toUpperCase()}
                </span>
              </div>
              <span className="text-gray-300 hidden sm:block">{user?.username}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Notifications */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
            <button onClick={() => setError('')} className="ml-auto hover:text-red-300">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {success && (
          <div className="bg-green-500/10 border border-green-500/50 text-green-400 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{success}</span>
          </div>
        )}

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Create Room */}
          <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-2xl border border-gray-700/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-600/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-white">Create a Room</h2>
            </div>
            <form onSubmit={createRoom} className="space-y-4">
              <input
                type="text"
                value={newRoomTitle}
                onChange={(e) => setNewRoomTitle(e.target.value)}
                placeholder="Room title (e.g., Movie Night)"
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                required
              />
              <button
                type="submit"
                disabled={isCreating}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 rounded-lg font-semibold text-white transition flex items-center justify-center gap-2"
              >
                {isCreating ? (
                  <>
                    <Spinner size="sm" />
                    <span>Creating...</span>
                  </>
                ) : (
                  'Create Room'
                )}
              </button>
            </form>
          </div>

          {/* Join Room */}
          <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-2xl border border-gray-700/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-600/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-white">Join a Room</h2>
            </div>
            <form onSubmit={joinRoom} className="space-y-4">
              <input
                type="text"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="Enter room code"
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition uppercase tracking-widest text-center font-mono"
                required
                maxLength={8}
              />
              <button
                type="submit"
                className="w-full py-3 bg-green-600 hover:bg-green-500 rounded-lg font-semibold text-white transition"
              >
                Join Room
              </button>
            </form>
          </div>
        </div>

        {/* My Rooms */}
        <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-2xl border border-gray-700/50">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-purple-600/20 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-white">My Rooms</h2>
          </div>

          {rooms.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-gray-400">No active rooms</p>
              <p className="text-gray-500 text-sm mt-1">Create or join a room to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {rooms.map((room) => (
                <div
                  key={room.id}
                  className="flex justify-between items-center bg-gray-900/50 p-4 rounded-xl border border-gray-700/50 hover:border-gray-600/50 transition group"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                      <span className="text-lg font-bold text-white">
                        {room.title[0].toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">{room.title}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-sm text-gray-400 font-mono bg-gray-800 px-2 py-0.5 rounded">
                          {room.room_code}
                        </code>
                        <button
                          onClick={() => copyRoomCode(room.room_code)}
                          className="text-gray-500 hover:text-gray-300 transition"
                          title="Copy room code"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </button>
                        {room.host_id === user?.id && (
                          <span className="text-xs text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded-full">
                            Host
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate(`/room/${room.room_code}`)}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition"
                  >
                    Enter
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
