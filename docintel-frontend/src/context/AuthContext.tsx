/**
 * Global auth state: current user, login/register/logout actions.
 * Wraps the whole app so any component can call useAuth().
 */
import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { api, tokenStorage } from "@/lib/api";
import type { User, LoginPayload, RegisterPayload } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const restoreSession = async () => {
      const token = tokenStorage.getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const { data } = await api.get<User>("/auth/me");
        setUser(data);
      } catch {
        tokenStorage.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = async (payload: LoginPayload) => {
    const { data } = await api.post("/auth/login", payload);
    tokenStorage.setTokens(data.access_token, data.refresh_token);
    const { data: userData } = await api.get<User>("/auth/me");
    setUser(userData);
  };

  const register = async (payload: RegisterPayload) => {
    const { data } = await api.post("/auth/register", payload);
    tokenStorage.setTokens(data.access_token, data.refresh_token);
    const { data: userData } = await api.get<User>("/auth/me");
    setUser(userData);
  };

  const logout = () => {
    tokenStorage.clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
