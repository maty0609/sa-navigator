"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Opportunity, OPPORTUNITY_STATUS_OPTIONS, OpportunityStatus } from "@/lib/queries";

export interface OpportunityFormValues {
  client: string;
  project: string;
  owner: string;
  ccw_estimate: string;
  salesforce_link: string;
  sow_sod: string;
  total_tcv: number | null;
  total_bgp: number | null;
  total_margin: number | null;
  account_manager: string;
  close_date: string;
  status: OpportunityStatus;
}

interface OpportunityFormProps {
  initialData?: Opportunity;
  onSubmit: (values: OpportunityFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

/** Format a number as GBP currency string */
function formatGBP(value: number | null): string {
  if (value == null) return "";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 2,
  }).format(value);
}

/** Parse a GBP-formatted string or plain number string back to a number, or null */
function parseGBP(input: string): number | null {
  const trimmed = input.trim();
  if (!trimmed) return null;
  const cleaned = trimmed.replace(/[£,]/g, "").trim();
  const num = parseFloat(cleaned);
  return isNaN(num) ? null : num;
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
  const [totalTcv, setTotalTcv] = useState<number | null>(
    initialData?.total_tcv ?? null,
  );
  const [totalBgp, setTotalBgp] = useState<number | null>(
    initialData?.total_bgp ?? null,
  );
  const [totalMargin, setTotalMargin] = useState<number | null>(
    initialData?.total_margin ?? null,
  );
  const [accountManager, setAccountManager] = useState(
    initialData?.account_manager ?? "",
  );
  const [closeDate, setCloseDate] = useState(initialData?.close_date ?? "");
  const [status, setStatus] = useState<OpportunityStatus>(
    initialData?.status ?? "New",
  );

  // Display strings for formatted inputs
  const [tcvDisplay, setTcvDisplay] = useState<string>(
    initialData?.total_tcv != null ? formatGBP(initialData.total_tcv) : "",
  );
  const [bgpDisplay, setBgpDisplay] = useState<string>(
    initialData?.total_bgp != null ? formatGBP(initialData.total_bgp) : "",
  );
  const [marginDisplay, setMarginDisplay] = useState<string>(
    initialData?.total_margin != null ? String(initialData.total_margin) : "",
  );

  useEffect(() => {
    if (initialData) {
      setClient(initialData.client);
      setProject(initialData.project);
      setOwner(initialData.owner);
      setCcwEstimate(initialData.ccw_estimate);
      setSalesforceLink(initialData.salesforce_link);
      setSowSod(initialData.sow_sod);
      setTotalTcv(initialData.total_tcv);
      setTotalBgp(initialData.total_bgp);
      setTotalMargin(initialData.total_margin);
      setTcvDisplay(
        initialData.total_tcv != null ? formatGBP(initialData.total_tcv) : "",
      );
      setBgpDisplay(
        initialData.total_bgp != null ? formatGBP(initialData.total_bgp) : "",
      );
      setMarginDisplay(
        initialData.total_margin != null ? String(initialData.total_margin) : "",
      );
      setAccountManager(initialData.account_manager);
      setCloseDate(initialData.close_date);
      setStatus(initialData.status ?? "New");
    }
  }, [initialData]);

  // Format GBP fields as user types, parse back on blur
  const handleTcvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const parsed = parseGBP(raw);
    setTcvDisplay(raw);
    setTotalTcv(parsed);
  };
  const handleBgpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const parsed = parseGBP(raw);
    setBgpDisplay(raw);
    setTotalBgp(parsed);
  };

  const handleMarginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const num = parseFloat(raw);
    setMarginDisplay(raw);
    setTotalMargin(isNaN(num) ? null : num);
  };

  const handleTcvBlur = () => {
    if (totalTcv != null) {
      setTcvDisplay(formatGBP(totalTcv));
    }
  };
  const handleBgpBlur = () => {
    if (totalBgp != null) {
      setBgpDisplay(formatGBP(totalBgp));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Final parse on submit to ensure clean values
    const tcvFinal = parseGBP(tcvDisplay);
    const bgpFinal = parseGBP(bgpDisplay);
    const marginFinal = marginDisplay.trim() ? parseFloat(marginDisplay) : null;

    await onSubmit({
      client: client.trim(),
      project: project.trim(),
      owner: owner.trim(),
      ccw_estimate: ccwEstimate.trim(),
      salesforce_link: salesforceLink.trim(),
      sow_sod: sowSod.trim(),
      total_tcv: tcvFinal,
      total_bgp: bgpFinal,
      total_margin: isNaN(marginFinal as number) ? null : marginFinal,
      account_manager: accountManager.trim(),
      close_date: closeDate,
      status,
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
      <div className="space-y-2">
        <Label htmlFor="total_tcv">Total TCV (GBP)</Label>
        <Input
          id="total_tcv"
          placeholder="e.g. 150,000"
          value={tcvDisplay}
          onChange={handleTcvChange}
          onBlur={handleTcvBlur}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="total_bgp">Total BGP (GBP)</Label>
        <Input
          id="total_bgp"
          placeholder="e.g. 45,000"
          value={bgpDisplay}
          onChange={handleBgpChange}
          onBlur={handleBgpBlur}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="total_margin">Total Margin (%)</Label>
        <Input
          id="total_margin"
          type="number"
          step="0.1"
          placeholder="e.g. 70"
          value={marginDisplay}
          onChange={handleMarginChange}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="account_manager">Account Manager</Label>
        <Input
          id="account_manager"
          placeholder="e.g. John Smith"
          value={accountManager}
          onChange={(e) => setAccountManager(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="close_date">Close Date</Label>
        <Input
          id="close_date"
          type="date"
          value={closeDate}
          onChange={(e) => setCloseDate(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          value={status}
          onChange={(e) => setStatus(e.target.value as OpportunityStatus)}
          className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        >
          {OPPORTUNITY_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
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
