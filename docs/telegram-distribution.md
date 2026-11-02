# Telegram Distribution (manual MVP)

Plan reference: [mybestpicks_plan_v4.md §1, §11](mybestpicks_plan_v4.md). The
optional automation is [modules/14-telegram-posting.md](modules/14-telegram-posting.md)
(P2, post-launch).

## Purpose
Use the **existing** Telegram channel to bring interested readers back to
trustworthy guides, learn what readers are asking, and build an audience that does
not depend on Google. It is **not** a feed of deal spam.

## Before the first post
- [ ] Review the channel's current topic, size, handle and audience overlap. Do not
      assume any of them.
- [ ] Decide how to introduce the MyBestPicks brand without flooding existing
      subscribers with unrelated posts.
- [ ] Enter the verified public URL in Wagtail Settings → Site settings
      (`telegram_channel_url`, optionally `telegram_channel_label`). The site shows
      no Telegram link until this is set.

## Post template
```text
<One practical takeaway from the article — a sentence a reader can act on.>

• <supporting point>
• <supporting point>        (optional)

<Optional question or poll prompt — e.g. "What's your current hub setup?">

Read the guide: <canonical article URL + UTMs>
```

Rules:
- Only make claims the article supports. Never imply hands-on testing that did not
  happen.
- Use text and a link by default. Attach images only when their usage rights are
  clear.
- No price claims, and no "deal" or urgency framing.

## UTM convention
Append the following to the **canonical** article URL, keeping any query parameters
it already has:

```
utm_source=telegram&utm_medium=social&utm_campaign=article_share[&utm_content=<short-slug>]
```

- `utm_content` is optional, short, lowercase and hyphenated, for example
  `usb-c-hub-tip` or `poll-keyboard`.
- Standalone tips that link to an older article use the same scheme.
- Never put UTMs in RSS, sitemaps or canonical tags.

## Cadence
Start with **2–3 useful posts a week**: alternate article announcements, standalone
tips and occasional polls. There is no quota; adjust to what the channel responds to.

## Measuring success
Look at clicks through to guides, how much Telegram-referred readers engage with
articles (Umami, `utm_source=telegram`), new questions and repeat participation.
Review these weekly alongside Search Console. Do not judge success by raw
subscriber count, and do not treat subscribers and referral visits as the same
thing.

## Privacy
Respect the channel's and groups' privacy settings. **Never import subscriber
details into the website.** Use comments and poll results only to choose topics.
