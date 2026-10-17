"""Support UI only. Never sends an email or includes real account information."""
import re
import time
from driver import shell, tap, waitfor, find, back, deadline, remaining_timeout

EMAIL = "Limerencetechnologies@gmail.com"


def verify_support(ctx):
    check, snap = ctx["check"], ctx["snap"]
    uid = shell("am", "get-current-user").strip()
    if not uid.isdigit():
        raise RuntimeError("Cannot resolve current native user for mail preflight")
    resolver = shell(
        "cmd", "package", "resolve-activity", "--brief", "--user", uid,
        "-a", "android.intent.action.VIEW", "-d", "mailto:" + EMAIL,
    ).strip()
    no_resolver = re.fullmatch(r"No activity found\.?", resolver, re.I) is not None
    components = re.findall(r"[\w.]+/[\w.$]+", resolver)
    if not no_resolver and not components:
        raise RuntimeError("Unknown mail resolver result; no action dispatched")
    expected_package = components[-1].split("/")[0] if components else None

    tap("email-support")
    if no_resolver:
        error = waitfor("support-error", 20)
        check("Native support without mail application shows usable contact",
              EMAIL in error.get("text", ""))
    else:
        # Observe an actual foreground handoff, never infer it from a resolver.
        with deadline(20):
            while True:
                activity = shell("dumpsys", "activity", "activities")
                resumed = re.findall(r"mResumedActivity[^\r\n]+", activity)
                if resumed and expected_package + "/" in resumed[-1]:
                    break
                time.sleep(remaining_timeout(.5))
        check("Native support mail intent hands off without sending email", True)
        back()
        waitfor("email-support", 20)

    contact = waitfor("support-contact", 20)
    check("Native Settings displays approved support contact",
          contact.get("text") == EMAIL)
    button = find("email-support")
    check("Native support operation releases its controls",
          button is not None and button.get("enabled") == "true")
    snap("extended-support-contact")