import type { Decision, NewTransaction, Summary, Transaction, TransactionStatus } from "./types";

const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response));
  }
  return (await response.json()) as T;
}

// FastAPI returns {detail: string} for HTTP errors and {detail: [{msg}]} for validation errors.
async function errorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join("; ");
  } catch {
    // not JSON
  }
  return `${response.status} ${response.statusText}`;
}

export const api = {
  listTransactions(status?: TransactionStatus) {
    const query = status ? `?status=${status}` : "";
    return request<Transaction[]>(`/api/transactions${query}`);
  },
  getSummary() {
    return request<Summary>("/api/transactions/summary");
  },
  createTransaction(body: NewTransaction) {
    return request<Transaction>("/api/transactions", { method: "POST", body: JSON.stringify(body) });
  },
  decide(id: string, decision: Decision) {
    return request<Transaction>(`/api/transactions/${encodeURIComponent(id)}/${decision}`, { method: "POST" });
  },
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return "Cannot reach the API. Is the backend running on port 8000?";
  return error instanceof Error ? error.message : String(error);
}
