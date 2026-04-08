import { useState } from "react";
import { Link } from "react-router-dom";
import type { AssetRecord } from "../types/api";
import AssetPreview from "./AssetPreview";
import StatusMessage from "./StatusMessage";
import { approveAssetAccessibility, reanalyzeAsset } from "../api/assets";
import { useAsyncState } from "../hooks/useAsyncState";
import { deleteAsset } from "../api/assets";

type AssetCardProps = {
  asset: AssetRecord;
  eventId: number;
  onRefresh: () => Promise<void>;
};

export default function AssetCard({
  asset,
  eventId,
  onRefresh,
}: AssetCardProps) {
  const [correction, setCorrection] = useState(
    asset.analysis_user_correction || "",
  );
  const [finalAccessibility, setFinalAccessibility] = useState(
    asset.accessibility_text_final || asset.accessibility_text_generated || "",
  );

  const reanalyzeState = useAsyncState();
  const approveState = useAsyncState();

  async function handleReanalyze() {
    try {
      reanalyzeState.start("Reanalyzing asset...");
      await reanalyzeAsset(asset.id, correction);
      await onRefresh();
      reanalyzeState.succeed("Asset reanalyzed.");
    } catch (err) {
      console.error(err);
      reanalyzeState.fail(
        err instanceof Error ? err.message : "Failed to reanalyze asset.",
      );
    }
  }

  async function handleApproveAccessibility() {
    try {
      approveState.start("Approving accessibility text...");
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

  return (
    <article className="card">
      <div className="approval-review-layout">
        <div className="approval-preview-column">
          <h4>Asset #{asset.id}</h4>
          <AssetPreview asset={asset} />

          <p>
            <strong>Type:</strong> {asset.media_type}
          </p>
          <p>
            <strong>Status:</strong> {asset.analysis_status}
          </p>
        </div>

        <div className="approval-details-column">
          <div>
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
          </div>

          <button
            type="button"
            disabled={reanalyzeState.loading}
            onClick={handleReanalyze}
          >
            {reanalyzeState.loading ? "Reanalyzing..." : "Reanalyze"}
          </button>

          <StatusMessage
            loading={reanalyzeState.loading}
            status={reanalyzeState.status}
            error={reanalyzeState.error}
          />

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
            {approveState.loading ? "Approving..." : "Approve Accessibility"}
          </button>

          <StatusMessage
            loading={approveState.loading}
            status={approveState.status}
            error={approveState.error}
          />

          <div className="approval-action-row">
            <Link
              className="button-link"
              to={`/drafts/editor?event_id=${eventId}&asset_id=${asset.id}`}
            >
              Create Post from Asset
            </Link>

            <button
              type="button"
              className="button-danger"
              onClick={async () => {
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
                  alert(
                    err instanceof Error
                      ? err.message
                      : "Failed to delete asset.",
                  );
                }
              }}
            >
              Delete Asset
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
