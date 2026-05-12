"""
Daily Briefing Email Sender — Multi-Theme Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Daily Briefing Email Sender — Multi-Theme Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Receives JSON from Claude Routine, builds themed HTML, sends via Brevo API.

Design themes (rotates weekly, or set via JSON/env):
  linear   — dark minimal, purple accents (like Linear.app)
  vercel   — pure black/white, sharp typography (like Vercel)
  stripe   — clean white, indigo/purple gradients (like Stripe)
  apple    — frosted glass, SF-style typography (like Apple)
  framer   — bold gradients, expressive color (like Framer)

Environment variables:
  BREVO_API_KEY       - Brevo API key (brevo.com → Settings → API Keys)
  SENDER_EMAIL        - verified sender email (verify a single address in Brevo — no domain needed)
  SENDER_NAME         - display name for sender (default: "Kagen AI")
  RECIPIENT_EMAIL     - recipient email address
  BRIEFING_JSON       - JSON string from Claude Routine
  DESIGN_THEME        - optional override (linear/vercel/stripe/apple/framer)
  GH_KEY              - GitHub personal access token (Contents: write) for archiving HTML

Expected JSON from Routine:
{
  "urgent":             ["..."],
  "important":          ["..."],
  "meetings":           ["..."],
  "suggested_replies":  ["..."],
  "pending_followups":  ["..."],
  "new_documents":      ["..."],
  "professional_count": 10,
  "personal_count":     2,
  "design_theme":       "linear"   ← optional, Routine can set this
}
"""

import os, sys, json, urllib.request, urllib.error
from datetime import datetime, date

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────

BREVO_API_KEY   = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL    = os.environ.get("SENDER_EMAIL")
SENDER_NAME     = os.environ.get("SENDER_NAME", "Kagen AI")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
BRIEFING_JSON   = os.environ.get("BRIEFING_JSON")
ENV_THEME       = os.environ.get("DESIGN_THEME", "").lower()
GH_KEY          = os.environ.get("GH_KEY")
GH_REPO         = "realavalanche/daily-briefings"

# Weekly rotation — same theme all week, changes every Monday
WEEKLY_THEMES = ["linear", "vercel", "stripe", "apple", "framer"]

def get_weekly_theme():
    week_number = date.today().isocalendar()[1]
    return WEEKLY_THEMES[week_number % len(WEEKLY_THEMES)]


# ─────────────────────────────────────────────────────────
# THEME DEFINITIONS
# ─────────────────────────────────────────────────────────

