import type { TransactionStatus } from "../types";

export function StatusBadge({ status }: { status: TransactionStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>;
}
