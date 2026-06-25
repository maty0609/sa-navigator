"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { OpportunityForm, OpportunityFormValues } from "@/components/opportunities/OpportunityForm";
import { useOpportunity, useUpdateOpportunity, Opportunity, OPPORTUNITY_STATUS_OPTIONS, OpportunityStatus } from "@/lib/queries";
import { useOpportunityUpdates, useCreateOpportunityUpdate, useUpdateOpportunityUpdate, useDeleteOpportunityUpdate, OpportunityUpdateEntry, OpportunityChangeLog, OpportunityUpdate } from "@/lib/queries";
import { Pencil, Send, Loader2, X, Check, Trash2 } from "lucide-react";

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

interface OpportunityCardProps {
  opportunityId: string | null;
  onClose: () => void;
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function formatValue(value: string | number | null, format: "currency" | "percent" | "date" | "plain"): string {
  if (value == null || value === "") return "—";
  if (format === "currency") {
    return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(Number(value));
  }
  if (format === "percent") {
    return `${Number(value)}%`;
  }
  if (format === "date" && typeof value === "string") {
    const d = new Date(value + "T00:00:00");
    if (!isNaN(d.getTime())) return d.toLocaleDateString();
    return value;
  }
  return String(value);
}

function OpportunityDetails({ opportunity }: { opportunity: Opportunity }) {
  const details = [
    { label: "Client", value: opportunity.client },
    { label: "Project", value: opportunity.project },
    { label: "Owner", value: opportunity.owner },
    { label: "Status", value: opportunity.status },
    {
      label: "CCW Estimate",
      value: opportunity.ccw_estimate || "—",
      link: opportunity.ccw_estimate || null,
    },
    {
      label: "Salesforce",
      value: opportunity.salesforce_link || "—",
      link: opportunity.salesforce_link || null,
    },
    {
      label: "SoW/SOD",
      value: opportunity.sow_sod || "—",
      link: opportunity.sow_sod || null,
    },
    {
      label: "Total TCV",
      value: formatValue(opportunity.total_tcv, "currency"),
    },
    {
      label: "Total BGP",
      value: formatValue(opportunity.total_bgp, "currency"),
    },
    {
      label: "Total Margin",
      value: formatValue(opportunity.total_margin, "percent"),
    },
    {
      label: "Account Mgr",
      value: opportunity.account_manager || "—",
    },
    {
      label: "Close Date",
      value: formatValue(opportunity.close_date, "date"),
    },
    {
      label: "Created",
      value: new Date(opportunity.created_at).toLocaleString(),
    },
    {
      label: "Updated",
      value: new Date(opportunity.updated_at).toLocaleString(),
    },
  ];

  return (
    <div className="space-y-4">
      {details.map(({ label, value, link }) => (
        <div key={label} className="grid grid-cols-[120px_1fr] gap-2 items-start">
          <Label className="text-muted-foreground text-sm">{label}</Label>
          <span className="text-sm break-words">
            {label === "Status" ? (
              <StatusBadge status={value as OpportunityStatus} />
            ) : link ? (
              <a
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline underline-offset-2 hover:text-primary/80"
              >
                {value}
              </a>
            ) : (
              value
            )}
          </span>
        </div>
      ))}
    </div>
  );
}

const FIELD_LABELS: Record<string, string> = {
  client: "Client",
  project: "Project",
  owner: "Owner",
  ccw_estimate: "CCW Estimate",
  salesforce_link: "Salesforce Link",
  sow_sod: "SoW/SOD",
  total_tcv: "Total TCV",
  total_bgp: "Total BGP",
  total_margin: "Total Margin",
  account_manager: "Account Manager",
  close_date: "Close Date",
  status: "Status",
};

function isChangeLog(entry: OpportunityUpdateEntry): entry is OpportunityChangeLog {
  return "field_name" in entry;
}

function ConfirmDialog({ open, onClose, onConfirm, title, message }: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
}) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="pt-1">{message}</DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" size="sm" onClick={onConfirm}>
            Delete
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function UpdatesPanel({ opportunityId }: { opportunityId: string }) {
  const { data: entries, isLoading } = useOpportunityUpdates(opportunityId);
  const createUpdate = useCreateOpportunityUpdate();
  const updateUpdate = useUpdateOpportunityUpdate();
  const deleteUpdate = useDeleteOpportunityUpdate();

  const [text, setText] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<{ id: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || createUpdate.isPending) return;
    await createUpdate.mutateAsync({ opportunityId, text: text.trim() });
    setText("");
  };

  const handleEdit = (entry: OpportunityUpdate) => {
    setEditingId(entry.id);
    setEditText(entry.text);
  };

  const handleSaveEdit = async (entry: OpportunityUpdate) => {
    if (!editText.trim()) return;
    await updateUpdate.mutateAsync({
      opportunityId,
      updateId: entry.id,
      text: editText.trim(),
    });
    setEditingId(null);
    setEditText("");
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditText("");
  };

  const handleDelete = (entry: OpportunityUpdate) => {
    setDeleteTarget({ id: entry.id });
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    await deleteUpdate.mutateAsync({
      opportunityId,
      updateId: deleteTarget.id,
    });
    setDeleteTarget(null);
  };

  const handleCloseDelete = () => {
    setDeleteTarget(null);
  };

  return (
    <>
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={handleCloseDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Comment"
        message="Are you sure you want to delete this comment? This action cannot be undone."
      />
      <div className="flex flex-col">
        <div className="space-y-3 pr-1">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          ) : entries?.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No updates yet. Add the first one below.
            </p>
          ) : (
            entries?.map((entry: OpportunityUpdateEntry) =>
              isChangeLog(entry) ? (
                /* Field change log — visually distinct: left border accent, compact */
                <div
                  key={entry.id}
                  className="rounded-md border-l-4 border-l-blue-500 bg-blue-50/50 p-3 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{entry.creator_name}</span>
                    <span
                      className="text-xs text-muted-foreground"
                      title={new Date(entry.created_at).toLocaleString()}
                    >
                      {formatRelativeTime(entry.created_at)}
                    </span>
                  </div>
                  <p className="text-sm">
                    <span className="font-medium">
                      {FIELD_LABELS[entry.field_name] ?? entry.field_name}
                    </span>
                    {entry.old_value != null ? (
                      <>
                        <span className="text-muted-foreground mx-1">:</span>
                        <span className="line-through text-muted-foreground text-xs">
                          {entry.old_value}
                        </span>
                        <span className="text-muted-foreground mx-1">→</span>
                        <span className="font-medium text-green-700 text-xs">
                          {entry.new_value ?? "—"}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="text-muted-foreground mx-1">:</span>
                        <span className="font-medium text-green-700 text-xs">
                          {entry.new_value ?? "—"}
                        </span>
                      </>
                    )}
                  </p>
                </div>
              ) : (
                /* Manual text update — with edit/delete controls */
                <div
                  key={entry.id}
                  className="rounded-md border bg-card p-3 space-y-1.5 group"
                >
                  {editingId === entry.id ? (
                    /* In-place editing mode */
                    <>
                      <Textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        rows={3}
                        className="resize-none text-sm"
                      />
                      <div className="flex justify-end gap-1.5">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={handleCancelEdit}
                          disabled={updateUpdate.isPending}
                          className="h-7 text-xs px-2.5"
                        >
                          Cancel
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => handleSaveEdit(entry)}
                          disabled={!editText.trim() || updateUpdate.isPending}
                          className="h-7 text-xs px-2.5"
                        >
                          {updateUpdate.isPending ? (
                            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                          ) : (
                            <Check className="mr-1 h-3 w-3" />
                          )}
                          Save
                        </Button>
                      </div>
                    </>
                  ) : (
                    /* Normal display mode */
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{entry.creator_name}</span>
                        <div className="flex items-center gap-1">
                          <span
                            className="text-xs text-muted-foreground"
                            title={new Date(entry.created_at).toLocaleString()}
                          >
                            {formatRelativeTime(entry.created_at)}
                            {entry.edited_at ? " (edited)" : null}
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(entry)}
                            className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-accent"
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(entry)}
                            className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{entry.text}</p>
                    </>
                  )}
                </div>
              )
            )
          )}
        </div>

        <form onSubmit={handleSubmit} className="mt-3 space-y-2 pt-3 border-t">
          <Textarea
            placeholder="Write an update..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            className="resize-none"
          />
          <div className="flex justify-end">
            <Button
              type="submit"
              size="sm"
              disabled={!text.trim() || createUpdate.isPending}
            >
              {createUpdate.isPending ? (
                <>
                  <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                  Posting...
                </>
              ) : (
                <>
                  <Send className="mr-1 h-3.5 w-3.5" />
                  Post Update
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}

export function OpportunityCard({ opportunityId, onClose }: OpportunityCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const { data: opportunity, isLoading } = useOpportunity(opportunityId ?? undefined);
  const updateMutation = useUpdateOpportunity();

  const isOpen = !!opportunityId;

  const handleSave = async (values: OpportunityFormValues) => {
    if (!opportunityId) return;
    await updateMutation.mutateAsync({ id: opportunityId, data: values, logChanges: true });
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleClose = () => {
    setIsEditing(false);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-5xl max-h-[90vh] flex flex-col p-0 gap-0 overflow-hidden">
        {/* Header */}
        <DialogHeader className="px-6 py-4 border-b flex flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            <DialogTitle>Opportunity</DialogTitle>
            {opportunity && !isEditing && (
              <Badge variant="secondary">{opportunity.client} — {opportunity.project}</Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            {opportunity && !isEditing && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(true)}
                className="h-8"
              >
                <Pencil className="h-3.5 w-3.5 mr-1" />
                Edit
              </Button>
            )}
            {isEditing && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancelEdit}
                  disabled={updateMutation.isPending}
                  className="h-8"
                >
                  Cancel
                </Button>
                <span className="text-xs text-muted-foreground px-2">
                  Editing
                </span>
              </>
            )}
          </div>
        </DialogHeader>

        {/* Body */}
        <div className="flex-1 overflow-hidden grid grid-cols-[320px_1fr] grid-rows-[1fr] divide-x">
          {/* Left: Details or Edit Form */}
          <div className="p-6 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : isEditing && opportunity ? (
              <OpportunityForm
                initialData={opportunity}
                onSubmit={handleSave}
                onCancel={handleCancelEdit}
                isSubmitting={updateMutation.isPending}
              />
            ) : opportunity ? (
              <OpportunityDetails opportunity={opportunity} />
            ) : null}
          </div>

          {/* Right: Updates */}
          {opportunityId && (
            <div className="p-4 h-full overflow-y-auto">
              <UpdatesPanel opportunityId={opportunityId} />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
