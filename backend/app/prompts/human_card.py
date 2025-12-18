HUMAN_CARD_TEMPLATE = """# Human Review Required

## Task: {task_id} - {task_name}

### Specification Summary
{spec_summary}

### Test Results
- Status: {test_status}
- Passed: {tests_passed}/{tests_total}
- Coverage: {coverage}%

### Security Scan
- Findings: {security_findings_count}
- Severity: {max_severity}
- Flags: {security_flags}

### Proposed Changes
```diff
{patch_diff}
```

### AI Confidence: {confidence}%

{confidence_explanation}

### Actions Required
- [ ] Run locally and verify
- [ ] Approve PR
- [ ] Request changes

### Notes
{notes}

---
*Review requested by: {requested_by}*
*Timestamp: {timestamp}*
"""
