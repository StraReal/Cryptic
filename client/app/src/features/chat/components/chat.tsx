import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  CheckCheck,
  Home,
  Layers,
  Plus,
  SearchIcon,
  Settings,
  User,
  UserSquare,
} from "lucide-react";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import React from "react";

const ChatPage = () => {
  return (
    <div className=" grid grid-cols-12 h-screen bg-[#050C12]">
      <div className=" items-center pt-10 gap-4 border col-span-1 bg-[#B5D5DA] flex flex-col">
        <Home />
        <Plus />
        <UserSquare />
      </div>
      <div className="border flex flex-col col-span-3 bg-[#063346]">
        <div className=" items-center p-4 text-white">
          <InputGroup className=" text-white">
            <InputGroupInput
              className="text-white placeholder:text-white"
              placeholder="Search..."
            />
            <InputGroupAddon>
              <SearchIcon className="text-white" />
            </InputGroupAddon>
          </InputGroup>
        </div>
        <div className="  flex-1 flex flex-col my-4 mx-1 text-white">
          <div className=" text-black justify-between items-center rounded-md bg-[#B5D5DA] w-full h-12 gap-1 flex">
            {" "}
            <div className=" flex gap-2 items-center ml-2">
              <User />{" "}
              <div className=" flex flex-col">
                <p className=" text-sm">UserName</p>
                <p className=" text-xs">Hi this is charan</p>
              </div>
            </div>
            <p className=" text-xs mr-2">20:51</p>
          </div>
        </div>
      </div>
      <div className="border col-span-8 flex flex-col mx-1  bg-[#050C12]">
        <div className=" justify-between h-16 bg-[#063346] rounded-xl flex items-center px-4">
          <div className=" flex gap-2 text-white">
            <User />
            <p>UserName</p>
          </div>
          <div className=" flex text-white gap-4">
            <Layers />
            <Settings />
          </div>
        </div>
        <div className=" flex-1 text-white overflow-y-auto py-4 px-1 flex flex-col gap-4">
          {/* Received Message */}
          <div className="flex flex-col w-fit justify-start">
            <div className="max-w-xs bg-[#063346] text-white p-2  rounded-lg relative">
              Hello how are you doing this is just a test
            </div>
            <div className="flex justify-start text-xs mt-1 text-gray-400">
              <p>20:51</p>
              <CheckCheck size={16} />
            </div>
          </div>
          {/* Received Message */}
          <div className="flex flex-col w-fit justify-start">
            <div className="max-w-xs bg-[#063346] text-white p-2  rounded-lg relative">
              Hello how are you doing this is just a test
            </div>
            <div className="flex justify-start text-xs mt-1 text-gray-400">
              <p>20:51</p>
              <CheckCheck size={16} />
            </div>
          </div>
          {/* Sent Message */}
          <div className="flex flex-col w-fit ml-auto justify-end">
            <div className="max-w-xs bg-[#B5D5DA] text-black p-2 rounded-lg relative">
              Hello how are you doing this is just a test
            </div>
            <div className="flex justify-end text-xs mt-1 text-gray-400">
              <p>20:51</p>
              <CheckCheck size={16} />
            </div>
          </div>
          {/* Sent Message */}
          <div className="flex flex-col w-fit ml-auto justify-end">
            <div className="max-w-xs bg-[#B5D5DA] text-black p-2 rounded-lg relative">
              Hello how are you doing this is just a test
            </div>
            <div className="flex justify-end text-xs mt-1 text-gray-400">
              <p>20:51</p>
              <CheckCheck size={16} />
            </div>
          </div>
        </div>
        <div className=" h-16 text-white p-2">
          <div className="flex gap-2 items-center">
            <Input className="flex-1" placeholder="Message" />
            <Button>Send</Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
