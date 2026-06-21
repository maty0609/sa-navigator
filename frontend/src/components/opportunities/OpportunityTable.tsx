"use client";

import { useState } from "react";
import { useOpportunities, useDeleteOpportunity, Opportunity, OPPORTUNITY_STATUS_OPTIONS, OpportunityStatus } from "@/lib/queries";
import { useDashboardContext } from "@/app/(dashboard)/layout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Trash2, Pencil, Search, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { OpportunityDialog } from "@/components/opportunities/OpportunityDialog";

type SortField = "client" | "project" | "owner" | "account_manager" | "created_at" | "updated_at";

const statusBadgeVariants: Record<string, string> = {
  "New": "bg-blue-100 text-blue-700 hover:bg-blue-100",
  "Documentation in progress": "bg-yellow-100 text-yellow-700 hover:bg-yellow-100",
  "Waiting on client": "bg-orange-100 text-orange-700 hover:bg-orange-100",
  "Waiting on sales": "bg-purple-100 text-purple-700 hover:bg-purple-100",
  "Waiting on engineering": "bg-pink-100 text-pink-700 hover:bg-pink-100",
  "Won": "bg-green-100 text-green-700 hover:bg-green-100",
  "Lost": "bg-red-100 text-red-700 hover:bg-red-100",
};

function StatusBadge({ status }: { status: OpportunityStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadgeVariants[status] || "bg-gray-100 text-gray-700"}`}>
      {OPPORTUNITY_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status}
    </span>
  );
}

export function OpportunityTable() {
  const { setSelectedOpportunityId } = useDashboardContext();
  const [search, setSearch] = useState("");
  const [client, setClient] = useState("");
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<OpportunityStatus | "">("");
  const [editItem, setEditItem] = useState<Opportunity | null>(null);

  const sort = sortDir === "desc" ? `-${sortField}` : sortField;
  const { data, isLoading, isFetching } = useOpportunities({
    search,
    client,
    status: statusFilter || undefined,
    sort,
    page,
    page_size: 25,
  });
  const deleteMutation = useDeleteOpportunity();

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this opportunity?")) {
      await deleteMutation.mutateAsync(id);
      // Close card if the deleted opportunity is currently being viewed
      setSelectedOpportunityId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search opportunities..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-8"
          />
        </div>
        <Input
          placeholder="Filter by client..."
          value={client}
          onChange={(e) => { setClient(e.target.value); setPage(1); }}
          className="max-w-xs"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as OpportunityStatus | ""); setPage(1); }}
          className="flex h-9 w-[180px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="">All statuses</option>
          {OPPORTUNITY_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">
                <button className="flex items-center gap-1" onClick={() => handleSort("client")}>
                  Client {sortField === "client" && (sortDir === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead className="w-[200px]">
                <button className="flex items-center gap-1" onClick={() => handleSort("project")}>
                  Project {sortField === "project" && (sortDir === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead className="w-[150px]">
                <button className="flex items-center gap-1" onClick={() => handleSort("owner")}>
                  Owner {sortField === "owner" && (sortDir === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead className="w-[150px]">
                <button className="flex items-center gap-1" onClick={() => handleSort("account_manager")}>
                  Account Mgr {sortField === "account_manager" && (sortDir === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead className="w-[130px]">Status</TableHead>
              <TableHead className="w-[120px]">
                <button className="flex items-center gap-1" onClick={() => handleSort("created_at")}>
                  Created {sortField === "created_at" && (sortDir === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                  No opportunities found
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((opp) => (
                <TableRow
                  key={opp.id}
                  className="cursor-pointer"
                  onClick={() => setSelectedOpportunityId(opp.id)}
                >
                  <TableCell className="font-medium">{opp.client}</TableCell>
                  <TableCell className="max-w-xs truncate">{opp.project}</TableCell>
                  <TableCell>{opp.owner}</TableCell>
                  <TableCell>{opp.account_manager || "—"}</TableCell>
                  <TableCell>
                    <StatusBadge status={opp.status} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(opp.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => { e.stopPropagation(); setEditItem(opp); }}
                        className="h-8 w-8"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => { e.stopPropagation(); handleDelete(opp.id); }}
                        disabled={deleteMutation.isPending}
                        className="h-8 w-8 text-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total > 25 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {(page - 1) * 25 + 1}–{Math.min(page * 25, data.total)} of {data.total}
          </p>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page * 25 >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Edit dialog */}
      {editItem && (
        <OpportunityDialog
          isOpen={!!editItem}
          onClose={() => setEditItem(null)}
          initialData={editItem}
        />
      )}

      {/* Loading overlay */}
      {isFetching && (
        <div className="fixed inset-0 z-50 bg-background/50 pointer-events-none" />
      )}
    </div>
  );
}
