import { useState, createContext, useContext } from "react";
import LoginPage from "./features/auth/components/login";
import ChatRoomsPage from "./features/browse/components/browse";
import MainPage from "./features/main/components/main";
import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
  Outlet,
} from "react-router";
import { AuthContext, AuthProvider, RequireAuth } from "./core/auth/auth";

// Updated Login Page wrapper to handle navigation
function LoginPageWrapper() {
  const { isAuthenticated } = useContext(AuthContext);

  // If already authenticated, redirect to home
  if (isAuthenticated) {
    return <Navigate to="/browse" replace />;
  }

  return <LoginPage />;
}

// Router configuration
const router = createBrowserRouter([
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

function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
