import type { SessionPublic } from '../../api/types/session.types';

export const isSidebarSessionPinned = (session: SessionPublic) =>
  session.extra_data?.pinned === true;

export const sortSidebarSessions = (sessions: SessionPublic[]) =>
  [...sessions].sort((left, right) => {
    const leftPinned = isSidebarSessionPinned(left);
    const rightPinned = isSidebarSessionPinned(right);

    if (leftPinned !== rightPinned) {
      return leftPinned ? -1 : 1;
    }

    return new Date(right.update_time).getTime() - new Date(left.update_time).getTime();
  });

export const togglePinnedExtraData = (
  extraData: Record<string, any> | null | undefined,
  pinned: boolean
) => ({
  ...(extraData || {}),
  pinned,
});
