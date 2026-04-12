import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { getEvent, deleteEvent, updateEvent } from "../api/events";
import {
  listAssets,
  listEventAssets,
  updateAssetEvent,
  uploadAsset,
} from "../api/assets";
import type { AssetRecord, EventRecord, VendorEntry } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetCard from "../components/AssetCard";
import { useAsyncState } from "../hooks/useAsyncState";
import CreditsEditor, {
  parseVendorEntries,
  serializeVendorEntries,
} from "../components/CreditsEditor";
import { proposeAssetAnalysis } from "../api/assets";

function parseStructuredVendors(
  vendors: string | null | undefined,
): VendorEntry[] | null {
  if (!vendors) return null;

  try {
    const parsed = JSON.parse(vendors);

    if (!Array.isArray(parsed)) return null;

    const cleaned = parsed
      .filter(
        (item) =>
          typeof item === "object" &&
          item !== null &&
          ("role" in item || "instagram" in item),
      )
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

    return cleaned.length ? cleaned : null;
  } catch {
    return null;
  }
}

function filenameFromPath(filePath: string) {
  return filePath.split("/").pop() || filePath;
}

export default function EventDetailPage() {
  const { eventId } = useParams();
  const numericEventId = Number(eventId);

  const [event, setEvent] = useState<EventRecord | null>(null);
  const [assets, setAssets] = useState<AssetRecord[]>([]);
  const [allAssets, setAllAssets] = useState<AssetRecord[]>([]);
  const [selectedExistingAssetId, setSelectedExistingAssetId] =
    useState<string>("");

  const [uploadProgress, setUploadProgress] = useState<{
    currentFileName: string;
    currentFileIndex: number;
    totalFiles: number;
    percent: number;
  } | null>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [editState, setEditState] = useState<EventRecord | null>(null);
  const [vendorEntries, setVendorEntries] = useState<VendorEntry[]>([
    { role: "", instagram: "" },
  ]);

  const navigate = useNavigate();

  const loadState = useAsyncState();
  const uploadState = useAsyncState();
  const saveEventState = useAsyncState();
  const attachAssetState = useAsyncState();

  async function loadData() {
    if (!Number.isFinite(numericEventId)) return;

    try {
      loadState.start("Loading event...");

      const [eventData, assetData, libraryData] = await Promise.all([
        getEvent(numericEventId),
        listEventAssets(numericEventId),
        listAssets(),
      ]);

      setEvent(eventData);
      setEditState(eventData);
      setVendorEntries(parseVendorEntries(eventData.vendors));
      setAssets(assetData);
      setAllAssets(libraryData);
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

  const attachableAssets = useMemo(() => {
    return allAssets.filter((asset) => asset.event_id == null);
  }, [allAssets]);

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

    const fileList = Array.from(files);

    try {
      uploadState.start(`Uploading 1 of ${fileList.length}...`);
      setUploadProgress({
        currentFileName: fileList[0].name,
        currentFileIndex: 1,
        totalFiles: fileList.length,
        percent: 0,
      });

      for (const [index, file] of fileList.entries()) {
        setUploadProgress({
          currentFileName: file.name,
          currentFileIndex: index + 1,
          totalFiles: fileList.length,
          percent: 0,
        });

        uploadState.start(`Uploading ${index + 1} of ${fileList.length}...`);

        await uploadAsset(numericEventId, file, (percent) => {
          setUploadProgress({
            currentFileName: file.name,
            currentFileIndex: index + 1,
            totalFiles: fileList.length,
            percent,
          });
        });
      }

      form.reset();
      setUploadProgress(null);
      await loadData();
      await new Promise((resolve) => setTimeout(resolve, 400));
      uploadState.succeed("Upload complete.");
    } catch (err) {
      console.error(err);
      uploadState.fail(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploadProgress(null);
    }
  }

  async function handleSaveEvent() {
    if (!editState || !Number.isFinite(numericEventId)) return;

    try {
      saveEventState.start("Saving event changes...");

      const updated = await updateEvent(numericEventId, {
        title: editState.title,
        event_type: editState.event_type || null,
        location: editState.location || null,
        event_date: editState.event_date || null,
        event_timezone: editState.event_timezone || null,
        recap: editState.recap || null,
        keywords: editState.keywords || null,
        vendors: serializeVendorEntries(vendorEntries),
        event_guidance: editState.event_guidance || null,
      });

      setEvent(updated);
      setEditState(updated);
      setVendorEntries(parseVendorEntries(updated.vendors));
      setIsEditing(false);
      saveEventState.succeed("Event updated.");
    } catch (err) {
      console.error(err);
      saveEventState.fail(
        err instanceof Error ? err.message : "Failed to update event.",
      );
    }
  }

  async function handleAttachExistingAsset() {
    if (!selectedExistingAssetId) {
      attachAssetState.fail("Choose an existing asset to attach.");
      return;
    }

    try {
      attachAssetState.start("Attaching asset...");

      const assetId = Number(selectedExistingAssetId);

      await updateAssetEvent(assetId, numericEventId);
      setSelectedExistingAssetId("");
      await loadData();

      const shouldPropose = window.confirm(
        "Would you like to generate a proposed analysis using the new event context?\n\n" +
          "This will use AI tokens.\n\n" +
          "Press OK to generate.\n" +
          "Press Cancel to keep the current analysis.",
      );

      if (shouldPropose) {
        await proposeAssetAnalysis(assetId);
        attachAssetState.succeed(
          "Asset attached. Proposed analysis generated. Review it in Assets.",
        );
      } else {
        attachAssetState.succeed("Asset attached to event.");
      }
    } catch (err) {
      console.error(err);
      attachAssetState.fail(
        err instanceof Error ? err.message : "Failed to attach asset.",
      );
    }
  }

  if (!Number.isFinite(numericEventId)) {
    return <p>Invalid event id.</p>;
  }

  const structuredVendors = parseStructuredVendors(event?.vendors);

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
              onClick={() => {
                if (isEditing) {
                  setEditState(event);
                  setVendorEntries(parseVendorEntries(event.vendors));
                  setIsEditing(false);
                } else {
                  setIsEditing(true);
                }
              }}
            >
              {isEditing ? "Cancel Editing" : "Edit Event"}
            </button>

            <button
              type="button"
              className="button-danger"
              onClick={async () => {
                if (
                  !confirm(
                    "Delete this event?\n\nAssets, drafts, and approvals will be preserved. They will no longer be associated with this event.",
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
          {!isEditing ? (
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
              <p>
                <strong>Keywords:</strong> {event.keywords || "None"}
              </p>

              {structuredVendors ? (
                <div>
                  <strong>Vendors / collaborators:</strong>
                  <ul>
                    {structuredVendors.map((vendor, index) => (
                      <li key={`${vendor.role}-${vendor.instagram}-${index}`}>
                        {vendor.role || "Contributor"}
                        {vendor.instagram ? ` — ${vendor.instagram}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : event.vendors ? (
                <p>
                  <strong>Vendors:</strong> {event.vendors}
                </p>
              ) : null}
            </section>
          ) : (
            <section aria-labelledby="edit-event-heading">
              <h3 id="edit-event-heading">Edit Event</h3>
              <p className="helper-text">* Required</p>

              {editState && (
                <>
                  <div className="form-row">
                    <label htmlFor="edit-title">Title *</label>
                    <input
                      id="edit-title"
                      required
                      value={editState.title}
                      onChange={(e) =>
                        setEditState({ ...editState, title: e.target.value })
                      }
                    />
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-event-type">Event Type</label>
                    <input
                      id="edit-event-type"
                      value={editState.event_type || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          event_type: e.target.value || null,
                        })
                      }
                    />
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-location">Location</label>
                    <input
                      id="edit-location"
                      value={editState.location || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          location: e.target.value || null,
                        })
                      }
                    />
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-event-date">
                      Event Date &amp; Time
                    </label>
                    <input
                      id="edit-event-date"
                      type="datetime-local"
                      value={editState.event_date || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          event_date: e.target.value || null,
                        })
                      }
                    />
                    <p className="helper-text">
                      Optional. If you add a date/time, also provide a timezone.
                    </p>
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-event-timezone">Event Timezone</label>
                    <input
                      id="edit-event-timezone"
                      value={editState.event_timezone || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          event_timezone: e.target.value || null,
                        })
                      }
                    />
                    <p className="helper-text">
                      Optional unless you provide an event date/time.
                    </p>
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-recap">Recap</label>
                    <textarea
                      id="edit-recap"
                      rows={5}
                      value={editState.recap || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          recap: e.target.value || null,
                        })
                      }
                    />
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-guidance">Event Guidance</label>
                    <textarea
                      id="edit-guidance"
                      rows={4}
                      value={editState.event_guidance || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          event_guidance: e.target.value || null,
                        })
                      }
                    />
                  </div>

                  <div className="form-row">
                    <label htmlFor="edit-keywords">Keywords</label>
                    <input
                      id="edit-keywords"
                      value={editState.keywords || ""}
                      onChange={(e) =>
                        setEditState({
                          ...editState,
                          keywords: e.target.value || null,
                        })
                      }
                    />
                    <p className="helper-text">Optional, comma-delimited.</p>
                  </div>

                  <CreditsEditor
                    entries={vendorEntries}
                    onEntriesChange={setVendorEntries}
                  />

                  <div className="form-actions">
                    <button type="button" onClick={handleSaveEvent}>
                      Save Changes
                    </button>
                  </div>

                  <StatusMessage
                    loading={saveEventState.loading}
                    status={saveEventState.status}
                    error={saveEventState.error}
                  />
                </>
              )}
            </section>
          )}

          <section aria-labelledby="upload-heading">
            <h3 id="upload-heading">Add Assets (optional)</h3>

            <form onSubmit={handleUpload}>
              <div className="form-row">
                <label htmlFor="asset-upload">Choose images or videos</label>
                <input
                  id="asset-upload"
                  name="files"
                  type="file"
                  multiple
                  disabled={uploadState.loading}
                />
                <p className="helper-text">
                  Optional. Upload media now or come back later. Media must meet
                  Instagram filetype and size standards.
                </p>
              </div>

              <button type="submit" disabled={uploadState.loading}>
                {uploadState.loading ? "Uploading..." : "Upload Assets"}
              </button>
            </form>

            {uploadProgress && (
              <div className="form-row">
                <label>
                  Upload Progress: file {uploadProgress.currentFileIndex} of{" "}
                  {uploadProgress.totalFiles}
                </label>
                <progress value={uploadProgress.percent} max={100} />
                <p className="helper-text">
                  Uploading <strong>{uploadProgress.currentFileName}</strong> —{" "}
                  {uploadProgress.percent}%
                </p>
              </div>
            )}

            <StatusMessage
              loading={uploadState.loading}
              status={uploadState.status}
              error={uploadState.error}
            />
          </section>

          <section aria-labelledby="attach-existing-heading">
            <h3 id="attach-existing-heading">Attach Existing Asset</h3>
            <p className="helper-text">
              Use media already in your library instead of uploading it again.
            </p>

            <div className="form-row">
              <label htmlFor="existing-asset-select">Unassigned Assets</label>
              <select
                id="existing-asset-select"
                value={selectedExistingAssetId}
                onChange={(e) => setSelectedExistingAssetId(e.target.value)}
              >
                <option value="">Choose an asset</option>
                {attachableAssets.map((asset) => (
                  <option key={asset.id} value={String(asset.id)}>
                    {filenameFromPath(asset.file_path)} — {asset.media_type}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-actions">
              <button type="button" onClick={handleAttachExistingAsset}>
                Attach Asset
              </button>
            </div>

            <StatusMessage
              loading={attachAssetState.loading}
              status={attachAssetState.status}
              error={attachAssetState.error}
            />
          </section>

          <section aria-labelledby="assets-heading">
            <h3 id="assets-heading">Assets</h3>

            {!assets.length ? (
              <p>
                No assets yet. You can still edit event details, attach existing
                assets, and upload media later.
              </p>
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
