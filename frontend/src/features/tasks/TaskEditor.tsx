import { useEffect, useRef, useState } from "react";
import { App, Button, DatePicker, Form, Input, Select } from "antd";
import dayjs from "dayjs";
import { api, categories, type Bootstrap, type Task } from "../../api";

export function TaskEditor({
  data,
  user,
  task,
  onSaved,
}: {
  data: Bootstrap;
  user: number;
  task?: Task;
  onSaved: (task: Task) => void;
}) {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const { message } = App.useApp();
  const assignee = Form.useWatch<number>("assignee_id", form);
  const coexecutors = Form.useWatch<number[]>("coexecutor_ids", form) || [];
  const observers = Form.useWatch<number[]>("observer_ids", form) || [];
  const users = data.users.map((u) => ({ value: u.id, label: u.name }));
  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={
        task
          ? { ...task, due_date: dayjs(task.due_date) }
          : {
              assignee_id: user,
              department_id: data.departments[0]?.id,
              category: "personal",
              priority: "normal",
              due_date: dayjs().add(3, "day"),
              coexecutor_ids: [],
              observer_ids: [],
            }
      }
      onValuesChange={(changes) => {
        if ("assignee_id" in changes) {
          form.setFieldsValue({
            coexecutor_ids: coexecutors.filter(
              (id) => id !== changes.assignee_id,
            ),
            observer_ids: observers.filter((id) => id !== changes.assignee_id),
          });
        }
        if ("coexecutor_ids" in changes) {
          form.setFieldValue(
            "observer_ids",
            observers.filter((id) => !changes.coexecutor_ids.includes(id)),
          );
        }
      }}
      onFinish={async (values) => {
        setSaving(true);
        try {
          const saved = await api<Task>(
            task ? `/tasks/${task.id}` : "/tasks",
            user,
            task ? "PATCH" : "POST",
            {
              ...values,
              due_date: values.due_date.format("YYYY-MM-DD"),
              ...(task ? { expected_version: task.version } : {}),
            },
          );
          if (mounted.current) onSaved(saved);
        } catch (error) {
          message.error((error as Error).message);
        } finally {
          setSaving(false);
        }
      }}
    >
      <Form.Item
        name="title"
        label="Что сделать"
        rules={[
          { required: true, whitespace: true, message: "Введите название" },
        ]}
      >
        <Input maxLength={240} />
      </Form.Item>
      <Form.Item name="description" label="Описание">
        <Input.TextArea rows={4} maxLength={10000} />
      </Form.Item>
      <Form.Item
        name="department_id"
        label="Отделение"
        rules={[{ required: true }]}
      >
        <Select
          options={data.departments.map((d) => ({
            value: d.id,
            label: d.name,
          }))}
        />
      </Form.Item>
      <Form.Item
        name="assignee_id"
        label="Исполнитель"
        rules={[{ required: true }]}
      >
        <Select options={users} />
      </Form.Item>
      <Form.Item name="coexecutor_ids" label="Соисполнители">
        <Select
          mode="multiple"
          options={users.filter((u) => u.value !== assignee)}
          placeholder="Кто помогает выполнить задачу"
        />
      </Form.Item>
      <Form.Item name="observer_ids" label="Наблюдатели">
        <Select
          mode="multiple"
          options={users.filter(
            (u) => u.value !== assignee && !coexecutors.includes(u.value),
          )}
          placeholder="Кто следит за выполнением"
        />
      </Form.Item>
      <div className="two-col">
        <Form.Item name="due_date" label="Срок" rules={[{ required: true }]}>
          <DatePicker format="DD.MM.YYYY" />
        </Form.Item>
        <Form.Item name="priority" label="Приоритет">
          <Select
            options={[
              { value: "normal", label: "Обычный" },
              { value: "high", label: "Высокий" },
            ]}
          />
        </Form.Item>
      </div>
      <Form.Item name="category" label="Категория">
        <Select
          options={Object.entries(categories).map(([value, label]) => ({
            value,
            label,
          }))}
        />
      </Form.Item>
      <Button type="primary" block loading={saving} htmlType="submit">
        {task ? "Сохранить изменения" : "Создать задачу"}
      </Button>
    </Form>
  );
}
