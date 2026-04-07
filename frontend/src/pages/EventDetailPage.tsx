import { FormEvent, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getEvent } from "../api/events";
import { listEventAssets, uploadAsset } from "../api/assets";
import type { AssetRecord, EventRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetPreview from "../components/AssetPreview";
import AssetCard from "../components/AssetCard";

export default function EventDetailPage() {
  const { eventId } = useParams();
  const numericEventId = Number(eventId);

  const [event, setEvent] = useState<EventRecord | null>(null);
  const [assets, setAssets] = useState<AssetRecord[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");

  async function loadData() {
    if (!Number.isFinite(numericEventId)) return;

    try {
      setStatus("Loading event...");
      setError("");

      const [eventData, assetData] = await Promise.all([
        getEvent(numericEventId),
        listEventAssets(numericEventId),
      ]);

      setEvent(eventData);
      setAssets(assetData);
      setStatus("");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load event.");
      setStatus("");
    }
  }

  useEffect(() => {
    void loadData();
  }, [numericEventId]);

  async function handleUpload(eventSubmit: FormEvent<HTMLFormElement>) {
    eventSubmit.preventDefault();
    setUploadStatus("");
    setUploadError("");

    if (!Number.isFinite(numericEventId)) {
      setUploadError("Missing event id.");
      return;
    }

    const form = eventSubmit.currentTarget;
    const input = form.elements.namedItem("files") as HTMLInputElement | null;
    const files = input?.files;

    if (!files || files.length === 0) {
      setUploadError("Choose at least one file.");
      return;
    }

    try {
      setUploadStatus("Uploading assets...");

      for (const file of Array.from(files)) {
        await uploadAsset(numericEventId, file);
      }

      setUploadStatus("Upload complete.");
      form.reset();
      await loadData();
    } catch (err) {
      console.error(err);
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
      setUploadStatus("");
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

      <h2 id="event-detail-heading">{event?.title || "Event"}</h2>

      <StatusMessage status={status} error={error} />

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
              <strong>Guidance:</strong> {event.event_guidance || "No guidance provided."}
            </p>
          </section>

          <section aria-labelledby="upload-heading">
            <h3 id="upload-heading">Upload Assets to This Event</h3>

            <form onSubmit={handleUpload}>
              <div className="form-row">
                <label htmlFor="asset-upload">Choose images or videos</label>
                <input id="asset-upload" name="files" type="file" multiple />
              </div>

              <button type="submit">Upload Assets</button>
            </form>

            <StatusMessage status={uploadStatus} error={uploadError} />
          </section>

          <section aria-labelledby="assets-heading">
            <h3 id="assets-heading">Assets</h3>

            {!assets.length ? (
              <p>No assets uploaded yet.</p>
            ) : (
			<ul className="card-list">
			{assets.map((asset) => (
				<li key={asset.id}>
				<AssetCard asset={asset} eventId={numericEventId} onRefresh={loadData} />
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
