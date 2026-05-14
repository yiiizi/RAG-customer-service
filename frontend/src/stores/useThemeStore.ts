import { create } from 'zustand';

type ThemeMode = 'dark' | 'light' | 'system';

interface ThemeState {
  mode: ThemeMode;
  resolvedMode: 'dark' | 'light';  // 实际解析后的模式
  toggle: () => void;
  setMode: (m: ThemeMode) => void;
}

// Persist to localStorage
const STORAGE_KEY = 'rag-theme-mode';

function detectSystemPreference(): 'dark' | 'light' {
  try {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
  } catch { /* ignore */ }
  return 'light';
}

function resolveMode(mode: ThemeMode): 'dark' | 'light' {
  if (mode === 'system') return detectSystemPreference();
  return mode;
}

function loadMode(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') return stored;
  } catch { /* ignore */ }
  // 默认跟随系统
  return 'system';
}

function saveMode(mode: ThemeMode) {
  try { localStorage.setItem(STORAGE_KEY, mode); } catch { /* ignore */ }
}

// 同步设置 data-theme 到 HTML 根元素（在 React 渲染前也要调用一次）
export function applyThemeToDOM(resolved: 'dark' | 'light') {
  document.documentElement.setAttribute('data-theme', resolved);
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: loadMode(),
  resolvedMode: resolveMode(loadMode()),

  toggle: () =>
    set((s) => {
      const next: ThemeMode = s.mode === 'dark' ? 'light' : s.mode === 'light' ? 'system' : 'dark';
      saveMode(next);
      const resolved = resolveMode(next);
      applyThemeToDOM(resolved);
      return { mode: next, resolvedMode: resolved };
    }),

  setMode: (m) => {
    saveMode(m);
    const resolved = resolveMode(m);
    applyThemeToDOM(resolved);
    set({ mode: m, resolvedMode: resolved });
  },
}));

// 监听系统主题变化
if (typeof window !== 'undefined' && window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const state = useThemeStore.getState();
    if (state.mode === 'system') {
      const resolved = detectSystemPreference();
      applyThemeToDOM(resolved);
      useThemeStore.setState({ resolvedMode: resolved });
    }
  });
}
