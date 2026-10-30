#!/usr/bin/env python3
"""
Build the US version of the GreyLeads website (greyleads.us) from the India site.

    python3 tools/build-us-site.py

Reads the India pages in the repo root and writes a standalone static site to
us-site/ (its own wrangler.jsonc, sitemap, robots, assets). The India site is
the single source of design and layout: edit a page there, re-run this script,
and the US copy follows. US-only wording, prices and SEO live in this file.

The script prints a WARNING for any replacement that no longer matches (because
the India copy changed), and lists any India-specific words left on US pages.
"""
import html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "us-site")
US = "https://greyleads.us"
IN = "https://greyleads.in"

# ---------------------------------------------------------------------------
# Prices (USD). Change them here and re-run.
# ---------------------------------------------------------------------------
P = {
    "retainer":     "$1,500",   # marketing retainers, per month
    "lead_mgmt":    "$1,500",   # lead generation management, per month
    "lead_spend":   "$3,000",   # recommended starting ad spend for lead gen, per month
    "web_from":     "$3,000",   # website projects from
    "web_to":       "$15,000",  # typical upper end
    "care":         "$150",     # website care plan, per month
    "app_from":     "$15,000",  # first app version from
    "app_to":       "$60,000",
    "creative":     "$1,200",   # creative retainer, per month
    "ppc_mgmt":     "$1,500",   # paid media management, per month
    "ppc_spend":    "$2,000",   # minimum ad spend, per month
    "seo":          "$1,200",   # SEO & AEO, per month
    "brand":        "$2,500",   # brand identity project from
    "automation":   "$2,000",   # CRM & automation setup from
}

# Pages to publish on the US site: (India source file, URL path)
PAGES = [
    ("index.html", "/"),
    ("lead-generation.html", "/lead-generation"),
    ("websites.html", "/websites"),
    ("apps.html", "/apps"),
    ("creative-ads.html", "/creative-ads"),
    ("performance-marketing.html", "/performance-marketing"),
    ("seo-aeo.html", "/seo-aeo"),
    ("branding.html", "/branding"),
    ("automation.html", "/automation"),
    ("about.html", "/about"),
    ("work.html", "/work"),
    ("process.html", "/process"),
    ("contact.html", "/contact"),
    ("team.html", "/team"),
    ("privacy.html", "/privacy"),
    ("404.html", None),
    ("work/greyweave.html", "/work/greyweave"),
    ("work/iacharya.html", "/work/iacharya"),
    ("work/jonas-cafe.html", "/work/jonas-cafe"),
    ("work/pixcity.html", "/work/pixcity"),
    ("work/quadrate.html", "/work/quadrate"),
    ("work/solize.html", "/work/solize"),
]
# Pages that stay on greyleads.in only; US links point there.
EXTERNAL = ["/blog", "/careers"]

PRICE_LINE = (
    '<p class="gl-up" style="font-family: \'Geist Mono\', monospace; font-size: 13px; '
    'letter-spacing: 0.04em; color: #4A4360; margin: 20px 0 0; animation-delay: .2s">'
    'Starting from <strong style="color: #6D2EC7; font-weight: 700">{price}</strong>'
    ' · Senior team in India · Calls on US time</p>'
)

