/**
 * 认证相关的工具函数
 */

/**
 * 检查用户是否已登录
 * @returns 如果已登录返回 true，否则跳转到登录页并返回 false
 */
export function ensureAuthed(): boolean {
  const token = uni.getStorageSync("token");
  if (!token) {
    uni.reLaunch({ url: "/pages/login/index" });
    return false;
  }
  return true;
}

/**
 * 检查用户是否为教师
 * @param profile 用户信息对象
 * @returns 如果是教师返回 true，否则返回 false
 */
export function isTeacher(profile: { role?: string } | null): boolean {
  return profile?.role === "teacher";
}

/**
 * 要求用户必须是教师，否则跳转
 * @param profile 用户信息对象
 * @returns 如果是教师返回 true，否则跳转并返回 false
 */
export function requireTeacher(profile: { role?: string } | null): boolean {
  if (!isTeacher(profile)) {
    uni.showToast({ title: "只有教师可以访问此功能", icon: "none" });
    uni.reLaunch({ url: "/pages/index/index" });
    return false;
  }
  return true;
}
