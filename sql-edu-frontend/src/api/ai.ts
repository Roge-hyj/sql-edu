import { request } from "@/utils/request";

export type SqlHintResponse = {
  hint: any;
};

export function sqlHint(data: { sql: string }) {
  return request<SqlHintResponse>({
    url: "/ai/sql-hint",
    method: "POST",
    data,
  });
}

export type SqlCheckResponse = {
  is_correct: boolean;
  hint: any;
  submission_id: number;
  error_message?: string | null;
  /** 因危险操作（DROP/DELETE 等）被拒，而非结果不正确 */
  is_safety_blocked?: boolean;
  /** 本次获得经验（仅首次正确完成该题时返回） */
  earned_experience?: number | null;
  /** 是否升级 */
  level_up?: boolean;
  /** 新等级（仅升级时返回） */
  new_level?: number | null;
};

export function checkSql(data: {
  student_sql: string;
  question_id: number;
  language?: string;
  /** 是否在限时挑战中完成，完成时给予额外经验 */
  challenge_mode?: boolean;
}) {
  return request<SqlCheckResponse>({
    url: "/ai/check-sql",
    method: "POST",
    data,
  });
}

export type SubmissionOut = {
  id: number;
  user_id: number;
  question_id: number;
  student_sql: string;
  ai_hint: string | null;
  is_correct: boolean;
  hint_level: number;
  created_at: string;
};

export function getMySubmissions(params?: { question_id?: number; limit?: number }) {
  const limit = params?.limit ?? 100;
  const q = typeof params?.question_id === "number" ? `&question_id=${params.question_id}` : "";
  return request<SubmissionOut[]>({
    url: `/ai/submissions?limit=${limit}${q}`,
    method: "GET",
  });
}

export function getSubmission(submissionId: number) {
  return request<SubmissionOut>({
    url: `/ai/submissions/${submissionId}`,
    method: "GET",
  });
}

export type ChatMessage = {
  id: number;
  role: "system" | "user" | "assistant";
  content: string;
  created_at: string;
};

export function getChatMessages(params: { question_id: number; limit?: number }) {
  const limit = params.limit ?? 80;
  return request<ChatMessage[]>({
    url: `/ai/chat/messages?question_id=${params.question_id}&limit=${limit}`,
    method: "GET",
  });
}

export function clearChatMessages(questionId: number) {
  return request<{ deleted: number }>({
    url: `/ai/chat/messages?question_id=${questionId}`,
    method: "DELETE",
  });
}

export function chatWithTeacher(data: { question_id: number; message: string; language?: string }) {
  return request<{ reply: string }>({
    url: "/ai/chat",
    method: "POST",
    data,
  });
}

