<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="h1">{{ t.pageTitle }}</text>
        <text class="h2" v-if="profile">{{ t.loginPrefix }}{{ profile.username }}（{{ profile.email }}）</text>
      </view>
      <view class="top-actions">
        <view class="language-picker-wrapper" @click.stop>
          <view class="language-selector" @click="showLanguageMenu = !showLanguageMenu">
            <text>{{ languageOptions[languageIndex] }}</text>
            <text class="language-arrow" :class="{ rotated: showLanguageMenu }">▼</text>
          </view>
          <view class="language-menu" v-if="showLanguageMenu">
            <view
              v-for="(lang, idx) in languageOptions"
              :key="idx"
              class="language-menu-item"
              :class="{ active: idx === languageIndex }"
              @click="selectLanguage(idx)"
            >
              <text>{{ lang }}</text>
            </view>
          </view>
        </view>
        <button class="btn-outline" size="mini" @click="goPractice">{{ t.goPractice }}</button>
        <button class="btn-outline" size="mini" @click="handleLogout">{{ t.logout }}</button>
      </view>
    </view>

    <view class="card">
      <text class="card-title">{{ t.cardTitleEdit }}</text>
      <picker :range="questionTitles" :value="editingIndex" @change="onPickQuestion">
        <view class="picker">
          {{ editingIndex === -1 ? t.newQuestion : t.editPrefix + localizedTitle(questions[editingIndex]) }}
        </view>
      </picker>

      <input
        class="input"
        v-model="form.title"
        :placeholder="t.placeholderTitle"
        :maxlength="-1"
      />
      <textarea
        class="textarea"
        v-model="form.content"
        :placeholder="t.placeholderContent"
        auto-height
        :maxlength="-1"
      />
      <textarea
        class="textarea"
        v-model="form.correct_sql"
        :placeholder="t.placeholderCorrectSql"
        auto-height
        :maxlength="-1"
      />
      <text class="form-hint">{{ t.formHint }}</text>

      <view class="row">
        <button class="btn" :loading="saving" @click="handleSave">
          {{ editingIndex === -1 ? t.createQuestion : t.saveChanges }}
        </button>
        <button class="btn-outline" v-if="editingIndex !== -1" :loading="i18nGenerating" @click="handleGenerateI18n">
          {{ i18nGenerating ? t.i18nGenerating : t.i18nGenerate }}
        </button>
        <button class="btn-danger" v-if="editingIndex !== -1" :loading="saving" @click="handleDelete">
          {{ t.deleteCurrent }}
        </button>
      </view>
    </view>

    <view class="card">
      <text class="card-title">{{ t.cardTitleAIGen }}</text>
      <text class="card-desc">{{ t.cardDescAIGen }}</text>
      <view class="row row-ai-gen">
        <!-- 先选大板块：DDL / DML / DQL / Joins / 高级语法 / 函数等 -->
        <picker
          :range="knowledgeCategoryLabels"
          :value="selectedCategoryIndex"
          @change="onPickKnowledgeCategory"
        >
          <view class="picker">
            {{ knowledgeCategoryLabels[selectedCategoryIndex] || t.selectKnowledgePoint }}
          </view>
        </picker>
        <!-- 再在当前板块下选择具体知识点 -->
        <picker
          :range="knowledgePointLabels"
          :value="selectedKpIndex"
          @change="onPickKnowledgePoint"
        >
          <view class="picker">
            {{ knowledgePointLabels[selectedKpIndex] || t.selectKnowledgePoint }}
          </view>
        </picker>
        <view class="gen-count-wrap">
          <text class="gen-count-label">{{ t.genCountLabel }}</text>
          <input class="input gen-count-input" type="number" v-model.number="aiGenCount" min="1" max="5" />
        </view>
        <button
          class="btn btn-ai-gen"
          :loading="aiGenerating"
          :disabled="!knowledgePoints.length || aiGenerating"
          @click="handleGenerateByAI"
        >
          {{ aiGenerating ? t.generating : t.aiGenBtn }}
        </button>
      </view>
    </view>

    <view class="card">
      <text class="card-title">{{ t.listTitlePrefix }}{{ questions.length }}{{ t.listTitleSuffix }}</text>
      <view v-if="!questions.length" class="empty">{{ t.emptyList }}</view>
      <view v-for="(q, index) in questions" :key="q.id" class="item" @click="selectQuestion(q)">
        <view class="item-header">
          <text class="question-id">{{ t.questionIdPrefix }}{{ index + 1 }}</text>
          <text class="difficulty-badge" :class="`difficulty-${q.difficulty}`">
            {{ t.difficultyLabel }}{{ q.difficulty }}
          </text>
        </view>
        <text class="name">{{ localizedTitle(q) }}</text>
        <text class="content">{{ localizedContent(q).length > 100 ? localizedContent(q).substring(0, 100) + '...' : localizedContent(q) }}</text>
        <view class="item-footer">
          <text class="edit-hint">{{ t.editHint }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { getProfile, logout, type UserSchema } from "@/api/auth";
import { createQuestion, deleteQuestion, getQuestions, getQuestion, updateQuestion, getKnowledgePoints, generateQuestionsByAI, generateQuestionI18n, type QuestionOut, type KnowledgePoint } from "@/api/questions";
import { ensureAuthed, requireTeacher } from "@/utils/auth";

const languageOptions = ["简体中文", "English", "繁體中文"];
const languageIndex = ref(0);
const showLanguageMenu = ref(false);

const UI_STRINGS = [
  {
    navTitle: "题目管理",
    pageTitle: "题目管理（教师端）",
    loginPrefix: "当前登录：",
    goPractice: "学生练习页",
    logout: "退出登录",
    cardTitleEdit: "新建 / 编辑题目",
    newQuestion: "新建题目",
    editPrefix: "编辑：",
    placeholderTitle: "题目标题",
    placeholderContent: "题目内容描述",
    placeholderCorrectSql: "标准答案 SQL（将不会在学生端展示）",
    formHint: "难度、限时由系统根据题目与标准答案自动推断，无需填写。",
    createQuestion: "创建题目",
    saveChanges: "保存修改",
    deleteCurrent: "删除当前题目",
    cardTitleAIGen: "按知识点 AI 生成题目",
    cardDescAIGen: "选择 SQL 知识点，由 AI 生成对应练习题并加入题库",
    selectKnowledgePoint: "请选择知识点",
    genCountLabel: "生成数量",
    generating: "生成中...",
    aiGenBtn: "AI 生成题目",
    listTitlePrefix: "现有题目列表（共 ",
    listTitleSuffix: " 题）",
    emptyList: "暂无题目，请先创建。",
    questionIdPrefix: "题目 ID: ",
    difficultyLabel: "难度 ",
    editHint: "点击查看详情并编辑",
    noKp: "暂无知识点",
    genSuccess: "已生成 {n} 道题目",
    genFail: "未生成题目，请重试",
    genError: "生成失败",
    fillComplete: "请把题目信息填写完整",
    createSuccess: "创建成功",
    saveSuccess: "保存成功",
    confirmDelete: "确认删除",
    deleteConfirmContent: "确定要删除题目「{title}」吗？此操作不可恢复。",
    deleted: "已删除",
    i18nGenerate: "补全多语言",
    i18nGenerating: "生成中...",
    i18nSuccess: "已补全多语言题面",
  },
  {
    navTitle: "Questions",
    pageTitle: "Question Management (Teacher)",
    loginPrefix: "Logged in: ",
    goPractice: "Student Practice",
    logout: "Logout",
    cardTitleEdit: "New / Edit Question",
    newQuestion: "New question",
    editPrefix: "Edit: ",
    placeholderTitle: "Question title",
    placeholderContent: "Question description",
    placeholderCorrectSql: "Correct SQL (hidden from students)",
    formHint: "Difficulty and time limit are auto-inferred from the question and correct SQL.",
    createQuestion: "Create question",
    saveChanges: "Save changes",
    deleteCurrent: "Delete current",
    cardTitleAIGen: "AI generate by topic",
    cardDescAIGen: "Select an SQL topic to generate practice questions",
    selectKnowledgePoint: "Select topic",
    genCountLabel: "Count",
    generating: "Generating...",
    aiGenBtn: "AI generate",
    listTitlePrefix: "Question list (",
    listTitleSuffix: " total)",
    emptyList: "No questions yet. Create one first.",
    questionIdPrefix: "ID: ",
    difficultyLabel: "Difficulty ",
    editHint: "Tap to view and edit",
    noKp: "No topics available",
    genSuccess: "Generated {n} question(s)",
    genFail: "None generated, please retry",
    genError: "Generation failed",
    fillComplete: "Please fill in title, content and correct SQL",
    createSuccess: "Created",
    saveSuccess: "Saved",
    confirmDelete: "Confirm delete",
    deleteConfirmContent: "Delete question 「{title}」? This cannot be undone.",
    deleted: "Deleted",
    i18nGenerate: "Generate i18n",
    i18nGenerating: "Generating...",
    i18nSuccess: "i18n generated",
  },
  {
    navTitle: "題目管理",
    pageTitle: "題目管理（教師端）",
    loginPrefix: "當前登錄：",
    goPractice: "學生練習頁",
    logout: "退出登錄",
    cardTitleEdit: "新建 / 編輯題目",
    newQuestion: "新建題目",
    editPrefix: "編輯：",
    placeholderTitle: "題目標題",
    placeholderContent: "題目內容描述",
    placeholderCorrectSql: "標準答案 SQL（將不會在學生端展示）",
    formHint: "難度、限時由系統根據題目與標準答案自動推斷，無需填寫。",
    createQuestion: "創建題目",
    saveChanges: "保存修改",
    deleteCurrent: "刪除當前題目",
    cardTitleAIGen: "按知識點 AI 生成題目",
    cardDescAIGen: "選擇 SQL 知識點，由 AI 生成對應練習題並加入題庫",
    selectKnowledgePoint: "請選擇知識點",
    genCountLabel: "生成數量",
    generating: "生成中...",
    aiGenBtn: "AI 生成題目",
    listTitlePrefix: "現有題目列表（共 ",
    listTitleSuffix: " 題）",
    emptyList: "暫無題目，請先創建。",
    questionIdPrefix: "題目 ID: ",
    difficultyLabel: "難度 ",
    editHint: "點擊查看詳情並編輯",
    noKp: "暫無知識點",
    genSuccess: "已生成 {n} 道題目",
    genFail: "未生成題目，請重試",
    genError: "生成失敗",
    fillComplete: "請把題目信息填寫完整",
    createSuccess: "創建成功",
    saveSuccess: "保存成功",
    confirmDelete: "確認刪除",
    deleteConfirmContent: "確定要刪除題目「{title}」嗎？此操作不可恢復。",
    deleted: "已刪除",
    i18nGenerate: "補全多語言",
    i18nGenerating: "生成中...",
    i18nSuccess: "已補全多語言題面",
  },
] as const;

const t = computed(() => UI_STRINGS[languageIndex.value] ?? UI_STRINGS[0]);

const syncNavTitle = () => {
  try {
    uni.setNavigationBarTitle({ title: t.value.navTitle });
  } catch {
    // ignore
  }
};

const selectLanguage = (index: number) => {
  if (index >= 0 && index < languageOptions.length) {
    languageIndex.value = index;
    showLanguageMenu.value = false;
    const langMap: Record<string, string> = { "简体中文": "zh-CN", "English": "en", "繁體中文": "zh-TW" };
    uni.setStorageSync("ai_language", langMap[languageOptions[index]] || "zh-CN");
    syncNavTitle();
  }
};

onMounted(() => {
  const saved = uni.getStorageSync("ai_language") || "zh-CN";
  const langMap: Record<string, number> = { "zh-CN": 0, "en": 1, "zh-TW": 2 };
  const idx = langMap[saved];
  if (idx !== undefined) languageIndex.value = idx;
  syncNavTitle();
});

const profile = ref<UserSchema | null>(null);
const questions = ref<QuestionOut[]>([]);
const editingIndex = ref(-1);
const saving = ref(false);
const i18nGenerating = ref(false);

const knowledgePoints = ref<KnowledgePoint[]>([]);
const selectedCategoryIndex = ref(0); // 大板块索引：DDL/DML/DQL/Joins/Advanced/Functions
const selectedKpIndex = ref(0);       // 当前板块下的小知识点索引
const aiGenCount = ref(1);
const aiGenerating = ref(false);
const langCodeMap: Record<string, string> = { "简体中文": "zh-CN", "English": "en", "繁體中文": "zh-TW" };
const currentLangCode = computed(() => langCodeMap[languageOptions[languageIndex.value]] || "zh-CN");
const pickKpText = (kp: KnowledgePoint, key: "name" | "level" | "description") => {
  const lang = currentLangCode.value;
  const i18nKey = `${key}_i18n` as const;
  const dict = (kp as any)?.[i18nKey] as Record<string, string> | undefined;
  return (dict && dict[lang]) || (kp as any)?.[key] || "";
};

// 知识点大板块枚举
type KpCategoryKey = "ddl" | "dml" | "dql" | "joins" | "advanced" | "functions";

// 根据知识点 id 粗略归类到不同大板块（DDL/DML/DQL/Joins/高级语法/函数等）
const classifyKnowledgePoint = (kp: KnowledgePoint): KpCategoryKey => {
  const id = kp.id || "";
  if (id.startsWith("ddl-")) return "ddl";
  if (id.startsWith("dml-")) return "dml";
  if (
    id.startsWith("agg-") ||
    id === "group-by" ||
    id === "having" ||
    id.startsWith("join-") ||
    id === "union"
  ) {
    return "joins";
  }
  if (id === "arithmetic" || id === "case") {
    return "functions";
  }
  if (
    id.startsWith("window-") ||
    id === "cte" ||
    id === "complex-join" ||
    id === "null-handling" ||
    id.startsWith("subquery-")
  ) {
    return "advanced";
  }
  // 默认视为查询类（DQL）
  return "dql";
};

// 不同语言下的大板块显示文案
const categoryLabelMap: Record<
  KpCategoryKey,
  { "zh-CN": string; en: string; "zh-TW": string }
> = {
  ddl: {
    "zh-CN": "DDL（数据定义语言）",
    en: "DDL (Data Definition)",
    "zh-TW": "DDL（資料定義語言）",
  },
  dml: {
    "zh-CN": "DML（数据操作语言）",
    en: "DML (Data Manipulation)",
    "zh-TW": "DML（資料操作語言）",
  },
  dql: {
    "zh-CN": "DQL（数据查询语言）",
    en: "DQL (Data Query)",
    "zh-TW": "DQL（資料查詢語言）",
  },
  joins: {
    "zh-CN": "聚合与连接（Joins）",
    en: "Aggregations & Joins",
    "zh-TW": "聚合與連接（Joins）",
  },
  advanced: {
    "zh-CN": "进阶结构化语法",
    en: "Advanced SQL structures",
    "zh-TW": "進階結構化語法",
  },
  functions: {
    "zh-CN": "函数与表达式",
    en: "Functions & Expressions",
    "zh-TW": "函數與運算式",
  },
};

// 将所有知识点按大板块分组，并按固定顺序输出
const groupedKnowledgePoints = computed(() => {
  const groups: Record<KpCategoryKey, KnowledgePoint[]> = {
    ddl: [],
    dml: [],
    dql: [],
    joins: [],
    advanced: [],
    functions: [],
  };
  for (const kp of knowledgePoints.value) {
    const key = classifyKnowledgePoint(kp);
    groups[key].push(kp);
  }
  const lang = currentLangCode.value as "zh-CN" | "en" | "zh-TW";
  const order: KpCategoryKey[] = ["ddl", "dml", "dql", "joins", "advanced", "functions"];
  return order
    .map((key) => ({
      key,
      label: categoryLabelMap[key][lang],
      items: groups[key],
    }))
    .filter((g) => g.items.length > 0);
});

// 当前选中的大板块
const currentCategory = computed(() => {
  const groups = groupedKnowledgePoints.value;
  if (!groups.length) return null;
  const idx = Math.min(
    Math.max(selectedCategoryIndex.value, 0),
    groups.length - 1
  );
  return groups[idx];
});

// 大板块 picker 的文本
const knowledgeCategoryLabels = computed(() =>
  groupedKnowledgePoints.value.map((g) => g.label)
);

// 当前板块下的小知识点 picker 文本
const knowledgePointLabels = computed(() => {
  const cat = currentCategory.value;
  if (!cat) return [];
  return cat.items.map(
    (kp) => `${pickKpText(kp, "level")} · ${pickKpText(kp, "name")}`
  );
});

const localizedTitle = (q: QuestionOut | null | undefined) => {
  if (!q) return "";
  const lang = currentLangCode.value;
  if (lang === "en") return q.title_en || t.value.i18nGenerating;
  if (lang === "zh-TW") return q.title_zh_tw || t.value.i18nGenerating;
  return q.title;
};
const localizedContent = (q: QuestionOut | null | undefined) => {
  if (!q) return "";
  const lang = currentLangCode.value;
  if (lang === "en") return q.content_en || "";
  if (lang === "zh-TW") return q.content_zh_tw || "";
  return q.content;
};

const questionTitles = computed(() => [t.value.newQuestion].concat(questions.value.map((q) => localizedTitle(q))));

const form = reactive<{
  id: number;
  title: string;
  content: string;
  difficulty: number | null;
  correct_sql: string;
  time_limit_seconds: number | null;
}>({
  id: 0,
  title: "",
  content: "",
  difficulty: null,
  correct_sql: "",
  time_limit_seconds: null,
});

// ensureAuthed 已从 @/utils/auth 导入

const loadData = async () => {
  if (!ensureAuthed()) return;
  try {
    profile.value = await getProfile();
    if (!requireTeacher(profile.value)) {
      return;
    }
  } catch (error) {
    console.error("加载用户信息失败:", error);
    if (!uni.getStorageSync("token")) {
      uni.reLaunch({ url: "/pages/login/index" });
      return;
    }
  }
  
  // 加载知识点（教师端按知识点生成题目）
  try {
    const kpList = await getKnowledgePoints();
    knowledgePoints.value = Array.isArray(kpList) ? kpList : [];
    // 重新加载时重置大板块与小知识点索引
    selectedCategoryIndex.value = 0;
    selectedKpIndex.value = 0;
  } catch (e) {
    console.warn("加载知识点失败:", e);
    knowledgePoints.value = [];
  }

  // 加载题目列表
  try {
    // 一次性拉取尽可能多的题目，依赖后端分页上限（当前默认 1000）
    const result = await getQuestions({ skip: 0, limit: 1000 });
    if (Array.isArray(result)) {
      questions.value = result;
      console.log("加载题目成功，共", questions.value.length, "题");
    } else {
      console.warn("题目列表返回格式异常:", result);
      questions.value = [];
    }
  } catch (error: any) {
    console.error("加载题目列表失败:", error);
    
    // 正确提取错误信息
    let errorMsg = "";
    if (error?.data?.detail) {
      // FastAPI 返回的错误格式
      const detail = error.data.detail;
      if (Array.isArray(detail)) {
        // FastAPI 验证错误返回数组格式，提取第一个错误信息
        const firstError = detail[0];
        if (firstError?.msg) {
          errorMsg = firstError.msg;
        } else {
          errorMsg = JSON.stringify(detail);
        }
      } else if (typeof detail === "string") {
        errorMsg = detail;
      } else {
        errorMsg = JSON.stringify(detail);
      }
    } else if (error?.data?.message) {
      errorMsg = error.data.message;
    } else if (error?.message) {
      errorMsg = error.message;
    } else if (error?.detail) {
      errorMsg = typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail);
    } else if (error?.statusCode) {
      // 网络错误或HTTP错误
      errorMsg = `请求失败 (状态码: ${error.statusCode})`;
    } else if (typeof error === "string") {
      errorMsg = error;
    } else {
      // 尝试序列化整个错误对象
      try {
        errorMsg = JSON.stringify(error);
      } catch {
        errorMsg = "未知错误";
      }
    }
    
    // 只有在真正的错误时才显示提示（排除空列表、404等正常情况）
    if (errorMsg && !errorMsg.includes("404") && !errorMsg.includes("空") && !errorMsg.includes("Not Found")) {
      uni.showToast({ 
        title: `加载题目列表失败: ${errorMsg}`, 
        icon: "none", 
        duration: 3000 
      });
    }
    
    // 确保questions是数组，避免后续错误
    questions.value = [];
  }
};

