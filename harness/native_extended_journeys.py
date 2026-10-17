"""Native actions + independent local database/Auth assertions; no real users."""
import json
import os
import pathlib
import subprocess
import time
from driver import ROOT, nodes, find, dump, tapnode, shell, record, waitfor, fill, tap, back


def fixture(phones, tid=None, expire=False):
    data = {"action": "expire" if expire else "snapshot", "phones": phones}
    if tid:
        data["tid"] = tid
    r = subprocess.run(
        ["node", "harness/inspect_isolated_fixture.cjs", json.dumps(data)],
        capture_output=True, text=True, timeout=20,
    )
    if r.returncode:
        raise RuntimeError("Fixture inspection failed: " + r.stderr[-350:])
    result = json.loads(r.stdout)
    with (ROOT / "extended-fixture-audit.jsonl").open("a") as out:
        out.write(json.dumps(result) + "\n")
    return result


def native_dialog(label):
    tree = dump()
    candidates = [n for n in nodes(tree)
                  if n.get("resource-id", "").startswith("android:id/button")
                  and n.get("text", "").casefold() == label.casefold()
                  and n.get("visible-to-user") == "true" and n.get("enabled") == "true"]
    if len(candidates) != 1:
        raise AssertionError("Expected one visible native confirmation button: " + label)
    tapnode(candidates[0])


