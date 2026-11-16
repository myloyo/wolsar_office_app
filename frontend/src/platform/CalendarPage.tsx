import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button, Checkbox, Space, Tag } from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource } from "./shared";
import type { ChurchEvent, Room, SpaceInfo } from "./types";

export function CalendarPage({
  user,
  data,
}: {
  user: number;
  data: Bootstrap;
}) {
  const [month, setMonth] = useState(dayjs().startOf("month"));
  const [params] = useSearchParams();
  const [editing, setEditing] = useState<ChurchEvent | "new">();
  const [kinds, setKinds] = useState(["worship", "event", "training"]);
  const start = month.subtract((month.day() + 6) % 7, "day");
  const end = start.add(41, "day");
  const resource = useResource<ChurchEvent[]>(
    `/events?start=${start.format("YYYY-MM-DD")}&end=${end.format("YYYY-MM-DD")}`,
    user,
  );
  const rooms = useResource<Room[]>("/rooms", user);
  const ministries = useResource<SpaceInfo[]>("/spaces/ministry", user);
  const actor = data.users.find((u) => u.id === user);
  const admin = actor?.roles.includes("admin");
  const office = actor?.roles.includes("office");
  const choices = [
    ...(office || admin
      ? [{ value: "common", label: "Общий календарь церкви" }]
      : []),
    ...data.departments
      .filter((d) => admin || (office && actor?.department_ids.includes(d.id)))
      .map((d) => ({ value: `department:${d.id}`, label: d.name })),
    ...(ministries.data || [])
      .filter((m) => admin || data.led_ministry_ids?.includes(m.id))
      .map((m) => ({ value: `ministry:${m.id}`, label: m.name })),
  ];
  const scopeFilter = params.get("scope");
  const scopeId = Number(params.get("scope_id"));
  const days = Array.from({ length: 42 }, (_, i) => start.add(i, "day"));
  return (
    <>
      <PageTitle
        eyebrow="КАЛЕНДАРЬ ЦЕРКВИ"
        title={month.format("MMMM YYYY")}
        description="События и бронирование помещений с сохранением на сервере."
        action={
          choices.length > 0 && (
            <Button type="primary" onClick={() => setEditing("new")}>
              Новое событие
            </Button>
          )
        }
      />
      <div className="toolbar">
        <Space>
          <Button onClick={() => setMonth(month.subtract(1, "month"))}>
            ←
          </Button>
          <Button onClick={() => setMonth(dayjs().startOf("month"))}>
            Сегодня
          </Button>
          <Button onClick={() => setMonth(month.add(1, "month"))}>→</Button>
        </Space>
        <Checkbox.Group
          value={kinds}
          onChange={setKinds}
          options={[
            { value: "worship", label: "Богослужения" },
            { value: "event", label: "Мероприятия" },
            { value: "training", label: "Обучение" },
          ]}
        />
      </div>
      <Load loading={resource.loading} error={resource.error}>
        <div className="calendar-grid">
          {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
            <div className="calendar-weekday" key={d}>
              {d}
            </div>
          ))}
          {days.map((day) => (
            <div
              key={day.format("YYYY-MM-DD")}
              className={`calendar-cell ${day.month() !== month.month() ? "outside" : ""} ${day.isSame(dayjs(), "day") ? "today" : ""}`}
            >
              <strong>{day.date()}</strong>
              {resource.data
                ?.filter(
                  (e) =>
                    kinds.includes(e.kind) &&
                    (!scopeFilter ||
                      (e.scope === scopeFilter && e.scope_id === scopeId)) &&
                    dayjs(e.starts_at).isBefore(
                      day.add(1, "day").startOf("day"),
                    ) &&
                    dayjs(e.ends_at).isAfter(day.startOf("day")),
                )
                .map((e) => (
                  <button
                    key={e.id}
                    className={`calendar-event calendar-event-button ${e.kind === "worship" ? "worship" : ""}`}
                    onClick={() => setEditing(e)}
                  >
                    <span className={e.cancelled ? "struck" : ""}>
                      {dayjs(e.starts_at).format("HH:mm")} · {e.title}
                    </span>
                    {e.room_id && (
                      <small>
                        {rooms.data?.find((r) => r.id === e.room_id)?.name}
                      </small>
                    )}
                    {e.cancelled && <Tag>Отменено</Tag>}
                  </button>
                ))}
            </div>
          ))}
        </div>
      </Load>
      {editing && (
        <DataEditor
          readOnly={editing!=='new'&&!(admin||(editing.scope==='common'?office:editing.scope==='department'?office&&actor?.department_ids.includes(editing.scope_id||0):data.led_ministry_ids?.includes(editing.scope_id||0)))}
          title={editing === "new" ? "Новое событие" : "Событие календаря"}
          fields={[
            { name: "title", label: "Название", required: true },
            {
              name: "starts_at",
              label: "Начало",
              type: "datetime",
              required: true,
            },
            {
              name: "ends_at",
              label: "Окончание",
              type: "datetime",
              required: true,
            },
            {
              name: "kind",
              label: "Тип",
              type: "select",
              required: true,
              options: [
                { value: "worship", label: "Богослужение" },
                { value: "event", label: "Мероприятие" },
                { value: "training", label: "Обучение" },
              ],
            },
            {
              name: "scope_key",
              label: "Календарь",
              type: "select",
              options: choices,
              required: true,
            },
            {
              name: "room_id",
              label: "Помещение",
              type: "select",
              options: rooms.data?.map((r) => ({ value: r.id, label: r.name })),
            },
            { name: "cancelled", label: "Событие отменено", type: "check" },
          ]}
          initial={
            editing === "new"
              ? {
                  starts_at: dayjs().hour(10).minute(0).toISOString(),
                  ends_at: dayjs().hour(11).minute(0).toISOString(),
                  kind: "event",
                  scope_key:
                    choices.find((c) => c.value === `${scopeFilter}:${scopeId}`)
                      ?.value || choices[0]?.value,
                  cancelled: false,
                }
              : {
                  ...editing,
                  scope_key:
                    editing.scope === "common"
                      ? "common"
                      : `${editing.scope}:${editing.scope_id}`,
                }
          }
          onClose={() => setEditing(undefined)}
          save={async (values) => {
            const { scope_key, ...rest } = values;
            const [scope, id] = String(scope_key).split(":");
            await api(
              editing === "new" ? "/events" : `/events/${editing.id}`,
              user,
              editing === "new" ? "POST" : "PUT",
              {
                ...rest,
                scope,
                scope_id: id ? Number(id) : null,
                room_id: values.room_id || null,
                expected_version:
                  editing === "new" ? undefined : editing.version,
              },
            );
            await resource.reload();
          }}
        />
      )}
    </>
  );
}
