type ListToolbarProps = {
  searchId: string;
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;

  sortId: string;
  sortValue: string;
  onSortChange: (value: string) => void;
  sortOptions: { value: string; label: string }[];

  rightContent?: React.ReactNode;
};

export default function ListToolbar({
  searchId,
  searchValue,
  onSearchChange,
  searchPlaceholder,

  sortId,
  sortValue,
  onSortChange,
  sortOptions,

  rightContent,
}: ListToolbarProps) {
  return (
    <div className="approval-action-row asset-library-controls">
      <div className="form-row">
        <label htmlFor={searchId}>Search</label>
        <input
          id={searchId}
          type="search"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder}
        />
      </div>

      <div className="form-row">
        <label htmlFor={sortId}>Sort</label>
        <select
          id={sortId}
          value={sortValue}
          onChange={(e) => onSortChange(e.target.value)}
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {rightContent && (
        <div className="schedule-toolbar-right">{rightContent}</div>
      )}
    </div>
  );
}
