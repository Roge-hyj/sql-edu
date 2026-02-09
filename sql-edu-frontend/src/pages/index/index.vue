<template>
  <view class="page">
    <view class="topbar">
      <view class="topbar-left">
        <text class="h1">{{ t.pageTitle }}</text>
        <text class="h2" v-if="profile">{{ t.currentUser }}{{ profile.username }}（{{ profile.email }}）</text>
        <view v-if="profile && (profile.role === 'student' || profile.level)" class="level-bar-wrap">
          <text class="level-label">Lv.{{ profile.level ?? 1 }}</text>
          <view class="xp-bar-bg">
            <view
              class="xp-bar-fill"
              :style="{ width: xpProgressPercent + '%' }"
            />
          </view>
          <text class="xp-text">{{ profile.experience_in_level ?? 0 }}/{{ profile.xp_to_next_level ?? 100 }}</text>
        </view>
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
        <button class="btn-outline" size="mini" @click="goTeacher">{{ t.questionManage }}</button>
        <button class="btn-outline" size="mini" @click="handleLogout">{{ t.logout }}</button>
      </view>
    </view>

    <view class="card">
      <text class="card-title">{{ t.selectQuestion }}</text>
      <picker :range="questionTitles" :value="selectedIndex" @change="onPickQuestion">
        <view class="picker">
          {{ currentQuestion ? (overrideQuestion ? `ID ${currentQuestion.id} · ${localizedTitle(currentQuestion)}` : localizedTitle(currentQuestion)) : t.pickQuestion }}
        </view>
      </picker>
      <view class="row row-select">
        <view class="id-input-wrap">
          <text class="id-label">{{ t.questionId }}</text>
          <input
            class="id-input"
            type="number"
            v-model="questionIdInput"
            :placeholder="t.jumpPlaceholder"
            :maxlength="-1"
            @confirm="selectByQuestionId"
          />
        </view>
        <button class="btn-outline btn-small" :disabled="jumpingById" @click="selectByQuestionId">
          {{ jumpingById ? t.jumping : t.jump }}
        </button>
        <button class="btn-outline btn-small" :disabled="!questions.length" @click="randomPick">
          {{ t.randomPick }}
        </button>
      </view>
      <view v-if="currentQuestion" class="question">
        <text class="q-label">{{ t.questionContent }}</text>
        <text class="q-content">{{ localizedContent(displayQuestion ?? currentQuestion) }}</text>
        <view class="q-meta-row">
          <text class="q-meta">{{ t.difficulty }}{{ displayDifficultyText }}</text>
          <text class="q-meta" v-if="suggestedTimeText">{{ suggestedTimeText }}</text>
        </view>
        <view class="challenge-row" v-if="challengeTimeSeconds && !challengeActive">
          <button class="btn-challenge" size="mini" @click="startChallenge">{{ t.challenge }}（{{ challengeTimeLabel }}）</button>
        </view>
        <view class="challenge-row challenge-active" v-if="challengeActive">
          <text class="challenge-timer">{{ t.challengeRemain }} {{ formatChallengeRemain }}</text>
          <text class="challenge-hint">{{ t.challengeHint }}</text>
        </view>
        <view v-if="questionDetailLoading && !schemaPreviewTables.length" class="schema-preview-loading">
          <text class="schema-loading-text">{{ t.schemaLoading }}</text>
        </view>
        <view v-else-if="schemaPreviewTables.length" class="schema-preview-wrap">
          <text class="schema-preview-title">{{ t.schemaTitle }}</text>
          <view v-for="(tbl, ti) in schemaPreviewTables" :key="ti" class="schema-table-card">
            <text class="schema-table-name">{{ t.tableName }}{{ tbl.name }}</text>
            <scroll-view class="schema-table-scroll" scroll-x>
              <view class="schema-table">
                <view class="schema-row schema-header">
                  <view v-for="(col, ci) in tbl.columns" :key="ci" class="schema-cell schema-cell-header">{{ col }}</view>
                </view>
                <view
                  v-for="(row, ri) in tbl.rows"
                  :key="ri"
                  class="schema-row"
                  :class="'schema-row-' + (ri % 5)"
                >
                  <view v-for="(col, ci) in tbl.columns" :key="ci" class="schema-cell">
                    {{ row[col] != null ? String(row[col]) : 'NULL' }}
                  </view>
                </view>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>
    </view>

    <view class="card">
      <text class="card-title">{{ t.submitSql }}</text>
      <textarea
        class="textarea textarea-sql"
        v-model="studentSql"
        @input="saveStudentSql"
        :placeholder="t.sqlPlaceholder"
        :maxlength="-1"
        auto-height
      />
      <view class="row">
        <button class="btn" :loading="submitting" @click="handleCheckSql" :disabled="!currentQuestion || submitting">
          <text v-if="!submitting">{{ t.judgeBtn }}</text>
          <text v-else>{{ t.judgeThinking }}</text>
        </button>
        <button class="btn-outline" :disabled="!currentQuestion" @click="loadChat">{{ t.refreshChat }}</button>
      </view>
    </view>

    <view class="card" v-if="currentQuestion">
      <view class="card-header">
        <text class="card-title">{{ t.chatTitle }}</text>
        <view class="card-header-actions">
          <button class="btn-outline btn-clear-chat" size="mini" :disabled="!chatMessages.length || clearingChat" @click="handleClearChat">
            {{ clearingChat ? t.clearing : t.clearHistory }}
          </button>
        </view>
      </view>
      <scroll-view class="chat" scroll-y :scroll-into-view="scrollIntoView">
        <view v-if="!chatMessages.length" class="chat-empty">
          {{ t.chatEmpty }}
        </view>
        <view
          v-for="m in chatMessages"
          :key="m.id"
          :id="`msg-${m.id}`"
          class="msg"
          :class="m.role"
        >
          <view class="msg-meta">
            <text class="msg-role" v-if="m.role === 'assistant'">{{ t.roleAiTeacher }}</text>
            <text class="msg-role" v-else-if="m.role === 'user'">{{ t.roleMe }}</text>
            <text class="msg-role" v-else>{{ t.roleSystem }}</text>
            <text class="msg-time">{{ formatMessageTime(m.created_at) }}</text>
          </view>
          <view class="bubble">
            <rich-text class="msg-text" :nodes="parseMarkdown(m.content)"></rich-text>
          </view>
        </view>
      </scroll-view>

      <view class="chat-input">
        <view class="chat-input-wrapper">
          <textarea 
            class="chat-textarea" 
            v-model="chatInput" 
            :placeholder="t.chatPlaceholder"
            :auto-height="true"
            :maxlength="-1"
          />
          <button 
            class="btn-send" 
            :disabled="chatSending || !chatInput.trim()" 
            @click="sendChat"
            :loading="chatSending"
          >
            <text v-if="!chatSending">{{ t.send }}</text>
            <text v-else>{{ t.sending }}</text>
          </button>
        </view>
      </view>
    </view>

    <view class="modal-mask" v-if="showDifficultyModal" @click.self="closeDifficultyModal">
      <view class="modal-box">
        <text class="modal-title">{{ t.ratingTitle }}</text>
        <text class="modal-desc">{{ t.ratingDesc }}</text>
        <view class="rating-row">
          <text
            v-for="n in 10"
            :key="n"
            class="rating-btn"
            :class="{ active: difficultyRating === n }"
            @click="difficultyRating = n"
          >{{ n }}</text>
        </view>
        <view class="modal-actions">
          <button class="btn-outline" size="mini" @click="skipDifficultyFeedback">{{ t.skip }}</button>
          <button class="btn" size="mini" :disabled="difficultyRating === 0" @click="submitDifficultyRating">{{ t.submit }}</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { getProfile, logout, type UserSchema } from "@/api/auth";
