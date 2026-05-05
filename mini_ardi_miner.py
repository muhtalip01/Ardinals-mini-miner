#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from json import JSONDecoder
from typing import Any, Dict, List, Optional


ARDI_BIN = os.environ.get("ARDI_AGENT_BIN", "ardi-agent")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

RARITY_WEIGHT = {
    "legendary": 500,
    "rare": 300,
    "uncommon": 150,
    "common": 0,
}


def log(msg: str) -> None:
    print(f"[mini-ardi] {msg}", flush=True)


def run_cmd(args: List[str], timeout: int = 120) -> str:
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    return proc.stdout.strip()


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    decoder = JSONDecoder()

    # Prefer the main ardi-agent response object.
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
            if isinstance(obj, dict) and "status" in obj:
                return obj
        except Exception:
            continue

    # Fallback: first valid object.
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue

    return None


def ardi_json(*args: str, timeout: int = 120) -> Optional[Dict[str, Any]]:
    out = run_cmd([ARDI_BIN, *args], timeout=timeout)
    obj = extract_json(out)
    if obj is None:
        log(f"Could not parse JSON from: {out[:500]}")
    return obj


def get_context_data(ctx: Dict[str, Any]) -> Dict[str, Any]:
    data = ctx.get("data", {})
    if isinstance(data, dict) and isinstance(data.get("current"), dict):
        return data["current"]
    if isinstance(data, dict):
        return data
    return {}


def compact_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    data = get_context_data(ctx)
    riddles = data.get("riddles", [])
    compact = []
    for r in riddles:
        compact.append(
            {
                "wordId": r.get("wordId") or r.get("word_id"),
                "language": r.get("language"),
                "rarity": r.get("rarity"),
                "power": r.get("power"),
                "theme": r.get("theme"),
                "riddle": r.get("riddle"),
            }
        )
    return {
        "epochId": data.get("epochId") or data.get("epoch_id"),
        "commitDeadline": data.get("commitDeadline") or data.get("commit_deadline"),
        "revealDeadline": data.get("revealDeadline") or data.get("reveal_deadline"),
        "riddles": compact,
    }


def choose_locally_first(riddles: List[Dict[str, Any]], max_per_epoch: int) -> List[Dict[str, Any]]:
    def score(r: Dict[str, Any]) -> int:
        return RARITY_WEIGHT.get(str(r.get("rarity", "")).lower(), 0) + int(r.get("power") or 0)

    return sorted(riddles, key=score, reverse=True)[:max_per_epoch]


def groq_solve(ctx: Dict[str, Any], max_per_epoch: int) -> List[Dict[str, Any]]:
    if not GROQ_API_KEY and not OPENROUTER_API_KEY:
        log("No LLM API key set: GROQ_API_KEY and OPENROUTER_API_KEY are both missing")
        return []

    compact = compact_context(ctx)
    top_riddles = choose_locally_first(compact["riddles"], max_per_epoch)
    for rr in top_riddles:
        log("selected riddle: " + json.dumps(rr, ensure_ascii=False)[:500])
    system = (
        "You solve multilingual word riddles for a commit-reveal game. "
        "Return ONLY valid JSON array, no markdown, no prose. "
        "Each answer must be a real common dictionary word or well-known proper noun. "
        "Do not invent words. Do not answer with obscure random characters. "
        "Do not latch onto one clue while ignoring stronger clues. "
        "If the riddle contains a creature/object definition, prioritize the exact creature/object over related gods, places, or themes. "
        "Your reason must mention the strongest clue words that justify the answer. "
        "For Chinese use simplified Chinese. "
        "For Japanese prefer standard kanji/kana dictionary spelling, not romaji. "
        "For Korean use Hangul. "
        "For German capitalize nouns. "
        "For French/English use lowercase unless it is a proper noun. "
        "If unsure, prefer an easier lower-power riddle over inventing an answer."
    )

    user = {
        "task": f"Solve these riddles. Return up to {max_per_epoch} best candidates.",
        "output_schema": [
            {
                "wordId": 123,
                "answer": "exact answer",
                "alternative": "possible alternative or empty",
                "confidence": 0.0,
                "reason": "very short reason mentioning strongest clues",
            }
        ],
        "selection_rule": (
            "Choose only answers you are highly confident are real canonical words "
            "with the exact native spelling. Prefer legendary > rare > uncommon > common, "
            "then higher power, but skip any riddle if the answer is uncertain, has ambiguous spelling, "
            "or looks invented. Prefer fewer strong answers over filling the requested count."
        ),
        "riddles": top_riddles,
    }

    import requests

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2500,
    }

    resp = None

    # 1) Try Groq first
    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        if resp.status_code == 200:
            log("LLM provider=groq")
        else:
            log(f"Groq error {resp.status_code}: {resp.text[:300]}")
            resp = None

    except Exception as e:
        log(f"Groq exception: {e}")
        resp = None

    # 2) Fallback to OpenRouter
    if resp is None:
        if not OPENROUTER_API_KEY:
            log("OpenRouter fallback unavailable: OPENROUTER_API_KEY missing")
            return []

        openrouter_payload = dict(payload)
        openrouter_payload["model"] = OPENROUTER_MODEL

        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://local.mini-ardi",
                    "X-Title": "mini-ardi-miner",
                },
                json=openrouter_payload,
                timeout=90,
            )

            if resp.status_code == 200:
                log(f"LLM provider=openrouter model={OPENROUTER_MODEL}")
            else:
                log(f"OpenRouter error {resp.status_code}: {resp.text[:500]}")
                return []

        except Exception as e:
            log(f"OpenRouter exception: {e}")
            return []

    content = resp.json()["choices"][0]["message"]["content"]
    parsed = None
    try:
        parsed = json.loads(content)
    except Exception:
        obj = extract_json(content)
        if isinstance(obj, dict) and "answers" in obj:
            parsed = obj["answers"]

        if not isinstance(parsed, list):
            log(f"LLM returned non-list content; skipping cycle: {content[:500]}")
            return []

    clean = []

    for item in parsed:
        if not isinstance(item, dict):
            continue

        word_id = item.get("wordId") or item.get("word_id")
        answer = item.get("answer")
        confidence = item.get("confidence") or 0

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0

        if confidence < 0.8:
            log(f"rejected word={word_id} answer={answer} conf={confidence} reason=low confidence")
            continue

        if word_id and answer:
            clean.append(
                {
                    "wordId": int(word_id),
                    "answer": str(answer).strip(),
                    "alternative": item.get("alternative", ""),
                    "confidence": confidence,
                    "reason": item.get("reason", ""),
                }
            )

    return clean[:max_per_epoch]


