# 🧴 Skincare Industry Daily

An auto-updating news page for skincare/beauty industry leaders — CEOs, category
managers, founders — pulling fresh headlines every day from ~28 trade
publications (BeautyMatter, CosmeticsDesign, HAPPI, Global Cosmetic Industry,
Cosmetics Business, Beauty Independent, WWD Beauty, and more — full list in
`feeds.json`).

**Live site:** once deployed, this will be at
`https://<your-github-username>.github.io/<repo-name>/`

## How it works

- `feeds.json` — the list of sources. Each entry is either:
  - `"type": "native"` — a direct RSS feed URL, or
  - `"type": "google"` — a Google News search restricted to that site
    (used as a reliable fallback for publications without a clean public feed)
- `fetch_news.py` — fetches all sources, keeps articles from the last 10 days,
  and builds `index.html`
- `.github/workflows/update.yml` — a GitHub Actions workflow that runs the
  script automatically every day at **10:30 AM IST (05:00 UTC)** and commits
  the refreshed `index.html`

## Setup (5 minutes)

1. **Create a new GitHub repo** (public), e.g. `skincare-news`.
2. Upload all files in this folder to the repo (keep the folder structure,
   especially `.github/workflows/update.yml`).
3. Go to **Settings → Pages** in the repo:
   - Source: "Deploy from a branch"
   - Branch: `main`, folder: `/ (root)`
   - Save. GitHub will give you a URL like
     `https://yourname.github.io/skincare-news/`
4. Go to **Settings → Actions → General → Workflow permissions** and select
   **"Read and write permissions"** (needed so the workflow can commit the
   updated page back to the repo).
5. Go to the **Actions** tab → "Update Skincare News" → **Run workflow** to
   trigger the first build manually instead of waiting for 10:30 AM IST.
6. After it finishes (~1–2 min), refresh your Pages URL — you'll see today's
   headlines.

From then on it updates itself every day automatically. No server, no
hosting cost — it's just a GitHub repo + Actions + Pages, all free.

## Customizing

- **Add/remove sources**: edit `feeds.json`. For a new native RSS feed, find
  the `<link rel="alternate" type="application/rss+xml">` on the publication's
  site, or just check `<domain>/feed` or `<domain>/rss`. If it doesn't have
  one, add it with `"type": "google", "site": "domain.com"` — this works for
  almost any site.
- **Change how many articles per source**: edit `ARTICLES_PER_SOURCE` in
  `fetch_news.py`.
- **Change the update time**: edit the `cron` line in
  `.github/workflows/update.yml`. Cron is in UTC — IST is UTC+5:30, so
  10:30 AM IST = `0 5 * * *`.
- **Change the look**: all styling is inline in the `<style>` block inside
  `build_html()` in `fetch_news.py`.

## Notes

- Google News RSS results occasionally include syndicated re-posts from
  aggregators rather than the original publisher — this is a known tradeoff
  of using it as a fallback for sites without native feeds. Swap in a native
  feed URL whenever you find one for better precision.
- If a source returns 0 articles for a few days in a row, check the Actions
  log (Actions tab → latest run) — the printed `[!]` lines show the error for
  that source (paywall, feed moved, blocked bot access, etc).
