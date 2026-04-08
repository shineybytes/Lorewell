import { fetchJson } from "./client";
import type {
  ApprovedPostResponse,
  PostCreateResponse,
  PostGenerationResponse,
  PostRecord,
} from "../types/api";

export function listPosts() {
  return fetchJson<PostRecord[]>("/posts");
}

export function getPost(postId: number) {
  return fetchJson<PostRecord>(`/posts/${postId}`);
}

export function createPost(payload: {
  event_id: number;
  asset_id: number;
  brand_voice: string;
  cta_goal: string;
  generation_notes?: string;
}) {
  return fetchJson<PostCreateResponse>("/posts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function updatePost(
  postId: number,
  payload: {
    brand_voice: string;
    cta_goal: string;
    generation_notes?: string;
  },
) {
  return fetchJson<PostCreateResponse>(`/posts/${postId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function generatePost(postId: number, seedCaption?: string) {
  return fetchJson<PostGenerationResponse>(`/posts/${postId}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      seed_caption: seedCaption || null,
    }),
  });
}

export function approvePost(
  postId: number,
  payload: {
    caption_final: string;
    hashtags_final: string[];
    accessibility_text: string;
  },
) {
  return fetchJson<ApprovedPostResponse>(`/posts/${postId}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
export function deletePost(postId: number) {
  return fetchJson(`/posts/${postId}`, {
    method: "DELETE",
  });
}
