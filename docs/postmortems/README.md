# Postmortem log

Do not commit a made-up incident report. After executing the outage/recovery drill, create a dated Markdown report with:

- **Summary:** what failed and its user-visible effect, if any.
- **Timeline (UTC):** start, detection, diagnosis, mitigation and recovery timestamps.
- **Detection:** exact health-check output or logs, sanitized of secrets.
- **Root cause:** evidence-based explanation; label hypotheses as hypotheses.
- **Recovery:** commands used and verification results.
- **Impact/data integrity:** whether notes were missing or changed.
- **What went well / poorly:** specific observations.
- **Corrective actions:** owner, task and acceptance criterion.
- **Evidence:** commit SHA, workflow run, test output and scan report.
