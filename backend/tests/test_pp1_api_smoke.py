"""Run against a local running FastAPI server. Creates real Neon test records.

    python -m tests.test_pp1_api_smoke
"""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000/api/coordinator"


def request(method, path, data=None):
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        BASE + path, data=payload, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            return json.load(res)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode()}") from exc


def main():
    result = request("POST", "/start")
    thread = result["thread_id"]
    print("New PP1 workflow:", thread)
    rejected = False
    reviews = 0
    while result["workflow_status"] == "WAITING_FOR_REVIEW":
        pending = result["pending_review"]
        module = pending["module_name"]
        version = pending["version"]
        decision = {"decision": "approve", "feedback": ""}
        if module == "database_design" and not rejected:
            decision = {"decision": "reject", "feedback": "Test retry: restore missing relationship"}
            rejected = True
        print("Review:", module, version, decision["decision"])
        result = request("POST", f"/{thread}/review", decision)
        reviews += 1
        assert reviews <= 20, "Unexpected review loop"
    assert result["workflow_status"] == "COMPLETED", result
    history = request("GET", f"/{thread}/history")
    report = request("GET", f"/{thread}/report")
    assert report["report"]["workflow_status"] == "COMPLETED"
    assert len(history["reviews"]) == reviews
    assert len(history["artifacts"]) >= 8
    assert any(x["decision"] == "REJECT" for x in history["reviews"])
    assert any(x["module"] == "database_design" and x["version"] == 2 for x in history["artifacts"])
    print("PASS: all seven Modules, review history, retry versions, report")
    print("THREAD_ID:", thread)
    print("Restart FastAPI and GET /api/coordinator/" + thread + "/status to verify persistence.")


if __name__ == "__main__":
    main()
