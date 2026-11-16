import { useState } from "react";
import { App, Button, Checkbox, Tag } from "antd";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource } from "./shared";
import type { SpaceInfo } from "./types";

interface Preparation {
  id: number;
  title: string;
  kind: string;
  ministry_id: number;
  steps: string[];
  completed: number[];
}
export function PreparationsPage({
  user,
  data,
}: {
  user: number;
  data: Bootstrap;
}) {
  const resource = useResource<Preparation[]>("/preparations", user);
  const ministries = useResource<SpaceInfo[]>("/spaces/ministry", user);
  const [adding, setAdding] = useState(false);
  const { message } = App.useApp();
  const admin = data.users.find((u) => u.id === user)?.roles.includes("admin");
  const managed =
    ministries.data?.filter(
      (m) => admin || data.led_ministry_ids?.includes(m.id),
    ) || [];
  return (
    <>
      <PageTitle
        eyebrow="МЕРОПРИЯТИЯ"
        title="Праздники и конференции"
        description="Подготовка мероприятий служений с сохранением шагов."
        action={
          managed.length > 0 && (
            <Button type="primary" onClick={() => setAdding(true)}>
              Планировать мероприятие
            </Button>
          )
        }
      />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data?.map((p) => (
          <section className="panel spaced" key={p.id}>
            <div className="section-heading">
              <h3>{p.title}</h3>
              <Tag>{p.kind}</Tag>
            </div>
            {p.steps.map((step, index) => (
              <div className="week-item" key={index}>
                <Checkbox
                  checked={p.completed.includes(index)}
                  disabled={!managed.some((m) => m.id === p.ministry_id)}
                  onChange={async (e) => {
                    try {
                      await api(`/preparations/${p.id}`, user, "PUT", {
                        completed: e.target.checked
                          ? [...p.completed, index]
                          : p.completed.filter((i) => i !== index),
                      });
                      await resource.reload();
                    } catch (error) {
                      message.error((error as Error).message);
                    }
                  }}
                >
                  {index + 1}. {step}
                </Checkbox>
              </div>
            ))}
          </section>
        ))}
        {!resource.data?.length && (
          <p className="muted">Мероприятий пока нет</p>
        )}
      </Load>
      <p className="muted spaced">
        Алгоритм основан на доступных макетах. Полные регламенты и бюджетные
        правила требуют согласования.
      </p>
      {adding && (
        <DataEditor
          title="Новое мероприятие"
          fields={[
            { name: "title", label: "Название", required: true },
            {
              name: "ministry_id",
              label: "Служение",
              type: "select",
              required: true,
              options: managed.map((m) => ({ value: m.id, label: m.name })),
            },
            {
              name: "kind",
              label: "Тип",
              type: "select",
              required: true,
              options: ["МСЛ", "КСЛ", "ФКС", "ОМС"].map((value) => ({
                value,
                label: value,
              })),
            },
          ]}
          initial={{ kind: "МСЛ", ministry_id: managed[0]?.id }}
          onClose={() => setAdding(false)}
          save={async (values) => {
            await api("/preparations", user, "POST", values);
            await resource.reload();
          }}
        />
      )}
    </>
  );
}
