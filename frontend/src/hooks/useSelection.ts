import { useMemo, useState } from "react";

export function useSelection<T extends string | number>() {
  const [selectedIds, setSelectedIds] = useState<T[]>([]);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  function isSelected(id: T) {
    return selectedSet.has(id);
  }

  function toggle(id: T) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id],
    );
  }

  function selectAll(ids: T[]) {
    setSelectedIds((prev) => Array.from(new Set([...prev, ...ids])));
  }

  function deselect(ids: T[]) {
    const idSet = new Set(ids);
    setSelectedIds((prev) => prev.filter((id) => !idSet.has(id)));
  }

  function clear() {
    setSelectedIds([]);
  }

  function retainOnly(ids: T[]) {
    const allowed = new Set(ids);
    setSelectedIds((prev) => prev.filter((id) => allowed.has(id)));
  }

  return {
    selectedIds,
    selectedSet,
    isSelected,
    toggle,
    selectAll,
    deselect,
    clear,
    retainOnly,
  };
}
