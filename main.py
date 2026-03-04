import modelconnectors
import arxiv_search
import yaml
import json
import re
import random
from datetime import datetime

with open("config.yaml") as f:
    config = yaml.safe_load(f)

CHUNK_SIZE = 50
PREFILTER_KEEP = 100   # random sample of non-venue papers passed to Haiku
HAIKU_KEEP_PER_CHUNK = 5  # max papers Haiku keeps per chunk of 50


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def venue_prefilter(results):
    venues = config.get("top_venues", [])
    venue_papers, other_papers = [], []
    for r in results:
        comment = (r.comment or "").lower()
        if any(v.lower() in comment for v in venues):
            venue_papers.append(r)
        else:
            other_papers.append(r)

    # Keep all venue papers + a random sample of the rest
    sample = random.sample(other_papers, min(PREFILTER_KEEP, len(other_papers)))
    candidates = venue_papers + sample
    print(f"Venue filter: {len(venue_papers)} venue papers + {len(sample)} sampled others = {len(candidates)} candidates")
    return candidates


def chunked_haiku_filter(client, candidates):
    prefilter_model = config["claude"]["summary_model"]  # Haiku
    interests = "\n".join(f"- {i}" for i in config["interests"])
    shortlisted_ids = []

    chunks = [candidates[i:i + CHUNK_SIZE] for i in range(0, len(candidates), CHUNK_SIZE)]
    for i, chunk in enumerate(chunks):
        papers_text = "\n\n".join(
            f"ID: {r.entry_id}\nTitle: {r.title}\nAbstract: {r.summary}"
            for r in chunk)

        prompt = f"""You are filtering arxiv papers for a data scientist with these interests:
{interests}

From the papers below, return the IDs of the {HAIKU_KEEP_PER_CHUNK} most relevant ones (fewer if none are relevant).
Return only a JSON array of entry_id strings. No other text, no markdown fences.

Papers:
{papers_text}"""

        response = modelconnectors.send_message(client, prefilter_model, prompt)
        kept = parse_json(response.content[0].text)
        shortlisted_ids.extend(kept)
        print(f"  Chunk {i+1}/{len(chunks)}: kept {len(kept)} papers")

    return shortlisted_ids


def relevance_filter():
    client, selection_model = modelconnectors.create_connection()
    summary_model = config["claude"]["summary_model"]
    interests = "\n".join(f"- {i}" for i in config["interests"])

    # Step 1: fetch papers
    print("Fetching papers from arxiv...")
    results = arxiv_search.search_filter()
    results_by_id = {r.entry_id: r for r in results}
    print(f"Fetched {len(results)} papers")

    # Step 2: venue pre-filter (no API call)
    candidates = venue_prefilter(results)

    # Step 3: chunked Haiku filter
    print(f"Running Haiku pre-filter on {len(candidates)} candidates...")
    shortlisted_ids = chunked_haiku_filter(client, candidates)
    shortlisted = [results_by_id[eid] for eid in shortlisted_ids if eid in results_by_id]
    print(f"Haiku shortlisted {len(shortlisted)} papers")

    # Step 4: Sonnet picks final 20
    print("Running Sonnet final selection...")
    shortlist_text = "\n\n".join(
        f"ID: {r.entry_id}\nTitle: {r.title}\nVenue: {r.comment or 'n/a'}\nAbstract: {r.summary}"
        for r in shortlisted)

    selection_prompt = f"""You are an arxiv paper picker. Select the 20 most relevant papers based on these interests:
{interests}

Prefer papers accepted at top venues (NeurIPS, ICML, ICLR, Nature, etc.) when quality is equal.
Return a JSON array of exactly 20 objects with keys:
- "entry_id": the arxiv ID exactly as given
- "reason": one sentence explaining why it matches my interests

Return only the JSON array, no other text, no markdown fences.

Papers:
{shortlist_text}"""

    response = modelconnectors.send_message(client, selection_model, selection_prompt)
    selected = parse_json(response.content[0].text)

    # Step 5: Haiku summarizes the 20
    print("Running Haiku summarization...")
    selected_text = "\n\n".join(
        f"ID: {item['entry_id']}\nTitle: {results_by_id[item['entry_id']].title}\nAbstract: {results_by_id[item['entry_id']].summary}"
        for item in selected if item["entry_id"] in results_by_id)

    summary_prompt = f"""Summarize each paper in 2-3 plain English sentences. No jargon. Focus on what was done and why it matters.

Return a JSON array of objects with keys "entry_id" and "summary".
Return only the JSON array, no other text, no markdown fences.

Papers:
{selected_text}"""

    summary_response = modelconnectors.send_message(client, summary_model, summary_prompt)
    summaries = {s["entry_id"]: s["summary"] for s in parse_json(summary_response.content[0].text)}

    # Build output
    output = []
    for item in selected:
        r = results_by_id.get(item["entry_id"])
        if r:
            output.append({
                "entry_id": r.entry_id,
                "title": r.title,
                "authors": [a.name for a in r.authors],
                "summary": summaries.get(r.entry_id, r.summary),
                "categories": r.categories,
                "pdf_url": r.pdf_url,
                "venue": r.comment or "",
                "reason": item["reason"],
            })

    data = {
        "last_run": datetime.now().isoformat(),
        "papers": output,
    }

    with open("results.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Done — saved {len(output)} papers to results.json")
    return data


if __name__ == "__main__":
    relevance_filter()
