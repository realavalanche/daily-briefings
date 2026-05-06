"""
briefing_sender.py
------------------
Converts a daily briefing JSON into a rich HTML email and sends it via Gmail SMTP.
Credentials are read from environment variables:
  GMAIL_ADDRESS      — sender address
  GMAIL_APP_PASSWORD — Gmail App Password (not your account password)
  RECIPIENT_EMAIL    — recipient address
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

SECTION_CONFIG = {
    "urgent": {
        "label": "Urgent",
        "emoji": "🚨",
        "color": "#FF4444",
        "bg": "#fff5f5",
        "border": "#FF4444",
    },
    "important": {
        "label": "Important",
        "emoji": "⚡",
        "color": "#FFA500",
        "bg": "#fffaf0",
        "border": "#FFA500",
    },
    "meetings": {
        "label": "Meetings",
        "emoji": "📅",
        "color": "#2196F3",
        "bg": "#f0f7ff",
        "border": "#2196F3",
    },
    "suggested_replies": {
        "label": "Suggested Replies",
        "emoji": "💬",
        "color": "#4CAF50",
        "bg": "#f0faf0",
        "border": "#4CAF50",
    },
    "pending_followups": {
        "label": "Pending Follow-ups",
        "emoji": "🔁",
        "color": "#9C27B0",
        "bg": "#faf0ff",
        "border": "#9C27B0",
    },
    "new_documents": {
        "label": "New Documents",
        "emoji": "📄",
        "color": "#009688",
        "bg": "#f0fafa",
        "border": "#009688",
    },
}

SECTION_ORDER = [
    "urgent",
    "important",
    "meetings",
    "suggested_replies",
    "pending_followups",
    "new_documents",
]


def _section_html(key: str, items: list) -> str:
    if not items:
        return ""

    cfg = SECTION_CONFIG[key]
    color = cfg["color"]
    bg = cfg["bg"]
    border = cfg["border"]
    emoji = cfg["emoji"]
    label = cfg["label"]

    bullets = "\n".join(
        f"""
        <li style="
            padding: 6px 0;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            line-height: 1.55;
            color: #2d2d2d;
        ">{item}</li>"""
        for item in items
    )

    return f"""
    <div style="
        background: {bg};
        border-left: 4px solid {border};
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    ">
      <div style="
          display: flex;
          align-items: center;
          margin-bottom: 10px;
      ">
        <span style="font-size: 20px; margin-right: 10px;">{emoji}</span>
        <span style="
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {color};
        ">{label}</span>
        <span style="
            margin-left: auto;
            background: {color};
            color: #fff;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 9px;
            border-radius: 20px;
        ">{len(items)}</span>
      </div>
      <ul style="
          margin: 0;
          padding-left: 18px;
          list-style: disc;
      ">
        {bullets}
      </ul>
    </div>"""


def _summary_bar(personal: int, professional: int) -> str:
    total = personal + professional or 1
    pro_pct = round(professional / total * 100)
    per_pct = 100 - pro_pct

    return f"""
    <div style="
        background: #fff;
        border-radius: 10px;
        padding: 18px 22px;
        margin-top: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    ">
      <div style="
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          color: #555;
          margin-bottom: 12px;
      ">📊 Inbox Summary</div>

      <div style="display: flex; gap: 24px; margin-bottom: 14px;">
        <div style="flex: 1; background: #f0f7ff; border-radius: 8px; padding: 12px 16px; text-align: center;">
          <div style="font-size: 28px; font-weight: 800; color: #2196F3;">{professional}</div>
          <div style="font-size: 12px; color: #666; margin-top: 2px;">Professional</div>
        </div>
        <div style="flex: 1; background: #fff8f0; border-radius: 8px; padding: 12px 16px; text-align: center;">
          <div style="font-size: 28px; font-weight: 800; color: #FFA500;">{personal}</div>
          <div style="font-size: 12px; color: #666; margin-top: 2px;">Personal</div>
        </div>
      </div>

      <div style="background: #eee; border-radius: 20px; height: 10px; overflow: hidden;">
        <div style="display: flex; height: 100%;">
          <div style="width: {pro_pct}%; background: linear-gradient(90deg, #2196F3, #42A5F5);"></div>
          <div style="width: {per_pct}%; background: linear-gradient(90deg, #FFA500, #FFB74D);"></div>
        </div>
      </div>
      <div style="display: flex; justify-content: space-between; margin-top: 6px;">
        <span style="font-size: 11px; color: #2196F3; font-weight: 600;">{pro_pct}% Professional</span>
        <span style="font-size: 11px; color: #FFA500; font-weight: 600;">{per_pct}% Personal</span>
      </div>
    </div>"""


