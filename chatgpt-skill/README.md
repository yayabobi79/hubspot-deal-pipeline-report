# ChatGPT version

A ChatGPT Skills-compatible package of the same HubSpot deal pipeline
report, for users on ChatGPT instead of Claude.

**Scope note:** this package covers on-demand reporting and the
channel-performance analysis only. It does not include the weekly
Slack-automation feature from the Claude version -- that relies on
Claude-specific tools (a persistent scheduled-task system and the
Artifact publishing tool) that don't have a confirmed ChatGPT equivalent.
If you want scheduled/Slack delivery on ChatGPT, that would need separate
research into ChatGPT's own Tasks feature and whatever Slack integration
is available there.

**Platform caveats, read before relying on this:**

- **Token persistence is not guaranteed.** ChatGPT skills can run in a
  hosted, sandboxed container that may be ephemeral per conversation, or
  in a local-shell mode on your own machine (persistent, same as the
  Claude version). If you're on hosted mode, you may need to re-provide
  the token each session -- see `hubspot-deal-pipeline-report/SKILL.md`
  for how the skill handles both cases.
- **Network access may need enabling.** The script calls
  `api.hubapi.com` directly. If your ChatGPT workspace restricts outbound
  network access for skills, this needs to be enabled (and the domain
  allowlisted, if your workspace enforces an allowlist) or the script
  will fail to reach HubSpot.
- **Hosted mode may mean pasting your token into the chat.** Unlike the
  Claude version (which never asks for the raw token in conversation),
  a hosted ChatGPT container has no other way to receive a file from your
  computer. Use local-shell mode instead if you want to avoid this.

## Install

1. Download `hubspot-deal-pipeline-report.zip` from this folder.
2. In ChatGPT: Settings → (skills/code execution section, exact location
   may vary as this feature evolves) → upload the zip.
3. Ask ChatGPT for a "HubSpot deal pipeline report" to trigger it.

## Contents

```
hubspot-deal-pipeline-report/
├── SKILL.md           -- ChatGPT-flavored instructions (adapted from the Claude version)
├── requirements.txt    -- none; stdlib only
└── scripts/deal_pipeline_report.py  -- identical script used by the Claude version
```

The underlying script is unchanged from the Claude version (`../scripts/
deal_pipeline_report.py`) -- it's a plain Python CLI with no
Claude-specific or ChatGPT-specific dependencies, so it runs the same way
under either platform's Python execution.
