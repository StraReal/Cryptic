import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthContext } from "@/core/auth/auth";
import { Label } from "@radix-ui/react-label";
import React, { useContext } from "react";

const GuestPage = () => {
  const { login } = useContext(AuthContext);

  const handleSubmit = (e) => {
    e.preventDefault();
    login();
  };
  return (
    <>
      {" "}
      <div className=" text-white text-lg mb-6 font-cd font-medium">
        Enter as guest
      </div>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="username" className="text-sm  text-slate-300 font-cg">
            Username
          </Label>
          <Input
            id="username"
            name="username"
            type="text"
            autoComplete="current-password"
            placeholder="YourUsername"
            className="transition-colors duration-300 font-cg rounded-xs bg-slate-700 border-slate-600 text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-blue-500"
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
          className="w-full font-cd transition-colors duration-300 rounded-xs border-[#050C12] bg-[#B5D5DA] hover:bg-slate-400 hover:cursor-pointer text-slate-900 font-medium"
          size="default"
        >
          Sign in
        </Button>
      </form>
    </>
  );
};

export default GuestPage;
