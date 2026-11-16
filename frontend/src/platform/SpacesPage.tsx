import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { App, Button, Input, Tag } from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { Files } from "./Files";
import { DataEditor, Load, useResource } from "./shared";
import type { Person, SpaceInfo } from "./types";

export function SpacesPage({ kind, user }: { kind: string; user: number }) {
  const resource = useResource<SpaceInfo[]>(`/spaces/${kind}`, user);
  return (
    <>
      <PageTitle
        eyebrow="ПРОСТРАНСТВА"
        title={kind === "ministry" ? "Служения" : "Отделения"}
        description="Команда, проекты, объявления и файлы."
      />
      <Load loading={resource.loading} error={resource.error}>
        <div className="two-col">
          {resource.data?.map((s) => (
            <Link
              key={s.id}
              to={`/spaces/${kind}/${s.id}`}
              className="panel link-panel"
            >
              <h3>{s.name}</h3>
              <p>{s.description || "Описание ещё не добавлено"}</p>
              <span>Открыть пространство →</span>
            </Link>
          ))}
        </div>
        {!resource.data?.length && (
          <p className="muted">У вас пока нет доступных пространств.</p>
        )}
      </Load>
    </>
  );
}
export function SpacePage({ user, data }: { user: number; data: Bootstrap }) {
  const { scope = "department", id = "0" } = useParams();
  const resource = useResource<SpaceInfo>(`/spaces/${scope}/${id}`, user);
  const [post, setPost] = useState("");
  const [editing, setEditing] = useState(false);
  const [project, setProject] = useState(false);
  const { message } = App.useApp();
  const actor = data.users.find((u) => u.id === user);
  const canWrite =
    actor?.roles.includes("admin") ||
    (scope === "department"
      ? actor?.roles.includes("office") &&
        actor.department_ids.includes(Number(id))
      : data.led_ministry_ids?.includes(Number(id)));
  return (
    <>
      <PageTitle
        eyebrow="ПРОСТРАНСТВО"
        title={resource.data?.name || "Загрузка"}
        action={
          canWrite && (
            <Button onClick={() => setEditing(true)}>Изменить описание</Button>
          )
        }
      />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data && (
          <>
            <section className="panel">
              <p className="preserve-lines">
                {resource.data.description || "Описание не заполнено"}
              </p>
              {resource.data.vision && (
                <>
                  <h3>Видение</h3>
                  <p className="preserve-lines">{resource.data.vision}</p>
                </>
              )}
              <h3>Команда</h3>
              {resource.data.members?.map((m) => (
                <div className="list-row" key={m.id}>
                  <Link to={`/people/${m.id}`}>{m.name}</Link>
                  {m.leader && <Tag>Лидер</Tag>}
                </div>
              ))}
              <Link to={`/calendar?scope=${scope}&scope_id=${id}`}>
                <Button className="spaced">Календарь пространства</Button>
              </Link>
            </section>
            <div className="two-col spaced">
              <section className="panel">
                <div className="section-heading">
                  <h3>Лента объявлений</h3>
                </div>
                {canWrite && (
                  <>
                    <Input.TextArea
                      aria-label="Новое объявление"
                      value={post}
                      onChange={(e) => setPost(e.target.value)}
                      rows={3}
                      maxLength={10000}
                    />
                    <Button
                      className="spaced"
                      disabled={!post.trim()}
                      onClick={async () => {
                        try {
                          await api(
                            `/spaces/${scope}/${id}/posts`,
                            user,
                            "POST",
                            { text: post },
                          );
                          setPost("");
                          await resource.reload();
                        } catch (e) {
                          message.error((e as Error).message);
                        }
                      }}
                    >
                      Опубликовать
                    </Button>
                  </>
                )}
                {resource.data.posts?.map((p) => (
                  <article className="comment spaced" key={p.id}>
                    <div>
                      <strong>
                        {data.users.find((u) => u.id === p.author_id)?.name}
                      </strong>
                      <time>{dayjs(p.created_at).format("D MMM HH:mm")}</time>
                    </div>
                    <p className="preserve-lines">{p.text}</p>
                  </article>
                ))}
                {!resource.data.posts?.length && (
                  <p className="muted spaced">Объявлений пока нет</p>
                )}
              </section>
              <section className="panel">
                <div className="section-heading">
                  <h3>Проекты</h3>
                  {canWrite && (
                    <Button onClick={() => setProject(true)}>
                      Новый проект
                    </Button>
                  )}
                </div>
                {resource.data.projects?.map((p) => (
                  <div className="list-row" key={p.id}>
                    <div>
                      <strong>{p.title}</strong>
                      <p>{p.description}</p>
                    </div>
                    <Tag>{p.status === "active" ? "В работе" : "Завершён"}</Tag>
                  </div>
                ))}
                <Files
                  scope={scope}
                  scopeId={Number(id)}
                  user={user}
                  canWrite={!!canWrite}
                />
              </section>
            </div>
          </>
        )}
      </Load>
      {project && (
        <DataEditor
          title="Новый проект"
          fields={[
            { name: "title", label: "Название", required: true },
            { name: "description", label: "Описание", type: "textarea" },
          ]}
          initial={{ description: "" }}
          onClose={() => setProject(false)}
          save={async (values) => {
            await api(`/spaces/${scope}/${id}/projects`, user, "POST", values);
            await resource.reload();
          }}
        />
      )}
      {editing && resource.data && (
        <DataEditor
          title="Описание пространства"
          fields={[
            { name: "name", label: "Название", required: true },
            { name: "description", label: "Описание", type: "textarea" },
            ...(scope === "ministry"
              ? [
                  {
                    name: "vision",
                    label: "Видение",
                    type: "textarea" as const,
                  },
                ]
              : [{ name: "leader", label: "Руководитель" }]),
          ]}
          initial={{ ...resource.data }}
          onClose={() => setEditing(false)}
          save={async (values) => {
            await api(
              `/${scope === "ministry" ? "ministries" : "departments"}/${id}`,
              user,
              "PUT",
              scope === "ministry"
                ? { ...values, department_id: resource.data!.department_id }
                : values,
            );
            await resource.reload();
          }}
        />
      )}
    </>
  );
}
export function PersonPage({ user }: { user: number }) {
  const { id } = useParams();
  const resource = useResource<Person>(`/people/${id}`, user);
  return (
    <>
      <PageTitle
        eyebrow="СОТРУДНИК"
        title={resource.data?.name || "Страница сотрудника"}
      />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data && (
          <>
            <section className="panel">
              <h3>Задачи</h3>
              {resource.data.tasks.map((t) => (
                <Link
                  className="list-row"
                  key={t.id}
                  to={`/tasks?task=${t.id}`}
                >
                  <span>{t.title}</span>
                  <Tag>{t.status === "done" ? "Завершена" : "В работе"}</Tag>
                </Link>
              ))}
            </section>
            {resource.data.plan && (
              <section className="panel spaced">
                <h3>План текущей недели</h3>
                {resource.data.plan.items.map((i) => (
                  <div className="list-row" key={i.id}>
                    <span className={i.done ? "struck" : ""}>{i.title}</span>
                    <Tag>{i.done ? "Готово" : "В плане"}</Tag>
                  </div>
                ))}
                <h3 className="spaced">Итоги</h3>
                <p className="preserve-lines">
                  {resource.data.plan.review || "Ещё не записаны"}
                </p>
              </section>
            )}
          </>
        )}
      </Load>
    </>
  );
}
