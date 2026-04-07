import { fetchJson } from "./client";

export type ApprovedPost = {
  id: number;
  post_id: number;
  selected_asset_id: number;
  caption_final: string;
  hashtags_final: string[];
  accessibility_text: string;
  status: string;
};

export function listApprovedPosts() {
  return fetchJson<ApprovedPost[]>("/approved-posts");
}
