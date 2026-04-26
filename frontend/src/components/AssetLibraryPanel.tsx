import { useEffect, useMemo, useState } from "react";
import {
  applyAssetAnalysis,
  proposeAssetAnalysis,
  reanalyzeAsset,
  renameAsset,
  updateAssetEvent,
} from "../api/assets";
import type {
  AssetAnalysisProposalResponse,
  AssetRecord,
  EventRecord,
} from "../types/api";
import AssetCard from "./AssetCard";
import StatusMessage from "./StatusMessage";
import { useAsyncState } from "../hooks/useAsyncState";
import { useSelection } from "../hooks/useSelection";

type MediaTab = "all" | "image" | "video";
type AssetSortMode = "newest" | "oldest" | "name_asc" | "name_desc";

type AssetLibraryPanelProps = {
  assets: AssetRecord[];
  events: EventRecord[];
  onRefresh: () => Promise<void>;
};

function filenameFromPath(filePath: string) {
  return filePath.split("/").pop() || filePath;
}

function displayAssetName(asset: AssetRecord) {
  return asset.display_name || filenameFromPath(asset.file_path);
}

function sortName(asset: AssetRecord) {
  return displayAssetName(asset).toLowerCase();
}

function normalizeAnalysisStatus(status: string | null | undefined) {
  const normalized = (status || "").toLowerCase();

  switch (normalized) {
    case "pending":
      return { label: "Pending", className: "status-pending" };
    case "analyzed":
      return { label: "Analyzed", className: "status-analyzed" };
    case "approved":
      return { label: "Approved", className: "status-approved" };
    case "failed":
      return { label: "Failed", className: "status-failed" };
    default:
      return {
        label: normalized || "Unknown",
        className: "",
      };
  }
}

