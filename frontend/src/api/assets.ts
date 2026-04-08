import { fetchJson, API_BASE } from "./client";
import type { AssetRecord, UploadAssetResponse } from "../types/api";

export function listEventAssets(eventId: number) {
  return fetchJson<AssetRecord[]>(`/events/${eventId}/assets`);
}

export async function uploadAsset(
  eventId: number,
  file: File,
): Promise<UploadAssetResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/events/${eventId}/assets`, {
    method: "POST",
    body: formData,
  });

  const body = await response.json();

  if (!response.ok) {
    const detail =
      typeof body?.detail === "string" ? body.detail : "Upload failed";
    throw new Error(detail);
  }

  return body as UploadAssetResponse;
}

export function buildMediaUrl(filePath: string) {
  const filename = filePath.split("/").pop();
  return `${API_BASE}/media/${filename}`;
}

export function reanalyzeAsset(assetId: number, userCorrection: string) {
  return fetchJson<{
    asset_id: number;
    analysis_status: string;
    vision_summary_generated: string | null;
    accessibility_text_generated: string | null;
    analysis_error_message: string | null;
  }>(`/assets/${assetId}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_correction: userCorrection || null,
    }),
  });
}

export function approveAssetAccessibility(
  assetId: number,
  accessibilityTextFinal: string,
) {
  return fetchJson<{
    asset_id: number;
    analysis_status: string;
    accessibility_text_final: string;
  }>(`/assets/${assetId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      accessibility_text_final: accessibilityTextFinal,
    }),
  });
}

export function deleteAsset(assetId: number) {
  return fetchJson(`/assets/${assetId}`, {
    method: "DELETE",
  });
}
