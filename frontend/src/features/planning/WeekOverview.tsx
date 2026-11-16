import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  DatePicker,
  Drawer,
  Empty,
  Progress,
  Skeleton,
  Space,
  Tag,
} from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap, type EmployeeWeek } from "../../api";
import { planningWeek } from "../../date";

export function WeekOverview({
  user,
  data,
}: {
  user: number;
  data: Bootstrap;
}) {
  const current = planningWeek(dayjs().format("YYYY-MM-DD"));
  const [week, setWeek] = useState(current);
  const [rows, setRows] = useState<EmployeeWeek[]>();
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [selected, setSelected] = useState<EmployeeWeek>();
  useEffect(() => {
    let active = true;
    setRows(undefined);
    setError("");
    setSelected(undefined);
    api<EmployeeWeek[]>(`/planning/weeks?week=${week}`, user)
      .then((response) => {
        if (active) setRows(response);
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      });
    return () => {
      active = false;
    };
  }, [week, user, retry]);
  return (
    <section className="panel spaced">
      <div className="section-heading">
        <div>
          <h3>Недельные планы сотрудников</h3>
          <p className="muted">
            {dayjs(week).format("D MMMM")} —{" "}
            {dayjs(week).add(6, "day").format("D MMMM")}
          </p>
        </div>
        <Space wrap>
          <DatePicker
            aria-label="Неделя в сводке"
            value={dayjs(week)}
            allowClear={false}
            format="DD.MM.YYYY"
            disabledDate={(day) =>
              day.isAfter(dayjs(current).add(6, "day"), "day")
            }
            onChange={(day) => {
              if (day) setWeek(planningWeek(day.format("YYYY-MM-DD")));
            }}
          />
          <Button onClick={() => setRetry(retry + 1)}>Обновить</Button>
        </Space>
      </div>
      {error ? (
        <Alert type="error" message={error} />
      ) : !rows ? (
        <Skeleton active />
      ) : (
        <>
          <div className="pills spaced">
            <Tag color="green">
              План есть: {rows.filter((r) => r.plan.items.length > 0).length}
            </Tag>
            <Tag color="orange">
              Без плана: {rows.filter((r) => !r.plan.items.length).length}
            </Tag>
            <Tag color="blue">
              Закрыли неделю: {rows.filter((r) => r.plan.closed_at).length}
            </Tag>
          </div>
          <div className="table-wrap spaced">
            <table>
              <thead>
                <tr>
                  <th>Сотрудник</th>
                  <th>Отделения</th>
                  <th>Планирование</th>
                  <th>Выполнение</th>
                  <th>Итоги</th>
                  <th>План</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.user_id}>
                    <td>
                      <strong>{row.name}</strong>
                    </td>
                    <td>
                      {row.department_ids
                        .map(
                          (id) =>
                            data.departments.find((d) => d.id === id)?.name,
                        )
                        .filter(Boolean)
                        .join(", ") || "—"}
                    </td>
                    <td>
                      <Tag color={row.plan.items.length ? "green" : "orange"}>
                        {row.plan.items.length
                          ? "План заполнен"
                          : row.plan.opened
                            ? "Открыта без плана"
                            : "Не открыта"}
                      </Tag>
                      {row.plan.late && <Tag color="red">План позже среды</Tag>}
                    </td>
                    <td>
                      <Progress
                        size="small"
                        percent={
                          row.plan.items.length
                            ? Math.round(
                                (row.plan.items.filter((i) => i.done).length /
                                  row.plan.items.length) *
                                  100,
                              )
                            : 0
                        }
                        strokeColor="#ffb800"
                      />
                    </td>
                    <td>
                      <Tag
                        color={
                          row.plan.closed_at
                            ? "green"
                            : row.plan.review
                              ? "blue"
                              : "default"
                        }
                      >
                        {row.plan.closed_at
                          ? "Неделя закрыта"
                          : row.plan.review
                            ? "Итоги сохранены"
                            : "Нет итогов"}
                      </Tag>
                    </td>
                    <td>
                      <Button size="small" onClick={() => setSelected(row)}>
                        Открыть
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!rows.length && <Empty description="Сотрудников офиса пока нет" />}
          </div>
        </>
      )}
      <Drawer
        open={!!selected}
        onClose={() => setSelected(undefined)}
        title={selected?.name}
        width={540}
      >
        {selected && (
          <>
            <p className="muted">
              Неделя {dayjs(selected.plan.week).format("D MMMM")} —{" "}
              {dayjs(selected.plan.week).add(6, "day").format("D MMMM")}
            </p>
            <h3>Недельный план</h3>
            {selected.plan.items.length ? (
              selected.plan.items.map((i) => (
                <div className="list-row" key={i.id}>
                  <span className={i.done ? "struck" : ""}>{i.title}</span>
                  <Tag color={i.done ? "green" : "default"}>
                    {i.done ? "Готово" : "В плане"}
                  </Tag>
                </div>
              ))
            ) : (
              <p className="muted">План не заполнен</p>
            )}
            <h3 className="spaced">Итоги недели</h3>
            <p className="preserve-lines">
              {selected.plan.review || "Итоги не записаны"}
            </p>
            {selected.plan.closed_at && (
              <Tag color="green">
                Закрыта {dayjs(selected.plan.closed_at).format("D MMM HH:mm")}
              </Tag>
            )}
          </>
        )}
      </Drawer>
    </section>
  );
}
