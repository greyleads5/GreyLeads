# GreyLeads US website (greyleads.us)

Generated from the India site by `python3 tools/build-us-site.py`. Don't edit these files by hand:
change the India page or the US copy/prices in the script, then re-run it and commit.

## Go live

1. Buy greyleads.us and add it to Cloudflare (Websites -> Add a domain).
2. Cloudflare -> Workers & Pages -> Create -> Import a repository -> greyleads5/greyleads.
   Project name `greyleads-us`, root directory `us-site`, deploy command `npx wrangler deploy`.
3. In `us-site/wrangler.jsonc` (via the script), uncomment the greyleads.us routes, re-run, push.
4. Redirect www.greyleads.us -> greyleads.us (Rules -> Redirect Rules).
5. FormSubmit: the first form sent from greyleads.us triggers an activation email to
   greyleads5@gmail.com. Click it once.
6. Google Search Console: add greyleads.us, submit sitemap.xml. Bing Webmaster: import.
7. On greyleads.in, add the matching hreflang en-US links back to greyleads.us so Google
   pairs the two sites (hreflang only works when both sides point at each other).
