export interface User {
  id: number;
  name: string;
  roles: string[];
  department_ids: number[];
}
export interface Department {
  id: number;
  name: string;
  leader: string;
  description?: string;
}
export interface Bootstrap {
  demo: boolean;
  current_user_id: number;
  users: User[];
  departments: Department[];
  ministry_ids: number[];
  led_ministry_ids: number[];
}
export type Status = "new" | "in_progress" | "done";
export type Category =
  "personal" | "leaders" | "responsible" | "information" | "ideas";
export const categories: Record<Category, string> = {
  personal: "Личные",
  leaders: "Лидеры",
  responsible: "Ответственный или соисполнитель",
  information: "Информационные задачи",
  ideas: "Идеи",
};
export interface Task {
  id: number;
  title: string;
  description: string;
  creator_id: number;
  assignee_id: number;
  department_id: number;
  due_date: string;
  category: Category;
  priority: "normal" | "high";
  status: Status;
  coexecutor_ids: number[];
  observer_ids: number[];
  result: string;
  version: number;
}
export interface TaskComment {
  id: number;
  task_id: number;
  author_id: number;
  text: string;
  created_at: string;
  deleted: boolean;
  edited_at: string | null;
}
export interface TaskChecklistItem {
  id: number;
  task_id: number;
  title: string;
  done: boolean;
  deleted: boolean;
}
export interface TaskDetail {
  task: Task;
  comments: TaskComment[];
  checklist: TaskChecklistItem[];
  can_edit: boolean;
  can_contribute: boolean;
}
export interface WeekItem {
  id: number;
  title: string;
  done: boolean;
  task_id?: number | null;
  priority_id?: number | null;
  section?: string;
  carried_from_id?: number | null;
}
export interface Week {
  week: string;
  items: WeekItem[];
  review: string;
  opened: boolean;
  closed_at: string | null;
  opened_at?: string | null;
  planned_at?: string | null;
  late?: boolean | null;
}
export interface EmployeeWeek {
  user_id: number;
  name: string;
  department_ids: number[];
  plan: Week;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export async function api<T>(
  path: string,
  user: number,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Demo-User": String(user),
      "X-CSRF-Token": csrfToken(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/"))
      window.dispatchEvent(new Event("auth-expired"));
    const error: unknown = await response.json().catch(() => null);
    throw new ApiError(
      response.status,
      error &&
        typeof error === "object" &&
        "detail" in error &&
        typeof error.detail === "string"
        ? error.detail
        : `Не удалось выполнить запрос (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}

export function csrfToken() {
  return decodeURIComponent(
    document.cookie
      .split("; ")
      .find((c) => c.startsWith("wolsar_csrf="))
      ?.split("=")[1] || "",
  );
}
