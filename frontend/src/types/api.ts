export type EventRecord = {
  id: number;
  title: string;
  event_type: string | null;
  location: string | null;
  event_date: string | null;
  event_timezone?: string | null;
  recap?: string | null;
  keywords?: string | null;
  vendors?: string | null;
  event_guidance?: string | null;
};

export type AssetRecord = {
  id: number;
  event_id: number;
  file_path: string;
  media_type: string;
  analysis_status: string;
  vision_summary_generated: string | null;
  accessibility_text_generated: string | null;
  accessibility_text_final: string | null;
  analysis_error_message: string | null;
  analysis_user_correction: string | null;
};

export type EventCreatePayload = {
  title: string;
  event_type?: string | null;
  location?: string | null;
  event_date?: string | null;
  event_timezone?: string | null;
  recap?: string | null;
  keywords?: string | null;
  vendors?: string | null;
  event_guidance?: string | null;
};

export type UploadAssetResponse = {
  asset_id: number;
  media_type: string;
  analysis_status: string;
  vision_summary_generated: string | null;
  accessibility_text_generated: string | null;
};

export type PostRecord = {
  id: number;
  event_id: number | null;
  asset_id: number;
  brand_voice: string | null;
  cta_goal: string | null;
  generation_notes: string | null;
  generated_caption_options?: string | null;
  generated_hashtag_options?: string | null;
  generated_accessibility_options?: string | null;
  draft_caption_current?: string | null;
  draft_hashtags_current?: string | null;
  draft_accessibility_current?: string | null;
  approved_caption_final?: string | null;
  approved_hashtags_final?: string | null;
  approved_accessibility_text?: string | null;
  status: string;
  error_message?: string | null;
  created_at: string;
};

export type PostCreateResponse = {
  post_id: number;
  status: string;
};

export type PostGenerationResponse = {
  post_id: number;
  status: string;
  caption_option_1?: string | null;
  caption_option_2?: string | null;
  caption_option_3?: string | null;
  hashtags: string[];
  accessibility_text?: string | null;
  seo_keywords: string[];
  visual_summary?: string | null;
};

export type ApprovedPostResponse = {
  approved_post_id: number;
  status: string;
};
