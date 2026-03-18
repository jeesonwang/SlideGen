import type { UserPublic } from '../../api/types/auth.types';

export const shouldRedirectFromLogin = (
  isAuthenticated: boolean,
  user: UserPublic | null | undefined
): boolean => {
  return isAuthenticated && !!user;
};
