export function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(amount);
  } catch {
    // Unknown ISO code: fall back to a plain number.
    return `${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })} ${currency}`;
  }
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
