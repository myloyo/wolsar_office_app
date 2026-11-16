import { useEffect, useState } from "react";
import {
  Alert,
  App,
  Button,
  Checkbox,
  DatePicker,
  Input,
  Progress,
  Skeleton,
  Space,
  Tag,
  Select,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { api, type Task, type Week } from "../../api";
import { planningWeek } from "../../date";
import { PageTitle } from "../../components/PageTitle";
import { Link } from "react-router-dom";
import { useResource } from "../../platform/shared";
import type { Priority, Template } from "../../platform/types";

export function WeekPage({ user }: { user: number }) {
  const current = planningWeek(dayjs().format("YYYY-MM-DD"));
  const [selected, setSelected] = useState(current);
  const [week, setWeek] = useState<Week>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [review, setReview] = useState("");
  const [saving, setSaving] = useState(false);
  const [retry, setRetry] = useState(0);
  const tasks = useResource<Task[]>("/tasks", user);
  const priorities = useResource<Priority[]>(
    "/planning/priorities?month=all",
    user,
  );
  const templates = useResource<Template[]>("/planning/templates", user);
  const template =
    templates.data?.find((t) => t.approved) || templates.data?.[0];
  const [taskId, setTaskId] = useState<number>();
  const [priorityId, setPriorityId] = useState<number>();
  const [section, setSection] = useState("main");
  const { message } = App.useApp();
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api<Week>(`/week?week=${selected}`, user)
      .then((w) => {
        if (active) {
          setWeek(w);
          setReview(w.review);
        }
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selected, user, retry]);
  const archived = selected !== current;
  const editable =
    !loading && !archived && week?.week === selected && !week.closed_at;
  async function mutate(path: string, method = "POST", body?: unknown) {
    setSaving(true);
    try {
      await api(path, user, method, body);
      setWeek(await api<Week>(`/week?week=${selected}`, user));
      return true;
    } catch (e) {
      message.error((e as Error).message);
      return false;
    } finally {
      setSaving(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ЛИЧНОЕ ПЛАНИРОВАНИЕ"
        title="Моя неделя"
        description="Среда — открываем. Вторник — подводим итоги."
        action={
          <Space>
            <Button
              aria-label="Предыдущая неделя"
              disabled={saving}
              onClick={() =>
                setSelected(
                  dayjs(selected).subtract(7, "day").format("YYYY-MM-DD"),
                )
              }
            >
              ←
            </Button>
            <DatePicker
              aria-label="Выбрать неделю"
              allowClear={false}
              value={dayjs(selected)}
              disabled={saving}
              format="DD.MM.YYYY"
              disabledDate={(day) =>
                day.isAfter(dayjs(current).add(6, "day"), "day")
              }
              onChange={(day) => {
                if (day) setSelected(planningWeek(day.format("YYYY-MM-DD")));
              }}
            />
            <Button
              aria-label="Следующая неделя"
              disabled={selected >= current || saving}
              onClick={() =>
                setSelected(dayjs(selected).add(7, "day").format("YYYY-MM-DD"))
              }
            >
              →
            </Button>
          </Space>
        }
      />
      {error ? (
        <Alert
          type="error"
          message={error}
          action={
            <Button onClick={() => setRetry(retry + 1)}>Повторить</Button>
          }
        />
      ) : loading ? (
        <Skeleton active />
      ) : (
        week && (
          <>
            <div className="week-stages">
              <div className={`stage ${week.opened ? "green" : ""}`}>
                <small>СРЕДА</small>
                <h3>{week.opened ? "Неделя открыта" : "Открываем неделю"}</h3>
                <span>Собираем план</span>
              </div>
              <div className="stage dark">
                <small>ЧТ — ПТ — ВС</small>
                <h3>Работа по плану</h3>
                <span>
                  {week.items.filter((i) => i.done).length} из{" "}
                  {week.items.length} выполнено
                </span>
              </div>
              <div className={`stage ${week.closed_at ? "green" : ""}`}>
                <small>ВТОРНИК</small>
                <h3>{week.closed_at ? "Неделя закрыта" : "Подводим итоги"}</h3>
                <span>
                  {week.closed_at
                    ? dayjs(week.closed_at).format("D MMM · HH:mm")
                    : "Сохранить итоги и закрыть"}
                </span>
              </div>
            </div>
            {archived && (
              <Alert
                className="spaced"
                type="info"
                message="Архив недели · только просмотр"
              />
            )}
            {week.closed_at && !archived && (
              <Alert
                className="spaced"
                type="success"
                message="Неделя закрыта"
                description="План и итоги сохранены. Для исправления возобновите неделю."
                action={
                  <Button
                    loading={saving}
                    onClick={() => void mutate("/week/reopen")}
                  >
                    Возобновить
                  </Button>
                }
              />
            )}
            {!week.opened && !archived && (
              <Button
                className="spaced"
                type="primary"
                loading={saving}
                onClick={() => void mutate("/week/open")}
              >
                Открыть неделю
              </Button>
            )}
            <section className="panel spaced">
              <div className="section-heading">
                <h3>
                  План на {dayjs(week.week).format("D MMMM")} —{" "}
                  {dayjs(week.week).add(6, "day").format("D MMMM")}
                </h3>
                <Tag>
                  {week.items.filter((i) => i.done).length} из{" "}
                  {week.items.length}
                </Tag>
              </div>
              <Progress
                percent={
                  week.items.length
                    ? Math.round(
                        (week.items.filter((i) => i.done).length /
                          week.items.length) *
                          100,
                      )
                    : 0
                }
                strokeColor="#ffb800"
                showInfo={false}
              />
              {!week.items.length && (
                <p className="muted spaced">План пока не заполнен</p>
              )}
              {week.items.map((item) => (
                <div className="week-item" key={item.id}>
                  <Checkbox
                    disabled={!editable || saving}
                    checked={item.done}
                    onChange={(e) =>
                      void mutate(`/week/items/${item.id}`, "PATCH", {
                        done: e.target.checked,
                      })
                    }
                  >
                    <span className={item.done ? "struck" : ""}>
                      {item.title}
                    </span>
                  </Checkbox>
                  <div className="pills">
                    {item.task_id && (
                      <Link to={`/tasks?task=${item.task_id}`}>
                        <Tag>Связанная задача</Tag>
                      </Link>
                    )}
                    {item.priority_id && (
                      <Tag>
                        {priorities.data?.find((p) => p.id === item.priority_id)
                          ?.title || "Приоритет месяца"}
                      </Tag>
                    )}
                    {item.carried_from_id && (
                      <Tag color="orange">Перенесено</Tag>
                    )}
                    {item.section && item.section !== "main" && (
                      <Tag>{item.section}</Tag>
                    )}
                  </div>
                </div>
              ))}
              {editable && (
                <div className="three-col spaced">
                  <Select
                    allowClear
                    aria-label="Связать пункт с задачей"
                    placeholder="Связанная задача"
                    options={tasks.data?.map((t) => ({
                      value: t.id,
                      label: t.title,
                    }))}
                    value={taskId}
                    onChange={(value) => {
                      setTaskId(value);
                      if (!title)
                        setTitle(
                          tasks.data?.find((t) => t.id === value)?.title || "",
                        );
                    }}
                  />
                  <Select
                    allowClear
                    aria-label="Связать пункт с приоритетом"
                    placeholder="Приоритет месяца"
                    options={priorities.data
                      ?.filter(
                        (p) =>
                          dayjs(p.month + "-01").isBefore(
                            dayjs(selected).add(7, "day"),
                          ) &&
                          dayjs(p.month + "-01")
                            .endOf("month")
                            .isAfter(dayjs(selected).subtract(1, "day")),
                      )
                      .map((p) => ({ value: p.id, label: p.title }))}
                    value={priorityId}
                    onChange={setPriorityId}
                  />
                  <Select
                    aria-label="Раздел плана"
                    value={section}
                    onChange={setSection}
                    options={[
                      { value: "main", label: "Основное" },
                      ...(template?.sections || []).map((value) => ({
                        value,
                        label: value,
                      })),
                    ]}
                  />
                </div>
              )}
              {editable && (
                <Space.Compact className="spaced" style={{ width: "100%" }}>
                  <Input
                    aria-label="Новый пункт плана"
                    placeholder="Новый пункт плана"
                    maxLength={240}
                    value={title}
                    disabled={saving}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                  <Button
                    loading={saving}
                    disabled={!title.trim()}
                    icon={<PlusOutlined />}
                    onClick={async () => {
                      if (
                        await mutate("/week/items", "POST", {
                          title,
                          task_id: taskId ?? null,
                          priority_id: priorityId ?? null,
                          section,
                        })
                      ) {
                        setTitle("");
                        setTaskId(undefined);
                        setPriorityId(undefined);
                      }
                    }}
                  >
                    Добавить
                  </Button>
                </Space.Compact>
              )}
            </section>
            <section className="panel spaced">
              <h3>Итоги недели</h3>
              {template && (
                <p className="muted">
                  {template.name} ·{" "}
                  {template.approved ? "утверждён" : "черновик"}
                  <br />
                  {template.review_fields.join(" · ")}
                </p>
              )}
              <p className="muted">
                Что получилось? Что мешало? Что переносим на следующую неделю?
              </p>
              {editable ? (
                <>
                  <Input.TextArea
                    aria-label="Итоги недели"
                    rows={5}
                    maxLength={10000}
                    value={review}
                    disabled={saving}
                    onChange={(e) => setReview(e.target.value)}
                  />
                  <div className="pills spaced">
                    <Button
                      loading={saving}
                      disabled={!review.trim() || review === week.review}
                      onClick={async () => {
                        if (
                          await mutate("/week/review", "PUT", { text: review })
                        )
                          message.success("Итоги сохранены");
                      }}
                    >
                      Сохранить итоги
                    </Button>
                    <Button
                      type="primary"
                      loading={saving}
                      disabled={
                        !week.items.length ||
                        !week.review.trim() ||
                        review !== week.review
                      }
                      onClick={async () => {
                        if (await mutate("/week/close"))
                          message.success("Неделя закрыта");
                      }}
                    >
                      Закрыть неделю
                    </Button>
                    {review !== week.review && (
                      <span className="muted">
                        Сначала сохраните изменения итогов
                      </span>
                    )}
                  </div>
                  <p className="muted spaced">
                    Невыполненные пункты не мешают закрытию: укажите в итогах,
                    что переносится дальше.
                  </p>
                </>
              ) : (
                <p className="preserve-lines">
                  {week.review || "Итоги не записаны"}
                </p>
              )}
            </section>
          </>
        )
      )}
    </>
  );
}
