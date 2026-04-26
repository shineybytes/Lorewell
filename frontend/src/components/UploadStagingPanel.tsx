import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { uploadAssetNoEvent } from "../api/assets";
import StatusMessage from "./StatusMessage";
import { useAsyncState } from "../hooks/useAsyncState";

type StageFilter =
  | "all"
  | "ready"
  | "warning"
  | "blocked"
  | "uploading"
  | "failed";

type UploadStageStatus =
  | "ready"
  | "warning"
  | "blocked"
  | "uploading"
  | "done"
  | "failed"
  | "removed";

type UploadStageItem = {
  id: string;
  file: File;
  name: string;
  size: number;
  extension: string;
  mediaKind: "image" | "video" | "unknown";
  status: UploadStageStatus;
  message: string;
  progress: number;
};

type UploadStagingPanelProps = {
  onUploadComplete: () => Promise<void>;
};

const MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024;
const MAX_VIDEO_SIZE_BYTES = 300 * 1024 * 1024;
const ROW_MODE_THRESHOLD = 12;

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function getExtension(filename: string) {
  const parts = filename.toLowerCase().split(".");
  return parts.length > 1 ? parts[parts.length - 1] : "";
}

function classifyMedia(file: File): {
  extension: string;
  mediaKind: "image" | "video" | "unknown";
  status: UploadStageStatus;
  message: string;
} {
  const extension = getExtension(file.name);

  const imageExts = new Set(["jpg", "jpeg", "png"]);
  const videoExts = new Set(["mp4", "mov", "3gpp"]);

  if (imageExts.has(extension)) {
    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      return {
        extension,
        mediaKind: "image",
        status: "blocked",
        message: "Image exceeds 8 MB current limit.",
      };
    }

    if (extension === "png") {
      return {
        extension,
        mediaKind: "image",
        status: "warning",
        message:
          "PNG is ingestable but may not be ideal for Instagram publishing.",
      };
    }

    return {
      extension,
      mediaKind: "image",
      status: "ready",
      message: "Ready to upload.",
    };
  }

  if (videoExts.has(extension)) {
    if (file.size > MAX_VIDEO_SIZE_BYTES) {
      return {
        extension,
        mediaKind: "video",
        status: "blocked",
        message: "Video exceeds 300 MB current limit.",
      };
    }

    if (extension === "mov" || extension === "3gpp") {
      return {
        extension,
        mediaKind: "video",
        status: "warning",
        message:
          "This format may need conversion for Instagram publishing later.",
      };
    }

    return {
      extension,
      mediaKind: "video",
      status: "ready",
      message: "Ready to upload.",
    };
  }

  return {
    extension,
    mediaKind: "unknown",
    status: "blocked",
    message: "Unsupported file type for current Lorewell intake.",
  };
}

