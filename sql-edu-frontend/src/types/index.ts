/**
 * 统一类型定义文件
 * 集中管理前端所有 TypeScript 类型
 */

// ==================== 通用响应 ====================

export type ResponseOut = {
  result: "success" | "failure";
  detail?: string | null;
};

// ==================== 用户相关 ====================

export type UserSchema = {
  id: number;
  email: string;
  username: string;
  role: "student" | "teacher";
  /** 当前等级（学生端展示） */
  level?: number;
  /** 当前等级内经验（进度条当前值） */
  experience_in_level?: number;
  /** 升到下一级所需经验（进度条上限） */
  xp_to_next_level?: number;
};

export type LoginOut = {
  user: UserSchema;
  token: string;
  refresh_token: string;
};

// ==================== 题目相关 ====================

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

// ==================== AI 判题相关 ====================

export type SqlHintResponse = {
  hint: any;
};

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

// ==================== 对话相关 ====================

export type ChatMessage = {
  id: number;
  role: "system" | "user" | "assistant";
  content: string;
  created_at: string;
};
