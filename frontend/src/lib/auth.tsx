import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authApi } from './api';

interface User {
  id: number;
  username: string;
  email: string;
  elo: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const userData = await authApi.getMe();
          setUser(userData);
        } catch {
          // Token invalid, clear it
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setIsLoading(false);
    };
    loadUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    const newToken = response.access_token;
    localStorage.setItem('token', newToken);
    setToken(newToken);
    const userData = await authApi.getMe();
    setUser(userData);
  };

  const signup = async (username: string, email: string, password: string) => {
    const response = await authApi.signup(username, email, password);
    const newToken = response.access_token;
    localStorage.setItem('token', newToken);
    setToken(newToken);
    const userData = await authApi.getMe();
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
