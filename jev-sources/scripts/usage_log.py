"""One JSON line per event in <data>/logs/<name>.jsonl, for tuning. Local only; JEV_LOG=off turns it off. Never raises."""
import datetime, json, os
from paths import DATA


def write(name, **fields):
    if os.environ.get("JEV_LOG") == "off":
        return
    try:
        d = os.path.join(DATA, "logs")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{name}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **fields}) + "\n")
    except Exception:
        pass
