import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { AssetRecord } from "../types/api";
import AssetPreview from "./AssetPreview";
import StatusMessage from "./StatusMessage";
import {
  approveAssetAccessibility,
  deleteAsset,
  reanalyzeAsset,
} from "../api/assets";
import { useAsyncState } from "../hooks/useAsyncState";

type AssetCardProps = {
  asset: AssetRecord;
  eventId?: number | null;
  onRefresh: () => Promise<void>;
  compactPreview?: boolean;
  collapsed?: boolean;
};

function filenameFromPath(filePath: string) {
  return filePath.split("/").pop() || filePath;
}

function displayAssetName(asset: AssetRecord) {
  return asset.display_name || filenameFromPath(asset.file_path);
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) return "Unknown";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export default function AssetCard({
  asset,
  eventId,
  onRefresh,
  compactPreview = false,
  collapsed = false,
}: AssetCardProps) {
  const [correction, setCorrection] = useState(
    asset.analysis_user_correction || "",
  );
  const [finalAccessibility, setFinalAccessibility] = useState(
    asset.accessibility_text_final || asset.accessibility_text_generated || "",
  );

  useEffect(() => {
    setCorrection(asset.analysis_user_correction || "");
  }, [asset.analysis_user_correction]);

  useEffect(() => {
    setFinalAccessibility(
      asset.accessibility_text_final ||
        asset.accessibility_text_generated ||
        "",
    );
  }, [asset.accessibility_text_final, asset.accessibility_text_generated]);

  const reanalyzeState = useAsyncState();
  const approveState = useAsyncState();

  const resolvedEventId = useMemo(() => {
    return eventId ?? asset.event_id ?? null;
  }, [eventId, asset.event_id]);

  const draftHref = resolvedEventId
    ? `/drafts/editor?asset_id=${asset.id}&event_id=${resolvedEventId}`
    : `/drafts/editor?asset_id=${asset.id}`;

  async function handleReanalyze() {
    try {
      reanalyzeState.start(
        asset.media_type === "video"
          ? "Analyzing sampled video frames..."
          : "Analyzing image...",
      );
      await reanalyzeAsset(asset.id, correction);
      await onRefresh();
      reanalyzeState.succeed("Asset analyzed.");
    } catch (err) {
      console.error(err);
      reanalyzeState.fail(
        err instanceof Error ? err.message : "Failed to analyze asset.",
      );
    }
  }

  async function handleApproveAccessibility() {
    try {
      approveState.start("Saving accessibility text...");
      await approveAssetAccessibility(asset.id, finalAccessibility);
      await onRefresh();
      approveState.succeed("Accessibility approved.");
    } catch (err) {
      console.error(err);
      approveState.fail(
        err instanceof Error
          ? err.message
          : "Failed to approve accessibility text.",
      );
    }
  }

  async function handleDeleteAsset() {
    if (
      !confirm(
        "Delete this asset? This may affect drafts or approved posts that depend on it.",
      )
    ) {
      return;
    }

    try {
      await deleteAsset(asset.id);
      await onRefresh();
    } catch (err) {
      console.error(err);
      alert(err instanceof Error ? err.message : "Failed to delete asset.");
    }
  }

  return (
    <div className="approval-review-layout">
      <div className="approval-preview-column">
        <h4>{displayAssetName(asset)}</h4>
        <AssetPreview asset={asset} compact={compactPreview} />

        <p>
          <strong>Type:</strong> {asset.media_type}
        </p>
        <p>
          <strong>Status:</strong> {asset.analysis_status}
        </p>
        <p>
          <strong>Uploaded:</strong> {formatTimestamp(asset.created_at)}
        </p>
        <p className="helper-text">
          {asset.media_type === "video"
            ? "Video analysis uses sampled frames from the clip."
            : "Image analysis is based on the uploaded media."}
        </p>

        <div className="approval-action-row">
          <Link className="button-link" to={draftHref}>
            Create Draft
          </Link>

          <button type="button" onClick={handleReanalyze}>
            {reanalyzeState.loading
              ? asset.media_type === "video"
                ? "Analyzing video..."
                : "Analyzing..."
              : asset.analysis_status === "pending"
                ? "Analyze"
                : "Retry Analysis"}
          </button>

          <button
            type="button"
            className="button-danger"
            onClick={handleDeleteAsset}
          >
            Delete Asset
          </button>
        </div>

        <StatusMessage
          loading={reanalyzeState.loading}
          status={reanalyzeState.status}
          error={reanalyzeState.error}
        />
      </div>

      {!collapsed && (
        <div className="approval-details-column">
          <details>
            <summary>Show Details</summary>

            <div className="form-row" style={{ marginTop: "1rem" }}>
              <p>
                <strong>Visual summary:</strong>
              </p>
              <p>{asset.vision_summary_generated || "None"}</p>
            </div>

            <div>
              <p>
                <strong>Generated accessibility:</strong>
              </p>
              <p>{asset.accessibility_text_generated || "None"}</p>
            </div>

            <div>
              <p>
                <strong>Final accessibility:</strong>
              </p>
              <p>{asset.accessibility_text_final || "None"}</p>
            </div>

            <div className="form-row">
              <label htmlFor={`correction-${asset.id}`}>Correction</label>
              <textarea
                id={`correction-${asset.id}`}
                value={correction}
                onChange={(e) => setCorrection(e.target.value)}
              />
              <p className="helper-text">
                Optional. Add clarification if the current analysis missed the
                subject, setting, or action.
              </p>
            </div>

            <div className="form-row">
              <label htmlFor={`final-accessibility-${asset.id}`}>
                Final Accessibility Text
              </label>
              <textarea
                id={`final-accessibility-${asset.id}`}
                value={finalAccessibility}
                onChange={(e) => setFinalAccessibility(e.target.value)}
              />
            </div>

            <button
              type="button"
              disabled={approveState.loading}
              onClick={handleApproveAccessibility}
            >
              {approveState.loading ? "Saving..." : "Approve Accessibility"}
            </button>

            <StatusMessage
              loading={approveState.loading}
              status={approveState.status}
              error={approveState.error}
            />
          </details>
        </div>
      )}
    </div>
  );
}
