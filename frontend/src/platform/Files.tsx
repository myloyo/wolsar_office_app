import { useRef, useState } from "react";
import { App, Button, Space, Tag } from "antd";
import { api, csrfToken } from "../api";
import { Load, useResource } from "./shared";

interface StoredFile {
  id: string;
  name: string;
  size: number;
  deleted: boolean;
}
export function Files({
  scope,
  scopeId,
  user,
  canWrite,
}: {
  scope: string;
  scopeId: number;
  user: number;
  canWrite: boolean;
}) {
  const { data, loading, error, reload } = useResource<StoredFile[]>(
    `/files?scope=${scope}&scope_id=${scopeId}`,
    user,
  );
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();
  async function upload(file: File) {
    setBusy(true);
    try {
      const response = await fetch(
        `/api/files?scope=${scope}&scope_id=${scopeId}&name=${encodeURIComponent(file.name)}`,
        {
          method: "POST",
          headers: { "X-Demo-User": String(user), "X-CSRF-Token": csrfToken() },
          body: file,
        },
      );
      if (!response.ok) {
        const failure = await response.json();
        throw new Error(
          typeof failure.detail === "string"
            ? failure.detail
            : "Не удалось загрузить файл",
        );
      }
      await reload();
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setBusy(false);
      if (input.current) input.current.value = "";
    }
  }
  async function download(file: StoredFile) {
    try {
      const response = await fetch(`/api/files/${file.id}/download`, {
        headers: { "X-Demo-User": String(user) },
      });
      if (!response.ok) throw new Error("Файл недоступен");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      message.error((e as Error).message);
    }
  }
  return (
    <section className="task-section">
      <div className="section-heading">
        <h3>Файлы и фото</h3>
        {canWrite && (
          <Button loading={busy} onClick={() => input.current?.click()}>
            Прикрепить файл
          </Button>
        )}
      </div>
      <input
        ref={input}
        type="file"
        style={{ display: "none" }}
        accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.csv,.docx,.xlsx,.pptx"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void upload(file);
        }}
      />
      <Load loading={loading} error={error}>
        {data?.map((file) => (
          <div className="list-row" key={file.id}>
            <span>
              {file.name} <small>{Math.ceil(file.size / 1024)} КБ</small>
              {file.deleted && <Tag>Удалён</Tag>}
            </span>
            <Space>
              {!file.deleted && (
                <Button size="small" onClick={() => void download(file)}>
                  Скачать
                </Button>
              )}
              {canWrite && (
                <Button
                  size="small"
                  onClick={async () => {
                    try {
                      await api(
                        `/files/${file.id}${file.deleted ? "/restore" : ""}`,
                        user,
                        file.deleted ? "POST" : "DELETE",
                      );
                      await reload();
                    } catch (e) {
                      message.error((e as Error).message);
                    }
                  }}
                >
                  {file.deleted ? "Восстановить" : "Удалить"}
                </Button>
              )}
            </Space>
          </div>
        ))}
        {!data?.length && (
          <p className="muted">Файлов пока нет. До 10 МБ на файл.</p>
        )}
      </Load>
    </section>
  );
}