export default function AssetLibraryPanel({
  assets,
  events,
  onRefresh,
}: AssetLibraryPanelProps) {
  const [filterEventId, setFilterEventId] = useState<string>("all");
  const [mediaTab, setMediaTab] = useState<MediaTab>("all");
  const [sortMode, setSortMode] = useState<AssetSortMode>("newest");
  const [assetSearch, setAssetSearch] = useState("");
  const [expandedAssetId, setExpandedAssetId] = useState<number | null>(null);

  const [proposalByAssetId, setProposalByAssetId] = useState<
    Record<number, AssetAnalysisProposalResponse>
  >({});
  const [draftProposalEdits, setDraftProposalEdits] = useState<
    Record<number, { visual: string; accessibility: string }>
  >({});
  const [draftNames, setDraftNames] = useState<Record<number, string>>({});

  const loadState = useAsyncState();
  const analyzeSelectedState = useAsyncState();

  const selection = useSelection<number>();

  useEffect(() => {
    setDraftNames((prev) => {
      const next = { ...prev };
      for (const asset of assets) {
        if (!(asset.id in next)) {
          next[asset.id] = displayAssetName(asset);
        }
      }
      return next;
    });

    selection.retainOnly(assets.map((asset) => asset.id));
  }, [assets]);

  const eventsById = useMemo(() => {
    return new Map(events.map((event) => [event.id, event]));
  }, [events]);

  const filteredAssets = useMemo(() => {
    let result = [...assets];

    if (filterEventId === "unassigned") {
      result = result.filter((asset) => asset.event_id == null);
    } else if (filterEventId !== "all") {
      const numeric = Number(filterEventId);
      result = result.filter((asset) => asset.event_id === numeric);
    }

    if (mediaTab === "image") {
      result = result.filter((asset) => asset.media_type === "image");
    } else if (mediaTab === "video") {
      result = result.filter((asset) => asset.media_type === "video");
    }

    const query = assetSearch.trim().toLowerCase();

    if (query) {
      result = result.filter((asset) => {
        const displayName = displayAssetName(asset).toLowerCase();
        const filename = filenameFromPath(asset.file_path).toLowerCase();
        const eventTitle =
          asset.event_id != null
            ? (eventsById.get(asset.event_id)?.title ?? "").toLowerCase()
            : "";
        const mediaType = asset.media_type.toLowerCase();
        const analysisStatus = asset.analysis_status.toLowerCase();

        return (
          displayName.includes(query) ||
          filename.includes(query) ||
          eventTitle.includes(query) ||
          mediaType.includes(query) ||
          analysisStatus.includes(query)
        );
      });
    }

    result.sort((a, b) => {
      switch (sortMode) {
        case "oldest":
          return (
            new Date(a.created_at ?? "").getTime() -
            new Date(b.created_at ?? "").getTime()
          );
        case "name_asc":
          return sortName(a).localeCompare(sortName(b));
        case "name_desc":
          return sortName(b).localeCompare(sortName(a));
        case "newest":
        default:
          return (
            new Date(b.created_at ?? "").getTime() -
            new Date(a.created_at ?? "").getTime()
          );
      }
    });

    return result;
  }, [assets, filterEventId, mediaTab, sortMode, assetSearch, eventsById]);

  const visibleAssetIds = useMemo(
    () => filteredAssets.map((asset) => asset.id),
    [filteredAssets],
  );

  const selectablePendingAssets = useMemo(
    () =>
      filteredAssets.filter(
        (asset) =>
          normalizeAnalysisStatus(asset.analysis_status).label === "Pending",
      ),
    [filteredAssets],
  );

  function toggleExpandedAsset(id: number) {
    setExpandedAssetId((current) => (current === id ? null : id));
  }

  function selectAllVisibleAssets() {
    selection.selectAll(visibleAssetIds);
  }

  function deselectVisibleAssets() {
    selection.deselect(visibleAssetIds);
  }

  function selectPendingAssets() {
    selection.selectAll(selectablePendingAssets.map((asset) => asset.id));
  }

  async function handleAnalyzeSelected() {
    if (selection.selectedIds.length === 0) {
      analyzeSelectedState.fail("No assets selected.");
      return;
    }

    const selectedAssets = assets.filter((asset) =>
      selection.selectedSet.has(asset.id),
    );

    analyzeSelectedState.start(
      selectedAssets.length === 1
        ? "Analyzing 1 selected asset..."
        : `Analyzing ${selectedAssets.length} selected assets...`,
    );

    let successCount = 0;
    let failureCount = 0;

    for (const asset of selectedAssets) {
      try {
        await reanalyzeAsset(asset.id, "");
        successCount += 1;
      } catch (err) {
        console.error(err);
        failureCount += 1;
      }
    }

    await onRefresh();

    if (failureCount === 0) {
      analyzeSelectedState.succeed(
        successCount === 1
          ? "1 selected asset analyzed."
          : `${successCount} selected assets analyzed.`,
      );
      return;
    }

    if (successCount === 0) {
      analyzeSelectedState.fail("All selected asset analyses failed.");
      return;
    }

    analyzeSelectedState.succeed(
      `${successCount} analyzed, ${failureCount} failed.`,
    );
  }

  return (
    <section aria-labelledby="asset-library-heading">
      <div className="page-header">
        <div>
          <h3 id="asset-library-heading">Asset Library</h3>
          <p className="helper-text">
            Search, filter, sort, select, and expand assets on demand.
          </p>
        </div>
      </div>

      <div className="asset-library-legend helper-text">
        <span>
          <strong>Unassigned</strong>: no event is currently linked
        </span>
        <span>
          <strong className="status-pending">Pending</strong>: not analyzed yet
        </span>
        <span>
          <strong className="status-analyzed">Analyzed</strong>: analysis is
          available
        </span>
        <span>
          <strong className="status-approved">Approved</strong>: accessibility
          has been finalized
        </span>
        <span>
          <strong className="status-failed">Failed</strong>: the last analysis
          attempt did not succeed
        </span>
      </div>

      <div className="approval-action-row asset-library-controls">
        <div className="form-row">
          <label htmlFor="asset-search">Search</label>
          <input
            id="asset-search"
            type="search"
            value={assetSearch}
            onChange={(e) => setAssetSearch(e.target.value)}
            placeholder="Search name, filename, event, type, or status"
          />
        </div>

        <div className="form-row">
          <label htmlFor="asset-filter">Filter by Event</label>
          <select
            id="asset-filter"
            value={filterEventId}
            onChange={(e) => setFilterEventId(e.target.value)}
          >
            <option value="all">All Assets</option>
            <option value="unassigned">Unassigned</option>
            {events.map((event) => (
              <option key={event.id} value={String(event.id)}>
                {event.title}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="asset-sort">Sort</label>
          <select
            id="asset-sort"
            value={sortMode}
            onChange={(e) =>
              setSortMode(
                e.target.value as
                  | "newest"
                  | "oldest"
                  | "name_asc"
                  | "name_desc",
              )
            }
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="name_asc">Name A–Z</option>
            <option value="name_desc">Name Z–A</option>
          </select>
        </div>
      </div>

      <div
        className="tab-row asset-library-tabs"
        role="tablist"
        aria-label="Media type tabs"
      >
        <button
          type="button"
          className={mediaTab === "all" ? "tab-button active" : "tab-button"}
          onClick={() => setMediaTab("all")}
        >
          All ({assets.length})
        </button>
        <button
          type="button"
          className={mediaTab === "image" ? "tab-button active" : "tab-button"}
          onClick={() => setMediaTab("image")}
        >
          Images (
          {assets.filter((asset) => asset.media_type === "image").length})
        </button>
        <button
          type="button"
          className={mediaTab === "video" ? "tab-button active" : "tab-button"}
          onClick={() => setMediaTab("video")}
        >
          Video ({assets.filter((asset) => asset.media_type === "video").length}
          )
        </button>
      </div>

      <div className="approval-action-row asset-selection-toolbar">
        <button type="button" onClick={selectAllVisibleAssets}>
          Select All Visible
        </button>
        <button
          type="button"
          onClick={deselectVisibleAssets}
          disabled={
            !visibleAssetIds.some((id) => selection.selectedSet.has(id))
          }
        >
          Deselect Visible
        </button>
        <button type="button" onClick={selectPendingAssets}>
          Select Pending
        </button>
        <button type="button" onClick={selection.clear}>
          Clear All Selection
        </button>
        <button
          type="button"
          onClick={handleAnalyzeSelected}
          disabled={
            analyzeSelectedState.loading || selection.selectedIds.length === 0
          }
        >
          {analyzeSelectedState.loading
            ? "Analyzing..."
            : `Analyze Selected (${selection.selectedIds.length})`}
        </button>
      </div>

      <p className="helper-text asset-library-summary">
        Showing {filteredAssets.length} of {assets.length} assets
        {assetSearch.trim() ? ` for "${assetSearch.trim()}"` : ""}.
      </p>

      <StatusMessage
        loading={analyzeSelectedState.loading}
        status={analyzeSelectedState.status}
        error={analyzeSelectedState.error}
      />

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {!filteredAssets.length && !loadState.loading && !loadState.error ? (
        <p>No assets found for this view.</p>
      ) : (
        <>
          <div className="asset-index-header" aria-hidden="true">
            <span>Select</span>
            <span>Name</span>
            <span>Type</span>
            <span>Event</span>
            <span>Status</span>
            <span>Uploaded</span>
          </div>

          <ul className="asset-index-list">
            {filteredAssets.map((asset) => {
              const event = asset.event_id
                ? eventsById.get(asset.event_id)
                : null;
              const proposal = proposalByAssetId[asset.id];
              const proposalEdits = draftProposalEdits[asset.id];
              const currentName =
                draftNames[asset.id] ?? displayAssetName(asset);
              const isExpanded = expandedAssetId === asset.id;
              const analysisStatus = normalizeAnalysisStatus(
                asset.analysis_status,
              );
              const isSelected = selection.isSelected(asset.id);

              return (
                <li key={asset.id} className="asset-index-row">
                  <div className="asset-index-shell">
                    <div className="asset-index-checkbox">
                      <input
                        id={`asset-select-${asset.id}`}
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => selection.toggle(asset.id)}
                        onClick={(e) => e.stopPropagation()}
                        aria-label={`Select ${displayAssetName(asset)}`}
                      />
                    </div>

                    <div
                      className="asset-index-main"
                      onClick={() => toggleExpandedAsset(asset.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          toggleExpandedAsset(asset.id);
                        }
                      }}
                    >
                      <span className="asset-index-name">
                        {displayAssetName(asset)}
                      </span>
                      <span>{asset.media_type}</span>
                      <span>{event?.title || "Unassigned"}</span>
                      <span className={analysisStatus.className}>
                        {analysisStatus.label}
                      </span>
                      <span>
                        {new Date(asset.created_at ?? "").toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="asset-index-details">
                      <article className="card">
                        <div className="asset-card-header">
                          <div className="asset-card-meta">
                            <div className="asset-card-meta-row">
                              <label htmlFor={`asset-name-${asset.id}`}>
                                <strong>Asset Name:</strong>
                              </label>
                              <input
                                id={`asset-name-${asset.id}`}
                                value={currentName}
                                onChange={(e) => {
                                  const next = e.target.value;
                                  setDraftNames((prev) => ({
                                    ...prev,
                                    [asset.id]: next,
                                  }));
                                }}
                                onBlur={async (e) => {
                                  const nextName =
                                    e.target.value.trim() || null;
                                  const previousName =
                                    asset.display_name || null;

                                  if (nextName === previousName) {
                                    return;
                                  }

                                  try {
                                    await renameAsset(asset.id, nextName);
                                    await onRefresh();
                                  } catch (err) {
                                    console.error(err);
                                    alert(
                                      err instanceof Error
                                        ? err.message
                                        : "Failed to rename asset.",
                                    );
                                    setDraftNames((prev) => ({
                                      ...prev,
                                      [asset.id]: displayAssetName(asset),
                                    }));
                                  }
                                }}
                              />
                            </div>

                            <p className="helper-text">
                              Duplicate names are allowed. This is just a
                              display label.
                            </p>

                            <div className="asset-card-meta-row">
                              <span>
                                <strong>Event:</strong>{" "}
                                {event?.title || "Unassigned"}
                              </span>

                              <span className="inline-divider">|</span>

                              <label htmlFor={`asset-event-${asset.id}`}>
                                <strong>Re-assign Event:</strong>
                              </label>

                              <select
                                id={`asset-event-${asset.id}`}
                                value={asset.event_id ?? ""}
                                onChange={async (e) => {
                                  const raw = e.target.value;
                                  const nextEventId = raw ? Number(raw) : null;
                                  const previousEventId =
                                    asset.event_id ?? null;

                                  if (nextEventId === previousEventId) {
                                    return;
                                  }

                                  const confirmedMove = window.confirm(
                                    "Move this asset to the selected event?\n\n" +
                                      "Press OK to move it.\n" +
                                      "Press Cancel to keep the current event assignment.",
                                  );

                                  if (!confirmedMove) {
                                    return;
                                  }

                                  try {
                                    await updateAssetEvent(
                                      asset.id,
                                      nextEventId,
                                    );

                                    const shouldPropose = window.confirm(
                                      "Would you like to generate a proposed analysis using the new event context?\n\n" +
                                        "This will use AI tokens.\n\n" +
                                        "Press OK to generate.\n" +
                                        "Press Cancel to keep the current analysis.",
                                    );

                                    if (shouldPropose) {
                                      const proposed =
                                        await proposeAssetAnalysis(asset.id);

                                      setProposalByAssetId((prev) => ({
                                        ...prev,
                                        [asset.id]: proposed,
                                      }));

                                      setDraftProposalEdits((prev) => ({
                                        ...prev,
                                        [asset.id]: {
                                          visual:
                                            proposed.proposed_visual_summary ||
                                            proposed.current_visual_summary ||
                                            "",
                                          accessibility:
                                            proposed.proposed_accessibility_text ||
                                            proposed.current_accessibility_text ||
                                            "",
                                        },
                                      }));
                                    }

                                    await onRefresh();
                                  } catch (err) {
                                    console.error(err);
                                    alert(
                                      err instanceof Error
                                        ? err.message
                                        : "Failed to update asset event.",
                                    );
                                  }
                                }}
                              >
                                <option value="">Unassigned</option>
                                {events.map((eventOption) => (
                                  <option
                                    key={eventOption.id}
                                    value={String(eventOption.id)}
                                  >
                                    {eventOption.title}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </div>
                        </div>

                        {proposal && proposalEdits && (
                          <details className="form-row" open>
                            <summary>Analysis Comparison</summary>
                            <p className="helper-text">
                              Review the current analysis and the proposed
                              event-aware analysis. You can keep the current
                              version, use the proposed version, or edit a
                              merged final version.
                            </p>

                            <div className="approval-review-layout">
                              <div className="approval-preview-column">
                                <p>
                                  <strong>Current visual summary:</strong>
                                </p>
                                <p>
                                  {proposal.current_visual_summary || "None"}
                                </p>

                                <p>
                                  <strong>Current accessibility:</strong>
                                </p>
                                <p>
                                  {proposal.current_accessibility_text ||
                                    "None"}
                                </p>
                              </div>

                              <div className="approval-details-column">
                                <p>
                                  <strong>Proposed visual summary:</strong>
                                </p>
                                <p>
                                  {proposal.proposed_visual_summary || "None"}
                                </p>

                                <p>
                                  <strong>Proposed accessibility:</strong>
                                </p>
                                <p>
                                  {proposal.proposed_accessibility_text ||
                                    "None"}
                                </p>
                              </div>
                            </div>

                            <div className="form-row">
                              <label htmlFor={`merged-visual-${asset.id}`}>
                                Final Visual Summary
                              </label>
                              <textarea
                                id={`merged-visual-${asset.id}`}
                                value={proposalEdits.visual}
                                onChange={(e) =>
                                  setDraftProposalEdits((prev) => ({
                                    ...prev,
                                    [asset.id]: {
                                      ...prev[asset.id],
                                      visual: e.target.value,
                                    },
                                  }))
                                }
                              />
                            </div>

                            <div className="form-row">
                              <label
                                htmlFor={`merged-accessibility-${asset.id}`}
                              >
                                Final Accessibility
                              </label>
                              <textarea
                                id={`merged-accessibility-${asset.id}`}
                                value={proposalEdits.accessibility}
                                onChange={(e) =>
                                  setDraftProposalEdits((prev) => ({
                                    ...prev,
                                    [asset.id]: {
                                      ...prev[asset.id],
                                      accessibility: e.target.value,
                                    },
                                  }))
                                }
                              />
                            </div>

                            <div className="approval-action-row">
                              <button
                                type="button"
                                onClick={() => {
                                  setProposalByAssetId((prev) => {
                                    const next = { ...prev };
                                    delete next[asset.id];
                                    return next;
                                  });

                                  setDraftProposalEdits((prev) => {
                                    const next = { ...prev };
                                    delete next[asset.id];
                                    return next;
                                  });
                                }}
                              >
                                Keep Current
                              </button>

                              <button
                                type="button"
                                onClick={async () => {
                                  try {
                                    await applyAssetAnalysis(asset.id, {
                                      vision_summary_generated:
                                        proposal.proposed_visual_summary ||
                                        null,
                                      accessibility_text_generated:
                                        proposal.proposed_accessibility_text ||
                                        null,
                                    });

                                    setProposalByAssetId((prev) => {
                                      const next = { ...prev };
                                      delete next[asset.id];
                                      return next;
                                    });

                                    setDraftProposalEdits((prev) => {
                                      const next = { ...prev };
                                      delete next[asset.id];
                                      return next;
                                    });

                                    await onRefresh();
                                  } catch (err) {
                                    console.error(err);
                                    alert(
                                      err instanceof Error
                                        ? err.message
                                        : "Failed to apply proposed analysis.",
                                    );
                                  }
                                }}
                              >
                                Use Proposed
                              </button>

                              <button
                                type="button"
                                onClick={async () => {
                                  try {
                                    await applyAssetAnalysis(asset.id, {
                                      vision_summary_generated:
                                        proposalEdits.visual || null,
                                      accessibility_text_generated:
                                        proposalEdits.accessibility || null,
                                    });

                                    setProposalByAssetId((prev) => {
                                      const next = { ...prev };
                                      delete next[asset.id];
                                      return next;
                                    });

                                    setDraftProposalEdits((prev) => {
                                      const next = { ...prev };
                                      delete next[asset.id];
                                      return next;
                                    });

                                    await onRefresh();
                                  } catch (err) {
                                    console.error(err);
                                    alert(
                                      err instanceof Error
                                        ? err.message
                                        : "Failed to apply edited analysis.",
                                    );
                                  }
                                }}
                              >
                                Apply Edited
                              </button>
                            </div>
                          </details>
                        )}

                        <div className="asset-library-panel">
                          <AssetCard
                            asset={asset}
                            onRefresh={onRefresh}
                            compactPreview
                            collapsed={false}
                          />
                        </div>
                      </article>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