# ---------------------------------------------------------------------------
# Per-page SEO and hero copy
# ---------------------------------------------------------------------------
META = {
    "/": dict(
        title="Digital Marketing & Lead Generation Agency for US Businesses | GreyLeads",
        desc="Senior digital agency for US businesses: B2B lead generation, websites and apps, Google, Meta & LinkedIn ads, SEO and AEO. Calls on US time, month-to-month.",
        kw="digital marketing agency for us businesses, b2b lead generation agency, offshore digital marketing agency, outsourced marketing team india, website development company, seo and aeo agency, ppc agency",
        alt="GreyLeads – digital marketing and lead generation for US businesses",
    ),
    "/lead-generation": dict(
        title="B2B Lead Generation Services for US Companies | GreyLeads",
        desc="Lead generation for US companies: verified B2B data, LinkedIn, Google and Meta campaigns, landing pages and instant follow-up that fill your pipeline with qualified leads.",
        kw="b2b lead generation services, lead generation agency usa, outsourced lead generation, verified b2b data, linkedin lead generation, appointment setting, qualified leads",
        hero=("We build lead engines for brands in Bangalore, Chennai and across India: the right offer, the right audience, a landing page that converts, and a follow-up system that turns interest into revenue.",
              "We build lead engines for US companies: verified data on the right buyers, the right offer, a landing page that converts, and a follow-up system that turns interest into booked calls and revenue."),
        price=P["lead_mgmt"] + "/month", service="B2B lead generation for US companies",
    ),
    "/websites": dict(
        title="Website Design & Development for US Businesses | GreyLeads",
        desc="Fast, conversion-focused websites and e-commerce for US businesses, designed and built by a senior team. Fixed-price projects from " + P["web_from"] + ".",
        kw="website design and development company, web design agency for small business, offshore web development, webflow wordpress shopify development, conversion focused website",
        hero=("Your website is either your best salesperson or your most expensive brochure. From our Bangalore studio, we design and build fast, beautiful websites engineered to turn visitors into enquiries and customers.",
              "Your website is either your best salesperson or your most expensive brochure. Our senior studio designs and builds fast, beautiful websites for US businesses, engineered to turn visitors into inquiries and customers."),
        price=P["web_from"], service="Website design and development for US businesses",
    ),
    "/apps": dict(
        title="Mobile App Development Company for US Startups & Businesses | GreyLeads",
        desc="iOS, Android and web app development for US startups and businesses. Senior product team, fixed quotes after discovery, first versions from " + P["app_from"] + ".",
        kw="mobile app development company, app development for startups, offshore app development india, ios and android app development, react native flutter development, mvp development",
        hero=("From first idea to the app store and beyond, our Bangalore team designs, builds and launches iOS, Android and web apps that are a joy to use and built to grow your business.",
              "From first idea to the App Store and beyond, our senior product team designs, builds and launches iOS, Android and web apps for US startups and businesses: a joy to use and built to grow."),
        price=P["app_from"], service="Mobile and web app development for US startups and businesses",
    ),
    "/creative-ads": dict(
        title="Creative Ad Agency – Video, UGC & Social Ads for US Brands | GreyLeads",
        desc="Scroll-stopping ad creative for US brands: video, UGC-style, static and carousel ads for Meta, TikTok, YouTube and LinkedIn, tested every week.",
        kw="creative ad agency, ad creative production, ugc ads agency, video ads for facebook and instagram, performance creative agency, social media ad design",
        hero=("Great targeting can't save a boring ad. Our in-house Bangalore studio designs posts, videos and campaigns that stop the thumb, tell your story in seconds and make people act.",
              "Great targeting can't save a boring ad. Our in-house studio designs posts, videos and campaigns for US brands that stop the thumb, tell your story in seconds and make people act."),
        price=P["creative"] + "/month", service="Creative ads and video production for US brands",
    ),
    "/performance-marketing": dict(
        title="Performance Marketing Agency – Google, Meta & LinkedIn Ads | GreyLeads",
        desc="Google, Meta, YouTube and LinkedIn ads managed for US businesses by senior specialists, measured on leads, sales and ROAS. Management from " + P["ppc_mgmt"] + "/month.",
        kw="performance marketing agency, ppc management services, google ads agency, facebook ads agency, linkedin ads agency, paid media agency usa",
        hero=("We plan, run and optimise Meta, Google, YouTube and LinkedIn campaigns for brands in Bangalore, Chennai and across India, measured on sales, leads and return on ad spend.",
              "We plan, run and optimize Meta, Google, YouTube and LinkedIn campaigns for US businesses, measured on sales, leads and return on ad spend."),
        price=P["ppc_mgmt"] + "/month", service="Performance marketing for US businesses",
    ),
    "/seo-aeo": dict(
        title="SEO & AEO Agency – Rank on Google and in AI Answers | GreyLeads",
        desc="SEO and AEO for US businesses: rank on Google and get recommended by ChatGPT, Gemini and Google AI Overviews. Technical SEO, content and local search.",
        kw="seo agency, aeo agency, answer engine optimization, generative engine optimization, get recommended by chatgpt, seo services for small business usa, local seo",
        hero=("Buyers search on Google and ask ChatGPT, Gemini and Google's AI answers what to buy. We make sure your brand shows up in both, from local search in Bangalore and Chennai to all of India.",
              "Buyers search on Google and ask ChatGPT, Gemini and Google's AI answers what to buy. We make sure your brand shows up in both, from local search in your city to national rankings across the US."),
        price=P["seo"] + "/month", service="Search engine optimization (SEO) and answer engine optimization (AEO) for US businesses",
    ),
    "/branding": dict(
        title="Branding & Social Media Agency for US Brands | GreyLeads",
        desc="Brand identity, guidelines and social media management for US businesses: a clear voice and a distinctive look that people recognize, trust and choose.",
        kw="branding agency, brand identity design, logo and brand guidelines, social media management agency, social media content creation, rebranding agency",
        hero=("From Bangalore, we build brand identities with a clear voice and a distinctive look, then bring them to life on social media, so people recognise you, trust you and choose you.",
              "We build brand identities with a clear voice and a distinctive look, then bring them to life on social media, so people recognize you, trust you and choose you."),
        price=P["brand"], service="Branding and social media marketing for US brands",
    ),
    "/automation": dict(
        title="Marketing Automation & CRM Services – HubSpot, Salesforce, Zoho | GreyLeads",
        desc="CRM setup and marketing automation for US teams: HubSpot, Salesforce and Zoho, email and SMS sequences, lead routing and instant follow-up so no lead goes cold.",
        kw="marketing automation agency, hubspot implementation, crm setup services, salesforce consultant, email automation, lead routing, sales automation",
        hero=("For teams in Bangalore, Chennai and across India, we connect your website, ads and forms to a CRM, then automate WhatsApp, email and sales follow-ups, so no enquiry goes cold.",
              "For US sales teams, we connect your website, ads and forms to a CRM, then automate email, SMS, WhatsApp and sales follow-ups, so no lead goes cold."),
        price=P["automation"], service="Marketing automation and CRM for US teams",
    ),
    "/about": dict(
        title="About GreyLeads – A Senior Digital Team in India, Working for US Businesses",
        desc="GreyLeads is a senior digital marketing studio in Bengaluru, India, working with US businesses: one team for websites, apps, ads, SEO and lead generation.",
        kw="about greyleads, offshore digital marketing agency, digital agency india for us clients, outsourced marketing team",
    ),
    "/work": dict(
        title="Our Work & Case Studies | GreyLeads",
        desc="Case studies from GreyLeads: SEO, lead generation, verified B2B data, LinkedIn ads and apps for brands in India, Europe and beyond.",
        kw="digital marketing case studies, lead generation case study, seo case study, b2b data case study",
    ),
    "/process": dict(
        title="How We Work With US Clients – From First Call to First Lead | GreyLeads",
        desc="How GreyLeads works with US businesses: discovery, design and build, launch with full tracking, then weekly optimization, with calls on your time zone.",
        kw="how greyleads works, agency onboarding process, working with an offshore agency",
    ),
    "/contact": dict(
        title="Contact GreyLeads – Book a Free Growth Call",
        desc="Tell us what you're working on. A senior strategist replies within one business day and schedules a call in your US time zone.",
        kw="contact greyleads, hire digital marketing agency, free growth audit, lead generation consultation",
    ),
    "/team": dict(
        title="Our Team | GreyLeads",
        desc="Meet the senior strategists, designers, developers and media buyers at GreyLeads who work as one team on every US account.",
        kw="greyleads team, digital marketing team, offshore marketing team",
    ),
    "/privacy": dict(
        title="Privacy Policy | GreyLeads",
        desc="How GreyLeads collects, uses and protects personal data on greyleads.us.",
        kw="greyleads privacy policy",
    ),
}

