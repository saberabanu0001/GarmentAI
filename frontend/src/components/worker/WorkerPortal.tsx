"use client";

import { useState } from "react";
import { CheckCircle2, Printer, ThumbsDown, ThumbsUp } from "lucide-react";
import { postRag } from "@/lib/api/rag";
import type { RagHit } from "@/lib/types/rag";
import { workerTopicPills } from "@/data/workerTopics";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: RagHit[];
};

function citationKey(h: RagHit): string {
  return `${h.chunk_uid}-${h.rank}`;
}

export function WorkerPortal() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(prompt: string) {
    const q = prompt.trim();
    if (!q || pending) return;
    setError(null);
    setPending(true);
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: q,
    };
    setMessages((m) => [...m, userMsg]);
    setQuestion("");
    try {
      const res = await postRag({
        question: q,
        role: "worker",
        top_k: 5,
      });
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.answer,
          citations: res.hits,
        },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Sorry — the assistant could not reach the server. Start the API: `uvicorn backend.main:app --port 5050` and check `.env.local` (NEXT_PUBLIC_API_URL).",
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <section className="rounded-xl border-2 border-violet-400/50 bg-white p-6 shadow-md md:p-8">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 md:text-3xl">
          Your Industrial Rights, Simplified.
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600 md:text-base">
          Get instant answers grounded in your factory knowledge base (Labour
          Act, rules, manuals — per your indexed documents).
        </p>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask(question)}
            placeholder="Ask a question about your rights (Bangla / English)…"
            className="h-12 flex-1 rounded-xl border border-zinc-200 bg-zinc-50 px-4 text-sm outline-none ring-[#004D40] focus:ring-2"
          />
          <button
            type="button"
            onClick={() => ask(question)}
            disabled={pending}
            className="h-12 shrink-0 rounded-xl bg-[#004D40] px-6 text-sm font-semibold text-white shadow hover:bg-[#00695c] disabled:opacity-60"
          >
            {pending ? "Thinking…" : "Ask AI"}
          </button>
        </div>

        {error ? (
          <p className="mt-3 text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Common topics
          </span>
          {workerTopicPills.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => ask(t)}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-700 hover:border-[#004D40]/40 hover:text-[#004D40]"
            >
              {t}
            </button>
          ))}
        </div>

        <div className="mt-8 space-y-6 border-t border-zinc-100 pt-6">
          {messages.length === 0 ? (
            <p className="text-sm text-zinc-500">
              Ask a question above. Answers use retrieved sources from your
              backend (Garment API).
            </p>
          ) : null}
          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="rounded-xl bg-zinc-50 p-4">
                <div className="text-xs font-semibold text-zinc-500">
                  You
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm">{m.content}</p>
              </div>
            ) : (
              <div key={m.id} className="rounded-xl border border-zinc-100 p-4">
                <div className="text-xs font-semibold text-[#004D40]">
                  GarmentAI
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed">
                  {m.content}
                </p>
                {m.citations?.length ? (
                  <div className="mt-4 border-t border-zinc-100 pt-3">
                    <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                      Sources (retrieval)
                    </div>
                    <ul className="mt-2 space-y-2">
                      {m.citations.map((h) => (
                        <li key={citationKey(h)} className="text-xs text-zinc-600">
                          <span className="font-medium text-zinc-800">
                            {h.source_name}
                          </span>
                          {" — "}
                          <span>{h.section}</span>
                          <span className="text-zinc-400">
                            {" "}
                            (score {h.similarity.toFixed(3)})
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-zinc-100 pt-3">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                  >
                    <ThumbsUp className="size-3.5" /> Helpful
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                  >
                    <ThumbsDown className="size-3.5" /> Incorrect
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                  >
                    <Printer className="size-3.5" /> Print record
                  </button>
                </div>
              </div>
            ),
          )}
        </div>
      </section>

      <aside className="flex flex-col gap-4">
        <div className="overflow-hidden rounded-xl bg-white shadow-md">
          <div className="h-28 bg-gradient-to-br from-zinc-200 to-zinc-100" />
          <div className="space-y-2 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-800">
              <CheckCircle2 className="size-4 text-emerald-600" />
              Industrial compliance
            </div>
            <p className="text-xs text-zinc-600">
              Shift safety widgets connect to live data when your backend
              provides them.
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-red-100 bg-white p-4 shadow-md">
          <div className="text-xs font-semibold uppercase text-zinc-500">
            Labour helpline (BD)
          </div>
          <a
            href="tel:16357"
            className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-[#c62828] py-2 text-sm font-bold text-white hover:bg-red-700"
          >
            16357
          </a>
        </div>
        <div className="rounded-xl bg-[#004D40] p-4 text-white shadow-md">
          <div className="text-xs font-semibold uppercase text-white/80">
            Regulatory update
          </div>
          <p className="mt-2 text-sm leading-snug text-white/95">
            Hook this card to your news / amendment feed later.
          </p>
          <button
            type="button"
            className="mt-3 w-full rounded-lg bg-white/10 py-2 text-xs font-semibold hover:bg-white/20"
          >
            Read brief
          </button>
        </div>
      </aside>
    </div>
  );
}