onShow(() => {
  loadData();
});

const resetForm = () => {
  form.id = 0;
  form.title = "";
  form.content = "";
  form.difficulty = null;
  form.correct_sql = "";
  form.time_limit_seconds = null;
};

const onPickQuestion = (e: any) => {
  const idx = Number(e?.detail?.value || 0) - 1; // 因为 picker 第一个是“新建题目”
  if (idx < 0) {
    editingIndex.value = -1;
    resetForm();
    return;
  }
  selectQuestionByIndex(idx);
};

const onPickKnowledgeCategory = (e: any) => {
  const idx = Number(e?.detail?.value ?? 0);
  if (idx >= 0 && idx < groupedKnowledgePoints.value.length) {
    selectedCategoryIndex.value = idx;
    // 切换大板块时，小知识点默认选第一个
    selectedKpIndex.value = 0;
  }
};

const onPickKnowledgePoint = (e: any) => {
  const cat = currentCategory.value;
  if (!cat) return;
  const idx = Number(e?.detail?.value ?? 0);
  if (idx >= 0 && idx < cat.items.length) {
    selectedKpIndex.value = idx;
  }
};

const handleGenerateByAI = async () => {
  const cat = currentCategory.value;
  if (!cat || !cat.items.length) {
    uni.showToast({ title: t.value.noKp, icon: "none" });
    return;
  }
  const kp = cat.items[selectedKpIndex.value];
  if (!kp) return;
  const count = Math.max(1, Math.min(5, Number(aiGenCount.value) || 1));
  aiGenerating.value = true;
  try {
    const created = await generateQuestionsByAI({
      knowledge_point_id: kp.id,
      count,
    });
    const n = Array.isArray(created) ? created.length : 0;
    if (n > 0) {
      questions.value = await getQuestions({ skip: 0, limit: 1000 });
      uni.showToast({ title: t.value.genSuccess.replace("{n}", String(n)), icon: "success", duration: 2000 });
    } else {
      uni.showToast({ title: t.value.genFail, icon: "none" });
    }
  } catch (e: any) {
    const msg = e?.data?.detail || e?.message || t.value.genError;
    uni.showToast({ title: typeof msg === "string" ? msg : t.value.genError, icon: "none", duration: 2500 });
  } finally {
    aiGenerating.value = false;
  }
};

