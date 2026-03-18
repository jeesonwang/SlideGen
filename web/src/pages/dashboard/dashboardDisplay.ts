interface DashboardIdentity {
  username?: string | null;
  email?: string | null;
}

export const getDashboardGreetingName = ({
  username,
  email,
}: DashboardIdentity): string => {
  const normalizedUsername = username?.trim();
  if (normalizedUsername) {
    if (!normalizedUsername.includes('@')) {
      return normalizedUsername;
    }

    return normalizedUsername.split('@')[0] || 'there';
  }

  if (email?.trim()) {
    return email.trim().split('@')[0] || 'there';
  }

  return 'there';
};
