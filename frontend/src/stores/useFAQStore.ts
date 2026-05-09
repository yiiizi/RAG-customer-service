import { create } from 'zustand';
import type { FAQItem } from '@/types/faq';
import * as api from '@/services/faqService';

interface FAQState {
  items: FAQItem[];
  total: number;
  loading: boolean;
  keyword: string;
  category: string;
  page: number;
  pageSize: number;
  // actions
  fetchList: () => Promise<void>;
  setKeyword: (kw: string) => void;
  setCategory: (cat: string) => void;
  setPage: (p: number) => void;
  setPageSize: (ps: number) => void;
  create: (data: { question: string; answer: string; category: string }) => Promise<void>;
  update: (id: string, data: { question?: string; answer?: string; category?: string }) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

export const useFAQStore = create<FAQState>((set, get) => ({
  items: [],
  total: 0,
  loading: false,
  keyword: '',
  category: '',
  page: 1,
  pageSize: 20,

  fetchList: async () => {
    const { keyword, category, page, pageSize } = get();
    set({ loading: true });
    try {
      const res = await api.getFAQList({
        keyword,
        category,
        offset: (page - 1) * pageSize,
        limit: pageSize,
      });
      set({ items: res.items, total: res.total });
    } finally {
      set({ loading: false });
    }
  },

  setKeyword: (kw) => set({ keyword: kw, page: 1 }),
  setCategory: (cat) => set({ category: cat, page: 1 }),
  setPage: (p) => set({ page: p }),
  setPageSize: (ps) => set({ pageSize: ps, page: 1 }),

  create: async (data) => {
    await api.createFAQ(data);
    await get().fetchList();
  },

  update: async (id, data) => {
    await api.updateFAQ(id, data);
    await get().fetchList();
  },

  remove: async (id) => {
    await api.deleteFAQ(id);
    await get().fetchList();
  },
}));
