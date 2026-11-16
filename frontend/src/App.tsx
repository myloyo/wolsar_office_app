import { useCallback, useEffect, useRef, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import {
  Alert,
  App as AntApp,
  Avatar,
  Button,
  Checkbox,
  Drawer,
  Empty,
  Input,
  Modal,
  Progress,
  Select,
  Skeleton,
} from "antd";
import {
  ArrowRightOutlined,
  CheckOutlined,
  MenuOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { api, categories, type Bootstrap, type Task } from "./api";
import { MinistryPages } from "./modules";
import { CalendarPage } from "./platform/CalendarPage";
import { WorshipPage, LiveTimer } from "./platform/WorshipPage";
import { PrayerPage } from "./platform/PrayerPage";
import { PreparationsPage } from "./platform/PreparationsPage";
import { SpacesPage, SpacePage, PersonPage } from "./platform/SpacesPage";
import { AdminPage } from "./platform/AdminPage";
import {
  NotificationBell,
  NotificationsPage,
  SessionsPage,
} from "./platform/NotificationsPage";
import { PlanningPanel } from "./platform/PlanningPanel";
import { SlotsPage } from "./platform/SlotsPage";

import { PageTitle, PrototypeNote } from "./components/PageTitle";
export { PageTitle, PrototypeNote };
import { TaskEditor } from "./features/tasks/TaskEditor";
import { TaskPanel } from "./features/tasks/TaskPanel";
import { WeekPage } from "./features/planning/WeekPage";
import { WeekOverview } from "./features/planning/WeekOverview";
import { filterTasks, type TaskFilter } from "./features/tasks/filter";
const navigation = [
  ["/tasks", "Мои задачи", "01"],
  ["/planning", "Планирование", "02"],
  ["/departments", "Отделения", "03"],
  ["/week", "Моя неделя", "04"],
  ["/calendar", "Календарь", "05"],
  ["/service", "Богослужение", "06"],
  ["/schedule", "Расписание на год", "07"],
  ["/mc", "План МС", "08"],
  ["/events", "Праздники и конференции", "09"],
  ["/prayers", "Особые молитвы", "10"],
  ["/ministry", "Служения", "11"],
  ["/slots", "Запись на служение", "12"],
  ["/admin", "Управление", "13"],
];

export default function App() {
  const [user, setUser] = useState(
    Number(
      sessionStorage.getItem("session-user") ||
        localStorage.getItem("demo-user") ||
        1,
    ),
  );
  const [data, setData] = useState<Bootstrap>();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [create, setCreate] = useState(false);
  const [selected, setSelected] = useState<Task>();
  const [mobile, setMobile] = useState(false);
  const { message } = AntApp.useApp();
  const location = useLocation();
  const activeUser = useRef(user);
  activeUser.current = user;
  const serial = useRef(0);
  const saveTaskInList = useCallback(
    (task: Task) =>
      setTasks((current) => current.map((t) => (t.id === task.id ? task : t))),
    [],
  );
  const refresh = useCallback(async () => {
    const requestId = ++serial.current;
    setLoading(true);
    setError("");
    try {
      const [b, t] = await Promise.all([
        api<Bootstrap>("/bootstrap", user),
        api<Task[]>("/tasks", user),
      ]);
      if (activeUser.current !== user || serial.current !== requestId) return;
      setData(b);
      if (!b.demo && b.current_user_id !== user) {
        setUser(b.current_user_id);
        sessionStorage.setItem("session-user", String(b.current_user_id));
      }
      setTasks(t);
    } catch (e) {
      if (activeUser.current === user && serial.current === requestId)
        setError((e as Error).message);
    } finally {
      if (activeUser.current === user && serial.current === requestId)
        setLoading(false);
    }
  }, [user]);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  useEffect(() => {
    const id = Number(new URLSearchParams(location.search).get("task"));
    if (location.pathname === "/tasks" && id)
      setSelected(tasks.find((t) => t.id === id));
  }, [location.pathname, location.search, tasks]);
  const actor = data?.users.find((u) => u.id === user);
  const office = actor?.roles.some((r) => r === "admin" || r === "office");
  const admin = actor?.roles.includes("admin");
  const nav = (
    <>
      <Link className="brand" to="/tasks">
        <span className="brand-mark">≋</span>
        <span>
          СЛОВО ЖИЗНИ<small>САРАТОВ · РАБОЧЕЕ ПРОСТРАНСТВО</small>
        </span>
      </Link>
      <div className="nav-label">РАБОЧИЙ СТОЛ</div>
      <nav>
        {navigation
          .filter(
            ([path]) =>
              !(
                ["/planning", "/departments", "/week"].includes(path) && !office
              ) &&
              (path !== "/admin" || admin),
          )
          .map(([path, label, num]) => (
            <NavLink key={path} to={path} onClick={() => setMobile(false)}>
              <span className="nav-number">{num}</span>
              {label}
            </NavLink>
          ))}
      </nav>
      <div className="sidebar-foot">
        <span className="status-dot" /> Локальная демонстрация
        <small>СЖ Саратов / версия 0.1</small>
      </div>
    </>
  );
  if (location.pathname === "/timer")
    return <LiveTimer user={user} data={data} />;
  return (
    <div className="shell">
      <aside className="sidebar">{nav}</aside>
      <Drawer open={mobile} onClose={() => setMobile(false)} placement="left">
        {nav}
      </Drawer>
      <div className="main-shell">
        <header className="topbar">
          <Button
            className="mobile-menu"
            icon={<MenuOutlined />}
            onClick={() => setMobile(true)}
            aria-label="Открыть меню"
          />
          <span className="breadcrumb">
            СЖ Саратов <span>/</span>{" "}
            {navigation.find(([p]) => location.pathname.startsWith(p))?.[1] ||
              "Служение"}
          </span>
          <div className="user-select">
            <NotificationBell user={user} />
            {data?.demo ? (
              <>
                <span className="demo-pill">ДЕМО</span>
                <Select
                  aria-label="Демонстрационный пользователь"
                  value={user}
                  options={data.users.map((u) => ({
                    value: u.id,
                    label: u.name,
                  }))}
                  onChange={(id) => {
                    activeUser.current = id;
                    serial.current++;
                    setLoading(true);
                    setTasks([]);
                    setSelected(undefined);
                    setCreate(false);
                    setUser(id);
                    localStorage.setItem("demo-user", String(id));
                  }}
                />
                <Button onClick={() => (window.location.href = "/login")}>
                  Войти по коду
                </Button>
              </>
            ) : (
              <>
                <Link to="/sessions">
                  <Button>{actor?.name || "Мой доступ"}</Button>
                </Link>
                <Button
                  onClick={async () => {
                    await api("/auth/logout", user, "POST");
                    sessionStorage.removeItem("session-user");
                    window.location.href = "/login";
                  }}
                >
                  Выйти
                </Button>
              </>
            )}
            <Avatar style={{ background: "#ffba00", color: "#222" }}>СЖ</Avatar>
          </div>
        </header>
        <main className="content">
          {error ? (
            <Alert
              type="error"
              showIcon
              message="Сервер недоступен"
              description={error}
              action={<Button onClick={() => void refresh()}>Повторить</Button>}
            />
          ) : loading ? (
            <Skeleton active paragraph={{ rows: 12 }} />
          ) : (
            data && (
              <>
                <Routes>
                  <Route path="/" element={<Navigate to="/tasks" replace />} />
                  <Route
                    path="/tasks"
                    element={
                      <TasksPage
                        tasks={tasks}
                        user={user}
                        departmentIds={actor?.department_ids || []}
                        onSelect={setSelected}
                        onCreate={() => setCreate(true)}
                        canCreate={
                          actor?.roles.some((r) => r !== "volunteer") || false
                        }
                      />
                    }
                  />
                  <Route
                    path="/planning"
                    element={
                      admin ? (
                        <PlanningPage user={user} data={data} tasks={tasks} />
                      ) : (
                        <Empty description="Обзор доступен исполнительному пастору" />
                      )
                    }
                  />
                  <Route
                    path="/departments"
                    element={
                      office ? (
                        <SpacesPage kind="department" user={user} />
                      ) : (
                        <Empty description="Раздел доступен сотрудникам офиса" />
                      )
                    }
                  />
                  <Route
                    path="/week"
                    element={
                      office ? (
                        <WeekPage key={user} user={user} />
                      ) : (
                        <Empty description="Недельное планирование доступно сотрудникам офиса" />
                      )
                    }
                  />
                  <Route
                    path="/calendar"
                    element={<CalendarPage user={user} data={data} />}
                  />
                  <Route
                    path="/events"
                    element={<PreparationsPage user={user} data={data} />}
                  />
                  <Route
                    path="/prayers"
                    element={<PrayerPage user={user} data={data} />}
                  />
                  <Route
                    path="/schedule"
                    element={
                      <WorshipPage user={user} data={data} mode="schedule" />
                    }
                  />
                  <Route
                    path="/service"
                    element={<WorshipPage user={user} data={data} />}
                  />
                  <Route
                    path="/mc"
                    element={<WorshipPage user={user} data={data} mode="mc" />}
                  />
                  <Route
                    path="/ministry"
                    element={<SpacesPage kind="ministry" user={user} />}
                  />
                  <Route
                    path="/spaces/:scope/:id"
                    element={<SpacePage user={user} data={data} />}
                  />
                  <Route
                    path="/people/:id"
                    element={<PersonPage user={user} />}
                  />
                  <Route
                    path="/slots"
                    element={<SlotsPage user={user} data={data} />}
                  />
                  <Route
                    path="/admin"
                    element={
                      admin ? (
                        <AdminPage
                          user={user}
                          data={data}
                          onChanged={refresh}
                        />
                      ) : (
                        <Empty description="Только для администратора" />
                      )
                    }
                  />
                  <Route
                    path="/notifications"
                    element={<NotificationsPage user={user} />}
                  />
                  <Route
                    path="/sessions"
                    element={<SessionsPage user={user} />}
                  />
                  <Route
                    path="/ministry/*"
                    element={
                      <MinistryPages
                        onCreate={() => setCreate(true)}
                        canManage={
                          actor?.roles.some(
                            (r) => r === "admin" || r === "leader",
                          ) || false
                        }
                      />
                    }
                  />
                  <Route
                    path="*"
                    element={
                      <Empty description="Страница не найдена">
                        <Link to="/tasks">К моим задачам</Link>
                      </Empty>
                    }
                  />
                </Routes>
                <footer className="page-footer">
                  СЛОВО ЖИЗНИ · САРАТОВ<span>Вместе служим людям</span>
                </footer>
              </>
            )
          )}
        </main>
      </div>
      <Modal
        open={create}
        footer={null}
        onCancel={() => setCreate(false)}
        title="Новая задача офису"
        destroyOnClose
      >
        {data && (
          <TaskEditor
            key={user}
            data={data}
            user={user}
            onSaved={() => {
              setCreate(false);
              void refresh();
              message.success("Задача создана");
            }}
          />
        )}
      </Modal>
      {data && selected && (
        <TaskPanel
          key={`${user}-${selected.id}`}
          taskId={selected.id}
          user={user}
          data={data}
          onClose={() => setSelected(undefined)}
          onSaved={saveTaskInList}
        />
      )}
    </div>
  );
}

function TasksPage({
  tasks,
  user,
  departmentIds,
  onSelect,
  onCreate,
  canCreate,
}: {
  tasks: Task[];
  user: number;
  departmentIds: number[];
  onSelect: (t: Task) => void;
  onCreate: () => void;
  canCreate: boolean;
}) {
  const [filter, setFilter] = useState<TaskFilter>("all");
  const [query, setQuery] = useState("");
  const [showDone, setShowDone] = useState(false);
  const [board, setBoard] = useState("category");
  const filtered = filterTasks(
    tasks,
    user,
    departmentIds,
    filter,
    query,
    showDone || board === "status",
  );
  return (
    <>
      <PageTitle
        eyebrow="ЛИЧНОЕ ПРОСТРАНСТВО"
        title="Мои задачи"
        description="Всё, что важно. Всё, что нужно сделать."
        action={
          canCreate && (
            <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
              Новая задача
            </Button>
          )
        }
      />
      <div className="toolbar">
        <Input
          prefix={<SearchOutlined />}
          placeholder="Найти задачу"
          aria-label="Поиск задач"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ maxWidth: 290 }}
        />
        <div className="pills">
          {[
            ["all", "Все"],
            ["creator", "Я поручил"],
            ["assignee", "Я исполнитель"],
            ["coexecutor", "Соисполнитель"],
            ["observer", "Наблюдатель"],
            ...(departmentIds.length ? [["department", "Мои отделения"]] : []),
          ].map(([v, l]) => (
            <Button
              key={v}
              type={filter === v ? "primary" : "default"}
              onClick={() => setFilter(v as TaskFilter)}
            >
              {l}
            </Button>
          ))}
        </div>
        <Select
          aria-label="Вид доски"
          value={board}
          onChange={setBoard}
          options={[
            { value: "category", label: "По категориям" },
            { value: "status", label: "По статусам" },
          ]}
        />
        <Checkbox
          checked={showDone}
          onChange={(e) => setShowDone(e.target.checked)}
        >
          Завершённые
        </Checkbox>
      </div>
      <div className="legend">
        <span>
          <i className="legend-new" />
          Новая
        </span>
        <span>
          <i className="legend-soon" />
          Срок на этой неделе
        </span>
        <span>
          <i className="legend-overdue" />
          Просрочено
        </span>
        <span className="task-total">
          {filtered.length} задач в пространстве
        </span>
      </div>
      <div className={`task-board ${board === "status" ? "status-board" : ""}`}>
        {(board === "status"
          ? [
              ["new", "Новые"],
              ["in_progress", "В работе"],
              ["done", "Завершены"],
            ]
          : Object.entries(categories)
        ).map(([key, label], index) => {
          const list = filtered.filter(
            (t) => (board === "status" ? t.status : t.category) === key,
          );
          return (
            <section className="task-column" key={key}>
              <div className="column-heading">
                <h3>{label}</h3>
                <span>{list.length}</span>
              </div>
              <p className="column-description">
                {
                  [
                    "Мои приоритеты, планы и личные поручения",
                    "Задачи лидерам и от лидеров служений",
                    "Встречи, проекты и совместная работа",
                    "Важное, что нужно знать команде",
                    "Предложения для будущих изменений",
                  ][index]
                }
              </p>
              {list.length ? (
                list.map((t) => {
                  const overdue =
                    t.status !== "done" &&
                    dayjs(t.due_date).isBefore(dayjs(), "day");
                  return (
                    <button
                      className={`task-card ${overdue ? "overdue" : ""}`}
                      onClick={() => onSelect(t)}
                      key={t.id}
                    >
                      <div className="task-meta">
                        <span>
                          {t.priority === "high"
                            ? "СРОЧНО И ВАЖНО"
                            : {
                                new: "НОВАЯ",
                                in_progress: "В РАБОТЕ",
                                done: "ЗАВЕРШЕНА",
                              }[t.status]}
                        </span>
                        <span>↗</span>
                      </div>
                      <h4>{t.title}</h4>
                      <p>{t.description}</p>
                      <div className="task-bottom">
                        <span className="initial-avatar">СЖ</span>
                        <span>{dayjs(t.due_date).format("D MMM")}</span>
                        {t.status === "done" && <CheckOutlined />}
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="column-empty">Пока нет задач</div>
              )}
              {canCreate && (
                <button className="add-card" onClick={onCreate}>
                  <PlusOutlined /> Добавить задачу
                </button>
              )}
            </section>
          );
        })}
      </div>
    </>
  );
}

function PlanningPage({
  data,
  tasks,
  user,
}: {
  data: Bootstrap;
  tasks: Task[];
  user: number;
}) {
  return (
    <>
      <PageTitle
        eyebrow="ИСПОЛНИТЕЛЬНЫЙ ПАСТОР"
        title="Планирование офиса"
        description="От видения церкви — к работе каждого сотрудника."
      />
      <div className="hero-strip">
        <div>
          <div className="eyebrow">ТЕКУЩАЯ НЕДЕЛЯ</div>
          <h2>{dayjs().format("D MMMM")} · держим фокус вместе</h2>
          <p>Задачи, приоритеты и планы семи отделений в одном пространстве.</p>
        </div>
        <Link to="/week">
          <Button>
            Мой план <ArrowRightOutlined />
          </Button>
        </Link>
      </div>
      <PlanningPanel user={user} data={data} />
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Сотрудники и задачи</h3>
          <span className="muted">
            {data.users.length} демонстрационных пользователя
          </span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Сотрудник</th>
                <th>Роли</th>
                <th>Задач</th>
                <th>Выполнено</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u) => {
                const own = tasks.filter((t) => t.assignee_id === u.id);
                return (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.name}</strong>
                    </td>
                    <td>
                      {u.roles
                        .map(
                          (r) =>
                            ({
                              admin: "Администратор",
                              office: "Офис",
                              leader: "Лидер",
                              volunteer: "Служитель",
                            })[r],
                        )
                        .join(", ")}
                    </td>
                    <td>{own.length}</td>
                    <td>
                      <Progress
                        percent={
                          own.length
                            ? Math.round(
                                (own.filter((t) => t.status === "done").length /
                                  own.length) *
                                  100,
                              )
                            : 0
                        }
                        size="small"
                        strokeColor="#ffb800"
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <WeekOverview user={user} data={data} />
    </>
  );
}
