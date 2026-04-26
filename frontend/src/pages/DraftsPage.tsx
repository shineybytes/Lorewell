import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deletePost, listPosts } from "../api/posts";
import type { PostRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import { useAsyncState } from "../hooks/useAsyncState";
import ListToolbar from "../components/ListToolbar";
import ListSummary from "../components/ListSummary";

type DraftSortMode = "newest" | "oldest" | "title_asc" | "title_desc";

function formatDate(isoString: string | null | undefined) {
  if (!isoString) return "Unknown";

  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;

  return date.toLocaleString();
}

function draftDisplayTitle(draft: PostRecord) {
  return (
    draft.working_title || `${draft.event_title || "Untitled Event"} Draft`
  );
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<PostRecord[]>([]);
  const [draftSearch, setDraftSearch] = useState("");
  const [sortMode, setSortMode] = useState<DraftSortMode>("newest");
  const [expandedDraftId, setExpandedDraftId] = useState<number | null>(null);

  const loadState = useAsyncState();

  async function loadData(showLoadingMessage = true) {
    try {
      if (showLoadingMessage) {
        loadState.start("Loading drafts...");
      }

      const posts = await listPosts();
      const filtered = posts.filter(
        (post) => post.status === "draft" || post.status === "generated",
      );

      setDrafts(filtered);

      if (showLoadingMessage) {
        loadState.succeed("");
      }
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load drafts.",
      );
    }
  }

  useEffect(() => {
    void loadData(true);
  }, []);

  const filteredDrafts = useMemo(() => {
    let result = [...drafts];

    const query = draftSearch.trim().toLowerCase();

    if (query) {
      result = result.filter((draft) => {
        const title = draftDisplayTitle(draft).toLowerCase();
        const eventTitle = (draft.event_title || "").toLowerCase();
        const status = (draft.status || "").toLowerCase();
        const assetFilename = (draft.asset_filename || "").toLowerCase();
        const caption = (draft.draft_caption_current || "").toLowerCase();

        return (
          title.includes(query) ||
          eventTitle.includes(query) ||
          status.includes(query) ||
          assetFilename.includes(query) ||
          caption.includes(query)
        );
      });
    }

    result.sort((a, b) => {
      switch (sortMode) {
        case "oldest":
          return (
            new Date(a.created_at || "").getTime() -
            new Date(b.created_at || "").getTime()
          );
        case "title_asc":
          return draftDisplayTitle(a).localeCompare(draftDisplayTitle(b));
        case "title_desc":
          return draftDisplayTitle(b).localeCompare(draftDisplayTitle(a));
        case "newest":
        default:
          return (
            new Date(b.created_at || "").getTime() -
            new Date(a.created_at || "").getTime()
          );
      }
    });

    return result;
  }, [drafts, draftSearch, sortMode]);

  function toggleExpandedDraft(id: number) {
    setExpandedDraftId((current) => (current === id ? null : id));
  }

  return (
    <section aria-labelledby="drafts-heading">
      <header className="page-header">
        <div>
          <h2 id="drafts-heading">Drafts</h2>
          <p>Work in progress lives here.</p>
        </div>
      </header>

      <ListToolbar
        searchId="draft-search"
        searchValue={draftSearch}
        onSearchChange={setDraftSearch}
        searchPlaceholder="Search title, event, status, asset filename, or caption"
        sortId="draft-sort"
        sortValue={sortMode}
        onSortChange={(v) =>
          setSortMode(v as "newest" | "oldest" | "title_asc" | "title_desc")
        }
        sortOptions={[
          { value: "newest", label: "Newest first" },
          { value: "oldest", label: "Oldest first" },
          { value: "title_asc", label: "Title A–Z" },
          { value: "title_desc", label: "Title Z–A" },
        ]}
      />
      <ListSummary
        visibleCount={filteredDrafts.length}
        totalCount={drafts.length}
        noun="drafts"
        query={draftSearch}
      />

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {!filteredDrafts.length && !loadState.loading && !loadState.error ? (
        <p>No drafts yet.</p>
      ) : (
        <>
          <div className="draft-index-header" aria-hidden="true">
            <span>Title</span>
            <span>Status</span>
            <span>Asset</span>
            <span>Created</span>
          </div>

          <ul className="draft-index-list">
            {filteredDrafts.map((draft) => {
              const isExpanded = expandedDraftId === draft.id;

              return (
                <li key={draft.id} className="draft-index-row">
                  <div
                    className="draft-index-main"
                    onClick={() => toggleExpandedDraft(draft.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpandedDraft(draft.id);
                      }
                    }}
                  >
                    <span className="draft-index-title">
                      {draftDisplayTitle(draft)}
                    </span>
                    <span>{draft.status}</span>
                    <span>
                      {draft.asset_filename ||
                        (draft.asset_id ? `Asset #${draft.asset_id}` : "None")}
                    </span>
                    <span>{formatDate(draft.created_at)}</span>
                  </div>

                  {isExpanded && (
                    <div className="draft-index-details">
                      <article className="card">
                        <h3>
                          {draftDisplayTitle(draft)} —{" "}
                          {formatDate(draft.event_date)}
                        </h3>

                        <p>
                          <strong>Status:</strong> {draft.status}
                        </p>
                        <p>
                          <strong>Event:</strong> {draft.event_title || "None"}
                        </p>
                        <p>
                          <strong>Asset:</strong>{" "}
                          {draft.asset_filename ||
                            (draft.asset_id
                              ? `Asset #${draft.asset_id}`
                              : "None")}
                        </p>
                        <p>
                          <strong>Created:</strong>{" "}
                          {formatDate(draft.created_at)}
                        </p>

                        {draft.draft_caption_current && (
                          <p>
                            <strong>Draft Caption:</strong>{" "}
                            {draft.draft_caption_current}
                          </p>
                        )}

                        <div className="approval-action-row">
                          <Link
                            className="button-link"
                            to={`/drafts/editor?post_id=${draft.id}`}
                          >
                            Open Draft
                          </Link>

                          <button
                            type="button"
                            className="button-danger"
                            onClick={async (e) => {
                              e.stopPropagation();

                              if (!confirm("Delete this draft?")) return;

                              try {
                                await deletePost(draft.id);
                                setDrafts((prev) =>
                                  prev.filter(
                                    (candidate) => candidate.id !== draft.id,
                                  ),
                                );
                                setExpandedDraftId((current) =>
                                  current === draft.id ? null : current,
                                );
                              } catch (err) {
                                console.error(err);
                                alert(
                                  err instanceof Error
                                    ? err.message
                                    : "Failed to delete draft.",
                                );
                              }
                            }}
                          >
                            Delete Draft
                          </button>
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
