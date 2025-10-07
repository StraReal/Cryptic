import { Button } from "../ui/button";

const button = ({ children }) => {
  return (
    <Button
      type="submit"
      className="w-full font-cd transition-colors duration-300 rounded-xs border-[#050C12] bg-[#B5D5DA] hover:bg-slate-400 hover:cursor-pointer text-slate-900 font-medium"
      size="default"
    >
      {children}
    </Button>
  );
};

export default button;
