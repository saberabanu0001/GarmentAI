export type HrDocumentCategory =
  | "employee"
  | "recruitment"
  | "training"
  | "compliance"
  | "performance"
  | "other";

export type HrDocumentLanguage = "en" | "bn";

export type HrDocumentRow = {
  id: string;
  category: HrDocumentCategory | string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  rel_path: string;
  uploaded_at: string;
  uploaded_by: string;
  language?: HrDocumentLanguage | string;
  chroma_indexed?: boolean;
  chroma_chunks?: number;
  chroma_error?: string | null;
  chroma_indexed_at?: string | null;
};
