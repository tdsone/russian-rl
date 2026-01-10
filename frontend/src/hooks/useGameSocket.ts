import { useState, useEffect, useCallback, useRef } from 'react';

// Determine WebSocket URL based on environment
// In production, use the current host with /ws path (nginx proxies to backend)
// In development, use localhost:8000 directly
function getWebSocketUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    // Production: use current host with ws/wss protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/game`;
  }
  // Development: connect directly to backend
  return 'ws://localhost:8000/ws/game';
}

const WS_URL = getWebSocketUrl();

interface Move {
  from: [number, number];
  to: [number, number];
}

interface GameState {
  game_id: number;
  board: number[][];
  turn: 'white' | 'black';
  status: string;
  game_type: string;
  white_player_id: number;
  black_player_id: number | null;
  legal_moves: Move[];
}

interface OpenGame {
  game_id: number;
  creator: string;
  creator_elo: number;
  created_at: string;
}

type MessageHandler = {
  onConnected?: (data: { user_id: number; username: string }) => void;
  onGameCreated?: (state: GameState) => void;
  onGameStarted?: (state: GameState) => void;
  onGameState?: (state: GameState) => void;
  onGameOver?: (data: { winner: string; winner_id: number | null }) => void;
  onOpenGames?: (data: { games: OpenGame[] }) => void;
  onOpponentDisconnected?: () => void;
  onError?: (message: string) => void;
};

export function useGameSocket(token: string | null, handlers: MessageHandler) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  const tokenRef = useRef(token);

  // Update refs when values change
  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  // Send message
  const send = useCallback((type: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    const currentToken = tokenRef.current;
    if (!currentToken) return;
    
    // Don't reconnect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const ws = new WebSocket(`${WS_URL}?token=${currentToken}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed', event.code, event.reason);
      setIsConnected(false);
      // Only clear ref if this is still our active socket
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error', error);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const { type, data } = message;
      console.log('WebSocket message:', type, data);

      switch (type) {
        case 'connected':
          handlersRef.current.onConnected?.(data);
          break;
        case 'game_created':
          handlersRef.current.onGameCreated?.(data);
          break;
        case 'game_started':
          handlersRef.current.onGameStarted?.(data);
          break;
        case 'game_state':
          handlersRef.current.onGameState?.(data);
          break;
        case 'game_over':
          handlersRef.current.onGameOver?.(data);
          break;
        case 'open_games':
          handlersRef.current.onOpenGames?.(data);
          break;
        case 'opponent_disconnected':
          handlersRef.current.onOpponentDisconnected?.();
          break;
        case 'error':
          handlersRef.current.onError?.(data.message);
          break;
      }
    };
  }, []);

  // Disconnect
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Game actions
  const createGame = useCallback((gameType: 'ai' | 'pvp') => {
    send('create_game', { game_type: gameType });
  }, [send]);

  const joinGame = useCallback((gameId: number) => {
    send('join_game', { game_id: gameId });
  }, [send]);

  const makeMove = useCallback((gameId: number, from: [number, number], to: [number, number]) => {
    send('move', { game_id: gameId, from, to });
  }, [send]);

  const getOpenGames = useCallback(() => {
    send('get_open_games');
  }, [send]);

  const reconnect = useCallback((gameId: number) => {
    send('reconnect', { game_id: gameId });
  }, [send]);

  // Auto-connect when token is available
  useEffect(() => {
    if (token) {
      // Small delay to let React stabilize
      const timer = setTimeout(() => {
        connect();
      }, 100);
      return () => {
        clearTimeout(timer);
        disconnect();
      };
    }
  }, [token, connect, disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    createGame,
    joinGame,
    makeMove,
    getOpenGames,
    reconnect,
  };
}
