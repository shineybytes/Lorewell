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
3. Create draft from asset
4. Generate caption options (optionally seeded)
5. Edit and finalize caption, hashtags, and accessibility text
6. Send to approvals (creates approved snapshot)
7. Schedule post from approved content
8. Scheduler publishes to Instagram through Meta Graph API

## Failure Handling and Recovery

If a scheduled post fails:

- The schedule is marked as `failed`
- An error message is stored and visible in the UI

Users can:

- Retry publishing
  → creates a new schedule attempt

- Archive failure
  → marks the failure as acknowledged

- Restore failure
  → returns it to the active queue

Failures are never silently discarded.

## Scheduling Model

Schedules are created from approved posts:

POST /approved-posts/{id}/schedule

Schedules cannot be created directly.

This ensures:
- only finalized content is scheduled
- no incomplete drafts are published
- schedules always reference a stable snapshot

## Deletion Rules

| Object | Behavior |
|--------|--------|
| Draft  | Can always be deleted |
| Asset  | Cannot be deleted if used by a post |
| Event  | Cannot be deleted if it contains assets |

Deletion is intentionally constrained to prevent data inconsistency.

## Caption Generation

Draft generation supports optional seeding:

- User-provided caption can be used as a base
- AI generates variations based on:
  - brand voice
  - CTA goal
  - generation notes

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

#### Important Additional Notes about Environment

Lorewell uses environment variables for API credentials and runtime settings.

##### Required environment files:

`.env`
- Used for local development
- Contains real tokens and secrets
- Never commit this file

`.env.test`
- Used for automated tests and GitHub Actions
- Contains dummy values
- Safe to commit

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

## Wiki

Check out the Wiki for more details about installation, design.
