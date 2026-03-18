interface SidebarUserLike {
  username?: string | null;
  email?: string | null;
}

export interface SidebarUserPanelData {
  displayName: string;
  email: string;
  initials: string;
}

const getInitials = (name: string) =>
  name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

export const getSidebarUserPanelData = (
  user?: SidebarUserLike | null
): SidebarUserPanelData => {
  const displayName = user?.username || user?.email?.split('@')[0] || 'User';
  const email = user?.email || '';

  return {
    displayName,
    email,
    initials: getInitials(displayName),
  };
};
