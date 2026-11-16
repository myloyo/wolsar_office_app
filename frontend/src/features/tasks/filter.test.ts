import { describe, expect, it } from "vitest";
import type { Task } from "../../api";
import { filterTasks } from "./filter";

const base: Task = {
  id: 1,
  title: "Подготовить ВСТРЕЧУ",
  description: "",
  creator_id: 1,
  assignee_id: 2,
  department_id: 4,
  due_date: "2026-11-08",
  category: "personal",
  priority: "normal",
  status: "new",
  coexecutor_ids: [3],
  observer_ids: [4],
  result: "",
  version: 1,
};
describe("Фильтры задач", () => {
  it("не смешивает исполнителя, соисполнителя и наблюдателя", () => {
    const assigneeTasks = filterTasks([base], 3, [], "assignee", "", false);
    const coexecutorTasks = filterTasks([base], 3, [], "coexecutor", "", false);
    const observerTasks = filterTasks([base], 4, [], "observer", "", false);
    const observerAsCoexecutor = filterTasks([base], 4, [], "coexecutor", "", false);

    expect(assigneeTasks).toEqual([]);
    expect(coexecutorTasks).toEqual([base]);
    expect(observerTasks).toEqual([base]);
    expect(observerAsCoexecutor).toEqual([]);
  });

  it("учитывает несколько отделений", () => {
    const other = { ...base, id: 2, department_id: 5 };
    const tasks = [base, other];

    const bothDepartments = filterTasks(tasks, 1, [4, 5], "department", "", false);
    const oneDepartment = filterTasks(tasks, 1, [4], "department", "", false);

    expect(bothDepartments).toHaveLength(2);
    expect(oneDepartment).toEqual([base]);
  });

  it("совмещает поиск и фильтр завершённых задач", () => {
    const done = { ...base, id: 2, status: "done" as const };
    const tasks = [base, done];

    const active = filterTasks(tasks, 1, [], "creator", "  встречу  ", false);
    const includingDone = filterTasks(tasks, 1, [], "creator", "встречу", true);
    const unrelated = filterTasks([base], 1, [], "creator", "другое", true);

    expect(active).toEqual([base]);
    expect(includingDone).toHaveLength(2);
    expect(unrelated).toHaveLength(0);
  });
});
