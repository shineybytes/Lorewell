import { useMemo, useState } from "react";
import type { AssetRecord } from "../types/api";
import { buildMediaUrl } from "../api/assets";

type AssetPreviewProps = {
  asset: AssetRecord;
  compact?: boolean;
};

function assetAltText(asset: AssetRecord) {
  return (
    asset.accessibility_text_final ||
    asset.accessibility_text_generated ||
    asset.display_name ||
    `Asset ${asset.id}`
  );
}

export default function AssetPreview({
  asset,
  compact = false,
}: AssetPreviewProps) {
  const [isOpen, setIsOpen] = useState(false);

  const mediaUrl = useMemo(
    () => buildMediaUrl(asset.file_path),
    [asset.file_path],
  );
  const altText = useMemo(() => assetAltText(asset), [asset]);

  return (
    <>
      <button
        type="button"
        className={`asset-preview-wrapper ${compact ? "compact" : ""}`}
        onClick={() => setIsOpen(true)}
        aria-label={`Open preview for ${altText}`}
      >
        {asset.media_type === "image" ? (
          <img
            className="asset-preview"
            src={mediaUrl}
            alt={altText}
            loading="lazy"
            decoding="async"
          />
        ) : (
          <video
            className="asset-preview"
            src={mediaUrl}
            muted
            playsInline
            preload="none"
            aria-label={altText}
          />
        )}
      </button>

      {isOpen && (
        <div className="asset-preview-modal" onClick={() => setIsOpen(false)}>
          <div
            className="asset-preview-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="asset-preview-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close preview"
            >
              ✕
            </button>

            {asset.media_type === "image" ? (
              <img src={mediaUrl} alt={altText} />
            ) : (
              <video
                src={mediaUrl}
                controls
                autoPlay
                playsInline
                preload="metadata"
              />
            )}
          </div>
        </div>
      )}
    </>
  );
}
