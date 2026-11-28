#!/usr/bin/env python3
"""スキル運用ダッシュボード用の dashboard.json を作る。

入力: .claude/skills/*/SKILL.md, CLAUDE.md, および同じフォルダの
skills-meta.json, vendor-skills.json, usage-log.jsonl, feedback.json, runs.json
出力: dashboard.json（skills / usage_weekly / candidates / rules / runs）
載せるのは自作スキルだけ。vendor-skills.json に載っている導入スキルと、Anthropic・プラグインのスキルは除く。
"""
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SKILLS_DIR = ROOT / ".claude" / "skills"
JST = dt.timezone(dt.timedelta(hours=9))
WEEKS = 12

KIND_LABEL = {"general": "汎用ルール候補", "task-specific": "スキル候補", "skill-fix": "スキル改修"}
STATUS_LABEL = {"observing": "観測中", "promoted": "反映済み", "rejected": "見送り"}


def load(name, default):
    try:
        return json.loads((HERE / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    try:
        import yaml
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        out = {}
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t")):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip("\"'")
        return out


def first_sentence(text, limit=90):
    text = " ".join(str(text or "").split())
    for sep in ("。", ". "):
        if sep in text:
            text = text.split(sep)[0] + sep.strip()
            break
    return text if len(text) <= limit else text[: limit - 1] + "…"


def own_skills(meta, vendored):
    rows = []
    if not SKILLS_DIR.exists():
        return rows
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        fm = frontmatter(skill_md.read_text(encoding="utf-8"))
        name = str(fm.get("name") or skill_md.parent.name)
        if name in vendored or skill_md.parent.name in vendored:
            continue
        m = meta.get(name, {})
        rows.append({
            "id": name,
            "name": name,
            "source": "自作",
            "category": m.get("category", ""),
            "summary": m.get("summary") or first_sentence(fm.get("description", "")),
            "status": m.get("status", "運用中"),
            "updated": m.get("updated"),
            "model_reviewed": m.get("model_reviewed"),
        })
    return rows


def week_start(d):
    return d - dt.timedelta(days=d.weekday())


def main():
    today = dt.datetime.now(JST).date()
    meta = load("skills-meta.json", {})
    vendored = set(load("vendor-skills.json", {}))
    feedback = load("feedback.json", [])
    runs = load("runs.json", [])

    uses = []
    log = HERE / "usage-log.jsonl"
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                rec["_date"] = dt.date.fromisoformat(str(rec["date"])[:10])
                uses.append(rec)
            except (ValueError, KeyError):
                continue

    skills = own_skills(meta, vendored)
    own_ids = {s["id"] for s in skills}

    # 自作スキルの利用だけを数える（"/名前" や "project:名前" の形も拾う）
    def resolve(name):
        name = str(name).lstrip("/").strip()
        return name if name in own_ids else name.split(":")[-1]

    uses = [u for u in uses if resolve(u.get("skill", "")) in own_ids]
    total, last30, last90, last_used = Counter(), Counter(), Counter(), {}
    for u in uses:
        sid = resolve(u.get("skill", ""))
        total[sid] += 1
        age = (today - u["_date"]).days
        if age < 30:
            last30[sid] += 1
        if age < 90:
            last90[sid] += 1
        if sid not in last_used or u["_date"] > last_used[sid]:
            last_used[sid] = u["_date"]

    for s in skills:
        s["uses_30d"] = last30.get(s["id"], 0)
        s["uses_90d"] = last90.get(s["id"], 0)
        s["uses_total"] = total.get(s["id"], 0)
        lu = last_used.get(s["id"])
        s["last_used"] = lu.isoformat() if lu else None

    skills.sort(key=lambda s: (-s["uses_30d"], -s["uses_total"], s["id"]))

    this_week = week_start(today)
    weeks = [this_week - dt.timedelta(weeks=i) for i in range(WEEKS - 1, -1, -1)]
    wk_uses = Counter(week_start(u["_date"]) for u in uses)
    wk_sessions = {}
    for u in uses:
        wk_sessions.setdefault(week_start(u["_date"]), set()).add(u.get("session_id"))
    usage_weekly = [{"week": w.isoformat(), "uses": wk_uses.get(w, 0),
                     "sessions": len(wk_sessions.get(w, ()))} for w in weeks]

    candidates = []
    for f in feedback:
        occ = f.get("occurrences", [])
        dates = sorted(str(o.get("date", "")) for o in occ if o.get("date"))
        candidates.append({
            "id": f.get("id"),
            "kind": KIND_LABEL.get(f.get("kind"), f.get("kind", "")),
            "summary": f.get("summary", ""),
            "task_type": f.get("task_type") or f.get("skill") or "",
            "count": len({o.get("session_id") for o in occ}),
            "status": STATUS_LABEL.get(f.get("status"), f.get("status", "")),
            "target": f.get("target") or "",
            "last_seen": dates[-1] if dates else None,
        })
    candidates.sort(key=lambda c: (c["status"] != "観測中", -c["count"], c["id"] or ""))

    rules = []
    claude_md = ROOT / "CLAUDE.md"
    if claude_md.exists():
        section = ""
        for line in claude_md.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                section = line[3:].strip()
            elif section and re.match(r"^\s*[-*] ", line):
                rules.append({"id": f"r{len(rules) + 1:03d}", "section": section,
                              "rule": re.sub(r"^\s*[-*] ", "", line).strip()})

    run_rows = [{
        "date": r.get("date"),
        "sessions_analyzed": int(r.get("sessions_analyzed") or 0),
        "claude_md_changes": int(r.get("claude_md_changes") or 0),
        "skills_added": int(r.get("skills_added") or 0),
        "skills_updated": int(r.get("skills_updated") or 0),
        "summary": r.get("summary", ""),
    } for r in runs]
    run_rows.sort(key=lambda r: r["date"] or "", reverse=True)

    out = {
        "generated_at": dt.datetime.now(JST).isoformat(timespec="minutes"),
        "skills": skills,
        "usage_weekly": usage_weekly,
        "candidates": candidates,
        "rules": rules,
        "runs": run_rows,
    }
    (HERE / "dashboard.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"skills={len(skills)} uses={len(uses)} candidates={len(candidates)} rules={len(rules)} runs={len(run_rows)}")


if __name__ == "__main__":
    main()
