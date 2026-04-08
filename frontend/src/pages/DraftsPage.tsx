import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPosts } from "../api/posts";
import { deletePost } from "../api/posts";
import type { PostRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";

function formatDate(isoString: string) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;
  return date.toLocaleString();
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<PostRecord[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setStatus("Loading drafts...");
        setError("");

        const posts = await listPosts();
        const filtered = posts.filter(
          (post) => post.status === "draft" || post.status === "generated",
        );

        setDrafts(filtered);
        setStatus("");
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load drafts.");
        setStatus("");
      }
    }

    void load();
  }, []);

  return (
    <section aria-labelledby="drafts-heading">
      <header className="page-header">
        <div>
          <h2 id="drafts-heading">Drafts</h2>
          <p>Work in progress lives here.</p>
        </div>
      </header>

      <StatusMessage status={status} error={error} />

      {!drafts.length && !status && !error ? (
        <p>No drafts yet.</p>
      ) : (
        <ul className="card-list">
          {drafts.map((draft) => (
            <li key={draft.id}>
              <article className="card">
                <h3>Draft #{draft.id}</h3>
                <p>
                  <strong>Status:</strong> {draft.status}
                </p>
                <p>
                  <strong>Event:</strong> {draft.event_id ?? "None"}
                </p>
                <p>
                  <strong>Asset:</strong> {draft.asset_id}
                </p>
                <p>
                  <strong>Created:</strong> {formatDate(draft.created_at)}
                </p>

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
                    onClick={async () => {
                      if (!confirm("Delete this draft?")) return;

                      try {
                        await deletePost(draft.id);

                        // remove locally (faster UX than full reload)
                        setDrafts((prev) =>
                          prev.filter((d) => d.id !== draft.id),
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
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
