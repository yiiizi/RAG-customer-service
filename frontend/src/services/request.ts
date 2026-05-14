import axios from 'axios';
// Static message is required here since axios interceptors are outside React component tree.
// The App.useApp() hook cannot be used in non-component code.
// eslint-disable-next-line @typescript-eslint/no-deprecated
import { message } from 'antd';
import { getAccessToken, removeTokens } from '@/utils/token';

// In development, use relative path to leverage Vite proxy
// In production, use environment variable or relative path
const BASE_URL = import.meta.env.DEV ? '/api' : (import.meta.env.VITE_API_BASE || '/api');

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
});

// 请求拦截器：自动附加 Authorization Token
request.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器：处理 401 未授权，自动跳转登录页
request.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      removeTokens();
      message.error('登录已过期，请重新登录');
      window.location.href = '/login';
      return Promise.reject(err);
    }
    const msg = err.response?.data?.detail || err.message || '请求失败';
    message.error(msg);
    return Promise.reject(err);
  }
);

export default request;