THEMES = {

    # ── LINEAR — dark, minimal, purple
    "linear": {
        "name":          "Linear",
        "bg":            "#0f0f13",
        "card_bg":       "#16161d",
        "card_border":   "1px solid #2a2a35",
        "card_radius":   "10px",
        "header_bg":     "linear-gradient(135deg,#0f0f13,#1a1025)",
        "header_text":   "#ffffff",
        "header_sub":    "#666680",
        "divider":       "linear-gradient(90deg,#5b5bd6,#8b5cf6,#5b5bd6)",
        "footer_bg":     "#0f0f13",
        "footer_text":   "#444455",
        "badge_bg":      "rgba(91,91,214,0.15)",
        "badge_text":    "#8b8bff",
        "label_style":   "font-size:10px;letter-spacing:2px;text-transform:uppercase;",
        "sections": {
            "urgent":            ("#ff6b6b", "🔴"),
            "important":         ("#f59e0b", "🟡"),
            "meetings":          ("#5b5bd6", "📅"),
            "suggested_replies": ("#10b981", "✉️"),
            "pending_followups": ("#8b5cf6", "⏳"),
            "new_documents":     ("#06b6d4", "📁"),
        },
        "bullet_color":  "#5b5bd6",
        "item_color":    "#c4c4d4",
        "count_bg":      "rgba(255,255,255,0.08)",
        "count_color":   "#888899",
        "summary_nums":  ["#5b5bd6", "#10b981", "#8b5cf6"],
    },

    # ── VERCEL — pure black/white, sharp
    "vercel": {
        "name":          "Vercel",
        "bg":            "#111111",
        "card_bg":       "#1a1a1a",
        "card_border":   "1px solid #333333",
        "card_radius":   "8px",
        "header_bg":     "#000000",
        "header_text":   "#ffffff",
        "header_sub":    "#555555",
        "divider":       "linear-gradient(90deg,#ffffff,#555,#ffffff)",
        "footer_bg":     "#000000",
        "footer_text":   "#333333",
        "badge_bg":      "#222222",
        "badge_text":    "#888888",
        "label_style":   "font-size:9px;letter-spacing:3px;text-transform:uppercase;font-weight:700;",
        "sections": {
            "urgent":            ("#ff4444", "🔴"),
            "important":         ("#ffaa00", "🟡"),
            "meetings":          ("#ffffff", "📅"),
            "suggested_replies": ("#00cc88", "✉️"),
            "pending_followups": ("#aa88ff", "⏳"),
            "new_documents":     ("#44aaff", "📁"),
        },
        "bullet_color":  "#ffffff",
        "item_color":    "#aaaaaa",
        "count_bg":      "#222222",
        "count_color":   "#666666",
        "summary_nums":  ["#ffffff", "#00cc88", "#aa88ff"],
    },

    # ── STRIPE — white, indigo, professional
    "stripe": {
        "name":          "Stripe",
        "bg":            "#f6f9fc",
        "card_bg":       "#ffffff",
        "card_border":   "1px solid #e6ebf1",
        "card_radius":   "12px",
        "header_bg":     "linear-gradient(135deg,#635bff,#0a2540)",
        "header_text":   "#ffffff",
        "header_sub":    "rgba(255,255,255,0.6)",
        "divider":       "linear-gradient(90deg,#635bff,#00d4ff,#635bff)",
        "footer_bg":     "#f6f9fc",
        "footer_text":   "#8898aa",
        "badge_bg":      "rgba(99,91,255,0.1)",
        "badge_text":    "#635bff",
        "label_style":   "font-size:11px;letter-spacing:1px;text-transform:uppercase;",
        "sections": {
            "urgent":            ("#e25950", "🔴"),
            "important":         ("#e39f48", "🟡"),
            "meetings":          ("#635bff", "📅"),
            "suggested_replies": ("#24b47e", "✉️"),
            "pending_followups": ("#6772e5", "⏳"),
            "new_documents":     ("#43a8c7", "📁"),
        },
        "bullet_color":  "#635bff",
        "item_color":    "#525f7f",
        "count_bg":      "rgba(99,91,255,0.08)",
        "count_color":   "#8898aa",
        "summary_nums":  ["#635bff", "#24b47e", "#6772e5"],
    },

    # ── APPLE — frosted, clean, SF-inspired
    "apple": {
        "name":          "Apple",
        "bg":            "#f5f5f7",
        "card_bg":       "rgba(255,255,255,0.85)",
        "card_border":   "1px solid rgba(0,0,0,0.06)",
        "card_radius":   "18px",
        "header_bg":     "linear-gradient(180deg,#1d1d1f,#2d2d2f)",
        "header_text":   "#f5f5f7",
        "header_sub":    "#86868b",
        "divider":       "linear-gradient(90deg,#0071e3,#34aadc,#0071e3)",
        "footer_bg":     "#f5f5f7",
        "footer_text":   "#86868b",
        "badge_bg":      "rgba(0,113,227,0.1)",
        "badge_text":    "#0071e3",
        "label_style":   "font-size:11px;letter-spacing:0.5px;font-weight:600;",
        "sections": {
            "urgent":            ("#ff3b30", "🔴"),
            "important":         ("#ff9500", "🟡"),
            "meetings":          ("#0071e3", "📅"),
            "suggested_replies": ("#34c759", "✉️"),
            "pending_followups": ("#5856d6", "⏳"),
            "new_documents":     ("#32ade6", "📁"),
        },
        "bullet_color":  "#0071e3",
        "item_color":    "#1d1d1f",
        "count_bg":      "rgba(0,0,0,0.04)",
        "count_color":   "#86868b",
        "summary_nums":  ["#0071e3", "#34c759", "#5856d6"],
    },

    # ── FRAMER — bold, expressive, gradient-heavy
    "framer": {
        "name":          "Framer",
        "bg":            "#0a0a0f",
        "card_bg":       "#111118",
        "card_border":   "1px solid rgba(255,255,255,0.06)",
        "card_radius":   "16px",
        "header_bg":     "linear-gradient(135deg,#0a0a0f 0%,#1a0a2e 50%,#0a1a2e 100%)",
        "header_text":   "#ffffff",
        "header_sub":    "#555577",
        "divider":       "linear-gradient(90deg,#ff3cac,#784ba0,#2b86c5)",
        "footer_bg":     "#0a0a0f",
        "footer_text":   "#333355",
        "badge_bg":      "rgba(255,60,172,0.12)",
        "badge_text":    "#ff3cac",
        "label_style":   "font-size:10px;letter-spacing:2px;text-transform:uppercase;font-weight:800;",
        "sections": {
            "urgent":            ("#ff3cac", "🔴"),
            "important":         ("#ffb347", "🟡"),
            "meetings":          ("#2b86c5", "📅"),
            "suggested_replies": ("#00e5a0", "✉️"),
            "pending_followups": ("#784ba0", "⏳"),
            "new_documents":     ("#00d4ff", "📁"),
        },
        "bullet_color":  "#ff3cac",
        "item_color":    "#9999bb",
        "count_bg":      "rgba(255,255,255,0.05)",
        "count_color":   "#555577",
        "summary_nums":  ["#ff3cac", "#00e5a0", "#784ba0"],
    },
}


