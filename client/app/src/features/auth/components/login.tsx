import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthContext } from "@/core/auth/auth";
import { Label } from "@radix-ui/react-label";
import { useContext } from "react";

export const LoginPage = () => {
  const { login } = useContext(AuthContext);

  const handleSubmit = (e) => {
    e.preventDefault();
    login();
  };
  return (
    <>
      <div className=" text-white text-lg mb-6">Create an account</div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-medium text-slate-300">
            Email Address
          </Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className="transition-colors duration-300 bg-slate-700 border-slate-600 text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="space-y-2">
          <Label
            htmlFor="password"
            className="text-sm font-medium text-slate-300"
          >
            Password
          </Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            className="transition-colors duration-300 bg-slate-700 border-slate-600 text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center justify-end">
          <Button
            variant="link"
            className="px-0 font-medium text-sm h-auto text-blue-400 hover:text-blue-300"
            type="button"
          >
            Forgot your password?
          </Button>
        </div>

        <Button
          type="submit"
          className="w-full transition-colors duration-300 bg-white hover:bg-slate-400 hover:cursor-pointer text-slate-900 font-medium"
          size="default"
        >
          Sign in
        </Button>
      </form>
    </>
  );
};
