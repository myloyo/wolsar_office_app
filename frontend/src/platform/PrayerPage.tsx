import { useState } from "react";
import { Button, Tag } from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource } from "./shared";
import type { ChurchEvent } from "./types";

interface Prayer {
  id: number;
  title: string;
  details: string;
  creator_id: number;
  status: string;
  event_id: number | null;
}
export function PrayerPage({ user, data }: { user: number; data: Bootstrap }) {
  const resource = useResource<Prayer[]>("/prayers", user);
  const services = useResource<ChurchEvent[]>(
    `/services?year=${dayjs().year()}`,
    user,
  );
  const [adding, setAdding] = useState(false);
  const [link, setLink] = useState<Prayer>();
  const actor = data.users.find((u) => u.id === user);
  const canSchedule =
    actor?.roles.includes("admin") ||
    (actor?.roles.includes("office") && actor.department_ids.includes(1));
  return (
    <>
      <PageTitle
        eyebrow="ОСОБЫЕ МОЛИТВЫ"
        title="Заявки на молитву"
        description="Свои заявки видит автор; отделения Взаимодействия и Богослужения работают с общей очередью."
        action={
          <Button type="primary" onClick={() => setAdding(true)}>
            Новая заявка
          </Button>
        }
      />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data?.map((p) => (
          <section className="panel spaced" key={p.id}>
            <div className="section-heading">
              <h3>{p.title}</h3>
              <Tag color={p.status === "scheduled" ? "green" : "orange"}>
                {p.status === "scheduled"
                  ? "В расписании"
                  : "Ждёт рассмотрения"}
              </Tag>
            </div>
            <p className="preserve-lines">{p.details}</p>
            {p.event_id && (
              <p>
                Собрание:{" "}
                {services.data?.find((s) => s.id === p.event_id)?.title ||
                  p.event_id}
              </p>
            )}
            {canSchedule && (
              <Button onClick={() => setLink(p)}>Включить в собрание</Button>
            )}
          </section>
        ))}
        {!resource.data?.length && <p className="muted">Заявок пока нет</p>}
      </Load>
      {adding && (
        <DataEditor
          title="Заявка на молитву"
          fields={[
            { name: "title", label: "Краткое название", required: true },
            {
              name: "details",
              label: "Подробности для ответственных",
              type: "textarea",
            },
          ]}
          initial={{ details: "" }}
          onClose={() => setAdding(false)}
          save={async (values) => {
            await api("/prayers", user, "POST", values);
            await resource.reload();
          }}
        />
      )}
      {link && (
        <DataEditor
          title="Включить молитву в программу"
          fields={[
            {
              name: "event_id",
              label: "Собрание",
              type: "select",
              required: true,
              options: services.data?.map((e) => ({
                value: e.id,
                label: `${dayjs(e.starts_at).format("D MMM HH:mm")} · ${e.title}`,
              })),
            },
          ]}
          initial={{ event_id: link.event_id }}
          onClose={() => setLink(undefined)}
          save={async (values) => {
            await api(`/prayers/${link.id}/schedule`, user, "POST", values);
            await resource.reload();
          }}
        />
      )}
    </>
  );
}
