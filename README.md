# HubSpot deal pipeline report (Claude skill)

Generates a current-quarter HubSpot deal pipeline report broken down by
deal source, source detail, and stage, plus totals by deal owner. Runs as
an on-demand Claude skill; no HubSpot MCP connector required.

## Setup

### 1. Create a HubSpot private app token

In your HubSpot account: **Settings → Integrations → Private Apps → Create
a private app.**

Under the **Scopes** tab, enable read access for at least:

- `crm.objects.deals.read`
- `crm.objects.owners.read`
- pipelines read access (covered by the deals scopes above in most
  accounts; if a `--list-pipelines` call 403s, HubSpot's error message will
  name the exact scope it wants — add that one)

Save, then copy the generated access token. **Do not share this token or
commit it anywhere** — it grants read access to your CRM data.

### 2. Give the script access to the token

Two ways, pick whichever fits:

- **Comfortable with a terminal:** export it as an environment variable —
  ```bash
  export HUBSPOT_ACCESS_TOKEN=your-token-here
  ```
  Do this in your own terminal session, not by pasting it into a chat with
  Claude.

- **Never used a terminal:** save it as a plain text file at
  `~/HubSpotToken/token.txt` (just the token, nothing else, saved as plain
  text — not a `.rtf` rich text file). If you're going through the skill in
  a Claude conversation instead of doing this manually, it'll create the
  folder and walk you through saving the file via TextEdit step by step,
  without ever asking you to paste the token into the chat.

The script checks the environment variable first, then falls back to that
file.

### 3. Install the skill

Clone or copy this folder into your Claude skills directory, e.g.:

```bash
cp -r hubspot-deal-pipeline-report ~/.claude/skills/hubspot-deal-pipeline-report
```

## Usage

Ask Claude for a "HubSpot deal pipeline report" and it'll ask which
pipeline, stages, and sources you want (or run it directly):

```bash
python3 scripts/deal_pipeline_report.py --list-pipelines
python3 scripts/deal_pipeline_report.py --pipeline "Your Pipeline Name"
```

Optional filters:

```bash
python3 scripts/deal_pipeline_report.py \
  --pipeline "Your Pipeline Name" \
  --stages "Qualified,Demo,Negotiation" \
  --sources "OFFLINE,ORGANIC_SEARCH" \
  --date-field closedate
```

`--date-field` defaults to `closedate` (deals expected to close this
quarter). Use `createdate` for deals opened this quarter instead.

## Multi-account notes

- Every HubSpot account has different pipeline/stage labels and may use
  different properties for "deal source." Run `--list-pipelines` first in
  any new account rather than assuming names carry over.
- The source breakdown reads the standard `hs_analytics_source` and
  `hs_analytics_source_data_1` properties. If your team tracks deal source
  via a custom property instead, that requires changing the
  `SOURCE_PROPERTY` / `SOURCE_DETAIL_PROPERTY` constants in the script.

## Weekly automatic delivery (Slack)

The interactive flow above requires someone to ask for the report each
time. For unattended weekly delivery instead:

1. **Save the scope once**, so the scheduled run doesn't need to ask
   questions live:
   ```bash
   python3 scripts/deal_pipeline_report.py --pipeline "Your Pipeline Name" \
     [--stages "..."] [--sources "..."] --save-config
   ```
   This writes `~/HubSpotDealReport/config.json`. A later run with
   `--use-config` replays it with no other flags needed.

2. **Use the token file, not just the env var.** A scheduled run is a
   fresh, unattended process — it does not inherit a variable you
   `export`ed in one terminal session. Make sure the token is saved at
   `~/HubSpotToken/token.txt` (see setup above) even if you're comfortable
   with a terminal.

3. **The Slack connector must be authorized** for whichever account runs
   the schedule (via Claude's connector settings, or `claude mcp` in an
   interactive session).

4. **Ask Claude to set it up** ("send this to Slack every Monday morning")
   — the skill will ask which channel, confirm the schedule with you
   before creating anything, and register a scheduled task that runs
   `deal_pipeline_report.py --use-config` and posts the formatted result to
   Slack. The first run may pause on a one-time permission prompt (for
   Bash + the Slack tool) — running it once manually via "Run now" in the
   Scheduled section avoids that stalling the real first scheduled fire.
