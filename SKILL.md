---
name: hubspot-deal-pipeline-report
description: Generates a HubSpot deal pipeline report for the current quarter, broken down by deal source, source detail, and stage, plus totals by deal owner. Use when the user asks for a "deal pipeline report", "pipeline breakdown", "quarterly HubSpot deals report", or similar.
---

# HubSpot deal pipeline report

Runs `scripts/deal_pipeline_report.py` against the HubSpot CRM API and returns
a current-quarter deal breakdown by source, source detail, and stage, plus
totals by deal owner.

**Assume the person you're talking to may have never used a terminal, never
created a HubSpot private app, and doesn't know what an API token is.** Do
not use developer jargon ("set an env var", "run this command", "API scope")
without immediately explaining what it means in plain terms and doing the
non-chat parts yourself wherever possible. Never rush them past a step.

## Step 0: Check whether a token is already set up

Run (via Bash, don't ask the user to do this part):
```
test -n "$HUBSPOT_ACCESS_TOKEN" && echo "env-var-set"
test -s ~/HubSpotToken/token.txt && echo "file-set"
```
If either prints, skip straight to "Running the report" below.

If neither is set, walk the user through the onboarding below, one step at a
time -- wait for them to confirm each step is done before moving to the
next. Don't dump the whole list on them at once.

## Onboarding (only if no token found)

Say, in your own words, something like: "Before I can pull your HubSpot
data, you need to create a private access key in HubSpot -- this is a
one-time setup, takes about 5 minutes, and I'll walk you through every
click."

**Part A -- create the HubSpot private app:**

1. "Go to https://app.hubspot.com and log into your HubSpot account."
2. "Click the gear/settings icon in the top navigation bar."
3. "In the left sidebar, scroll down and click 'Integrations', then click
   'Private Apps' underneath it."
4. "Click the 'Create a private app' button in the top right."
5. "On the 'Basic Info' tab, give it any name, like 'Deal Pipeline Report'.
   This is just a label, it doesn't matter what you pick."
6. "Click the 'Scopes' tab near the top."
7. "There's a search box under 'Scopes' -- type `deals` into it, then find
   `crm.objects.deals` in the list and check the box under the **Read**
   column (not Write)."
8. "Clear the search box, type `owners`, find `crm.objects.owners`, and
   check its **Read** box too."
9. "Click 'Create app' in the top right, then confirm in the popup that
   appears."
10. "You'll now see an access token on screen, partially hidden. Click
    'Show token', then click the copy icon next to it. Keep this window
    open -- you'll need to paste it in the next part."

If the user gets a different screen than expected or a button isn't where
described (HubSpot's UI changes over time), ask them to describe what they
see rather than guessing, and adapt.

**Part B -- save the token to a file, without it ever being pasted into
this chat:**

Create the destination folder for them first (via Bash, silently):
```
mkdir -p ~/HubSpotToken
```

Then say: "Now, without pasting it here in our chat, let's save that token
to a file on your computer:
1. Open the **TextEdit** app (search for it with Spotlight -- press
   Cmd+Space, type TextEdit, hit Enter).
2. Paste the token you copied (Cmd+V) so it's the only thing in the
   document.
3. In the menu bar, click Format > 'Make Plain Text' (important -- it must
   not be saved as rich text).
4. Press Cmd+S to save. In the save dialog, name the file `token`, and in
   the location picker navigate to your Home folder, then into the
   `HubSpotToken` folder I just created, and save it there."

Then verify (via Bash, don't ask them to check):
```
test -s ~/HubSpotToken/token.txt && echo "found" || echo "not found"
```
If "not found", the filename or location is probably slightly off (e.g.
saved as `token.txt.txt`, or saved elsewhere) -- check
`ls -la ~/HubSpotToken/` and `ls ~/Desktop ~/Downloads ~/Documents 2>/dev/null | grep -i token`
for likely misplaced files, and help them fix it rather than asking them to
redo the whole thing blind. Never read the file's contents aloud to the
user or repeat the token back -- only confirm existence/non-emptiness.

## Running the report

1. If the user's request doesn't already specify them, ask in plain
   language:
   - "Which deal pipeline do you want the report on?" -- if unsure, run
     `python3 scripts/deal_pipeline_report.py --list-pipelines` yourself and
     show them the plain-English list of pipeline names to pick from,
     rather than asking them to run a command.
   - "Do you want to look at every stage, or just specific ones?" (optional
     -- default to all if they don't care)
   - "Any specific deal sources you want to focus on, or all of them?"
     (optional -- default to all)

2. Run:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" \
     [--stages "<comma-separated stages>"] \
     [--sources "<comma-separated sources>"]
   ```

3. Present the result as a clean, readable summary (headline total, then
   source/detail/stage breakdown, then owner totals) -- not the raw
   script output verbatim, and not with technical framing.

4. If the script errors on a missing/wrong pipeline or stage name, it
   returns the valid options in the error message -- translate those into a
   plain follow-up question rather than showing the raw error text.

5. If it errors with a HubSpot "missing scopes" message, that means a
   permission wasn't checked back in Part A step 7/8 -- tell the user
   exactly which one by name, and walk them back to the Private Apps
   screen to add it (same screen, Scopes tab, same search-and-check
   process).

6. After showing the chat summary, offer: "Want me to also put together a
   deeper channel-performance analysis as a shareable report, with
   recommendations?" If yes, follow "Building the channel-performance
   artifact" below. Artifacts are private by default, so building one
   doesn't need the same confirmation as posting to Slack -- but **never
   post the result to Slack from this on-demand flow without asking
   first**; that's a separate, explicit yes.

## Building the channel-performance artifact

Used by both the on-demand flow (on request) and the scheduled weekly flow
(automatically, since that's already an approved standing automation).

1. **Get structured data**, not the text report:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" [--stages "..."] [--sources "..."] --format json
   ```
   (or `--use-config --format json` in the scheduled flow). This gives
   `by_source_total`, `by_source_avg`, `by_source_count`,
   `by_source_outcome` (won/lost/open amounts per source, derived from
   HubSpot's own stage-probability metadata -- not label guessing), plus
   the existing source/detail/stage/owner breakdowns.

2. **Analyze, don't just restate the numbers:**
   - Rank sources by total pipeline value AND separately by average deal
     size -- these tell different stories (a channel can have a small
     total but a high average, meaning fewer but bigger deals).
   - Where a source has enough closed deals to be meaningful (won + lost
     > 0), compute a win-rate-style split: won / (won + lost). Don't
     compute this for sources that are almost entirely still "open" --
     say so instead of presenting a misleading ratio from a tiny sample.
   - Call out the "(no source)" / "(no detail)" buckets as a data-quality
     finding, not just another row -- untracked source data is itself an
     actionable finding (fix attribution before over-trusting the rest).
   - **On costs: there is no spend/cost-per-lead data in HubSpot deals.**
     Do not invent cost figures or ROI numbers. Clearly separate
     "what the data shows" (deal value and win-rate by channel) from
     "directional recommendations" (e.g. suggesting which channels look
     worth leaning into based on value + win-rate, and recommending the
     team start tracking a cost-per-channel property so a future report
     can actually quantify cost efficiency). Label the cost-related
     section as directional, not data-driven.

3. **Write the recommendations in the voice of an experienced B2B
   marketing/sales professional** -- specific and opinionated (e.g. "double
   down on X," "investigate why Y converts poorly despite volume"), not
   generic filler like "continue monitoring performance." Ground every
   claim in the actual numbers from step 1; flag explicitly anywhere
   you're being directional rather than data-backed.

4. **Build the artifact.** Load the `artifact-design` skill before writing
   any HTML (required before using the Artifact tool), and the `dataviz`
   skill before building any chart (e.g. a bar chart of total or average
   deal size by source). Include: headline stats, the chart, a source
   performance table (total, average, win-rate where meaningful), and the
   written analysis/recommendations section with the cost caveat visible.

5. **Reuse the same artifact URL across runs** instead of minting a new
   link every time (weekly reports should update one stable link, not
   scatter a new URL each Monday). Before publishing, call the Artifact
   tool with `action: "list"` and look for a prior one from this skill
   (e.g. titled `hubspot_deal_pipeline_analysis`); if found, publish with
   that `url` to update it in place. Otherwise publish fresh.

6. Return the artifact URL to whoever needs it -- shown in chat for
   on-demand use, included in the Slack message for the scheduled flow.

## Setting up automatic weekly delivery (Slack)

Trigger this when the user asks for the report to run "automatically",
"every week", "on a schedule", etc. It's a separate, one-time setup on top
of everything above -- don't skip straight to it if the token isn't set up
yet; do the onboarding first.

**1. Check Slack access.** Search for a Slack send-message tool (e.g. via
ToolSearch with a query like "slack send message"). If none is available,
tell the user in plain terms: "For the report to post automatically, your
Slack needs to be connected to Claude first. You (or whoever administers
this) can do that from the Claude connector settings, or via `claude mcp`
in a terminal session -- I can't do this step for you." Don't proceed to
create a schedule until Slack access is confirmed.

**2. Ask which Slack channel or person** the report should post to. Get
the exact channel name (e.g. `#sales-pipeline`) or person's name for a DM.

**3. Determine the report scope** the same way as "Running the report"
above (pipeline, stages, sources) if not already established in this
conversation.

**4. Persist that scope** so the unattended run doesn't need to ask
questions live:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" \
     [--stages "<...>"] [--sources "<...>"] --save-config
   ```

**5. Make sure the token is saved to the file, not just an env var.** A
scheduled run is a fresh, unattended process -- it will NOT inherit a
token only `export`ed in one terminal session. If the user only has the
env var set, walk them through Part B of the onboarding above (or, for a
technical user, have them run themselves, in their own terminal --
never through this chat: `mkdir -p ~/HubSpotToken && cat > ~/HubSpotToken/token.txt <<< "their-token"`).

**6. Ask what day/time** they want it to run (e.g. "Monday mornings").
Convert to a cron expression in local time, nudged a few minutes off the
exact hour (e.g. `11 8 * * 1` rather than `0 8 * * 1`) so it isn't bunched
with everyone else's on-the-hour jobs.

**7. Before creating anything, show the user exactly what will be set
up** (schedule, channel, scope) and get an explicit go-ahead -- this is a
standing automation that will post to their Slack on its own, not a
one-off action.

**8. Create the scheduled task** using the scheduled-tasks tool
(`create_scheduled_task`), with a fully self-contained prompt (the
scheduled run has no memory of this conversation) along these lines:

```
Generate this week's HubSpot deal pipeline report and post it to Slack.
This is an unattended scheduled run -- follow these steps exactly.

1. Run: python3 <absolute path to>/scripts/deal_pipeline_report.py --use-config --format json
   (reads the token from ~/HubSpotToken/token.txt, falling back to
   HUBSPOT_ACCESS_TOKEN; reads saved scope from ~/HubSpotDealReport/config.json)
2. If it fails (missing token/config, HubSpot API error, missing scopes),
   don't try to fix it -- post a short message to <channel> explaining the
   weekly report failed, with the exact error, so a human can fix setup.
   Stop here.
3. If it succeeds, follow "Building the channel-performance artifact" in
   this skill's SKILL.md: analyze the JSON output (value and average deal
   size by source, win-rate where the sample supports it, data-quality
   gaps), write recommendations in the voice of an experienced B2B
   marketing/sales professional, clearly separating data-backed
   observations from directional cost-related suggestions (no spend data
   exists), and publish/update the artifact (reuse the existing
   `hubspot_deal_pipeline_analysis` artifact URL via `action: "list"`
   rather than minting a new link).
4. Post to <channel> using the Slack send-message tool: a clean summary
   (headline deal count/total, then source > detail > stage breakdown,
   then owner totals -- not raw script output) followed by the artifact
   URL from step 3.
5. This is unattended -- don't ask clarifying questions. If the Slack
   post itself fails, note that in the completion summary. If the
   artifact step fails but the report data is fine, still post the Slack
   summary without the link rather than failing the whole run.
```

**9. Tell the user** that the very first scheduled run may pause on a
permission prompt (for Bash + the Slack tool) since nothing is
pre-approved yet, and suggest they click "Run now" from the Scheduled
section once, right after setup, so the real weekly run doesn't stall
silently waiting on an approval nobody's watching for.

## Notes

- "This quarter" defaults to filtering on `closedate` (deals expected/booked
  to close this quarter). Only switch to `--date-field createdate` if the
  user specifically means deals opened this quarter.
- The on-demand flow above and the scheduled flow are independent -- a user
  can use either, or both (e.g. ask ad hoc most of the time, with a
  standing Monday summary as well).
