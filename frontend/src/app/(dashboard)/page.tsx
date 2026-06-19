"use client";

import { OpportunityTable } from "@/components/opportunities/OpportunityTable";
import { OpportunityDialog } from "@/components/opportunities/OpportunityDialog";
import { OpportunityCard } from "@/components/opportunities/OpportunityCard";
import { useDashboardContext } from "@/app/(dashboard)/layout";

export default function DashboardPage() {
  const { showAddDialog, setShowAddDialog, selectedOpportunityId, setSelectedOpportunityId } = useDashboardContext();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Opportunities</h2>
        <p className="text-muted-foreground">Manage your team&apos;s opportunities</p>
      </div>
      <OpportunityTable />
      <OpportunityDialog isOpen={showAddDialog} onClose={() => setShowAddDialog(false)} />
      <OpportunityCard
        opportunityId={selectedOpportunityId}
        onClose={() => setSelectedOpportunityId(null)}
      />
    </div>
  );
}
