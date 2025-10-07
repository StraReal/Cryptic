import React from "react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

const input = ({ label, id, name, type, placeholder, className }) => {
  return (
    <>
      <Label htmlFor={label} className="text-sm  text-slate-300 font-cg">
        {label}
      </Label>
      <Input
        id={id}
        name={name}
        type={type}
        autoComplete="current-password"
        placeholder={placeholder}
        className="transition-colors duration-300 font-cg rounded-xs bg-slate-700 border-slate-600 text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-blue-500"
      />
    </>
  );
};

export default input;
