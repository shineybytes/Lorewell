import { useEffect, useMemo, useState } from "react";
import {
  listSchedules,
  toggleScheduleAcknowledged,
  retrySchedule,
  archiveAllFailed,
  restoreAllFailed,
  deleteSchedule,
} from "../api/schedules";
import type { Schedule } from "../api/schedules";
import StatusMessage from "../components/StatusMessage";
import InstagramPreview from "../components/InstagramPreview";
import { useAsyncState } from "../hooks/useAsyncState";
import { friendlyPublishError } from "../utils/error";
import ListToolbar from "../components/ListToolbar";
import ListSummary from "../components/ListSummary";

type ScheduleTab =
  | "all"
  | "future"
  | "recent"
  | "past"
  | "attention"
  | "archived";

type SortDirection = "newest" | "oldest";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [activeTab, setActiveTab] = useState<ScheduleTab>("recent");
  const [sortDirection, setSortDirection] = useState<SortDirection>("newest");
  const [scheduleSearch, setScheduleSearch] = useState("");
  const [expandedScheduleId, setExpandedScheduleId] = useState<number | null>(
    null,
  );
  const loadState = useAsyncState();

  const [actionState, setActionState] = useState<
    Record<number, { loading: boolean; status: string; error: string }>
  >({});

  function setScheduleActionState(
    scheduleId: number,
    next: { loading: boolean; status: string; error: string },
  ) {
    setActionState((prev) => ({
      ...prev,
      [scheduleId]: next,
    }));
  }

  async function loadData(showLoadingMessage = true) {
    try {
      if (showLoadingMessage) {
        loadState.start("Loading schedules...");
      }

      const data = await listSchedules();
      setSchedules(data);

      if (showLoadingMessage) {
        loadState.succeed("");
      }
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load schedules.",
      );
    }
  }

  useEffect(() => {
    void loadData(true);

    const intervalId = setInterval(() => {
      void loadData(false);
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const scheduleViews = useMemo(() => {
    const now = new Date();
    const oneHourMs = 60 * 60 * 1000;

    const all = schedules;

    const future = schedules.filter(
      (s) =>
        (s.status === "scheduled" || s.status === "publishing") &&
        new Date(s.publish_at).getTime() >= now.getTime(),
    );

    const past = schedules.filter(
      (s) => s.status === "published" || s.status === "failed",
    );

    const attention = schedules.filter(
      (s) => s.status === "failed" && !s.failure_acknowledged,
    );

    const archived = schedules.filter(
      (s) => s.status === "failed" && s.failure_acknowledged,
    );

    const recentWindowStart = now.getTime() - oneHourMs;
    const recentWindowEnd = now.getTime() + oneHourMs;

    let recent = schedules.filter((s) => {
      const t = new Date(s.publish_at).getTime();
      return t >= recentWindowStart && t <= recentWindowEnd;
    });

    if (recent.length === 0 && schedules.length > 0) {
      const anchor = new Date(
        schedules
          .slice()
          .sort(
            (a, b) =>
              Math.abs(new Date(a.publish_at).getTime() - now.getTime()) -
              Math.abs(new Date(b.publish_at).getTime() - now.getTime()),
          )[0].publish_at,
      );

      const start = anchor.getTime() - oneHourMs;
      const end = anchor.getTime() + oneHourMs;

      recent = schedules.filter((s) => {
        const t = new Date(s.publish_at).getTime();
        return t >= start && t <= end;
      });
    }

    return {
      all,
      future,
      recent,
      past,
      attention,
      archived,
    };
  }, [schedules]);

  const counts = useMemo(
    () => ({
      all: scheduleViews.all.length,
      future: scheduleViews.future.length,
      recent: scheduleViews.recent.length,
      past: scheduleViews.past.length,
      attention: scheduleViews.attention.length,
      archived: scheduleViews.archived.length,
    }),
    [scheduleViews],
  );

  const visibleSchedules = useMemo(() => {
    const subset = scheduleViews[activeTab];
    const query = scheduleSearch.trim().toLowerCase();

    const filtered = query
      ? subset.filter((s) => {
          const id = String(s.id);
          const approvedPostId = String(s.approved_post_id);
          const publishAt = (s.publish_at || "").toLowerCase();
          const timezone = (s.publish_timezone || "").toLowerCase();
          const status = (s.status || "").toLowerCase();
          const caption = (s.caption_final || "").toLowerCase();
          const hashtags = (s.hashtags_final || []).join(" ").toLowerCase();
          const assetPath = (s.asset_file_path || "").toLowerCase();
          const error = (s.error_message || "").toLowerCase();

          return (
            id.includes(query) ||
            approvedPostId.includes(query) ||
            publishAt.includes(query) ||
            timezone.includes(query) ||
            status.includes(query) ||
            caption.includes(query) ||
            hashtags.includes(query) ||
            assetPath.includes(query) ||
            error.includes(query)
          );
        })
      : subset;

    return filtered.slice().sort((a, b) => {
      const aTime = new Date(a.publish_at).getTime();
      const bTime = new Date(b.publish_at).getTime();

      if (sortDirection === "oldest") {
        return aTime - bTime;
      }

      return bTime - aTime;
    });
  }, [activeTab, scheduleViews, sortDirection, scheduleSearch]);

  function toggleExpandedSchedule(id: number) {
    setExpandedScheduleId((current) => (current === id ? null : id));
  }

  return (
    <section aria-labelledby="schedules-heading">
      <header className="page-header">
        <div>
          <h2 id="schedules-heading">Schedules</h2>
          <p>Track scheduled, publishing, published, and failed posts.</p>
        </div>
      </header>

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      <div className="tab-row" role="tablist" aria-label="Schedule views">
        {[
          { key: "all", label: "All" },
          { key: "future", label: "Future" },
          { key: "recent", label: "Recent" },
          { key: "past", label: "Past" },
          { key: "attention", label: "Needs Attention" },
          { key: "archived", label: "Archived" },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            className={
              activeTab === tab.key ? "tab-button active" : "tab-button"
            }
            onClick={() => setActiveTab(tab.key as ScheduleTab)}
          >
            {tab.label} ({counts[tab.key as ScheduleTab]})
          </button>
        ))}
      </div>

      <ListToolbar
        searchId="schedule-search"
        searchValue={scheduleSearch}
        onSearchChange={setScheduleSearch}
        searchPlaceholder="Search id, status, publish time, caption, hashtags, asset path, or error"
        sortId="schedule-sort"
        sortValue={sortDirection}
        onSortChange={(v) => setSortDirection(v as "newest" | "oldest")}
        sortOptions={[
          { value: "newest", label: "Newest first" },
          { value: "oldest", label: "Oldest first" },
        ]}
        rightContent={
          <>
            {activeTab === "attention" && (
              <button
                type="button"
                onClick={async () => {
                  if (!confirm("Archive all failed schedules?")) return;
                  await archiveAllFailed();
                  await loadData(false);
                }}
              >
                Archive All
              </button>
            )}

            {activeTab === "archived" && (
              <button
                type="button"
                onClick={async () => {
                  if (!confirm("Restore all archived failures?")) return;
                  await restoreAllFailed();
                  await loadData(false);
                }}
              >
                Restore All
              </button>
            )}
          </>
        }
      />
      <ListSummary
        visibleCount={visibleSchedules.length}
        totalCount={counts[activeTab]}
        noun="schedules"
        query={scheduleSearch}
      />

      {!visibleSchedules.length && !loadState.loading && !loadState.error ? (
        <p>No schedules in this view.</p>
      ) : (
        <>
          <div className="schedule-index-header" aria-hidden="true">
            <span>ID</span>
            <span>Status</span>
            <span>Publish Time</span>
            <span>Post</span>
          </div>

          <ul className="schedule-index-list">
            {visibleSchedules.map((s) => {
              const previewAsset =
                s.asset_file_path && s.asset_media_type
                  ? {
                      id: s.selected_asset_id ?? 0,
                      event_id: 0,
                      file_path: s.asset_file_path,
                      media_type: s.asset_media_type,
                      analysis_status: "approved",
                      vision_summary_generated: null,
                      accessibility_text_generated:
                        s.accessibility_text ?? null,
                      accessibility_text_final: s.accessibility_text ?? null,
                      analysis_error_message: null,
                      analysis_user_correction: null,
                    }
                  : null;

              const scheduleAction = actionState[s.id] || {
                loading: false,
                status: "",
                error: "",
              };

              const canUnschedule =
                s.status === "scheduled" || s.status === "publishing";

              const isExpanded = expandedScheduleId === s.id;

              return (
                <li key={s.id} className="schedule-index-row">
                  <div
                    className="schedule-index-main"
                    onClick={() => toggleExpandedSchedule(s.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpandedSchedule(s.id);
                      }
                    }}
                  >
                    <span>#{s.id}</span>
                    <span>{s.status}</span>
                    <span>{s.publish_at}</span>
                    <span>{s.approved_post_id}</span>
                  </div>

                  {isExpanded && (
                    <div className="schedule-index-details">
                      <article className="card">
                        <div className="approval-review-layout">
                          <div className="approval-preview-column">
                            <InstagramPreview
                              asset={previewAsset}
                              caption={s.caption_final}
                              hashtags={s.hashtags_final}
                              profileLabel="Scheduled Preview"
                            />
                          </div>

                          <div className="approval-details-column">
                            <h3>Schedule #{s.id}</h3>

                            <p>
                              <strong>Approved Post:</strong>{" "}
                              {s.approved_post_id}
                            </p>
                            <p>
                              <strong>Publish At (UTC):</strong> {s.publish_at}
                            </p>
                            <p>
                              <strong>Timezone:</strong> {s.publish_timezone}
                            </p>
                            <p>
                              <strong>Status:</strong> {s.status}
                            </p>
                            <p>
                              <strong>Instagram:</strong>{" "}
                              {s.published_instagram_id
                                ? `Published to Instagram (Post ID: ${s.published_instagram_id})`
                                : "Not published yet"}
                            </p>
                            <p>
                              <strong>Error:</strong>{" "}
                              {s.error_message
                                ? friendlyPublishError(s.error_message)
                                : "None"}
                            </p>

                            {canUnschedule && (
                              <button
                                type="button"
                                className="button-danger"
                                disabled={scheduleAction.loading}
                                onClick={async (e) => {
                                  e.stopPropagation();

                                  try {
                                    if (!confirm("Unschedule this post?")) {
                                      return;
                                    }

                                    setScheduleActionState(s.id, {
                                      loading: true,
                                      status: "Unscheduling post...",
                                      error: "",
                                    });

                                    await deleteSchedule(s.id);
                                    await loadData(false);

                                    setScheduleActionState(s.id, {
                                      loading: false,
                                      status: "Post unscheduled.",
                                      error: "",
                                    });

                                    setExpandedScheduleId((current) =>
                                      current === s.id ? null : current,
                                    );
                                  } catch (err) {
                                    console.error(err);
                                    setScheduleActionState(s.id, {
                                      loading: false,
                                      status: "",
                                      error:
                                        err instanceof Error
                                          ? err.message
                                          : "Failed to unschedule post.",
                                    });
                                  }
                                }}
                              >
                                {scheduleAction.loading
                                  ? "Unscheduling..."
                                  : "Unschedule"}
                              </button>
                            )}

                            {(activeTab === "attention" ||
                              activeTab === "archived") && (
                              <>
                                <p>
                                  <strong>Archived:</strong>{" "}
                                  {s.failure_acknowledged ? "Yes" : "No"}
                                </p>

                                {activeTab === "attention" && (
                                  <button
                                    type="button"
                                    disabled={scheduleAction.loading}
                                    onClick={async (e) => {
                                      e.stopPropagation();

                                      try {
                                        setScheduleActionState(s.id, {
                                          loading: true,
                                          status: "Retrying publish...",
                                          error: "",
                                        });

                                        await retrySchedule(s.id);
                                        await loadData(false);

                                        setScheduleActionState(s.id, {
                                          loading: false,
                                          status: "Retry scheduled.",
                                          error: "",
                                        });
                                      } catch (err) {
                                        console.error(err);
                                        setScheduleActionState(s.id, {
                                          loading: false,
                                          status: "",
                                          error:
                                            err instanceof Error
                                              ? err.message
                                              : "Failed to retry publish.",
                                        });
                                      }
                                    }}
                                  >
                                    {scheduleAction.loading
                                      ? "Retrying..."
                                      : "Retry Publishing"}
                                  </button>
                                )}

                                <button
                                  type="button"
                                  disabled={scheduleAction.loading}
                                  onClick={async (e) => {
                                    e.stopPropagation();

                                    try {
                                      setScheduleActionState(s.id, {
                                        loading: true,
                                        status: s.failure_acknowledged
                                          ? "Restoring failure to active queue..."
                                          : "Archiving failure...",
                                        error: "",
                                      });

                                      await toggleScheduleAcknowledged(s.id);
                                      await loadData(false);

                                      setScheduleActionState(s.id, {
                                        loading: false,
                                        status: s.failure_acknowledged
                                          ? "Failure restored to Needs Attention."
                                          : "Failure archived.",
                                        error: "",
                                      });
                                    } catch (err) {
                                      console.error(err);
                                      setScheduleActionState(s.id, {
                                        loading: false,
                                        status: "",
                                        error:
                                          err instanceof Error
                                            ? err.message
                                            : "Failed to update failure status.",
                                      });
                                    }
                                  }}
                                >
                                  {scheduleAction.loading
                                    ? "Updating..."
                                    : s.failure_acknowledged
                                      ? "Restore to Needs Attention"
                                      : "Archive Failure"}
                                </button>
                              </>
                            )}

                            <StatusMessage
                              loading={scheduleAction.loading}
                              status={scheduleAction.status}
                              error={scheduleAction.error}
                            />
                          </div>
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
