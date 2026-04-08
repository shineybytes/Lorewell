type StatusMessageProps = {
  status?: string;
  error?: string;
  loading?: boolean;
};

export default function StatusMessage({
  status,
  error,
  loading = false,
}: StatusMessageProps) {
  return (
    <div className="status-stack">
      <p role="status" aria-live="polite" className="status-message">
        {loading ? `⏳ ${status || "Working..."}` : status || ""}
      </p>
      <p role="alert" className="error-message">
        {error || ""}
      </p>
    </div>
  );
}