const selectQuestion = async (q: QuestionOut) => {
  // 找到题目在列表中的索引
  const idx = questions.value.findIndex((item) => item.id === q.id);
  if (idx >= 0) {
    await selectQuestionByIndex(idx);
    // 滚动到编辑区域
    uni.pageScrollTo({
      scrollTop: 0,
      duration: 300,
    });
  }
};

const selectQuestionByIndex = async (idx: number) => {
  editingIndex.value = idx;
  const q = questions.value[idx];
  
  // 从服务器重新获取完整题目信息（确保获取到最新的correct_sql）
  try {
    const fullQuestion = await getQuestion(q.id);
    form.id = fullQuestion.id;
    form.title = fullQuestion.title;
    form.content = fullQuestion.content;
    form.difficulty = fullQuestion.difficulty ?? null;
    form.correct_sql = fullQuestion.correct_sql;
    form.time_limit_seconds = fullQuestion.time_limit_seconds ?? null;
    // 更新列表中的题目信息
    questions.value.splice(idx, 1, fullQuestion);
  } catch (error) {
    // 如果获取失败，使用列表中的数据
    form.id = q.id;
    form.title = q.title;
    form.content = q.content;
    form.difficulty = q.difficulty ?? null;
    form.correct_sql = q.correct_sql;
    form.time_limit_seconds = q.time_limit_seconds ?? null;
  }
};

