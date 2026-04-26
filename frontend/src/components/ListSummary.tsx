type ListSummaryProps = {
  visibleCount: number;
  totalCount: number;
  noun: string;
  query?: string;
};

export default function ListSummary({
  visibleCount,
  totalCount,
  noun,
  query = "",
}: ListSummaryProps) {
  return (
    <p className="helper-text asset-library-summary">
      Showing {visibleCount} of {totalCount} {noun}
      {query.trim() ? ` for "${query.trim()}"` : ""}.
    </p>
  );
}
