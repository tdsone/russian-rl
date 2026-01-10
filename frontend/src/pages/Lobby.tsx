import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Users, RefreshCw } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { useGameSocket } from '@/hooks/useGameSocket';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface OpenGame {
  game_id: number;
  creator: string;
  creator_elo: number;
  created_at: string;
}

export function LobbyPage() {
  const { t } = useTranslation();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [openGames, setOpenGames] = useState<OpenGame[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [waitingGameId, setWaitingGameId] = useState<number | null>(null);

  const handlers = {
    onGameCreated: useCallback((state: { game_id: number; status: string }) => {
      setIsCreating(false);
      if (state.status === 'waiting') {
        setWaitingGameId(state.game_id);
      } else {
        // AI game starts immediately
        navigate(`/game/${state.game_id}`);
      }
    }, [navigate]),
    onGameStarted: useCallback((state: { game_id: number }) => {
      navigate(`/game/${state.game_id}`);
    }, [navigate]),
    onOpenGames: useCallback((data: { games: OpenGame[] }) => {
      setOpenGames(data.games);
    }, []),
    onError: useCallback((message: string) => {
      console.error('WebSocket error:', message);
      setIsCreating(false);
    }, []),
  };

  const { isConnected, createGame, joinGame, getOpenGames } = useGameSocket(token, handlers);

  // Fetch open games on connect
  useEffect(() => {
    if (isConnected) {
      getOpenGames();
    }
  }, [isConnected, getOpenGames]);

  const handleCreateAIGame = () => {
    setIsCreating(true);
    createGame('ai');
  };

  const handleCreatePvPGame = () => {
    setIsCreating(true);
    createGame('pvp');
  };

  const handleJoinGame = (gameId: number) => {
    joinGame(gameId);
  };

  const handleRefresh = () => {
    getOpenGames();
  };

  const handleCancelWaiting = () => {
    setWaitingGameId(null);
  };

  if (!user) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">{t('game.title')}</h1>
        <p className="text-muted-foreground">{t('game.subtitle')}</p>
      </div>

      {/* Waiting for opponent overlay */}
      {waitingGameId && (
        <Card className="mb-8 border-primary">
          <CardContent className="py-8 text-center">
            <div className="animate-pulse mb-4">
              <Users className="w-12 h-12 mx-auto text-primary" />
            </div>
            <p className="text-lg font-medium mb-2">{t('game.waitingForOpponent')}</p>
            <p className="text-sm text-muted-foreground mb-4">Game ID: {waitingGameId}</p>
            <Button variant="outline" onClick={handleCancelWaiting}>
              {t('common.cancel')}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create game buttons */}
      {!waitingGameId && (
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          <Card className="hover:border-primary transition-colors cursor-pointer" onClick={handleCreateAIGame}>
            <CardHeader className="text-center">
              <Bot className="w-12 h-12 mx-auto mb-2 text-primary" />
              <CardTitle>{t('game.vsAI')}</CardTitle>
              <CardDescription>
                Play against a computer opponent
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button disabled={isCreating || !isConnected}>
                {isCreating ? t('common.loading') : t('game.createGame')}
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:border-primary transition-colors cursor-pointer" onClick={handleCreatePvPGame}>
            <CardHeader className="text-center">
              <Users className="w-12 h-12 mx-auto mb-2 text-accent" />
              <CardTitle>{t('game.vsPvP')}</CardTitle>
              <CardDescription>
                Play against another player online
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button variant="secondary" disabled={isCreating || !isConnected}>
                {isCreating ? t('common.loading') : t('game.createGame')}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Open games list */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{t('game.openGames')}</CardTitle>
            <CardDescription>Join a game created by another player</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={!isConnected}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent>
          {openGames.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {t('game.noOpenGames')}
            </p>
          ) : (
            <div className="space-y-2">
              {openGames.map((game) => (
                <div
                  key={game.game_id}
                  className="flex items-center justify-between p-4 rounded-lg border hover:border-primary transition-colors"
                >
                  <div>
                    <p className="font-medium">{game.creator}</p>
                    <p className="text-sm text-muted-foreground">
                      ELO: {Math.round(game.creator_elo)}
                    </p>
                  </div>
                  <Button onClick={() => handleJoinGame(game.game_id)}>
                    {t('game.joinGame')}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Connection status */}
      {!isConnected && (
        <p className="text-center text-muted-foreground mt-4">
          Connecting to server...
        </p>
      )}
    </div>
  );
}
