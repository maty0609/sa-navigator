import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Opportunity {
  id: string;
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
  created_by: string;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
}

export type OpportunityStatus =
  | "New"
  | "Documentation in progress"
  | "Waiting on client"
  | "Waiting on sales"
  | "Waiting on engineering"
  | "Won"
  | "Lost";

export const OPPORTUNITY_STATUS_OPTIONS: { value: OpportunityStatus; label: string }[] = [
  { value: "New", label: "New" },
  { value: "Documentation in progress", label: "Documentation in progress" },
  { value: "Waiting on client", label: "Waiting on client" },
  { value: "Waiting on sales", label: "Waiting on sales" },
  { value: "Waiting on engineering", label: "Waiting on engineering" },
  { value: "Won", label: "Won" },
  { value: "Lost", label: "Lost" },
];

export interface OpportunityUpdate {
  id: string;
  text: string;
  opportunity_id: string;
  created_by: string;
  creator_name: string;
  created_at: string;
  edited_at: string | null;
}

export interface OpportunityChangeLog {
  id: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  opportunity_id: string;
  created_by: string;
  creator_name: string;
  created_at: string;
}

export type OpportunityUpdateEntry = OpportunityUpdate | OpportunityChangeLog;

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
}

export interface OpportunityFilters {
  search?: string;
  owner?: string;
  client?: string;
  project?: string;
  status?: OpportunityStatus;
  sort?: string;
  page?: number;
  page_size?: number;
}

// --- Auth Queries ---

export function useLogin() {
  return useMutation<AuthTokens, Error, LoginCredentials>({
    mutationFn: async (credentials) => {
      const response = await api.post("/api/auth/login", credentials);
      return response.data;
    },
  });
}

// --- Opportunity Queries ---

export function useOpportunities(filters: OpportunityFilters = {}) {
  const { search = "", owner, client, project, status, sort = "-created_at", page = 1, page_size = 25 } = filters;

  return useQuery<OpportunityListResponse>({
    queryKey: ["opportunities", { search, owner, client, project, status, sort, page, page_size }],
    queryFn: async () => {
      const response = await api.get("/api/opportunities", {
        params: { search, owner, client, project, status, sort, page, page_size },
      });
      return response.data;
    },
    staleTime: 30_000,
  });
}

export function useOpportunity(id: string | undefined) {
  return useQuery<Opportunity>({
    queryKey: ["opportunity", id],
    queryFn: async () => {
      const response = await api.get(`/api/opportunities/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateOpportunity() {
  const queryClient = useQueryClient();

  return useMutation<Opportunity, Error, Omit<Opportunity, "id" | "created_by" | "created_at" | "updated_at" | "last_activity_at">>({
    mutationFn: async (data) => {
      const response = await api.post("/api/opportunities", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });
}

export function useUpdateOpportunity() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { id: string; data: Partial<Opportunity>; logChanges?: boolean }>({
    mutationFn: async ({ id, data, logChanges }) => {
      const params: Record<string, boolean> = {};
      if (logChanges) params.log_changes = true;
      await api.patch(`/api/opportunities/${id}`, data, { params });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["opportunity"] });
      queryClient.invalidateQueries({ queryKey: ["opportunity_updates"] });
    },
  });
}

export function useDeleteOpportunity() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`/api/opportunities/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });
}

export function useOpportunityUpdates(opportunityId: string | undefined) {
  return useQuery<OpportunityUpdateEntry[]>({
    queryKey: ["opportunity_updates", opportunityId],
    queryFn: async () => {
      const response = await api.get(`/api/opportunities/${opportunityId}/updates`);
      return response.data;
    },
    enabled: !!opportunityId,
  });
}

export function useCreateOpportunityUpdate() {
  const queryClient = useQueryClient();

  return useMutation<OpportunityUpdate, Error, { opportunityId: string; text: string }>({
    mutationFn: async ({ opportunityId, text }) => {
      const response = await api.post(`/api/opportunities/${opportunityId}/updates`, { text });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity_updates"] });
    },
  });
}

export function useUpdateOpportunityUpdate() {
  const queryClient = useQueryClient();

  return useMutation<OpportunityUpdate, Error, { opportunityId: string; updateId: string; text: string }>({
    mutationFn: async ({ opportunityId, updateId, text }) => {
      const response = await api.patch(`/api/opportunities/${opportunityId}/updates/${updateId}`, { text });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity_updates"] });
    },
  });
}

export function useDeleteOpportunityUpdate() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { opportunityId: string; updateId: string }>({
    mutationFn: async ({ opportunityId, updateId }) => {
      await api.delete(`/api/opportunities/${opportunityId}/updates/${updateId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunity_updates"] });
    },
  });
}
