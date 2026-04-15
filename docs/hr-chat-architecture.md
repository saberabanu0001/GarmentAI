# HR chat — how it works (plain English)

This page explains **AI Chat (HR)** in the GarmentAI app: what happens when an HR manager types a question, where answers come from, and what is **not** connected yet.

---

## In one sentence

You ask a question in the browser → the **backend** searches a **local knowledge index** (Chroma) for relevant text → a **Groq** language model writes an answer using **only** that text (plus safe fallbacks) → you see the answer and optional **source titles**.

---

## The big picture (simple)

Think of three boxes:

1. **Your browser** — the HR chat screen (`/hr/chat`).
2. **GarmentAI API** — your FastAPI server (Python).
3. **Brain + library** — **Chroma** (saved snippets from laws, manuals, etc.) and **Groq** (the AI that writes sentences).

```mermaid
flowchart TB
  subgraph you [You]
    Screen[HR_chat_screen]
  end
  subgraph app [GarmentAI_on_your_computer]
    API[Backend_API]
    Index[(Chroma_index)]
  end
  subgraph cloud [Internet]
    AI[Groq_AI]
    MicAI[Speech_to_text_if_you_use_Listen]
  end
  Screen -->|"question_JSON"| API
  API -->|"find_similar_text"| Index
  Index -->|"matching_snippets"| API
  API -->|"write_answer"| AI
  AI -->|"reply_text"| API
  API -->|"answer_and_sources"| Screen
  Screen -->|"optional_voice_clip"| MicAI
  MicAI -->|"text"| Screen
```

**Important:** **HR documents** uploads are saved on disk, then a **background job** extracts text (PDF via `pymupdf4llm`), splits into chunks, embeds with **`intfloat/multilingual-e5-small`**, and stores them in Chroma collection **`hr_uploads`**. HR chat searches that collection too. Re-running `python scripts/ingest_laws.py` **without** `--no-clean` **wipes** all Chroma data including `hr_uploads` — use `--no-clean` or re-upload/re-index after a full rebuild.

---

## Step by step: you click “Ask AI”

```mermaid
sequenceDiagram
  participant You
  participant Page as HR_chat_page
  participant Server as Backend
  participant Library as Chroma
  participant Writer as Groq

  You->>Page: Type question and press Ask_AI
  Page->>Server: Send_question_and_maybe_login_token
  Server->>Server: Check_who_you_are_HR_role_if_logged_in
  Server->>Library: Search_for_relevant_chunks_hr_can_see
  Library-->>Server: Top_matching_text_snippets
  Server->>Server: Keep_only_snippets_above_similarity_bar
  Server->>Writer: Please_answer_using_these_snippets_only
  Writer-->>Server: Answer_paragraph
  Server-->>Page: Answer_plus_source_list
  Page-->>You: Show_answer_and_citations
```

**Plain words:**

- The server treats you as **HR** (`hr_staff`) when you are logged in, so it only pulls document snippets your role is allowed to see.
- If nothing matches well enough, the app still replies — but it should **not** invent fake law quotes; the code tells the model to be honest when the library has nothing solid.
- **Listen** records your voice, sends audio to **transcribe**, puts text in the box — you still press **Ask AI** to run the flow above.
- **Read aloud** uses the **browser’s** built-in speech (no extra server).

---

## What each part of the project does

| Piece | What it is |
|-------|------------|
| [HR chat page](../frontend/src/app/(dashboard)/hr/chat/page.tsx) | Opens the chat UI for HR. |
| [RagChatPortal](../frontend/src/components/chat/RagChatPortal.tsx) | The actual chat: languages, topic chips, Ask AI, voice button, citations. |
| [rag.ts](../frontend/src/lib/api/rag.ts) | Sends your question to `/api/chat`; adds your **login token** if you have one. |
| [chat.py](../backend/api/chat.py) | Receives the question, decides **role** (from token or body), runs RAG. |
| [rag.py](../backend/services/rag.py) | Search Chroma → filter by quality → call Groq with a strict “use only this text” instruction. |
| [chroma_engine.py](../backend/services/chroma_engine.py) | Vector search + **who can see which chunk** (worker vs HR vs compliance). |
| [voice API](../backend/api/voice.py) | Turns short voice recordings into text for the input box. |

---

## HR vs worker chat (difference)

Same engine; different **labels**, **suggested topics**, and **which documents** the role may see. HR chat does **not** show the worker “helpline” card.

---

## Data you should know about

| Storage | Role in HR chat |
|---------|------------------|
| **Chroma** (`data/chroma_data/`) | The “library” the chat searches. Built by your team using ingest scripts. |
| **Groq** | Cloud AI that **words** the answer (needs `GROQ_API_KEY`). |
| **HR uploads folder** (`data/hr_uploads/`) | **Not searched by chat today** until you add an “ingest this file” step into Chroma. |

---

## Ideas for later (not built yet)

1. **After each HR upload** — automatically chunk, embed, and add to Chroma so chat can use new PDFs.
2. **Stronger security** — require login for all chat (`ENFORCE_AUTH_CHAT=true` in config).
3. **Factory filter** — send `factory_id` so answers prefer one factory’s tenant docs.

---

## Technical diagram (for developers)

Same architecture as above, with filenames:

```mermaid
flowchart LR
  subgraph browser [Browser]
    Portal[RagChatPortal.tsx]
  end
  subgraph api [FastAPI]
    ChatRoute[chat.py]
    VoiceRoute[voice.py]
    RagSvc[rag.py]
    ChromaSvc[chroma_engine.py]
    LlmSvc[llm_wrapper.py]
  end
  subgraph local [Local_disk]
    ChromaDB[(chroma_data)]
  end
  subgraph remote [Cloud]
    GroqAPI[Groq_LLM]
    STT[Transcription_API]
  end
  Portal --> ChatRoute
  ChatRoute --> RagSvc
  RagSvc --> ChromaSvc
  ChromaSvc --> ChromaDB
  RagSvc --> LlmSvc
  LlmSvc --> GroqAPI
  Portal --> VoiceRoute
  VoiceRoute --> STT
```

---

*GarmentAI / Experiment — update when ingestion or auth rules change.*
