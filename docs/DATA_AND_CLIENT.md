# Public repo vs client version (sensitive data)

This project is set up so you can:

1. **Publish a public repo** that contains no sensitive data (no user data CSVs, no API keys, no FAISS index built from real articles).
2. **Give the client a working version** that includes the data they need to run the app.

## How it works

- **Sensitive files are in `.gitignore`** and are not committed:
  - `data/articles_cleaned_filtered.csv`
  - `data/data_with_stats.csv`
  - `data/simplified_data.csv`
  - `backend/Response/faiss_index.bin`
  - `.env` (API keys, etc.)

- The **public repo** only has code, sample/placeholder data, and docs. Cloning it does not include the above files.

- The **client version** is the same repo **plus** the data and config you deliver separately.

## Making the current repo “public”

1. **Stop tracking the sensitive files** (they stay on your disk but are removed from Git):
   ```bash
   git rm --cached data/articles_cleaned_filtered.csv data/data_with_stats.csv data/simplified_data.csv 2>/dev/null || true
   git rm --cached backend/Response/faiss_index.bin 2>/dev/null || true
   git add .gitignore data/README.md .env.example docs/DATA_AND_CLIENT.md
   git commit -m "Keep sensitive data out of repo; add data README and client instructions"
   ```

2. **Push** to the public remote. From then on, anyone who clones will not get those files.

3. **If those files were ever committed in the past**, they still exist in Git history. To remove them from history entirely (e.g. for a fully public-safe repo), you’d need to use something like [git filter-repo](https://github.com/newren/git-filter-repo) or BFG Repo-Cleaner. Only do this if the repo is not shared with others yet, or coordinate with everyone.

## Giving the client a working version

**Option A – Same repo + data package**

1. Client clones the **public** repo.
2. You send the **data package** over a secure channel (encrypted ZIP, secure link, USB, etc.):
   - `articles_cleaned_filtered.csv`
   - `data_with_stats.csv`
   - (Optional) `faiss_index.bin` if you don’t want them to run the vector_retriever script.
3. Client places the CSVs in `data/`, adds a `.env` from `.env.example`, and runs the app. If you didn’t send `faiss_index.bin`, they run:
   ```bash
   python backend/Response/vector_retriever.py
   ```

**Option B – Private repo or branch with data**

1. Keep a **private** repo (or private branch) where you *do* commit the data files (by not ignoring them there, or by having that repo’s `.gitignore` different).
2. Give the client access only to that private repo or branch. They clone and run.

**Option C – Client-only copy**

1. On your machine, keep the data files in place (they’re only untracked now).
2. Create a ZIP (or tarball) of the whole project directory and send it to the client. That snapshot includes the data and is for their use only.

## Summary

| Version   | Repo contents        | Data / secrets        |
|----------|----------------------|------------------------|
| Public   | Code + docs + sample | Not included          |
| Client   | Same code            | Added via package or private repo/copy |

After you run the `git rm --cached` and commit above, your **remote** can be the public version. The client gets the same code plus the data through one of the options above.
