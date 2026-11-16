import { useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  App,
  Button,
  Checkbox,
  Drawer,
  Empty,
  Input,
  Modal,
  Select,
  Skeleton,
  Space,
  Tag,
} from "antd";
import { EditOutlined, PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import {
  api,
  ApiError,
  categories,
  type Bootstrap,
  type Status,
  type Task,
  type TaskDetail,
} from "../../api";
import { TaskEditor } from "./TaskEditor";
import { Files } from "../../platform/Files";
import { RecurrencePanel } from "../../platform/RecurrencePanel";
import { DataEditor } from "../../platform/shared";

export function TaskPanel({
  taskId,
  user,
  data,
  onClose,
  onSaved,
}: {
  taskId?: number;
  user: number;
  data: Bootstrap;
  onClose: () => void;
  onSaved: (task: Task) => void;
}) {
  const [detail, setDetail] = useState<TaskDetail>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [editing, setEditing] = useState(false);
  const [elementEditor, setElementEditor] = useState<{
    kind: "comment" | "checklist";
    id: number;
    value: string;
  }>();
  const [comment, setComment] = useState("");
  const [itemTitle, setItemTitle] = useState("");
  const [result, setResult] = useState("");
  const mounted = useRef(true);
  const loadSerial = useRef(0);
  const { message } = App.useApp();
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const reload = useCallback(
    async (resetDrafts = true) => {
      if (!taskId) return;
      const requestId = ++loadSerial.current;
      if (resetDrafts) setLoading(true);
      setError("");
      try {
        const response = await api<TaskDetail>(`/tasks/${taskId}`, user);
        if (mounted.current && loadSerial.current === requestId) {
          setDetail(response);
          if (resetDrafts) setResult(response.task.result);
          setConflict(false);
          onSaved(response.task);
        }
      } catch (e) {
        if (mounted.current && loadSerial.current === requestId)
          setError((e as Error).message);
      } finally {
        if (mounted.current && loadSerial.current === requestId)
          setLoading(false);
      }
    },
    [taskId, user, onSaved],
  );
  useEffect(() => {
    void reload();
  }, [reload]);
  async function mutate(path: string, method: string, body: unknown) {
    if (!detail) return false;
    setSaving(true);
    try {
      await api(path, user, method, body);
      if (!mounted.current) return false;
      await reload(false);
      return true;
    } catch (e) {
      if (mounted.current) {
        message.error((e as Error).message);
        if (e instanceof ApiError && e.status === 409) setConflict(true);
      }
      return false;
    } finally {
      if (mounted.current) setSaving(false);
    }
  }
  const task = detail?.task;
  const canWork = detail?.can_contribute && !conflict;
  const name = (id: number) =>
    data.users.find((u) => u.id === id)?.name || `Участник ${id}`;
  return (
    <Drawer
      title="Карточка задачи"
      width={600}
      open={!!taskId}
      onClose={onClose}
      extra={
        <Button
          icon={<ReloadOutlined />}
          onClick={() => void reload()}
          disabled={loading || saving}
          aria-label="Обновить карточку"
        />
      }
    >
      {error ? (
        <Alert
          type="error"
          message={error}
          action={<Button onClick={() => void reload()}>Повторить</Button>}
        />
      ) : loading ? (
        <Skeleton active />
      ) : (
        detail &&
        task && (
          <>
            <div className="section-heading">
              <Tag>{categories[task.category]}</Tag>
              {detail.can_edit && (
                <Button
                  size="small"
                  icon={<EditOutlined />}
                  disabled={saving || conflict}
                  onClick={() => setEditing(true)}
                >
                  Редактировать
                </Button>
              )}
            </div>
            <h2>{task.title}</h2>
            <p className="preserve-lines">
              {task.description || "Описание пока не добавлено"}
            </p>
            <dl className="details">
              <dt>Постановщик</dt>
              <dd>{name(task.creator_id)}</dd>
              <dt>Исполнитель</dt>
              <dd>{name(task.assignee_id)}</dd>
              <dt>Соисполнители</dt>
              <dd>
                {task.coexecutor_ids.map(name).join(", ") || "Не назначены"}
              </dd>
              <dt>Наблюдатели</dt>
              <dd>{task.observer_ids.map(name).join(", ") || "Нет"}</dd>
              <dt>Отделение</dt>
              <dd>
                {
                  data.departments.find((d) => d.id === task.department_id)
                    ?.name
                }
              </dd>
              <dt>Срок</dt>
              <dd>{dayjs(task.due_date).format("D MMMM YYYY")}</dd>
              <dt>Приоритет</dt>
              <dd>{task.priority === "high" ? "Высокий" : "Обычный"}</dd>
            </dl>
            {conflict && (
              <Alert
                className="spaced"
                type="warning"
                message="Задача изменена другим участником"
                description="Обновите карточку перед следующим изменением."
                action={<Button onClick={() => void reload()}>Обновить</Button>}
              />
            )}
            {!detail.can_contribute && (
              <Alert
                className="spaced"
                type="info"
                message="Доступ только для просмотра"
              />
            )}
            <Select
              className="spaced"
              aria-label="Статус задачи"
              style={{ width: "100%" }}
              disabled={!canWork || saving}
              value={task.status}
              options={[
                { value: "new", label: "Новая" },
                { value: "in_progress", label: "В работе" },
                { value: "done", label: "Завершена" },
              ]}
              onChange={(status: Status) =>
                void mutate(`/tasks/${task.id}`, "PATCH", {
                  status,
                  expected_version: task.version,
                })
              }
            />
            <section className="task-section">
              <h3>
                Чек-лист{" "}
                <Tag>
                  {detail.checklist.filter((i) => i.done && !i.deleted).length}{" "}
                  / {detail.checklist.filter((i) => !i.deleted).length}
                </Tag>
              </h3>
              {detail.checklist.length ? (
                detail.checklist.map((item) => (
                  <div className="week-item" key={item.id}>
                    <Checkbox
                      disabled={!canWork || saving || item.deleted}
                      checked={item.done}
                      onChange={(e) =>
                        void mutate(
                          `/tasks/${task.id}/checklist/${item.id}`,
                          "PATCH",
                          { done: e.target.checked },
                        )
                      }
                    >
                      <span className={item.done ? "struck" : ""}>
                        {item.title}
                      </span>
                    </Checkbox>
                    {canWork && (
                      <Space>
                        <Button
                          size="small"
                          disabled={saving}
                          onClick={() =>
                            setElementEditor({
                              kind: "checklist",
                              id: item.id,
                              value: item.title,
                            })
                          }
                        >
                          Изменить
                        </Button>
                        <Button
                          size="small"
                          disabled={saving}
                          onClick={() =>
                            void mutate(
                              `/tasks/${task.id}/checklist/${item.id}${item.deleted ? "/restore" : ""}`,
                              item.deleted ? "POST" : "DELETE",
                              {},
                            )
                          }
                        >
                          {item.deleted ? "Восстановить" : "Удалить"}
                        </Button>
                      </Space>
                    )}
                  </div>
                ))
              ) : (
                <p className="muted">Пунктов пока нет</p>
              )}
              {canWork && (
                <Space.Compact style={{ width: "100%" }} className="spaced">
                  <Input
                    aria-label="Новый пункт чек-листа"
                    placeholder="Новый пункт"
                    maxLength={240}
                    value={itemTitle}
                    disabled={saving}
                    onChange={(e) => setItemTitle(e.target.value)}
                  />
                  <Button
                    icon={<PlusOutlined />}
                    disabled={!itemTitle.trim() || saving}
                    onClick={async () => {
                      if (
                        await mutate(`/tasks/${task.id}/checklist`, "POST", {
                          title: itemTitle,
                        })
                      )
                        setItemTitle("");
                    }}
                  >
                    Добавить
                  </Button>
                </Space.Compact>
              )}
            </section>
            <section className="task-section">
              <h3>Результат</h3>
              {canWork ? (
                <>
                  <Input.TextArea
                    aria-label="Результат задачи"
                    rows={3}
                    maxLength={10000}
                    value={result}
                    disabled={saving}
                    onChange={(e) => setResult(e.target.value)}
                  />
                  <Button
                    className="spaced"
                    disabled={saving || result === task.result}
                    onClick={() =>
                      void mutate(`/tasks/${task.id}`, "PATCH", {
                        result,
                        expected_version: task.version,
                      })
                    }
                  >
                    Сохранить результат
                  </Button>
                </>
              ) : (
                <p className="preserve-lines">
                  {task.result || "Результат ещё не записан"}
                </p>
              )}
            </section>
            <section className="task-section">
              <h3>Комментарии</h3>
              {detail.comments.length ? (
                detail.comments.map((c) => (
                  <article className="comment" key={c.id}>
                    <div>
                      <strong>{name(c.author_id)}</strong>
                      <time dateTime={c.created_at}>
                        {dayjs(c.created_at).format("D MMM · HH:mm")}
                      </time>
                    </div>
                    <p className="preserve-lines">{c.text}</p>
                    {(c.author_id === user ||
                      data.users
                        .find((u) => u.id === user)
                        ?.roles.includes("admin")) && (
                      <Space>
                        {!c.deleted && (
                          <Button
                            size="small"
                            disabled={saving}
                            onClick={() =>
                              setElementEditor({
                                kind: "comment",
                                id: c.id,
                                value: c.text,
                              })
                            }
                          >
                            Изменить
                          </Button>
                        )}
                        <Button
                          size="small"
                          disabled={saving}
                          onClick={() =>
                            void mutate(
                              `/tasks/${task.id}/comments/${c.id}${c.deleted ? "/restore" : ""}`,
                              c.deleted ? "POST" : "DELETE",
                              {},
                            )
                          }
                        >
                          {c.deleted ? "Восстановить" : "Удалить"}
                        </Button>
                      </Space>
                    )}
                  </article>
                ))
              ) : (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="Комментариев пока нет"
                />
              )}
              {canWork && (
                <>
                  <Input.TextArea
                    aria-label="Новый комментарий"
                    placeholder="Написать комментарий"
                    maxLength={10000}
                    rows={3}
                    value={comment}
                    disabled={saving}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <Button
                    className="spaced"
                    type="primary"
                    loading={saving}
                    disabled={!comment.trim()}
                    onClick={async () => {
                      if (
                        await mutate(`/tasks/${task.id}/comments`, "POST", {
                          text: comment,
                        })
                      )
                        setComment("");
                    }}
                  >
                    Отправить комментарий
                  </Button>
                </>
              )}
            </section>
            <Files
              scope="task"
              scopeId={task.id}
              user={user}
              canWrite={!!canWork}
            />
            <RecurrencePanel
              user={user}
              taskId={task.id}
              dueDate={task.due_date}
              canEdit={detail.can_edit}
            />
            {elementEditor && (
              <DataEditor
                title="Изменить элемент задачи"
                fields={[
                  {
                    name: elementEditor.kind === "comment" ? "text" : "title",
                    label: "Текст",
                    type: "textarea",
                    required: true,
                  },
                ]}
                initial={{
                  [elementEditor.kind === "comment" ? "text" : "title"]:
                    elementEditor.value,
                }}
                onClose={() => setElementEditor(undefined)}
                save={async (values) => {
                  const ok = await mutate(
                    `/tasks/${task.id}/${elementEditor.kind === "comment" ? "comments" : "checklist"}/${elementEditor.id}`,
                    "PUT",
                    values,
                  );
                  if (!ok) throw new Error("Не удалось сохранить изменение");
                }}
              />
            )}
            <Modal
              title="Редактировать задачу"
              open={editing}
              onCancel={() => setEditing(false)}
              footer={null}
              destroyOnClose
            >
              <TaskEditor
                data={data}
                user={user}
                task={task}
                onSaved={(updated) => {
                  if (!mounted.current) return;
                  setEditing(false);
                  onSaved(updated);
                  void reload();
                  message.success("Изменения сохранены");
                }}
              />
            </Modal>
          </>
        )
      )}
    </Drawer>
  );
}
