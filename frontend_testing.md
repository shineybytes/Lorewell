# Lorewell Frontend Publishability Checklist

This checklist ensures the frontend is functionally correct, understandable, and safe to release without automated frontend testing.

Use this before each release candidate.

## 0. Pre-flight
Confirm:

- [ ] Backend is running
- [ ] Frontend is running
- [ ] Database is in a known state (fresh or acceptable)
- [ ] (If testing real publish) cloudflared is running
- [ ] (If testing real publish) APP_BASE_URL is public
- [ ] (If testing real publish) Meta token is valid

## 1. Navigation and Page Load
- [ ] App loads without blank screen
- [ ] No red errors in browser console on load
- [ ] Navigation works:
  - [ ] Events
  - [ ] New Event
  - [ ] Drafts
  - [ ] Approvals
  - [ ] Schedules
- [ ] Refresh works on each page
- [ ] No “invalid id” errors in normal flows

## 2. Event Creation
- [ ] Title is required
- [ ] Event can be created with:
  - [ ] no date/time + no timezone
  - [ ] date/time + timezone
- [ ] Event cannot be created with:
  - [ ] date/time but missing timezone
  - [ ] timezone but missing date/time
- [ ] Invalid timezone is rejected
- [ ] Event loads correctly after creation
- [ ] Recap displays correctly
- [ ] Guidance displays correctly

## 3. Asset Upload and Review
- [ ] Upload JPEG succeeds
- [ ] Upload MP4 succeeds
- [ ] Unsupported file type is rejected
- [ ] Upload does NOT navigate away
- [ ] Uploaded asset appears without refresh
- [ ] Image preview renders
- [ ] Video preview renders
- [ ] Asset status is shown
- [ ] Vision summary is shown
- [ ] Accessibility text is shown

## 4. Asset Library

- [ ] Upload asset without event
- [ ] Asset appears in Asset Library
- [ ] Asset preview renders (image/video)
- [ ] Asset can be renamed
- [ ] Asset can be reassigned to event
- [ ] Asset can be unassigned from event
- [ ] Reassignment prompts for reanalysis
- [ ] Proposed analysis can be generated
- [ ] Proposed vs current analysis can be compared
- [ ] User can:
  - [ ] Keep current
  - [ ] Use proposed
  - [ ] Apply edited merge
- [ ] Asset delete works for unused assets
- [ ] Asset delete is blocked if in use
- [ ] Sorting works:
  - [ ] Newest
  - [ ] Oldest
  - [ ] Name A–Z
  - [ ] Name Z–A

## 5. Asset Correction Workflow
- [ ] Correction textarea is editable
- [ ] Clicking Reanalyze shows visible feedback
- [ ] Updated result appears after reanalyze
- [ ] Accessibility text is editable
- [ ] Approval updates visible state
- [ ] No page refresh required to see updates
- [ ] No console errors during actions

## 6. Draft Creation Flow
- [ ] `Create Post from Asset` navigates correctly
- [ ] Event context displays correctly
- [ ] Asset preview displays correctly
- [ ] Brand Voice is editable
- [ ] CTA Goal is editable
- [ ] Generation Notes is editable
- [ ] Generate Draft works
- [ ] Three (3) different caption options appear
- [ ] `Use This Caption` works
- [ ] Final Caption is editable
- [ ] Final Hashtags are editable
- [ ] Final Accessibility Text is editable

## 7. Draft Persistence
- [ ] Generate draft
- [ ] Leave page
- [ ] Draft appears in Drafts
- [ ] Reopen draft
- [ ] Brand Voice persists
- [ ] CTA Goal persists
- [ ] Generation Notes persist
- [ ] Regenerate reflects updated inputs
- [ ] No unexpected data loss

## 8. Approval Flow
- [ ] `Send to Approvals` works
- [ ] Action gives visible feedback
- [ ] Draft disappears from Drafts
- [ ] Appears in Approvals
- [ ] Caption matches
- [ ] Hashtags match
- [ ] Accessibility text matches

## 9. Scheduling Flow
- [ ] Approved post appears in Approvals
- [ ] Date/time input works
- [ ] Timezone dropdown loads
- [ ] Default timezone is sensible
- [ ] Scheduling fails if:
  - [ ] missing date
  - [ ] missing timezone
