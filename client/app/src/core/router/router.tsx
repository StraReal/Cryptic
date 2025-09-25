import { createBrowserRouter, Navigate } from "react-router";
import { AuthContext, RequireAuth } from "../auth/auth";
import MainPage from "@/features/main/components/main";
import ChatRoomsPage from "@/features/browse/components/browse";
import { useContext } from "react";
import AuthPage from "@/features/auth/components/auth-view";

// Router configuration
export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPageWrapper />,
  },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      {
        index: true, // This makes it the default route for "/"
        element: <MainPage />,
      },
      {
        path: "browse",
        element: <ChatRoomsPage />,
      },
    ],
  },
  {
    // Catch-all route - redirect to login if no match
    path: "*",
    element: <Navigate to="/login" replace />,
  },
]);

// Updated Login Page wrapper to handle navigation
function LoginPageWrapper() {
  const { isAuthenticated } = useContext(AuthContext);

  // If already authenticated, redirect to home
  if (isAuthenticated) {
    return <Navigate to="/browse" replace />;
  }

  return <AuthPage />;
}
