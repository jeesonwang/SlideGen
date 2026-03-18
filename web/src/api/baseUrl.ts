export const resolveApiBaseUrl = (
  explicitBaseUrl: string | undefined,
  isDev: boolean
): string => {
  if (explicitBaseUrl) {
    return explicitBaseUrl;
  }

  return isDev ? '' : 'http://127.0.0.1:7860';
};

export const buildApiUrl = (
  path: string,
  explicitBaseUrl: string | undefined,
  isDev: boolean
): string => {
  const baseUrl = resolveApiBaseUrl(explicitBaseUrl, isDev);

  if (!baseUrl) {
    return path;
  }

  return new URL(path, baseUrl).toString();
};
