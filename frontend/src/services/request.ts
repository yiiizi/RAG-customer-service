import axios from 'axios';
import { message } from 'antd';

// In development, use current hostname so other computers on the network can connect
const isDev = import.meta.env.DEV;
const apiPort = import.meta.env.VITE_API_PORT || '8000';
const BASE_URL = isDev
  ? `http://${window.location.hostname}:${apiPort}/api`
  : (import.meta.env.VITE_API_BASE || '/api');

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000,
});

request.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败';
    message.error(msg);
    return Promise.reject(err);
  }
);

export default request;
