const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  pending: "Starting...",
  fetching: "Fetching Reddit posts...",
  analyzing: "AI is analyzing trends...",
  completed: "Completed",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  pending: "bg-blue-100 text-blue-700",
  fetching: "bg-yellow-100 text-yellow-700",
  analyzing: "bg-purple-100 text-purple-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const ACTIVE_STATUSES = ["queued", "pending", "fetching", "analyzing"];

export function StatusBadge({ status }: { status: string }) {
  const isActive = ACTIVE_STATUSES.includes(status);

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status] || "bg-gray-100 text-gray-700"}`}
    >
      {isActive && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-current" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
        </span>
      )}
      {STATUS_LABELS[status] || status}
    </span>
  );
}
