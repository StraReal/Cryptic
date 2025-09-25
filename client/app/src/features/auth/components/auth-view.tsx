import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TabsContent } from "@radix-ui/react-tabs";
import { LoginPage } from "./login";
import GuestPage from "./guest";

const AuthPage = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[#050C12] p-4">
      <Tabs defaultValue="guest" className="w-[400px]">
        <Card className=" w-2/3 max-w-1/3 min-w-sm rounded-sm shadow-lg bg-[#063346]">
          <CardHeader className="pb-4">
            <TabsList className="">
              <TabsTrigger value="guest">Guest</TabsTrigger>
              <TabsTrigger value="account">Account</TabsTrigger>
            </TabsList>
          </CardHeader>
          <CardContent>
            <TabsContent value="guest">
              <GuestPage />
            </TabsContent>
            <TabsContent value="account">
              <LoginPage />
            </TabsContent>
          </CardContent>
        </Card>
      </Tabs>
    </div>
  );
};

export default AuthPage;
