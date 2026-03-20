# Lorewell

Lorewell is a lightweight Instagram auto-posting MVP for scheduling posts from event metadata and uploaded media.

It currently supports:

- event creation
- media upload
- AI-generated captions, hashtags, and accessibility text
- manual approval before posting
- scheduled Instagram publishing
- retry logic for Instagram media readiness

## What Lorewell does

Lorewell turns:

- event data
- image/video
- schedule

into:

- approved Instagram post published automatically

### Current flow:
1. Create event
2. Upload asset
3. Create scheduled post
4. Generate caption package with OpenAI
5. Approve post
6. Scheduler publishes to Instagram through Meta Graph API

## Current MVP stack

- FastAPI
- SQLite
- SQLAlchemy
- APScheduler
- OpenAI API
- Meta Graph API / Instagram Platform
- Cloudflare Tunnel for temporary public media hosting


### Setup

#### Create environment and install dependencies

If using the helper script:

`source ./init.sh`

If setting up manually:

```
    python3 -m venv env
    source env/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    cp .env.example .env
```
#### Environment variables

Set these in `.env`:

```
    OPENAI_API_KEY=your_openai_key
    OPENAI_MODEL=gpt-5.4-mini
    
    PAGE_ACCESS_TOKEN=your_page_access_token
    INSTAGRAM_ACCOUNT_ID=your_instagram_business_or_creator_id
    GRAPH_API_VERSION=v25.0
    
    APP_BASE_URL=https://your-public-tunnel-url
    MEDIA_DIR=media
    DATABASE_URL=sqlite:///./lorewell.db
    
    DEFAULT_BRAND_VOICE=elegant, warm, story-driven, clear call to action
```
## Important notes about tokens
### OpenAI

You need an API key with active billing/quota.

### Meta

Lorewell currently uses a Page access token obtained from:

`Core FB -> me/accounts -> Target FB Page  page access token`

This token may expire, so manual refresh is currently part of the MVP workflow.

___The permissions as of 03/18/2026:___
- `email`
- `pages_show_list`
- `business_management`
- `instagram_basic`
- `instagram_manage_comments`
- `instagram_content_publish`
- `instagram_manage_messages`
- `pages_read_engagement`

#### Meta / Instagram account terminology

Lorewell uses the official Meta Graph API for publishing posts.  
Meta requires a specific relationship between a Facebook user, a Facebook Page, and an Instagram professional account.

In this README we use the following neutral terms:

| Term | Meaning |
|------|---------|
| Facebook user | The person who owns or manages the Page |
| Facebook Page | The Page connected to the Instagram account |
| Instagram account | A Business or Creator Instagram account |
| Page access token | Token used to call the Graph API |
| Instagram account ID | Numeric ID used for publishing |

###### Account Requirements

Lorewell requires:

1. A Facebook user logged into Meta
2. A Facebook Page owned or managed by that user
3. An Instagram Business or Creator account linked to that Page
4. A Page access token obtained from the Graph API
5. The Instagram account ID

The relationships must look like this:
```
    Facebook user
        ↓ manages
    Facebook Page
        ↓ linked to
    Instagram professional account
```

## Running the app

Start the API server:
```
    source ./init.sh
    lorewell-run
```

Or directly:

`python -m uvicorn app.main:app --reload`

Swagger docs: http://localhost:8000/docs

If using a tunnel: https://your-public-url/docs

## Public media hosting

For Instagram publishing, Meta must be able to fetch uploaded media through a public URL.

For local development, a temporary Cloudflare tunnel works well:

`cloudflared tunnel --url http://localhost:8000`

[Check the Readme for Cloudflared For installation](https://github.com/cloudflare/cloudflared)

Then set:
`APP_BASE_URL=https://your-generated-subdomain.trycloudflare.com`

## API flow
### Create event
`POST /events`

Example body:
```
{
  "title": "Lorewell Test Post",
  "event_type": "dj set",
  "location": "San Diego",
  "event_date": "2026-03-18T17:30:00",
  "notes": "Testing Lorewell autopost pipeline",
  "keywords": "dj, instagram, automation, test",
  "brand_voice": "professional, energetic, nightlife, DJ branding",
  "cta": "Follow @dreamtonethedj for more sets"
}
```
### Upload asset
`POST /events/{event_id}/upload`

### Create scheduled post
`POST /posts`

Example:
```
{
  "event_id": 1,
  "asset_id": 1,
  "publish_at": "2026-03-19T01:42:00"
}
```
Note: the MVP currently behaves most reliably when scheduling in UTC-style naive timestamps because the scheduler uses datetime.utcnow().

### Generate caption package
`POST /posts/generate`

Example:
```
{
  "post_id": 1
}
```
Returns structured output like:
```
{
  "caption_short": "Short Generated Caption",
  "caption_medium": "Medium Generated Caption",
  "caption_long": "Long Generated Caption",
  "hashtags": [
    "#a",
    "#list",
    "#of",
    "#hashtags",
  ],
  "accessibility_text": "Description of Image or Video",
  "seo_keywords": [
    "seo words",
    "whatever"
  ],
  "visual_summary": "AI Generate vision summary"
}
```
### Approve post
`POST /posts/{post_id}/approve`

Example:
```
{
  "caption_final": "Final caption for the post",
  "hashtags_final": "#the #set #of #hashtags",
  "accessibility_text": "Accessibility text for post"
}
```
### Check post status
`GET /posts`

Statuses currently include:

- draft
- approved
- publishing
- published
- failed

## Known MVP limitations
1. Timezone handling

The scheduler currently compares against:

`datetime.utcnow()`

This means local naive times can behave unexpectedly. A future improvement should make all scheduling timezone-aware.

2. Token refresh

Meta token refresh is currently manual.

3. Single-asset workflow

The MVP currently focuses on one asset per post.

4. No frontend dashboard yet

Swagger is the current admin interface.

5. Limited failure recovery

There is basic retry logic for Instagram media readiness, but no robust job retry system yet.

## What has been proven

Lorewell has already successfully demonstrated:

- event creation
- image upload
- OpenAI caption generation
- approval flow
- scheduled Instagram publishing
- public media accessibility
- Meta media container creation
- publish retry handling
- successful end-to-end Instagram posting

### Suggested next features

- proper timezone support
- long-lived token / refresh workflow
- lightweight dashboard UI
- carousel support
- reusable multi-account architecture
- better scheduling and retry management

## Security notes

___***Do not commit real values from .env.***___

Especially keep these out of git:
```
    OPENAI_API_KEY
    META_ACCESS_TOKEN
```

If a token has been pasted into chat or logs, rotate it.

## Technical debt / TODO

The current version (v0.2) passes all tests, but there are a few warnings that should be resolved in a future version.

### FastAPI startup event deprecation

FastAPI warns that `@app.on_event("startup")` is deprecated and should be replaced with lifespan handlers.

Current code still works, but should be migrated to:

- FastAPI lifespan context
- or `asynccontextmanager` startup pattern


---

### datetime.utcnow() deprecation

Warnings indicate that `datetime.utcnow()` is deprecated in favor of timezone-aware datetimes.

Current code uses naive UTC timestamps in:

- scheduler
- SQLAlchemy defaults
- tests

Future fix should:

- switch to `datetime.now(datetime.UTC)`
- make all stored timestamps UTC-aware
- update scheduler comparisons
- update tests accordingly

### SQLAlchemy default timestamp warnings

SQLAlchemy warns about callable defaults using `datetime.utcnow()`.

Future fix should update model defaults to timezone-aware functions.

