export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "bg-green-100 text-green-800 border-green-200",
  negative: "bg-red-100 text-red-800 border-red-200",
  neutral: "bg-gray-100 text-gray-800 border-gray-200",
  mixed: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

export const COLLECTION_TYPE_STYLES: Record<
  string,
  { label: string; className: string }
> = {
  now: {
    label: "Now",
    className: "bg-blue-100 text-blue-800 border-blue-200",
  },
  daily: {
    label: "Today",
    className: "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  weekly: {
    label: "This Week",
    className: "bg-indigo-100 text-indigo-800 border-indigo-200",
  },
  rising: {
    label: "Rising",
    className: "bg-orange-100 text-orange-800 border-orange-200",
  },
};

export const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  stopped: "bg-yellow-100 text-yellow-700",
};
