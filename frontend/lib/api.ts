const TOKEN_STORAGE_KEY = "hm_access_token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: number;
  email: string;
  display_name: string | null;
  is_active: boolean;
}

interface ApiErrorPayload {
  detail?: string;
}

export function saveToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorPayload;
      if (typeof body.detail === "string" && body.detail.length > 0) {
        message = body.detail;
      }
    } catch {
      // Non-JSON error body (e.g. backend unreachable proxy response).
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export async function login(
  email: string,
  password: string,
): Promise<Token> {
  return request<Token>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface RegisterInput {
  email: string;
  password: string;
  display_name?: string;
}

export async function register(input: RegisterInput): Promise<UserOut> {
  return request<UserOut>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}