import { request } from "@/utils/request";

export type ResponseOut = {
  result: "success" | "failure";
  detail?: string | null;
};

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

export function getEmailCode(params: { email: string }) {
  return request<ResponseOut>({
    url: `/auth/code?email=${encodeURIComponent(params.email)}`,
    method: "GET",
  });
}

export function register(data: {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  captcha: string;
  invite_code?: string | null;
}) {
  return request<ResponseOut>({
    url: "/auth/register",
    method: "POST",
    data,
  });
}

export function login(data: { email: string; password: string }) {
  return request<LoginOut>({
    url: "/auth/login",
    method: "POST",
    data,
  });
}

export function refreshToken(data: { refresh_token: string }) {
  return request<{ access_token: string; token_type: string }>({
    url: "/auth/refresh",
    method: "POST",
    data,
  });
}

export function logout() {
  return request<ResponseOut>({
    url: "/auth/logout",
    method: "POST",
  });
}

export function getProfile() {
  return request<UserSchema>({
    url: "/auth/profile",
    method: "GET",
  });
}

export function updateProfile(data: { username?: string }) {
  return request<UserSchema>({
    url: "/auth/profile",
    method: "PUT",
    data,
  });
}

export function changePassword(data: {
  old_password: string;
  new_password: string;
  confirm_password: string;
}) {
  return request<ResponseOut>({
    url: "/auth/change-password",
    method: "POST",
    data,
  });
}

export function deleteAccount(data: { password: string }) {
  return request<ResponseOut>({
    url: "/auth/delete-account",
    method: "DELETE",
    data,
  });
}