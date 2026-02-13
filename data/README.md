# Data directory

This folder holds the data files required for the GetGreen backend to run.

## Public repo (no data included)

The **public repository does not include** the following files. You need to add them locally or obtain them from the project maintainer:

| File | Purpose |
|------|---------|
| `articles_cleaned_filtered.csv` | Article corpus for retrieval (title + scraped text). |
| `data_with_stats.csv` | User activity and stats; must include a `user_id` column. |

After adding these files, build the FAISS index once (from project root):

```bash
python backend/Response/vector_retriever.py
```

## Client / full version

If you received a **client package** or **data bundle**, place the CSV files listed above in this `data/` directory. Then create a `.env` in the project root with any required keys (see `.env.example`).

Other files in this directory (e.g. sample CSVs, notebooks) may be present in the public repo for reference only.