def commit_answers(epoch_id: int, answers: List[Dict[str, Any]], dry_run: bool = False) -> None:
    for a in answers:
        word_id = a["wordId"]
        answer = a["answer"]

        log(
            f"candidate word={word_id} answer={answer} alt={a.get('alternative')} "
            f"conf={a.get('confidence')} reason={a.get('reason')}"
        )

        if dry_run:
            log(f"dry-run would commit epoch={epoch_id} word={word_id} answer={answer} conf={a.get('confidence')}")
            continue

        if os.getenv("ARDI_ENABLE_COMMIT") != "YES":
           log(f"real commit blocked; set ARDI_ENABLE_COMMIT=YES to enable word={word_id} answer={answer}")
           continue

        out = run_cmd(
            [ARDI_BIN, "commit", "--word-id", str(word_id), "--answer", answer],
            timeout=180,
        )
        print(out, flush=True)


def drive_pending(dry_run: bool = False) -> None:
    commits = ardi_json("commits", timeout=120)
    if not commits:
        log("no commits data")
        return

    data = commits.get("data", {})
    if not isinstance(data, dict):
        log("commits data is not a dict")
        return

    pending = data.get("pending", [])
    if not pending:
        log("no local pending entries")
        return

    min_epoch = int(os.getenv("ARDI_PENDING_MIN_EPOCH") or 0)

    for p in pending:
        if not isinstance(p, dict):
            continue

        status = p.get("status")
        epoch_id = p.get("epoch_id")
        word_id = p.get("word_id")

        if not epoch_id or not word_id:
            continue

        try:
            epoch_int = int(epoch_id)
        except Exception:
            log(f"skip pending with invalid epoch={epoch_id} word={word_id}")
            continue

        if epoch_int < min_epoch:
            log(f"skip old pending epoch={epoch_id} word={word_id}; min_epoch={min_epoch}")
            continue

        if status == "committed":
            wait = int(p.get("next_reveal_in_seconds") or 0)
            if wait > 0:
                log(f"reveal not ready epoch={epoch_id} word={word_id}, wait={wait}s")
                continue

            cmd = [ARDI_BIN, "reveal", "--epoch", str(epoch_id), "--word-id", str(word_id)]

        elif status in ("revealed", "won"):
            cmd = [ARDI_BIN, "inscribe", "--epoch", str(epoch_id), "--word-id", str(word_id)]

        else:
            continue

        if dry_run:
            log("dry-run would run: " + " ".join(cmd))
            continue

        log("running: " + " ".join(cmd))
        out = run_cmd(cmd, timeout=180)
        print(out, flush=True)


def tick(max_per_epoch: int, dry_run: bool = False) -> None:
    # Old pending reveal/inscribe automation is disabled by default.
    # This prevents old epochs from being revealed or inscribed accidentally.
    if os.getenv("ARDI_ENABLE_PENDING") == "YES":
        drive_pending(dry_run=dry_run)
    else:
        log("old pending reveal/inscribe skipped; set ARDI_ENABLE_PENDING=YES to enable")

    # Then look for an open commit window.
    ctx = ardi_json("context", timeout=120)
    if not ctx or ctx.get("status") != "ok":
        log("no context or context not ok")
        return

    data = get_context_data(ctx)
    deadline = data.get("commitDeadline") or data.get("commit_deadline")
    epoch_id = data.get("epochId") or data.get("epoch_id")
    riddles = data.get("riddles", [])

    log(f"debug context status={ctx.get('status')} epoch_id={epoch_id} deadline={deadline} riddles={len(riddles) if isinstance(riddles, list) else 'no-list'}")

    if not deadline or not epoch_id or not riddles:
        log("no open commit window")
        return

    now = int(time.time())
    remaining = int(deadline) - now
    if remaining <= 15:
        log(f"commit window too short ({remaining}s), skip")
        return

    log(f"epoch={epoch_id} commit window open, closes in {remaining}s, riddles={len(riddles)}")

    answers = groq_solve(ctx, max_per_epoch=max_per_epoch)
    if not answers:
        log("no answers from Groq")
        return

    commit_answers(epoch_id=int(epoch_id), answers=answers, dry_run=dry_run)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true", help="run forever")
    ap.add_argument("--interval", type=int, default=30, help="seconds between ticks")
    ap.add_argument("--max", type=int, default=5, help="max commits per epoch")
    ap.add_argument("--dry-run", action="store_true", help="print but do not commit/reveal/inscribe")
    args = ap.parse_args()

    if args.loop:
        log(f"loop mode interval={args.interval}s max={args.max}")
        while True:
            try:
                tick(max_per_epoch=args.max, dry_run=args.dry_run)
            except Exception as e:
                log(f"ERROR: {e}")
            time.sleep(args.interval)
    else:
        tick(max_per_epoch=args.max, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