const handleSave = async () => {
  if (!form.title || !form.content || !form.correct_sql) {
    return uni.showToast({ title: t.value.fillComplete, icon: "none" });
  }
  saving.value = true;
  try {
    if (editingIndex.value === -1) {
      const created = await createQuestion({
        title: form.title,
        content: form.content,
        correct_sql: form.correct_sql,
        difficulty: undefined,
        time_limit_seconds: undefined,
        required_output_columns: undefined,
      });
      uni.showToast({ title: t.value.createSuccess, icon: "success" });
      // 重新加载题目列表，确保顺序与后端一致，新题可见
      await loadData();
      resetForm();
      editingIndex.value = -1;
    } else {
      const current = questions.value[editingIndex.value];
      const updated = await updateQuestion(current.id, {
        title: form.title,
        content: form.content,
        correct_sql: form.correct_sql,
        difficulty: undefined,
        time_limit_seconds: undefined,
        required_output_columns: undefined,
      });
      uni.showToast({ title: t.value.saveSuccess, icon: "success" });
      // 重新加载题目列表，并保持当前编辑题目高亮
      await loadData();
      const idx = questions.value.findIndex((q) => q.id === updated.id);
      editingIndex.value = idx >= 0 ? idx : -1;
      form.correct_sql = updated.correct_sql;
    }
  } finally {
    saving.value = false;
  }
};

