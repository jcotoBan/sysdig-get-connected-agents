#!/usr/bin/env python3
"""
get_agents.py — Fetch Sysdig agent status from the data sources API.

DESCRIPTION
    Queries /api/cloud/v2/dataSources/agents and filters to agents that are
    actively connected or up to date, then writes results to a CSV file.

SETUP
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

REQUIRED ENVIRONMENT VARIABLES
    SYSDIG_SECURE_API_TOKEN    your Sysdig API token

HOST / REGION (pick one)
    --host URL      explicit base URL, e.g. https://my-onprem.example.com
    --region NAME   SaaS region shorthand (default: us4)

    Supported regions:
      us1  → https://us2.app.sysdig.com
      us4  → https://app.us4.sysdig.com   (default)
      eu1  → https://eu1.app.sysdig.com
      au1  → https://app.au1.sysdig.com

    SYSDIG_SECURE_URL env var is also accepted as a fallback when neither
    --host nor --region is provided.

USAGE
    python get_agents.py                            # active agents, us4 region → agents.csv
    python get_agents.py --region eu1               # active agents, EU region
    python get_agents.py --host https://sysdig.corp # on-prem / custom host
    python get_agents.py --out my_report.csv        # custom output file
    python get_agents.py --all                      # include disconnected/never-connected agents too
"""

import csv
import os
import sys
import argparse
import requests

ENDPOINT        = "/api/cloud/v2/dataSources/agents"
DEFAULT_CSV     = "agents.csv"
ACTIVE_STATUSES = {"Up to Date", "Almost Out of Date"}

REGIONS = {
    "us1": "https://us2.app.sysdig.com",
    "us4": "https://app.us4.sysdig.com",
    "eu1": "https://eu1.app.sysdig.com",
    "au1": "https://app.au1.sysdig.com",
}


def resolve_host(args) -> str:
    if args.host:
        return args.host.rstrip("/")
    if args.region:
        url = REGIONS.get(args.region)
        if not url:
            print(f"Error: unknown region '{args.region}'. Valid options: {', '.join(REGIONS)}", file=sys.stderr)
            sys.exit(1)
        return url
    env_url = os.environ.get("SYSDIG_SECURE_URL")
    if env_url:
        return env_url.rstrip("/")
    return REGIONS["us4"]


def fetch_agents(base_url: str, token: str) -> dict:
    url  = base_url + ENDPOINT
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def print_stats(stats: dict, healthy_pct: int) -> None:
    print(f"Agent health: {healthy_pct}%")
    print(f"  Total:           {stats.get('totalCount', 0)}")
    print(f"  Healthy:         {stats.get('healthyCount', 0)}")
    print(f"  Almost outdated: {stats.get('almostOutOfDateCount', 0)}")
    print(f"  Out of date:     {stats.get('outOfDateCount', 0)}")
    print(f"  Disconnected:    {stats.get('disconnectedCount', 0)}")
    print(f"  Never connected: {stats.get('neverConnected', 0)}")
    print()


def print_table(agents: list) -> None:
    cols = ["hostname", "clusterName", "agentStatus", "agentVersion", "agentLastSeen", "deploymentType"]
    widths = {c: len(c) for c in cols}
    rows = []
    for a in agents:
        labels = a.get("labels", {})
        row = {
            "hostname":       labels.get("hostname", ""),
            "clusterName":    a.get("clusterName", ""),
            "agentStatus":    a.get("agentStatus", ""),
            "agentVersion":   a.get("agentVersion", ""),
            "agentLastSeen":  a.get("agentLastSeen", ""),
            "deploymentType": a.get("deploymentType", ""),
        }
        for c in cols:
            widths[c] = max(widths[c], len(row[c]))
        rows.append(row)

    header = "  ".join(c.upper().ljust(widths[c]) for c in cols)
    sep    = "  ".join("-" * widths[c] for c in cols)
    print(header)
    print(sep)
    for row in rows:
        print("  ".join(row[c].ljust(widths[c]) for c in cols))


def write_csv(agents: list, path: str) -> None:
    fieldnames = ["hostname", "machineId", "agentId", "clusterName", "agentStatus",
                  "connected", "agentVersion", "agentLastSeen", "deploymentType", "containerised"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for a in agents:
            labels = a.get("labels", {})
            writer.writerow({
                "hostname":       labels.get("hostname", ""),
                "machineId":      labels.get("machineId", ""),
                "agentId":        labels.get("agentId", ""),
                "clusterName":    a.get("clusterName", ""),
                "agentStatus":    a.get("agentStatus", ""),
                "connected":      a.get("connected", False),
                "agentVersion":   a.get("agentVersion", ""),
                "agentLastSeen":  a.get("agentLastSeen", ""),
                "deploymentType": a.get("deploymentType", ""),
                "containerised":  a.get("containerised", False),
            })
    print(f"CSV written to {path} ({len(agents)} agent(s))")


def main():
    parser = argparse.ArgumentParser(
        description="Export Sysdig agent status to CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Active statuses included by default: " + ", ".join(sorted(ACTIVE_STATUSES)),
    )
    host_group = parser.add_mutually_exclusive_group()
    host_group.add_argument("--host", metavar="URL",
                            help="Full base URL (for on-prem or unlisted regions), e.g. https://sysdig.corp")
    host_group.add_argument("--region", metavar="NAME",
                            help="SaaS region shorthand: us1, us4 (default), eu1, au1")
    parser.add_argument("--all", action="store_true",
                        help="Include all agents regardless of status (default: active only)")
    parser.add_argument("--out", metavar="FILE", default=DEFAULT_CSV,
                        help=f"Output CSV file (default: {DEFAULT_CSV})")
    args = parser.parse_args()

    token = os.environ.get("SYSDIG_SECURE_API_TOKEN")
    if not token:
        print("Error: SYSDIG_SECURE_API_TOKEN must be set", file=sys.stderr)
        sys.exit(1)

    base_url = resolve_host(args)
    print(f"Connecting to: {base_url}\n")

    data   = fetch_agents(base_url, token)
    agents = data.get("details", [])

    print_stats(data.get("agentStats", {}), data.get("healthyPercent", 0))

    if not args.all:
        agents = [a for a in agents if a.get("agentStatus") in ACTIVE_STATUSES]
        print(f"Active agents ({len(agents)}):\n")
    else:
        print(f"All agents ({len(agents)}):\n")

    print_table(agents)
    print()
    write_csv(agents, args.out)


if __name__ == "__main__":
    main()
