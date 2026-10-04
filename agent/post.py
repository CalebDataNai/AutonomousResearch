"""Write one ~1000-word research post with a Foundry-hosted model and update the manifest."""
import datetime as dt, json, os, re, sys
from openai import OpenAI

MODEL = os.environ["FOUNDRY_MODEL"]  # your deployment name
client = OpenAI(base_url=os.environ["FOUNDRY_BASE_URL"], api_key=os.environ["FOUNDRY_API_KEY"])
POSTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts")
AREAS = ["evaluation and benchmarks", "interpretability", "agents and tool use", "training efficiency",
         "alignment and safety", "multimodal models", "reasoning models"]

PROMPT = """You write the daily post for an AI research microblog read by informed non-specialists.
Today is {date}. Focus area: {area}. Pick one specific, recent, concrete topic in that area.

Write about 2000 words (1500 to 2500) in Markdown:
- The first line is '# Title' (under 90 characters).
- Use 3 to 4 '##' sections covering the claim, the evidence, caveats, and open questions.
- Cite only sources you are confident exist, as Markdown links with the title. If unsure of a detail, say so.
- Never invent quotes, statistics, or URLs. Paraphrase; do not reproduce copyrighted text.
Return only the post."""


def draft(today):
    area = AREAS[today.timetuple().tm_yday % len(AREAS)]
    for _ in range(2):
        r = client.chat.completions.create(
            model=MODEL, max_completion_tokens=8000,
            messages=[{"role": "user", "content": PROMPT.format(date=today.date(), area=area)}])
        text = (r.choices[0].message.content or "").strip()
        title = re.match(r"#\s+(.+)", text)
        if title and 700 <= len(text.split()) <= 1400:
            return title.group(1).strip(), text
    sys.exit("No valid draft after 2 attempts; nothing written.")


def main():
    today = dt.datetime.now(dt.timezone.utc)
    title, text = draft(today)
    os.makedirs(POSTS, exist_ok=True)
    slug = f"{today:%Y-%m-%d}-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]
    if os.path.exists(os.path.join(POSTS, slug + ".md")):
        slug += f"-{today:%H%M}"
    with open(os.path.join(POSTS, slug + ".md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    path = os.path.join(POSTS, "index.json")
    index = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    index.insert(0, {"slug": slug, "title": title, "date": today.isoformat(timespec="minutes"),
                     "model": MODEL, "words": len(text.split())})
    json.dump(index, open(path, "w", encoding="utf-8"), indent=2)
    print(f"Wrote {slug}.md ({len(text.split())} words)")


if __name__ == "__main__":
    main()
