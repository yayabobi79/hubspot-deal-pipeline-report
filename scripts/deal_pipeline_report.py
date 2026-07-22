#!/usr/bin/env python3
"""
HubSpot deal pipeline report: current-quarter deals broken down by
source x stage, and by owner.

Auth: reads a HubSpot private app access token, checked in this order:
  1. The HUBSPOT_ACCESS_TOKEN environment variable (technical users/CI).
  2. A plain text file at ~/HubSpotToken/token.txt (non-technical users --
     saved via TextEdit or similar, never typed into a terminal or chat).
Never hardcode a token here.

Usage:
    python3 deal_pipeline_report.py --pipeline "Sales Pipeline" \
        --stages "Qualified,Demo,Negotiation" \
        --sources "Organic search,Referral" \
        --date-field closedate

    --stages and --sources are optional; omit to include all stages / all
    sources found in the pipeline.
    --date-field selects which date determines "this quarter": `closedate`
    (deals expected/booked to close this quarter -- the usual meaning of a
    "pipeline for the quarter") or `createdate` (deals opened this quarter).
    Defaults to closedate.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HUBSPOT_API_BASE = "https://api.hubapi.com"
SOURCE_PROPERTY = "hs_analytics_source"
SOURCE_DETAIL_PROPERTY = "hs_analytics_source_data_1"
DEFAULT_TOKEN_FILE = os.path.expanduser("~/HubSpotToken/token.txt")
DEFAULT_CONFIG_FILE = os.path.expanduser("~/HubSpotDealReport/config.json")


def resolve_token(token_env, token_file):
    token = os.environ.get(token_env)
    if token and token.strip():
        return token.strip()
    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            return token
    raise SystemExit(
        f"No HubSpot token found. Set the {token_env} environment variable, "
        f"or save your token as plain text in {token_file}."
    )


def api_request(token, method, path, params=None, body=None):
    url = f"{HUBSPOT_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"HubSpot API error {e.code} on {method} {path}: {detail}"
        )


def fetch_pipelines(token):
    data = api_request(token, "GET", "/crm/v3/pipelines/deals")
    return data.get("results", [])


def resolve_pipeline(pipelines, query):
    query_norm = query.strip().lower()
    for p in pipelines:
        if p["id"] == query or p["label"].strip().lower() == query_norm:
            return p
    available = ", ".join(f'"{p["label"]}" ({p["id"]})' for p in pipelines)
    raise SystemExit(
        f'Pipeline "{query}" not found. Available pipelines: {available}'
    )


def resolve_stages(pipeline, stage_queries):
    all_stages = pipeline["stages"]
    if not stage_queries:
        return all_stages
    resolved = []
    for q in stage_queries:
        q_norm = q.strip().lower()
        match = next(
            (s for s in all_stages if s["id"] == q or s["label"].strip().lower() == q_norm),
            None,
        )
        if not match:
            available = ", ".join(f'"{s["label"]}" ({s["id"]})' for s in all_stages)
            raise SystemExit(
                f'Stage "{q}" not found in pipeline "{pipeline["label"]}". '
                f"Available stages: {available}"
            )
        resolved.append(match)
    return resolved


def current_quarter_range(today=None):
    today = today or datetime.date.today()
    quarter = (today.month - 1) // 3
    start_month = quarter * 3 + 1
    start = datetime.date(today.year, start_month, 1)
    if start_month + 3 > 12:
        end = datetime.date(today.year + 1, (start_month + 3) % 12, 1)
    else:
        end = datetime.date(today.year, start_month + 3, 1)
    return start, end


def to_millis(d):
    dt = datetime.datetime.combine(d, datetime.time.min, tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_deals(token, pipeline_id, stage_ids, date_field, start, end):
    filters = [
        {"propertyName": "pipeline", "operator": "EQ", "value": pipeline_id},
        {"propertyName": date_field, "operator": "GTE", "value": str(to_millis(start))},
        {"propertyName": date_field, "operator": "LT", "value": str(to_millis(end))},
    ]
    if stage_ids:
        filters.append({"propertyName": "dealstage", "operator": "IN", "values": stage_ids})

    properties = [
        "amount",
        "dealstage",
        "dealname",
        "hubspot_owner_id",
        SOURCE_PROPERTY,
        SOURCE_DETAIL_PROPERTY,
        date_field,
    ]
    deals = []
    after = None
    while True:
        body = {
            "filterGroups": [{"filters": filters}],
            "properties": properties,
            "limit": 100,
        }
        if after:
            body["after"] = after
        page = api_request(token, "POST", "/crm/v3/objects/deals/search", body=body)
        deals.extend(page.get("results", []))
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return deals


def fetch_owners(token):
    owners = {}
    after = None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        page = api_request(token, "GET", "/crm/v3/owners", params=params)
        for o in page.get("results", []):
            name = f'{o.get("firstName", "")} {o.get("lastName", "")}'.strip() or o.get("email", o["id"])
            owners[o["id"]] = name
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return owners


def build_report(deals, owners, stage_labels_by_id, source_filter):
    source_filter_norm = {s.strip().lower() for s in source_filter} if source_filter else None

    by_source_detail_stage = {}
    by_source_detail_total = {}
    by_source_total = {}
    by_owner_total = {}
    grand_total = 0.0

    for deal in deals:
        props = deal.get("properties", {})
        amount = float(props.get("amount") or 0)
        source = props.get(SOURCE_PROPERTY) or "(no source)"
        source_detail = props.get(SOURCE_DETAIL_PROPERTY) or "(no detail)"
        stage_id = props.get("dealstage")
        stage_label = stage_labels_by_id.get(stage_id, stage_id or "(no stage)")
        owner_id = props.get("hubspot_owner_id")
        owner_name = owners.get(owner_id, "(unassigned)") if owner_id else "(unassigned)"

        if source_filter_norm is not None and source.strip().lower() not in source_filter_norm:
            continue

        by_source_detail_stage.setdefault(source, {}).setdefault(source_detail, {}).setdefault(stage_label, 0.0)
        by_source_detail_stage[source][source_detail][stage_label] += amount
        by_source_detail_total.setdefault(source, {}).setdefault(source_detail, 0.0)
        by_source_detail_total[source][source_detail] += amount
        by_source_total[source] = by_source_total.get(source, 0.0) + amount
        by_owner_total[owner_name] = by_owner_total.get(owner_name, 0.0) + amount
        grand_total += amount

    return {
        "by_source_detail_stage": by_source_detail_stage,
        "by_source_detail_total": by_source_detail_total,
        "by_source_total": by_source_total,
        "by_owner_total": by_owner_total,
        "grand_total": grand_total,
        "deal_count": sum(1 for d in deals if _passes_source_filter(d, source_filter_norm)),
    }


def _passes_source_filter(deal, source_filter_norm):
    if source_filter_norm is None:
        return True
    source = (deal.get("properties", {}).get(SOURCE_PROPERTY) or "(no source)").strip().lower()
    return source in source_filter_norm


def format_report(report, pipeline_label, start, end, date_field):
    lines = []
    lines.append(f"# Deal pipeline report: {pipeline_label}")
    lines.append(f"Quarter window ({date_field}): {start.isoformat()} to {end.isoformat()}")
    lines.append(f"Deals matched: {report['deal_count']}  |  Total amount: {report['grand_total']:,.2f}")
    lines.append("")
    lines.append("## By source > source detail > stage")
    for source, details in sorted(
        report["by_source_detail_stage"].items(), key=lambda kv: -report["by_source_total"][kv[0]]
    ):
        total = report["by_source_total"][source]
        lines.append(f"- {source}: {total:,.2f}")
        for detail, stages in sorted(
            details.items(), key=lambda kv: -report["by_source_detail_total"][source][kv[0]]
        ):
            detail_total = report["by_source_detail_total"][source][detail]
            lines.append(f"    - {detail}: {detail_total:,.2f}")
            for stage_label, amount in sorted(stages.items(), key=lambda kv: -kv[1]):
                lines.append(f"        - {stage_label}: {amount:,.2f}")
    lines.append("")
    lines.append("## By owner")
    for owner, amount in sorted(report["by_owner_total"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- {owner}: {amount:,.2f}")
    return "\n".join(lines)


def print_pipelines(pipelines):
    for p in pipelines:
        print(f'{p["label"]}  (id: {p["id"]})')
        for s in p["stages"]:
            print(f'    - {s["label"]}  (id: {s["id"]})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", help="Pipeline label or id")
    parser.add_argument("--stages", default="", help="Comma-separated stage labels/ids; omit for all")
    parser.add_argument("--sources", default="", help="Comma-separated source values to include; omit for all")
    parser.add_argument("--date-field", default="closedate", choices=["closedate", "createdate"])
    parser.add_argument("--token-env", default="HUBSPOT_ACCESS_TOKEN")
    parser.add_argument(
        "--token-file",
        default=DEFAULT_TOKEN_FILE,
        help=f"Plain text file to read the token from if the env var isn't set (default: {DEFAULT_TOKEN_FILE})",
    )
    parser.add_argument(
        "--list-pipelines",
        action="store_true",
        help="Print available pipelines and stages (with their exact labels/ids) and exit.",
    )
    parser.add_argument(
        "--start-date",
        help="Override window start (YYYY-MM-DD). Debugging aid to test wider ranges than the current quarter.",
    )
    parser.add_argument(
        "--end-date",
        help="Override window end, exclusive (YYYY-MM-DD). Use with --start-date.",
    )
    parser.add_argument(
        "--config-file",
        default=DEFAULT_CONFIG_FILE,
        help=f"Where saved pipeline/stages/sources config is read from or written to (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save the given --pipeline/--stages/--sources/--date-field to --config-file for later unattended (e.g. scheduled) runs.",
    )
    parser.add_argument(
        "--use-config",
        action="store_true",
        help="Load pipeline/stages/sources/date-field from --config-file instead of the --pipeline/--stages/--sources/--date-field flags. For unattended runs.",
    )
    args = parser.parse_args()

    token = resolve_token(args.token_env, args.token_file)

    if args.list_pipelines:
        print_pipelines(fetch_pipelines(token))
        return

    if args.use_config:
        if not os.path.exists(args.config_file):
            raise SystemExit(
                f"No saved config at {args.config_file}. Run once with --pipeline ... --save-config first."
            )
        with open(args.config_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        pipeline_query = cfg.get("pipeline")
        stages_raw = cfg.get("stages", "")
        sources_raw = cfg.get("sources", "")
        date_field = cfg.get("date_field", "closedate")
        if not pipeline_query:
            raise SystemExit(f"Config at {args.config_file} is missing a pipeline value.")
    else:
        if not args.pipeline:
            raise SystemExit("--pipeline is required (or use --list-pipelines / --use-config).")
        pipeline_query = args.pipeline
        stages_raw = args.stages
        sources_raw = args.sources
        date_field = args.date_field

    pipelines = fetch_pipelines(token)
    pipeline = resolve_pipeline(pipelines, pipeline_query)
    stage_queries = [s for s in stages_raw.split(",") if s.strip()]
    stages = resolve_stages(pipeline, stage_queries)
    stage_ids = [s["id"] for s in stages]
    stage_labels_by_id = {s["id"]: s["label"] for s in pipeline["stages"]}

    source_filter = [s for s in sources_raw.split(",") if s.strip()]

    if args.save_config:
        os.makedirs(os.path.dirname(args.config_file), exist_ok=True)
        with open(args.config_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "pipeline": pipeline_query,
                    "stages": stages_raw,
                    "sources": sources_raw,
                    "date_field": date_field,
                },
                f,
                indent=2,
            )
        print(f"Saved config to {args.config_file}", file=sys.stderr)

    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            raise SystemExit("Pass both --start-date and --end-date, or neither.")
        start = datetime.date.fromisoformat(args.start_date)
        end = datetime.date.fromisoformat(args.end_date)
    else:
        start, end = current_quarter_range()
    deals = fetch_deals(token, pipeline["id"], stage_ids, date_field, start, end)
    owners = fetch_owners(token)

    report = build_report(deals, owners, stage_labels_by_id, source_filter)
    print(format_report(report, pipeline["label"], start, end, date_field))


if __name__ == "__main__":
    main()
