import type { AssetRecord } from "../types/api";
import { buildMediaUrl } from "../api/assets";

type AssetPreviewProps = {
  asset: AssetRecord;
};

export default function AssetPreview({ asset }: AssetPreviewProps) {
  const mediaUrl = buildMediaUrl(asset.file_path);

  if (asset.media_type === "image") {
    return (
      <img
        className="asset-preview"
        src={mediaUrl}
        alt={
          asset.accessibility_text_final ||
          asset.accessibility_text_generated ||
          `Asset ${asset.id}`
        }
      />
    );
  }

  if (asset.media_type === "video") {
    return <video className="asset-preview" src={mediaUrl} controls />;
  }

  return <div>No preview available.</div>;
}
