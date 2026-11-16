import { useState } from "react";
import { Button, Tag } from "antd";
import dayjs from "dayjs";
import { api } from "../api";
import { DataEditor, Load, useResource } from "./shared";

interface Recurrence {
  frequency: string;
  next_date: string;
  active: boolean;
}
export function RecurrencePanel({
  user,
  taskId,
  dueDate,
  canEdit,
}: {
  user: number;
  taskId: number;
  dueDate: string;
  canEdit: boolean;
}) {
  const resource = useResource<Recurrence | null>(
    `/tasks/${taskId}/recurrence`,
    user,
  );
  const [editing, setEditing] = useState(false);
  return (
    <section className="task-section">
      <div className="section-heading">
        <h3>Повторение задачи</h3>
        {canEdit && (
          <Button size="small" onClick={() => setEditing(true)}>
            Настроить
          </Button>
        )}
      </div>
      <Load loading={resource.loading} error={resource.error}>
        {resource.data ? (
          <p>
            <Tag color={resource.data.active ? "green" : "default"}>
              {resource.data.active ? "Включено" : "Приостановлено"}
            </Tag>
            {resource.data.frequency === "weekly"
              ? "Каждую неделю"
              : "Каждый месяц"}{" "}
            · следующее: {dayjs(resource.data.next_date).format("D MMMM YYYY")}
          </p>
        ) : (
          <p className="muted">Не настроено</p>
        )}
      </Load>
      {editing && (
        <DataEditor
          title="Повторяющаяся задача"
          fields={[
            {
              name: "frequency",
              label: "Периодичность",
              type: "select",
              required: true,
              options: [
                { value: "weekly", label: "Каждую неделю" },
                { value: "monthly", label: "Каждый месяц" },
              ],
            },
            {
              name: "next_date",
              label: "Дата первого повторения",
              type: "date",
              required: true,
            },
            { name: "active", label: "Повторение включено", type: "check" },
          ]}
          initial={
            resource.data
              ? { ...resource.data }
              : {
                  frequency: "weekly",
                  next_date: dayjs(dueDate).add(7, "day").format("YYYY-MM-DD"),
                  active: true,
                }
          }
          onClose={() => setEditing(false)}
          save={async (values) => {
            await api(`/tasks/${taskId}/recurrence`, user, "PUT", values);
            await resource.reload();
          }}
        />
      )}
      <p className="muted">
        Новые экземпляры создаёт фоновый обработчик. Вложения и обсуждение
        исходной задачи не копируются.
      </p>
    </section>
  );
}
