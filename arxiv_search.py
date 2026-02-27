import logging
import re
import arxiv
import datetime

client = arxiv.Client()

def search_filter()-> str:
  end_date = datetime.datetime.now()
  start_date = end_date - datetime.timedelta(days=7)
  date_filter = f'submittedDate:[{start_date.strftime("%Y%m%d")}0000 TO {end_date.strftime("%Y%m%d")}2359]'

  # Set up search
  search = arxiv.Search(
    query=(
        f"({date_filter}) AND ("
        "cat:stat.* "
        "OR cat:q-fin.* "
        "OR cat:cs.LG "
        "OR cat:cs.AI "
        "OR cat:cs.MA "
        "OR cat:cs.CL"
        ")"
    ),
    max_results=20, #Reduce for now for testing
    sort_by=arxiv.SortCriterion.SubmittedDate
  )

  results = list(client.results(search))

  for r in results:
    print(r.title)

  return results