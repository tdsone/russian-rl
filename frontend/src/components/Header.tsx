import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Globe, LogOut, Trophy, Gamepad2 } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';

export function Header() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'ru' : 'en';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="border-b bg-card">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">У</span>
          </div>
          <span className="font-semibold text-lg">{t('game.title')}</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-2">
          {user && (
            <>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/lobby">
                  <Gamepad2 className="w-4 h-4 mr-1" />
                  {t('nav.play')}
                </Link>
              </Button>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/leaderboard">
                  <Trophy className="w-4 h-4 mr-1" />
                  {t('nav.leaderboard')}
                </Link>
              </Button>
            </>
          )}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Language toggle */}
          <Button variant="ghost" size="icon" onClick={toggleLanguage} title="Toggle language">
            <Globe className="w-5 h-5" />
            <span className="ml-1 text-xs font-medium">{i18n.language.toUpperCase()}</span>
          </Button>

          {/* User info / Auth */}
          {user ? (
            <div className="flex items-center gap-3">
              <div className="text-sm">
                <span className="font-medium">{user.username}</span>
                <span className="text-muted-foreground ml-2">ELO: {Math.round(user.elo)}</span>
              </div>
              <Button variant="ghost" size="icon" onClick={handleLogout} title={t('auth.logout')}>
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/login">{t('auth.login')}</Link>
              </Button>
              <Button size="sm" asChild>
                <Link to="/signup">{t('auth.signup')}</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
