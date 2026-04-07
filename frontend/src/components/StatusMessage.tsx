type StatusMessageProps = {
  status?: string;
  error?: string;
};

export default function StatusMessage({ status, error }: StatusMessageProps) {
  return (
    <>
      <p role="status" aria-live="polite">
        {status || ""}
      </p>
      <p role="alert">{error || ""}</p>
    </>
  );
}
