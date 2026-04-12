import type { VendorEntry } from "../types/api";

export type CreditStylePreset =
  | "by"
  | "colon"
  | "dash"
  | "handle_only"
  | "custom";

type CreditsEditorProps = {
  entries: VendorEntry[];
  onEntriesChange: (entries: VendorEntry[]) => void;
  preset?: CreditStylePreset;
  onPresetChange?: (preset: CreditStylePreset) => void;
  template?: string;
  onTemplateChange?: (template: string) => void;
  showStyleControls?: boolean;
};

export function parseVendorEntries(
  raw: string | null | undefined,
): VendorEntry[] {
  if (!raw) return [{ role: "", instagram: "" }];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [{ role: "", instagram: "" }];

    const cleaned = parsed
      .filter((item) => typeof item === "object" && item !== null)
      .map((item) => ({
        role:
          typeof (item as { role?: unknown }).role === "string"
            ? (item as { role: string }).role
            : "",
        instagram:
          typeof (item as { instagram?: unknown }).instagram === "string"
            ? (item as { instagram: string }).instagram
            : "",
      }))
      .filter((item) => item.role || item.instagram);

    return cleaned.length ? cleaned : [{ role: "", instagram: "" }];
  } catch {
    return [{ role: "", instagram: "" }];
  }
}

export function serializeVendorEntries(entries: VendorEntry[]): string | null {
  const cleaned = entries
    .map((entry) => ({
      role: entry.role.trim(),
      instagram: entry.instagram.trim(),
    }))
    .filter((entry) => entry.role || entry.instagram);

  return cleaned.length ? JSON.stringify(cleaned) : null;
}

export function presetToTemplate(preset: CreditStylePreset): string {
  switch (preset) {
    case "by":
      return "{role} by {handle}";
    case "colon":
      return "{role}: {handle}";
    case "dash":
      return "{role} — {handle}";
    case "handle_only":
      return "{handle}";
    case "custom":
      return "{role} by {handle}";
    default:
      return "{role} by {handle}";
  }
}

function normalizeRole(role: string): string {
  const trimmed = role.trim();
  if (!trimmed) return "";

  const lower = trimmed.toLowerCase();

  if (lower === "photography" || lower === "photo" || lower === "photos") {
    return "Photos";
  }

  if (lower === "floral" || lower === "florals") {
    return "Florals";
  }

  if (lower === "planner" || lower === "planning") {
    return "Planning";
  }

  return trimmed;
}

export function formatCreditLine(entry: VendorEntry, template: string): string {
  const role = normalizeRole(entry.role);
  const handle = entry.instagram.trim();

  if (!role && !handle) return "";

  const line = template
    .replaceAll("{role}", role)
    .replaceAll("{handle}", handle)
    .replace(/\s+/g, " ")
    .trim();

  if (line === "by" || line === ":" || line === "—") return "";
  return line;
}

export function buildCreditsText(
  entries: VendorEntry[],
  template: string,
): string {
  return entries
    .map((entry) => formatCreditLine(entry, template))
    .filter(Boolean)
    .join("\n");
}

export default function CreditsEditor({
  entries,
  onEntriesChange,
  preset = "by",
  onPresetChange,
  template = "{role} by {handle}",
  onTemplateChange,
  showStyleControls = false,
}: CreditsEditorProps) {
  function updateEntry(index: number, field: keyof VendorEntry, value: string) {
    onEntriesChange(
      entries.map((entry, i) =>
        i === index ? { ...entry, [field]: value } : entry,
      ),
    );
  }

  function addEntry() {
    onEntriesChange([...entries, { role: "", instagram: "" }]);
  }

  function removeEntry(index: number) {
    if (entries.length === 1) {
      onEntriesChange([{ role: "", instagram: "" }]);
      return;
    }

    onEntriesChange(entries.filter((_, i) => i !== index));
  }

  const effectiveTemplate =
    preset === "custom" ? template : presetToTemplate(preset);

  const preview = buildCreditsText(entries, effectiveTemplate);

  return (
    <div className="form-row">
      <label>Credits / collaborators</label>
      <p className="helper-text">
        Optional. Add collaborators the post may credit.
      </p>

      {showStyleControls && onPresetChange && onTemplateChange && (
        <>
          <div className="form-row">
            <label htmlFor="credit-style">Credit Style</label>
            <select
              id="credit-style"
              value={preset}
              onChange={(e) =>
                onPresetChange(e.target.value as CreditStylePreset)
              }
            >
              <option value="by">Role by Handle</option>
              <option value="colon">Role: Handle</option>
              <option value="dash">Role — Handle</option>
              <option value="handle_only">Handle only</option>
              <option value="custom">Custom template</option>
            </select>
          </div>

          {preset === "custom" && (
            <div className="form-row">
              <label htmlFor="credit-template">Custom Credit Template</label>
              <input
                id="credit-template"
                value={template}
                onChange={(e) => onTemplateChange(e.target.value)}
                placeholder="{role} by {handle}"
              />
              <p className="helper-text">
                Use {"{role}"} and {"{handle}"}. Example:{" "}
                {"<3 {role} : {handle} !"}
              </p>
            </div>
          )}

          <div className="form-row">
            <label>Preview</label>
            <textarea readOnly value={preview} />
          </div>
        </>
      )}

      {entries.map((entry, index) => (
        <div key={index} className="approval-action-row">
          <input
            type="text"
            value={entry.role}
            onChange={(e) => updateEntry(index, "role", e.target.value)}
            placeholder="Role / contribution"
            aria-label={`Credit role ${index + 1}`}
          />
          <input
            type="text"
            value={entry.instagram}
            onChange={(e) => updateEntry(index, "instagram", e.target.value)}
            placeholder="Instagram handle"
            aria-label={`Credit handle ${index + 1}`}
          />
          <button
            type="button"
            className="button-danger"
            onClick={() => removeEntry(index)}
          >
            Remove
          </button>
        </div>
      ))}

      <div className="form-actions">
        <button type="button" onClick={addEntry}>
          + Add collaborator
        </button>
      </div>
    </div>
  );
}
