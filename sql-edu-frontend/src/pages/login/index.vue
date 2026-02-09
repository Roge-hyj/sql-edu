<template>
    <view class="container">
      <view class="lang-bar">
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
      </view>
      <view class="header">
        <text class="title">{{ t.title }}</text>
        <text class="subtitle">{{ t.subtitle }}</text>
      </view>

      <view class="form-box">
        <view class="tabs">
          <view class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">{{ t.tabLogin }}</view>
          <view class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">{{ t.tabRegister }}</view>
          <view class="tab" :class="{ active: mode === 'delete' }" @click="mode = 'delete'">{{ t.tabDelete }}</view>
        </view>

        <template v-if="mode === 'login'">
          <input
            class="input"
            v-model="loginForm.email"
            type="text"
            :placeholder="t.placeholderEmailOrUser"
            :maxlength="-1"
          />
          <input
            class="input"
            v-model="loginForm.password"
            type="password"
            :placeholder="t.placeholderPassword"
            :maxlength="72"
          />
          <button class="btn" @click="handleLogin" :loading="loading">{{ t.btnLogin }}</button>
        </template>

        <template v-else-if="mode === 'register'">
          <input
            class="input"
            v-model="registerForm.email"
            type="text"
            :placeholder="t.placeholderEmail"
            :maxlength="-1"
          />
          <view class="row">
            <input
              class="input input-grow"
              v-model="registerForm.captcha"
              type="text"
              :placeholder="t.placeholderCaptcha"
              :maxlength="-1"
            />
            <button class="btn-mini" :disabled="codeCountdown > 0" @click="handleGetCode">
              {{ codeCountdown > 0 ? `${codeCountdown}s` : t.getCode }}
            </button>
          </view>
          <input
            class="input"
            v-model="registerForm.username"
            type="text"
            :placeholder="t.placeholderUsername"
            :maxlength="-1"
          />
          <input
            class="input"
            v-model="registerForm.password"
            type="password"
            :placeholder="t.placeholderPasswordRegister"
            :maxlength="72"
          />
          <input
            class="input"
            v-model="registerForm.confirm_password"
            type="password"
            :placeholder="t.placeholderConfirmPassword"
            :maxlength="72"
          />
          <input
            class="input"
            v-model="registerForm.invite_code"
            type="text"
            :placeholder="t.placeholderInviteCode"
            :maxlength="-1"
          />
          <button class="btn" @click="handleRegister" :loading="loading">{{ t.btnRegister }}</button>
          <view class="tip">
            <text>{{ t.tipAfterRegister }}</text>
          </view>
        </template>

        <template v-else-if="mode === 'delete'">
          <view class="delete-warning">
            <text class="warning-title">⚠️ {{ t.tabDelete }}</text>
            <text class="warning-desc">{{ t.deleteWarning }}</text>
            <view class="warning-list">
              <text>• {{ t.deleteItem1 }}</text>
              <text>• {{ t.deleteItem2 }}</text>
              <text>• {{ t.deleteItem3 }}</text>
            </view>
          </view>
          <input
            class="input"
            v-model="deleteForm.email"
            type="text"
            :placeholder="t.placeholderEmailOrUser"
            :maxlength="-1"
          />
          <input
            class="input"
            v-model="deleteForm.password"
            type="password"
            :placeholder="t.placeholderPasswordDelete"
            :maxlength="72"
          />
          <button class="btn btn-danger" @click="handleDeleteAccount" :loading="loading">{{ t.btnConfirmDelete }}</button>
        </template>
      </view>
      
      <view class="debug-info" v-if="token">
        <text>{{ t.loginSuccess }}</text>
      </view>
      
    </view>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, computed, onMounted } from 'vue';
  import { getEmailCode, login, register, deleteAccount } from '@/api/auth';

  const languageOptions = ["简体中文", "English", "繁體中文"];
  const languageIndex = ref(0);
  const showLanguageMenu = ref(false);
  const UI_STRINGS = [
    { title: "SQL 智能教学系统", navTitle: "登录", loginSuccess: "✅ 登录成功！", subtitle: "开启你的 SQL 进阶之路", tabLogin: "登录", tabRegister: "注册", tabDelete: "注销账户", placeholderEmailOrUser: "请输入用户名或邮箱", placeholderPassword: "请输入密码", btnLogin: "登 录", placeholderEmail: "请输入邮箱", placeholderCaptcha: "请输入验证码", getCode: "获取验证码", placeholderUsername: "请输入用户名", placeholderPasswordRegister: "请输入密码(6-20位)", placeholderConfirmPassword: "请再次输入密码", placeholderInviteCode: "教师邀请码（填入可获得教师端权限，可留空）", btnRegister: "注 册", tipAfterRegister: "注册成功后会自动切回登录。", deleteWarning: "此操作不可逆！注销后将删除：", deleteItem1: "您的账户信息", deleteItem2: "所有提交记录", deleteItem3: "所有学习数据", placeholderPasswordDelete: "请输入密码以确认注销", btnConfirmDelete: "确认注销" },
    { title: "SQL Learning", navTitle: "Login", loginSuccess: "✅ Login success!", subtitle: "Start your SQL journey", tabLogin: "Login", tabRegister: "Register", tabDelete: "Delete account", placeholderEmailOrUser: "Username or email", placeholderPassword: "Password", btnLogin: "Login", placeholderEmail: "Email", placeholderCaptcha: "Verification code", getCode: "Get code", placeholderUsername: "Username", placeholderPasswordRegister: "Password (6-20 chars)", placeholderConfirmPassword: "Confirm password", placeholderInviteCode: "Teacher invite code (optional)", btnRegister: "Register", tipAfterRegister: "You will be redirected to login after registration.", deleteWarning: "This cannot be undone. The following will be deleted:", deleteItem1: "Your account", deleteItem2: "All submissions", deleteItem3: "All learning data", placeholderPasswordDelete: "Password to confirm", btnConfirmDelete: "Confirm delete" },
    { title: "SQL 智能教學系統", navTitle: "登錄", loginSuccess: "✅ 登錄成功！", subtitle: "開啟你的 SQL 進階之路", tabLogin: "登錄", tabRegister: "註冊", tabDelete: "註銷賬戶", placeholderEmailOrUser: "請輸入用戶名或郵箱", placeholderPassword: "請輸入密碼", btnLogin: "登 錄", placeholderEmail: "請輸入郵箱", placeholderCaptcha: "請輸入驗證碼", getCode: "獲取驗證碼", placeholderUsername: "請輸入用戶名", placeholderPasswordRegister: "請輸入密碼(6-20位)", placeholderConfirmPassword: "請再次輸入密碼", placeholderInviteCode: "教師邀請碼（可留空）", btnRegister: "註 冊", tipAfterRegister: "註冊成功後會自動切回登錄。", deleteWarning: "此操作不可逆！註銷後將刪除：", deleteItem1: "您的賬戶信息", deleteItem2: "所有提交記錄", deleteItem3: "所有學習數據", placeholderPasswordDelete: "請輸入密碼以確認註銷", btnConfirmDelete: "確認註銷" },
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

  const loading = ref(false);
  const token = ref('');
  const refreshToken = ref('');
  const mode = ref<'login' | 'register' | 'delete'>('login');
  const codeCountdown = ref(0);
  let countdownTimer: any = null;
  
  // 定义表单数据
  const loginForm = reactive({
    email: '',
    password: ''
  });

  const deleteForm = reactive({
    email: '',
    password: ''
  });

  const registerForm = reactive({
    email: '',
    captcha: '',
    username: '',
    password: '',
    confirm_password: '',
    invite_code: ''
  });

  const startCountdown = (seconds = 60) => {
    codeCountdown.value = seconds;
    if (countdownTimer) clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      codeCountdown.value -= 1;
      if (codeCountdown.value <= 0) {
        clearInterval(countdownTimer);
        countdownTimer = null;
        codeCountdown.value = 0;
      }
    }, 1000);
  };

  const handleGetCode = async () => {
    if (!registerForm.email) {
      return uni.showToast({ title: '请输入邮箱', icon: 'none' });
    }
    if (codeCountdown.value > 0) return;
    loading.value = true;
    try {
      const res: any = await getEmailCode({ email: registerForm.email });
      if (res?.result === 'success') {
        uni.showToast({ title: '验证码已发送', icon: 'success' });
        startCountdown(60);
      } else {
        uni.showToast({ title: res?.detail || '验证码发送失败', icon: 'none' });
      }
    } catch (e) {
      console.error('获取验证码失败:', e);
    } finally {
      loading.value = false;
    }
  };

  const handleRegister = async () => {
    const f = registerForm;
    if (!f.email || !f.captcha || !f.username || !f.password || !f.confirm_password) {
      return uni.showToast({ title: '请把注册信息填写完整', icon: 'none' });
    }
    if (f.password !== f.confirm_password) {
      return uni.showToast({ title: '两次密码不一致', icon: 'none' });
    }
    loading.value = true;
    try {
      const res: any = await register({
        email: f.email,
        username: f.username,
        password: f.password,
        confirm_password: f.confirm_password,
        captcha: f.captcha,
        invite_code: f.invite_code || undefined,
      });
      if (res?.result === 'success') {
        uni.showToast({ title: '注册成功，请登录', icon: 'success' });
        mode.value = 'login';
        loginForm.email = f.email;
        loginForm.password = f.password;
        registerForm.captcha = '';
      } else {
        uni.showToast({ title: res?.detail || '注册失败', icon: 'none' });
      }
    } catch (e) {
      console.error('注册失败:', e);
    } finally {
      loading.value = false;
    }
  };
  
  const handleLogin = async () => {
    if (!loginForm.email || !loginForm.password) {
      return uni.showToast({ title: '账号密码不能为空', icon: 'none' });
    }
  
    loading.value = true;
    try {
      // 1. 发起请求 (调用我们封装好的 api)
      const res: any = await login(loginForm);
      console.log('登录响应:', res);
      
      // 2. 拿到 Token (根据后端返回结构: { user, token, refresh_token })
      if (res?.token) {
        uni.showToast({ title: '欢迎回来!', icon: 'success' });
        
        // 3. 存到本地存储 (这就相当于领了门票)
        uni.setStorageSync('token', res.token);
        if (res.refresh_token) uni.setStorageSync('refresh_token', res.refresh_token);
        if (res.user) uni.setStorageSync('user', res.user);

        token.value = res.token; // 让页面显示出来给你看
        refreshToken.value = res.refresh_token || '';
        
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/index/index' });
        }, 600);
      }
    } catch (error) {
      console.error('登录失败:', error);
      // 具体的错误提示 request.ts 已经帮我们弹了
    } finally {
      loading.value = false;
    }
  };
  
  const handleDeleteAccount = async () => {
    if (!deleteForm.email || !deleteForm.password) {
      return uni.showToast({ title: '请填写完整信息', icon: 'none' });
    }
    
    // 二次确认
    uni.showModal({
      title: '最后确认',
      content: '确定要注销账户吗？此操作不可逆！',
      confirmText: '确定注销',
      confirmColor: '#ff3b30',
      success: async (res) => {
        if (res.confirm) {
          loading.value = true;
          try {
            // 先尝试登录验证身份并获取token
            let loginResult: any;
            try {
              loginResult = await login({
                email: deleteForm.email,
                password: deleteForm.password
              });
              
              // 保存token到本地存储，以便后续调用需要认证的接口
              if (loginResult?.token) {
                uni.setStorageSync('token', loginResult.token);
                if (loginResult.refresh_token) {
                  uni.setStorageSync('refresh_token', loginResult.refresh_token);
                }
              }
            } catch (loginError: any) {
              // 登录失败，说明用户名/密码错误
              uni.showToast({ title: '用户名/邮箱或密码错误', icon: 'none' });
              loading.value = false;
              return;
            }
            
            // 登录成功后，调用注销接口
            try {
              const result: any = await deleteAccount({ password: deleteForm.password });
              if (result?.result === 'success') {
                uni.showToast({ title: '账户已注销', icon: 'success' });
                
                // 清除本地存储
                uni.removeStorageSync('token');
                uni.removeStorageSync('refresh_token');
                uni.removeStorageSync('user');
                
                // 重置状态
                token.value = '';
                refreshToken.value = '';
                
                // 清空表单
                deleteForm.email = '';
                deleteForm.password = '';
                loginForm.email = '';
                loginForm.password = '';
                
                // 切换到登录页面
                setTimeout(() => {
                  mode.value = 'login';
                }, 1000);
              } else {
                uni.showToast({ title: result?.detail || '注销失败', icon: 'none' });
                // 清除临时token
                uni.removeStorageSync('token');
                uni.removeStorageSync('refresh_token');
              }
            } catch (error: any) {
              console.error('注销账户失败:', error);
              // 清除临时token
              uni.removeStorageSync('token');
              uni.removeStorageSync('refresh_token');
              // request.ts 已经处理了错误提示
            }
          } catch (error: any) {
            console.error('注销账户失败:', error);
          } finally {
            loading.value = false;
          }
        }
      }
    });
  };
  </script>
  
  <style>
  .container { 
    position: relative;
    padding: 80px 30px; 
    background-color: #fff;
    min-height: 100vh;
  }
  .lang-bar {
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 10;
  }
  .language-picker-wrapper { position: relative; }
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
  .language-arrow { font-size: 10px; color: #9ca3af; transition: transform 0.2s; }
  .language-arrow.rotated { transform: rotate(180deg); }
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
  .language-menu-item.active { background: #eff6ff; color: #2563eb; font-weight: 500; }
  .header { 
    margin-bottom: 60px; 
    text-align: center; 
  }
  .title { 
    font-size: 28px; 
    font-weight: bold; 
    color: #333;
    display: block; 
    margin-bottom: 12px; 
  }
  .subtitle { 
    font-size: 16px; 
    color: #999; 
    letter-spacing: 1px;
  }
  .input {
    border: 1px solid #eee;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 20px;
    background-color: #f8f8f8;
    font-size: 16px;
  }
  .tabs {
    display: flex;
    gap: 10px;
    background: #f3f4f6;
    border-radius: 999px;
    padding: 6px;
    margin-bottom: 18px;
  }
  .tab {
    flex: 1;
    text-align: center;
    padding: 10px 0;
    border-radius: 999px;
    font-size: 14px;
    color: #6b7280;
  }
  .tab.active {
    background: #fff;
    color: #111827;
    box-shadow: 0 4px 10px rgba(17, 24, 39, 0.06);
    font-weight: 600;
  }
  .row {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  .input-grow {
    flex: 1;
    margin-bottom: 20px;
  }
  .btn-mini {
    height: 44px;
    line-height: 44px;
    padding: 0 12px;
    border-radius: 999px;
    background: #111827;
    color: #fff;
    font-size: 12px;
    white-space: nowrap;
  }
  .tip {
    margin-top: 10px;
    text-align: center;
    color: #6b7280;
    font-size: 12px;
  }
  .btn {
    background-color: #007aff; /* 经典的科技蓝 */
    color: white;
    border-radius: 50px;
    margin-top: 30px;
    font-size: 18px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }
  .btn:active {
    transform: scale(0.98);
  }
  .debug-info {
    margin-top: 40px;
    padding: 15px;
    background: #f0f9eb;
    border-radius: 8px;
    border: 1px solid #e1f3d8;
    color: #67c23a;
    font-size: 12px;
  }
  .token-text {
    margin-top: 8px;
    word-break: break-all;
    color: #333;
    font-family: monospace;
  }
  .delete-warning {
    padding: 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 12px;
    margin-bottom: 20px;
  }
  .warning-title {
    display: block;
    color: #dc2626;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .warning-desc {
    display: block;
    color: #991b1b;
    font-size: 14px;
    margin-bottom: 12px;
  }
  .warning-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding-left: 10px;
  }
  .warning-list text {
    color: #7f1d1d;
    font-size: 13px;
  }
  .btn-danger {
    background-color: #dc2626;
    color: white;
  }
  .btn-danger:active {
    background-color: #b91c1c;
  }
  </style>