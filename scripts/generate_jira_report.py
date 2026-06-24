import os
import requests
from datetime import datetime

JIRA_URL = os.environ["JIRA_URL"]
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]

auth = (JIRA_EMAIL, JIRA_API_TOKEN)
base_url = f"https://{JIRA_URL}/rest/api/3"

# 계정 ID 조회
me = requests.get(f"{base_url}/myself", auth=auth)
me.raise_for_status()
account_id = me.json()["accountId"]
print(f"Account ID: {account_id}")


def search_issues(jql, max_results=100):
    res = requests.post(
        f"{base_url}/search/jql",
        auth=auth,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "status", "priority", "created", "updated", "resolutiondate", "project"],
        },
    )
    if not res.ok:
        print(f"Error {res.status_code}: {res.text}")
        res.raise_for_status()
    return res.json().get("issues", [])


assigned = search_issues(
    f"assignee = '{account_id}' AND statusCategory != Done ORDER BY updated DESC"
)
resolved = search_issues(
    f"assignee = '{account_id}' AND statusCategory = Done ORDER BY updated DESC"
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
