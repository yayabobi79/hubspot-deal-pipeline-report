---
name: hubspot-deal-pipeline-report
description: Generates a HubSpot deal pipeline report for the current quarter, broken down by deal source, source detail, and stage, plus totals by deal owner. Use when the user asks for a "deal pipeline report", "pipeline breakdown", "quarterly HubSpot deals report", or similar.
---

# HubSpot deal pipeline report

Generates a current-quarter deal breakdown by source, source detail, and
stage, plus totals by deal owner, and an optional channel-performance
analysis. Supports two ways of reaching HubSpot data -- **Option A**: a
bundled private-app script (`scripts/deal_pipeline_report.py`), portable
and works even without any pre-existing HubSpot connection; **Option B**:
the HubSpot MCP connector, if the user's account already has (or can get)
that connected, trading some accuracy and portability for simpler setup.
See Step 0 for how to determine which applies and how to present the
choice.

**Assume the person you're talking to may have never used a terminal, never
created a HubSpot private app, and doesn't know what an API token is.** Do
not use developer jargon ("set an env var", "run this command", "API scope")
without immediately explaining what it means in plain terms and doing the
non-chat parts yourself wherever possible. Never rush them past a step.

## Step 0: Which data source is already set up?

This skill can get HubSpot data two ways. Check both before asking the
user anything:

**Check A -- private app token** (via Bash, don't ask the user to do this
part):
```
test -n "$HUBSPOT_ACCESS_TOKEN" && echo "env-var-set"
test -s ~/HubSpotToken/token.txt && echo "file-set"
```

**Check B -- HubSpot connector already authorized.** Search for it (e.g.
ToolSearch with a query like "hubspot crm search deals" or "hubspot query
crm data") -- describe it by capability, not by a hardcoded tool-group ID,
since the exact identifier varies by connection. If real tool schemas
come back (not just "no matches"), the connector is authorized in this
account already.

**Then:**
- If Check A found something → use **Option A** (private app script)
  below; skip to "Running the report (Option A)".
- If only Check B is authorized and Check A found nothing → use
  **Option B** (connector) below; skip to "Running the report
  (Option B)".
- If **neither** is set up, present the choice before doing anything
  else -- don't default silently, and don't walk the user through one
  path's setup without telling them the other exists. Say something like:

  > "There are two ways I can connect to your HubSpot data. Quick
  > tradeoffs:
  >
  > **Option A -- private app + token.** You create a private app in
  > HubSpot and give me its access token (about 5 minutes). Pros: works
  > for anyone regardless of what's already connected to this account;
  > gives the most accurate win/loss numbers (reads HubSpot's own
  > stage-probability data); also works if you ever use the ChatGPT
  > version of this skill. Cons: a few manual setup steps up front.
  >
  > **Option B -- HubSpot connector.** If your Claude account already has
  > (or can have) HubSpot connected, I can use that instead -- no token to
  > create. Pros: little to no setup if it's already connected; standard
  > one-click OAuth if not. Cons: only works here in Claude, not on
  > ChatGPT; and I can't automatically tell which stages count as "won" vs
  > "lost" this way, so you'd tell me once during setup instead of it
  > being detected automatically.
  >
  > Which would you prefer?"

  If they're unsure, default to recommending Option A for anyone who
  might also use this on ChatGPT, or Option B if they mention HubSpot is
  already connected to Claude for other things.

If neither is available and the user picks Option B, first tell them
"your Claude account needs HubSpot connected first -- that's done via
Claude's connector settings, or `claude mcp`/`/mcp` in an interactive
session; I can't do that step for you," then wait until Check B passes
before continuing.

Walk through whichever option's onboarding one step at a time -- wait for
confirmation at each step, don't dump the whole list at once.

## Option A: Private app + token setup

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

## Option B: HubSpot connector setup

Only relevant if the user chose this in Step 0. No private app, no token
-- but there's one manual step this path can't avoid: HubSpot's connector
tools have no equivalent of the private-app path's stage-metadata lookup,
so which stages count as "won" vs "lost" has to come from the user
instead of being detected automatically.

1. Confirm the connector is authorized (Step 0, Check B). If not, tell the
   user to connect it via Claude's connector settings or `claude mcp` /
   `/mcp`, and wait.

2. Ask which pipeline they want (list pipelines via a CRM search/query
   call if you need to show options -- e.g. a `dealstage`/`pipeline`
   property lookup -- rather than guessing names).

3. Ask which stage(s) in that pipeline represent "Closed Won" and which
   represent "Closed Lost" (there may be more than one of each, or none
   yet if the pipeline is new). Save this alongside the rest of the scope
   in `~/HubSpotDealReport/config.json` under a `stage_outcomes` map, e.g.
   `{"Closed Won": "won", "Closed Lost": "lost"}` -- everything else
   defaults to "open". Tell the user this mapping won't update itself if
   they rename or add stages later, so it's worth confirming again after
   any pipeline changes.

## Running the report (Option A: private app script)

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

## Running the report (Option B: connector)

No script here -- gather the same shape of data directly via the
connector's CRM tools, then reason over it yourself (or use its SQL-like
query tool's own GROUP BY/SUM/AVG where that's easier than pulling raw
records).

