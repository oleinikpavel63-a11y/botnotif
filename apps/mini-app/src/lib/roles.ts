/**
 * UI-side role helpers. These mirror the backend RBAC for *convenience only* —
 * the backend re-checks every mutation, so hiding a control here is never a
 * security boundary.
 */
import type { Role } from '../types/contracts';

const RANK: Record<Role, number> = {
  VIEWER: 10,
  OPERATOR: 20,
  ADMIN: 30,
  OWNER: 40,
};

export const ROLE_LABELS: Record<Role, string> = {
  OWNER: 'Владелец',
  ADMIN: 'Администратор',
  OPERATOR: 'Оператор',
  VIEWER: 'Наблюдатель',
};

export const ALL_ROLES: Role[] = ['OWNER', 'ADMIN', 'OPERATOR', 'VIEWER'];

export function atLeast(role: Role, minimum: Role): boolean {
  return RANK[role] >= RANK[minimum];
}

/** Playback control (play/pause/resume/stop) — OPERATOR and up. */
export function canControlPlayback(role: Role): boolean {
  return atLeast(role, 'OPERATOR');
}

/** Emergency stop — ADMIN and up (also enforced server-side). */
export function canEmergencyStop(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

export function canManageTracks(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

export function canManageScenarios(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

export function canManageSchedules(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

/** Users screen visibility — ADMIN and up. OPERATOR/VIEWER are excluded. */
export function canViewUsers(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

export function canViewAudit(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}

/** Preview / audio playback of raw tracks — admin-only per spec. */
export function canPreviewTracks(role: Role): boolean {
  return atLeast(role, 'ADMIN');
}
