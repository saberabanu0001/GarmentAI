# GarmentAI frontend (Next.js + TypeScript)

## Run

From the **repository root**:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API

Point the UI at the FastAPI server (default `http://127.0.0.1:5050`):

```bash
# repo root, venv active
uvicorn backend.main:app --reload --host 127.0.0.1 --port 5050
```

Optional: `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:5050
```

RAG requests use `POST /api/chat` (see `src/lib/api/rag.ts`).
