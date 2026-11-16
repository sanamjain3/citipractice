import { formatMoney } from "../format";
import type { Summary, TransactionStatus } from "../types";

type Filter = TransactionStatus | "ALL";

interface Props {
  summary: Summary | null;
  activeFilter: Filter;
  onSelect: (filter: Filter) => void;
}

const CARDS: { filter: Filter; label: string; key: keyof Omit<Summary, "total_amount_by_currency"> }[] = [
  { filter: "ALL", label: "Total", key: "total_count" },
  { filter: "PENDING", label: "Pending", key: "pending" },
  { filter: "FLAGGED", label: "Flagged", key: "flagged" },
  { filter: "APPROVED", label: "Approved", key: "approved" },
  { filter: "REJECTED", label: "Rejected", key: "rejected" },
];

export function SummaryCards({ summary, activeFilter, onSelect }: Props) {
  const volume = summary
    ? Object.entries(summary.total_amount_by_currency)
        .map(([currency, total]) => formatMoney(total, currency))
        .join(" · ")
    : "";

  return (
    <section className="cards" aria-label="Summary">
      {CARDS.map(({ filter, label, key }) => (
        <button
          key={filter}
          type="button"
          className={`card card-${filter.toLowerCase()}${activeFilter === filter ? " active" : ""}`}
          onClick={() => onSelect(filter)}
          aria-pressed={activeFilter === filter}
        >
          <span className="card-label">{label}</span>
          <span className="card-value">{summary ? summary[key] : "–"}</span>
          {filter === "ALL" && volume && <span className="card-sub">{volume}</span>}
          {filter === "FLAGGED" && <span className="card-sub">Over 10,000, needs review</span>}
        </button>
      ))}
    </section>
  );
}
