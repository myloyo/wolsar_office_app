import { useState } from "react";
import { Button, DatePicker, Progress, Tag } from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap, type EmployeeWeek } from "../api";
import { DataEditor, Load, useResource, type FieldSpec } from "./shared";
import type { Goal, Priority, Template } from "./types";

export function PlanningPanel({
  user,
  data,
}: {
  user: number;
  data: Bootstrap;
}) {
  const [period, setPeriod] = useState(dayjs().format("YYYY-MM"));
  const goals = useResource<Goal[]>(
    `/planning/goals?year=${period.slice(0, 4)}`,
    user,
  );
  const priorities = useResource<Priority[]>(
    `/planning/priorities?month=${period}`,
    user,
  );
  const templates = useResource<Template[]>("/planning/templates", user);
  const [editor, setEditor] = useState<{
    kind: string;
    id?: number;
    initial: Record<string, unknown>;
  }>();
  const [showReport, setShowReport] = useState(false);
  const actor = data.users.find((u) => u.id === user);
  const admin = actor?.roles.includes("admin");
  const departments = data.departments
    .filter(
      (d) =>
        admin ||
        (actor?.roles.includes("office") &&
          actor.department_ids.includes(d.id)),
    )
    .map((d) => ({ value: d.id, label: d.name }));
  const fields: Record<string, FieldSpec[]> = {
    goal: [
      { name: "title", label: "Годовая цель", required: true },
      {
        name: "year",
        label: "Год",
        type: "number",
        required: true,
        min: 2020,
        max: 2100,
      },
      {
        name: "department_id",
        label: "Отделение (пусто — вся церковь)",
        type: "select",
        options: departments,
      },
      {
        name: "progress",
        label: "Прогресс, %",
        type: "number",
        min: 0,
        max: 100,
        required: true,
      },
    ],
    priority: [
      { name: "title", label: "Приоритет месяца", required: true },
      { name: "month", label: "Месяц", type: "month", required: true },
      {
        name: "department_id",
        label: "Отделение",
        type: "select",
        options: departments,
        required: true,
      },
      {
        name: "goal_id",
        label: "Связанная годовая цель",
        type: "select",
        options: goals.data?.map((g) => ({ value: g.id, label: g.title })),
      },
      {
        name: "progress",
        label: "Прогресс, %",
        type: "number",
        min: 0,
        max: 100,
        required: true,
      },
    ],
    template: [
      { name: "name", label: "Название шаблона", required: true },
      {
        name: "sections",
        label: "Разделы плана",
        type: "tags",
        required: true,
      },
      {
        name: "review_fields",
        label: "Вопросы итогов",
        type: "tags",
        required: true,
      },
      { name: "approved", label: "Утверждён администратором", type: "check" },
    ],
  };
  return (
    <>
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Цели и приоритеты</h3>
          <DatePicker
            picker="month"
            allowClear={false}
            value={dayjs(period + "-01")}
            onChange={(date) => {
              if (date) setPeriod(date.format("YYYY-MM"));
            }}
          />
        </div>
        <div className="two-col">
          <div>
            <div className="section-heading">
              <h3>Годовые цели</h3>
              {admin && (
                <Button
                  size="small"
                  onClick={() =>
                    setEditor({
                      kind: "goal",
                      initial: {
                        year: Number(period.slice(0, 4)),
                        progress: 0,
                        department_id: null,
                      },
                    })
                  }
                >
                  Добавить
                </Button>
              )}
            </div>
            <Load loading={goals.loading} error={goals.error}>
              {goals.data?.map((g) => (
                <div className="list-row" key={g.id}>
                  <div>
                    <strong>{g.title}</strong>
                    <Progress
                      percent={g.progress}
                      size="small"
                      strokeColor="#ffb800"
                    />
                  </div>
                  {admin && (
                    <Button
                      size="small"
                      onClick={() =>
                        setEditor({ kind: "goal", id: g.id, initial: { ...g } })
                      }
                    >
                      Изменить
                    </Button>
                  )}
                </div>
              ))}
              {!goals.data?.length && <p className="muted">Целей пока нет</p>}
            </Load>
          </div>
          <div>
            <div className="section-heading">
              <h3>Приоритеты месяца</h3>
              {departments.length > 0 && (
                <Button
                  size="small"
                  onClick={() =>
                    setEditor({
                      kind: "priority",
                      initial: {
                        month: period,
                        department_id: departments[0]?.value,
                        progress: 0,
                        goal_id: null,
                      },
                    })
                  }
                >
                  Добавить
                </Button>
              )}
            </div>
            <Load loading={priorities.loading} error={priorities.error}>
              {priorities.data?.map((p) => (
                <div className="list-row" key={p.id}>
                  <div>
                    <strong>{p.title}</strong>
                    <small>
                      {
                        data.departments.find((d) => d.id === p.department_id)
                          ?.name
                      }
                    </small>
                    <Progress percent={p.progress} size="small" />
                  </div>
                  <Button
                    size="small"
                    onClick={() =>
                      setEditor({
                        kind: "priority",
                        id: p.id,
                        initial: { ...p },
                      })
                    }
                  >
                    Изменить
                  </Button>
                </div>
              ))}
              {!priorities.data?.length && (
                <p className="muted">Приоритетов пока нет</p>
              )}
            </Load>
          </div>
        </div>
      </section>
      {admin && (
        <section className="panel spaced">
          <div className="section-heading">
            <h3>Шаблоны недельного цикла</h3>
            <Button
              onClick={() =>
                setEditor({
                  kind: "template",
                  initial: {
                    sections: ["Основные задачи"],
                    review_fields: ["Что получилось", "Что переносим"],
                    approved: false,
                  },
                })
              }
            >
              Новый шаблон
            </Button>
          </div>
          {templates.data?.map((t) => (
            <div className="list-row" key={t.id}>
              <div>
                <strong>{t.name}</strong>
                <Tag color={t.approved ? "green" : "orange"}>
                  {t.approved ? "Утверждён" : "Черновик"}
                </Tag>
                <p className="muted">
                  План: {t.sections.join(" · ")}
                  <br />
                  Итоги: {t.review_fields.join(" · ")}
                </p>
              </div>
              <Button
                size="small"
                onClick={() =>
                  setEditor({ kind: "template", id: t.id, initial: { ...t } })
                }
              >
                Изменить
              </Button>
            </div>
          ))}
          <Button
            className="spaced"
            type="primary"
            onClick={() => setShowReport(!showReport)}
          >
            {showReport ? "Скрыть отчёт" : "Месячный отчёт"}
          </Button>
          {showReport && <MonthReport user={user} month={period} />}
        </section>
      )}
      {editor && (
        <DataEditor
          title={
            editor.kind === "template"
              ? "Шаблон недельного цикла"
              : "Планирование"
          }
          fields={fields[editor.kind]}
          initial={editor.initial}
          onClose={() => setEditor(undefined)}
          save={async (values) => {
            const base =
              editor.kind === "goal"
                ? "goals"
                : editor.kind === "priority"
                  ? "priorities"
                  : "templates";
            await api(
              `/planning/${base}${editor.id ? `/${editor.id}` : ""}`,
              user,
              editor.id ? "PUT" : "POST",
              values,
            );
            await goals.reload();
            await priorities.reload();
            await templates.reload();
          }}
        />
      )}
    </>
  );
}
function MonthReport({ user, month }: { user: number; month: string }) {
  const report = useResource<{
    month: string;
    basis: string;
    weeks: { week: string; employees: EmployeeWeek[] }[];
  }>(`/planning/report?month=${month}`, user);
  return (
    <Load loading={report.loading} error={report.error}>
      <p className="muted spaced">{report.data?.basis}</p>
      {report.data?.weeks.map((w) => (
        <div key={w.week} className="spaced">
          <h3>
            Неделя {dayjs(w.week).format("D MMMM")} —{" "}
            {dayjs(w.week).add(6, "day").format("D MMMM")}
          </h3>
          {w.employees.map((e) => (
            <article className="comment" key={e.user_id}>
              <strong>{e.name}</strong>{" "}
              <Tag>
                {e.plan.items.filter((i) => i.done).length} /{" "}
                {e.plan.items.length}
              </Tag>
              <Tag color={e.plan.closed_at ? "green" : "orange"}>
                {e.plan.closed_at ? "Закрыта" : "Не закрыта"}
              </Tag>
              <p className="preserve-lines">
                {e.plan.review || "Итоги не записаны"}
              </p>
            </article>
          ))}
        </div>
      ))}
    </Load>
  );
}
