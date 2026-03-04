"""
SUPERSEDED — this script previously generated articles.csv (with URLs as scraped_text,
which was broken) and user_stats.csv (a duplicate of data_with_stats-copy.csv).

Both generated files have been replaced:
  - articles.csv / articles_cleaned_filtered.csv  →  articles_with_actions.csv
    Columns: Title, URL, action_ids, action_names, scraped_text
    Source:  External-Links.csv (all action mappings) +
             core/data/articles_cleaned_filtered.csv (real scraped text)

  - user_stats.csv  →  use data_with_stats-copy.csv directly (same content)

To rebuild the FAISS/NumPy embedding index for the RAG, run:
  python core/backend/vector_retriever.py
"""
raise SystemExit(
    "build_app_data.py is superseded. "
    "The canonical article data is now articles_with_actions.csv. "
    "See the docstring above for details."
)
