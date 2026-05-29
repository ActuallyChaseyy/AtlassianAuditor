# AtlassianAuditor

A Python tool that audits Atlassian organisation access and generates an HTML report with actionable security findings across Groups, Users, and Jira projects.

## What it does

AtlassianAuditor connects to the Atlassian Admin API and Jira REST API to collect data about your organisation, then runs a series of checks and produces a self-contained HTML report. Findings are categorised by severity (warning / info) and grouped by area (Groups, Users, Jira).

**Checks run:**

Checks are split across two files. Plug-and-play checks work out of the box and can be toggled on or off. Configured checks require org-specific values to be set before they are meaningful.

*Plug-and-play (`checks.py`)*

| Category | Check |
|----------|-------|
| Groups | Empty groups |
| Groups | Groups where all members are inactive |
| Groups | Groups not assigned to any Jira project |
| Groups | Groups with no description |
| Groups | Identical group names across multiple tenants |
| Users | Inactive users still assigned to groups |
| Users | Managed users not in any group |
| Users | Duplicate managed accounts sharing an email address |
| Users | Users with admin roles across 3+ Jira projects |
| Users | Managed users with direct (non-group) Jira project access |
| Jira | Projects with multiple directly-assigned users |
| Jira | Projects with an empty group assigned |
| Jira | Projects with no lead assigned |
| Jira | Projects with no group-based access |

*Configured (`checks_configured.py`)*

| Category | Check | Config |
|----------|-------|--------|
| Groups | Groups above a member threshold assigned to a Jira project | `LARGE_GROUPS_ON_JIRA_THRESHOLD` (default: 50) |
| Jira | Jira projects missing a required group | `REQUIRED_GROUP_NAME` |

## Output

Running the tool produces a self-contained `report.html` file. 

The report has five tabs:

| Tab | Contents |
|-----|----------|
| **Summary** | At-a-glance counts for groups, users, and Jira projects, followed by all check findings grouped by severity (warnings first, then info). Each finding is expandable and lists every affected entity with supporting detail. |
| **Groups** | Searchable list of all groups. Expand any group to see its members (name, email, account status) and the Jira projects it has access to with the assigned roles. |
| **Users** | Searchable table of all managed users (name, email, account status). Only managed (internal) accounts are included - external and guest accounts are out of scope. |
| **Permissions** | Reserved for a future permissions audit. Currently shows a placeholder. |
| **Jira Spaces** | Searchable list of all Jira projects across all tenants. Expand any project to see which users have direct access and which groups are assigned, including each group's members and permission roles. |

## Prerequisites

- Python 3.10+
- An Atlassian organisation with Admin API access
- An Atlassian Admin API key (org-level)
- An Atlassian account with API token access to each Jira tenant

## Setup

1. Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy the example environment file and fill in your credentials:

```bash
cp src/.env.example src/.env
```

```ini
# src/.env
ADMIN_API_KEY=        # Atlassian org-level admin API key
ORG_ID=               # Your Atlassian organisation ID
ATLASSIAN_USERNAME=   # Email address of the Atlassian account used for Jira API calls
ATLASSIAN_API_TOKEN=  # Atlassian API token for the above account
```

