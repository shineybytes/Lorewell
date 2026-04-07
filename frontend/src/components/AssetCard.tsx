import { useState } from "react";
import { Link } from "react-router-dom";
import type { AssetRecord } from "../types/api";
import AssetPreview from "./AssetPreview";
import { approveAssetAccessibility, reanalyzeAsset } from "../api/assets";

type AssetCardProps = {
  asset: AssetRecord;
  eventId: number;
  onRefresh: () => Promise<void>;
};

export default function AssetCard({ asset, eventId, onRefresh }: AssetCardProps) {
  const [correction, setCorrection] = useState(asset.analysis_user_correction || "");
  const [finalAccessibility, setFinalAccessibility] = useState(
    asset.accessibility_text_final || asset.accessibility_text_generated || ""
  );
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function handleReanalyze() {
    try {
      setStatus("Reanalyzing asset...");
      setError("");
      await reanalyzeAsset(asset.id, correction);
      await onRefresh();
      setStatus("Asset reanalyzed.");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to reanalyze asset.");
      setStatus("");
    }
  }

  async function handleApproveAccessibility() {
    try {
      setStatus("Approving accessibility text...");
      setError("");
      await approveAssetAccessibility(asset.id, finalAccessibility);
      await onRefresh();
      setStatus("Accessibility approved.");
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Failed to approve accessibility text."
      );
      setStatus("");
    }
  }

  return (
    <article className="card">
      <h4>Asset #{asset.id}</h4>
      <AssetPreview asset={asset} />

      <p>
        <strong>Type:</strong> {asset.media_type}
      </p>
      <p>
        <strong>Status:</strong> {asset.analysis_status}
      </p>
      <p>
        <strong>Visual summary:</strong> {asset.vision_summary_generated || "None"}
      </p>
      <p>
        <strong>Generated accessibility:</strong>{" "}
        {asset.accessibility_text_generated || "None"}
      </p>
      <p>
        <strong>Final accessibility:</strong>{" "}
        {asset.accessibility_text_final || "None"}
      </p>

      <div className="form-row">
        <label htmlFor={`correction-${asset.id}`}>Correction</label>
        <textarea
          id={`correction-${asset.id}`}
          value={correction}
          onChange={(e) => setCorrection(e.target.value)}
        />
      </div>

      <button type="button" onClick={handleReanalyze}>
        Reanalyze
      </button>

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

      <button type="button" onClick={handleApproveAccessibility}>
        Approve Accessibility
      </button>

      <p role="status" aria-live="polite">
        {status}
      </p>
      <p role="alert">{error}</p>

      <Link
        className="button-link"
        to={`/drafts/editor?event_id=${eventId}&asset_id=${asset.id}`}
      >
        Create Post from Asset
      </Link>
    </article>
  );
}
