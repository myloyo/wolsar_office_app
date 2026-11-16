import { useEffect } from "react";
import { Link } from "react-router-dom";
import { App, Badge, Button, Tag } from "antd";
import dayjs from "dayjs";
import { api } from "../api";
import { PageTitle } from "../components/PageTitle";
import { Load, useResource } from "./shared";

interface Notification {
  id: number;
  title: string;
  href: string;
  created_at: string;
  read: boolean;
}
export function NotificationBell({ user }: { user: number }) {
  const resource = useResource<Notification[]>("/notifications", user);
  const { reload } = resource;
  useEffect(() => {
    const timer = setInterval(() => void reload(), 30000);
    return () => clearInterval(timer);
  }, [reload]);
  return (
    <Link to="/notifications">
      <Badge
        count={resource.data?.filter((n) => !n.read).length || 0}
        size="small"
      >
        <Button aria-label="Уведомления">Уведомления</Button>
      </Badge>
    </Link>
  );
}
export function NotificationsPage({ user }: { user: number }) {
  const resource = useResource<Notification[]>("/notifications", user);
  const { message } = App.useApp();
  async function enablePush() {
    try {
      const { key } = await api<{ key: string }>(
        "/notifications/push/key",
        user,
      );
      if (!key) {
        message.info(
          "Доставка push ещё не настроена администратором. Уведомления внутри приложения уже доступны.",
        );
        return;
      }
      if (!("serviceWorker" in navigator) || !("PushManager" in window))
        throw new Error("Браузер не поддерживает push");
      const registration = await navigator.serviceWorker.getRegistration();
      if (!registration)
        throw new Error("Для push откройте опубликованную PWA-версию по HTTPS");
      const bytes = Uint8Array.from(
        atob(key.replace(/-/g, "+").replace(/_/g, "/")),
        (c) => c.charCodeAt(0),
      );
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: bytes,
      });
      const json = subscription.toJSON();
      await api("/notifications/push/subscribe", user, "POST", {
        endpoint: json.endpoint,
        keys: json.keys,
      });
      message.success("Уведомления на этом устройстве включены");
    } catch (e) {
      message.error((e as Error).message);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ОБНОВЛЕНИЯ"
        title="Уведомления"
        action={
          <Button onClick={() => void enablePush()}>
            Включить на этом устройстве
          </Button>
        }
      />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data?.map((n) => (
          <article className="panel spaced" key={n.id}>
            <div className="section-heading">
              <h3>{n.title}</h3>
              <Tag color={n.read ? "default" : "blue"}>
                {n.read ? "Прочитано" : "Новое"}
              </Tag>
            </div>
            <p className="muted">
              {dayjs(n.created_at).format("D MMMM HH:mm")}
            </p>
            <Link to={n.href}>
              <Button
                onClick={() =>
                  void api(`/notifications/${n.id}/read`, user, "POST")
                }
              >
                Открыть
              </Button>
            </Link>
            {!n.read && (
              <Button
                type="link"
                onClick={async () => {
                  await api(`/notifications/${n.id}/read`, user, "POST");
                  await resource.reload();
                }}
              >
                Отметить прочитанным
              </Button>
            )}
          </article>
        ))}
        {!resource.data?.length && (
          <p className="muted">Пока нет уведомлений</p>
        )}
      </Load>
    </>
  );
}
export function SessionsPage({ user }: { user: number }) {
  const resource = useResource<
    { id: string; created_at: string; expires_at: string; current: boolean }[]
  >("/auth/sessions", user);
  const { message } = App.useApp();
  return (
    <>
      <PageTitle eyebrow="МОЙ ДОСТУП" title="Активные сеансы" />
      <Load loading={resource.loading} error={resource.error}>
        {resource.data?.map((s) => (
          <div className="panel spaced" key={s.id}>
            <p>Вход: {dayjs(s.created_at).format("D MMMM HH:mm")}</p>
            <p>Действует до {dayjs(s.expires_at).format("D MMMM HH:mm")}</p>
            {s.current ? (
              <Tag color="green">Этот сеанс</Tag>
            ) : (
              <Button
                onClick={async () => {
                  try {
                    await api(`/auth/sessions/${s.id}`, user, "DELETE");
                    await resource.reload();
                  } catch (e) {
                    message.error((e as Error).message);
                  }
                }}
              >
                Завершить
              </Button>
            )}
          </div>
        ))}
      </Load>
      <Button
        className="spaced"
        onClick={async () => {
          await api("/auth/logout-all", user, "POST");
          sessionStorage.removeItem("session-user");
          location.href = "/login";
        }}
      >
        Завершить все сеансы
      </Button>
    </>
  );
}