# ---------------------------------------------------------------------------
# Copy replacements. Applied to every page (outside <style>), including JSON-LD.
# Order matters: longer, more specific strings first.
# ---------------------------------------------------------------------------
FOOTER_OLD = "A digital marketing agency in Bengaluru (Bangalore), also serving Chennai, Mumbai, Delhi NCR, Hyderabad and Pune. We build websites and apps, run ads and SEO, and turn attention into qualified leads."
FOOTER_NEW = "A senior digital marketing team in Bengaluru, India, working with businesses across the United States. We build websites and apps, run ads and SEO, and turn attention into qualified leads."

COMMON = [
    (FOOTER_OLD, FOOTER_NEW),
    ("Bengaluru, Karnataka 560103<", "Bengaluru, Karnataka 560103, India<"),
    ("GreyLeads is a full-service digital marketing agency in Bangalore, working with brands across metro India and around the world.",
     "GreyLeads is a full-service digital marketing agency for US businesses, with a senior team in Bengaluru, India."),
    ("Marketing retainers start from ₹40,000 a month.", f"Marketing retainers start from {P['retainer']} a month."),
    ("Still wondering something? Ask us on WhatsApp. A real person replies, not a bot.",
     "Still wondering something? Email us or message us on WhatsApp. A real person replies, not a bot."),
    ("We go live with tracking from day one, so every rupee and every lead is visible.",
     "We go live with tracking from day one, so every dollar and every lead is visible."),
    ("We go live with full tracking, so every rupee and every lead is visible.",
     "We go live with full tracking, so every dollar and every lead is visible."),
    ("Keeps every rupee accountable, from client budgets", "Keeps every dollar accountable, from client budgets"),
    ("Keeps every rupee accountable", "Keeps every dollar accountable"),
    ("every rupee accounted for", "every dollar accounted for"),
    ("Tell us your goal. Our Bengaluru team replies within 24 hours.",
     "Tell us your goal. Our team replies within one business day."),
    ("Phone / WhatsApp<input type=\"tel\" name=\"phone\" placeholder=\"+91\"",
     "Phone<input type=\"tel\" name=\"phone\" placeholder=\"+1\""),
    ("New growth plan request – GreyLeads website", "New growth plan request – GreyLeads US website"),
    # AI answer mockup on the home page
    ("Best digital marketing agency in Bengaluru?", "Best lead generation agency for B2B?"),
    (">greyleads.in<", ">greyleads.us<"),
]

