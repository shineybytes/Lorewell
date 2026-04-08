import { FormEvent, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getEvent } from "../api/events";
import { listEventAssets, uploadAsset } from "../api/assets";
import type { AssetRecord, EventRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetCard from "../components/AssetCard";
import { useAsyncState } from "../hooks/useAsyncState";
import { useNavigate } from "react-router-dom";
import { deleteEvent } from "../api/events";

export default function EventDetailPage() {
  const { eventId } = useParams();
  const numericEventId = Number(eventId);

  const [event, setEvent] = useState<EventRecord | null>(null);
  const [assets, setAssets] = useState<AssetRecord[]>([]);

  const navigate = useNavigate();

  const loadState = useAsyncState();
  const uploadState = useAsyncState();

  async function loadData() {
    if (!Number.isFinite(numericEventId)) return;

    try {
      loadState.start("Loading event...");

      const [eventData, assetData] = await Promise.all([
        getEvent(numericEventId),
        listEventAssets(numericEventId),
      ]);

      setEvent(eventData);
      setAssets(assetData);
      loadState.succeed("");
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load event.",
      );
    }
  }

  useEffect(() => {
    void loadData();
  }, [numericEventId]);

  async function handleUpload(eventSubmit: FormEvent<HTMLFormElement>) {
    eventSubmit.preventDefault();

    if (!Number.isFinite(numericEventId)) {
      uploadState.fail("Missing event id.");
      return;
    }

    const form = eventSubmit.currentTarget;
    const input = form.elements.namedItem("files") as HTMLInputElement | null;
    const files = input?.files;

    if (!files || files.length === 0) {
      uploadState.fail("Choose at least one file.");
      return;
    }

    try {
      uploadState.start("Uploading assets...");

      for (const file of Array.from(files)) {
        await uploadAsset(numericEventId, file);
      }

      form.reset();
      await loadData();
      uploadState.succeed("Upload complete.");
    } catch (err) {
      console.error(err);
      uploadState.fail(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  if (!Number.isFinite(numericEventId)) {
    return <p>Invalid event id.</p>;
  }

  return (
    <section aria-labelledby="event-detail-heading">
      <p>
        <Link to="/">Back to Events</Link>
      </p>

      <header className="page-header">
        <div>
          <h2 id="event-detail-heading">{event?.title || "Event"}</h2>
        </div>

        {event && (
          <div className="approval-action-row">
            <button
              type="button"
              className="button-danger"
              onClick={async () => {
                if (
                  !confirm(
                    "Delete this event? This may affect related assets and drafts.",
                  )
                ) {
                  return;
                }

                try {
                  await deleteEvent(numericEventId);
                  navigate("/");
                } catch (err) {
                  console.error(err);
                  alert(
                    err instanceof Error
                      ? err.message
                      : "Failed to delete event.",
                  );
                }
              }}
            >
              Delete Event
            </button>
          </div>
        )}
      </header>

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {event && (
        <>
          <section aria-labelledby="event-info-heading">
            <h3 id="event-info-heading">Event Info</h3>
            <p>
              <strong>Type:</strong> {event.event_type || "None"}
            </p>
            <p>
              <strong>Location:</strong> {event.location || "None"}
            </p>
            <p>
              <strong>Date:</strong>{" "}
              {event.event_date
                ? event.event_timezone
                  ? `${event.event_date} (${event.event_timezone})`
                  : event.event_date
                : "Unknown"}
            </p>
            <p>
              <strong>Recap:</strong> {event.recap || "No recap provided."}
            </p>
            <p>
              <strong>Guidance:</strong>{" "}
              {event.event_guidance || "No guidance provided."}
            </p>
          </section>

          <section aria-labelledby="upload-heading">
            <h3 id="upload-heading">Upload Assets to This Event</h3>

            <form onSubmit={handleUpload}>
              <div className="form-row">
                <label htmlFor="asset-upload">Choose images or videos</label>
                <input id="asset-upload" name="files" type="file" multiple />
              </div>

              <button type="submit" disabled={uploadState.loading}>
                {uploadState.loading ? "Uploading..." : "Upload Assets"}
              </button>
            </form>

            <StatusMessage
              loading={uploadState.loading}
              status={uploadState.status}
              error={uploadState.error}
            />
          </section>

          <section aria-labelledby="assets-heading">
            <h3 id="assets-heading">Assets</h3>

            {!assets.length ? (
              <p>No assets uploaded yet.</p>
            ) : (
              <ul className="card-list">
                {assets.map((asset) => (
                  <li key={asset.id}>
                    <AssetCard
                      asset={asset}
                      eventId={numericEventId}
                      onRefresh={loadData}
                    />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}