1. Ask the same three questions as Option A (pipeline, stages, sources) if
   not already established.

2. Pull matching deals for the current quarter (`closedate` between the
   quarter's start/end, unless the user means `createdate`), scoped to the
   chosen pipeline/stages, with properties: `amount`, `dealstage`,
   `hubspot_owner_id`, `hs_analytics_source`, `hs_analytics_source_data_1`.
   Look up owner names via the owners-search tool rather than guessing
   from IDs.

3. Assemble the same summary shape "Building the channel-performance
   artifact" below expects: total and average amount per source, deal
   counts, and a won/lost/open split per source -- using the
   `stage_outcomes` mapping saved during setup (not stage-name guessing on
   the fly) to classify each deal's stage.

4. Present and offer the deeper analysis exactly as in Option A steps
   3-6.

5. **Caveat to keep in mind, not necessarily to say aloud every time:**
   this path hasn't been validated against real data the way the script
   was -- if numbers look off, check the `stage_outcomes` mapping and the
   property names first before assuming the connector itself is wrong.

## Building the channel-performance artifact

Used by both the on-demand flow (on request) and the scheduled weekly flow
(automatically, since that's already an approved standing automation), and
by either data-source option -- the rest of this section works the same
regardless of whether the numbers came from the script (Option A) or the
connector (Option B), as long as you have the same summary shape.

1. **Get structured data**, not the text report. Option A:
   ```
   python3 scripts/deal_pipeline_report.py --pipeline "<pipeline>" [--stages "..."] [--sources "..."] --format json
   ```
   (or `--use-config --format json` in the scheduled flow). Option B:
   assemble the equivalent shape yourself per "Running the report (Option
   B)" above. Either way you end up with `by_source_total`,
   `by_source_avg`, `by_source_count`, `by_source_outcome` (won/lost/open
   amounts per source -- from stage-probability metadata in Option A, from
   the user-provided `stage_outcomes` mapping in Option B), plus the
   source/detail/stage/owner breakdowns.

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
of everything above -- don't skip straight to it if a data source isn't
set up yet; do the Step 0 onboarding first.

**Prefer Option A (the private app script) for anything scheduled.** It's
the path that's actually been run end-to-end as a live scheduled task and
confirmed working. Option B (connector) is untested for unattended runs --
scheduled tasks execute as a fresh session, and whether the connector's
authorization and the saved `stage_outcomes` mapping are both reliably
available in that context hasn't been verified. If the user is on Option
B and wants scheduling, say so explicitly and suggest either switching to
Option A for the scheduled report specifically, or proceeding with the
understanding that the first scheduled run is the real test of whether it
works at all.

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
