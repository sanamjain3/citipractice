import { useCallback, useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "./api";
import { SummaryCards } from "./components/SummaryCards";
import { TransactionForm } from "./components/TransactionForm";
import { TransactionTable } from "./components/TransactionTable";
import type { Decision, NewTransaction, Summary, Transaction, TransactionStatus } from "./types";

type Filter = TransactionStatus | "ALL";

export default function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [statusFilter, setStatusFilter] = useState<Filter>("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [list, totals] = await Promise.all([
        api.listTransactions(statusFilter === "ALL" ? undefined : statusFilter),
        api.getSummary(),
      ]);
      setTransactions(list);
      setSummary(totals);
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const visible = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return transactions;
    return transactions.filter((t) => t.account_id.toLowerCase().includes(term) || t.id.startsWith(term));
  }, [transactions, search]);

  async function handleDecide(id: string, decision: Decision) {
    setBusyId(id);
    try {
      await api.decide(id, decision);
      await refresh();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate(data: NewTransaction) {
    const created = await api.createTransaction(data);
    await refresh();
    return created;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Payment Approvals</h1>
          <p className="muted">Review, approve and reject incoming transactions.</p>
        </div>
        <button className="btn" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      {error && (
        <div className="banner" role="alert">
          {error}
          <button className="banner-close" onClick={() => setError(null)} aria-label="Dismiss">
            ×
          </button>
        </div>
      )}

      <SummaryCards summary={summary} activeFilter={statusFilter} onSelect={setStatusFilter} />

      <main className="layout">
        <TransactionTable
          transactions={visible}
          loading={loading}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          search={search}
          onSearchChange={setSearch}
          busyId={busyId}
          onDecide={handleDecide}
        />
        <TransactionForm onSubmit={handleCreate} />
      </main>
    </div>
  );
}
