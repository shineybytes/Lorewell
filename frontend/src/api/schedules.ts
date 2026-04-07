import { fetchJson } from "./client";

export type Schedule = {
  id: number;
  approved_post_id: number;
  publish_at: string;
  publish_timezone: string;
  status: string;
};

export function listSchedules() {
  return fetchJson<Schedule[]>("/schedules");
}

export function createSchedule(
  approvedPostId: number,
  payload: {
    publish_at: string;
    publish_timezone: string;
  }
) {
  return fetchJson(`/approved-posts/${approvedPostId}/schedule`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
