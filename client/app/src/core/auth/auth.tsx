import { createContext, useContext, useState } from "react";
import { Navigate, Outlet } from "react-router";

// Create Auth Context
export const AuthContext = createContext({
  isAuthenticated: false,
  login: () => {},
  logout: () => {},
});

// Auth Provider Component
export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = () => {
    setIsAuthenticated(true);
  };

  const logout = () => {
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Protected Route Component
export function RequireAuth() {
  const { isAuthenticated } = useContext(AuthContext);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
