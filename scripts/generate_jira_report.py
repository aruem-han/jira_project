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
          res = requests.get(
              f"{base_url}/search",
              auth=auth,
              params={
                  "jql": jql,
                  "startAt": start,
                  "maxResults": 50,
                  "fields": "summary,status,priority,created,updated,resolutiondate,project",
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
  lines = [f"# Jira 주간 리포트 — {today}\n"]

  lines.append(f"## 현재 할당된 이슈 ({len(assigned)}건)\n")
  if assigned:
      for i in assigned:
          key = i["key"]
          summary = i["fields"]["summary"]
          status = i["fields"]["status"]["name"]
          priority = (i["fields"].get("priority") or {}).get("name", "-")
          project = i["fields"]["project"]["name"]
          lines.append(f"- **[{key}]** {summary}")
          lines.append(f"  - 프로젝트: {project} | 상태: `{status}` | 우선순위: `{priority}`")
  else:
      lines.append("- 할당된 이슈 없음")

  lines.append(f"\n## 해결 완료된 이슈 ({len(resolved)}건)\n")
  if resolved:
      for i in resolved:
          key = i["key"]
          summary = i["fields"]["summary"]
          resolved_date = (i["fields"].get("resolutiondate") or "")[:10] or "-"
          project = i["fields"]["project"]["name"]
          lines.append(f"- **[{key}]** {summary}")
          lines.append(f"  - 프로젝트: {project} | 완료일: `{resolved_date}`")
  else:
      lines.append("- 해결 완료된 이슈 없음")

  os.makedirs("reports", exist_ok=True)
  filepath = f"reports/jira-report-{today}.md"
  with open(filepath, "w", encoding="utf-8") as f:
      f.write("\n".join(lines))

  print(f"리포트 생성 완료: {filepath}")