import { getQuestions, getQuestion, submitDifficultyFeedback, generateQuestionI18n, type QuestionOut } from "@/api/questions";
import { ensureAuthed, requireTeacher } from "@/utils/auth";
import { checkSql, getChatMessages, chatWithTeacher, clearChatMessages, type ChatMessage, type SqlCheckResponse } from "@/api/ai";

const profile = ref<UserSchema | null>(null);

const questions = ref<QuestionOut[]>([]);
const selectedIndex = ref(0);
/** 通过输入题目ID跳转时拉取的题目（可能不在当前列表中） */
const overrideQuestion = ref<QuestionOut | null>(null);
const currentQuestion = computed<QuestionOut | null>(() => {
  if (overrideQuestion.value) return overrideQuestion.value;
  if (!questions.value.length) return null;
  return questions.value[selectedIndex.value] || null;
});
const activeLangCode = computed(() => currentLanguage.value || "zh-CN");
const localizedTitle = (q: QuestionOut | null | undefined) => {
  if (!q) return "";
  const lang = activeLangCode.value;
  if (lang === "en") return q.title_en || t.value.translationPendingTitle;
  if (lang === "zh-TW") return q.title_zh_tw || t.value.translationPendingTitle;
  return q.title;
};
const localizedContent = (q: QuestionOut | null | undefined) => {
  if (!q) return "";
  const lang = activeLangCode.value;
  if (lang === "en") return q.content_en || t.value.translationPendingContent;
  if (lang === "zh-TW") return q.content_zh_tw || t.value.translationPendingContent;
  return q.content;
};
const questionTitles = computed(() => questions.value.map((q) => localizedTitle(q)));

/** 当前题目的详情（含表结构预览），选题时拉取以保证每道题都显示图表参考 */
const questionDetail = ref<QuestionOut | null>(null);
const questionDetailLoading = ref(false);
/** 展示用题目：优先使用详情（含 schema_preview），保证表结构能显示 */
const displayQuestion = computed<QuestionOut | null>(() => {
  const cur = currentQuestion.value;
  const detail = questionDetail.value;
  if (detail && cur && detail.id === cur.id) return detail;
  return cur;
});

/** 题目ID输入框（用于跳转） */
const questionIdInput = ref("");
const jumpingById = ref(false);

const studentSql = ref("");
const submitting = ref(false);
const checkResult = ref<SqlCheckResponse | null>(null);
const chatMessages = ref<ChatMessage[]>([]);
const chatInput = ref("");
const chatSending = ref(false);
const scrollIntoView = ref("");

// 语言选择
const languageOptions = ["简体中文", "English", "繁體中文"];
const languageMap = {
  "简体中文": "zh-CN",
  "English": "en",
  "繁體中文": "zh-TW"
};
const languageIndex = ref(0);
const showLanguageMenu = ref(false);
const currentLanguage = computed(() => languageMap[languageOptions[languageIndex.value]]);

