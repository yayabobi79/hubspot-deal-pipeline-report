---
name: hubspot-deal-pipeline-report
description: Generates a HubSpot deal pipeline report for the current quarter, broken down by deal source, source detail, and stage, plus totals by deal owner, with an optional channel-performance analysis. Use when the user asks for a "deal pipeline report", "pipeline breakdown", "quarterly HubSpot deals report", "which channels bring in deals", or similar.
---

# HubSpot deal pipeline report

Runs `scripts/deal_pipeline_report.py` against the HubSpot CRM API (plain
Python standard library only -- no pip install required) and returns a
current-quarter deal breakdown by source, source detail, and stage, plus
totals by deal owner. Can also produce a channel-performance analysis
(which sources bring higher/lower-value deals, which convert better).

**Assume the person you're talking to may have never created a HubSpot
private app and doesn't know what an API token is.** Explain each step in
plain terms and do the technical parts yourself wherever this environment
allows it. Never rush them past a step.

**Platform note:** this skill's Python execution may run in one of two
modes depending on how this environment is configured:
- **Hosted/sandboxed mode** -- code runs in a managed, likely ephemeral
  container. A file saved during one conversation may not exist in the
  next one, so token setup and config below may need repeating each
  session. If a file check unexpectedly comes back empty, treat that as
  normal for this mode rather than an error.
- **Local shell mode** -- code runs on the user's own machine, in which
  case saved files persist across conversations the same way they would
  for any local tool.
If you can tell which mode you're in, say so; if not, just proceed and let
the file checks tell you.

**Network note:** this script makes outbound HTTPS calls to
`api.hubapi.com`. If those calls fail with a network/connection error
rather than a HubSpot API error, this environment's network access likely
needs to be enabled or `api.hubapi.com` allowlisted by whoever administers
it -- tell the user this plainly rather than retrying blindly.

## Step 0: Check whether a token is already available

Run (via the shell tool, don't ask the user to do this part):
```
test -n "$HUBSPOT_ACCESS_TOKEN" && echo "env-var-set"
test -s ~/HubSpotToken/token.txt && echo "file-set"
```
If either prints, skip straight to "Running the report" below.

If neither is set, walk the user through onboarding below, one step at a
time -- wait for confirmation at each step rather than dumping the whole
list at once.

## Onboarding (only if no token found)

Say, in your own words: "Before I can pull your HubSpot data, you need a
private access key from HubSpot -- a one-time setup, about 5 minutes."

**Part A -- create the HubSpot private app** (identical regardless of
platform, since this happens on HubSpot's own website):

1. "Go to https://app.hubspot.com and log into your HubSpot account."
2. "Click the gear/settings icon in the top navigation bar."
3. "In the left sidebar, scroll down and click 'Integrations', then click
   'Private Apps' underneath it."
4. "Click the 'Create a private app' button in the top right."
5. "On the 'Basic Info' tab, give it any name, like 'Deal Pipeline
   Report'."
6. "Click the 'Scopes' tab near the top."
7. "Search `deals`, find `crm.objects.deals`, and check its **Read**
   column (not Write)."
8. "Clear the search, search `owners`, find `crm.objects.owners`, and
   check its **Read** box too."
9. "Click 'Create app' in the top right, then confirm in the popup."
10. "Click 'Show token', then copy it. Keep this window open."

If the screen doesn't match (HubSpot's UI changes over time), ask the user
to describe what they see and adapt rather than guessing.

**Part B -- get the token into this environment:**

If you were able to tell you're in **local shell mode** (the user's own
machine): create the folder yourself (`mkdir -p ~/HubSpotToken`), then walk
them through saving the token as plain text at `~/HubSpotToken/token.txt`
using a text editor on their machine, the same way you would for any local
credential -- **never ask them to paste it into this chat** in that case.

If you're in **hosted/sandboxed mode**, or can't tell which mode you're
in, there is no way for the user to place a file into this container
themselves. Tell them plainly: "In this environment, I don't have a way to
receive that file from your computer -- the only path is pasting the token
here so I can save it for this session. That means it will be part of
this conversation. If you'd rather avoid that, this skill also supports
running on your own machine in local-shell mode, where you can save the
file yourself without ever sharing it in chat." Let the user decide; if
they choose to paste it, save it immediately to `~/HubSpotToken/token.txt`
and don't repeat it back or reference its contents afterward.

Verify either way (via the shell tool):
```
test -s ~/HubSpotToken/token.txt && echo "found" || echo "not found"
```

## Running the report

1. If not already specified, ask in plain language:
   - "Which deal pipeline?" -- if unsure, run
     `python3 scripts/deal_pipeline_report.py --list-pipelines` yourself
     and show the plain list of pipeline names, rather than asking the
     user to run a command.
   - "Every stage, or specific ones?" (optional -- default all)
   - "Specific deal sources, or all of them?" (optional -- default all)

2. Run:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" \
     [--stages "<comma-separated stages>"] \
     [--sources "<comma-separated sources>"]
   ```

3. Present the result as a clean, readable summary -- not raw script
   output verbatim.

4. If the script errors on a missing/wrong pipeline or stage name, it
   returns the valid options -- turn those into a plain follow-up question.

5. If it errors with a HubSpot "missing scopes" message, that means a
   scope wasn't checked in Part A step 7/8 -- name it exactly and walk the
   user back to the Private Apps Scopes tab to add it.

## Channel-performance analysis (optional)

After showing the summary, offer: "Want a deeper analysis of which
channels are performing better or worse, with recommendations?"

1. Get structured data instead of text:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" [--stages "..."] [--sources "..."] --format json
   ```
   This includes `by_source_total`, `by_source_avg`, `by_source_count`,
   and `by_source_outcome` (won/lost/open amounts per source, derived from
   HubSpot's own stage `isClosed`/`probability` metadata -- not label
   guessing, so it holds regardless of how stages are named).

2. Analyze rather than restate:
   - Rank sources by total pipeline value AND separately by average deal
     size -- a channel can have a small total but a high average.
   - Compute a win-rate-style split (won / (won + lost)) only where a
     source has enough closed deals to be meaningful; say so explicitly
     where a source is almost entirely still open instead of presenting a
     misleading ratio from a tiny sample.
   - Call out "(no source)"/"(no detail)" buckets as a data-quality
     finding worth fixing, not just another row.
   - **There is no marketing spend/cost-per-lead data in HubSpot deals.**
     Do not invent cost or ROI figures. Separate "what the data shows"
     (value and win-rate by channel) from "directional recommendations"
     (e.g. suggesting the team start tracking cost-per-channel so a future
     report can quantify actual cost efficiency). Label the cost-related
     section as directional, not data-driven.

3. Write recommendations in the voice of an experienced B2B marketing/sales
   professional -- specific and opinionated, grounded in the real numbers,
   with directional/cost claims explicitly flagged as such.

4. Present this as a clear, well-formatted chat response. If this
   environment's code tool can produce a downloadable file, you may also
   offer to write the analysis to an HTML or Markdown file the user can
   download -- but do not assume a specific mechanism for this beyond
   what's actually available; ask the user or just check what tools you
   have rather than guessing at platform-specific publishing features.

## Notes

- "This quarter" defaults to filtering on `closedate` (deals
  expected/booked to close this quarter). Use `--date-field createdate`
  only if the user specifically means deals opened this quarter.
- This package covers on-demand reporting and analysis only. It does not
  include automatic weekly delivery or Slack posting -- those would need
  this platform's own scheduling/connector mechanisms, which are out of
  scope here unless specifically requested and researched separately.