PAGE_REPL = {
    "/": [
    ],
    "/lead-generation": [
        ("It depends on your market and deal size. Most clients start from ₹75,000 a month in ad spend, and we'll recommend a figure in your free audit.",
         f"It depends on your market and deal size. Most US clients start from {P['lead_spend']} a month in ad spend, plus our management fee from {P['lead_mgmt']} a month. We'll recommend a figure in your free audit."),
        ("Yes. We connect to Zoho, HubSpot, Salesforce, LeadSquared and most popular CRMs, or set one up for you, with instant WhatsApp and email follow-ups.",
         "Yes. We connect to HubSpot, Salesforce, Pipedrive, Zoho and most popular CRMs, or set one up for you, with instant email and SMS follow-ups."),
        ("Do you offer lead generation in Bangalore and Chennai?", "Do you work with US companies?"),
        ("Yes. Our team is based in Bellandur, Bengaluru, and we run lead generation for brands across Bangalore, Chennai and metro India, targeting the areas and audiences you actually serve.",
         "Yes. Our senior team is based in Bengaluru, India, and runs lead generation for companies across the United States, targeting the states, industries and job titles you actually sell to. We schedule calls in your time zone."),
        ("backed by focused landing pages, lead scoring and instant WhatsApp and email follow-ups.",
         "backed by focused landing pages, lead scoring and instant email and SMS follow-ups."),
        ("Instant WhatsApp and email follow-ups keep every lead warm", "Instant email and SMS follow-ups keep every lead warm"),
        ("get a WhatsApp or email reply within seconds", "get an email or SMS reply within seconds"),
    ],
    "/websites": [
        ("Every site is a fixed-price project based on pages, features and integrations. Most projects range from ₹1.5 lakh to ₹6 lakh, and you'll get an exact quote after a short discovery call.",
         f"Every site is a fixed-price project based on pages, features and integrations. Most projects range from {P['web_from']} to {P['web_to']}, and you'll get an exact quote after a short discovery call."),
        ("Yes. Monthly care plans cover updates, backups, security and small changes, from ₹8,000 a month.",
         f"Yes. Monthly care plans cover updates, backups, security and small changes, from {P['care']} a month."),
        ("Do you build websites for businesses in Bangalore and Chennai?", "Do you build websites for US businesses?"),
        ("Yes. We design and build websites from our studio in Bellandur, Bengaluru, for businesses across Bangalore, Chennai and the rest of India.",
         "Yes. We design and build websites for businesses across the United States from our studio in Bengaluru, India, with reviews and calls scheduled in your time zone."),
    ],
    "/apps": [
        ("It depends on features and platforms. A focused first version typically ranges from ₹6 lakh to ₹25 lakh. You'll get a fixed quote after discovery.",
         f"It depends on features and platforms. A focused first version typically ranges from {P['app_from']} to {P['app_to']}. You'll get a fixed quote after discovery."),
        ("Do you develop apps for startups and businesses in Bangalore?", "Do you develop apps for US startups and businesses?"),
        ("Yes. From our Bengaluru studio we design and build iOS, Android and web apps for startups and businesses across Bangalore, Chennai and India.",
         "Yes. From our studio in Bengaluru, India, we design and build iOS, Android and web apps for startups and businesses across the US, with sprint reviews scheduled in your time zone."),
    ],
    "/performance-marketing": [
        ("Every rupee,", "Every dollar,"),
        ("Every rupee", "Every dollar"),
        ("We connect every rupee to a result.", "We connect every dollar to a result."),
        ("We usually recommend at least ₹50,000 a month in ad spend to get meaningful data, plus our management fee.",
         f"We usually recommend at least {P['ppc_spend']} a month in ad spend to get meaningful data, plus our management fee."),
        ("A fixed monthly management fee based on scope. Most clients start from ₹40,000 a month.",
         f"A fixed monthly management fee based on scope. Most clients start from {P['ppc_mgmt']} a month."),
        ("Do you run ads for businesses in Bangalore and Chennai?", "Do you run ads for US businesses?"),
        ("Yes. We manage campaigns for brands across Bangalore, Chennai and metro India from our Bengaluru team, targeting the cities and areas you serve.",
         "Yes. Our team in Bengaluru, India, manages campaigns for businesses across the United States, targeting the states, cities and audiences you serve."),
    ],
    "/seo-aeo": [
        ("best agency in Bangalore", "best agency for B2B leads"),
        ("Bangalore and Chennai", "Your city, nationwide"),
        ("Are you an SEO company in Bangalore?", "Do you do SEO for US businesses?"),
        ("Yes. GreyLeads is an SEO and AEO agency based in Bellandur, Bengaluru, also serving Chennai and metro India. We handle technical SEO, local SEO and Google Business Profile, content, and visibility in AI answers.",
         "Yes. GreyLeads is an SEO and AEO agency with a senior team in Bengaluru, India, working with businesses across the US. We handle technical SEO, local SEO and Google Business Profile, content, and visibility in AI answers."),
    ],
    "/branding": [
        ("Are you a branding agency in Bangalore?", "Do you work with US brands?"),
        ("Yes. We create brand identities and run social media for businesses across Bangalore, Chennai and India from our studio in Bellandur, Bengaluru.",
         f"Yes. We create brand identities and run social media for businesses across the United States from our studio in Bengaluru, India. Brand identity projects start from {P['brand']}."),
    ],
    "/automation": [
        ("Do you set up marketing automation for businesses in Bangalore and Chennai?", "Do you set up marketing automation for US businesses?"),
        ("Yes. We set up CRM and marketing automation for businesses across Bangalore, Chennai and India, working from our Bengaluru team.",
         f"Yes. We set up CRM and marketing automation for businesses across the United States, working from our team in Bengaluru, India. Setups start from {P['automation']}."),
        ("Lead capture from your website, ads and forms, CRM updates, instant WhatsApp and email replies,",
         "Lead capture from your website, ads and forms, CRM updates, instant email, SMS and WhatsApp replies,"),
    ],
    "/about": [
        ("GreyLeads is a Bengaluru-based digital marketing studio. We help ambitious brands stop blending in, and start getting chosen.",
         "GreyLeads is a senior digital marketing studio in Bengaluru, India, working with US businesses. We help ambitious brands stop blending in, and start getting chosen."),
        ("Today we work with startups, D2C brands, education companies, B2B firms and local businesses across India and beyond, from our studio in Bellandur, Bengaluru.",
         "Today we work with startups, D2C brands, education companies, B2B firms and local businesses in the US, Europe and India, from our studio in Bellandur, Bengaluru."),
    ],
    "/contact": [
        ("Tell us what you're working on. A senior strategist, not a salesperson, will get back to you within one working day.",
         "Tell us what you're working on. A senior strategist, not a salesperson, will get back to you within one business day and book a call in your time zone."),
        ("Hi! We run a clinic in Bengaluru and want more patient enquiries online.",
         "Hi! We run a dental practice in Austin and want more patient inquiries online."),
        ("Bengaluru (Bangalore) studio", "Our studio · Bengaluru, India"),
        ("Bellandur, Bengaluru (Bangalore)<br>", "Bellandur, Bengaluru<br>"),
        ("Visits by appointment. Please call or WhatsApp before you drop in.",
         "We meet US clients on Zoom or Google Meet, scheduled in your time zone. Studio visits by appointment."),
    ],
    "/privacy": [
        ("You can reach us at", "This policy covers greyleads.us and greyleads.in. You can reach us at"),
    ],
}