def build_html(briefing: dict) -> str:
    date_str = briefing.get("date", datetime.today().strftime("%B %d, %Y"))
    personal = briefing.get("personal_count", 0)
    professional = briefing.get("professional_count", 0)

    sections_html = "".join(
        _section_html(key, briefing.get(key, []))
        for key in SECTION_ORDER
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Daily Briefing — {date_str}</title>
</head>
<body style="
    margin: 0;
    padding: 0;
    background: #f0f2f5;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
">
  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background: #f0f2f5; padding: 32px 16px;">
    <tr>
      <td align="center">

        <!-- Card -->
        <table width="100%" cellpadding="0" cellspacing="0" style="
            max-width: 640px;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0,0,0,0.10);
        ">

          <!-- ── HEADER ── -->
          <tr>
            <td style="
                background: linear-gradient(135deg, #0f1729 0%, #1a2d5a 60%, #1565C0 100%);
                padding: 36px 32px 28px;
            ">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <!-- Logo placeholder -->
                    <div style="
                        display: inline-block;
                        background: rgba(255,255,255,0.12);
                        border: 1px solid rgba(255,255,255,0.2);
                        border-radius: 8px;
                        padding: 6px 14px;
                        font-size: 13px;
                        font-weight: 700;
                        color: rgba(255,255,255,0.9);
                        letter-spacing: 0.04em;
                        margin-bottom: 20px;
                    ">⚡ SUCCESSIVE DIGITAL</div>
                    <div style="
                        font-size: 30px;
                        font-weight: 800;
                        color: #ffffff;
                        line-height: 1.2;
                        letter-spacing: -0.5px;
                    ">Good Morning ☀️</div>
                    <div style="
                        font-size: 15px;
                        color: rgba(255,255,255,0.65);
                        margin-top: 6px;
                        font-weight: 400;
                    ">{date_str}</div>
                  </td>
                  <td align="right" valign="top">
                    <div style="
                        background: rgba(255,255,255,0.1);
                        border-radius: 50%;
                        width: 64px;
                        height: 64px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 32px;
                        line-height: 64px;
                        text-align: center;
                    ">🗞️</div>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <div style="
                  margin-top: 20px;
                  height: 1px;
                  background: linear-gradient(90deg, rgba(255,255,255,0.3), transparent);
              "></div>
              <div style="
                  margin-top: 12px;
                  font-size: 13px;
                  color: rgba(255,255,255,0.5);
                  letter-spacing: 0.1em;
                  text-transform: uppercase;
              ">Your AI-powered daily briefing</div>
            </td>
          </tr>

          <!-- ── BODY ── -->
          <tr>
            <td style="padding: 28px 28px 8px;">
              {sections_html}
              {_summary_bar(personal, professional)}
            </td>
          </tr>

          <!-- ── FOOTER ── -->
          <tr>
            <td style="
                padding: 20px 28px 28px;
                text-align: center;
            ">
              <div style="
                  height: 1px;
                  background: #eee;
                  margin-bottom: 18px;
              "></div>
              <div style="
                  font-size: 12px;
                  color: #aaa;
                  line-height: 1.6;
              ">
                Generated by <strong style="color: #555;">Kagen AI</strong> &mdash; Successive Digital<br/>
                <span style="font-size: 11px;">This briefing is personalized and confidential.</span>
              </div>
            </td>
          </tr>

        </table>
        <!-- /Card -->

      </td>
    </tr>
  </table>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Plain-text fallback
# ---------------------------------------------------------------------------

def build_plain_text(briefing: dict) -> str:
    date_str = briefing.get("date", datetime.today().strftime("%B %d, %Y"))
    lines = [
        f"DAILY BRIEFING — {date_str}",
        "=" * 50,
        "Good Morning! Here is your AI-powered daily briefing.",
        "",
    ]

    for key in SECTION_ORDER:
        items = briefing.get(key, [])
        if not items:
            continue
        cfg = SECTION_CONFIG[key]
        lines.append(f"{cfg['emoji']} {cfg['label'].upper()}")
        lines.append("-" * 30)
        for item in items:
            lines.append(f"  • {item}")
        lines.append("")

    personal = briefing.get("personal_count", 0)
    professional = briefing.get("professional_count", 0)
    lines += [
        "INBOX SUMMARY",
        "-" * 30,
        f"  Professional: {professional}",
        f"  Personal:     {personal}",
        "",
        "---",
        "Generated by Kagen AI — Successive Digital",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File saver
# ---------------------------------------------------------------------------

def save_html(html: str, date_str: str) -> str:
    safe_date = date_str.replace(" ", "_").replace(",", "")
    filename = f"briefing_{safe_date}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[✓] HTML saved → {filename}")
    return filename


# ---------------------------------------------------------------------------
# Email sender
# ---------------------------------------------------------------------------

def send_email(briefing: dict) -> None:
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not all([sender, password, recipient]):
        raise EnvironmentError(
            "Missing one or more required environment variables: "
            "GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL"
        )

    date_str = briefing.get("date", datetime.today().strftime("%B %d, %Y"))
    subject = f"🌅 Daily Briefing — {date_str}"

    html_body = build_html(briefing)
    text_body = build_plain_text(briefing)

    # Save HTML locally before sending
    save_html(html_body, date_str)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Attach plain text first, HTML last (preferred by email clients)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"[→] Connecting to smtp.gmail.com:587 …")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, msg.as_string())

    print(f"[✓] Email sent to {recipient}")
    print(f"[✓] Subject: {subject}")


