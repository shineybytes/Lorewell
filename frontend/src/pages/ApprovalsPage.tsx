import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { forkApprovedPostToDraft, listApprovedPosts } from "../api/approvals";
import type { ApprovedPost } from "../api/approvals";
import StatusMessage from "../components/StatusMessage";
import { listTimezones } from "../api/events";
import { useAsyncState } from "../hooks/useAsyncState";
import InstagramPreview from "../components/InstagramPreview";
import { createSchedule, publishNow } from "../api/schedules";
import { friendlyPublishError } from "../utils/error";
import ListToolbar from "../components/ListToolbar";
import ListSummary from "../components/ListSummary";

type ApprovalSortMode = "newest" | "oldest" | "caption_asc" | "caption_desc";

function approvalDisplayTitle(post: ApprovedPost) {
  if (post.caption_final?.trim()) {
    return post.caption_final.length > 60
      ? `${post.caption_final.slice(0, 60)}…`
      : post.caption_final;
  }

  return `Approved #${post.id}`;
}

export default function ApprovalsPage() {
  const navigate = useNavigate();
  const loadState = useAsyncState();

  const [posts, setPosts] = useState<ApprovedPost[]>([]);
  const [timezones, setTimezones] = useState<string[]>([]);
  const [defaultTz, setDefaultTz] = useState("America/Los_Angeles");

  const [approvalSearch, setApprovalSearch] = useState("");
  const [sortMode, setSortMode] = useState<ApprovalSortMode>("newest");
  const [expandedPostId, setExpandedPostId] = useState<number | null>(null);

  const [scheduleState, setScheduleState] = useState<
    Record<number, { date: string; tz: string }>
  >({});

  const [actionState, setActionState] = useState<
    Record<number, { loading: boolean; status: string; error: string }>
  >({});

  function setPostActionState(
    postId: number,
    next: { loading: boolean; status: string; error: string },
  ) {
    setActionState((prev) => ({
      ...prev,
      [postId]: next,
    }));
  }

  async function loadData(showLoadingMessage = true) {
    try {
      if (showLoadingMessage) {
        loadState.start("Loading approved posts...");
      }

      const data = await listApprovedPosts();
      setPosts(data);

      if (showLoadingMessage) {
        loadState.succeed("");
      }
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load approvals.",
      );
    }
  }

  useEffect(() => {
    void loadData(true);
  }, []);

  useEffect(() => {
    async function loadTimezones() {
      try {
        const data = await listTimezones();
        setTimezones(data);

        const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;

        if (data.includes(browserTz)) {
          setDefaultTz(browserTz);
        }
      } catch (err) {
        console.error(err);
      }
    }

    void loadTimezones();
  }, []);

  const filteredPosts = useMemo(() => {
    let result = [...posts];

    const query = approvalSearch.trim().toLowerCase();

    if (query) {
      result = result.filter((post) => {
        const title = approvalDisplayTitle(post).toLowerCase();
        const caption = (post.caption_final || "").toLowerCase();
        const hashtags = post.hashtags_final.join(" ").toLowerCase();
        const accessibility = (post.accessibility_text || "").toLowerCase();
        const status = (post.status || "").toLowerCase();
        const assetPath = (post.asset_file_path || "").toLowerCase();

        return (
          title.includes(query) ||
          caption.includes(query) ||
          hashtags.includes(query) ||
          accessibility.includes(query) ||
          status.includes(query) ||
          assetPath.includes(query)
        );
      });
    }

    result.sort((a, b) => {
      switch (sortMode) {
        case "oldest":
          return a.id - b.id;
        case "caption_asc":
          return approvalDisplayTitle(a).localeCompare(approvalDisplayTitle(b));
        case "caption_desc":
          return approvalDisplayTitle(b).localeCompare(approvalDisplayTitle(a));
        case "newest":
        default:
          return b.id - a.id;
      }
    });

    return result;
  }, [posts, approvalSearch, sortMode]);

  function toggleExpandedPost(id: number) {
    setExpandedPostId((current) => (current === id ? null : id));
  }

  return (
    <section aria-labelledby="approvals-heading">
      <header className="page-header">
        <div>
          <h2 id="approvals-heading">Approvals</h2>
          <p>Posts ready for scheduling.</p>
        </div>
      </header>

      <ListToolbar
        searchId="approval-search"
        searchValue={approvalSearch}
        onSearchChange={setApprovalSearch}
        searchPlaceholder="Search caption, hashtags, accessibility, status, or asset path"
        sortId="approval-sort"
        sortValue={sortMode}
        onSortChange={(v) =>
          setSortMode(v as "newest" | "oldest" | "caption_asc" | "caption_desc")
        }
        sortOptions={[
          { value: "newest", label: "Newest first" },
          { value: "oldest", label: "Oldest first" },
          { value: "caption_asc", label: "Caption A–Z" },
          { value: "caption_desc", label: "Caption Z–A" },
        ]}
      />
      <ListSummary
        visibleCount={filteredPosts.length}
        totalCount={posts.length}
        noun="approvals"
        query={approvalSearch}
      />
      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {!filteredPosts.length && !loadState.loading && !loadState.error ? (
        <p>No approved posts yet.</p>
      ) : (
        <>
          <div className="approval-index-header" aria-hidden="true">
            <span>Caption</span>
            <span>Status</span>
            <span>Asset</span>
            <span>ID</span>
          </div>

          <ul className="approval-index-list">
            {filteredPosts.map((post) => {
              const state = scheduleState[post.id] || {
                date: "",
                tz: defaultTz,
              };

              const postAction = actionState[post.id] || {
                loading: false,
                status: "",
                error: "",
              };

              const previewAsset =
                post.asset_file_path && post.asset_media_type
                  ? {
                      id: post.selected_asset_id,
                      event_id: 0,
                      file_path: post.asset_file_path,
                      media_type: post.asset_media_type,
                      analysis_status: "approved",
                      vision_summary_generated: null,
                      accessibility_text_generated: post.accessibility_text,
                      accessibility_text_final: post.accessibility_text,
                      analysis_error_message: null,
                      analysis_user_correction: null,
                    }
                  : null;

              const isExpanded = expandedPostId === post.id;

              return (
                <li key={post.id} className="approval-index-row">
                  <div
                    className="approval-index-main"
                    onClick={() => toggleExpandedPost(post.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpandedPost(post.id);
                      }
                    }}
                  >
                    <span className="approval-index-title">
                      {approvalDisplayTitle(post)}
                    </span>
                    <span>{post.status}</span>
                    <span>{post.asset_file_path || "None"}</span>
                    <span>#{post.id}</span>
                  </div>

                  {isExpanded && (
                    <div className="approval-index-details">
                      <article className="card">
                        <div className="approval-review-layout">
                          <div className="approval-preview-column">
                            <InstagramPreview
                              asset={previewAsset}
                              caption={post.caption_final}
                              hashtags={post.hashtags_final}
                              profileLabel="Approved Preview"
                            />
                          </div>

                          <div className="approval-details-column">
                            <h3>Approved #{post.id}</h3>

                            <div className="approval-action-row">
                              <button
                                type="button"
                                disabled={postAction.loading}
                                onClick={async () => {
                                  try {
                                    setPostActionState(post.id, {
                                      loading: true,
                                      status: "Creating revision draft...",
                                      error: "",
                                    });

                                    const forked =
                                      await forkApprovedPostToDraft(post.id);

                                    setPostActionState(post.id, {
                                      loading: false,
                                      status: "Revision draft created.",
                                      error: "",
                                    });

                                    navigate(
                                      `/drafts/editor?post_id=${forked.post_id}`,
                                    );
                                  } catch (err) {
                                    console.error(err);
                                    setPostActionState(post.id, {
                                      loading: false,
                                      status: "",
                                      error:
                                        err instanceof Error
                                          ? err.message
                                          : "Failed to create revision draft.",
                                    });
                                  }
                                }}
                              >
                                {postAction.loading
                                  ? "Working..."
                                  : "Create Revision Draft"}
                              </button>

                              <button
                                type="button"
                                disabled={postAction.loading}
                                onClick={async () => {
                                  const confirmed = window.confirm(
                                    "Publish this post now? This will attempt to post immediately.",
                                  );

                                  if (!confirmed) {
                                    return;
                                  }

                                  try {
                                    setPostActionState(post.id, {
                                      loading: true,
                                      status:
                                        "Queueing post for immediate publish...",
                                      error: "",
                                    });

                                    await publishNow(post.id);

                                    setPostActionState(post.id, {
                                      loading: false,
                                      status:
                                        "Queued for immediate publishing.",
                                      error: "",
                                    });
                                  } catch (err) {
                                    console.error(err);
                                    setPostActionState(post.id, {
                                      loading: false,
                                      status: "",
                                      error: friendlyPublishError(
                                        err instanceof Error
                                          ? err.message
                                          : "Failed to publish now",
                                      ),
                                    });
                                  }
                                }}
                              >
                                {postAction.loading
                                  ? "Working..."
                                  : "Publish Now"}
                              </button>
                            </div>

                            <div>
                              <p>
                                <strong>Caption:</strong>
                              </p>
                              <p>{post.caption_final}</p>
                            </div>

                            <div>
                              <p>
                                <strong>Hashtags:</strong>
                              </p>
                              <p>{post.hashtags_final.join(" ")}</p>
                            </div>

                            <div>
                              <p>
                                <strong>Accessibility:</strong>
                              </p>
                              <p>{post.accessibility_text}</p>
                            </div>

                            <p>
                              <strong>Status:</strong> {post.status}
                            </p>

                            <div className="form-row">
                              <label htmlFor={`publish-at-${post.id}`}>
                                Publish At (optional until you schedule)
                              </label>
                              <input
                                id={`publish-at-${post.id}`}
                                type="datetime-local"
                                value={state.date}
                                onChange={(e) =>
                                  setScheduleState((prev) => ({
                                    ...prev,
                                    [post.id]: {
                                      date: e.target.value,
                                      tz: state.tz,
                                    },
                                  }))
                                }
                              />
                              <p className="helper-text">
                                Optional until you click Schedule.
                              </p>
                            </div>

                            <div className="form-row">
                              <label htmlFor={`publish-tz-${post.id}`}>
                                Timezone (optional until you schedule)
                              </label>
                              <select
                                id={`publish-tz-${post.id}`}
                                value={state.tz}
                                onChange={(e) =>
                                  setScheduleState((prev) => ({
                                    ...prev,
                                    [post.id]: {
                                      date: state.date,
                                      tz: e.target.value,
                                    },
                                  }))
                                }
                              >
                                <option value="">Select a timezone</option>
                                {timezones.map((tz) => (
                                  <option key={tz} value={tz}>
                                    {tz}
                                  </option>
                                ))}
                              </select>
                              <p className="helper-text">
                                Optional until you click Schedule. Required
                                together with Publish At.
                              </p>
                            </div>

                            <button
                              type="button"
                              disabled={postAction.loading}
                              onClick={async () => {
                                try {
                                  if (!state.date) {
                                    setPostActionState(post.id, {
                                      loading: false,
                                      status: "",
                                      error: "Choose a publish date and time.",
                                    });
                                    return;
                                  }

                                  if (!state.tz) {
                                    setPostActionState(post.id, {
                                      loading: false,
                                      status: "",
                                      error: "Choose a timezone.",
                                    });
                                    return;
                                  }

                                  setPostActionState(post.id, {
                                    loading: true,
                                    status: "Scheduling post...",
                                    error: "",
                                  });

                                  await createSchedule(post.id, {
                                    publish_at: state.date,
                                    publish_timezone: state.tz,
                                  });

                                  setPostActionState(post.id, {
                                    loading: false,
                                    status: "Scheduled.",
                                    error: "",
                                  });
                                } catch (err) {
                                  console.error(err);
                                  setPostActionState(post.id, {
                                    loading: false,
                                    status: "",
                                    error: friendlyPublishError(
                                      err instanceof Error
                                        ? err.message
                                        : "Failed to schedule",
                                    ),
                                  });
                                }
                              }}
                            >
                              {postAction.loading ? "Working..." : "Schedule"}
                            </button>

                            <StatusMessage
                              loading={postAction.loading}
                              status={postAction.status}
                              error={postAction.error}
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
