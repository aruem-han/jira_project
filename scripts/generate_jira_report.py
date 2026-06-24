import os
import requests
from datetime import datetime

JIRA_URL = os.environ["JIRA_URL"]
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
base_url = f"https://{JIRA_URL}/rest/api/3"


def search_issues(jql, max_results=200):
    issues, start = [], 0
    while True:
        res = requests.post(
            f"{base_url}/search/jql",
            auth=auth,
            json={
                "jql": jql,
                "startAt": start,
                "maxResults": 50,
                "fields": ["summary", "status", "priority", "created", "updated", "resolutiondate", "project"],
            },
        )
        res.raise_for_status()
        data = res.json()
        issues.extend(data["issues"])
        if len(issues) >= data["total"] or len(issues) >= max_results:
            break
        start += 50
    return issues


assigned = search_issues(
    f'assignee = "{JIRA_EMAIL}" AND statusCategory != Done ORDER BY updated DESC'
)
resolved = search_issues(
    f'assignee = "{JIRA_EMAIL}" AND statusCategory = Done ORDER BY updated DESC'
)

today = datetime.now().strftime("%Y-%m-%d")
lines = [f"# Jira Weekly Report - {today}\n"]

lines.append(f"## Assigned Issues ({len(assigned)})\n")
if assigned:
    for i in assigned:
        key = i["key"]
        summary = i["fields"]["summary"]
        status = i["fields"]["status"]["name"]
        priority = (i["fields"].get("priority") or {}).get("name", "-")
        project = i["fields"]["project"]["name"]
        lines.append(f"- **[{key}]** {summary}")
        lines.append(f"  - Project: {project} | Status: `{status}` | Priority: `{priority}`")
else:
    lines.append("- No assigned issues")

lines.append(f"\n## Resolved Issues ({len(resolved)})\n")
if resolved:
    for i in resolved:
        key = i["key"]
        summary = i["fields"]["summary"]
        resolved_date = (i["fields"].get("resolutiondate") or "")[:10] or "-"
        project = i["fields"]["project"]["name"]
        lines.append(f"- **[{key}]** {summary}")
        lines.append(f"  - Project: {project} | Resolved: `{resolved_date}`")
else:
    lines.append("- No resolved issues")

os.makedirs("reports", exist_ok=True)
filepath = f"reports/jira-report-{today}.md"
with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Report saved: {filepath}")
