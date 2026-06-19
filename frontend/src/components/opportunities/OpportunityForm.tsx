"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Opportunity } from "@/lib/queries";

export interface OpportunityFormValues {
  client: string;
  project: string;
  owner: string;
  ccw_estimate: string;
  salesforce_link: string;
  sow_sod: string;
}

interface OpportunityFormProps {
  initialData?: Opportunity;
  onSubmit: (values: OpportunityFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

export function OpportunityForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting,
}: OpportunityFormProps) {
  const [client, setClient] = useState(initialData?.client ?? "");
  const [project, setProject] = useState(initialData?.project ?? "");
  const [owner, setOwner] = useState(initialData?.owner ?? "");
  const [ccwEstimate, setCcwEstimate] = useState(
    initialData?.ccw_estimate ?? "",
  );
  const [salesforceLink, setSalesforceLink] = useState(
    initialData?.salesforce_link ?? "",
  );
  const [sowSod, setSowSod] = useState(initialData?.sow_sod ?? "");

  useEffect(() => {
    if (initialData) {
      setClient(initialData.client);
      setProject(initialData.project);
      setOwner(initialData.owner);
      setCcwEstimate(initialData.ccw_estimate);
      setSalesforceLink(initialData.salesforce_link);
      setSowSod(initialData.sow_sod);
    }
  }, [initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      client: client.trim(),
      project: project.trim(),
      owner: owner.trim(),
      ccw_estimate: ccwEstimate.trim(),
      salesforce_link: salesforceLink.trim(),
      sow_sod: sowSod.trim(),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="client">Client *</Label>
        <Input
          id="client"
          placeholder="e.g. Acme Corp"
          value={client}
          onChange={(e) => setClient(e.target.value)}
          required
          autoFocus={!initialData}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="project">Project *</Label>
        <Input
          id="project"
          placeholder="e.g. ERP Migration"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="owner">Owner *</Label>
        <select
          id="owner"
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          required
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="">Select an owner</option>
          <option value="Harry">Harry</option>
          <option value="Matyas">Matyas</option>
          <option value="Nick">Nick</option>
        </select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="ccw_estimate">CCW Estimate</Label>
        <Input
          id="ccw_estimate"
          placeholder="e.g. https://apps.cisco.com/ccw"
          value={ccwEstimate}
          onChange={(e) => setCcwEstimate(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="salesforce_link">Salesforce Link</Label>
        <Input
          id="salesforce_link"
          placeholder="e.g. https://natilik.lightning.force.com/..."
          value={salesforceLink}
          onChange={(e) => setSalesforceLink(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="sow_sod">SoW/SOD</Label>
        <Input
          id="sow_sod"
          placeholder="e.g. https://..."
          value={sowSod}
          onChange={(e) => setSowSod(e.target.value)}
        />
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : initialData ? "Save Changes" : "Create"}
        </Button>
      </div>
    </form>
  );
}