function makeStageItem(file: File, index: number): UploadStageItem {
  const classification = classifyMedia(file);

  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${index}`,
    file,
    name: file.name,
    size: file.size,
    extension: classification.extension,
    mediaKind: classification.mediaKind,
    status: classification.status,
    message: classification.message,
    progress: 0,
  };
}

export default function UploadStagingPanel({
  onUploadComplete,
}: UploadStagingPanelProps) {
  const [stageFilter, setStageFilter] = useState<StageFilter>("all");
  const [stagedFiles, setStagedFiles] = useState<UploadStageItem[]>([]);
  const [expandedStageItemId, setExpandedStageItemId] = useState<string | null>(
    null,
  );

  const uploadState = useAsyncState();

  const visibleStagedFiles = stagedFiles.filter(
    (item) => item.status !== "removed",
  );

  const stageCounts = useMemo(
    () => ({
      all: visibleStagedFiles.length,
      ready: visibleStagedFiles.filter((item) => item.status === "ready")
        .length,
      warning: visibleStagedFiles.filter((item) => item.status === "warning")
        .length,
      blocked: visibleStagedFiles.filter((item) => item.status === "blocked")
        .length,
      uploading: visibleStagedFiles.filter(
        (item) => item.status === "uploading",
      ).length,
      failed: visibleStagedFiles.filter((item) => item.status === "failed")
        .length,
    }),
    [visibleStagedFiles],
  );

  const filteredStagedFiles =
    stageFilter === "all"
      ? visibleStagedFiles
      : visibleStagedFiles.filter((item) => item.status === stageFilter);

  const uploadableStageItems = stagedFiles.filter(
    (item) =>
      item.status === "ready" ||
      item.status === "warning" ||
      item.status === "failed",
  );

  const useRowMode = filteredStagedFiles.length > ROW_MODE_THRESHOLD;

  useEffect(() => {
    if (stageFilter === "all") return;
    if (stageCounts[stageFilter] === 0) {
      setStageFilter("all");
    }
  }, [stageFilter, stageCounts]);

  function handleStageSelection(event: ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || files.length === 0) {
      return;
    }

    const nextItems = Array.from(files).map((file, index) =>
      makeStageItem(file, index),
    );

    setStagedFiles((prev) => [...prev, ...nextItems]);
    event.target.value = "";
  }

  function removeStagedFile(id: string) {
    setStagedFiles((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, status: "removed" } : item,
      ),
    );

    setExpandedStageItemId((current) => (current === id ? null : current));
  }

  function removeBlockedFiles() {
    setStagedFiles((prev) =>
      prev.map((item) =>
        item.status === "blocked" ? { ...item, status: "removed" } : item,
      ),
    );

    setExpandedStageItemId((current) => {
      const expanded = visibleStagedFiles.find((item) => item.id === current);
      return expanded?.status === "blocked" ? null : current;
    });
  }

  function clearFinishedFiles() {
    setStagedFiles((prev) =>
      prev.filter(
        (item) => item.status !== "done" && item.status !== "removed",
      ),
    );

    setExpandedStageItemId((current) => {
      const expanded = stagedFiles.find((item) => item.id === current);
      return expanded &&
        (expanded.status === "done" || expanded.status === "removed")
        ? null
        : current;
    });
  }

  function toggleExpandedStageItem(id: string) {
    setExpandedStageItemId((current) => (current === id ? null : id));
  }

  async function handleUploadStagedFiles() {
    if (uploadableStageItems.length === 0) {
      uploadState.fail("No ready files to upload.");
      return;
    }

    uploadState.start(
      uploadableStageItems.length === 1
        ? "Uploading 1 asset..."
        : `Uploading ${uploadableStageItems.length} assets...`,
    );

    let successCount = 0;
    let failureCount = 0;

    for (const item of uploadableStageItems) {
      setStagedFiles((prev) =>
        prev.map((candidate) =>
          candidate.id === item.id
            ? {
                ...candidate,
                status: "uploading",
                progress: 0,
                message: "Uploading...",
              }
            : candidate,
        ),
      );

      try {
        await uploadAssetNoEvent(item.file, (percent) => {
          setStagedFiles((prev) =>
            prev.map((candidate) =>
              candidate.id === item.id
                ? {
                    ...candidate,
                    progress: percent,
                  }
                : candidate,
            ),
          );
        });

        successCount += 1;

        setStagedFiles((prev) =>
          prev.map((candidate) =>
            candidate.id === item.id
              ? {
                  ...candidate,
                  status: "done",
                  progress: 100,
                  message: "Uploaded successfully.",
                }
              : candidate,
          ),
        );
      } catch (err) {
        console.error(err);
        failureCount += 1;

        setStagedFiles((prev) =>
          prev.map((candidate) =>
            candidate.id === item.id
              ? {
                  ...candidate,
                  status: "failed",
                  message:
                    err instanceof Error ? err.message : "Upload failed.",
                }
              : candidate,
          ),
        );
      }
    }

    await onUploadComplete();

    if (failureCount === 0) {
      uploadState.succeed(
        successCount === 1
          ? "1 asset uploaded successfully."
          : `${successCount} assets uploaded successfully.`,
      );
      return;
    }

    if (successCount === 0) {
      uploadState.fail("All uploads failed.");
      return;
    }

    uploadState.succeed(
      `${successCount} uploaded, ${failureCount} failed. Review the staging list for details.`,
    );
  }

  return (
    <section aria-labelledby="asset-upload-heading">
      <h3 id="asset-upload-heading">Upload Assets</h3>

      <div className="form-row">
        <label htmlFor="asset-library-upload">Choose images or videos</label>
        <input
          id="asset-library-upload"
          name="file"
          type="file"
          multiple
          disabled={uploadState.loading}
          onChange={handleStageSelection}
        />
        <p className="helper-text">
          Files are staged first so you can review warnings and remove blocked
          items before upload.
        </p>
      </div>

      <div className="upload-staging-legend helper-text">
        <span>
          <strong className="status-ready">Ready</strong>: Accepted
        </span>
        <span>
          <strong className="status-warning">Warning</strong>: Please review
        </span>
        <span>
          <strong className="status-blocked">Blocked</strong>: Not accepted
        </span>
      </div>

      {visibleStagedFiles.length > 0 && (
        <section
          className="card"
          aria-labelledby="upload-staging-heading"
          style={{ marginBottom: "1rem" }}
        >
          <div className="page-header">
            <div>
              <h4 id="upload-staging-heading">Upload Staging</h4>
              <p className="helper-text">
                Review each file before Lorewell ingests it.
              </p>
            </div>

            <div className="approval-action-row asset-library-controls">
              <button type="button" onClick={removeBlockedFiles}>
                Remove Blocked
              </button>
              <button type="button" onClick={clearFinishedFiles}>
                Clear Finished
              </button>
              <button
                type="button"
                onClick={handleUploadStagedFiles}
                disabled={
                  uploadState.loading || uploadableStageItems.length === 0
                }
              >
                {uploadState.loading ? "Uploading..." : "Upload Ready Files"}
              </button>
            </div>
          </div>

          <div className="upload-staging-toolbar">
            <div className="upload-staging-summary helper-text">
              <span>
                <strong className="status-ready">{stageCounts.ready}</strong>{" "}
                Ready
              </span>
              <span>
                <strong className="status-warning">
                  {stageCounts.warning}
                </strong>{" "}
                Warning
              </span>
              <span>
                <strong className="status-blocked">
                  {stageCounts.blocked}
                </strong>{" "}
                Blocked
              </span>
              <span>
                <strong className="status-uploading">
                  {stageCounts.uploading}
                </strong>{" "}
                Uploading
              </span>
              <span>
                <strong className="status-failed">{stageCounts.failed}</strong>{" "}
                Failed
              </span>
            </div>

            <div
              className="tab-row upload-staging-filters"
              role="tablist"
              aria-label="Upload staging filters"
            >
              <button
                type="button"
                className={
                  stageFilter === "all" ? "tab-button active" : "tab-button"
                }
                onClick={() => setStageFilter("all")}
              >
                All ({stageCounts.all})
              </button>
              <button
                type="button"
                className={
                  stageFilter === "ready" ? "tab-button active" : "tab-button"
                }
                onClick={() => setStageFilter("ready")}
              >
                Ready ({stageCounts.ready})
              </button>
              <button
                type="button"
                className={
                  stageFilter === "warning" ? "tab-button active" : "tab-button"
                }
                onClick={() => setStageFilter("warning")}
              >
                Warning ({stageCounts.warning})
              </button>
              <button
                type="button"
                className={
                  stageFilter === "blocked" ? "tab-button active" : "tab-button"
                }
                onClick={() => setStageFilter("blocked")}
              >
                Blocked ({stageCounts.blocked})
              </button>
              <button
                type="button"
                className={
                  stageFilter === "uploading"
                    ? "tab-button active"
                    : "tab-button"
                }
                onClick={() => setStageFilter("uploading")}
              >
                Uploading ({stageCounts.uploading})
              </button>
              <button
                type="button"
                className={
                  stageFilter === "failed" ? "tab-button active" : "tab-button"
                }
                onClick={() => setStageFilter("failed")}
              >
                Failed ({stageCounts.failed})
              </button>
            </div>
          </div>

          {filteredStagedFiles.length === 0 ? (
            <p className="helper-text">No files match this filter.</p>
          ) : useRowMode ? (
            <ul className="upload-staging-list">
              {filteredStagedFiles.map((item) => (
                <li key={item.id} className="upload-staging-row-compact">
                  <div
                    className="upload-staging-main"
                    onClick={() => toggleExpandedStageItem(item.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpandedStageItem(item.id);
                      }
                    }}
                  >
                    <span className="upload-name">{item.name}</span>
                    <span>{formatBytes(item.size)}</span>
                    <span>{item.mediaKind}</span>
                    <span className={`status-${item.status}`}>
                      {item.status}
                    </span>

                    {item.status !== "uploading" && item.status !== "done" ? (
                      <button
                        type="button"
                        className="button-danger"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeStagedFile(item.id);
                        }}
                      >
                        ✕
                      </button>
                    ) : (
                      <span />
                    )}
                  </div>

                  {expandedStageItemId === item.id && (
                    <div className="upload-staging-details">
                      <p>{item.message}</p>

                      <p>
                        <strong>Detected:</strong>{" "}
                        {item.mediaKind === "unknown"
                          ? "Unknown"
                          : `${item.mediaKind} (${item.extension || "no extension"})`}
                      </p>

                      {item.status === "uploading" && (
                        <progress max={100} value={item.progress}>
                          {item.progress}%
                        </progress>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <ul className="card-list">
              {filteredStagedFiles.map((item) => (
                <li key={item.id}>
                  <article className="card">
                    <div className="page-header">
                      <div>
                        <h4>{item.name}</h4>
                        <p>
                          <strong>Size:</strong> {formatBytes(item.size)}
                        </p>
                        <p>
                          <strong>Detected:</strong>{" "}
                          {item.mediaKind === "unknown"
                            ? "Unknown"
                            : `${item.mediaKind} (${item.extension || "no extension"})`}
                        </p>
                        <p>
                          <strong>Status:</strong> {item.status}
                        </p>
                        <p className="helper-text">{item.message}</p>

                        {item.status === "uploading" && (
                          <progress max={100} value={item.progress}>
                            {item.progress}%
                          </progress>
                        )}
                      </div>

                      <div className="approval-action-row">
                        {item.status !== "uploading" &&
                          item.status !== "done" && (
                            <button
                              type="button"
                              className="button-danger"
                              onClick={() => removeStagedFile(item.id)}
                            >
                              Remove
                            </button>
                          )}
                      </div>
                    </div>
                  </article>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <StatusMessage
        loading={uploadState.loading}
        status={uploadState.status}
        error={uploadState.error}
      />
    </section>
  );
}
