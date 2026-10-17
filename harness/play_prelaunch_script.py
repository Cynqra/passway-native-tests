"""Build a private, bounded Google Robo crawl for the existing release.

Reference: https://firebase.google.com/docs/test-lab/android/robo-scripts-reference
This is single-device fictional-account coverage, not real SMS, paired-device
acceptance, an AppCheck exemption, or a successful test result.
"""
import json
import os
import re
import sys


def descriptor(identifier):
    return [{"resourceIdRegex": "(?:.*:id/)?" + re.escape(identifier)}]


def present(identifier):
    return {"condition": "element_present", "elementDescriptors": descriptor(identifier)}


def click(identifier):
    return {"eventType": "VIEW_CLICKED", "elementDescriptors": descriptor(identifier)}


def enter(identifier, text):
    return {"eventType": "VIEW_TEXT_CHANGED", "elementDescriptors": descriptor(identifier),
            "replacementText": text}


def wait_for(identifier):
    return {"eventType": "WAIT_FOR_ELEMENT", "delayTime": 30000,
            "elementDescriptors": descriptor(identifier)}


def assertion(identifier):
    return {"eventType": "ASSERTION", "contextDescriptor": present(identifier)}


def build(config):
    if not isinstance(config, dict) or config.get("project") != "passway-2ddc8":
        raise ValueError("Configured fictional project required")
    fixtures = config.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != 2:
        raise ValueError("Exactly two configured fictional accounts required")
    if {f.get("phone") for f in fixtures if isinstance(f, dict)} != {
        "+919999900001", "+919999900002"
    }:
        raise ValueError("Reserved fictional phone accounts only")
    if any(not isinstance(f, dict) or
           not isinstance(f.get("code"), str) or
           not re.fullmatch(r"[0-9]{6}", f["code"]) for f in fixtures):
        raise ValueError("Configured six digit fictional verification codes required")
    account = fixtures[0]
    scripts = []

    def add(identifier, description, context, actions, runs=1, priority=10):
        scripts.append({"id": identifier, "description": description,
                        "priority": priority, "maxNumberOfRuns": runs,
                        "contextDescriptor": context, "actions": actions})

    add(1600, "Advance current onboarding without assuming an existing login",
        present("welcome-next"), [click("welcome-next")], runs=3)
    add(1601, "Finish current onboarding", present("get-started"), [click("get-started")])
    add(1602, "Configured fictional phone only; no real SMS request",
        present("phone-input"), [
            enter("phone-input", account["phone"][3:]), click("send-code"),
            wait_for("verify-input"), assertion("verify-input")])
    add(1603, "Verify configured fictional account without bypassing app verification",
        present("verify-input"), [
            enter("verify-input", account["code"]), click("verify"),
            {"eventType": "WAIT", "delayTime": 3000}])
    add(1604, "Adult eligibility only if the fictional account needs onboarding",
        present("age-day"), [
            enter("age-day", "01"), enter("age-month", "01"), enter("age-year", "1990"),
            click("age-continue")])
    add(1605, "Scroll to and affirm current use rules only when presented",
        {"condition": "element_present",
         "elementDescriptors": [{"text": "Read and accept these rules before connecting or sending content. You can decline and sign out, or delete your account without accepting."}]}, [
            {"eventType": "ELEMENT_SCROLL_INTO_VIEW",
             "elementDescriptors": [{"className": "android.widget.ScrollView"}],
             "childElementDescriptors": descriptor("accept-use-rules")},
            click("accept-use-rules"), wait_for("generate"), assertion("generate")])
    add(1606, "Request a single reserved-account code without an external test peer",
        present("generate"), [
            enter("name-input", "Play Review"), click("generate")])
    # A separate conditional action handles Android's runtime permission dialog.
    # It must not be blocked by a WAIT_FOR_ELEMENT inside the preceding script.
    permission = [{"resourceIdRegex":
                   ".*:id/(?:permission_allow_foreground_only_button|permission_allow_button)$"}]
    add(1607, "Allow Android foreground permission only when requested",
        {"condition": "element_present", "elementDescriptors": permission},
        [{"eventType": "VIEW_CLICKED", "elementDescriptors": permission}],
        runs=3, priority=100)
    add(1608, "Verify code screen, cancel owned code, then verify settings",
        present("cancel-code"), [
            wait_for("code-text"), assertion("code-text"), click("cancel-code"),
            wait_for("generate"), assertion("generate"), click("open-settings"),
            wait_for("settings-name"), assertion("settings-name")])
    scripts.append({
        "id": 1699,
        "description": "Do not mutate shared accounts or create unsolicited content while exploring",
        "contextDescriptor": {"condition": "app_under_test_shown"},
        "actions": [{"eventType": "ELEMENT_IGNORED", "elementDescriptors": [{
            "resourceIdRegex": "(?:.*:id/)?(?:delete-account|policy-delete-account|"
                               "sign-out|decline-use-rules|chat-options|send-message|"
                               "email-support|have-code|generate)$"}]}]})
    return scripts


def main():
    if len(sys.argv) != 3:
        raise ValueError("Private fixture file and private output path required")
    with open(sys.argv[1]) as handle:
        scripts = build(json.load(handle))
    # No credentials in stdout, repository payload, or world-readable files.
    fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(scripts, handle, indent=2)
        handle.write("\n")
    print("Prepared bounded single-device fictional-account crawl; not test execution proof.")


if __name__ == "__main__":
    main()