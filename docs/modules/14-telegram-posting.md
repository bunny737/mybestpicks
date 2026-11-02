# Module: Telegram posting integration (optional)

> Keep this file in sync with the code AT ALL TIMES.
> If the code and this file disagree, this file is wrong. Fix it in the same commit.

**Status:** Not Started (post-launch only. Must not delay the website launch)
**Priority:** P2
**Ticket:** MBP-014
**Plan reference:** docs/mybestpicks_plan_v4.md §11 (Telegram channel)
**Depends on:** 03, 06 (SiteSettings Telegram fields), 09 (UTM convention)
**Blocks:** none

## Purpose
An optional Wagtail admin action, **Preview → Confirm → Publish to Telegram**, that
posts a reviewed article summary to the existing channel through the Telegram Bot
API. Manual posting stays the MVP. The manual workflow is in
[../telegram-distribution.md](../telegram-distribution.md).

## Prerequisites (owner)
- A bot added as an administrator of the channel with permission to post.
- `TELEGRAM_BOT_TOKEN` in env or the secret store only.
- The channel identifier (`@handle` or numeric id) in Wagtail settings. It is not
  secret.

## Data model (as planned; update to as-built)
```
Model: TelegramPost   app: home (or a small `distribution` app; ask first)
  article              FK → ArticlePage (PROTECT)
  text                 the exact text sent (after editor edits)
  link_url             canonical URL + UTMs
  status               draft | sending | sent | failed
  sent_at
  telegram_message_id  returned by the API, used for dedup
  error                last error, if any
  created_by           FK → user
  UNIQUE constraint preventing a second "sent" post for the same article + campaign
```

## Business rules
1. Publishing needs explicit human confirmation. **No automatic on-publish hook.**
2. Each article and campaign is sent at most once. A retry reuses the same record and
   is blocked if `telegram_message_id` is already set.
3. The token is read from env. It is never stored in the DB, Wagtail settings,
   logs or error messages.
4. The first version sends text plus a link. Images are sent only when their usage
   rights are clear (provenance from module 05).
5. API errors and 429 rate limits are handled gracefully: status `failed` with an
   error message, and a retry after `retry_after`. The admin request never hangs.
6. Only users with a dedicated permission can send.

## Changelog
- 2026-11-02  Created stub from plan v4.
