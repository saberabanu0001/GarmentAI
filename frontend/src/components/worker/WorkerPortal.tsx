"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Mic,
  Printer,
  Square,
  ThumbsDown,
  ThumbsUp,
  Volume2,
} from "lucide-react";
import { postRag } from "@/lib/api/rag";
import { postVoiceTranscribe } from "@/lib/api/voice";
import type { RagHit } from "@/lib/types/rag";
import { workerTopicPills } from "@/data/workerTopics";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: RagHit[];
};

type UiLanguage = "en" | "bn";
type AnswerLanguage = "auto" | "en" | "bn";

function citationKey(h: RagHit): string {
  return `${h.chunk_uid}-${h.rank}`;
}

function messagesNewestFirst(messages: ChatMessage[]): ChatMessage[] {
  const out: ChatMessage[] = [];
  let i = messages.length - 1;
  while (i >= 0) {
    const cur = messages[i];
    if (cur.role === "assistant") {
      if (i >= 1 && messages[i - 1].role === "user") {
        out.push(messages[i - 1], cur);
        i -= 2;
      } else {
        out.push(cur);
        i -= 1;
      }
    } else {
      out.push(cur);
      i -= 1;
    }
  }
  return out;
}

function hasBengali(text: string): boolean {
  return /[\u0980-\u09FF]/.test(text);
}

function pickSpeechLang(answerLanguage: AnswerLanguage, uiLang: UiLanguage, text: string): string {
  if (answerLanguage === "bn") return "bn-BD";
  if (answerLanguage === "en") return "en-US";
  if (hasBengali(text)) return "bn-BD";
  return uiLang === "bn" ? "bn-BD" : "en-US";
}

const copy = {
  en: {
    title: "Your Industrial Rights, Simplified.",
    subtitle:
      "Get instant answers grounded in your factory knowledge base (Labour Act, rules, manuals — per your indexed documents).",
    askPlaceholder: "Ask a question about your rights (Bangla / English)…",
    askBtn: "Ask AI",
    thinking: "Thinking…",
    empty:
      "Ask a question above. Answers use retrieved sources from your backend (Garment API).",
    you: "You",
    assistant: "GarmentAI",
    basedOn: "Based on these documents in your factory library",
    helpful: "Helpful",
    incorrect: "Incorrect",
    printRecord: "Print record",
    topics: "Common topics",
    uiLang: "UI language",
    answerLang: "Answer language",
    answerAuto: "Auto",
    answerEn: "English",
    answerBn: "Bangla",
    compliance: "Industrial compliance",
    complianceHint: "Shift safety widgets connect to live data when your backend provides them.",
    helpline: "Labour helpline (BD)",
    regUpdate: "Regulatory update",
    regHint: "Hook this card to your news / amendment feed later.",
    readBrief: "Read brief",
    listen: "Listen",
    listening: "Listening…",
    stopListening: "Stop",
    voiceUnsupported: "Voice input is not supported in this browser.",
    transcribing: "Transcribing…",
    aiError:
      "Sorry — the assistant could not reach the server. Start the API: `uvicorn backend.main:app --port 5050` and check `.env.local` (NEXT_PUBLIC_API_URL).",
  },
  bn: {
    title: "আপনার শ্রমিক অধিকার, সহজ ভাষায়।",
    subtitle:
      "আপনার কারখানার নথি (শ্রম আইন, নিয়ম, ম্যানুয়াল) থেকে দ্রুত উত্তর পান।",
    askPlaceholder: "আপনার প্রশ্ন লিখুন (বাংলা / ইংরেজি)…",
    askBtn: "এআইকে জিজ্ঞেস করুন",
    thinking: "ভাবছি…",
    empty: "উপরে প্রশ্ন করুন। উত্তর আপনার ব্যাকএন্ডের নথি থেকে আসবে।",
    you: "আপনি",
    assistant: "GarmentAI",
    basedOn: "উত্তরটি আপনার লাইব্রেরির এই নথিগুলোর উপর ভিত্তি করে",
    helpful: "উপকারী",
    incorrect: "ভুল",
    printRecord: "রেকর্ড প্রিন্ট",
    topics: "সাধারণ বিষয়",
    uiLang: "ইউআই ভাষা",
    answerLang: "উত্তরের ভাষা",
    answerAuto: "অটো",
    answerEn: "ইংরেজি",
    answerBn: "বাংলা",
    compliance: "শিল্প কমপ্লায়েন্স",
    complianceHint: "আপনার ব্যাকএন্ডে লাইভ ডেটা এলে এই সেফটি উইজেটগুলো আপডেট হবে।",
    helpline: "শ্রম সহায়তা (বাংলাদেশ)",
    regUpdate: "নিয়ন্ত্রক আপডেট",
    regHint: "পরে এই কার্ডকে নিউজ/সংশোধনী ফিডের সাথে যুক্ত করুন।",
    readBrief: "বিস্তারিত পড়ুন",
    listen: "শুনুন",
    listening: "শোনা হচ্ছে…",
    stopListening: "বন্ধ করুন",
    voiceUnsupported: "এই ব্রাউজারে ভয়েস ইনপুট সমর্থিত নয়।",
    transcribing: "ট্রান্সক্রাইব হচ্ছে…",
    aiError:
      "দুঃখিত — সার্ভারে পৌঁছানো যায়নি। API চালু করুন: `uvicorn backend.main:app --port 5050`, এবং `.env.local` এ NEXT_PUBLIC_API_URL ঠিক আছে কিনা দেখুন।",
  },
} as const;

