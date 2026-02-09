import { request } from "@/utils/request";
import type { SqlHintResponse, SqlCheckResponse, SubmissionOut, ChatMessage } from "@/types";

// 重新导出类型，保持向后兼容
export type { SqlHintResponse, SqlCheckResponse, SubmissionOut, ChatMessage } from "@/types";

export function sqlHint(data: { sql: string }) {
  return request<SqlHintResponse>({
    url: "/ai/sql-hint",
    method: "POST",
    data,
  });
}

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

