"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { OpportunityForm, OpportunityFormValues } from "@/components/opportunities/OpportunityForm";
import { useCreateOpportunity, useUpdateOpportunity, Opportunity } from "@/lib/queries";

interface OpportunityDialogProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: Opportunity;
}

export function OpportunityDialog({ isOpen, onClose, initialData }: OpportunityDialogProps) {
  const createMutation = useCreateOpportunity();
  const updateMutation = useUpdateOpportunity();

  const isEdit = !!initialData;

  const handleSubmit = async (values: OpportunityFormValues) => {
    try {
      if (isEdit && initialData) {
        await updateMutation.mutateAsync({ id: initialData.id, data: values });
      } else {
        await createMutation.mutateAsync(values);
      }
      onClose();
    } catch {
      // Error is handled by React Query mutation (shows in browser console)
      // The mutation will retry or you can add a toast notification here
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Opportunity" : "New Opportunity"}</DialogTitle>
        </DialogHeader>
        <OpportunityForm
          initialData={initialData}
          onSubmit={handleSubmit}
          onCancel={onClose}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      </DialogContent>
    </Dialog>
  );
}
