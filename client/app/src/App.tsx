import { RouterProvider } from "react-router";
import { AuthProvider } from "./core/auth/auth";
import { router } from "./core/router/router";

function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