const handleDelete = async () => {
  if (editingIndex.value === -1) return;
  const current = questions.value[editingIndex.value];
  const content = t.value.deleteConfirmContent.replace("{title}", current.title);
  uni.showModal({
    title: t.value.confirmDelete,
    content,
    success: async (res) => {
      if (!res.confirm) return;
      saving.value = true;
      try {
        await deleteQuestion(current.id);
        uni.showToast({ title: t.value.deleted, icon: "success" });
        // 删除后重新加载题目列表，重置表单状态
        await loadData();
        editingIndex.value = -1;
        resetForm();
      } finally {
        saving.value = false;
      }
    },
  });
};

const handleGenerateI18n = async () => {
  if (editingIndex.value === -1) return;
  const current = questions.value[editingIndex.value];
  if (!current) return;
  i18nGenerating.value = true;
  try {
    const updated = await generateQuestionI18n(current.id);
    questions.value.splice(editingIndex.value, 1, updated);
    // 同步表单（避免标题/内容切换语言后仍显示旧值）
    form.id = updated.id;
    form.title = updated.title;
    form.content = updated.content;
    form.correct_sql = updated.correct_sql;
    uni.showToast({ title: t.value.i18nSuccess, icon: "success", duration: 1500 });
  } finally {
    i18nGenerating.value = false;
  }
};