const workerTopicPillsBn = ["মাতৃত্বকালীন ছুটি", "সাপ্তাহিক ছুটি", "ওভারটাইম মজুরি"];

export function WorkerPortal() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uiLang, setUiLang] = useState<UiLanguage>("en");
  const [answerLang, setAnswerLang] = useState<AnswerLanguage>("auto");
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [voiceInputSupported, setVoiceInputSupported] = useState(true);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const t = copy[uiLang];
  const showExtraWidgets = process.env.NEXT_PUBLIC_SHOW_WORKER_WIDGETS === "true";

  const topicPills = useMemo(
    () => (uiLang === "bn" ? workerTopicPillsBn : workerTopicPills),
    [uiLang],
  );

  useEffect(() => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setVoiceInputSupported(false);
    }
    return () => {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        try {
          recorderRef.current.stop();
        } catch {
          // ignore
        }
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      window.speechSynthesis.cancel();
    };
  }, []);

  async function startVoiceInput() {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setVoiceInputSupported(false);
      return;
    }
    if (listening) return;
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstart = () => setListening(true);
      recorder.onerror = () => {
        setListening(false);
        setError("Voice recording failed. Please try again.");
      };
      recorder.onstop = async () => {
        setListening(false);
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        chunksRef.current = [];
        if (!blob.size) return;
        setTranscribing(true);
        try {
          const lang: "auto" | "en" | "bn" = uiLang === "bn" ? "bn" : "auto";
          const text = await postVoiceTranscribe(blob, lang);
          if (!text) return;
          setQuestion((prev) => (prev.trim() ? `${prev.trim()} ${text}` : text));
        } catch (e) {
          setError(e instanceof Error ? e.message : "Transcription failed");
        } finally {
          setTranscribing(false);
        }
      };

      recorder.start();
    } catch {
      setListening(false);
      setError("Microphone permission denied or unavailable.");
    }
  }

  function stopVoiceInput() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      try {
        recorderRef.current.stop();
      } catch {
        // ignore
      }
    }
  }

  function speak(text: string) {
    if (!text.trim()) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = pickSpeechLang(answerLang, uiLang, text);
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }

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
        response_language: answerLang,
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
          content: t.aiError,
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
          {t.title}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600 md:text-base">{t.subtitle}</p>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-xs">
          <label className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-2.5 py-1.5">
            <span className="text-zinc-600">{t.uiLang}</span>
            <select
              className="bg-transparent font-medium text-zinc-800 outline-none"
              value={uiLang}
              onChange={(e) => setUiLang(e.target.value as UiLanguage)}
            >
              <option value="en">English</option>
              <option value="bn">বাংলা</option>
            </select>
          </label>
          <label className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-2.5 py-1.5">
            <span className="text-zinc-600">{t.answerLang}</span>
            <select
              className="bg-transparent font-medium text-zinc-800 outline-none"
              value={answerLang}
              onChange={(e) => setAnswerLang(e.target.value as AnswerLanguage)}
            >
              <option value="auto">{t.answerAuto}</option>
              <option value="bn">{t.answerBn}</option>
              <option value="en">{t.answerEn}</option>
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask(question)}
            placeholder={t.askPlaceholder}
            className="h-12 flex-1 rounded-xl border border-zinc-200 bg-zinc-50 px-4 text-sm outline-none ring-[#004D40] focus:ring-2"
          />
          <button
            type="button"
            onClick={() => ask(question)}
            disabled={pending}
            className="h-12 shrink-0 rounded-xl bg-[#004D40] px-6 text-sm font-semibold text-white shadow hover:bg-[#00695c] disabled:opacity-60"
          >
            {pending ? t.thinking : t.askBtn}
          </button>
          <button
            type="button"
            onClick={() => (listening ? stopVoiceInput() : startVoiceInput())}
            disabled={!voiceInputSupported || transcribing}
            title={voiceInputSupported ? (listening ? t.stopListening : t.listening) : t.voiceUnsupported}
            className="inline-flex h-12 items-center justify-center gap-1 rounded-xl border border-zinc-200 bg-white px-4 text-xs font-semibold text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {listening ? <Square className="size-4" /> : <Mic className="size-4" />}
            {listening ? t.stopListening : transcribing ? t.transcribing : t.listen}
          </button>
        </div>

        {!voiceInputSupported ? (
          <p className="mt-2 text-xs text-amber-700">{t.voiceUnsupported}</p>
        ) : null}

        {error ? (
          <p className="mt-3 text-sm text-red-700" role="alert">
            {error}
          </p>
        ) : null}

        <div className="mt-6 space-y-6 border-t border-zinc-100 pt-6">
          {messages.length === 0 ? <p className="text-sm text-zinc-500">{t.empty}</p> : null}
          <div className="max-h-[min(70vh,720px)] space-y-6 overflow-y-auto pr-1">
            {messagesNewestFirst(messages).map((m) =>
              m.role === "user" ? (
                <div key={m.id} className="rounded-xl bg-zinc-50 p-4">
                  <div className="text-xs font-semibold text-zinc-500">{t.you}</div>
                  <p className="mt-1 whitespace-pre-wrap text-sm">{m.content}</p>
                </div>
              ) : (
                <div key={m.id} className="rounded-xl border border-zinc-100 p-4">
                  <div className="text-xs font-semibold text-[#004D40]">{t.assistant}</div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-zinc-800">
                    {m.content}
                  </p>
                  {m.citations?.length ? (
                    <div className="mt-4 rounded-lg bg-emerald-50/60 px-3 py-3">
                      <div className="text-xs font-medium text-emerald-900/90">{t.basedOn}</div>
                      <ul className="mt-2 space-y-1.5">
                        {m.citations.map((h) => (
                          <li
                            key={citationKey(h)}
                            className="text-xs leading-snug text-emerald-950/80"
                          >
                            <span className="font-medium">{h.source_name}</span>
                            {h.section ? (
                              <>
                                <span className="text-emerald-800/70"> — </span>
                                <span>{h.section}</span>
                              </>
                            ) : null}
                            <span className="text-emerald-800/60"> (score {h.similarity.toFixed(3)})</span>
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
                      <ThumbsUp className="size-3.5" /> {t.helpful}
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                    >
                      <ThumbsDown className="size-3.5" /> {t.incorrect}
                    </button>
                    <button
                      type="button"
                      onClick={() => speak(m.content)}
                      className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                    >
                      <Volume2 className="size-3.5" /> {t.listen}
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 rounded-lg border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                    >
                      <Printer className="size-3.5" /> {t.printRecord}
                    </button>
                  </div>
                </div>
              ),
            )}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2 border-t border-zinc-100 pt-6">
          <span className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{t.topics}</span>
          {topicPills.map((topic) => (
            <button
              key={topic}
              type="button"
              onClick={() => ask(topic)}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-700 hover:border-[#004D40]/40 hover:text-[#004D40]"
            >
              {topic}
            </button>
          ))}
        </div>
      </section>

      <aside className="flex flex-col gap-4">
        {showExtraWidgets ? (
          <div className="overflow-hidden rounded-xl bg-white shadow-md">
            <div className="h-28 bg-gradient-to-br from-zinc-200 to-zinc-100" />
            <div className="space-y-2 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-800">
                <CheckCircle2 className="size-4 text-emerald-600" />
                {t.compliance}
              </div>
              <p className="text-xs text-zinc-600">{t.complianceHint}</p>
            </div>
          </div>
        ) : null}

        <div className="rounded-xl border border-red-100 bg-white p-4 shadow-md">
          <div className="text-xs font-semibold uppercase text-zinc-500">{t.helpline}</div>
          <a
            href="tel:16357"
            className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-[#c62828] py-2 text-sm font-bold text-white hover:bg-red-700"
          >
            16357
          </a>
        </div>

        {showExtraWidgets ? (
          <div className="rounded-xl bg-[#004D40] p-4 text-white shadow-md">
            <div className="text-xs font-semibold uppercase text-white/80">{t.regUpdate}</div>
            <p className="mt-2 text-sm leading-snug text-white/95">{t.regHint}</p>
            <button
              type="button"
              className="mt-3 w-full rounded-lg bg-white/10 py-2 text-xs font-semibold hover:bg-white/20"
            >
              {t.readBrief}
            </button>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
