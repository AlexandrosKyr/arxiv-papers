import modelconnectors
import arxiv_search
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

client, model = modelconnectors.create_connection

def relevance_filter(client, model):
    results = arxiv_search.search_filter()
    papers = "\n\n".join(
        f"{r.entry_id}\nTitle: {r.title}\nAbstract: {r.summary}"
        for r in results)
    interests = "\n".join(f"    - {i}" for i in config["interests"])
    prompt = f"""You are an arxiv relevant paper picker. All the papers that you are getting are from categories I chose.
    However I want you to still choose the 20 more relevant. Here are some interests of mine not in any particular order:
    {interests}
    Here are the Titles and Abstracts of the papers:
    {papers}"""

    response = modelconnectors.send_message(client, model, prompt)
    return response
