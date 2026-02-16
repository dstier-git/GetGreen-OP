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
pull 
set up a llama model on your computer thru Ollama
might have to install some JS stuff, check terminal errors

once setup, run in 2 separate terminals both  starting from GetGreen-OP:
cd backend/Response && source ../../venv/bin/activate && uvicorn mainTry:app --reload --port 8000

cd frontend && npm run dev