# US spelling, applied to visible text only (not inside tags, styles or URLs).
SPELL = [
    (r"\boptimis(e|ed|es|ing|ation|ations)\b", r"optimiz\1"),
    (r"\bOptimis(e|ed|es|ing|ation|ations)\b", r"Optimiz\1"),
    (r"\borganis(e|ed|es|ing|ation|ations)\b", r"organiz\1"),
    (r"\brecognis(e|ed|es|ing|able)\b", r"recogniz\1"),
    (r"\banalys(e|ed|es|ing)\b", r"analyz\1"),
    (r"\bcolours\b", "colors"), (r"\bcolour\b", "color"), (r"\bColours\b", "Colors"), (r"\bColour\b", "Color"),
    (r"\bbehaviour", "behavior"), (r"\bfavourite", "favorite"), (r"\bcentre", "center"),
    (r"\benquiries\b", "inquiries"), (r"\benquiry\b", "inquiry"), (r"\bEnquiries\b", "Inquiries"), (r"\bEnquiry\b", "Inquiry"),
    (r"\bprogramme", "program"), (r"\bcatalogue", "catalog"), (r"\blicence\b", "license"),
]

LEFTOVER = re.compile(r"₹|lakh|crore|Bangalore|Chennai|Mumbai|Hyderabad|Pune|Delhi|metro India|rupee", re.I)

warnings = []


def warn(msg):
    warnings.append(msg)


def split_protected(s):
    """Split html into [(is_protected, chunk)] where <style> blocks are protected."""
    parts, pos = [], 0
    for m in re.finditer(r"<style\b.*?</style>", s, re.S):
        parts.append((False, s[pos:m.start()]))
        parts.append((True, m.group(0)))
        pos = m.end()
    parts.append((False, s[pos:]))
    return parts


def replace_text(s, pairs, where):
    parts = split_protected(s)
    for old, new in pairs:
        variants = {old: new, html.escape(old, quote=False): html.escape(new, quote=False),
                    old.replace("'", "&#39;"): new.replace("'", "&#39;"), old.replace("'", "’"): new.replace("'", "’")}
        n = 0
        for v, nv in variants.items():
            for i, (prot, chunk) in enumerate(parts):
                if prot or v not in chunk:
                    continue
                n += chunk.count(v)
                parts[i] = (prot, chunk.replace(v, nv))
        if n == 0:
            warn(f"{where}: no match for: {old[:90]}")
    return "".join(c for _, c in parts)


def spell_text(s):
    """Apply US spelling to text nodes and JSON-LD string values only."""
    def fix(t):
        for a, b in SPELL:
            t = re.sub(a, b, t)
        return t

    out = []
    for prot, chunk in split_protected(s):
        if prot:
            out.append(chunk)
            continue
        # text between tags (also covers JSON-LD contents); skip anything that looks like a URL path
        def tx(m):
            t = m.group(1)
            return ">" + re.sub(r"(?<![/\-\w])([^\"/<>]+)", lambda mm: fix(mm.group(1)), t) + "<"
        chunk = re.sub(r">([^<]+)<", tx, chunk)
        # meta descriptions, alt text and aria labels
        chunk = re.sub(r'((?:content|alt|aria-label|title|placeholder)=")([^"]*)(")',
                       lambda m: m.group(1) + (fix(m.group(2)) if "://" not in m.group(2) else m.group(2)) + m.group(3), chunk)
        out.append(chunk)
    return "".join(out)


ORG_PATCH = {
    "@id": US + "/#organization",
    "url": US + "/",
    "description": "Senior digital marketing agency in Bengaluru, India, working with US businesses: B2B lead generation, websites and apps, Google, Meta and LinkedIn ads, SEO and AEO, creative and marketing automation.",
    "priceRange": "$$",
    "areaServed": [{"@type": "Country", "name": "United States"}],
    "logo": {"@type": "ImageObject", "url": US + "/apple-touch-icon.png", "width": 180, "height": 180},
    "image": US + "/assets/og-image-us.jpg",
}


def patch_jsonld(s, path, meta):
    def fix_node(n):
        if isinstance(n, dict):
            t = n.get("@type")
            ts = t if isinstance(t, list) else [t]
            if "Organization" in ts:
                n.update(ORG_PATCH)
                cp = n.get("contactPoint")
                if isinstance(cp, dict):
                    cp["areaServed"] = "US"
                    cp["availableLanguage"] = ["English"]
                n["sameAs"] = [u for u in n.get("sameAs", []) if "google.com/maps" not in u] + [IN + "/"]
                n.pop("hasMap", None)
            if "WebSite" in ts:
                n["inLanguage"] = "en-US"
                n["@id"] = US + "/#website"
                n["url"] = US + "/"
            if "WebPage" in ts and meta:
                n["name"] = meta["title"]
                n["description"] = meta["desc"]
            if "Service" in ts:
                n["areaServed"] = [{"@type": "Country", "name": "United States"}]
                if meta and meta.get("service"):
                    n["name"] = meta["service"]
                if meta:
                    n["description"] = meta["desc"]
            if "inLanguage" in n:
                n["inLanguage"] = "en-US"
            for k, v in list(n.items()):
                n[k] = fix_node(v)
            return n
        if isinstance(n, list):
            return [fix_node(x) for x in n]
        if isinstance(n, str):
            v = n
            if v.startswith(IN) and v != IN + "/":
                tail = v[len(IN):]
                if any(tail.startswith(e) for e in EXTERNAL) or tail.startswith("/assets/og"):
                    return v if not tail.startswith("/assets/og") else US + tail
                return US + tail
            return v
        return n

    def repl(m):
        d = json.loads(m.group(1))
        d = fix_node(d)
        return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "</script>"

    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, s, flags=re.S)


