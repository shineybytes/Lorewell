import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  applyAssetAnalysis,
  listAssets,
  proposeAssetAnalysis,
  renameAsset,
  updateAssetEvent,
  uploadAssetNoEvent,
} from "../api/assets";
import { listEvents } from "../api/events";
import type {
  AssetAnalysisProposalResponse,
  AssetRecord,
  EventRecord,
} from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetCard from "../components/AssetCard";
import { useAsyncState } from "../hooks/useAsyncState";

type MediaTab = "all" | "image" | "video";
type AssetSortMode = "newest" | "oldest" | "name_asc" | "name_desc";

function filenameFromPath(filePath: string) {
  return filePath.split("/").pop() || filePath;
}

function displayAssetName(asset: AssetRecord) {
  return asset.display_name || filenameFromPath(asset.file_path);
}

function sortName(asset: AssetRecord) {
  return displayAssetName(asset).toLowerCase();
}

export default function AssetsPage() {
  const [assets, setAssets] = useState<AssetRecord[]>([]);
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [filterEventId, setFilterEventId] = useState<string>("all");
  const [mediaTab, setMediaTab] = useState<MediaTab>("all");
  const [sortMode, setSortMode] = useState<AssetSortMode>("newest");

  const [proposalByAssetId, setProposalByAssetId] = useState<
    Record<number, AssetAnalysisProposalResponse>
  >({});
  const [draftProposalEdits, setDraftProposalEdits] = useState<
    Record<number, { visual: string; accessibility: string }>
  >({});
  const [draftNames, setDraftNames] = useState<Record<number, string>>({});

  const loadState = useAsyncState();
  const uploadState = useAsyncState();

  async function loadData(showLoadingMessage = true) {
    try {
      if (showLoadingMessage) {
        loadState.start("Loading assets...");
      }

      const [assetData, eventData] = await Promise.all([
        listAssets(),
        listEvents(),
      ]);

      setAssets(assetData);
      setEvents(eventData);

      setDraftNames((prev) => {
        const next = { ...prev };
        for (const asset of assetData) {
          if (!(asset.id in next)) {
            next[asset.id] = displayAssetName(asset);
          }
        }
        return next;
      });

      if (showLoadingMessage) {
        loadState.succeed("");
      }
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load assets.",
      );
    }
  }

  useEffect(() => {
    void loadData(true);
  }, []);

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

    result.sort((a, b) => {
      switch (sortMode) {
        case "oldest":
          return (
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );
        case "name_asc":
          return sortName(a).localeCompare(sortName(b));
        case "name_desc":
          return sortName(b).localeCompare(sortName(a));
        case "newest":
        default:
          return (
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
      }
    });

    return result;
  }, [assets, filterEventId, mediaTab, sortMode]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const form = event.currentTarget;
    const input = form.elements.namedItem("file") as HTMLInputElement | null;
    const files = input?.files;

    if (!files || files.length === 0) {
      uploadState.fail("Choose at least one file.");
      return;
    }

    const fileList = Array.from(files);

    try {
      uploadState.start(
        fileList.length === 1
          ? "Uploading asset..."
          : `Uploading ${fileList.length} assets...`,
      );

      for (const file of fileList) {
        await uploadAssetNoEvent(file);
      }

      form.reset();
      await loadData(false);
      uploadState.succeed(
        fileList.length === 1 ? "Asset uploaded." : "Assets uploaded.",
      );
    } catch (err) {
      console.error(err);
      uploadState.fail(
        err instanceof Error ? err.message : "Failed to upload asset.",
      );
    }
  }

  return (
    <section aria-labelledby="assets-heading">
      <div className="page-header">
        <div>
          <h2 id="assets-heading">Assets</h2>
          <p>Manage uploaded media, analysis, and event associations.</p>
        </div>
      </div>

      <section aria-labelledby="asset-upload-heading">
        <h3 id="asset-upload-heading">Upload Asset</h3>

        <form onSubmit={handleUpload}>
          <div className="form-row">
            <label htmlFor="asset-library-upload">
              Choose images or videos
            </label>
            <input
              id="asset-library-upload"
              name="file"
              type="file"
              multiple
              disabled={uploadState.loading}
            />
            <p className="helper-text">
              Upload directly to Asset Library without assigning an event yet.
            </p>
          </div>

          <button type="submit" disabled={uploadState.loading}>
            {uploadState.loading ? "Uploading..." : "Upload to Asset Library"}
          </button>
        </form>

        <StatusMessage
          loading={uploadState.loading}
          status={uploadState.status}
          error={uploadState.error}
        />
      </section>

      <div className="tab-row" role="tablist" aria-label="Media type tabs">
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

      <div className="approval-action-row">
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

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {!filteredAssets.length && !loadState.loading && !loadState.error ? (
        <p>No assets found for this view.</p>
      ) : (
        <ul className="card-list">
          {filteredAssets.map((asset) => {
            const event = asset.event_id
              ? eventsById.get(asset.event_id)
              : null;
            const proposal = proposalByAssetId[asset.id];
            const proposalEdits = draftProposalEdits[asset.id];
            const currentName = draftNames[asset.id] ?? displayAssetName(asset);

            return (
              <li key={asset.id}>
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
                            const nextName = e.target.value.trim() || null;
                            const previousName = asset.display_name || null;

                            if (nextName === previousName) {
                              return;
                            }

                            try {
                              await renameAsset(asset.id, nextName);
                              setAssets((prev) =>
                                prev.map((candidate) =>
                                  candidate.id === asset.id
                                    ? {
                                        ...candidate,
                                        display_name: nextName,
                                      }
                                    : candidate,
                                ),
                              );
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
                        Duplicate names are allowed. This is just a display
                        label.
                      </p>

                      <div className="asset-card-meta-row">
                        <span>
                          <strong>Event:</strong> {event?.title || "Unassigned"}
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
                            const previousEventId = asset.event_id ?? null;

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
                              const updated = await updateAssetEvent(
                                asset.id,
                                nextEventId,
                              );

                              setAssets((prev) =>
                                prev.map((candidate) =>
                                  candidate.id === asset.id
                                    ? updated
                                    : candidate,
                                ),
                              );

                              const shouldPropose = window.confirm(
                                "Would you like to generate a proposed analysis using the new event context?\n\n" +
                                  "This will use AI tokens.\n\n" +
                                  "Press OK to generate.\n" +
                                  "Press Cancel to keep the current analysis.",
                              );

                              if (!shouldPropose) {
                                return;
                              }

                              const proposed = await proposeAssetAnalysis(
                                asset.id,
                              );

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
                        Review the current analysis and the proposed event-aware
                        analysis. You can keep the current version, use the
                        proposed version, or edit a merged final version.
                      </p>

                      <div className="approval-review-layout">
                        <div className="approval-preview-column">
                          <p>
                            <strong>Current visual summary:</strong>
                          </p>
                          <p>{proposal.current_visual_summary || "None"}</p>

                          <p>
                            <strong>Current accessibility:</strong>
                          </p>
                          <p>{proposal.current_accessibility_text || "None"}</p>
                        </div>

                        <div className="approval-details-column">
                          <p>
                            <strong>Proposed visual summary:</strong>
                          </p>
                          <p>{proposal.proposed_visual_summary || "None"}</p>

                          <p>
                            <strong>Proposed accessibility:</strong>
                          </p>
                          <p>
                            {proposal.proposed_accessibility_text || "None"}
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
                        <label htmlFor={`merged-accessibility-${asset.id}`}>
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
                              const updated = await applyAssetAnalysis(
                                asset.id,
                                {
                                  vision_summary_generated:
                                    proposal.proposed_visual_summary || null,
                                  accessibility_text_generated:
                                    proposal.proposed_accessibility_text ||
                                    null,
                                },
                              );

                              setAssets((prev) =>
                                prev.map((candidate) =>
                                  candidate.id === asset.id
                                    ? updated
                                    : candidate,
                                ),
                              );

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
                              const updated = await applyAssetAnalysis(
                                asset.id,
                                {
                                  vision_summary_generated:
                                    proposalEdits.visual || null,
                                  accessibility_text_generated:
                                    proposalEdits.accessibility || null,
                                },
                              );

                              setAssets((prev) =>
                                prev.map((candidate) =>
                                  candidate.id === asset.id
                                    ? updated
                                    : candidate,
                                ),
                              );

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
                      onRefresh={() => loadData(false)}
                      compactPreview
                    />
                  </div>
                </article>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
