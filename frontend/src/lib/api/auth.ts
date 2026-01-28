import { apiClient } from "./client";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface OkResponse {
  ok: boolean;
}

export async function login(req: LoginRequest): Promise<OkResponse> {
  const { data } = await apiClient.post("/auth/login", req);
  return data; // { ok: true }
}

export async function register(req: RegisterRequest): Promise<OkResponse> {
  const { data } = await apiClient.post("/auth/register", req);
  return data; // { ok: true }
}

export async function refresh(): Promise<OkResponse> {
  const { data } = await apiClient.post("/auth/refresh");
  return data;
}

export async function logout(): Promise<OkResponse> {
  const { data } = await apiClient.post("/auth/logout");
  return data;
}
