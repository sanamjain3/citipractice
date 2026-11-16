import { formatDateTime, formatMoney } from "../format";
import { STATUSES, type Decision, type Transaction, type TransactionStatus } from "../types";
import { StatusBadge } from "./StatusBadge";

type Filter = TransactionStatus | "ALL";

interface Props {
  transactions: Transaction[];
  loading: boolean;
  statusFilter: Filter;
  onStatusFilterChange: (filter: Filter) => void;
  search: string;
  onSearchChange: (value: string) => void;
  busyId: string | null;
  onDecide: (id: string, decision: Decision) => void;
}

const AWAITING_DECISION: TransactionStatus[] = ["PENDING", "FLAGGED"];

export function TransactionTable({
  transactions,
  loading,
  statusFilter,
  onStatusFilterChange,
  search,
  onSearchChange,
  busyId,
  onDecide,
}: Props) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Transactions</h2>
        <div className="filters">
          <input
            type="search"
            placeholder="Search account or ID"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search transactions"
          />
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value as Filter)}
            aria-label="Filter by status"
          >
            <option value="ALL">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0) + s.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Created</th>
              <th>Account</th>
              <th className="num">Amount</th>
              <th>Status</th>
              <th>Risk reason</th>
              <th className="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => {
              const busy = busyId === tx.id;
              return (
                <tr key={tx.id} className={tx.status === "FLAGGED" ? "row-flagged" : undefined}>
                  <td className="muted">{formatDateTime(tx.created_at)}</td>
                  <td>
                    <div className="account">{tx.account_id}</div>
                    <div className="tx-id" title={tx.id}>
                      {tx.id.slice(0, 8)}
                    </div>
                  </td>
                  <td className="num">{formatMoney(tx.amount, tx.currency)}</td>
                  <td>
                    <StatusBadge status={tx.status} />
                  </td>
                  <td className="muted reason">{tx.risk_reason ?? "—"}</td>
                  <td className="actions-col">
                    {AWAITING_DECISION.includes(tx.status) ? (
                      <div className="actions">
                        <button className="btn btn-approve" disabled={busy} onClick={() => onDecide(tx.id, "approve")}>
                          Approve
                        </button>
                        <button className="btn btn-reject" disabled={busy} onClick={() => onDecide(tx.id, "reject")}>
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className="muted">Decided</span>
                    )}
                  </td>
                </tr>
              );
            })}
            {!loading && transactions.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">
                  No transactions match these filters.
                </td>
              </tr>
            )}
            {loading && transactions.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">
                  Loading…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
