export function formatINR(n) {
  if (n === null || n === undefined || n === "") return "₹0";
  const num = Number(n);
  if (Number.isNaN(num)) return "₹0";
  if (num >= 1e7) return `₹${(num / 1e7).toFixed(2)} Cr`;
  if (num >= 1e5) return `₹${(num / 1e5).toFixed(2)} L`;
  return `₹${num.toLocaleString("en-IN")}`;
}

export function formatNumber(n) {
  return Number(n || 0).toLocaleString("en-IN");
}

export function formatDate(d) {
  if (!d) return "—";
  const dt = new Date(d);
  if (Number.isNaN(dt.getTime())) return "—";
  return dt.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export const CITIES = ["Mumbai", "Navi Mumbai", "Thane"];
export const STATUSES = ["Active", "Struck Off", "Under Liquidation"];
export const CLASSES = ["Private", "Public", "One Person Company"];

export const SORT_OPTIONS = [
  { value: "date_of_incorporation", label: "Incorporation date" },
  { value: "paid_up_capital", label: "Paid-up capital" },
  { value: "authorized_capital", label: "Authorized capital" },
  { value: "name", label: "Company name" },
  { value: "data_quality_score", label: "Data quality" },
];
