/**
 * Session types
 */

export const SessionStatus = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  FAILED: 'failed',
  ARCHIVED: 'archived',
  DELETED: 'deleted',
} as const;

export type SessionStatus = (typeof SessionStatus)[keyof typeof SessionStatus];

export interface SessionBase {
  title: string;
  status: SessionStatus;
  topic?: string | null;
  extra_data?: Record<string, any> | null;
}

export interface SessionCreate extends SessionBase {}

export interface SessionUpdate {
  title?: string | null;
  status?: SessionStatus | null;
  topic?: string | null;
  extra_data?: Record<string, any> | null;
}

export interface SessionPublic extends SessionBase {
  id: string;
  user_id: string;
  file_count: number;
  message_count: number;
  create_time: string;
  update_time: string;
}

export interface SessionsPublic {
  data: SessionPublic[];
  count: number;
}
