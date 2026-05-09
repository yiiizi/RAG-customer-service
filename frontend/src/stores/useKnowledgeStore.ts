import { create } from 'zustand';
import type { KBDocument, KBStats } from '@/types/knowledge';
import * as api from '@/services/knowledgeService';

interface KnowledgeState {
  documents: KBDocument[];
  total: number;
  stats: KBStats | null;
  loading: boolean;
  uploading: boolean;
  uploadProgress: Record<string, number>;
  // actions
  fetchList: () => Promise<void>;
  fetchStats: () => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  deleteFile: (fileName: string) => Promise<void>;
  reindexFile: (fileName: string) => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  documents: [],
  total: 0,
  stats: null,
  loading: false,
  uploading: false,
  uploadProgress: {},

  fetchList: async () => {
    set({ loading: true });
    try {
      const res = await api.getKBList();
      set({ documents: res.items, total: res.total });
    } finally {
      set({ loading: false });
    }
  },

  fetchStats: async () => {
    try {
      const stats = await api.getKBStats();
      set({ stats });
    } catch { /* stats unavailable */ }
  },

  uploadFile: async (file: File) => {
    set({ uploading: true });
    try {
      await api.uploadFile(file);
      await get().fetchList();
      await get().fetchStats();
    } finally {
      set({ uploading: false });
    }
  },

  deleteFile: async (fileName: string) => {
    await api.deleteKBFile(fileName);
    await get().fetchList();
    await get().fetchStats();
  },

  reindexFile: async (fileName: string) => {
    await api.reindexFile(fileName);
    await get().fetchList();
  },
}));
