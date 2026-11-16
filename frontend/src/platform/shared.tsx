import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Alert,
  Button,
  Checkbox,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Skeleton,
} from "antd";
import dayjs from "dayjs";
import { api } from "../api";

export function useResource<T>(path: string, user: number) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const serial = useRef(0);
  const reload = useCallback(async () => {
    const current = ++serial.current;
    setLoading(true);
    setError("");
    try {
      const result = await api<T>(path, user);
      if (serial.current === current) setData(result);
    } catch (e) {
      if (serial.current === current) setError((e as Error).message);
    } finally {
      if (serial.current === current) setLoading(false);
    }
  }, [path, user]);
  const invalidate = useCallback(() => {
    serial.current++;
  }, []);
  useEffect(() => {
    void reload();
    return invalidate;
  }, [reload, invalidate]);
  return { data, error, loading, reload, setData };
}
export function Load({
  loading,
  error,
  children,
}: {
  loading: boolean;
  error: string;
  children: ReactNode;
}) {
  return error ? (
    <Alert type="error" message={error} />
  ) : loading ? (
    <Skeleton active />
  ) : (
    <>{children}</>
  );
}
export interface FieldSpec {
  name: string;
  label: string;
  type?:
    | "text"
    | "textarea"
    | "number"
    | "date"
    | "datetime"
    | "month"
    | "select"
    | "multi"
    | "tags"
    | "check";
  options?: { value: string | number; label: string }[];
  required?: boolean;
  min?: number;
  max?: number;
}
export function DataEditor({
  title,
  fields,
  initial,
  save,
  onClose,
  readOnly = false,
}: {
  title: string;
  fields: FieldSpec[];
  initial?: Record<string, unknown>;
  save: (values: Record<string, unknown>) => Promise<void>;
  onClose: () => void;
  readOnly?: boolean;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const values = { ...initial };
  for (const field of fields) {
    if (
      ["date", "datetime", "month"].includes(field.type || "") &&
      values[field.name]
    )
      values[field.name] = dayjs(String(values[field.name]));
  }
  return (
    <Modal open title={title} onCancel={onClose} footer={null} destroyOnClose>
      <Form
        layout="vertical"
        disabled={readOnly}
        initialValues={values}
        onFinish={async (formValues) => {
          setSaving(true);
          setError("");
          try {
            const body = { ...formValues };
            for (const field of fields) {
              const value = body[field.name];
              if (dayjs.isDayjs(value))
                body[field.name] =
                  field.type === "datetime"
                    ? value.toISOString()
                    : value.format(
                        field.type === "month" ? "YYYY-MM" : "YYYY-MM-DD",
                      );
            }
            await save(body);
            onClose();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setSaving(false);
          }
        }}
      >
        {fields.map((field) => (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            valuePropName={field.type === "check" ? "checked" : "value"}
            rules={
              field.required
                ? [{ required: true, message: "Заполните поле" }]
                : []
            }
          >
            {field.type === "textarea" ? (
              <Input.TextArea rows={4} maxLength={10000} />
            ) : field.type === "number" ? (
              <InputNumber
                precision={0}
                min={field.min}
                max={field.max}
                style={{ width: "100%" }}
              />
            ) : ["date", "datetime", "month"].includes(field.type || "") ? (
              <DatePicker
                showTime={field.type === "datetime"}
                picker={field.type === "month" ? "month" : "date"}
                style={{ width: "100%" }}
              />
            ) : ["select", "multi", "tags"].includes(field.type || "") ? (
              <Select
                allowClear={!field.required}
                mode={
                  field.type === "multi"
                    ? "multiple"
                    : field.type === "tags"
                      ? "tags"
                      : undefined
                }
                options={field.options}
              />
            ) : field.type === "check" ? (
              <Checkbox />
            ) : (
              <Input maxLength={field.max || 240} />
            )}
          </Form.Item>
        ))}
        {error && <Alert className="spaced" type="error" message={error} />}
        {!readOnly && (
          <Button
            className="spaced"
            type="primary"
            block
            loading={saving}
            htmlType="submit"
          >
            Сохранить
          </Button>
        )}
      </Form>
    </Modal>
  );
}
