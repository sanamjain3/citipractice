import { useState, type FormEvent } from "react";
import { errorMessage } from "../api";
import { formatMoney } from "../format";
import type { NewTransaction, Transaction } from "../types";

const CURRENCIES = ["USD", "EUR", "GBP", "INR", "JPY"];
const FLAG_THRESHOLD = 10000;

interface Props {
  onSubmit: (data: NewTransaction) => Promise<Transaction>;
}

export function TransactionForm({ onSubmit }: Props) {
  const [accountId, setAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Transaction | null>(null);

  const numericAmount = Number(amount);
  const willFlag = amount !== "" && numericAmount > FLAG_THRESHOLD;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!accountId.trim()) return setError("Account ID is required.");
    if (!(numericAmount > 0)) return setError("Amount must be greater than 0.");

    setSubmitting(true);
    try {
      const created = await onSubmit({ account_id: accountId.trim(), amount: numericAmount, currency });
      setResult(created);
      setAmount("");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>New transaction</h2>
      </div>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <label>
          Account ID
          <input value={accountId} onChange={(e) => setAccountId(e.target.value)} placeholder="ACC-1001" maxLength={64} />
        </label>
        <label>
          Amount
          <input
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
          />
        </label>
        <label>
          Currency
          <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
            {CURRENCIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>

        <p className={`hint${willFlag ? " hint-warn" : ""}`}>
          {willFlag
            ? "This amount is over 10,000 and will be flagged for review."
            : "Amounts over 10,000 are flagged for review automatically."}
        </p>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Submitting…" : "Submit transaction"}
        </button>

        {error && (
          <p className="message message-error" role="alert">
            {error}
          </p>
        )}
        {result && (
          <p className="message message-ok" role="status">
            Created {formatMoney(result.amount, result.currency)} for {result.account_id}, status{" "}
            <strong>{result.status}</strong>.
          </p>
        )}
      </form>
    </section>
  );
}