# ---------------------------------------------------------------------------
# Entry point / sample data
# ---------------------------------------------------------------------------

SAMPLE_BRIEFING = {
    "date": "May 6, 2025",
    "urgent": [
        "Client escalation from Acme Corp — SLA breach on ticket #4421",
        "Server CPU usage at 94% on prod-node-03 — investigate immediately",
        "Payment gateway integration failing in staging — release blocked",
    ],
    "important": [
        "Q2 roadmap deck needs final sign-off before Thursday's board call",
        "Vendor contract renewal due by EOD Friday — legal review pending",
        "New hire onboarding scheduled for 10 AM — team leads to attend",
    ],
    "meetings": [
        "09:00 AM — Daily standup with product & engineering",
        "11:30 AM — Client demo call: Nova Financial (Zoom)",
        "02:00 PM — 1:1 with Priya re: sprint velocity concerns",
        "04:30 PM — Weekly leadership sync",
    ],
    "suggested_replies": [
        "Reply to Rahul's Slack: Confirm the API spec review by Wednesday",
        "Email to Sarah (BizDev): Approve the updated proposal draft",
        "Respond to Dinesh: Yes to the AWS cost optimization workshop invite",
    ],
    "pending_followups": [
        "Design team: Final assets for the mobile app v2.1 release",
        "Finance: Reimbursement approval for March travel expenses",
        "DevOps: Kubernetes cluster upgrade status — due last Friday",
    ],
    "new_documents": [
        "Q1 Performance Report — shared by Analytics team",
        "Updated Privacy Policy v3.2 — Legal department",
        "Architecture Proposal: Event-Driven Microservices — Arjun Mehta",
        "Brand Guidelines 2025 — Design team upload",
    ],
    "personal_count": 7,
    "professional_count": 31,
}


if __name__ == "__main__":
    import sys

    # Accept optional JSON file path as argument, else use sample data
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
        with open(json_path, "r", encoding="utf-8") as f:
            briefing_data = json.load(f)
        print(f"[✓] Loaded briefing from {json_path}")
    else:
        briefing_data = SAMPLE_BRIEFING
        print("[i] No JSON file provided — using built-in sample briefing")

    # Check whether to send email or just save HTML
    if all([
        os.environ.get("GMAIL_ADDRESS"),
        os.environ.get("GMAIL_APP_PASSWORD"),
        os.environ.get("RECIPIENT_EMAIL"),
    ]):
        send_email(briefing_data)
    else:
        print("[!] Email env vars not set — skipping send, saving HTML only")
        html = build_html(briefing_data)
        date_str = briefing_data.get("date", datetime.today().strftime("%B %d, %Y"))
        save_html(html, date_str)

        # Also print plain text preview
        print("\n" + "=" * 50)
        print(build_plain_text(briefing_data))