# ─────────────────────────────────────────────────────────
# SECTION BUILDER
# ─────────────────────────────────────────────────────────

def build_section(key, items, theme):
    if not items:
        return ""

    t          = THEMES[theme]
    color, emoji = t["sections"][key]
    titles     = {
        "urgent":            "Urgent — Action Needed Today",
        "important":         "Important — This Week",
        "meetings":          "Today's Meetings",
        "suggested_replies": "Suggested Replies",
        "pending_followups": "Pending Follow-ups",
        "new_documents":     "New Documents",
    }
    title = titles[key]

    rows = ""
    for item in items:
        rows += f"""
        <tr>
          <td style="padding:7px 0;vertical-align:top;width:16px;">
            <span style="color:{t['bullet_color']};font-weight:900;
                         font-size:16px;line-height:1;">›</span>
          </td>
          <td style="padding:7px 0 7px 8px;font-size:14px;
                     color:{t['item_color']};line-height:1.6;">
            {item}
          </td>
        </tr>"""

    return f"""
    <div style="margin-bottom:16px;border-radius:{t['card_radius']};
                overflow:hidden;border:{t['card_border']};
                box-shadow:0 2px 12px rgba(0,0,0,0.15);">

      <div style="background:{color};padding:13px 20px;">
        <table width="100%" cellpadding="0" cellspacing="0"><tr>
          <td>
            <span style="font-size:17px;margin-right:8px;">{emoji}</span>
            <span style="{t['label_style']}color:#ffffff;">{title}</span>
          </td>
          <td style="text-align:right;">
            <span style="background:{t['count_bg']};color:#fff;
                         font-size:11px;font-weight:700;
                         padding:3px 9px;border-radius:20px;">
              {len(items)}
            </span>
          </td>
        </tr></table>
      </div>

      <div style="background:{t['card_bg']};padding:12px 20px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          {rows}
        </table>
      </div>
    </div>"""


