# HubSpot weekly deal pipeline report

Generates a current-quarter HubSpot deal pipeline report broken down by
deal source, source detail, and stage, plus totals by deal owner, with a
channel-performance analysis (which sources bring higher-value deals,
which convert better, directional recommendations).

Available for two platforms:

- **Claude** (this root folder) -- full feature set: on-demand reporting,
  the analysis artifact, and weekly automated Slack delivery via a
  scheduled task.
- **ChatGPT** ([`chatgpt-skill/`](chatgpt-skill/)) -- on-demand reporting
  and the analysis only, packaged as `hubspot-deal-pipeline-report.zip`
  per [ChatGPT's Skills format](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
  Doesn't include Slack/scheduling -- see that folder's README for why and
  for platform-specific caveats (token persistence, network access).

Both use the exact same underlying script
(`scripts/deal_pipeline_report.py`), which is plain Python standard
library with no platform-specific dependencies.

## Setup (Claude)

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
- Win/lost/open classification uses HubSpot's own stage metadata
  (`isClosed` + `probability`), not label text-matching, so it works
  regardless of what your stages happen to be named.

## Channel-performance analysis artifact

Add `--format json` to get structured data (`by_source_total`,
`by_source_avg`, `by_source_count`, `by_source_outcome` with won/lost/open
amounts per source) instead of the human-readable text report:

```bash
python3 scripts/deal_pipeline_report.py --pipeline "Your Pipeline Name" --format json
```

Ask Claude for "a deeper channel analysis" or "a report on what's working"
and it'll turn this into a shareable artifact: which sources bring
higher-value deals vs. lower, which convert better where the sample is
large enough to mean anything, data-quality gaps (e.g. untracked source),
and recommendations written from a B2B marketing/sales perspective.

**Important limitation:** HubSpot deal records don't include marketing
spend or cost-per-lead. Any "reduce costs" guidance is necessarily
directional (e.g., "start tracking cost per channel") rather than backed
by real cost numbers — the skill labels these separately from the
data-grounded value/win-rate findings rather than inventing ROI figures.

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
   `deal_pipeline_report.py --use-config`, builds the channel-performance
   artifact, and posts both the formatted summary and the artifact link to
   Slack. The first run may pause on a one-time permission prompt (for
   Bash, the Slack tool, and the Artifact tool) — running it once manually
   via "Run now" in the Scheduled section avoids that stalling the real
   first scheduled fire.
5. **The artifact link stays stable across weeks** — each run updates the
   same published page rather than posting a new URL every Monday.
