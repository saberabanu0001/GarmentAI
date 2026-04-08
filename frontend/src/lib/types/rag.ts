export type RagHit = {
  rank: number;
  similarity: number;
  chunk_uid: string;
  chunks_file: string;
  document_name: string;
  source_name: string;
  section: string;
  collection: string;
  doc_scope: string;
  language: string;
  text: string;
};

export type RagResponse = {
  answer: string;
  hits: RagHit[];
};

export type RagErrorBody = {
  error: string;
  allowed?: string[];
};
