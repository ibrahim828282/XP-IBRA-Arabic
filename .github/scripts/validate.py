"""Validate catalog/arabic.json: schema, no duplicate games/translations, every URL https.

Run from the repo root:  pip install jsonschema && python .github/scripts/validate.py
Exit code 0 = valid, 1 = problems (listed on stdout).
"""
import json
import pathlib
import sys

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "catalog" / "arabic.json"
SCHEMA = ROOT / "catalog" / "arabic.schema.json"
URL_FIELDS = ("page", "download", "sha256url", "searchUrl")


def main() -> int:
    errors = []
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except Exception as exc:  # not JSON at all: nothing else can be checked
        print(f"ERROR arabic.json is not valid JSON: {exc}")
        return 1
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    validator = jsonschema.Draft7Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {where}: {err.message}")

    seen_ids = {}
    for gi, game in enumerate(data.get("games") or []):
        if not isinstance(game, dict):
            continue
        appid = str(game.get("appid", "")).strip()
        gname = game.get("name", f"games[{gi}]")
        if appid in seen_ids:
            errors.append(f"duplicate game: appid {appid} ({gname}) already at games[{seen_ids[appid]}]")
        else:
            seen_ids[appid] = gi

        names, pages = {}, {}
        for ti, tr in enumerate(game.get("translations") or []):
            if not isinstance(tr, dict):
                continue
            tag = f"{gname} / translations[{ti}]"
            n = str(tr.get("name", "")).strip().casefold()
            if n:
                if n in names:
                    errors.append(f"duplicate translation name in {gname}: '{tr.get('name')}' (translations[{names[n]}] and [{ti}])")
                else:
                    names[n] = ti
            p = str(tr.get("page") or "").strip().rstrip("/").casefold()
            if p:
                if p in pages:
                    errors.append(f"duplicate translation page in {gname}: {tr.get('page')} (translations[{pages[p]}] and [{ti}])")
                else:
                    pages[p] = ti
            for field in URL_FIELDS:
                url = tr.get(field)
                if url is None or url == "":
                    continue
                if not isinstance(url, str) or not url.startswith("https://"):
                    errors.append(f"not https: {tag}.{field} = {url!r}")

    games = len(data.get("games") or [])
    trs = sum(len(g.get("translations") or []) for g in data.get("games") or [] if isinstance(g, dict))
    if errors:
        print(f"arabic.json: {len(errors)} problem(s):")
        for e in errors:
            print("  - " + e)
        return 1
    print(f"arabic.json OK: {games} game(s), {trs} translation(s), schema valid, no duplicates, all URLs https.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
