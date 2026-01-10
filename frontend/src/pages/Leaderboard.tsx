import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Trophy } from 'lucide-react';
import { leaderboardApi } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface LeaderboardEntry {
  rank: number;
  username: string;
  elo: number;
  games_played: number;
}

export function LeaderboardPage() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const data = await leaderboardApi.get();
        setEntries(data.entries);
      } catch {
        setError('Failed to load leaderboard');
      } finally {
        setIsLoading(false);
      }
    };
    fetchLeaderboard();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <Card>
        <CardHeader className="text-center">
          <Trophy className="w-12 h-12 mx-auto mb-2 text-accent" />
          <CardTitle className="text-2xl">{t('leaderboard.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              {t('common.loading')}
            </div>
          ) : error ? (
            <div className="text-center py-8 text-destructive">
              {error}
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No players yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 text-left font-medium text-muted-foreground">
                      {t('leaderboard.rank')}
                    </th>
                    <th className="py-3 px-4 text-left font-medium text-muted-foreground">
                      {t('leaderboard.player')}
                    </th>
                    <th className="py-3 px-4 text-right font-medium text-muted-foreground">
                      {t('leaderboard.elo')}
                    </th>
                    <th className="py-3 px-4 text-right font-medium text-muted-foreground">
                      {t('leaderboard.games')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.rank} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <span className={
                          entry.rank === 1 ? 'text-yellow-500 font-bold' :
                          entry.rank === 2 ? 'text-gray-400 font-bold' :
                          entry.rank === 3 ? 'text-amber-600 font-bold' : ''
                        }>
                          #{entry.rank}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium">{entry.username}</td>
                      <td className="py-3 px-4 text-right tabular-nums">
                        {Math.round(entry.elo)}
                      </td>
                      <td className="py-3 px-4 text-right tabular-nums text-muted-foreground">
                        {entry.games_played}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
