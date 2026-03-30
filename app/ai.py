from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import OpenAI

from app.config import settings
from app.models import Asset, Event, Post


client = OpenAI(api_key=settings.openai_api_key)


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


def _build_generation_prompt(
    event: Event | None,
    asset: Asset,
    post: Post,
) -> str:
    brand_voice = post.brand_voice or settings.default_brand_voice
    cta_goal = getattr(post, "cta_goal", None) or getattr(post, "cta_instruction", None) or ""
    generation_notes = post.generation_notes or ""

    event_title = event.title if event else ""
    event_type = event.event_type if event else ""
    location = event.location if event else ""
    event_date = event.event_date.isoformat() if event and event.event_date else ""
    recap = event.recap if event else ""
    keywords = event.keywords if event else ""
    vendors = event.vendors if event else ""

    asset_accessibility = asset.accessibility_text_final or asset.accessibility_text_generated or ""
    asset_visual_summary = asset.vision_summary_generated or ""

    event_guidance = event.event_guidance if event else ""

    return f"""
Generate a structured Instagram caption package for a single media asset.

Event context:
- Title: {event_title}
- Event type: {event_type}
- Location: {location}
- Event date: {event_date}
- Vendors: {vendors}
- Recap: {recap}
- Keywords: {keywords}
- Event Guidance: {event_guidance}

Post generation context:
- Brand voice: {brand_voice}
- CTA goal: {cta_goal}
- Additional generation notes: {generation_notes}

Asset context:
- Media type: {asset.media_type}
- Existing visual summary: {asset_visual_summary}
- Existing accessibility text: {asset_accessibility}

Return JSON only with these keys:
caption_short, caption_medium, caption_long, hashtags, accessibility_text, seo_keywords, visual_summary

Rules:
- Keep captions specific, natural, and human
- Avoid cringe, spammy, or generic marketing language
- Integrate the CTA goal naturally rather than making it sound forced
- Use searchable keywords naturally
- hashtags must be an array of 8 to 15 relevant hashtags
- accessibility_text should clearly describe what is visible
- seo_keywords must be an array of short keyword phrases
- visual_summary should be concise and useful for internal reference
""".strip()


def generate_caption_package(
    event: Event | None,
    asset: Asset,
    post: Post,
) -> dict:
    content = [
        {
            "type": "input_text",
            "text": _build_generation_prompt(event=event, asset=asset, post=post),
        }
    ]

    if asset.media_type == "image":
        content.append(
            {
                "type": "input_image",
                "image_url": _to_data_url(asset.file_path),
            }
        )

    response = client.responses.create(
        model=settings.openai_model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}},
    )

    return json.loads(response.output_text)


def analyze_media(file_path: str, media_type: str, user_correction: str | None = None) -> dict:
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
        }
    ]

    if media_type == "image":
        content.append(
            {
                "type": "input_image",
                "image_url": _to_data_url(file_path),
            }
        )
    else:
        return {
            "visual_summary": f"Auto-generated summary for {media_type}",
            "accessibility_text": f"Auto-generated accessibility text for {media_type}",
        }

    response = client.responses.create(
        model=settings.openai_model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}},
    )

    return json.loads(response.output_text)
