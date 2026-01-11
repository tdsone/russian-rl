import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Users } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { useGameSocket } from '@/hooks/useGameSocket';
import { GameBoard } from '@/components/GameBoard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

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

export function GamePage() {
  const { t } = useTranslation();
  const { gameId } = useParams<{ gameId: string }>();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [gameOver, setGameOver] = useState<{ winner: string; winnerId: number | null } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlers = {
    onGameCreated: useCallback((state: GameState) => {
      setGameState(state);
    }, []),
    onGameStarted: useCallback((state: GameState) => {
      setGameState(state);
    }, []),
    onGameState: useCallback((state: GameState) => {
      setGameState(state);
    }, []),
    onGameOver: useCallback((data: { winner: string; winner_id: number | null }) => {
      setGameOver({ winner: data.winner, winnerId: data.winner_id });
    }, []),
    onOpponentDisconnected: useCallback(() => {
      setError('Opponent disconnected');
    }, []),
    onError: useCallback((message: string) => {
      setError(message);
    }, []),
  };

  const { isConnected, makeMove, reconnect } = useGameSocket(token, handlers);

  // Reconnect to game when component mounts
  useEffect(() => {
    if (isConnected && gameId) {
      reconnect(parseInt(gameId));
    }
  }, [isConnected, gameId, reconnect]);

  const handleMove = useCallback((from: [number, number], to: [number, number]) => {
    if (gameId) {
      makeMove(parseInt(gameId), from, to);
    }
  }, [gameId, makeMove]);

  const handlePlayAgain = () => {
    navigate('/lobby');
  };

  if (!user) {
    return null;
  }

  // Determine player's color
  const myColor: 'white' | 'black' = gameState?.white_player_id === user.id ? 'white' : 'black';
  const isMyTurn = gameState?.turn === myColor && gameState?.status === 'active';
  const isWaiting = gameState?.status === 'waiting';

  // Determine if player won
  const didWin = gameOver && (
    (gameOver.winner === 'white' && gameState?.white_player_id === user.id) ||
    (gameOver.winner === 'black' && gameState?.black_player_id === user.id)
  );

  // Handle leaving game while waiting
  const handleCancelWaiting = () => {
    navigate('/lobby');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col items-center">
        {/* Waiting for opponent */}
        {isWaiting && (
          <Card className="mb-6 w-full max-w-md border-primary">
            <CardContent className="py-8 text-center">
              <div className="animate-pulse mb-4">
                <Users className="w-12 h-12 mx-auto text-primary" />
              </div>
              <p className="text-lg font-medium mb-2">{t('game.waitingForOpponent')}</p>
              <p className="text-sm text-muted-foreground mb-4">Game ID: {gameId}</p>
              <Button variant="outline" onClick={handleCancelWaiting}>
                {t('common.cancel')}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Game status */}
        {!isWaiting && (
          <Card className="mb-6 w-full max-w-md">
            <CardHeader className="py-4">
              <CardTitle className="text-center text-lg">
                {gameOver ? (
                  <span className={didWin ? 'text-green-600' : 'text-red-600'}>
                    {didWin ? t('game.youWin') : t('game.youLose')}
                  </span>
                ) : (
                  <span>
                    {isMyTurn ? t('game.yourTurn') : t('game.opponentTurn')}
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            {!gameOver && gameState && (
              <CardContent className="py-2 text-center text-sm text-muted-foreground">
                <p>
                  {t('game.turn')}: {gameState.turn === 'white' ? t('game.white') : t('game.black')} | 
                  You: {myColor === 'white' ? t('game.white') : t('game.black')}
                </p>
                {gameState.game_type === 'ai' && (
                  <p className="text-xs mt-1">Playing against AI</p>
                )}
              </CardContent>
            )}
          </Card>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg">
            {error}
          </div>
        )}

        {/* Game board */}
        {!isWaiting && (
          gameState ? (
            <GameBoard
              board={gameState.board}
              legalMoves={gameState.legal_moves}
              isMyTurn={isMyTurn}
              myColor={myColor}
              onMove={handleMove}
            />
          ) : (
            <div className="w-96 h-96 flex items-center justify-center bg-muted rounded-lg">
              <p className="text-muted-foreground">{t('common.loading')}</p>
            </div>
          )
        )}

        {/* Game over actions */}
        {gameOver && (
          <div className="mt-6">
            <Button onClick={handlePlayAgain} size="lg">
              {t('game.playAgain')}
            </Button>
          </div>
        )}

        {/* Instructions */}
        {!isWaiting && !gameOver && gameState && isMyTurn && (
          <p className="mt-4 text-sm text-muted-foreground">
            {t('game.selectPiece')}
          </p>
        )}
      </div>
    </div>
  );
}
