"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useEffect, useState, createContext, useContext } from "react";
import { DashboardHeader } from "@/components/layout/DashboardHeader";

interface DashboardContextType {
  showAddDialog: boolean;
  setShowAddDialog: (show: boolean) => void;
  selectedOpportunityId: string | null;
  setSelectedOpportunityId: (id: string | null) => void;
}

export const DashboardContext = createContext<DashboardContextType>({
  showAddDialog: false,
  setShowAddDialog: () => {},
  selectedOpportunityId: null,
  setSelectedOpportunityId: () => {},
});

export function useDashboardContext() {
  return useContext(DashboardContext);
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  return (
    <DashboardContext.Provider value={{ showAddDialog, setShowAddDialog, selectedOpportunityId, setSelectedOpportunityId }}>
      <div className="flex min-h-screen flex-col">
        <DashboardHeader onAdd={() => setShowAddDialog(true)} />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </DashboardContext.Provider>
  );
}
