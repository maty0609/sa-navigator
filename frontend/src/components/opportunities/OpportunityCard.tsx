"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { OpportunityForm, OpportunityFormValues } from "@/components/opportunities/OpportunityForm";
import { useOpportunity, useUpdateOpportunity, Opportunity } from "@/lib/queries";
import { useOpportunityUpdates, useCreateOpportunityUpdate, OpportunityUpdate as OpportunityUpdateType } from "@/lib/queries";
import { Pencil, Send, Loader2 } from "lucide-react";

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

function OpportunityDetails({ opportunity }: { opportunity: Opportunity }) {
  const details = [
    { label: "Client", value: opportunity.client },
    { label: "Project", value: opportunity.project },
    { label: "Owner", value: opportunity.owner },
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
            {link ? (
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

function UpdatesPanel({ opportunityId }: { opportunityId: string }) {
  const { data: updates, isLoading } = useOpportunityUpdates(opportunityId);
  const createUpdate = useCreateOpportunityUpdate();
  const [text, setText] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || createUpdate.isPending) return;
    await createUpdate.mutateAsync({ opportunityId, text: text.trim() });
    setText("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        ) : updates?.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No updates yet. Add the first one below.
          </p>
        ) : (
          updates?.map((update: OpportunityUpdateType) => (
            <div
              key={update.id}
              className="rounded-md border bg-card p-3 space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{update.creator_name}</span>
                <span
                  className="text-xs text-muted-foreground"
                  title={new Date(update.created_at).toLocaleString()}
                >
                  {formatRelativeTime(update.created_at)}
                </span>
              </div>
              <p className="text-sm whitespace-pre-wrap">{update.text}</p>
            </div>
          ))
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
  );
}

export function OpportunityCard({ opportunityId, onClose }: OpportunityCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const { data: opportunity, isLoading } = useOpportunity(opportunityId ?? undefined);
  const updateMutation = useUpdateOpportunity();

  const isOpen = !!opportunityId;

  const handleSave = async (values: OpportunityFormValues) => {
    if (!opportunityId) return;
    await updateMutation.mutateAsync({ id: opportunityId, data: values });
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
        <div className="flex-1 overflow-hidden grid grid-cols-[1fr_340px] divide-x">
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
            <div className="p-4">
              <UpdatesPanel opportunityId={opportunityId} />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
