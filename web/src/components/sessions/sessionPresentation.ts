import {
  InboxOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { SessionStatus, type SessionPublic } from '../../api/types/session.types.ts';

export interface SessionStatusPresentation {
  color: 'processing' | 'success' | 'error' | 'default' | 'warning';
  label: string;
  icon: typeof InboxOutlined;
}

export interface SessionSummary {
  total: number;
  active: number;
  archived: number;
}

export const getSessionStatusPresentation = (
  status: string
): SessionStatusPresentation => {
  switch (status) {
    case SessionStatus.ACTIVE:
      return {
        color: 'processing',
        label: 'Active',
        icon: ClockCircleOutlined,
      };
    case SessionStatus.COMPLETED:
      return {
        color: 'success',
        label: 'Completed',
        icon: CheckCircleOutlined,
      };
    case SessionStatus.FAILED:
      return {
        color: 'error',
        label: 'Failed',
        icon: CloseCircleOutlined,
      };
    case SessionStatus.ARCHIVED:
      return {
        color: 'default',
        label: 'Archived',
        icon: InboxOutlined,
      };
    case SessionStatus.DELETED:
      return {
        color: 'default',
        label: 'Deleted',
        icon: DeleteOutlined,
      };
    default:
      return {
        color: 'default',
        label: 'Unknown',
        icon: InboxOutlined,
      };
  }
};

export const getSessionMetaLine = (session: SessionPublic): string => {
  if (session.topic?.trim()) {
    return session.topic.trim();
  }

  return `Updated ${new Date(session.update_time).toLocaleDateString('en-US')}`;
};

export const getSessionSummary = (
  sessions: SessionPublic[]
): SessionSummary => {
  return sessions.reduce(
    (summary, session) => {
      summary.total += 1;
      if (session.status === SessionStatus.ACTIVE) {
        summary.active += 1;
      }
      if (session.status === SessionStatus.ARCHIVED) {
        summary.archived += 1;
      }
      return summary;
    },
    { total: 0, active: 0, archived: 0 }
  );
};