/** 整页 UI 文案（随语言切换） */
const UI_STRINGS = [
  {
    navTitle: "首页",
    pageTitle: "SQL 智能教学系统（学生端）",
    currentUser: "当前用户：",
    questionManage: "题目管理",
    logout: "退出登录",
    selectQuestion: "选择题目",
    pickQuestion: "请选择题目",
    questionId: "题号",
    jumpPlaceholder: "输入 1、2、3… 跳转",
    jumping: "跳转中...",
    jump: "跳转",
    randomPick: "随机选题",
    questionContent: "题目内容",
    difficulty: "难度：",
    suggestedTime: "建议限时",
    challenge: "限时挑战",
    challengeRemain: "剩余",
    challengeHint: "在限时内提交正确即挑战成功",
    schemaLoading: "正在加载表结构参考…",
    schemaTitle: "相关表结构（示例数据）",
    tableName: "表名：",
    submitSql: "提交 SQL",
    sqlPlaceholder: "请输入 SQL",
    judgeBtn: "判题并获取 AI 提示",
    judgeThinking: "AI 正在思考...",
    refreshChat: "刷新对话",
    chatTitle: "与 AI 教师对话",
    clearing: "清除中...",
    clearHistory: "清除历史对话",
    chatEmpty: "提示：先提交一次 SQL，AI 老师会根据你的结果开始对话。",
    chatPlaceholder: "向 AI 老师追问（例如：我该如何修改 WHERE 条件？）",
    send: "发送",
    sending: "思考中...",
    ratingTitle: "回答正确！请为本题难度打分（1～10）",
    ratingDesc: "1 最简单，10 最难，用于优化题目难度显示",
    skip: "跳过",
    submit: "提交",
    langSwitchedFmt: "已切换为 {lang}",
    suggestedTimeSecFmt: "建议限时 {n} 秒",
    suggestedTimeMinFmt: "建议限时 {n} 分钟",
    translationPendingTitle: "（翻译生成中…）",
    translationPendingContent: "题目翻译生成中，请稍等…",
    timeUp: "时间到",
    randomPickedFmt: "已随机到：{title}",
    roleAiTeacher: "AI 老师",
    roleMe: "我",
    roleSystem: "系统",
    durationSecFmt: "{n} 秒",
    durationMinFmt: "{n} 分钟",
  },
  {
    navTitle: "Home",
    pageTitle: "SQL Learning (Student)",
    currentUser: "User: ",
    questionManage: "Questions",
    logout: "Logout",
    selectQuestion: "Select Question",
    pickQuestion: "Pick a question",
    questionId: "No.",
    jumpPlaceholder: "1, 2, 3…",
    jumping: "Jumping...",
    jump: "Jump",
    randomPick: "Random",
    questionContent: "Question",
    difficulty: "Difficulty: ",
    suggestedTime: "Suggested time",
    challenge: "Timed challenge",
    challengeRemain: "Left",
    challengeHint: "Submit correct SQL in time",
    schemaLoading: "Loading schema…",
    schemaTitle: "Table structure (sample)",
    tableName: "Table: ",
    submitSql: "Submit SQL",
    sqlPlaceholder: "Enter SQL",
    judgeBtn: "Judge & AI hint",
    judgeThinking: "Thinking...",
    refreshChat: "Refresh chat",
    chatTitle: "Chat with AI",
    clearing: "Clearing...",
    clearHistory: "Clear history",
    chatEmpty: "Submit SQL once to start the chat.",
    chatPlaceholder: "Ask a follow-up (e.g. How to fix WHERE?)",
    send: "Send",
    sending: "Thinking...",
    ratingTitle: "Correct! Rate difficulty (1–10)",
    ratingDesc: "1 easiest, 10 hardest",
    skip: "Skip",
    submit: "Submit",
    langSwitchedFmt: "Switched to {lang}",
    suggestedTimeSecFmt: "Suggested: {n}s",
    suggestedTimeMinFmt: "Suggested: {n} min",
    translationPendingTitle: "(Translating...)",
    translationPendingContent: "Generating translation… Please wait.",
    timeUp: "Time is up",
    randomPickedFmt: "Random: {title}",
    roleAiTeacher: "AI Teacher",
    roleMe: "Me",
    roleSystem: "System",
    durationSecFmt: "{n}s",
    durationMinFmt: "{n} min",
  },
  {
    navTitle: "首頁",
    pageTitle: "SQL 智能教學系統（學生端）",
    currentUser: "當前用戶：",
    questionManage: "題目管理",
    logout: "退出登錄",
    selectQuestion: "選擇題目",
    pickQuestion: "請選擇題目",
    questionId: "題號",
    jumpPlaceholder: "輸入 1、2、3… 跳轉",
    jumping: "跳轉中...",
    jump: "跳轉",
    randomPick: "隨機選題",
    questionContent: "題目內容",
    difficulty: "難度：",
    suggestedTime: "建議限時",
    challenge: "限時挑戰",
    challengeRemain: "剩餘",
    challengeHint: "在限時內提交正確即挑戰成功",
    schemaLoading: "正在加載表結構參考…",
    schemaTitle: "相關表結構（示例數據）",
    tableName: "表名：",
    submitSql: "提交 SQL",
    sqlPlaceholder: "請輸入 SQL",
    judgeBtn: "判題並獲取 AI 提示",
    judgeThinking: "AI 正在思考...",
    refreshChat: "刷新對話",
    chatTitle: "與 AI 教師對話",
    clearing: "清除中...",
    clearHistory: "清除歷史對話",
    chatEmpty: "提示：先提交一次 SQL，AI 老師會根據你的結果開始對話。",
    chatPlaceholder: "向 AI 老師追問（例如：我該如何修改 WHERE 條件？）",
    send: "發送",
    sending: "思考中...",
    ratingTitle: "回答正確！請為本題難度打分（1～10）",
    ratingDesc: "1 最簡單，10 最難，用於優化題目難度顯示",
    skip: "跳過",
    submit: "提交",
    langSwitchedFmt: "已切換為 {lang}",
    suggestedTimeSecFmt: "建議限時 {n} 秒",
    suggestedTimeMinFmt: "建議限時 {n} 分鐘",
    translationPendingTitle: "（翻譯生成中…）",
    translationPendingContent: "題目翻譯生成中，請稍等…",
    timeUp: "時間到",
    randomPickedFmt: "已隨機到：{title}",
    roleAiTeacher: "AI 老師",
    roleMe: "我",
    roleSystem: "系統",
    durationSecFmt: "{n} 秒",
    durationMinFmt: "{n} 分鐘",
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

/** 解析 schema_preview JSON，返回表结构数组供展示；每表示例数据最多显示 4 行，有就行 */
const schemaPreviewTables = computed(() => {
  const q = displayQuestion.value;
  const raw = q?.schema_preview;
  if (!raw || typeof raw !== "string") return [];
  try {
    const obj = JSON.parse(raw) as { tables?: Array<{ name: string; columns: string[]; rows: Record<string, unknown>[] }> };
    const tables = obj?.tables;
    if (!Array.isArray(tables)) return [];
    return tables
      .filter(
        (t) =>
          t &&
          typeof t === "object" &&
          typeof t.name === "string" &&
          Array.isArray(t.columns) &&
          Array.isArray(t.rows)
      )
      .map((t) => ({
        name: t.name,
        columns: t.columns,
        rows: (t.rows || []).slice(0, 4),
      }));
  } catch {
    return [];
  }
});

/** 显示难度：优先动态难度，否则教师设置难度 */
const displayDifficultyText = computed(() => {
  const q = displayQuestion.value;
  if (!q) return "";
  const d = q.display_difficulty ?? q.difficulty;
  return typeof d === "number" ? d.toFixed(1) : String(d);
});

/** 建议限时文案（如「建议限时 5 分钟」），完全根据题目难度 */
const suggestedTimeText = computed(() => {
  const q = displayQuestion.value;
  if (!q) return "";
  const sec = q.suggested_time_seconds;
  if (sec == null || sec <= 0) return "";
  if (sec < 60) return t.value.suggestedTimeSecFmt.replace("{n}", String(sec));
  const min = Math.round(sec / 60);
  return t.value.suggestedTimeMinFmt.replace("{n}", String(min));
});

const isTranslationMissingForLang = (q: QuestionOut | null | undefined) => {
  if (!q) return false;
  const lang = activeLangCode.value;
  if (lang === "en") return !(q.title_en && q.content_en);
  if (lang === "zh-TW") return !(q.title_zh_tw && q.content_zh_tw);
  return false;
};

const upsertQuestionInState = (updated: QuestionOut) => {
  const idx = questions.value.findIndex((x) => x.id === updated.id);
  if (idx >= 0) questions.value.splice(idx, 1, updated);
  if (overrideQuestion.value?.id === updated.id) overrideQuestion.value = updated;
  if (questionDetail.value?.id === updated.id) questionDetail.value = updated;
};

const ensureCurrentQuestionI18n = async () => {
  const q = displayQuestion.value ?? currentQuestion.value;
  if (!q) return;
  if (activeLangCode.value === "zh-CN") return;
  if (!isTranslationMissingForLang(q)) return;
  try {
    const updated = await generateQuestionI18n(q.id);
    upsertQuestionInState(updated);
  } catch {
    // ignore: keep showing placeholder
  }
};

watch(
  [displayQuestion, activeLangCode],
  async () => {
    await ensureCurrentQuestionI18n();
  },
  { immediate: true }
);

/** 限时挑战可用秒数，完全根据题目难度（suggested_time_seconds 由后端按难度计算） */
const challengeTimeSeconds = computed(() => {
  const q = displayQuestion.value;
  if (!q) return 0;
  const sec = q.suggested_time_seconds;
  return sec != null && sec > 0 ? sec : 0;
});

const challengeTimeLabel = computed(() => {
  const s = challengeTimeSeconds.value;
  if (s < 60) return t.value.durationSecFmt.replace("{n}", String(s));
  return t.value.durationMinFmt.replace("{n}", String(Math.round(s / 60)));
});

/** 限时挑战：是否进行中、剩余秒数、定时器 */
const challengeActive = ref(false);
const challengeRemainSeconds = ref(0);
let challengeTimerId: ReturnType<typeof setInterval> | null = null;

const formatChallengeRemain = computed(() => {
  const s = challengeRemainSeconds.value;
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
});

const startChallenge = () => {
  const total = challengeTimeSeconds.value;
  if (total <= 0) return;
  if (challengeTimerId) clearInterval(challengeTimerId);
  challengeActive.value = true;
  challengeRemainSeconds.value = total;
  challengeTimerId = setInterval(() => {
    challengeRemainSeconds.value = Math.max(0, challengeRemainSeconds.value - 1);
    if (challengeRemainSeconds.value <= 0 && challengeTimerId) {
      clearInterval(challengeTimerId);
      challengeTimerId = null;
      challengeActive.value = false;
      uni.showToast({ title: t.value.timeUp, icon: "none" });
    }
  }, 1000);
};

/** 正确提交后弹出难度评分 */
const showDifficultyModal = ref(false);
const difficultyRating = ref(0);
const pendingDifficultyQuestionId = ref<number | null>(null);

const closeDifficultyModal = () => {
  showDifficultyModal.value = false;
  difficultyRating.value = 0;
  pendingDifficultyQuestionId.value = null;
};

const skipDifficultyFeedback = () => {
  closeDifficultyModal();
};

const submitDifficultyRating = async () => {
  const qid = pendingDifficultyQuestionId.value;
  if (qid == null || difficultyRating.value < 1 || difficultyRating.value > 10) return;
  try {
    await submitDifficultyFeedback(qid, difficultyRating.value);
    uni.showToast({ title: "难度评分已记录", icon: "success" });
  } catch {
    // request 里会提示
  }
  closeDifficultyModal();
};

/** 经验进度条百分比（当前等级内） */
const xpProgressPercent = computed(() => {
  const p = profile.value;
  if (!p || p.xp_to_next_level == null || p.xp_to_next_level === 0) return 0;
  const cur = p.experience_in_level ?? 0;
  return Math.min(100, Math.round((cur / p.xp_to_next_level) * 100));
});

const selectLanguage = (index: number) => {
  if (index >= 0 && index < languageOptions.length) {
    languageIndex.value = index;
    showLanguageMenu.value = false;
    // 保存语言偏好到本地存储
    uni.setStorageSync("ai_language", currentLanguage.value);
    syncNavTitle();
    uni.showToast({
      title: t.value.langSwitchedFmt.replace("{lang}", languageOptions[index]),
      icon: "success",
      duration: 1500,
    });
  }
};

// 选题时拉取题目详情（含表结构预览），保证每道题都显示图表参考
watch(
  currentQuestion,
  async (q) => {
    questionDetail.value = null;
    if (!q) return;
    // 通过题号跳转时已用 getQuestion 拿到完整详情，直接复用
    if (overrideQuestion.value && overrideQuestion.value.id === q.id) {
      questionDetail.value = overrideQuestion.value;
      return;
    }
    const qid = q.id;
    questionDetailLoading.value = true;
    try {
      const detail = await getQuestion(qid);
      if (currentQuestion.value?.id === qid) questionDetail.value = detail;
    } catch {
      if (currentQuestion.value?.id === qid) questionDetail.value = null;
    } finally {
      questionDetailLoading.value = false;
    }
  },
  { immediate: true }
);

// 保存SQL内容到本地存储（防抖处理，按题目ID分别保存）
let saveSqlTimer: ReturnType<typeof setTimeout> | null = null;
const saveStudentSql = () => {
  if (saveSqlTimer) {
    clearTimeout(saveSqlTimer);
  }
  saveSqlTimer = setTimeout(() => {
    if (studentSql.value && currentQuestion.value) {
      // 按题目ID分别保存SQL代码
      const storageKey = `last_student_sql_${currentQuestion.value.id}`;
      uni.setStorageSync(storageKey, studentSql.value);
      console.log(`已保存题目 ${currentQuestion.value.id} 的SQL代码`);
    }
  }, 500); // 500ms 防抖
};

// ensureAuthed 已从 @/utils/auth 导入

const bootstrap = async () => {
  if (!ensureAuthed()) return;

  try {
    profile.value = await getProfile();
    uni.setStorageSync("user", profile.value);
  } catch {
    // token 无效时 request.ts 会提示并清理 token，这里再兜底跳转
    if (!uni.getStorageSync("token")) {
      uni.reLaunch({ url: "/pages/login/index" });
      return;
    }
  }

  // 一次性拉取尽可能多的题目，依赖后端分页上限（当前默认 1000）
  questions.value = await getQuestions({ skip: 0, limit: 1000 });
  
  // 恢复上次选择的题目（从本地存储）
  const savedQuestionIndex = uni.getStorageSync("last_selected_question_index");
  
  if (questions.value.length) {
    // 恢复题目选择（SQL 输入框不恢复上次内容，始终为空）
    if (savedQuestionIndex !== null && savedQuestionIndex !== undefined) {
      const index = Number(savedQuestionIndex);
      if (index >= 0 && index < questions.value.length) {
        selectedIndex.value = index;
      } else {
        selectedIndex.value = 0;
      }
    } else {
      selectedIndex.value = 0;
    }
    studentSql.value = "";
  }
  
  // 加载语言偏好
  const savedLanguage = uni.getStorageSync("ai_language") || "zh-CN";
  const langKey = Object.keys(languageMap).find(key => languageMap[key] === savedLanguage);
  if (langKey) {
    const index = languageOptions.indexOf(langKey);
    if (index >= 0) {
      languageIndex.value = index;
    }
  }

  syncNavTitle();
};

onShow(() => {
  bootstrap();
});

// 点击外部关闭语言菜单
const handleClickOutside = () => {
  showLanguageMenu.value = false;
};

onMounted(() => {
  // 在uni-app中，可以通过监听页面点击事件来关闭菜单
  // 注意：uni-app的页面点击事件可能需要特殊处理
});

onUnmounted(() => {
  if (challengeTimerId) {
    clearInterval(challengeTimerId);
    challengeTimerId = null;
  }
});

/** 保存当前题目SQL并清空判题/对话状态 */
const saveCurrentAndClearState = () => {
  if (currentQuestion.value && studentSql.value) {
    const storageKey = `last_student_sql_${currentQuestion.value.id}`;
    uni.setStorageSync(storageKey, studentSql.value);
  }
  checkResult.value = null;
  chatMessages.value = [];
  scrollIntoView.value = "";
  showDifficultyModal.value = false;
  pendingDifficultyQuestionId.value = null;
  difficultyRating.value = 0;
  // 切换题目时结束限时挑战
  if (challengeTimerId) {
    clearInterval(challengeTimerId);
    challengeTimerId = null;
  }
  challengeActive.value = false;
  challengeRemainSeconds.value = 0;
};

const onPickQuestion = (e: any) => {
  const newIndex = Number(e?.detail?.value || 0);
  
  saveCurrentAndClearState();
  overrideQuestion.value = null;
  selectedIndex.value = newIndex;
  uni.setStorageSync("last_selected_question_index", selectedIndex.value);
  studentSql.value = "";
  loadChat();
};

/** 通过题号跳转：优先按序号 1、2、3…（当前列表第几题），也可按数据库 ID 拉取 */
const selectByQuestionId = async () => {
  const raw = String(questionIdInput.value || "").trim();
  if (!raw) {
    uni.showToast({ title: "请输入题号", icon: "none" });
    return;
  }
  const num = Number.parseInt(raw, 10);
  if (Number.isNaN(num) || num < 1) {
    uni.showToast({ title: "请输入有效的题号（正整数）", icon: "none" });
    return;
  }

  const total = questions.value.length;

  // 1）按序号跳转：输入 1、2、3… 表示当前列表的第 1、2、3 题
  if (num >= 1 && num <= total) {
    const idx = num - 1;
    saveCurrentAndClearState();
    overrideQuestion.value = null;
    selectedIndex.value = idx;
    uni.setStorageSync("last_selected_question_index", selectedIndex.value);
    studentSql.value = "";
    loadChat();
    questionIdInput.value = "";
    uni.showToast({ title: `已切换到第 ${num} 题`, icon: "success" });
    return;
  }

  // 2）当前列表中是否存在该数据库 ID
  const idxById = questions.value.findIndex((q) => q.id === num);
  if (idxById >= 0) {
    saveCurrentAndClearState();
    overrideQuestion.value = null;
    selectedIndex.value = idxById;
    uni.setStorageSync("last_selected_question_index", selectedIndex.value);
    studentSql.value = "";
    loadChat();
    questionIdInput.value = "";
    uni.showToast({ title: `已切换到题目 ${num}`, icon: "success" });
    return;
  }

  // 3）尝试按数据库 ID 拉取（可能不在当前列表）
  jumpingById.value = true;
  try {
    const q = await getQuestion(num);
    saveCurrentAndClearState();
    overrideQuestion.value = q;
    studentSql.value = "";
    loadChat();
    questionIdInput.value = "";
    uni.showToast({ title: `已切换到题目 ${q.id}`, icon: "success" });
  } catch (e: any) {
    let msg = "加载失败，请重试";
    if (e?.statusCode === 404) {
      msg = total > 0 ? `当前共 ${total} 题，请输入 1 到 ${total} 跳转` : "题目不存在";
    } else if (e?.data?.detail) {
      const d = e.data.detail;
      msg = typeof d === "string" ? d : Array.isArray(d) && d[0]?.msg ? d[0].msg : msg;
    } else if (e?.statusCode >= 400 && e?.statusCode < 500) {
      msg = total > 0 ? `当前共 ${total} 题，请输入 1 到 ${total}` : "题目不存在或请求被拒绝";
    } else if (e?.errMsg && (e.errMsg.includes("fail") || e.errMsg.includes("network"))) {
      msg = "网络错误，请检查网络后重试";
    }
    uni.showToast({ title: msg, icon: "none", duration: 2500 });
  } finally {
    jumpingById.value = false;
  }
};

/** 随机选题（洛谷风格） */
const randomPick = () => {
  if (!questions.value.length) {
    uni.showToast({ title: "暂无题目", icon: "none" });
    return;
  }
  saveCurrentAndClearState();
  overrideQuestion.value = null;
  const randomIndex = Math.floor(Math.random() * questions.value.length);
  selectedIndex.value = randomIndex;
  uni.setStorageSync("last_selected_question_index", selectedIndex.value);
  studentSql.value = "";
  loadChat();
  const q = questions.value[randomIndex];
  uni.showToast({
    title: t.value.randomPickedFmt.replace("{title}", localizedTitle(q)),
    icon: "success",
    duration: 2000,
  });
};

const handleCheckSql = async () => {
  if (!ensureAuthed()) return;
  if (!currentQuestion.value) return;
  if (!studentSql.value.trim()) {
    uni.showToast({ title: "请输入 SQL", icon: "none" });
    return;
  }

  // 提交前保存SQL代码
  if (currentQuestion.value && studentSql.value) {
    const storageKey = `last_student_sql_${currentQuestion.value.id}`;
    uni.setStorageSync(storageKey, studentSql.value);
  }

  submitting.value = true;
  try {
    checkResult.value = await checkSql({
      student_sql: studentSql.value,
      question_id: currentQuestion.value.id,
      language: currentLanguage.value,
      challenge_mode: challengeActive.value,
    });
    // 后端会把本次“提交 SQL + AI 回复”写入对话历史，前端只需刷新对话
    await loadChat();
    // 首次正确：展示经验与升级反馈
    const res = checkResult.value;
    if (res?.is_correct) {
      if (res.earned_experience != null && res.earned_experience > 0) {
        uni.showToast({ title: `+${res.earned_experience} 经验`, icon: "none", duration: 2000 });
        profile.value = await getProfile();
        if (res.level_up && res.new_level != null) {
          setTimeout(() => {
            uni.showToast({ title: `恭喜升级！Lv.${res.new_level}`, icon: "success", duration: 2500 });
          }, 2100);
        }
      }
      // 若判题正确，弹出难度评分（1～10）
      if (currentQuestion.value) {
        pendingDifficultyQuestionId.value = currentQuestion.value.id;
        difficultyRating.value = 0;
        showDifficultyModal.value = true;
      }
    }
  } finally {
    submitting.value = false;
  }
};

const loadChat = async () => {
  if (!ensureAuthed()) return;
  if (!currentQuestion.value) return;
  const qid = currentQuestion.value.id;
  try {
    const list = await getChatMessages({ question_id: qid, limit: 120 });
    if (currentQuestion.value?.id !== qid) return;
    chatMessages.value = list;
    const last = chatMessages.value[chatMessages.value.length - 1];
    if (last) {
      scrollIntoView.value = `msg-${last.id}`;
    }
  } catch (error) {
    console.error('加载对话失败:', error);
  }
};

const clearingChat = ref(false);
const handleClearChat = async () => {
  if (!ensureAuthed() || !currentQuestion.value) return;
  if (!chatMessages.value.length) {
    uni.showToast({ title: "当前没有历史对话", icon: "none" });
    return;
  }
  uni.showModal({
    title: "清除历史对话",
    content: "确定要清除本题与 AI 老师的全部对话记录吗？清除后无法恢复。",
    success: async (res) => {
      if (!res.confirm) return;
      clearingChat.value = true;
      try {
        await clearChatMessages(currentQuestion.value!.id);
        chatMessages.value = [];
        scrollIntoView.value = "";
        uni.showToast({ title: "已清除历史对话", icon: "success" });
      } catch {
        uni.showToast({ title: "清除失败，请重试", icon: "none" });
      } finally {
        clearingChat.value = false;
      }
    },
  });
};

const sendChat = async () => {
  if (!ensureAuthed()) return;
  if (!currentQuestion.value) return;
  const msg = chatInput.value.trim();
  if (!msg) return;
  
  chatSending.value = true;
  
  // 先添加用户消息到界面（立即反馈）
  const tempUserMsg: ChatMessage = {
    id: Date.now(),
    role: 'user',
    content: msg,
    created_at: new Date().toISOString(),
  };
  chatMessages.value.push(tempUserMsg);
  
  // 清空输入框
  chatInput.value = "";
  
  // 滚动到底部
  setTimeout(() => {
    const last = chatMessages.value[chatMessages.value.length - 1];
    if (last) {
      scrollIntoView.value = `msg-${last.id}`;
    }
  }, 100);
  
  try {
    await chatWithTeacher({ 
      question_id: currentQuestion.value.id, 
      message: msg,
      language: currentLanguage.value,
    });
    // 重新加载完整对话历史
    await loadChat();
  } catch (error: any) {
    // 如果请求失败，移除临时消息
    const index = chatMessages.value.findIndex(m => m.id === tempUserMsg.id);
    if (index >= 0) {
      chatMessages.value.splice(index, 1);
    }
    // 恢复输入内容
    chatInput.value = msg;
    // 错误提示已经在request.ts中处理了
  } finally {
    chatSending.value = false;
  }
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

const goTeacher = async () => {
  if (!ensureAuthed()) return;
  
  // 检查用户角色
  if (!profile.value) {
    try {
      profile.value = await getProfile();
    } catch {
      uni.showToast({ title: "请先登录", icon: "none" });
      return;
    }
  }
  
  if (!requireTeacher(profile.value)) {
    return;
  }
  
  uni.navigateTo({ url: "/pages/teacher/index" });
};

// 对话时间展示（仿微信：今天 HH:mm，昨天 昨天 HH:mm，更早 月/日 HH:mm）
const formatMessageTime = (created_at: string | undefined): string => {
  if (!created_at) return "";
  const date = new Date(created_at);
  if (Number.isNaN(date.getTime())) return "";
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const msgDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const pad = (n: number) => String(n).padStart(2, "0");
  const timeStr = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  if (msgDay.getTime() === today.getTime()) {
    return timeStr;
  }
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  if (msgDay.getTime() === yesterday.getTime()) {
    return `昨天 ${timeStr}`;
  }
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getMonth() + 1}/${date.getDate()} ${timeStr}`;
  }
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()} ${timeStr}`;
};

// 简单的Markdown解析函数，转换为rich-text支持的格式
const parseMarkdown = (text: string): string => {
  if (!text) return '';
  
  let html = text;
  
  // 先处理代码块（避免代码块内的内容被其他规则处理）
  const codeBlocks: string[] = [];
  html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push(`<pre style="background: #f3f4f6; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; white-space: pre-wrap; word-break: break-all;"><code style="font-family: ui-monospace, monospace; font-size: 0.9em; color: #111827;">${escapeHtml(code.trim())}</code></pre>`);
    return placeholder;
  });
  
  // 转义HTML特殊字符（但保留已处理的代码块占位符）
  html = escapeHtml(html);
  
  // 恢复代码块
  codeBlocks.forEach((block, index) => {
    html = html.replace(`__CODE_BLOCK_${index}__`, block);
  });
  
  // 处理标题 ### text（必须在转义后处理，因为需要HTML标签）
  html = html.replace(/###\s+(.+?)(?=\n|$)/g, '<h3 style="font-size: 16px; font-weight: 600; margin: 12px 0 8px 0; color: #111827;">$1</h3>');
  html = html.replace(/##\s+(.+?)(?=\n|$)/g, '<h2 style="font-size: 18px; font-weight: 600; margin: 14px 0 10px 0; color: #111827;">$1</h2>');
  html = html.replace(/^#\s+(.+?)(?=\n|$)/gm, '<h1 style="font-size: 20px; font-weight: 600; margin: 16px 0 12px 0; color: #111827;">$1</h1>');
  
  // 处理加粗 **text** 或 __text__（但要避免匹配代码块占位符）
  html = html.replace(/\*\*([^*\n]+?)\*\*/g, '<strong style="font-weight: 600; color: #111827;">$1</strong>');
  html = html.replace(/(?<!__)(?<!_)_([^_\n]+?)_(?!_)/g, '<strong style="font-weight: 600; color: #111827;">$1</strong>');
  
  // 处理行内代码 `code`（但要避免匹配代码块）
  html = html.replace(/`([^`\n]+?)`/g, '<code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 0.9em; color: #dc2626;">$1</code>');
  
  // 处理换行
  html = html.replace(/\n/g, '<br/>');
  
  return html;
};

// HTML转义函数（uni-app兼容版本）
const escapeHtml = (text: string): string => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
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
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 12px;
}
.topbar-left {
  flex: 1;
  min-width: 0;
}
.level-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.level-label {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
  flex-shrink: 0;
}
.xp-bar-bg {
  flex: 1;
  min-width: 60px;
  height: 10px;
  background: #e5e7eb;
  border-radius: 5px;
  overflow: hidden;
}
.xp-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 5px;
  transition: width 0.3s ease;
}
.xp-text {
  font-size: 11px;
  color: #6b7280;
  flex-shrink: 0;
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}
.card-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.btn-clear-chat {
  font-size: 12px;
  padding: 6px 12px;
  white-space: nowrap;
}
.card-title {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}
.language-picker-wrapper {
  position: relative;
  flex-shrink: 0;
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
  cursor: pointer;
  user-select: none;
}
.language-selector:active {
  background: #f3f4f6;
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
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-width: 120px;
  overflow: hidden;
}
.language-menu-item {
  padding: 10px 16px;
  font-size: 13px;
  color: #111827;
  cursor: pointer;
  transition: background 0.2s;
}
.language-menu-item:active {
  background: #f3f4f6;
}
.language-menu-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}
.picker {
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  color: #111827;
}
.question {
  margin-top: 12px;
}
.q-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.q-content {
  display: block;
  font-size: 14px;
  color: #111827;
  line-height: 1.5;
}
.q-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}
.q-meta {
  display: block;
  font-size: 12px;
  color: #9ca3af;
}
.challenge-row {
  margin-top: 10px;
}
.btn-challenge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  padding: 8px 14px;
}
.challenge-active {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #fef3c7;
  border-radius: 10px;
  border: 1px solid #fcd34d;
}
.challenge-timer {
  font-size: 14px;
  font-weight: 600;
  color: #b45309;
}
.challenge-hint {
  font-size: 12px;
  color: #92400e;
}
/* 表结构预览：小表展示列名与示例数据 */
.schema-preview-loading {
  margin-top: 16px;
  padding: 12px;
  border-top: 1px solid #e5e7eb;
}
.schema-loading-text {
  font-size: 13px;
  color: #6b7280;
}
.schema-preview-wrap {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}
.schema-preview-title {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
}
.schema-preview-hint {
  display: block;
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 10px;
}
.schema-table-card {
  margin-bottom: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 12px;
  overflow: hidden;
}
.schema-table-card:last-child {
  margin-bottom: 0;
}
.schema-table-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}
.schema-table-name-hint {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 4px;
}
.schema-table-header-label {
  display: block;
  font-size: 11px;
  color: #1d4ed8;
  font-weight: 600;
  margin-bottom: 6px;
}
.schema-table-scroll {
  width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}
.schema-table {
  display: inline-block;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.schema-row {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}
.schema-row:last-child {
  border-bottom: none;
}
.schema-header {
  font-weight: 700;
  color: #1e40af;
  background: #dbeafe;
}
.schema-cell-header {
  color: #1e40af;
}
.schema-cell {
  flex: 1;
  min-width: 60px;
  max-width: 140px;
  padding: 8px 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-right: 1px solid #e5e7eb;
}
.schema-cell:last-child {
  border-right: none;
}
.schema-row-0 { background: #dbeafe; }
.schema-row-1 { background: #fef9c3; }
.schema-row-2 { background: #dcfce7; }
.schema-row-3 { background: #f3e8ff; }
.schema-row-4 { background: #ffedd5; }
.modal-mask {
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-box {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  width: 100%;
  max-width: 340px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}
.modal-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}
.modal-desc {
  display: block;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}
.rating-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.rating-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}
.rating-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fafafa;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
    monospace;
  font-size: 13px;
  box-sizing: border-box;
}
.textarea-sql {
  max-height: 50vh;
  overflow-y: auto;
}
.row {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}
.row-select {
  align-items: center;
  flex-wrap: wrap;
}
.id-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 120px;
}
.id-label {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}
.id-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  min-width: 0;
}
.btn-small {
  padding: 8px 14px;
  font-size: 13px;
  white-space: nowrap;
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
.chat {
  height: 320px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px;
}
.chat-empty {
  font-size: 13px;
  color: #6b7280;
}
.msg {
  margin-bottom: 10px;
}
.msg-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.msg-role {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}
.msg-time {
  font-size: 11px;
  color: #9ca3af;
}
.bubble {
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
}
.msg.user .bubble {
  background: #eef2ff;
  border-color: #c7d2fe;
}
.msg.assistant .bubble {
  background: #ecfdf5;
  border-color: #bbf7d0;
}
.msg.system .bubble {
  background: #111827;
  border-color: #111827;
}
.msg.system .msg-text {
  color: #e5e7eb;
}
.msg-text {
  display: block;
  white-space: normal;
  word-break: break-word;
  color: #111827;
  font-size: 13px;
  line-height: 1.55;
}
.msg-text :deep(h1),
.msg-text :deep(h2),
.msg-text :deep(h3) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  color: #111827;
}
.msg-text :deep(strong) {
  font-weight: 600;
  color: #111827;
}
.msg-text :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 0.9em;
  color: #dc2626;
}
.msg-text :deep(pre) {
  background: #f3f4f6;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}
.msg-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #111827;
}
.chat-input {
  margin-top: 10px;
}
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-textarea {
  width: 100%;
  min-height: 80px;
  max-height: 200px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
  resize: none;
  overflow-y: auto;
}
.chat-textarea:focus {
  border-color: #2563eb;
  outline: none;
}
.btn-send {
  align-self: flex-start;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  min-width: 80px;
}
.btn-send:disabled {
  background: #9ca3af;
  opacity: 0.6;
}
.btn-send:not(:disabled):active {
  background: #1d4ed8;
  transform: scale(0.98);
}
</style>
