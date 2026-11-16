import { useEffect, useState, type ReactNode } from "react";
import { Alert, Button, Checkbox, Form, Input, Skeleton } from "antd";
import { api } from "../api";

interface SessionInfo {
  authenticated: boolean;
  demo: boolean;
  user_id?: number;
  local_codes: boolean;
}
export function AuthGate({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionInfo>();
  const [error, setError] = useState("");
  const [force, setForce] = useState(location.pathname === "/login");
  useEffect(() => {
    api<SessionInfo>("/auth/session", 0)
      .then((s) => {
        if (s.authenticated)
          sessionStorage.setItem("session-user", String(s.user_id));
        else sessionStorage.removeItem("session-user");
        setSession(s);
      })
      .catch((e) => setError((e as Error).message));
    const expire = () => setForce(true);
    window.addEventListener("auth-expired", expire);
    return () => window.removeEventListener("auth-expired", expire);
  }, []);
  if (error)
    return (
      <div className="login-shell">
        <Alert
          type="error"
          message={error}
          action={<Button onClick={() => location.reload()}>Повторить</Button>}
        />
      </div>
    );
  if (!session)
    return (
      <div className="login-shell">
        <Skeleton active />
      </div>
    );
  if (!force && (session.authenticated || session.demo)) return <>{children}</>;
  return <Login local={session.local_codes} demo={session.demo} />;
}
function Login({ local, demo }: { local: boolean; demo: boolean }) {
  const [challenge, setChallenge] = useState("");
  const [localCode, setLocalCode] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const invitation = new URLSearchParams(location.search).get("invitation");
  return (
    <div className="login-shell">
      <section className="panel login-panel">
        <div className="eyebrow">СЛОВО ЖИЗНИ · САРАТОВ</div>
        <h1>
          {invitation ? "Принять приглашение" : "Войти в рабочее пространство"}
        </h1>
        <p className="muted">Одноразовый код на почту. Пароль не нужен.</p>
        {!challenge ? (
          <Form
            layout="vertical"
            onFinish={async (values) => {
              setSaving(true);
              setError("");
              try {
                const result = await api<{
                  challenge_id: string;
                  local_code?: string;
                }>("/auth/request-code", 0, "POST", {
                  email: values.email,
                  purpose: values.recovery ? "recovery" : "login",
                  invitation,
                });
                setEmail(values.email);
                setChallenge(result.challenge_id);
                setLocalCode(result.local_code || "");
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setSaving(false);
              }
            }}
          >
            <Form.Item
              name="email"
              label="Почта"
              rules={[
                { required: true, type: "email", message: "Укажите почту" },
              ]}
            >
              <Input autoComplete="email" />
            </Form.Item>
            <Form.Item name="recovery" valuePropName="checked">
              <Checkbox>Восстановить доступ и завершить другие сеансы</Checkbox>
            </Form.Item>
            <Button type="primary" block htmlType="submit" loading={saving}>
              Получить код
            </Button>
          </Form>
        ) : (
          <>
            <p>
              Если адрес допущен, код отправлен на {email}. Он действует 5
              минут.
            </p>
            {local && localCode && (
              <Alert
                type="warning"
                message={`Локальная проверка · код ${localCode}`}
                description="В опубликованном приложении этот режим запрещён."
              />
            )}
            <Form
              layout="vertical"
              onFinish={async (values) => {
                setSaving(true);
                setError("");
                try {
                  const result = await api<{ user_id: number }>(
                    "/auth/verify-code",
                    0,
                    "POST",
                    { challenge_id: challenge, code: values.code },
                  );
                  sessionStorage.setItem(
                    "session-user",
                    String(result.user_id),
                  );
                  location.href = "/tasks";
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setSaving(false);
                }
              }}
            >
              <Form.Item
                className="spaced"
                name="code"
                label="Код"
                rules={[
                  {
                    required: true,
                    pattern: /^\d{6}$/,
                    message: "Введите 6 цифр",
                  },
                ]}
              >
                <Input
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                />
              </Form.Item>
              <Button type="primary" block htmlType="submit" loading={saving}>
                Войти
              </Button>
            </Form>
            <Button
              className="spaced"
              type="link"
              onClick={() => {
                setChallenge("");
                setError("");
              }}
            >
              Указать другую почту или запросить снова
            </Button>
          </>
        )}
        {error && <Alert className="spaced" type="error" message={error} />}
        <p className="muted spaced">
          Новый адрес подключается по приглашению администратора. Для смены
          утраченной почты обратитесь к администратору.
        </p>
        {demo && (
          <Button
            block
            onClick={() => {
              sessionStorage.removeItem("session-user");
              location.href = "/tasks";
            }}
          >
            Продолжить локальную демонстрацию
          </Button>
        )}
      </section>
    </div>
  );
}
