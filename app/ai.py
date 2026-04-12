from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import OpenAI

from app.config import settings
from app.models import Asset, Event, Post
from app.video_analysis import extract_keyframes


client = OpenAI(api_key=settings.openai_api_key)

def _vendors_for_prompt(event: Event | None) -> str:
    if not event or not event.vendors:
        return "None"

    try:
        vendors = json.loads(event.vendors)
    except Exception:
        return event.vendors

    if not isinstance(vendors, list):
        return str(event.vendors)

    lines = []
    for vendor in vendors:
        role = (vendor.get("role") or "").strip()
        handle = (vendor.get("instagram") or "").strip()

        if role and handle:
            lines.append(f"{role}: {handle}")
        elif role:
            lines.append(role)
        elif handle:
            lines.append(handle)

    return "; ".join(lines) if lines else "None"

def _build_credits_block(event) -> str:
    if not event or not event.vendors:
        return ""

    try:
        vendors = json.loads(event.vendors)
    except Exception:
        return ""

    if not isinstance(vendors, list):
        return ""

    lines = []

    for v in vendors:
        role = (v.get("role") or "").strip()
        insta = (v.get("instagram") or "").strip()

        if not role and not insta:
            continue

        role_lower = role.lower()

        if role_lower in ["photography", "photo", "photos"]:
            prefix = "Photos by"
        elif role_lower == "venue":
            prefix = "Venue"
        elif role_lower == "dj":
            prefix = "DJ"
        elif role_lower == "florals":
            prefix = "Florals"
        else:
            prefix = role or "Contributor"

        if insta:
            lines.append(f"{prefix} {insta}")
        else:
            lines.append(prefix)

    return "\n".join(lines)

def _to_data_url(path: str) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    mime = "image/jpeg"
    if suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    elif suffix == ".gif":
        mime = "image/gif"

    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _json_response_from_content(content: list[dict]) -> dict:
    response = client.responses.create(
        model=settings.openai_model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}},
    )
    return json.loads(response.output_text)


def _build_generation_prompt(
    event,
    asset,
    post,
    seed_caption: str | None = None,
) -> str:
    event_bits = []
    if event:
        event_bits.append(f"Event Title: {event.title}")
        if event.event_type:
            event_bits.append(f"Event Type: {event.event_type}")
        if event.location:
            event_bits.append(f"Location: {event.location}")
        if event.recap:
            event_bits.append(f"Recap: {event.recap}")
        if event.event_guidance:
            event_bits.append(f"Guidance: {event.event_guidance}")
        if event.vendors:
            event_bits.append(f"Vendors: {_vendors_for_prompt(event)}")

    asset_bits = [
        f"Media Type: {asset.media_type}",
        f"Visual Summary: {asset.vision_summary_generated or 'None'}",
        f"Accessibility Text: {asset.accessibility_text_final or asset.accessibility_text_generated or 'None'}",
    ]

    post_bits = [
        f"Brand Voice: {post.brand_voice or 'None'}",
        f"CTA Goal: {post.cta_goal or 'None'}",
        f"Generation Notes: {post.generation_notes or 'None'}",
    ]

    variant_section = ""
    if seed_caption and seed_caption.strip():
        variant_section = f"""
Existing caption draft:
{seed_caption.strip()}

Use this as the basis for the new caption options.
Preserve the core intent and message, but provide three distinct variations.
"""

    return f"""
You are generating Instagram post content.

Context:
{chr(10).join(event_bits)}

Asset:
{chr(10).join(asset_bits)}

Post Settings:
{chr(10).join(post_bits)}

{variant_section}

Return JSON only with these keys:
caption_option_1, caption_option_2, caption_option_3, hashtags, accessibility_text, seo_keywords, visual_summary

Rules:
- Produce three distinct caption options for the same post
- All three captions should follow the same instructions and be viable final choices
- Keep captions specific, natural, and human
- Avoid cringe, spammy, or generic marketing language
- Integrate the CTA goal naturally rather than making it sound forced
- Use searchable keywords naturally
- hashtags must be an array of 8 to 15 relevant hashtags
- accessibility_text should clearly describe what is visible
- seo_keywords must be an array of short keyword phrases
- visual_summary should be concise and useful for internal reference

Priority:
- The main drivers of the caption should be, in order: recap, media analysis, brand voice, CTA goal, and generation notes
- Event type, location, and vendors are secondary context
- Vendors may help you understand the setting and avoid incorrect assumptions, but should not dominate the caption unless clearly relevant to the recap or visible media
- Do not invent collaborators, services, or event features that are not supported by the recap or media
- Do not generate a credits block or attribution lines
- Caption generation and hashtag generation are your focus
""".strip()


def generate_caption_package(
    event: Event | None,
    asset: Asset,
    post: Post,
    seed_caption: str | None = None,
) -> dict:
    content = [
        {
            "type": "input_text",
            "text": _build_generation_prompt(
                event=event,
                asset=asset,
                post=post,
                seed_caption=seed_caption,
            ),
        }
    ]

    if asset.media_type == "image":
        content.append(
            {
                "type": "input_image",
                "image_url": _to_data_url(asset.file_path),
            }
        )
    result = _json_response_from_content(content)
    credits_block = _build_credits_block(event)
    result["credits"] = credits_block
    return result

def _analyze_single_image(
    file_path: str,
    user_correction: str | None = None,
) -> dict:
    correction_text = user_correction or ""
    content = [
        {
            "type": "input_text",
            "text": f"""
Analyze this media asset and return JSON only with these keys:
visual_summary, accessibility_text

User correction or clarification:
{correction_text}

Rules:
- Treat the user correction as important context if provided
- visual_summary should be short and useful for internal reference
- accessibility_text should clearly describe what is visible
- keep both outputs specific and grounded in the media
""".strip(),
        },
        {
            "type": "input_image",
            "image_url": _to_data_url(file_path),
        },
    ]

    return _json_response_from_content(content)


def _analyze_video(
    file_path: str,
    user_correction: str | None = None,
) -> dict:
    frame_paths = extract_keyframes(file_path, frame_count=3)

    content: list[dict] = [
        {
            "type": "input_text",
            "text": f"""
Analyze these sampled frames from a short video and return JSON only with these keys:
visual_summary, accessibility_text

User correction or clarification:
{user_correction or ""}

Rules:
- Treat these images as representative frames from one continuous clip
- Infer the likely overall action, subject, setting, and vibe of the video
- Do not describe each frame separately unless necessary
- Treat the user correction as important context if provided
- visual_summary should be short and useful for internal reference
- accessibility_text should clearly describe what is visible in the overall clip
- keep both outputs specific and grounded in the sampled frames
""".strip(),
        }
    ]

    for frame_path in frame_paths:
        content.append(
            {
                "type": "input_image",
                "image_url": _to_data_url(frame_path),
            }
        )

    return _json_response_from_content(content)


def analyze_media(
    file_path: str,
    media_type: str,
    user_correction: str | None = None,
) -> dict:
    if media_type == "image":
        return _analyze_single_image(
            file_path,
            user_correction=user_correction,
        )

    if media_type == "video":
        try:
            return _analyze_video(
                file_path,
                user_correction=user_correction,
            )
        except Exception:
            cleaned_correction = (user_correction or "").strip()

            if cleaned_correction:
                return {
                    "visual_summary": cleaned_correction,
                    "accessibility_text": cleaned_correction,
                }

            return {
                "visual_summary": "Video uploaded. Automatic video analysis failed.",
                "accessibility_text": "Video uploaded. Add a manual description in Corrections to generate accessibility text.",
            }

    raise ValueError(f"Unsupported media_type: {media_type}")
