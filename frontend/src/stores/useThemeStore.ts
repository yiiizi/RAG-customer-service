import { create } from 'zustand';

type ThemeMode = 'dark' | 'light';

interface ThemeState {
  mode: ThemeMode;
  toggle: () => void;
  setMode: (m: ThemeMode) => void;
}

// Persist to localStorage
const STORAGE_KEY = 'rag-theme-mode';

function loadMode(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch { /* ignore */ }
  return 'dark';
}

function saveMode(mode: ThemeMode) {
  try { localStorage.setItem(STORAGE_KEY, mode); } catch { /* ignore */ }
}

export const useThemeStore = create<ThemeState>((set) => ({
  mode: loadMode(),

  toggle: () =>
    set((s) => {
      const next = s.mode === 'dark' ? 'light' : 'dark';
      saveMode(next);
      return { mode: next };
    }),

  setMode: (m) => {
    saveMode(m);
    set({ mode: m });
  },
}));
