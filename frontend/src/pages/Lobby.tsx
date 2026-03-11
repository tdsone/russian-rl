import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Users, RefreshCw } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { useGameSocket } from '@/hooks/useGameSocket';
import { agentsApi, type AgentInfo } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface OpenGame {
  game_id: number;
  creator: string;
  creator_elo: number;
  created_at: string;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  Easy: 'bg-green-100 text-green-800',
  Medium: 'bg-amber-100 text-amber-800',
  Hard: 'bg-red-100 text-red-800',
};

export function LobbyPage() {
  const { t } = useTranslation();
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [openGames, setOpenGames] = useState<OpenGame[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('random');

  const handlers = {
    onGameCreated: useCallback((state: { game_id: number; status: string }) => {
      setIsCreating(false);
      // Navigate to game page for both AI and PvP games
      // For PvP games in "waiting" status, the Game page will show "waiting for opponent"
      navigate(`/game/${state.game_id}`);
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

  // Fetch agents list
  useEffect(() => {
    agentsApi.list().then(setAgents).catch(console.error);
  }, []);

  // Fetch open games on connect
  useEffect(() => {
    if (isConnected) {
      getOpenGames();
    }
  }, [isConnected, getOpenGames]);

  const handleCreateAIGame = () => {
    setIsCreating(true);
    createGame('ai', selectedAgent);
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

  if (!user) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">{t('game.title')}</h1>
        <p className="text-muted-foreground">{t('game.subtitle')}</p>
      </div>

      {/* Create game buttons */}
      <div className="grid md:grid-cols-2 gap-4 mb-8">
          <Card>
            <CardHeader className="text-center">
              <Bot className="w-12 h-12 mx-auto mb-2 text-primary" />
              <CardTitle>{t('game.vsAI')}</CardTitle>
              <CardDescription>
                Choose an opponent and start playing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 mb-4">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedAgent === agent.id
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-muted-foreground/30'
                    }`}
                  >
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-muted-foreground">{agent.description}</p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${DIFFICULTY_COLORS[agent.difficulty] ?? 'bg-gray-100 text-gray-800'}`}>
                      {agent.difficulty}
                    </span>
                  </div>
                ))}
              </div>
              <div className="text-center">
                <Button onClick={handleCreateAIGame} disabled={isCreating || !isConnected}>
                  {isCreating ? t('common.loading') : t('game.createGame')}
                </Button>
              </div>
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
