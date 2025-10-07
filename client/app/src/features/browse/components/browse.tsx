import React, { useState, useMemo } from "react";
import { chatRooms } from "./data";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import {
  Settings,
  Plus,
  Sparkles,
  Search,
  Filter,
  Grid,
  List,
} from "lucide-react";
import { useNavigate } from "react-router";

const RoomCard = ({ room, viewMode }) => (
  <Card className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border bg-slate-800 border-slate-700 hover:border-slate-600">
    <CardContent
      className={`flex items-center ${viewMode === "grid" ? "p-4" : "p-3"}`}
    >
      <span
        className={`${
          viewMode === "grid" ? "text-2xl mr-3" : "text-xl mr-2"
        } flex-shrink-0`}
      >
        {room.icon}
      </span>
      <div className="flex-grow min-w-0">
        <h4
          className={`font-medium text-slate-50 truncate ${
            viewMode === "grid" ? "text-base" : "text-sm"
          }`}
        >
          {room.name}
        </h4>
        <p
          className={`text-slate-400 truncate ${
            viewMode === "grid" ? "text-sm" : "text-xs"
          }`}
        >
          {room.description}
        </p>
        <Badge
          variant="secondary"
          className="mt-1 text-xs bg-green-900/50 text-green-300 border-green-800/50 px-2 py-0"
        >
          {room.online}
        </Badge>
      </div>
    </CardContent>
  </Card>
);

const ChatRoomsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [viewMode, setViewMode] = useState("grid"); // 'grid' or 'list'
  const [showFilters, setShowFilters] = useState(false);
  const customRooms = [];

  // Get unique categories from rooms
  const categories = useMemo(() => {
    const cats = [
      "all",
      ...new Set(chatRooms.map((room) => room.category || "general")),
    ];
    return cats;
  }, []);

  // Filter and search rooms
  const filteredRooms = useMemo(() => {
    return chatRooms.filter((room) => {
      const matchesSearch =
        room.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        room.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory =
        selectedCategory === "all" ||
        (room.category || "general") === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50">
      {/* Fixed Header */}
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto p-4">
          {/* Main Header */}
          <header className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-extralight tracking-tight">
                Chat Rooms
              </h1>
              <p className="text-slate-400 text-sm">Welcome back</p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowFilters(!showFilters)}
                className="text-slate-400 hover:text-slate-50"
              >
                <Filter className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() =>
                  setViewMode(viewMode === "grid" ? "list" : "grid")
                }
                className="text-slate-400 hover:text-slate-50"
              >
                {viewMode === "grid" ? (
                  <List className="h-4 w-4" />
                ) : (
                  <Grid className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-400 hover:text-slate-50"
              >
                <Settings className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-400 hover:text-slate-50"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </header>

          {/* Search Bar */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 h-4 w-4" />
            <Input
              placeholder="Search rooms..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-slate-800 border-slate-700 text-slate-50 placeholder:text-slate-400 focus:border-blue-500"
            />
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mb-4 p-4 bg-slate-800 rounded-lg border border-slate-700">
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <Button
                    key={category}
                    variant={
                      selectedCategory === category ? "default" : "outline"
                    }
                    size="sm"
                    onClick={() => setSelectedCategory(category)}
                    className={`text-xs capitalize ${
                      selectedCategory === category
                        ? "bg-blue-600 text-white"
                        : "bg-transparent border-slate-600 text-slate-300 hover:bg-slate-700"
                    }`}
                  >
                    {category}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 pb-8">
        {/* Results Info */}
        <div className="flex justify-between items-center mb-6">
          <p className="text-slate-400 text-sm">
            {filteredRooms.length} room{filteredRooms.length !== 1 ? "s" : ""}{" "}
            found
          </p>
        </div>

        {/* Public Rooms Grid/List */}
        <section className="mb-8">
          <h3 className="text-xl font-medium text-slate-50 mb-4">
            Public Rooms
          </h3>

          {filteredRooms.length > 0 ? (
            <div
              className={`grid gap-3 ${
                viewMode === "grid"
                  ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "grid-cols-1 max-w-4xl"
              }`}
              onClick={() => navigate("/chat/1")}
            >
              {filteredRooms.map((room) => (
                <RoomCard key={room.id} room={room} viewMode={viewMode} />
              ))}
            </div>
          ) : (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-8 text-center text-slate-400">
                <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="mb-2">No rooms found</p>
                <p className="text-sm">Try adjusting your search or filters</p>
              </CardContent>
            </Card>
          )}
        </section>

        {/* Custom Rooms Section */}
        <section>
          <h3 className="text-xl font-medium text-slate-50 mb-4">Your Rooms</h3>

          {customRooms.length > 0 ? (
            <div
              className={`grid gap-3 ${
                viewMode === "grid"
                  ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "grid-cols-1 max-w-4xl"
              }`}
            >
              {customRooms.map((room) => (
                <RoomCard key={room.id} room={room} viewMode={viewMode} />
              ))}
            </div>
          ) : (
            <Card className="border-dashed bg-slate-800/50 border-slate-600">
              <CardContent className="p-6 text-center text-slate-400">
                <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="mb-2">No custom rooms yet</p>
                <p className="text-sm mb-4">
                  Create your first room to get started
                </p>
                <Button className="transition-colors duration-200 bg-blue-600 hover:bg-blue-700">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Room
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
