# sysdig-get-connected-agents

A Python script that queries the Sysdig platform for agent status and exports the results to CSV. By default it filters to only **active** agents (Up to Date or Almost Out of Date), making it easy to audit which agents are healthy across your environment.

> **⚠️ Disclaimer — Private/Undocumented Endpoint**
>
> This script uses the internal endpoint `/api/cloud/v2/dataSources/agents`, which is **not part of the official Sysdig public API**. It is not documented, not covered by any SLA, and may change or be removed without notice in future Sysdig releases. Use at your own risk and be prepared to update the script if the endpoint changes.

---

## Requirements

- Python 3.8+
- A valid Sysdig API token

## Setup

```bash
git clone https://github.com/jcotoBan/sysdig-get-connected-agents.git
cd sysdig-get-connected-agents

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Set your API token as an environment variable:

```bash
export SYSDIG_SECURE_API_TOKEN="your-token-here"
```

The host is resolved in this order:
1. `--host` flag (explicit URL — use this for on-prem)
2. `--region` flag (SaaS region shorthand)
3. `SYSDIG_SECURE_URL` environment variable
4. Default: `us4` region (`https://app.us4.sysdig.com`)

### Supported regions

| Flag | URL |
|---|---|
| `us1` | `https://us2.app.sysdig.com` |
| `us4` *(default)* | `https://app.us4.sysdig.com` |
| `eu1` | `https://eu1.app.sysdig.com` |
| `au1` | `https://app.au1.sysdig.com` |

## Usage

```bash
# Active agents only (Up to Date / Almost Out of Date) → agents.csv
python get_agents.py

# Specify a region
python get_agents.py --region eu1

# On-prem or unlisted region
python get_agents.py --host https://sysdig.your-company.com

# Custom output file
python get_agents.py --out my_report.csv

# All agents regardless of status
python get_agents.py --all

# Combine flags
python get_agents.py --region eu1 --all --out full_eu1.csv
```

## Output

The script prints a summary and table to the terminal, then writes a CSV file.

**Terminal output:**
```
Connecting to: https://app.us4.sysdig.com

Agent health: 100%
  Total:           1
  Healthy:         1
  ...

Active agents (1):

HOSTNAME               CLUSTERNAME  AGENTSTATUS  AGENTVERSION  AGENTLASTSEEN         DEPLOYMENTTYPE
---------------------  -----------  -----------  ------------  --------------------  -----------------------
localhost.localdomain  cototest     Up to Date   14.3.1        2026-05-12T16:31:36Z  host, non-containerised

CSV written to agents.csv (1 agent(s))
```

**CSV columns:**

| Column | Description |
|---|---|
| `hostname` | Host name of the agent |
| `machineId` | Machine/instance ID |
| `agentId` | Sysdig agent ID |
| `clusterName` | Kubernetes cluster name (if applicable) |
| `agentStatus` | Up to Date / Almost Out of Date / Disconnected / Never Connected |
| `connected` | Boolean — currently connected |
| `agentVersion` | Agent version string |
| `agentLastSeen` | ISO 8601 timestamp of last contact |
| `deploymentType` | e.g. `host, non-containerised` |
| `containerised` | Boolean — running as a container |
