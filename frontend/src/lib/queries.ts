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
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface OpportunityUpdate {
  id: string;
  text: string;
  opportunity_id: string;
  created_by: string;
  creator_name: string;
  created_at: string;
}

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
  const { search = "", owner, client, project, sort = "-created_at", page = 1, page_size = 25 } = filters;

  return useQuery<OpportunityListResponse>({
    queryKey: ["opportunities", { search, owner, client, project, sort, page, page_size }],
    queryFn: async () => {
      const response = await api.get("/api/opportunities", {
        params: { search, owner, client, project, sort, page, page_size },
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

  return useMutation<Opportunity, Error, Omit<Opportunity, "id" | "created_by" | "created_at" | "updated_at">>({
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

  return useMutation<void, Error, { id: string; data: Partial<Opportunity> }>({
    mutationFn: async ({ id, data }) => {
      await api.patch(`/api/opportunities/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["opportunity"] });
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
  return useQuery<OpportunityUpdate[]>({
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
