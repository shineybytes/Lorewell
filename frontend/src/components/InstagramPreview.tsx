import type { AssetRecord } from "../types/api";
import { appConfig } from "../config/app";
import AssetPreview from "./AssetPreview";

type InstagramPreviewProps = {
  asset: AssetRecord | null;
  caption: string;
  hashtags: string[] | string;
  accountName?: string;
  profileLabel?: string;
};

export default function InstagramPreview({
  asset,
  caption,
  hashtags,
  accountName = appConfig.instagramDisplayName,
  profileLabel = appConfig.instagramProfileLabel,
}: InstagramPreviewProps) {
  const hashtagList = Array.isArray(hashtags)
    ? hashtags
    : hashtags.split(/\s+/).filter(Boolean);

  return (
    <section
      className="instagram-preview card"
      aria-labelledby="instagram-preview-heading"
    >
      <h4 id="instagram-preview-heading">Instagram Preview</h4>

      <div className="instagram-preview-header">
        <div className="instagram-preview-avatar" aria-hidden="true">
          IG
        </div>
        <div>
          <p className="instagram-preview-account">{accountName}</p>
          <p className="instagram-preview-label">{profileLabel}</p>
        </div>
      </div>

      <div className="instagram-preview-media">
        {asset ? <AssetPreview asset={asset} /> : <p>No media selected.</p>}
      </div>

      <div className="instagram-preview-body">
        <p className="instagram-preview-caption">
          <strong>{accountName}</strong> {caption || "No caption yet."}
        </p>

        {hashtagList.length > 0 && (
          <p className="instagram-preview-hashtags">{hashtagList.join(" ")}</p>
        )}
      </div>
    </section>
  );
}
