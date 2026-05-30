#!/usr/bin/env python3
import json
import sys
try:
    from comby import Comby
except ImportError:
    print(json.dumps({"error": "comby Python package not found. Run: pip install comby"}))
    sys.exit(0)

def cmd_search(args):
    template, path = args[0], args[1]
    language = args[2] if len(args) > 2 and args[2] else None
    try:
        c = Comby()
        kw = {}
        if language:
            kw["language"] = language
        found = False
        for m in c.matches(path, template, **kw):
            found = True
            print(json.dumps({"matched": m.matched, "range_start": str(m.range.start) if hasattr(m, "range") else "", "range_end": str(m.range.end) if hasattr(m, "range") else ""}, ensure_ascii=False))
        if not found:
            print("No matches found")
    except Exception as e:
        err = str(e)
        if "/bin/sh:" in err and "comby" in err:
            print(json.dumps({"error": "comby binary not found. Install: yay -S comby-bin (Arch) / brew install comby (macOS) / download from https://github.com/comby-tools/comby/releases"}))
        else:
            print(json.dumps({"error": err[:300]}))

def cmd_replace(args):
    template, replacement, path = args[0], args[1], args[2]
    language = args[3] if len(args) > 3 and args[3] else None
    try:
        c = Comby()
        kw = {}
        if language:
            kw["language"] = language
        found = False
        for r in c.rewrite(path, template, replacement, **kw):
            found = True
            print(json.dumps({"rewritten_source": r.rewritten_source if hasattr(r, "rewritten_source") else str(r)}, ensure_ascii=False))
        if not found:
            print("No replacements made")
    except Exception as e:
        err = str(e)
        if "/bin/sh:" in err and "comby" in err:
            print(json.dumps({"error": "comby binary not found. Install: yay -S comby-bin (Arch) / brew install comby (macOS) / download from https://github.com/comby-tools/comby/releases"}))
        else:
            print(json.dumps({"error": err[:300]}))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: comby_helper.py <search|replace> <args...>"}))
        sys.exit(0)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "search": cmd_search(args)
    elif cmd == "replace": cmd_replace(args)
    else: print(json.dumps({"error": f"Unknown command: {cmd}"}))
