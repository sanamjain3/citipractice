export type TransactionStatus = "PENDING" | "FLAGGED" | "APPROVED" | "REJECTED";

export const STATUSES: TransactionStatus[] = ["PENDING", "FLAGGED", "APPROVED", "REJECTED"];

export interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  currency: string;
  status: TransactionStatus;
  risk_reason: string | null;
  created_at: string;
}

export interface Summary {
  total_count: number;
  pending: number;
  flagged: number;
  approved: number;
  rejected: number;
  total_amount_by_currency: Record<string, number>;
}

export interface NewTransaction {
  account_id: string;
  amount: number;
  currency: string;
}

export type Decision = "approve" | "reject";
