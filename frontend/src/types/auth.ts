export interface UserResponse {
  id: number;
  username?: string | null;
  email?: string | null;
  phone?: string | null;
  role: 'user' | 'staff' | 'admin' | string;
  is_active: boolean;
  created_at?: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}
