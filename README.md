# GetGreen-Open-Project
Github repo for the GetGreen.ai project for OP Fall 25. Store all files here!
To add new changes from everyone else:
- In terminal, cd to GetGreen-OP folder
- Run: git pull origin main (Tells Git to "pull" the new stuff from the repo to your computer)


To add your changes:
- In terminal, cd to the folder containing the file you changecd
- Run: git add <file name including extension> (Tells Git to queue adding your file)
- Run: git commit -m "message explaining commit" (Tells Git you're committing this set of changes since last commit)
- Run: git push origin main ("Pushes" your changes to the repo for everyone)

RUN THE MODEL + FRONTEND:

The **app** (frontend + backend) lives in **`core/`**. Everything else in the repo (analysis, misc, nlp, backend tutorials, etc.) is for reference/artifacts.

1. Pull, set up Ollama with a Llama model, and install JS deps if needed.
2. From GetGreen-OP, run in two terminals:

   **Backend:**  
   `cd core/backend/Response && source ../../../venv/bin/activate && uvicorn mainTry:app --reload --port 8000`

   **Frontend:**  
   `cd core/frontend && npm run dev`

See **`core/README.md`** for data setup (core/data/, .env, FAISS index).