def run(ctx, peer):
    user, ready = ctx["user"], ctx["ready_generate"]
    hide, snap, check = ctx["hide_keyboard"], ctx["snap"], ctx["check"]
    a, b, c, d = ["999990000" + str(i) for i in range(1, 5)]
    for key in ["window_animation_scale", "transition_animation_scale", "animator_duration_scale"]:
        shell("settings", "put", "global", key, "0")

    def generate():
        user(0); ready(); fill("name-input", "Extended Test A"); hide()
        tap("generate"); waitfor("code-text", 45)
        code = find("code-text")["text"].strip()
        if len(code) != 4:
            raise AssertionError("Unexpected native code")
        return code

    def redeem(code, name):
        user(peer); ready(); tap("have-code"); waitfor("code-box-0")
        fill("code-box-0", code); fill("name-input", name); hide(); tap("connect")

    def pair(name):
        code = generate(); redeem(code, name); waitfor("Waiting for them to accept", 60)
        user(0); waitfor("accept", 60); tap("accept"); waitfor("message-input", 60)
        return code

    def change_peer(phone):
        user(peer); ready(); tap("You"); waitfor("settings-name")
        tap("sign-out"); waitfor("phone-input", 45); ctx["login"](peer, phone)

    # Saving and returning to a screen is checked against Firestore, not a toast alone.
    user(0); ready(); tap("You"); waitfor("settings-name")
    fill("settings-name", "Native Persisted Name"); hide(); tap("Save name"); waitfor("Name saved", 30)
    check("Native profile rename persists in Firestore",
          fixture([a])["profiles"][0]["displayName"] == "Native Persisted Name")
    tap("Connect"); ready(); tap("You"); waitfor("settings-name")
    check("Native profile rename survives navigation", find("settings-name")["text"] == "Native Persisted Name")
    from native_support_journey import verify_support
    verify_support(ctx)
    tap("Connect"); ready()

    code = generate(); tap("cancel-code"); waitfor("generate", 30)
    check("Native Cancel code deactivates the exact server code", fixture([a], code)["code"]["status"] == "deactivated")
    redeem(code, "Extended Test B"); waitfor("That code is not active. Ask them to generate a new one.", 45)
    s = fixture([a, b], code)
    check("Native canceled-code redemption creates no pending request",
          find("code-box-0") is not None and not s["requests"])
    ready()

    code = generate(); back(); waitfor("generate", 30)
    check("Native Android Back cancels the owned server code", fixture([a], code)["code"]["status"] == "deactivated")

    code = generate(); fixture([a], code, expire=True)
    redeem(code, "Extended Test B"); waitfor("That code is not active. Ask them to generate a new one.", 45)
    check("Native expired-code response creates no pending request", not fixture([a, b], code)["requests"],
          "Only owned demo server expiry injected; real five-minute UI countdown not accelerated or certified")
    ready(); user(0); ready()

    code = generate(); redeem(code, "Extended Test B"); waitfor("Waiting for them to accept", 60)
    user(0); waitfor("decline", 60); tap("decline"); waitfor("generate", 30)
    state = fixture([a, b], code)
    check("Native decline commits one declined request without a new active chat",
          len(state["requests"]) == 1 and state["requests"][0]["status"] == "declined"
          and not any(x["status"] == "active" for x in state["connections"]))
    user(peer); waitfor("That code is no longer available.", 45)
    check("Native declined peer returns to editable code form", find("code-box-0") is not None)
    ready()

    pair("Extended Test B")
    tap("chat-options"); tap("Block and end connection"); waitfor("Person blocked", 45); snap("extended-blocked")
    s = fixture([a, b])
    check("Native block records a person block and closes all selected-pair chats",
          len(s["blocks"]) == 1 and not any(x["status"] == "active" for x in s["connections"]))
    code = generate(); redeem(code, "Extended Test B")
    waitfor("That code is not active. Ask them to generate a new one.", 45)
    state = fixture([a, b], code)
    check("Native blocked re-pairing is rejected without consuming generator code",
          not state["requests"] and state["code"]["status"] == "active")
    user(0); ready()

    # A third fictional Firebase identity avoids undoing a real person-level block.
    change_peer(c); pair("Extended Test C")
    fill("message-input", "Synthetic native report evidence"); hide(); tap("send-message")
    waitfor("Synthetic native report evidence", 30)
    tap("chat-options"); tap("Report and end connection"); waitfor("What went wrong?", 30)
    tap("Spam or a bot"); waitfor("Report submitted", 45); snap("extended-report-submitted")
    s = fixture([a, c])
    check("Native report persists exactly one report and blocks the selected pair",
          len(s["reports"]) == 1 and len(s["blocks"]) == 1
          and not any(x["status"] == "active" for x in s["connections"]))
    check("Native report establishes extended server evidence retention",
          s["reports"][0]["deleteAt"] > s["now"] + 89 * 86400000)

    # Fourth identity supplies an unrelated active chat during account deletion.
    change_peer(d); pair("Extended Test D")
    before = fixture([a, d]); old_uid = before["profiles"][0]["uid"]
    tap("chat-back"); waitfor("new-connection", 30); tap("You"); waitfor("settings-name")
    tap("delete-account"); waitfor("Delete your account?", 20); native_dialog("Cancel")
    s = fixture([a, d])
    check("Native deletion confirmation Cancel preserves account and active chat",
          s["profiles"][0]["authExists"] and s["profiles"][0]["profileExists"]
          and any(x["status"] == "active" for x in s["connections"]))
    tap("delete-account"); waitfor("Delete your account?", 20); native_dialog("Delete account")
    waitfor("phone-input", 60); snap("extended-account-deleted")
    s = fixture([a, d]); deleted = s["profiles"][0]
    check("Native account deletion removes Auth/profile and completes durable job",
          not deleted["authExists"] and not deleted["profileExists"] and deleted["deletionStatus"] == "complete")
    check("Native account deletion closes the unrelated active chat",
          not any(x["status"] == "active" for x in s["connections"]))
    user(peer); waitfor("Connection ended", 60)
    check("Native peer observes deletion closure with no message composer", find("message-input") is None)

    ctx["login"](0, a)
    recreated = fixture([a])["profiles"][0]
    check("Native re-registration after deletion receives a new eligible Firebase identity",
          recreated["authExists"] and recreated["profileExists"]
          and recreated["uid"] != old_uid and recreated["profileStatus"] == "active")
    snap("extended-reregistered")
    record("Extended native destructive journeys completed", "PASS",
           "Four fictional Firebase identities on two Android users; local services only; no block reset or production mutation")
    (ROOT / "extended-complete.json").write_text(json.dumps({
        "passed": True,
        "scope": "Native UI plus independently read Auth/Firestore emulator state",
        "fixturePhones": [a, b, c, d],
        "productionChanged": False,
        "realSmsTested": False,
        "storeAttestationTested": False,
        "expiry": "Owned demo server record fault injection, not an accelerated five-minute UI timer",
    }, indent=2))