import { useState } from "react";
import type { AssetRecord } from "../types/api";
import { buildMediaUrl } from "../api/assets";

type AssetPreviewProps = {
  asset: AssetRecord;
  compact?: boolean;
};

export default function AssetPreview({
  asset,
  compact = false,
}: AssetPreviewProps) {
  const [isOpen, setIsOpen] = useState(false);
  const mediaUrl = buildMediaUrl(asset.file_path);

  return (
    <>
      <button
        type="button"
        className={`asset-preview-wrapper ${compact ? "compact" : ""}`}
        onClick={() => setIsOpen(true)}
      >
        {asset.media_type === "image" ? (
          <img
            className="asset-preview"
            src={mediaUrl}
            alt={
              asset.accessibility_text_final ||
              asset.accessibility_text_generated ||
              `Asset ${asset.id}`
            }
          />
        ) : (
          <video
            className="asset-preview"
            src={mediaUrl}
            muted
            playsInline
            preload="metadata"
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
            >
              ✕
            </button>

            {asset.media_type === "image" ? (
              <img
                src={mediaUrl}
                alt={
                  asset.accessibility_text_final ||
                  asset.accessibility_text_generated ||
                  `Asset ${asset.id}`
                }
              />
            ) : (
              <video src={mediaUrl} controls autoPlay playsInline />
            )}
          </div>
        </div>
      )}
    </>
  );
}
