import { useEffect, useRef, useState } from 'react';

interface Participant {
  id: number;
  user_id: number;
  username: string;
  joined_at: string;
}

interface BrowserViewProps {
  frame: string | null;        // Base64 encoded image
  currentUrl: string;          // Current page URL
  isHost: boolean;             // Is this user the room host?
  hasControl: boolean;         // Does this user have browser control?
  isRunning: boolean;          // Is browser session active?
  onStart: () => void;         // Start browser
  onStop: () => void;          // Stop browser
  onNavigate: (url: string) => void;
  onClick: (x: number, y: number) => void;
  onType: (text: string) => void;
  onKeyPress: (key: string) => void;
  onScroll: (deltaX: number, deltaY: number) => void;
  // Control bar props
  participants: Participant[];
  controllerId: number | null;
  currentUserId: number;
  onRequestControl: () => void;
  onPassControl: (targetUserId: number) => void;
  onTakeControl: () => void;
}

// The actual browser size on the server
const BROWSER_WIDTH = 1280;
const BROWSER_HEIGHT = 720;

export default function BrowserView({
  frame,
  currentUrl,
  isHost,
  hasControl,
  isRunning,
  onStart,
  onStop,
  onNavigate,
  onClick,
  onType,
  onKeyPress,
  onScroll,
  participants,
  controllerId,
  currentUserId,
  onRequestControl,
  onPassControl,
  onTakeControl,
}: BrowserViewProps) {
  const [urlInput, setUrlInput] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  // Update URL input when page changes
  useEffect(() => {
    if (currentUrl) {
      setUrlInput(currentUrl);
    }
  }, [currentUrl]);

  // Handle click on the browser image
  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imageRef.current || !hasControl) return;

    // Get click position relative to the image
    const rect = imageRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Get displayed image size
    const displayWidth = rect.width;
    const displayHeight = rect.height;

    // Convert to actual browser coordinates
    const actualX = Math.round((clickX / displayWidth) * BROWSER_WIDTH);
    const actualY = Math.round((clickY / displayHeight) * BROWSER_HEIGHT);

    onClick(actualX, actualY);
  };

  // Handle keyboard input when image is focused
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!hasControl || !isRunning) return;

    // Prevent default browser behavior for most keys
    e.preventDefault();

    // Special keys
    const specialKeys = [
      'Enter', 'Backspace', 'Tab', 'Escape', 'Delete',
      'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
      'Home', 'End', 'PageUp', 'PageDown',
    ];

    if (specialKeys.includes(e.key)) {
      onKeyPress(e.key);
    } else if (e.key.length === 1) {
      // Regular character
      onType(e.key);
    }
  };

  // Handle scroll wheel
  const handleWheel = (e: React.WheelEvent) => {
    if (!hasControl || !isRunning) return;
    e.preventDefault();
    onScroll(e.deltaX, e.deltaY);
  };

  // Handle URL form submit
  const handleNavigate = (e: React.FormEvent) => {
    e.preventDefault();
    if (urlInput.trim()) {
      onNavigate(urlInput.trim());
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* URL Bar - only show when browser is running */}
      {isRunning && (
        <div className="flex items-center gap-2 p-2 bg-gray-800 border-b border-gray-700">
          <form onSubmit={handleNavigate} className="flex-1 flex gap-2">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="Enter URL..."
              disabled={!hasControl}
              className="flex-1 px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-white text-sm placeholder-gray-400 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            {hasControl && (
              <button
                type="submit"
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm transition"
              >
                Go
              </button>
            )}
          </form>
          {isHost && (
            <button
              onClick={onStop}
              className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm transition"
            >
              Stop
            </button>
          )}
        </div>
      )}

      {/* Browser Content */}
      <div
        ref={containerRef}
        className="flex-1 flex items-center justify-center overflow-hidden bg-black"
      >
        {!isRunning ? (
          // Browser not started
          <div className="text-center">
            <div className="w-24 h-24 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-gray-400 mb-4">Browser not started</p>
            {isHost ? (
              <button
                onClick={onStart}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition"
              >
                Start Browser
              </button>
            ) : (
              <p className="text-gray-500 text-sm">Waiting for host to start the browser...</p>
            )}
          </div>
        ) : !frame ? (
          // Browser started but no frame yet
          <div className="text-center">
            <div className="w-12 h-12 border-2 border-gray-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading browser...</p>
          </div>
        ) : (
          // Display the browser frame
          <img
            ref={imageRef}
            src={`data:image/jpeg;base64,${frame}`}
            alt="Browser view"
            className={`max-w-full max-h-full object-contain ${hasControl ? 'cursor-pointer' : 'cursor-default'}`}
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            onWheel={handleWheel}
            tabIndex={hasControl ? 0 : -1}
            draggable={false}
          />
        )}
      </div>

      {/* Control Bar - shows when browser is running */}
      {isRunning && (
        <div className="p-3 bg-gray-800 border-t border-gray-700">
          <div className="flex items-center justify-center gap-2">
            {participants.map((p) => {
              const isController = p.user_id === controllerId;
              const isMe = p.user_id === currentUserId;
              const canPassToThis = hasControl && !isMe;
              const canRequest = !hasControl && isMe;

              return (
                <button
                  key={p.id}
                  onClick={() => {
                    if (canPassToThis) {
                      onPassControl(p.user_id);
                    } else if (canRequest) {
                      onRequestControl();
                    }
                  }}
                  disabled={!canPassToThis && !canRequest}
                  className={`relative group ${canPassToThis || canRequest ? 'cursor-pointer' : 'cursor-default'}`}
                  title={
                    isController
                      ? `${p.username} has control`
                      : canPassToThis
                      ? `Pass control to ${p.username}`
                      : canRequest
                      ? 'Request control'
                      : p.username
                  }
                >
                  {/* Avatar */}
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-medium transition-all
                      ${isController
                        ? 'bg-gradient-to-br from-green-500 to-emerald-600 ring-2 ring-green-400'
                        : 'bg-gradient-to-br from-blue-500 to-purple-500'}
                      ${canPassToThis ? 'hover:ring-2 hover:ring-blue-400' : ''}
                      ${canRequest ? 'hover:ring-2 hover:ring-yellow-400' : ''}
                    `}
                  >
                    {p.username[0].toUpperCase()}
                  </div>

                  {/* Controller icon */}
                  {isController && (
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center border-2 border-gray-800">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                        <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}

                  {/* "You" indicator */}
                  {isMe && !isController && (
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-gray-600 rounded-full flex items-center justify-center border-2 border-gray-800">
                      <span className="text-[8px] text-white font-bold">YOU</span>
                    </div>
                  )}
                </button>
              );
            })}

            {/* Host "Take Control" button - only if host doesn't have control */}
            {isHost && !hasControl && (
              <button
                onClick={onTakeControl}
                className="ml-4 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 rounded text-sm transition flex items-center gap-1"
                title="Take control (host only)"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
                Take
              </button>
            )}
          </div>

          {/* Hint text */}
          <p className="text-gray-500 text-xs text-center mt-2">
            {hasControl
              ? 'You have control • Click avatar to pass control'
              : 'Click your avatar to request control'}
          </p>
        </div>
      )}
    </div>
  );
}
