# Site analytics and SEO

CubeDynamics supports Google Analytics 4 for aggregate site usage and Google
Search Console for indexing diagnostics. The documentation build also provides
canonical URLs, per-page descriptions, social-sharing metadata, structured
software metadata, `robots.txt`, and an XML sitemap.

## Activate Google Analytics

Do not reuse the measurement IDs from `analytics-library` or `data-library`.
Those are separate GA4 data streams, and reusing either one would mix unrelated
traffic.

1. In Google Analytics, create a web data stream for
   `https://cu-esiil.github.io/cubedynamics/`.
2. Copy its measurement ID, which has the form `G-XXXXXXXXXX`.
3. In the GitHub repository, open **Settings → Secrets and variables →
   Actions → Variables**.
4. Create a repository variable named
   `CUBEDYNAMICS_GA_MEASUREMENT_ID` and set it to the new measurement ID.
5. Run the Pages workflow, or merge a change to `main`, and confirm a visit in
   the Analytics Realtime report.

The Pages workflow passes that repository variable into MkDocs. If the variable
is absent, the site emits no Google Analytics request. The configured tag also
disables Google Signals and advertising-personalization signals.

## Connect Google Search Console

The repository includes the same HTML verification file already used by other
CU-ESIIL GitHub Pages sites. After deployment:

1. Add the URL-prefix property
   `https://cu-esiil.github.io/cubedynamics/` in Search Console.
2. Select the HTML file verification method and confirm the deployed file is
   available at
   `https://cu-esiil.github.io/cubedynamics/google21782db4655ca373.html`.
3. Submit
   `https://cu-esiil.github.io/cubedynamics/sitemap.xml` in the Sitemaps panel.

## What to monitor

Use Analytics to follow engaged sessions, popular documentation pages,
vignette entry points, referral sources, and search terms used within the site.
Use Search Console to follow indexed pages, search queries, click-through rate,
mobile usability, and crawl errors.

Treat traffic as evidence about navigation and discoverability, not as a direct
measure of scientific impact. Avoid collecting user-level identifiers or adding
advertising features without a separate privacy review.

## Relevant Google documentation

- [Set up Analytics for a website](https://support.google.com/analytics/answer/9304153)
- [Build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Consolidate duplicate URLs with canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Verify ownership in Search Console](https://support.google.com/webmasters/answer/9008080)
