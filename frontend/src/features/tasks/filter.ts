import type { Task } from "../../api";

export type TaskFilter =
  "all" | "creator" | "assignee" | "coexecutor" | "observer" | "department";
export function filterTasks(
  tasks: Task[],
  user: number,
  departments: number[],
  filter: TaskFilter,
  query: string,
  showDone: boolean,
) {
  return tasks.filter((task) => {
    if (!showDone && task.status === "done") return false;
    if (
      !task.title
        .toLocaleLowerCase("ru")
        .includes(query.trim().toLocaleLowerCase("ru"))
    )
      return false;
    switch (filter) {
      case "creator":
        return task.creator_id === user;
      case "assignee":
        return task.assignee_id === user;
      case "coexecutor":
        return task.coexecutor_ids.includes(user);
      case "observer":
        return task.observer_ids.includes(user);
      case "department":
        return departments.includes(task.department_id);
      default:
        return true;
    }
  });
}