# ─────────────────────────────────────────────────────────
# SUMMARY BAR
# ─────────────────────────────────────────────────────────

def build_summary(data, theme):
    t     = THEMES[theme]
    prof  = data.get("professional_count", 0)
    pers  = data.get("personal_count", 0)
    total = prof + pers
    c     = t["summary_nums"]

    return f"""
    <div style="margin-bottom:16px;border-radius:{t['card_radius']};
                overflow:hidden;border:{t['card_border']};
                box-shadow:0 2px 12px rgba(0,0,0,0.15);">
      <div style="background:{t['card_bg']};padding:20px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0"><tr>
          <td style="text-align:center;padding:8px 4px;
                     border-right:1px solid rgba(128,128,128,0.15);">
            <div style="font-size:34px;font-weight:800;color:{c[0]};">{total}</div>
            <div style="{t['label_style']}color:{t['count_color']};margin-top:4px;">
              Total
            </div>
          </td>
          <td style="text-align:center;padding:8px 4px;
                     border-right:1px solid rgba(128,128,128,0.15);">
            <div style="font-size:34px;font-weight:800;color:{c[1]};">{prof}</div>
            <div style="{t['label_style']}color:{t['count_color']};margin-top:4px;">
              Professional
            </div>
          </td>
          <td style="text-align:center;padding:8px 4px;">
            <div style="font-size:34px;font-weight:800;color:{c[2]};">{pers}</div>
            <div style="{t['label_style']}color:{t['count_color']};margin-top:4px;">
              Personal
            </div>
          </td>
        </tr></table>
      </div>
    </div>"""


# ─────────────────────────────────────────────────────────
# FULL HTML EMAIL
# ─────────────────────────────────────────────────────────

def build_html(data, theme):
    t         = THEMES[theme]
    today     = datetime.now().strftime("%A, %d %B %Y")
    day_num   = datetime.now().strftime("%d")
    day_short = datetime.now().strftime("%a").upper()
    month     = datetime.now().strftime("%b").upper()

    body = ""
    for key in ["urgent","important","meetings",
                "suggested_replies","pending_followups","new_documents"]:
        body += build_section(key, data.get(key, []), theme)
    body += build_summary(data, theme)

    # Theme badge for header
    theme_badge = f"""
    <div style="display:inline-block;background:{t['badge_bg']};
                 color:{t['badge_text']};font-size:10px;font-weight:700;
                 letter-spacing:1.5px;text-transform:uppercase;
                 padding:4px 10px;border-radius:20px;margin-bottom:12px;">
      {t['name']} Theme
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Daily Briefing — {today}</title>
</head>
<body style="margin:0;padding:0;background:{t['bg']};
             font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Helvetica,Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0"
       style="background:{t['bg']};padding:24px 0;">
<tr><td align="center">
<table width="660" cellpadding="0" cellspacing="0"
       style="max-width:660px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="background:{t['header_bg']};
               border-radius:16px 16px 0 0;padding:36px 36px 28px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="vertical-align:top;">
          {theme_badge}
          <p style="margin:0 0 6px;{t['label_style']}
                     color:{t['header_sub']};">
            Successive Digital · Kagen AI
          </p>
          <h1 style="margin:0 0 8px;color:{t['header_text']};
                      font-size:26px;font-weight:800;line-height:1.2;">
            🌅 Good Morning, Siddharth
          </h1>
          <p style="margin:0;color:{t['header_sub']};font-size:13px;">
            {today}
          </p>
        </td>
        <!-- Calendar badge -->
        <td style="text-align:right;vertical-align:top;">
          <div style="display:inline-block;
                       background:rgba(255,255,255,0.07);
                       border:1px solid rgba(255,255,255,0.1);
                       border-radius:14px;padding:12px 18px;
                       text-align:center;min-width:56px;">
            <div style="color:{t['header_sub']};font-size:9px;
                         letter-spacing:2px;text-transform:uppercase;">
              {month}
            </div>
            <div style="color:{t['header_text']};font-size:30px;
                         font-weight:800;line-height:1.1;">
              {day_num}
            </div>
            <div style="color:{t['header_sub']};font-size:9px;
                         letter-spacing:2px;">
              {day_short}
            </div>
          </div>
        </td>
      </tr></table>
    </td>
  </tr>

  <!-- COLOUR DIVIDER -->
  <tr>
    <td style="background:{t['divider']};height:3px;"></td>
  </tr>

  <!-- BODY -->
  <tr>
    <td style="background:{t['bg']};padding:20px 16px;">
      {body}
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:{t['footer_bg']};
               border-radius:0 0 16px 16px;
               padding:20px 36px;text-align:center;
               border-top:1px solid rgba(128,128,128,0.08);">
      <p style="margin:0;color:{t['footer_text']};
                 font-size:11px;line-height:1.8;">
        Generated by <strong>Kagen AI</strong>
        &nbsp;·&nbsp; Successive Digital
        &nbsp;·&nbsp; {today}
        &nbsp;·&nbsp; Theme: {t['name']}
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>"""


