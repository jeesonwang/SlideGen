export const getErrorDetail = (error: unknown, fallback: string): string => {
  if (
    error &&
    typeof error === 'object' &&
    'detail' in error &&
    typeof error.detail === 'string'
  ) {
    return error.detail;
  }

  return fallback;
};
