"use client";

import { Button } from "@/components/ui/button";
import { LogOut, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { OpportunityDialog } from "@/components/opportunities/OpportunityDialog";

export function DashboardHeader({ onAdd }: { onAdd: () => void }) {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  };

  return (
    <header className="border-b bg-background">
      <div className="flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold">SA Navigator</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onAdd}>
            <Plus className="mr-1 h-4 w-4" />
            New Opportunity
          </Button>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="mr-1 h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
}