- [ ] Scheduling succeeds with valid input
- [ ] Scheduled item appears in Schedules
- [ ] Schedule displays:
  - [ ] Approved Post ID
  - [ ] Publish time
  - [ ] Timezone
  - [ ] Status
- [ ] Unschedule button appears for scheduled items
- [ ] Unschedule removes item from schedule list
- [ ] Cannot unschedule published item

## 10. Scheduling UX Enhancements
- [ ] Retry button visible on failed items
- [ ] Archive/Restore buttons visible
- [ ] Sorting works (Newest/Oldest)
- [ ] Tabs filter correctly:
  - [ ] Future
  - [ ] Past
  - [ ] Recent
  - [ ] Needs Attention
  - [ ] Archived

## 11. Real Publishing Flow (Optional but Recommended)
- [ ] cloudflared (or similar) tunnel is active
- [ ] `APP_BASE_URL` is public
- [ ] Schedule post ~1–2 minutes ahead
- [ ] Backend logs show scheduler activity
- [ ] Status transitions:
  - [ ] scheduled → publishing → published
  - [ ] OR scheduled → failed
- [ ] Instagram post appears if successful
- [ ] Failure is visible if not successful

## 12. Failure Handling
- [ ] Failed schedules show visible status
- [ ] Error message is visible or retrievable
- [ ] App does NOT fail silently
- [ ] UI remains usable after failure
- [ ] Retry publishing works
- [ ] Archive moves item out of active queue
- [ ] Restore returns item to active queue

## 13. State Feedback and Loading
- [ ] Actions show loading state
- [ ] UI does not feel unresponsive
- [ ] Status updates are visible after navigation
- [ ] No stale UI after successful actions

## 14. Accessibility Sanity Pass
- [ ] All inputs have labels
- [ ] Tab navigation works
- [ ] Focus indicators are visible
- [ ] Status messages are readable
- [ ] Errors are visible
- [ ] Headings are structured logically
- [ ] No color-only communication
- [ ] Images have alt text when applicable

## 15. Responsive Sanity Pass
- [ ] Test at smaller width:
  - [ ] Navigation is usable
  - [ ] Forms do not overflow
  - [ ] Buttons remain visible
  - [ ] Cards stack properly
  - [ ] Textareas are usable

## 16. Console Check
- [ ] No red errors on load
- [ ] No red errors on navigation
- [ ] No red errors on:
  - [ ] Upload
  - [ ] Generate
  - [ ] Approve
  - [ ] Schedule

# Minimum Release Path (Required)
This is the required end-to-end flow before release:

- [ ] Create Event
- [ ] Upload Asset (with or without event)
- [ ] Reanalyze or approve accessibility
- [ ] Create Draft
- [ ] Generate Draft
- [ ] Select Caption
- [ ] Send to Approvals
- [ ] Schedule Post
- [ ] Confirm it appears in Schedules

If any step fails, release is blocked.

## Alternate Valid Flow (Asset-first)
We're moving towards Asset as first-class objects, so here is the alternate workflow.

- [ ] Upload Asset (no event)
- [ ] Create Draft from Asset
- [ ] Create Event
- [ ] Attach Asset to Event
- [ ] Confirm reanalysis prompt appears
- [ ] Continue standard flow

## Release Blockers

Do NOT release if:

- Blank page appears
- Navigation breaks
- Upload redirects unexpectedly
- Draft cannot be reopened
- Approval loses content
- Scheduling fails
- Status is incorrect or misleading
- Publish fails silently
- Console shows errors in main flow
- Non-Blocking Issues

These are acceptable for release:

- Minor spacing issues
- Copy clarity improvements
- Preview not yet implemented
- Requires manual refresh for updates
- Minor responsive quirks

## Recommended Testing Workflow
- [ ] Quick Pass
- [ ] Run Minimum Release Path
- [ ] Full Pass
- [ ] Run full checklist once
- [ ] Integration Pass
- [ ] Test at least one real publish

#Purpose
This checklist ensures Lorewell is, functional, understandable, and reliable.
Following this should allow security between developers or release apps without requiring a frontend testing framework.
