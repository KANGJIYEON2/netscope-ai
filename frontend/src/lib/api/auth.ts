import { apiClient } from "./client";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  tenant_id: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export async function login(req: LoginRequest): Promise<AuthResponse> {
  const { data } = await apiClient.post("/auth/login", req);
  return data;
}

export async function register(req: RegisterRequest): Promise<AuthResponse> {
  const { data } = await apiClient.post("/auth/register", req);
  return data;
}
