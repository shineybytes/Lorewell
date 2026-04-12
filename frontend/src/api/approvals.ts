import { fetchJson } from "./client";

export type ApprovedPost = {
  id: number;
  post_id: number;
  selected_asset_id: number;
  caption_final: string;
  hashtags_final: string[];
  accessibility_text: string;
  status: string;
  asset_file_path: string | null;
  asset_media_type: string | null;
};

export function listApprovedPosts() {
  return fetchJson<ApprovedPost[]>("/approved-posts");
}

export function forkApprovedPostToDraft(approvedPostId: number) {
  return fetchJson<{ post_id: number; status: string }>(
    `/approved-posts/${approvedPostId}/fork-draft`,
    {
      method: "POST",
    },
  );
}
