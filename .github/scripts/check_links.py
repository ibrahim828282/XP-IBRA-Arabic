"""Open every link in catalog/arabic.json (HEAD, then GET when HEAD is refused) with a timeout.

Writes broken.md (a Markdown list of broken links) and exits 1 when any link is broken, 0 when all open.
Search links (searchUrl) are skipped: search engines often refuse automated requests.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "catalog" / "arabic.json"
OUT = ROOT / "broken.md"
FIELDS = ("page", "download", "sha256url", "installZip")
TIMEOUT = 25
UA = "XP-IBRA-Arabic link check (+https://github.com/ibrahim828282/XP-IBRA-Arabic)"


def probe(url: str):
    """Return None when the link opens, else a short reason."""
    last = None
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Range": "bytes=0-0"} if method == "GET" else {"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                if resp.status < 400:
                    return None
                last = f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            # some servers refuse HEAD (403/405/501): try GET before calling it broken
            if method == "HEAD":
                continue
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    return last


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    broken, checked = [], 0
    for game in data.get("games") or []:
        for tr in game.get("translations") or []:
            for field in FIELDS:
                url = tr.get(field)
                if not url:
                    continue
                checked += 1
                why = probe(url)
                status = "OK" if why is None else f"BROKEN ({why})"
                print(f"{status:40} {game.get('name')} / {tr.get('name')} / {field}: {url}")
                if why is not None:
                    broken.append(f"- **{game.get('name')}** / {tr.get('name')} / `{field}`: {url} — {why}")
    print(f"checked {checked} link(s), {len(broken)} broken")
    if broken:
        OUT.write_text("\n".join(broken) + "\n", encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
