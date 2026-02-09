// src/utils/request.ts

// 1. 定义基础 URL
// 开发环境(development)走代理 /api，生产环境(production)走真实网址
const BASE_URL = import.meta.env.MODE === 'development' ? '/api' : 'https://你的线上域名/api';

interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  header?: any;
}

export const request = <T = any>(options: RequestOptions): Promise<T> => {
  return new Promise((resolve, reject) => {
    const logoutAndGoLogin = () => {
      uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' });
      uni.removeStorageSync('token');
      uni.removeStorageSync('refresh_token');
      uni.removeStorageSync('user');
      uni.reLaunch({ url: '/pages/login/index' });
    };

    const isAuthEndpoint = (url: string) => {
      return (
        url.startsWith('/auth/login') ||
        url.startsWith('/auth/register') ||
        url.startsWith('/auth/code') ||
        url.startsWith('/auth/refresh')
      );
    };

    const shouldTryRefresh = (code: number, detail?: string) => {
      // 只在“认证失败”场景尝试 refresh；避免把“权限不足(teacher/student)”当成登录过期
      if (code === 401) return true;
      if (code !== 403) return false;
      const d = (detail || '').toLowerCase();
      return (
        d.includes('not authenticated') ||
        d.includes('access token') ||
        d.includes('token') ||
        d.includes('could not validate credentials')
      );
    };

    const doRequest = (tokenOverride?: string, retried?: boolean) => {
      // 自动获取 Token (登录后存在 storage 里)
      const token = tokenOverride ?? uni.getStorageSync('token');

      // 组装请求头
      const header: any = {
        'Content-Type': 'application/json',
        ...options.header,
      };

      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      }

      uni.request({
        url: BASE_URL + options.url,
        method: options.method || 'GET',
        data: options.data,
        header,
        success: async (res: any) => {
          const code = res.statusCode;
          const rawDetail = res?.data?.detail;
          // 后端可能返回 detail 为字符串或数组（如 FastAPI 校验错误）
          const detail =
            typeof rawDetail === "string"
              ? rawDetail
              : Array.isArray(rawDetail) && rawDetail.length > 0
                ? (rawDetail[0]?.msg ?? rawDetail[0]?.message ?? String(rawDetail[0]))
                : rawDetail != null
                  ? String(rawDetail)
                  : "";

          // 200-299 算成功
          if (code >= 200 && code < 300) {
            resolve(res.data as T);
            return;
          }

          // 认证失败：缺 token、token 过期、token 不可用（才尝试 refresh）
          if (shouldTryRefresh(code, detail) && !retried && !isAuthEndpoint(options.url)) {
            const refresh_token = uni.getStorageSync('refresh_token');
            if (!refresh_token) {
              logoutAndGoLogin();
              reject(res);
              return;
            }

            // 尝试刷新 access token，再重试一次原请求
            try {
              const refreshRes: any = await new Promise((ok, bad) => {
                uni.request({
                  url: BASE_URL + '/auth/refresh',
                  method: 'POST',
                  data: { refresh_token },
                  header: { 'Content-Type': 'application/json' },
                  success: (r: any) => ok(r),
                  fail: (e: any) => bad(e),
                });
              });

              if (refreshRes?.statusCode >= 200 && refreshRes?.statusCode < 300 && refreshRes?.data?.access_token) {
                uni.setStorageSync('token', refreshRes.data.access_token);
                doRequest(refreshRes.data.access_token, true);
                return;
              }
            } catch {
              // ignore
            }

            logoutAndGoLogin();
            reject(res);
            return;
          }

          // 其他错误 - 构造一个包含完整错误信息的对象
          const errorObj = {
            statusCode: code,
            data: res.data,
            detail: detail || '请求出错了',
            message: detail || '请求出错了',
          };
          
          // 只在非认证错误时显示toast（认证错误已经在上面处理了）
          if (!shouldTryRefresh(code, detail)) {
            uni.showToast({
              title: detail || '请求出错了',
              icon: 'none',
            });
          }
          
          reject(errorObj);
        },
        fail: (err) => {
          uni.showToast({ title: '网络连不上后端', icon: 'none' });
          reject(err);
        },
      });
    };

    doRequest();
  });
};