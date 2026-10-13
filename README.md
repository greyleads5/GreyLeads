# GreyLeads website

Static site for [greyleads.in](https://greyleads.in), hosted on Cloudflare Workers (static assets).

- Every push to `main` is deployed automatically by Cloudflare Workers Builds (`npx wrangler deploy`, configured in `wrangler.jsonc`).
- `.assetsignore` keeps repo-only files (README, notes, config) off the live site.
- `_headers` and `_redirects` are applied by Cloudflare to the static assets.
- `sitemap.xml`, `robots.txt` and the SEO tags in each page are maintained by the monthly SEO check.
- See `DEPLOY-NOTES.txt` for go-live and SEO steps.