# ─────────────────────────────────────────────────────────
# PLAIN TEXT FALLBACK
# ─────────────────────────────────────────────────────────

def build_plain(data):
    today  = datetime.now().strftime("%A, %d %B %Y")
    lines  = [f"Daily Briefing — {today}\n"]
    labels = {
        "urgent":            "URGENT",
        "important":         "IMPORTANT",
        "meetings":          "TODAY'S MEETINGS",
        "suggested_replies": "SUGGESTED REPLIES",
        "pending_followups": "PENDING FOLLOW-UPS",
        "new_documents":     "NEW DOCUMENTS",
    }
    for key, label in labels.items():
        items = data.get(key, [])
        if items:
            lines.append(f"\n{label}:")
            lines += [f"  • {i}" for i in items]
    lines.append(
        f"\nProfessional: {data.get('professional_count',0)} | "
        f"Personal: {data.get('personal_count',0)}"
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# GITHUB ARCHIVER  (commits HTML to repo if GH_KEY is set)
# ─────────────────────────────────────────────────────────

def push_to_github(filename, html_body):
    if not GH_KEY:
        print("⚠️  GH_KEY not set — skipping GitHub archive")
        return

    import base64
    encoded = base64.b64encode(html_body.encode("utf-8")).decode("utf-8")
    path    = filename  # stored at repo root

    # Check if file already exists (need its SHA to update)
    check_url = f"https://api.github.com/repos/{GH_REPO}/contents/{path}"
    check_req = urllib.request.Request(
        check_url,
        headers={"Authorization": f"Bearer {GH_KEY}", "Accept": "application/vnd.github+json"},
    )
    sha = None
    try:
        with urllib.request.urlopen(check_req, timeout=15) as r:
            sha = json.loads(r.read().decode("utf-8")).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"⚠️  GitHub check failed ({e.code}) — skipping archive")
            return

    body = {"message": f"briefing: add {filename}", "content": encoded}
    if sha:
        body["sha"] = sha

    put_req = urllib.request.Request(
        check_url,
        data    = json.dumps(body).encode("utf-8"),
        headers = {
            "Authorization": f"Bearer {GH_KEY}",
            "Accept":        "application/vnd.github+json",
            "Content-Type":  "application/json",
        },
        method  = "PUT",
    )
    try:
        with urllib.request.urlopen(put_req, timeout=15) as r:
            result = json.loads(r.read().decode("utf-8"))
        print(f"📦 Archived to GitHub → {GH_REPO}/{path}")
    except urllib.error.HTTPError as e:
        print(f"⚠️  GitHub archive failed ({e.code}): {e.read().decode('utf-8')}")


# ─────────────────────────────────────────────────────────
# HTML SAVER  (always runs so briefing is never lost)
# ─────────────────────────────────────────────────────────

