/**
 * Authentication and User related types
 */

export interface UserBase {
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  username?: string | null;
}

export interface UserPublic extends UserBase {
  id: string;
}

export interface UserRegister {
  email: string;
  password: string;
  username?: string | null;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  username?: string | null;
}

export interface UpdatePassword {
  current_password: string;
  new_password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string; // email is used as username
  password: string;
}

export interface UsersPublic {
  data: UserPublic[];
  count: number;
}
