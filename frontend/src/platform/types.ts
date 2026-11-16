import type { Task, Week } from "../api";
export interface SpaceInfo {
  id: number;
  name: string;
  description: string;
  vision?: string;
  leader?: string;
  department_id?: number;
  members?: { id: number; name: string; leader: boolean }[];
  posts?: { id: number; author_id: number; text: string; created_at: string }[];
  projects?: {
    id: number;
    title: string;
    description: string;
    status: string;
  }[];
}
export interface ManagedUser {
  id: number;
  name: string;
  email: string | null;
  roles: string[];
  department_ids: number[];
  active: boolean;
}
export interface Room {
  id: number;
  name: string;
}
export interface ChurchEvent {
  id: number;
  title: string;
  starts_at: string;
  ends_at: string;
  kind: "worship" | "event" | "training";
  scope: "common" | "department" | "ministry";
  scope_id: number | null;
  room_id: number | null;
  version: number;
  cancelled: boolean;
  creator_id: number;
  assignments?: Record<string,number|null>;
  mc?: Mc;
}
export interface Slot {
  id: number;
  event_id: number;
  ministry_id: number;
  title: string;
  capacity: number;
  signups: { user_id: number; status: string }[];
}
export interface Block {
  id: string;
  name: string;
  minutes: number;
  owner_id: number | null;
  note: string;
}
export interface Mc {
  host_id: number | null;
  value: string;
  text: string;
  story: string;
  slides: string;
  ready: boolean;
}
export interface Ceremony {
  event: ChurchEvent;
  program: {
    blocks: Block[];
    assignments: Record<string, number | null>;
    mc: Mc;
  };
  timer: {
    index: number;
    remaining: number;
    running: boolean;
    started_at: string | null;
  };
  version: number;
}
export interface Priority {
  id: number;
  title: string;
  month: string;
  department_id: number;
  goal_id: number | null;
  progress: number;
}
export interface Goal {
  id: number;
  title: string;
  year: number;
  department_id: number | null;
  progress: number;
}
export interface Template {
  id: number;
  name: string;
  sections: string[];
  review_fields: string[];
  approved: boolean;
}
export interface Person {
  id: number;
  name: string;
  roles: string[];
  department_ids: number[];
  tasks: Task[];
  plan: Week | null;
}
