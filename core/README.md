# GetGreen app

## 1. Data

Put these in **`core/core_data/`**:

- `articles_cleaned_filtered.csv` – article corpus
- `data_with_stats-copy.csv` – user/stats source CSV
- `data_with_stats.db` – sqlite database file (auto-created/updated by backend)

Then build the search index once:

```bash
cd core/backend
python vector_retriever.py
```

## 2. Environment

Copy `core/.env.example` to `core/.env`. Add Supabase/OpenAI keys if you use them.

## 3. Run

**Terminal 1 – backend:**

```bash
cd core/backend
uvicorn response:app --reload --port 8000
```

**Terminal 2 – frontend:**

```bash
cd core/frontend
npm install
npm run dev
```

Frontend: http://localhost:8080. Backend: http://localhost:8000.