def patch_head(s, path, meta):
    s = s.replace('<html lang="en-IN">', '<html lang="en-US">')
    if path is None:
        return s
    url = US + (path if path != "/" else "/")
    in_url = IN + (path if path != "/" else "/")
    if meta:
        t = html.escape(meta["title"], quote=False)
        d = html.escape(meta["desc"], quote=True)
        s = re.sub(r"<title>.*?</title>", "<title>" + t + "</title>", s, count=1, flags=re.S)
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            s = re.sub(r'<meta ' + attr + r' content="[^"]*">', '<meta ' + attr + ' content="' + d + '">', s, count=1)
        for attr in ('property="og:title"', 'name="twitter:title"'):
            s = re.sub(r'<meta ' + attr + r' content="[^"]*">', '<meta ' + attr + ' content="' + html.escape(meta["title"], quote=True) + '">', s, count=1)
        s = re.sub(r'<meta name="keywords" content="[^"]*">', '<meta name="keywords" content="' + html.escape(meta["kw"], quote=True) + '">', s, count=1)
        if meta.get("alt"):
            s = re.sub(r'<meta property="og:image:alt" content="[^"]*">', '<meta property="og:image:alt" content="' + html.escape(meta["alt"], quote=True) + '">', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="' + url + '">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="' + url + '">', s, count=1)
    # geo tags point at Bengaluru; not useful for a US-facing site
    s = re.sub(r'<meta name="(geo\.region|geo\.placename|geo\.position|ICBM)" content="[^"]*">\n?', "", s)
    # hreflang: US page <-> India page
    s = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', "", s)
    s = s.replace("<!--seo-->\n", "<!--seo-->\n"
                  f'<link rel="alternate" hreflang="en-US" href="{url}">\n'
                  f'<link rel="alternate" hreflang="en-IN" href="{in_url}">\n'
                  f'<link rel="alternate" hreflang="x-default" href="{in_url}">\n', 1)
    s = s.replace('<meta property="og:locale" content="en_IN">', '<meta property="og:locale" content="en_US">\n<meta property="og:locale:alternate" content="en_IN">')
    # og images are served from the US domain
    s = re.sub(r'(content=")' + re.escape(IN) + r'(/assets/)', r"\1" + US + r"\2", s)
    if path == "/":
        s = s.replace(US + "/assets/og-image.jpg", US + "/assets/og-image-us.jpg")
    return s


def patch_links(s):
    # Blog and careers stay on greyleads.in
    for e in EXTERNAL:
        s = re.sub(r'href="' + re.escape(e) + r'(["/#?])', 'href="' + IN + e + r"\1", s)
    # absolute links to India pages that exist on the US site
    def ab(m):
        tail = m.group(1)
        if any(tail.startswith(e) for e in EXTERNAL):
            return m.group(0)
        return 'href="' + US + tail + '"'
    s = re.sub(r'href="' + re.escape(IN) + r'(/[^"]*)"', ab, s)
    # identify US form submissions
    s = s.replace('<input type="hidden" name="_template" value="table">',
                  '<input type="hidden" name="_template" value="table">\n<input type="hidden" name="source" value="greyleads.us">')
    return s


def add_price(s, path, meta):
    if not meta or not meta.get("hero"):
        return s
    new = meta["hero"][1]
    i = s.find(new)
    if i < 0:
        warn(f"{path}: hero text not found for price line")
        return s
    j = s.find("</p>", i) + 4
    return s[:j] + "\n" + PRICE_LINE.format(price=meta["price"]) + s[j:]



# ---------------------------------------------------------------------------
# Home page: extra section for US buyers, inserted after "Why GreyLeads".
# ---------------------------------------------------------------------------
def _card(title, text):
    return ('<div class="gl-card" style="background: #FFFFFF; border-radius: 28px; padding: 32px; display: flex; '
            'flex-direction: column; gap: 14px; box-shadow: 0 20px 50px rgba(76,29,149,0.06)">'
            '<h3 style="font-family: \'Bricolage Grotesque\', sans-serif; font-weight: 700; font-size: 24px; '
            'letter-spacing: -0.03em; margin: 0">' + title + '</h3>'
            '<p style="font-size: 16px; line-height: 1.6; color: #4A4360; margin: 0">' + text + '</p></div>')


def _price(label, price, href):
    return ('<a href="' + href + '" class="gl-card" style="text-decoration: none; background: rgba(255,255,255,0.7); '
            'border: 1px solid rgba(18,11,36,0.08); border-radius: 20px; padding: 20px 22px; display: flex; '
            'flex-direction: column; gap: 6px">'
            '<span style="font-family: \'Geist Mono\', monospace; font-size: 12px; letter-spacing: 0.08em; '
            'text-transform: uppercase; color: #6E6585">' + label + '</span>'
            '<span style="font-family: \'Bricolage Grotesque\', sans-serif; font-weight: 800; font-size: 26px; '
            'letter-spacing: -0.03em; color: #120B24">from <span style="color: #6D2EC7">' + price + '</span></span></a>')


US_SECTION = (
    '\n<section class="gl-cv" id="us-clients" style="max-width: 1320px; margin: 0 auto; padding: 0 28px 128px">\n'
    '<div style="font-family: \'Geist Mono\', monospace; font-size: 13px; letter-spacing: 0.08em; '
    'text-transform: uppercase; color: #6E6585">For US teams</div>\n'
    '<h2 style="font-family: \'Bricolage Grotesque\', sans-serif; font-weight: 800; font-size: clamp(38px, 5vw, 72px); '
    'line-height: 0.98; letter-spacing: -0.045em; margin: 24px 0 0">A senior team, <span class="gl-gt" '
    'style="font-family: \'Instrument Serif\', serif; font-style: italic; font-weight: 400">on your clock.</span></h2>\n'
    '<p style="font-size: 19px; line-height: 1.6; color: #4A4360; margin: 24px 0 0; max-width: 680px">'
    'Our studio is in Bengaluru, India. Our clients are wherever the growth is. Here is how working with us '
    'looks from the US.</p>\n'
    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-top: 56px">'
    + _card("Calls on your time.", "Kickoffs, reviews and monthly reports are scheduled in your US time zone, on Zoom or Google Meet.")
    + _card("Work moves overnight.", "We work while you sleep, so feedback you send at the end of your day is often done by the next morning.")
    + _card("Senior talent, sensible cost.", "An experienced team for websites, apps, ads and SEO, for a fraction of a typical US agency retainer.")
    + _card("Your accounts, your data.", "Everything runs in your ad accounts, CRM and domains from day one. Month to month after the first three months.")
    + '</div>\n'
    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 16px">'
    + _price("Lead generation", P["lead_mgmt"] + "/mo", "/lead-generation")
    + _price("Websites", P["web_from"], "/websites")
    + _price("Apps", P["app_from"], "/apps")
    + _price("Ads management", P["ppc_mgmt"] + "/mo", "/performance-marketing")
    + _price("SEO &amp; AEO", P["seo"] + "/mo", "/seo-aeo")
    + '</div>\n</section>\n'
)


def add_us_section(s, path):
    if path != "/":
        return s
    i = s.find('<section class="gl-cv" id="why"')
    if i < 0:
        warn("index.html: 'why' section not found; US section not added")
        return s
    j = s.find("</section>", i) + len("</section>")
    return s[:j] + US_SECTION + s[j:]



def build_page(src, path):
    s = open(os.path.join(ROOT, src), encoding="utf-8").read()
    meta = META.get(path)
    pairs = list(COMMON)
    if meta and meta.get("hero"):
        pairs.insert(0, meta["hero"])
    pairs += PAGE_REPL.get(path, [])
    # common pairs are optional on pages that don't contain them
    s2 = s
    for old, new in pairs:
        before = s2
        s2 = replace_text(s2, [(old, new)], src)
        if s2 == before and (old, new) in COMMON:
            warnings.pop()  # not every page has every common string
    s = s2
    s = spell_text(s)
    s = patch_jsonld(s, path, meta)
    s = patch_links(s)
    s = patch_head(s, path, meta)
    s = add_price(s, path, meta)
    s = add_us_section(s, path)
    # leftover India-specific words in visible text (ignore the address/schema)
    body = re.sub(r"<style\b.*?</style>|<script\b.*?</script>|<head>.*?</head>", "", s, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", body)
    for m in LEFTOVER.finditer(text):
        ctx = text[max(0, m.start() - 60): m.end() + 60].replace("\n", " ")
        warn(f"{src}: leftover '{m.group(0)}': …{' '.join(ctx.split())}…")
    out = os.path.join(OUT, src)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(s)
    return s


def copy_assets(pages_html):
    used = set()
    for s in pages_html:
        for m in re.findall(r'(?:src|href|srcset|content|poster|data-src)="([^"]+)"', s):
            for part in m.split(","):
                u = part.strip().split(" ")[0]
                if u.startswith(US + "/assets/"):
                    u = u[len(US):]
                if u.startswith("/assets/"):
                    used.add(u.split("?")[0].split("#")[0])
        for m in re.findall(r"url\(['\"]?(/assets/[^'\")]+)", s):
            used.add(m)
    used |= {"/assets/fonts/" + f for f in os.listdir(os.path.join(ROOT, "assets/fonts"))}
    n = 0
    for u in sorted(used):
        src = os.path.join(ROOT, u.lstrip("/"))
        if not os.path.exists(src):
            if not u.endswith("og-image-us.jpg"):
                warn(f"asset missing: {u}")
            continue
        dst = os.path.join(OUT, u.lstrip("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    us_og = os.path.join(ROOT, "tools", "us-og-image.jpg")
    if os.path.exists(us_og):
        shutil.copy2(us_og, os.path.join(OUT, "assets", "og-image-us.jpg"))
    return n


def write_static():
    for f in ("favicon.svg", "apple-touch-icon.png", "_headers"):
        shutil.copy2(os.path.join(ROOT, f), os.path.join(OUT, f))
    redirects = open(os.path.join(ROOT, "_redirects"), encoding="utf-8").read()
    keep = []
    for line in redirects.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1].startswith("/blog"):
            continue  # blog lives on greyleads.in
        keep.append(line)
    keep.append(f"/blog {IN}/blog 301")
    keep.append(f"/blog/* {IN}/blog/:splat 301")
    keep.append(f"/careers {IN}/careers 301")
    open(os.path.join(OUT, "_redirects"), "w").write("\n".join(keep) + "\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {US}/sitemap.xml\n")
    urls = [p for _, p in PAGES if p]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for p in urls:
        pr = "1.0" if p == "/" else ("0.9" if p.count("/") == 1 and p not in ("/privacy", "/team", "/process") else "0.6")
        sm.append(f"  <url><loc>{US}{p}</loc>"
                  f'<xhtml:link rel="alternate" hreflang="en-US" href="{US}{p}"/>'
                  f'<xhtml:link rel="alternate" hreflang="en-IN" href="{IN}{p}"/>'
                  f"<priority>{pr}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(OUT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    open(os.path.join(OUT, ".assetsignore"), "w").write("wrangler.jsonc\n.assetsignore\nREADME.md\n")
    open(os.path.join(OUT, "wrangler.jsonc"), "w").write(
        "// Cloudflare Workers config for the GreyLeads US website (greyleads.us).\n"
        "// Generated by tools/build-us-site.py. Deploy from this folder (root directory: us-site).\n"
        "{\n"
        '  "name": "greyleads-us",\n'
        '  "compatibility_date": "2025-09-01",\n'
        '  "workers_dev": true,\n'
        '  "preview_urls": true,\n'
        "  // Uncomment once greyleads.us is bought and added to Cloudflare:\n"
        '  // "routes": [\n'
        '  //   { "pattern": "greyleads.us", "custom_domain": true },\n'
        '  //   { "pattern": "www.greyleads.us", "custom_domain": true }\n'
        "  // ],\n"
        '  "assets": {\n'
        '    "directory": ".",\n'
        '    "html_handling": "auto-trailing-slash",\n'
        '    "not_found_handling": "404-page"\n'
        "  }\n"
        "}\n")
    open(os.path.join(OUT, "llms.txt"), "w").write(LLMS)
    open(os.path.join(OUT, "README.md"), "w").write(
        "# GreyLeads US website (greyleads.us)\n\n"
        "Generated from the India site by `python3 tools/build-us-site.py`. Don't edit these files by hand:\n"
        "change the India page or the US copy/prices in the script, then re-run it and commit.\n\n"
        "## Go live\n\n"
        "1. Buy greyleads.us and add it to Cloudflare (Websites -> Add a domain).\n"
        "2. Cloudflare -> Workers & Pages -> Create -> Import a repository -> greyleads5/greyleads.\n"
        "   Project name `greyleads-us`, root directory `us-site`, deploy command `npx wrangler deploy`.\n"
        "3. In `us-site/wrangler.jsonc` (via the script), uncomment the greyleads.us routes, re-run, push.\n"
        "4. Redirect www.greyleads.us -> greyleads.us (Rules -> Redirect Rules).\n"
        "5. FormSubmit: the first form sent from greyleads.us triggers an activation email to\n"
        "   greyleads5@gmail.com. Click it once.\n"
        "6. Google Search Console: add greyleads.us, submit sitemap.xml. Bing Webmaster: import.\n"
        "7. On greyleads.in, add the matching hreflang en-US links back to greyleads.us so Google\n"
        "   pairs the two sites (hreflang only works when both sides point at each other).\n")


LLMS = f"""# GreyLeads (US)

> GreyLeads (GreyLeads Solutions Pvt Ltd) is a full-service digital marketing agency with a senior team in Bengaluru, India, working with businesses across the United States. One team runs B2B lead generation, builds websites and apps, manages Google, Meta, LinkedIn and YouTube ads, handles SEO and AEO (answer engine optimization), creates ad creative and brand identities, and automates CRM, email and SMS follow-up. We report on leads, sales and cost per customer.

## Key facts

- Name: GreyLeads (legal name: GreyLeads Solutions Pvt Ltd)
- Type: Digital marketing and lead generation agency
- Serves: businesses across the United States (US site: {US}; India site: {IN})
- Team location: RMZ Ecoworld, Building 6A, Outer Ring Road, Bellandur, Bengaluru, Karnataka 560103, India
- Calls: scheduled in the client's US time zone, on Zoom or Google Meet
- Founder and CEO: John Jayaseelan
- Phone and WhatsApp: +91 70105 52833
- Email: contact@greyleads.in
- Pricing: marketing retainers from {P['retainer']} a month; websites from {P['web_from']}; apps from {P['app_from']}; fixed quotes after a discovery call
- Contracts: a three-month starting period for marketing, then month to month
- Ownership: clients own their website, app code, ad accounts, creatives and data from day one

## Services

- [B2B lead generation]({US}/lead-generation): verified B2B data, LinkedIn, Google and Meta lead campaigns, landing pages, lead scoring, CRM and instant follow-up. From {P['lead_mgmt']}/month.
- [Website design and development]({US}/websites): fast, conversion-focused websites and e-commerce. From {P['web_from']}.
- [Mobile app development]({US}/apps): iOS, Android and web apps. First versions from {P['app_from']}.
- [SEO and AEO]({US}/seo-aeo): technical and local SEO, content, and visibility in ChatGPT, Gemini and Google AI answers. From {P['seo']}/month.
- [Performance marketing]({US}/performance-marketing): Google, Meta, YouTube and LinkedIn ads managed for leads and sales. From {P['ppc_mgmt']}/month.
- [Creative ads]({US}/creative-ads): video, UGC-style, static and carousel ads, tested every week. From {P['creative']}/month.
- [Branding and social media]({US}/branding): brand identity, guidelines and social media management. From {P['brand']}.
- [Marketing automation]({US}/automation): HubSpot, Salesforce and Zoho CRM setup, email and SMS sequences, sales alerts. From {P['automation']}.

## Case studies

- [IAcharya]({US}/work/iacharya): SEO and ad campaigns. Page 1 on Google within six months and 150+ course leads every month.
- [Greyweave]({US}/work/greyweave): a brand-new website reached page 1 on Google in six months.
- [Pix.city]({US}/work/pixcity): targeted, 100% verified decision-maker data across France and Europe.
- [Quadrate]({US}/work/quadrate): targeted, 100% verified B2B data for a sales team.
- [SOLIZE]({US}/work/solize): LinkedIn ad campaigns for a global digital engineering brand.
- [Jona's Cafe]({US}/work/jonas-cafe): mobile app rebuilt for iOS and Android.

## Company

- [About]({US}/about) · [Team]({US}/team) · [How we work]({US}/process) · [Contact]({US}/contact) · [Blog]({IN}/blog)
"""


def main():
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            p = os.path.join(OUT, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    built = [build_page(src, path) for src, path in PAGES]
    n = copy_assets(built)
    write_static()
    print(f"Built {len(built)} pages and {n} assets into {os.path.relpath(OUT, ROOT)}/")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print("  WARNING", w)


if __name__ == "__main__":
    main()