const goPractice = () => {
  uni.reLaunch({ url: "/pages/index/index" });
};

const handleLogout = async () => {
  try {
    await logout();
  } catch {
    // ignore
  } finally {
    uni.removeStorageSync("token");
    uni.removeStorageSync("refresh_token");
    uni.removeStorageSync("user");
    uni.reLaunch({ url: "/pages/login/index" });
  }
};
</script>

<style>
.page {
  padding: 18px 14px 40px;
  background: #f6f7fb;
  min-height: 100vh;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.top-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.language-picker-wrapper {
  position: relative;
}
.language-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  font-size: 12px;
  color: #6b7280;
}
.language-arrow {
  font-size: 10px;
  color: #9ca3af;
  transition: transform 0.2s;
}
.language-arrow.rotated {
  transform: rotate(180deg);
}
.language-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 100;
  min-width: 120px;
}
.language-menu-item {
  padding: 10px 16px;
  font-size: 13px;
  color: #111827;
}
.language-menu-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}
.h1 {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}
.h2 {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}
.card {
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  margin-top: 12px;
  box-shadow: 0 6px 18px rgba(17, 24, 39, 0.06);
}
.card-title {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 10px;
}
.card-desc {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 12px;
}
.row-ai-gen {
  flex-wrap: wrap;
  align-items: center;
}
.row-ai-gen .picker {
  flex: 1;
  min-width: 140px;
  margin-bottom: 0;
}
.gen-count-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}
.gen-count-label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}
.gen-count-input {
  width: 56px;
  margin-bottom: 0;
  text-align: center;
}
.btn-ai-gen {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  color: #fff;
  white-space: nowrap;
}
.picker {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  color: #111827;
  margin-bottom: 12px;
}
.input {
  border: 1px solid #e5e7eb;
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 10px;
  background-color: #f8f8f8;
  font-size: 14px;
}
.form-hint {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  margin-bottom: 4px;
}
.textarea {
  width: 100%;
  min-height: 140px;
  max-height: 65vh;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  font-size: 13px;
  margin-bottom: 10px;
  box-sizing: border-box;
  overflow-y: auto;
}
.row {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}
.btn {
  flex: 1;
  background: #2563eb;
  color: #fff;
  border-radius: 999px;
  font-size: 14px;
}
.btn-outline {
  background: #fff;
  color: #111827;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  font-size: 14px;
}
.btn-danger {
  flex: 1;
  background: #dc2626;
  color: #fff;
  border-radius: 999px;
  font-size: 14px;
}
.item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}
.item:active {
  background: #f3f4f6;
  transform: scale(0.98);
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.question-id {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
  font-family: ui-monospace, monospace;
}
.difficulty-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: #e5e7eb;
  color: #6b7280;
}
.difficulty-1 { background: #d1fae5; color: #065f46; }
.difficulty-2 { background: #bbf7d0; color: #166534; }
.difficulty-3 { background: #fef3c7; color: #92400e; }
.difficulty-4 { background: #fde68a; color: #b45309; }
.difficulty-5 { background: #fed7aa; color: #c2410c; }
.difficulty-6 { background: #fecaca; color: #991b1b; }
.difficulty-7 { background: #fbcfe8; color: #9f1239; }
.difficulty-8 { background: #e9d5ff; color: #6b21a8; }
.difficulty-9 { background: #c4b5fd; color: #5b21b6; }
.difficulty-10 { background: #a78bfa; color: #4c1d95; }
.name {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 6px;
}
.content {
  display: block;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 8px;
}
.item-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
}
.edit-hint {
  font-size: 11px;
  color: #9ca3af;
}
.empty {
  font-size: 13px;
  color: #9ca3af;
}
</style>

