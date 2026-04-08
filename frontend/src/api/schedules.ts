import { fetchJson } from "./client";

export type Schedule = {
  id: number;
  approved_post_id: number;
  publish_at: string;
  publish_timezone: string;
  status: string;
  error_message?: string | null;
  published_instagram_id?: string | null;
  failure_acknowledged: boolean;
  caption_final: string;
  hashtags_final: string[];
  accessibility_text?: string | null;
  asset_file_path: string | null;
  asset_media_type: string | null;
  selected_asset_id: number | null;
};

export function listSchedules() {
  return fetchJson<Schedule[]>("/schedules");
}

export function publishNow(approvedPostId: number) {
  return fetchJson(`/approved-posts/${approvedPostId}/publish-now`, {
    method: "POST",
  });
}

export function createSchedule(
  approvedPostId: number,
  payload: {
    publish_at: string;
    publish_timezone: string;
  },
) {
  return fetchJson(`/approved-posts/${approvedPostId}/schedule`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function retrySchedule(scheduleId: number) {
  return fetchJson(`/schedules/${scheduleId}/retry`, {
    method: "POST",
  });
}

export function archiveAllFailed() {
  return fetchJson("/schedules/archive-all-failed", {
    method: "POST",
  });
}

export function restoreAllFailed() {
  return fetchJson("/schedules/restore-all-failed", {
    method: "POST",
  });
}

export function deletePost(postId: number) {
  return fetchJson(`/posts/${postId}`, { method: "DELETE" });
}

export function deleteAsset(assetId: number) {
  return fetchJson(`/assets/${assetId}`, { method: "DELETE" });
}

export function deleteEvent(eventId: number) {
  return fetchJson(`/events/${eventId}`, { method: "DELETE" });
}

export function toggleScheduleAcknowledged(scheduleId: number) {
  return fetchJson<{ id: number; failure_acknowledged: boolean }>(
    `/schedules/${scheduleId}/acknowledge`,
    {
      method: "PATCH",
    },
  );
}
