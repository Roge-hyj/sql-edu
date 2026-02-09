import { request } from "@/utils/request";

export type QuestionOut = {
  id: number;
  title: string;
  content: string;
  /** 多语言题面（可选；未填写则前端回退到 title/content） */
  title_en?: string | null;
  content_en?: string | null;
  title_zh_tw?: string | null;
  content_zh_tw?: string | null;
  difficulty: number;
  correct_sql: string;
  time_limit_seconds?: number | null;
  /** 表结构预览 JSON：tables[{name,columns,rows}]，供学生查看列名与示例数据 */
  schema_preview?: string | null;
  /** 要求的结果列名或完整说明，供学生端显著展示，避免列名不规范错误 */
  required_output_columns?: string | null;
  /** 动态难度 1～10，由客观数据与学生评分综合计算 */
  display_difficulty?: number | null;
  /** 限时挑战建议秒数 */
  suggested_time_seconds?: number | null;
};

export function getQuestions(params?: { skip?: number; limit?: number }) {
  const skip = params?.skip ?? 0;
  // 默认一次性拉取尽可能多的题目（依赖后端分页上限，当前默认 1000）
  const limit = params?.limit ?? 1000;
  return request<QuestionOut[]>({
    // 后端路由是 /questions/（带尾斜杠），避免 307 重定向导致 Authorization 丢失
    url: `/questions/?skip=${skip}&limit=${limit}`,
    method: "GET",
  });
}

export function getQuestion(questionId: number) {
  return request<QuestionOut>({
    url: `/questions/${questionId}`,
    method: "GET",
  });
}

export function createQuestion(data: {
  title: string;
  content: string;
  title_en?: string | null;
  content_en?: string | null;
  title_zh_tw?: string | null;
  content_zh_tw?: string | null;
  correct_sql: string;
  difficulty?: number | null;
  time_limit_seconds?: number | null;
  schema_preview?: string | null;
  required_output_columns?: string | null;
}) {
  return request<QuestionOut>({
    // 后端路由是 /questions/（带尾斜杠），避免 307 重定向导致 Authorization 丢失
    url: "/questions/",
    method: "POST",
    data,
  });
}

export function updateQuestion(
  questionId: number,
  data: {
    title: string;
    content: string;
    title_en?: string | null;
    content_en?: string | null;
    title_zh_tw?: string | null;
    content_zh_tw?: string | null;
    correct_sql: string;
    difficulty?: number | null;
    time_limit_seconds?: number | null;
    schema_preview?: string | null;
    required_output_columns?: string | null;
  }
) {
  return request<QuestionOut>({
    url: `/questions/${questionId}`,
    method: "PUT",
    data,
  });
}

export function deleteQuestion(questionId: number) {
  return request<{ result: "success" | "failure"; detail?: string | null }>({
    url: `/questions/${questionId}`,
    method: "DELETE",
  });
}

/** 正确完成题目后提交难度评分（1～10），用于动态调整题目难度 */
export function submitDifficultyFeedback(questionId: number, rating: number) {
  return request<{ result: string; detail?: string | null }>({
    url: `/questions/${questionId}/difficulty-feedback`,
    method: "POST",
    data: { rating },
  });
}

/** SQL 知识点（入门→精通），教师端按知识点生成题目用 */
export type KnowledgePoint = {
  id: string;
  name: string;
  level: string;
  description: string;
  /** 多语言可选字段（后端可能返回），前端按 ai_language 选择显示 */
  name_i18n?: Record<string, string>;
  level_i18n?: Record<string, string>;
  description_i18n?: Record<string, string>;
};

export function getKnowledgePoints() {
  return request<KnowledgePoint[]>({
    url: "/questions/knowledge-points",
    method: "GET",
  });
}

/** 根据题目内容与 SQL 由 AI 生成表结构预览（教师端），返回更新后的题目 */
export function generateSchemaPreview(questionId: number) {
  return request<QuestionOut>({
    url: `/questions/${questionId}/generate-schema-preview`,
    method: "POST",
  });
}

/** 为题目生成英文/繁体题面（教师端手动触发） */
export function generateQuestionI18n(questionId: number) {
  return request<QuestionOut>({
    url: `/questions/${questionId}/generate-i18n`,
    method: "POST",
  });
}

/** 根据知识点由 AI 生成题目并加入题库（教师端），返回新创建的题目列表 */
export function generateQuestionsByAI(data: { knowledge_point_id: string; count?: number }) {
  return request<QuestionOut[]>({
    url: "/questions/generate-by-ai",
    method: "POST",
    data: { knowledge_point_id: data.knowledge_point_id, count: data.count ?? 1 },
  });
}