- **ADMIN_API_KEY** - generate at [admin.atlassian.com](https://admin.atlassian.com) → Settings → API keys
- **ORG_ID** - found in the URL of your admin portal: `admin.atlassian.com/o/<ORG_ID>/...`
- **ATLASSIAN_API_TOKEN** - generate at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

## Usage

```bash
cd src
python Auditor.py [--tenants TENANT ...] [--debug]
```

| Flag | Description |
|------|-------------|
| `--tenants` | One or more tenant subdomains to scan. Omit to scan all tenants. |
| `--debug` | Load data from the cached `audit_data.json` instead of hitting the API. |

**Examples:**

```bash
# Scan all tenants
python Auditor.py

# Scan a single tenant (e.g. foo.atlassian.net)
python Auditor.py --tenants foo

# Scan multiple tenants
python Auditor.py --tenants foo bar baz

# Regenerate the report from cached data (no API calls)
python Auditor.py --debug

# Combine: cached data filtered to one tenant
python Auditor.py --tenants foo --debug
```

The script will:
1. Fetch all tenants, groups (with members), managed users, and Jira projects (with role assignments) from the API
2. Cache the raw data to `audit_data.json`
3. Run all checks against the collected data
4. Write `report.html` to the project root

Open `report.html` in any browser to view the report.

## Internals 

### Debug mode

After the first run, pass `--debug` at the command line (or set `DEBUG_MODE = True` in `Auditor.py`) to load data from the cached `audit_data.json` file instead of hitting the API. This speeds up development and testing significantly.

```bash
python Auditor.py --debug
```

### Adding new checks

Checks are split into two files depending on whether they need configuration:

- **`checks.py`** — plug-and-play checks. Each has a `CHECK_<NAME> = True/False` toggle at the top of the file. No other setup needed.
- **`checks_configured.py`** — checks that require org-specific values (a group name, a threshold, etc.). Each check has its own config variables defined above it in the file.

Both files follow the same three-step pattern.

#### 1. Write the check function

Create a private function named `_check_<something>`. It receives whatever slices of `audit_data` it needs, builds a list of `items` (one dict per offending entity), then delegates to `_finding()`.

```python
def _check_example(groups, tenant_map):
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map)}
        for g in groups
        if <your condition here>
    ]
    return _finding(
        "example",           # unique snake_case id - used as an HTML anchor
        "warning",           # "warning" or "info"
        "Groups",            # category shown in the report: "Groups", "Users", or "Jira"
        "groups that ...",   # short title; the report prepends the item count automatically
        "Explanation of why this matters and what to do about it.",
        items,
    )
```

`_finding()` returns `None` when `items` is empty, so the check disappears from the report automatically when there's nothing to flag - no extra guard needed.

**Item dict keys:**

Each dict in `items` must have at least a `"label"` key (the primary display value). Add any extra keys that give useful context in the report - look at existing checks for examples:

| Key | Used for |
|-----|----------|
| `label` | Primary display name (required) |
| `tenant` | Which Atlassian directory the entity belongs to |
| `email` | User email address |
| `groups` | Comma-separated group names |
| `projects` | Comma-separated project names |
| `count` | Numeric count shown alongside the label |
| `key` | Jira project key |

#### 2. Register the check in `run_checks()`

**Plug-and-play (`checks.py`):** add a toggle flag at the top of the file, then add the conditional call to `run_checks()`:

```python
CHECK_EXAMPLE = True

def run_checks(audit_data) -> list[dict]:
    ...
    raw = [
        ...
        _check_example(groups, tenant_map) if CHECK_EXAMPLE else None,
    ]
```

**Configured (`checks_configured.py`):** add config variables above the function, add an `ENABLED` flag, then register it in `run_checks()` the same way:

```python
EXAMPLE_ENABLED   = False
EXAMPLE_THRESHOLD = 10

def run_checks(audit_data) -> list[dict]:
    ...
    raw = [
        ...
        _check_example(groups) if EXAMPLE_ENABLED else None,
    ]
```

#### 3. Test with debug mode

Enable `DEBUG_MODE = True` in `Auditor.py` to iterate against the cached `audit_data.json` without hitting the API on every run.

### HTTP Behaviour 

All HTTP requests go through `http_util.py`, which handles retries, rate limiting and pagination consistently across the Admin and Jira API. 

**Retries and rate limiting**
The tool will retry a request up to 10 times before giving up and returning the last response. This can be configured with the `max_retries` variable at the top of `http_util.py`. Two categories of failure will trigger a retry: 
- **Network errors** including timeouts, connection refused etc. Retried with a 5 second delay between attempts 
- **HTTP error codes** 429, 500, 502, 503, 504

For `429 Rate limited` responses, the tool respects the `Retry-After` header if present. For all other retryable responses, it defaults to a 5 second wait. 

> **Large organisations:** The retry logic handles transient rate limiting automatically, but orgs with a high volume of groups, users or projects may exhaust retries during sustained throttling. If you see repeated `429` failures across many requests, consider running the tool during off-peak hours or reducing concurrent usage of the same API credentials - ideally the script should have a dedicated set of API keys. Also consider increasing the `max_retries` variable, or `default_timeout` variable to give more leniency between request attempts.

**Pagination**
Atlassian Admin API uses cursor-based pagination. The tool passes a `cursor` parameter on each request and follows the `links.next` value in the response until it is absent. 

Jira API uses offset-based pagination with a page size of 50. The tool increments `startAt` by the number of items returned per page and stops when the response includes `isLast: true` or returns an empty page. Failed Jira pages (non-`2xx` responses) are logged and terminate the current pagination sequence. 

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Project structure

```
src/
├── Auditor.py                  # Entry point
├── .env.example                # Environment variable template
├── handlers/
│   ├── http_util.py            # HTTP helpers and pagination
│   ├── tenants.py              # Fetch org tenants (directories)
│   ├── groups.py               # Fetch groups and their members
│   ├── users.py                # Fetch managed users
│   └── jira_spaces.py          # Fetch Jira projects and role assignments
└── report/
    ├── checks.py               # Plug-and-play audit checks (toggle on/off)
    ├── checks_configured.py    # Configured audit checks (require org-specific values)
    └── generator.py            # HTML report generation
```
