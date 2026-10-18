from forgeclaw.services.developer_mode import DeveloperModeService, _extract_json_payload

def test_extract_json_payload():
    # Plain JSON array
    raw_array = '[{"id": "t1", "title": "Test"}]'
    assert _extract_json_payload(raw_array) == raw_array

    # Markdown fenced JSON array
    fenced = '```json\n[{"id": "t1", "title": "Test"}]\n```'
    assert _extract_json_payload(fenced) == '[{"id": "t1", "title": "Test"}]'

    # JSON array with conversational preamble
    preamble = 'Here is the plan:\n[{"id": "t1", "title": "Test"}]\nHope this helps!'
    assert _extract_json_payload(preamble) == '[{"id": "t1", "title": "Test"}]'

def test_extract_patch_resilience():
    service = DeveloperModeService()

    # Standard diff
    diff = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new"
    assert service._extract_patch(diff).startswith("diff --git")

    # Fenced diff
    fenced_diff = f"```diff\n{diff}\n```"
    assert service._extract_patch(fenced_diff).startswith("diff --git")

    # Diff with introductory text
    intro_diff = f"Here is the requested patch:\n\n{diff}"
    assert service._extract_patch(intro_diff).startswith("diff --git")
