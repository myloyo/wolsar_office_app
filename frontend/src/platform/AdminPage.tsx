import { useState } from "react";
import { Alert, App, Button, Input, Select, Space, Tag } from "antd";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource, type FieldSpec } from "./shared";
import type { ManagedUser, Room, SpaceInfo } from "./types";

const roles = [
  { value: "admin", label: "Администратор" },
  { value: "office", label: "Сотрудник офиса" },
  { value: "leader", label: "Лидер служения" },
  { value: "volunteer", label: "Служитель" },
];
export function AdminPage({
  user,
  data,
  onChanged,
}: {
  user: number;
  data: Bootstrap;
  onChanged: () => Promise<void>;
}) {
  const users = useResource<ManagedUser[]>("/admin/users", user);
  const ministries = useResource<SpaceInfo[]>("/spaces/ministry", user);
  const rooms = useResource<Room[]>("/rooms", user);
  const [editor, setEditor] = useState<{
    kind: string;
    initial?: Record<string, unknown>;
    id?: number;
  }>();
  const [link, setLink] = useState("");
  const { message } = App.useApp();
  const [ministry, setMinistry] = useState<number>();
  const members = useResource<SpaceInfo>(
    `/spaces/ministry/${ministry || ministries.data?.[0]?.id || 0}`,
    user,
  );
  const deptOptions = data.departments.map((d) => ({
    value: d.id,
    label: d.name,
  }));
  const people = (users.data || []).map((u) => ({
    value: u.id,
    label: u.name,
  }));
  const fields: Record<string, FieldSpec[]> = {
    recovery: [{ name: "email", label: "Новая почта", required: true }],
    invite: [
      { name: "email", label: "Почта", required: true },
      { name: "name", label: "Имя", required: true },
      {
        name: "roles",
        label: "Роли",
        type: "multi",
        options: roles,
        required: true,
      },
      {
        name: "department_ids",
        label: "Отделения",
        type: "multi",
        options: deptOptions,
      },
    ],
    user: [
      { name: "name", label: "Имя", required: true },
      {
        name: "roles",
        label: "Роли",
        type: "multi",
        options: roles,
        required: true,
      },
      {
        name: "department_ids",
        label: "Отделения",
        type: "multi",
        options: deptOptions,
      },
      { name: "active", label: "Учётная запись активна", type: "check" },
    ],
    department: [
      { name: "name", label: "Название", required: true },
      { name: "leader", label: "Руководитель" },
      { name: "description", label: "Описание", type: "textarea" },
    ],
    ministry: [
      { name: "name", label: "Название", required: true },
      {
        name: "department_id",
        label: "Отделение",
        type: "select",
        options: deptOptions,
        required: true,
      },
      { name: "description", label: "Описание", type: "textarea" },
      { name: "vision", label: "Видение", type: "textarea" },
    ],
    room: [{ name: "name", label: "Помещение", required: true }],
    member: [
      {
        name: "user_id",
        label: "Участник",
        type: "select",
        options: people,
        required: true,
      },
      { name: "leader", label: "Лидер служения", type: "check" },
    ],
  };
  return (
    <>
      <PageTitle
        eyebrow="УПРАВЛЕНИЕ"
        title="Команда и доступ"
        description="Приглашения, пользователи и структура церкви."
      />
      <div className="pills spaced">
        <Button
          type="primary"
          onClick={() =>
            setEditor({
              kind: "invite",
              initial: { roles: ["volunteer"], department_ids: [] },
            })
          }
        >
          Пригласить пользователя
        </Button>
        <Button
          onClick={() =>
            setEditor({
              kind: "department",
              initial: { leader: "Не назначен", description: "" },
            })
          }
        >
          Новое отделение
        </Button>
        <Button
          onClick={() =>
            setEditor({
              kind: "ministry",
              initial: {
                department_id: data.departments[0]?.id,
                description: "",
                vision: "",
              },
            })
          }
        >
          Новое служение
        </Button>
        <Button onClick={() => setEditor({ kind: "room" })}>
          Новое помещение
        </Button>
      </div>
      {link && (
        <Alert
          className="spaced"
          type="success"
          message="Приглашение создано · действует 3 дня"
          description={
            <>
              <p>
                Передайте ссылку приглашённому. Для входа потребуется код на
                указанную почту.
              </p>
              <Input readOnly value={link} />
            </>
          }
        />
      )}
      <section className="panel spaced">
        <h3>Пользователи</h3>
        <Load loading={users.loading} error={users.error}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Имя</th>
                  <th>Почта</th>
                  <th>Роли</th>
                  <th>Состояние</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {users.data?.map((u) => (
                  <tr key={u.id}>
                    <td>{u.name}</td>
                    <td>{u.email || "Не указана"}</td>
                    <td>
                      {u.roles
                        .map(
                          (r) => roles.find((role) => role.value === r)?.label,
                        )
                        .join(", ")}
                    </td>
                    <td>
                      <Tag color={u.active ? "green" : "orange"}>
                        {u.active ? "Активен" : "Приглашён / отключён"}
                      </Tag>
                    </td>
                    <td>
                      <Button
                        size="small"
                        onClick={() =>
                          setEditor({
                            kind: "user",
                            id: u.id,
                            initial: {
                              name: u.name,
                              roles: u.roles,
                              department_ids: u.department_ids,
                              active: u.active,
                            },
                          })
                        }
                      >
                        Изменить
                      </Button>
                      {u.id !== user && (
                        <Button
                          size="small"
                          onClick={() =>
                            setEditor({
                              kind: "recovery",
                              id: u.id,
                              initial: { email: u.email || "" },
                            })
                          }
                        >
                          Восстановить доступ
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Load>
        <p className="muted spaced">
          Изменение ролей или активности завершает сессии пользователя. Нельзя
          отключить себя или снять собственную роль администратора.
        </p>
      </section>
      <div className="two-col spaced">
        <section className="panel">
          <h3>Отделения</h3>
          {data.departments.map((d) => (
            <div className="list-row" key={d.id}>
              <span>{d.name}</span>
              <Button
                size="small"
                onClick={() =>
                  setEditor({
                    kind: "department",
                    id: d.id,
                    initial: {
                      name: d.name,
                      leader: d.leader,
                      description: d.description || "",
                    },
                  })
                }
              >
                Изменить
              </Button>
            </div>
          ))}
        </section>
        <section className="panel">
          <h3>Служения</h3>
          {ministries.data?.map((m) => (
            <div className="list-row" key={m.id}>
              <span>{m.name}</span>
              <Button
                size="small"
                onClick={() =>
                  setEditor({
                    kind: "ministry",
                    id: m.id,
                    initial: {
                      name: m.name,
                      department_id: m.department_id,
                      description: m.description,
                      vision: m.vision,
                    },
                  })
                }
              >
                Изменить
              </Button>
            </div>
          ))}
        </section>
      </div>
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Участники служения</h3>
          <Space wrap>
            <Select
              style={{ minWidth: 230 }}
              value={ministry || ministries.data?.[0]?.id}
              options={ministries.data?.map((m) => ({
                value: m.id,
                label: m.name,
              }))}
              onChange={setMinistry}
            />
            <Button
              disabled={!ministries.data?.length}
              onClick={() =>
                setEditor({ kind: "member", initial: { leader: false } })
              }
            >
              Добавить участника
            </Button>
          </Space>
        </div>
        {members.data?.members?.map((m) => (
          <div className="list-row" key={m.id}>
            <span>
              {m.name} {m.leader && <Tag>Лидер</Tag>}
            </span>
            <Space>
              <Button
                size="small"
                onClick={() =>
                  setEditor({
                    kind: "member",
                    initial: { user_id: m.id, leader: m.leader },
                  })
                }
              >
                Изменить роль
              </Button>
              <Button
                size="small"
                onClick={async () => {
                  try {
                    await api(
                      `/ministries/${members.data!.id}/members/${m.id}`,
                      user,
                      "DELETE",
                    );
                    await members.reload();
                    await onChanged();
                  } catch (e) {
                    message.error((e as Error).message);
                  }
                }}
              >
                Исключить
              </Button>
            </Space>
          </div>
        ))}
      </section>
      <section className="panel spaced">
        <h3>Помещения</h3>
        {rooms.data?.map((r) => (
          <Tag key={r.id}>{r.name}</Tag>
        ))}
      </section>
      {editor && (
        <DataEditor
          title={
            editor.kind === "invite"
              ? "Новое приглашение"
              : "Изменение структуры"
          }
          fields={fields[editor.kind]}
          initial={editor.initial}
          onClose={() => setEditor(undefined)}
          save={async (values) => {
            if (editor.kind === "invite" || editor.kind === "recovery") {
              const result = await api<{ invitation: string }>(
                editor.kind === "recovery"
                  ? `/admin/users/${editor.id}/recovery`
                  : "/admin/invitations",
                user,
                "POST",
                values,
              );
              setLink(
                `${location.origin}/login?invitation=${encodeURIComponent(result.invitation)}`,
              );
            } else {
              const base =
                editor.kind === "user"
                  ? `/admin/users/${editor.id}`
                  : editor.kind === "department"
                    ? `/departments${editor.id ? `/${editor.id}` : ""}`
                    : editor.kind === "ministry"
                      ? `/ministries${editor.id ? `/${editor.id}` : ""}`
                      : editor.kind === "room"
                        ? "/rooms"
                        : `/ministries/${members.data?.id}/members`;
              await api(
                base,
                user,
                editor.id || editor.kind === "member" ? "PUT" : "POST",
                values,
              );
            }
            await users.reload();
            await ministries.reload();
            await rooms.reload();
            await members.reload();
            if (editor.kind !== "invite") await onChanged();
          }}
        />
      )}
    </>
  );
}
