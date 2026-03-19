import base64
import json
from pathlib import Path
from openai import OpenAI
from app.config import settings
from app.models import Event, Asset

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


def generate_caption_package(event: Event, asset: Asset) -> dict:
    brand_voice = event.brand_voice or settings.default_brand_voice
    user_text = f"""
Generate a structured Instagram caption package for this event.

Event title: {event.title}
Event type: {event.event_type or ''}
Location: {event.location or ''}
Event date: {event.event_date.isoformat() if event.event_date else ''}
Notes: {event.notes or ''}
Keywords: {event.keywords or ''}
CTA: {event.cta or ''}
Brand voice: {brand_voice}

Return JSON only with keys:
caption_short, caption_medium, caption_long, hashtags, accessibility_text, seo_keywords, visual_summary

Rules:
- Keep captions specific and human
- Avoid cringe marketing language
- Use searchable keywords naturally
- hashtags must be an array of 8 to 15 relevant hashtags
- accessibility_text should clearly describe what is visible
- seo_keywords must be an array of short keyword phrases
""".strip()

    content = [{"type": "input_text", "text": user_text}]

    if asset.media_type == "image":
        content.append({
            "type": "input_image",
            "image_url": _to_data_url(asset.file_path),
        })

    response = client.responses.create(
        model=settings.openai_model,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}},
    )

    text = response.output_text
    return json.loads(text)