def save_html(html_body, theme):
    date_slug = datetime.now().strftime("%Y-%m-%d")
    filename  = f"briefing_{date_slug}_{theme}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_body)
    print(f"💾 HTML saved → {filename}")
    return filename


# ─────────────────────────────────────────────────────────
# SEND  (via Brevo API — works in any cloud/sandbox)
# ─────────────────────────────────────────────────────────

def send(data, theme):
    today   = datetime.now().strftime("%A, %d %B %Y")
    subject = f"🌅 Daily Briefing — {today} · {THEMES[theme]['name']} Edition"

    html_body  = build_html(data, theme)
    plain_body = build_plain(data)

    # Always save HTML locally first so briefing is never lost
    saved_file = save_html(html_body, theme)
    push_to_github(saved_file, html_body)

    payload = json.dumps({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": RECIPIENT_EMAIL}],
        "subject":     subject,
        "htmlContent": html_body,
        "textContent": plain_body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data    = payload,
        headers = {
            "api-key":      BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept":       "application/json",
        },
        method  = "POST",
    )

    print(f"📡 Sending via Brevo API → {RECIPIENT_EMAIL}…")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        print(f"✅ Sent via Brevo  →  {RECIPIENT_EMAIL}  [{THEMES[theme]['name']} theme]  (messageId: {result.get('messageId')})")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"❌ Brevo API error {e.code}: {body}")
        raise SystemExit(1)

    return saved_file


# ─────────────────────────────────────────────────────────
# THEME RESOLUTION
# Priority: env var > JSON field > weekly rotation
# ─────────────────────────────────────────────────────────

def resolve_theme(data):
    if ENV_THEME and ENV_THEME in THEMES:
        print(f"🎨 Theme from env: {ENV_THEME}")
        return ENV_THEME
    json_theme = data.get("design_theme", "").lower()
    if json_theme and json_theme in THEMES:
        print(f"🎨 Theme from JSON: {json_theme}")
        return json_theme
    theme = get_weekly_theme()
    print(f"🎨 Theme from weekly rotation: {theme}")
    return theme


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not BREVO_API_KEY:
        print("❌ Set BREVO_API_KEY environment variable (brevo.com → Settings → API Keys)")
        sys.exit(1)
    if not SENDER_EMAIL:
        print("❌ Set SENDER_EMAIL environment variable (verify a single sender address in Brevo)")
        sys.exit(1)
    if not RECIPIENT_EMAIL:
        print("❌ Set RECIPIENT_EMAIL environment variable")
        sys.exit(1)

    if BRIEFING_JSON:
        data = json.loads(BRIEFING_JSON)
        print("✅ Loaded briefing from BRIEFING_JSON")
    else:
        print("⚠️  No BRIEFING_JSON — using sample data")
        data = {
            "design_theme": "framer",          # ← change to test each theme
            "urgent": [
                "Reply to client re: proposal — deadline today",
                "Review and sign NDA — expires today"
            ],
            "important": [
                "Prepare Q2 delivery plan for board review",
                "Follow up with BD team on 3 open RFPs"
            ],
            "meetings": [
                "10:00 AM — Weekly leadership sync",
                "11:30 AM — Kagen ADD demo with ZS Associates",
                "03:00 PM — 1:1 with Delivery Head"
            ],
            "suggested_replies": [
                "Re: Project Timeline — Confirming on track for May 15",
                "Re: Invoice #4521 — Forwarded to finance, EOD resolution"
            ],
            "pending_followups": [
                "Legal sign-off pending — ABC Corp contract (sent Apr 30)",
                "Design files awaited from client — KOL Analytics project"
            ],
            "new_documents": [
                "Q2 Delivery Plan v2.pdf — shared by Priya (Drive)",
                "ADD Architecture Deck — Strategy and Solutions (SharePoint)"
            ],
            "professional_count": 11,
            "personal_count":     3
        }

    theme = resolve_theme(data)
    send(data, theme)