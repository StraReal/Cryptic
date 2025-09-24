import React from "react";
import { chatRooms } from "./data";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Settings, Plus, Sparkles } from "lucide-react";

const RoomCard = ({ room }) => (
  <Card className="cursor-pointer transition-all duration-200 hover:shadow-md hover:scale-[1.01] border bg-slate-800 border-slate-700">
    <CardContent className="flex items-center p-4">
      <span className="text-3xl mr-4">{room.icon}</span>
      <div className="flex-grow">
        <h4 className="text-lg font-medium text-slate-50">{room.name}</h4>
        <p className="text-sm text-slate-400">{room.description}</p>
        <Badge
          variant="secondary"
          className="mt-2 text-xs bg-green-900 text-green-300 border-green-800"
        >
          {room.online} online
        </Badge>
      </div>
    </CardContent>
  </Card>
);

const ChatRoomsPage = () => {
  const customRooms = []; // Example for custom rooms

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 p-6 md:p-10">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="flex justify-between items-center mb-10 pb-4">
          <div>
            <h1 className="text-4xl font-extralight tracking-tight">
              Chat Rooms
            </h1>
            <p className="text-slate-400 mt-1">Welcome, fds!</p>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-slate-400 hover:text-slate-50 transition-colors duration-200"
            >
              <Settings className="h-5 w-5" />
              <span className="sr-only">Settings</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-slate-400 hover:text-slate-50 transition-colors duration-200"
            >
              <Plus className="h-5 w-5" />
              <span className="sr-only">Create Room</span>
            </Button>
          </div>
        </header>

        <Separator className="mb-10 bg-slate-700" />

        {/* Public Rooms Section */}
        <section className="mb-12">
          <h3 className="text-xl font-medium text-slate-50 mb-6">
            Explore Public Rooms
          </h3>
          <div className="grid gap-4">
            {chatRooms.map((room) => (
              <RoomCard key={room.id} room={room} />
            ))}
          </div>
        </section>

        {/* Custom Rooms Section */}
        <section>
          <h3 className="text-xl font-medium text-slate-50 mb-6">
            Your Custom Rooms
          </h3>
          {customRooms.length > 0 ? (
            <div className="grid gap-4">
              {customRooms.map((room) => (
                <RoomCard key={room.id} room={room} />
              ))}
            </div>
          ) : (
            <Card className="border-dashed bg-slate-800 border-slate-600">
              <CardContent className="p-6 text-center text-slate-400">
                <p className="mb-4">No custom rooms yet.</p>
                <Button className="transition-colors duration-200">
                  <Sparkles className="mr-2 h-4 w-4" />
                  Create Your First Room
                </Button>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  );
};

export default ChatRoomsPage;
