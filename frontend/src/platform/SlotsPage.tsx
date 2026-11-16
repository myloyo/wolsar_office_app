import { useState } from "react";
import { App, Button, DatePicker, Tag } from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource } from "./shared";
import type { ChurchEvent, Slot, SpaceInfo } from "./types";

export function SlotsPage({ user, data }: { user: number; data: Bootstrap }) {
  const [year, setYear] = useState(dayjs().year());
  const slots = useResource<Slot[]>("/slots", user);
  const events = useResource<ChurchEvent[]>(
    `/events?start=${year}-01-01&end=${year}-12-31`,
    user,
  );
  const ministries = useResource<SpaceInfo[]>("/spaces/ministry", user);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();
  const admin = data.users.find((u) => u.id === user)?.roles.includes("admin");
  const managed = (ministries.data || []).filter(
    (m) => admin || data.led_ministry_ids?.includes(m.id),
  );
  return (
    <>
      <PageTitle
        eyebrow="СЛУЖИТЕЛИ"
        title="Запись на служение"
        description="Свободные места и запросы замены."
        action={
          managed.length > 0 && (
            <Button type="primary" onClick={() => setAdding(true)}>
              Создать слот
            </Button>
          )
        }
      />
      <DatePicker
        picker="year"
        allowClear={false}
        value={dayjs().year(year)}
        onChange={(date) => {
          if (date) setYear(date.year());
        }}
      />
      <Load loading={slots.loading} error={slots.error}>
        {slots.data
          ?.filter((slot) => events.data?.some((e) => e.id === slot.event_id))
          .map((slot) => {
            const event = events.data?.find((e) => e.id === slot.event_id);
            const active = slot.signups.filter((s) => s.status === "active");
            const signed = active.some((s) => s.user_id === user);
            return (
              <section className="panel spaced" key={slot.id}>
                <div className="section-heading">
                  <div>
                    <h3>{slot.title}</h3>
                    <p>
                      {event?.title} ·{" "}
                      {dayjs(event?.starts_at).format("D MMMM HH:mm")}
                    </p>
                  </div>
                  <Tag
                    color={active.length < slot.capacity ? "orange" : "green"}
                  >
                    {active.length} / {slot.capacity}
                  </Tag>
                </div>
                <p>
                  {active
                    .map(
                      (s) => data.users.find((u) => u.id === s.user_id)?.name,
                    )
                    .join(", ") || "Пока никто не записался"}
                </p>
                {slot.signups.some((s) => s.status === "replacement") &&
                  active.length < slot.capacity && (
                    <Tag color="red">Нужна замена</Tag>
                  )}
                <Button
                  loading={busy}
                  disabled={
                    (!signed && active.length >= slot.capacity) ||
                    event?.cancelled
                  }
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await api(
                        `/slots/${slot.id}/${signed ? "replacement" : "signup"}`,
                        user,
                        "POST",
                      );
                      await slots.reload();
                    } catch (e) {
                      message.error((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {signed ? "Не могу · найдите замену" : "Записаться"}
                </Button>
              </section>
            );
          })}
        {!slots.data?.length && (
          <p className="muted spaced">
            Слотов пока нет. Лидер служения создаёт их для событий календаря.
          </p>
        )}
      </Load>
      {adding && (
        <DataEditor
          title="Новый слот служения"
          fields={[
            {
              name: "event_id",
              label: "Событие",
              required: true,
              type: "select",
              options: events.data
                ?.filter((e) => !e.cancelled)
                .map((e) => ({
                  value: e.id,
                  label: `${dayjs(e.starts_at).format("D MMM HH:mm")} · ${e.title}`,
                })),
            },
            {
              name: "ministry_id",
              label: "Служение",
              required: true,
              type: "select",
              options: managed.map((m) => ({ value: m.id, label: m.name })),
            },
            {
              name: "title",
              label: "Позиция (звук, свет, встреча гостей)",
              required: true,
            },
            {
              name: "capacity",
              label: "Количество мест",
              required: true,
              type: "number",
              min: 1,
              max: 100,
            },
          ]}
          initial={{ capacity: 1, ministry_id: managed[0]?.id }}
          onClose={() => setAdding(false)}
          save={async (values) => {
            await api("/slots", user, "POST", values);
            await slots.reload();
          }}
        />
      )}
    </>
  );
}
