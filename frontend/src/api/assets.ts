import { fetchJson, API_BASE } from "./client";
import type {
  AssetAnalysisProposalResponse,
  AssetApplyAnalysisPayload,
  AssetRecord,
  UploadAssetResponse,
} from "../types/api";

export function listAssets() {
  return fetchJson<AssetRecord[]>("/assets");
}

export function listEventAssets(eventId: number) {
  return fetchJson<AssetRecord[]>(`/events/${eventId}/assets`);
}

export function getAsset(assetId: number) {
  return fetchJson<AssetRecord>(`/assets/${assetId}`);
}

export function uploadAsset(
  eventId: number,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadAssetResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/events/${eventId}/assets`);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      onProgress(percent);
    };

    xhr.onload = () => {
      let body: unknown = null;

      try {
        body = xhr.responseText ? JSON.parse(xhr.responseText) : null;
      } catch {
        body = null;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as UploadAssetResponse);
        return;
      }

      const detail =
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof (body as { detail?: unknown }).detail === "string"
          ? (body as { detail: string }).detail
          : "Upload failed";

      reject(new Error(detail));
    };

    xhr.onerror = () => {
      reject(new Error("Upload failed."));
    };

    xhr.send(formData);
  });
}

export function updateAssetEvent(assetId: number, eventId: number | null) {
  return fetchJson<AssetRecord>(`/assets/${assetId}/event`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      event_id: eventId,
    }),
  });
}

export function proposeAssetAnalysis(assetId: number, userCorrection = "") {
  return fetchJson<AssetAnalysisProposalResponse>(
    `/assets/${assetId}/propose-analysis`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_correction: userCorrection || null,
      }),
    },
  );
}

export function applyAssetAnalysis(
  assetId: number,
  payload: AssetApplyAnalysisPayload,
) {
  return fetchJson<AssetRecord>(`/assets/${assetId}/apply-analysis`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
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
export function uploadAssetNoEvent(file: File): Promise<UploadAssetResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/assets/upload`);

    xhr.onload = () => {
      let body: unknown = null;

      try {
        body = xhr.responseText ? JSON.parse(xhr.responseText) : null;
      } catch {
        body = null;
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as UploadAssetResponse);
        return;
      }

      const detail =
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof (body as { detail?: unknown }).detail === "string"
          ? (body as { detail: string }).detail
          : "Upload failed";

      reject(new Error(detail));
    };

    xhr.onerror = () => {
      reject(new Error("Upload failed."));
    };

    xhr.send(formData);
  });
}

export function renameAsset(assetId: number, displayName: string | null) {
  return fetchJson<{ id: number; display_name: string | null }>(
    `/assets/${assetId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        display_name: displayName,
      }),
    },
  );
}
