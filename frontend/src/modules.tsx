import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import {
  App,
  Alert,
  Button,
  Checkbox,
  DatePicker,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Tag,
} from "antd";
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  CalendarOutlined,
  PauseOutlined,
  PlayCircleOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { PageTitle, PrototypeNote } from "./components/PageTitle";

const services = ["1 ВС · 10:00", "2 ВС · 13:00", "ОП", "ВХМ"];
const positions = [
  "Молитвенник",
  "Ведущий прославления",
  "МС",
  "Проповедник",
  "Администратор",
  "Ивент",
  "Звук",
  "Свет",
  "Экран",
  "Сторителлинг / интервью",
  "Молитва на сцене",
  "Режиссёр",
  "Служитель трансляции",
];
const eventTypes = [
  {
    key: "МСЛ",
    name: "Мероприятие служения",
    text: "Любое мероприятие вашего служения, открытое или закрытое. Для закрытого задача нужна, только если требуется помощь офиса.",
    budget: "Бюджет служения, самоокупаемость или статья отделения",
  },
  {
    key: "КСЛ",
    name: "Конференция служения",
    text: "Конференция для служения. Программу, команду и необходимые ресурсы согласуем заранее.",
    budget: "Требует согласования с отделением",
  },
  {
    key: "ФКС",
    name: "Франшизная конференция служения",
    text: "Проведение конференции по готовой программе. Согласуйте использование материалов и условия проведения.",
    budget: "Требует согласования",
  },
  {
    key: "ОМС",
    name: "Обучающее мероприятие служения",
    text: "Обучение и развитие команды служения. Уточните аудиторию, программу и потребность в ресурсах.",
    budget: "Бюджет служения или согласованная статья",
  },
];

export function MinistryPages({
  onCreate,
  canManage,
}: {
  onCreate: () => void;
  canManage: boolean;
}) {
  return (
    <Routes>
      <Route
        index
        element={<MinistryHome onCreate={onCreate} canManage={canManage} />}
      />
      <Route path="card" element={<MinistryCard canManage={canManage} />} />
      <Route
        path="architecture"
        element={
          canManage ? (
            <Architecture />
          ) : (
            <Alert
              type="warning"
              message="Архитектура доступна лидерской команде служения"
            />
          )
        }
      />
      <Route path="planning" element={<EventPlanning onCreate={onCreate} />} />
      <Route path="event" element={<MinistryEvent onCreate={onCreate} />} />
      <Route path="children" element={<Children />} />
      <Route path="event-team" element={<EventTeam />} />
    </Routes>
  );
}
function MinistryHome({
  onCreate,
  canManage,
}: {
  onCreate: () => void;
  canManage: boolean;
}) {
  return (
    <>
      <PageTitle
        eyebrow="ПРОСТРАНСТВО СЛУЖЕНИЯ"
        title="Молодёжное служение"
        description="Команда, события и задачи — рядом."
        action={
          <Link to="/ministry/card">
            <Button>
              Карточка служения <ArrowRightOutlined />
            </Button>
          </Link>
        }
      />
      <div className="ministry-grid">
        <div>
          <div className="two-col">
            <Link to="/ministry/card" className="panel link-panel">
              <span className="eyebrow">МОЁ СЛУЖЕНИЕ</span>
              <h3>
                Видение, структура,
                <br />
                место в оргсхеме
              </h3>
              <p>Отделение Богослужения</p>
              <ArrowRightOutlined />
            </Link>
            <Link to="/calendar" className="panel link-panel">
              <span className="eyebrow">КАЛЕНДАРЬ ЦЕРКВИ</span>
              <h3>
                Воскресенье
                <br />
                10:00 и 13:00
              </h3>
              <p>События и встречи</p>
              <CalendarOutlined />
            </Link>
          </div>
          {canManage && (
            <>
              <button className="quick-action" onClick={onCreate}>
                <span>
                  <strong>Быстрая задача офису</strong>
                  <small>Флаеры, стулья, печать, техника</small>
                </span>
                <PlusOutlined />
              </button>
              <Link to="/ministry/planning" className="quick-action outline">
                <span>
                  <strong>Планирование мероприятия</strong>
                  <small>МСЛ, КСЛ, ФКС, ОМС по регламенту</small>
                </span>
                <CalendarOutlined />
              </Link>
            </>
          )}
          <section className="panel spaced">
            <div className="section-heading">
              <h3>Работа команды</h3>
              <Tag>Обзор</Tag>
            </div>
            <Link to="/tasks" className="list-row">
              <span>Открыть мои задачи</span>
              <ArrowRightOutlined />
            </Link>
            <Link to="/ministry/event" className="list-row">
              <span>Пример подготовки мероприятия</span>
              <ArrowRightOutlined />
            </Link>
            <Link to="/ministry/event-team" className="list-row">
              <span>Служение Ивент</span>
              <ArrowRightOutlined />
            </Link>
          </section>
        </div>
        <section className="vision-card">
          <div className="eyebrow">МЫ СЛУЖИМ ВМЕСТЕ</div>
          <h2>
            У каждого
            <br />
            есть место.
            <br />
            <span>
              У каждого
              <br />
              есть дар.
            </span>
          </h2>
          <p>Познакомьтесь со служениями и найдите свою команду.</p>
          <Link to="/ministry/children">
            <Button>
              Детское служение <ArrowRightOutlined />
            </Button>
          </Link>
        </section>
      </div>
    </>
  );
}
function MinistryCard({ canManage }: { canManage: boolean }) {
  const { message } = App.useApp();
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ БОГОСЛУЖЕНИЯ"
        title="Карточка служения"
        description="Молодёжное служение"
      />
      <PrototypeNote />
      <div className="two-col">
        <section className="panel">
          <h3>Архитектура служения</h3>
          <dl className="details">
            <dt>Лидер-архитектор</dt>
            <dd>Не назначен</dd>
            <dt>Координатор</dt>
            <dd>
              <Tag color="orange">Не заполнено</Tag>
            </dd>
            <dt>Пастор</dt>
            <dd>Не назначен</dd>
          </dl>
          {canManage && (
            <Link to="/ministry/architecture">
              <Button block>Открыть архитектуру</Button>
            </Link>
          )}
          <h3 className="spaced">О служении</h3>
          <dl className="details">
            <dt>Целевая аудитория</dt>
            <dd>16–25 лет</dd>
            <dt>Помещение</dt>
            <dd>Молодёжная комната</dd>
            <dt>Обеспечение</dt>
            <dd>Выделенный бюджет, отделение Богослужения</dd>
          </dl>
          <p>Богослужения, неформальные мероприятия и встречи команды.</p>
        </section>
        <div>
          <section className="panel">
            <h3>Документы</h3>
            {[
              "Видение служения",
              "Должностные инструкции",
              "Состав команды и вакансии",
              "Регулярные встречи",
            ].map((t) => (
              <div className="list-row" key={t}>
                {t}
                <Tag color="orange">Не заполнено</Tag>
              </div>
            ))}
          </section>
          <section className="panel spaced">
            <h3>Прошедшие мероприятия</h3>
            <p className="muted">
              Здесь появятся мероприятия с обратной связью для планирования
              следующих встреч.
            </p>
          </section>
          <Button
            className="spaced"
            type="primary"
            onClick={() =>
              message.info(
                "Предложения правок будут подключены после согласования процесса модерации.",
              )
            }
          >
            Предложить правку
          </Button>
        </div>
      </div>
    </>
  );
}
function Architecture() {
  return (
    <>
      <PageTitle eyebrow="МОЛОДЁЖНОЕ СЛУЖЕНИЕ" title="Архитектура служения" />
      <PrototypeNote />
      <Alert
        showIcon
        message="Раздел лидерской команды"
        description="Доступна лидеру, координатору и пастору служения. Состав команды в этом прототипе не настроен."
      />
      <div className="two-col spaced">
        <section className="panel">
          <h3>Лидерская команда</h3>
          {["Лидер-архитектор", "Координатор", "Пастор"].map((t) => (
            <div className="list-row" key={t}>
              {t}
              <Tag>Не назначен</Tag>
            </div>
          ))}
        </section>
        <section className="panel">
          <h3>Группы и лидеры групп</h3>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Группы ещё не добавлены"
          />
        </section>
        <section className="panel">
          <h3>Служители и вакансии</h3>
          <div className="list-row">
            Служителей в команде <strong>0</strong>
          </div>
          <div className="list-row">
            Открытые вакансии <Tag color="orange">Координатор</Tag>
          </div>
        </section>
        <section className="panel">
          <h3>Для команды</h3>
          <p>Чат лидерской команды</p>
          <p>Должностные инструкции и стандарты</p>
          <p>Внутренние заметки и планы</p>
          <span className="muted">Документы пока не загружены</span>
        </section>
      </div>
    </>
  );
}
function EventPlanning({ onCreate }: { onCreate: () => void }) {
  const [type, setType] = useState(0);
  const selected = eventTypes[type];
  return (
    <>
      <PageTitle
        eyebrow="ЛИДЕР СЛУЖЕНИЯ"
        title="Планирование мероприятия"
        description="Выберите формат и проверьте регламент подготовки."
      />
      <PrototypeNote />
      <div className="event-type-grid">
        {eventTypes.map((t, i) => (
          <button
            key={t.key}
            onClick={() => setType(i)}
            className={`event-type ${type === i ? "active" : ""}`}
          >
            <strong>{t.key}</strong>
            <span>{t.name}</span>
          </button>
        ))}
      </div>
      <section className="panel spaced narrow">
        <h2>
          {selected.key}: {selected.name}
        </h2>
        <p>{selected.text}</p>
        <dl className="details">
          <dt>Кто решает</dt>
          <dd>Лидер служения</dd>
          <dt>Бюджет</dt>
          <dd>{selected.budget}</dd>
          <dt>Календарь</dt>
          <dd>Проверить участников, служения и помещения</dd>
        </dl>
        <Button block type="primary" onClick={onCreate}>
          Создать задачу офису
        </Button>
        <p className="muted">
          Выбранный регламент пока не прикрепляется к задаче автоматически.
        </p>
      </section>
    </>
  );
}
function MinistryEvent({ onCreate }: { onCreate: () => void }) {
  const [done, setDone] = useState<number[]>([]);
  return (
    <>
      <PageTitle
        eyebrow="МСЛ · МОЛОДЁЖНОЕ СЛУЖЕНИЕ"
        title="Подготовка мероприятия"
        description="Пример алгоритма работы лидера."
      />
      <PrototypeNote />
      <div className="two-col">
        <section className="panel">
          <h3>Регламент МСЛ</h3>
          <p>Цель: служители, целевая контактная аудитория, гости.</p>
          <p>Решение принимает лидер служения.</p>
          <p>Бюджет: бюджет служения, самоокупаемость или статья отделения.</p>
          <h3>Участники</h3>
          <p className="muted">Ответственный пока не назначен</p>
        </section>
        <section className="panel">
          <h3>Алгоритм</h3>
          {[
            "Идея мероприятия, спикеры",
            "Проверить календарь",
            "Задача поставлена",
            "Планёрка с командой",
            "Проведение мероприятия",
            "Обратная связь",
          ].map((title, i) => (
            <div className="algorithm-step" key={title}>
              <Checkbox
                checked={done.includes(i)}
                onChange={(e) =>
                  setDone(
                    e.target.checked
                      ? [...done, i]
                      : done.filter((x) => x !== i),
                  )
                }
              >
                <strong>
                  {i + 1}. {title}
                </strong>
              </Checkbox>
              {i === 1 && (
                <Link to="/calendar">
                  <Button size="small">Календарь</Button>
                </Link>
              )}
              {i === 3 && (
                <Button size="small" onClick={onCreate}>
                  Быстрая задача офису
                </Button>
              )}
            </div>
          ))}
        </section>
      </div>
    </>
  );
}
function Children() {
  const { message } = App.useApp();
  return (
    <>
      <PageTitle
        eyebrow="ЧЛЕН ЦЕРКВИ"
        title="Детское служение"
        description="Так страницу служения видит любой член церкви."
      />
      <PrototypeNote />
      <section className="panel narrow">
        <h3>Для детей 3–10 лет</h3>
        <p>Воскресенье, 10:00 и 13:00</p>
        <p>Праздники и летние мероприятия.</p>
        <p className="muted">
          Контакты лидера и координатора ещё не добавлены.
        </p>
        <Button
          type="primary"
          block
          onClick={() =>
            message.info("Раздел для родителей ещё не спроектирован.")
          }
        >
          Я родитель
        </Button>
        <Button
          className="spaced"
          block
          onClick={() =>
            message.info(
              "Заявки в лидерскую команду будут подключены следующим этапом.",
            )
          }
        >
          Хочу служить в детском
        </Button>
      </section>
    </>
  );
}
function EventTeam() {
  const [checks, setChecks] = useState<string[]>([]);
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ БОГОСЛУЖЕНИЯ"
        title="Служение Ивент"
        description="Духовное служение порядка, времени и поддержки."
      />
      <PrototypeNote />
      <section className="panel">
        <p>
          Помогаем собранию течь в порядке Божьем, держим время, атмосферу и
          коммуникацию, чтобы служители сцены служили спокойно и свободно.
        </p>
        <h3>Расписание служителей</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Служитель</th>
                {services.map((s) => (
                  <th key={s}>{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                "Демо · Служитель 1",
                "Демо · Служитель 2",
                "Демо · Служитель 3",
              ].map((name, i) => (
                <tr key={name}>
                  <td>{name}</td>
                  {services.map((s, j) => (
                    <td key={s}>
                      <Checkbox
                        aria-label={`${name}, ${s}`}
                        checked={checks.includes(`${i}-${j}`)}
                        onChange={(e) =>
                          setChecks(
                            e.target.checked
                              ? [...checks, `${i}-${j}`]
                              : checks.filter((x) => x !== `${i}-${j}`),
                          )
                        }
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel spaced">
        <h3>Подробные чек-листы</h3>
        {services.slice(0, 2).map((s) => (
          <Link className="list-row" key={s} to="/service">
            <strong>{s}</strong>
            <span>Открыть →</span>
          </Link>
        ))}
      </section>
    </>
  );
}

export function EventsPage({ onCreate }: { onCreate: () => void }) {
  const [template, setTemplate] = useState("");
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ БОГОСЛУЖЕНИЯ"
        title="Праздники и конференции"
        description="Планирование больших событий и работа по регламентам."
      />
      <PrototypeNote />
      <div className="three-col">
        <button className="quick-action" onClick={onCreate}>
          <span>
            <strong>Задача офису</strong>
            <small>Дизайн, реклама, бухгалтерия, хозяйство</small>
          </span>
          <PlusOutlined />
        </button>
        <Link to="/ministry/planning" className="quick-action">
          <span>
            <strong>Планировать мероприятие</strong>
            <small>Выбрать тип и прочитать регламент</small>
          </span>
          <ArrowRightOutlined />
        </Link>
        <Link to="/week" className="quick-action yellow">
          <span>
            <strong>Задача себе</strong>
            <small>Личный список дел по мероприятию</small>
          </span>
          <PlusOutlined />
        </Link>
      </div>
      <div className="two-col spaced">
        <section className="panel">
          <h3>Шаблоны прошедших мероприятий</h3>
          <p className="muted">
            Примеры названий из макета. Содержимое шаблонов пока не
            предоставлено.
          </p>
          {[
            "Бог рядом",
            "Дримеры",
            "Семейная конференция",
            "Рождество",
            "Пасха",
          ].map((t) => (
            <button
              className={`template-row ${template === t ? "chosen" : ""}`}
              key={t}
              onClick={() => setTemplate(t)}
            >
              <strong>{t}</strong>
              <span>Выбрать →</span>
            </button>
          ))}
        </section>
        <section className="panel">
          <h3>{template || "План мероприятия"}</h3>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              template
                ? "Для этого шаблона нужны программа и регламент"
                : "Выберите шаблон или начните с чистого плана"
            }
          />
          <Link to="/ministry/planning">
            <Button>Начать планирование</Button>
          </Link>
        </section>
      </div>
    </>
  );
}

export function PrayerPage() {
  const [requests, setRequests] = useState<
    { id: number; type: string; who: string; when: string; detail: string }[]
  >([]);
  const [form] = Form.useForm();
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ ВЗАИМОДЕЙСТВИЯ"
        title="Особые молитвы"
        description="Заявки на молитвы и благословения во время богослужения."
      />
      <PrototypeNote />
      <section className="panel">
        <h3>Новая заявка</h3>
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            setRequests([...requests, { ...values, id: Date.now() }]);
            form.resetFields();
          }}
          initialValues={{ type: "Молитва за исцеление", when: services[0] }}
        >
          <div className="four-col">
            <Form.Item name="type" label="Молитва" rules={[{ required: true }]}>
              <Select
                options={[
                  "Молитва за исцеление",
                  "Благословение ребёнка",
                  "Молитва за крещение",
                  "Благодарность",
                ].map((value) => ({ value, label: value }))}
              />
            </Form.Item>
            <Form.Item
              name="who"
              label="За кого"
              rules={[
                { required: true, whitespace: true, message: "Укажите имя" },
              ]}
            >
              <Input maxLength={120} />
            </Form.Item>
            <Form.Item name="when" label="Когда хотят">
              <Select
                options={services.map((value) => ({ value, label: value }))}
              />
            </Form.Item>
            <Form.Item name="detail" label="Детали">
              <Input maxLength={500} />
            </Form.Item>
          </div>
          <Button htmlType="submit" type="primary">
            Добавить в прототип
          </Button>
        </Form>
      </section>
      <section className="panel spaced">
        <h3>Заявки и статусы</h3>
        {requests.length ? (
          requests.map((r) => (
            <div className="list-row" key={r.id}>
              <div>
                <strong>
                  {r.type} · {r.who}
                </strong>
                <small>
                  {r.when} · {r.detail}
                </small>
              </div>
              <Tag color="orange">Ждёт согласования</Tag>
            </div>
          ))
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Заявок пока нет"
          />
        )}
      </section>
    </>
  );
}

export function CalendarPage() {
  const [month, setMonth] = useState(dayjs().startOf("month"));
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<
    { name: string; date: string; kind: string }[]
  >([]);
  const [filters, setFilters] = useState([
    "Богослужение",
    "Мероприятие",
    "Обучение",
  ]);
  const offset = (month.day() + 6) % 7;
  const days = Array.from({ length: 42 }, (_, i) =>
    month.subtract(offset, "day").add(i, "day"),
  );
  return (
    <>
      <PageTitle
        eyebrow="ОБЩИЙ КАЛЕНДАРЬ ЦЕРКВИ"
        title={month.format("MMMM YYYY")}
        description="События, служения и встречи команды."
        action={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setOpen(true)}
          >
            Событие
          </Button>
        }
      />
      <PrototypeNote />
      <div className="toolbar">
        <Space>
          <Button
            onClick={() => setMonth(month.subtract(1, "month"))}
            aria-label="Предыдущий месяц"
          >
            ←
          </Button>
          <Button onClick={() => setMonth(dayjs().startOf("month"))}>
            Сегодня
          </Button>
          <Button
            onClick={() => setMonth(month.add(1, "month"))}
            aria-label="Следующий месяц"
          >
            →
          </Button>
        </Space>
        <Checkbox.Group
          value={filters}
          onChange={setFilters}
          options={["Богослужение", "Мероприятие", "Обучение"]}
        />
      </div>
      <div className="calendar-grid">
        {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
          <div className="calendar-weekday" key={d}>
            {d}
          </div>
        ))}
        {days.map((d) => (
          <div
            className={`calendar-cell ${d.month() !== month.month() ? "outside" : ""} ${d.isSame(dayjs(), "day") ? "today" : ""}`}
            key={d.format("YYYY-MM-DD")}
          >
            <span className="day-number">{d.date()}</span>
            {d.day() === 0 && filters.includes("Богослужение") && (
              <div className="calendar-event worship">
                10:00 · Богослужение
                <br />
                13:00 · Богослужение
              </div>
            )}
            {events
              .filter(
                (e) =>
                  e.date === d.format("YYYY-MM-DD") && filters.includes(e.kind),
              )
              .map((e, i) => (
                <div className="calendar-event" key={i}>
                  {e.name}
                </div>
              ))}
          </div>
        ))}
      </div>
      <p className="muted spaced">
        Воскресные собрания — демонстрационное расписание. Бронирование
        помещений ещё не подключено.
      </p>
      <Modal
        open={open}
        onCancel={() => setOpen(false)}
        title="Событие календаря"
        footer={null}
        destroyOnClose
      >
        <Form
          layout="vertical"
          initialValues={{ date: dayjs(), kind: "Мероприятие" }}
          onFinish={(v) => {
            setEvents([
              ...events,
              { name: v.name, date: v.date.format("YYYY-MM-DD"), kind: v.kind },
            ]);
            setOpen(false);
          }}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, whitespace: true }]}
          >
            <Input maxLength={240} />
          </Form.Item>
          <Form.Item name="date" label="Дата" rules={[{ required: true }]}>
            <DatePicker />
          </Form.Item>
          <Form.Item name="kind" label="Тип">
            <Select
              options={["Мероприятие", "Обучение"].map((value) => ({
                value,
                label: value,
              }))}
            />
          </Form.Item>
          <Button type="primary" htmlType="submit">
            Добавить в прототип
          </Button>
        </Form>
      </Modal>
    </>
  );
}

function MonthFilter({
  month,
  setMonth,
}: {
  month: number;
  setMonth: (m: number) => void;
}) {
  return (
    <div className="pills spaced">
      <Button
        type={month === -1 ? "primary" : "default"}
        onClick={() => setMonth(-1)}
      >
        Весь год
      </Button>
      {Array.from({ length: 12 }, (_, i) => (
        <Button
          size="small"
          key={i}
          type={month === i ? "primary" : "default"}
          onClick={() => setMonth(i)}
        >
          {dayjs().month(i).format("MMM")}
        </Button>
      ))}
    </div>
  );
}
function sundays() {
  const start = dayjs().startOf("year");
  return Array.from({ length: 366 }, (_, i) => start.add(i, "day")).filter(
    (d) => d.year() === start.year() && d.day() === 0,
  );
}
export function SchedulePage() {
  const [month, setMonth] = useState(dayjs().month());
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  return (
    <>
      <PageTitle
        eyebrow="БОГОСЛУЖЕНИЕ · ГОДОВОЕ РАСПИСАНИЕ"
        title={`Расписание на ${dayjs().year()} год`}
        description="Одно полотно: собрания, позиции и назначенные служители."
      />
      <PrototypeNote />
      <MonthFilter month={month} setMonth={setMonth} />
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Служители на собраниях</h3>
          <Link to="/service">
            <Button>Открыть чек-лист</Button>
          </Link>
        </div>
        <div className="table-wrap schedule-table">
          <table>
            <thead>
              <tr>
                <th>Дата собрания</th>
                {positions.map((p) => (
                  <th key={p}>{p}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sundays()
                .filter((d) => month === -1 || d.month() === month)
                .flatMap((d) =>
                  services.slice(0, 2).map((s, index) => (
                    <tr key={`${d.format("MM-DD")}-${index}`}>
                      <td>
                        <strong>
                          {d.format("DD.MM")} · {s}
                        </strong>
                      </td>
                      {positions.map((p, j) => {
                        const key = `${d.format("MM-DD")}-${index}-${j}`;
                        return (
                          <td key={p}>
                            <Input
                              aria-label={`${d.format("DD.MM")} ${s}, ${p}`}
                              placeholder="Не назначен"
                              value={assignments[key] || ""}
                              onChange={(e) =>
                                setAssignments({
                                  ...assignments,
                                  [key]: e.target.value,
                                })
                              }
                              size="small"
                              maxLength={120}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  )),
                )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

type Block = {
  id: number;
  name: string;
  minutes: number;
  owner: string;
  note: string;
};
export const initialBlocks: Block[] = [
  {
    id: 1,
    name: "Приветственное видео",
    minutes: 3,
    owner: "Ивент",
    note: "Свет зала выключить, экран — приветственное видео.",
  },
  {
    id: 2,
    name: "Прославление, 1 часть",
    minutes: 10,
    owner: "Ведущий прославления",
    note: "Две быстрые песни. Лидер держит связь с командой.",
  },
  {
    id: 3,
    name: "МС и пожертвования",
    minutes: 5,
    owner: "МС",
    note: "Приветствие собрания и приглашение к участию.",
  },
  {
    id: 4,
    name: "Прославление, 2 часть",
    minutes: 20,
    owner: "Ведущий прославления",
    note: "Служение и молитва.",
  },
  {
    id: 5,
    name: "Выход проповедника",
    minutes: 2,
    owner: "Ивент",
    note: "Подготовить микрофон.",
  },
  {
    id: 6,
    name: "Проповедь",
    minutes: 40,
    owner: "Проповедник",
    note: "Слово Божье для церкви.",
  },
  {
    id: 7,
    name: "Призыв и молитва покаяния",
    minutes: 8,
    owner: "Проповедник",
    note: "Молитва с теми, кто принимает решение.",
  },
  {
    id: 8,
    name: "Закрытие",
    minutes: 5,
    owner: "МС",
    note: "Следующие шаги и объявления.",
  },
];
export function ServicePage() {
  const [selected, setSelected] = useState(services[0]);
  const [blocks, setBlocks] = useState<Block[]>(initialBlocks);
  const [start, setStart] = useState(600);
  const [positionFilter, setPositionFilter] = useState<string[]>([]);
  const [nextId, setNextId] = useState(9);
  const { message } = App.useApp();
  let time = start;
  function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= blocks.length) return;
    const copy = [...blocks];
    [copy[index], copy[target]] = [copy[target], copy[index]];
    setBlocks(copy);
  }
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ БОГОСЛУЖЕНИЯ"
        title="Чек-лист собрания"
        description="Подготовка команды и порядок проведения собрания."
        action={
          <Link to="/timer">
            <Button type="primary" icon={<PlayCircleOutlined />}>
              Таймер на экран
            </Button>
          </Link>
        }
      />
      <PrototypeNote />
      <div className="pills spaced">
        {services.map((s) => (
          <Button
            key={s}
            type={selected === s ? "primary" : "default"}
            onClick={() => setSelected(s)}
          >
            {s}
          </Button>
        ))}
      </div>
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Кто служит · {selected}</h3>
          <Link to="/schedule">
            <Button size="small">Расписание на год</Button>
          </Link>
        </div>
        <Checkbox.Group
          value={positionFilter}
          onChange={setPositionFilter}
          options={positions}
        />
        <div className="table-wrap spaced">
          <table>
            <thead>
              <tr>
                <th>Позиция</th>
                <th>Кто служит</th>
              </tr>
            </thead>
            <tbody>
              {positions
                .filter(
                  (p) => !positionFilter.length || positionFilter.includes(p),
                )
                .map((p) => (
                  <tr key={p}>
                    <td>{p}</td>
                    <td>
                      <Tag color="orange">Не назначен</Tag>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel spaced">
        <div className="section-heading">
          <h3>Ход собрания</h3>
          <Space>
            <span>Начало</span>
            <Button
              size="small"
              onClick={() => setStart(Math.max(0, start - 5))}
              aria-label="Начать на 5 минут раньше"
            >
              −
            </Button>
            <strong>
              {Math.floor(start / 60)
                .toString()
                .padStart(2, "0")}
              :{(start % 60).toString().padStart(2, "0")}
            </strong>
            <Button
              size="small"
              onClick={() => setStart(Math.min(1439, start + 5))}
              aria-label="Начать на 5 минут позже"
            >
              +
            </Button>
            <Tag color="gold">
              {blocks.reduce((sum, b) => sum + b.minutes, 0)} мин
            </Tag>
          </Space>
        </div>
        <div className="table-wrap">
          <table className="rundown">
            <thead>
              <tr>
                <th>Порядок</th>
                <th>Время</th>
                <th>Мин</th>
                <th>Блок</th>
                <th>Ответственный</th>
                <th>Что сделать</th>
              </tr>
            </thead>
            <tbody>
              {blocks.map((b, i) => {
                const begin = time;
                time += b.minutes;
                const fmt = (n: number) =>
                  `${Math.floor(n / 60) % 24}:${(n % 60).toString().padStart(2, "0")}`;
                return (
                  <tr key={b.id}>
                    <td>
                      <Space size={2}>
                        <Button
                          size="small"
                          disabled={i === 0}
                          onClick={() => move(i, -1)}
                          aria-label={`Поднять ${b.name}`}
                        >
                          ↑
                        </Button>
                        <Button
                          size="small"
                          disabled={i === blocks.length - 1}
                          onClick={() => move(i, 1)}
                          aria-label={`Опустить ${b.name}`}
                        >
                          ↓
                        </Button>
                        <Button
                          size="small"
                          danger
                          onClick={() =>
                            setBlocks(blocks.filter((x) => x.id !== b.id))
                          }
                          aria-label={`Удалить ${b.name}`}
                        >
                          ×
                        </Button>
                      </Space>
                    </td>
                    <td>
                      {fmt(begin)}–{fmt(time)}
                    </td>
                    <td>
                      <InputNumber
                        aria-label={`Длительность: ${b.name}`}
                        min={1}
                        max={180}
                        value={b.minutes}
                        onChange={(value) =>
                          setBlocks(
                            blocks.map((x) =>
                              x.id === b.id ? { ...x, minutes: value || 1 } : x,
                            ),
                          )
                        }
                      />
                    </td>
                    <td>
                      <strong>{b.name}</strong>
                    </td>
                    <td>{b.owner}</td>
                    <td>{b.note}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="pills spaced">
          {["Песня", "Молитва", "Объявления", "Интервью", "Свободный блок"].map(
            (name) => (
              <Button
                key={name}
                size="small"
                icon={<PlusOutlined />}
                onClick={() => {
                  setBlocks([
                    ...blocks,
                    {
                      id: nextId,
                      name,
                      minutes: 5,
                      owner: "Не назначен",
                      note: "",
                    },
                  ]);
                  setNextId(nextId + 1);
                }}
              >
                {name}
              </Button>
            ),
          )}
        </div>
      </section>
      <section className="panel spaced">
        <h3>Как собирается богослужение</h3>
        <div className="workflow">
          <span>1. Макет чек-листа</span>
          <ArrowRightOutlined />
          <span>2. Ценность и план МС</span>
          <ArrowRightOutlined />
          <span>3. Служители</span>
          <ArrowRightOutlined />
          <span>4. Слайды и видео</span>
          <ArrowRightOutlined />
          <strong>5. Planning Center → ProPresenter</strong>
        </div>
        <Button
          className="spaced"
          onClick={() =>
            message.info(
              "Интеграция с Planning Center требует отдельного согласования и подключения аккаунта.",
            )
          }
        >
          Planning Center · ещё не подключён
        </Button>
      </section>
      <div className="three-col spaced">
        <section className="panel">
          <h3>Служения с полным доступом</h3>
          <Link to="/ministry/event-team">Ивент →</Link>
          <p>Сторителлинг · база историй</p>
        </section>
        <section className="panel">
          <h3>Собрания отделения</h3>
          <p>ВС · воскресные собрания</p>
          <p>ОП · общая практика</p>
        </section>
        <section className="panel">
          <h3>Видение отделения</h3>
          <strong>«Каждое богослужение вдохновляет людей»</strong>
        </section>
      </div>
    </>
  );
}

export function TimerPage() {
  const [index, setIndex] = useState(0);
  const [seconds, setSeconds] = useState(initialBlocks[0].minutes * 60);
  const [running, setRunning] = useState(false);
  useEffect(() => {
    if (!running) return;
    const until = Date.now() + seconds * 1000;
    const handle = window.setInterval(() => {
      const left = Math.max(0, Math.ceil((until - Date.now()) / 1000));
      setSeconds(left);
      if (left === 0) setRunning(false);
    }, 250);
    return () => clearInterval(handle);
  }, [running, index, seconds]);
  function select(value: number) {
    const next = Math.max(0, Math.min(initialBlocks.length - 1, value));
    setRunning(false);
    setIndex(next);
    setSeconds(initialBlocks[next].minutes * 60);
  }
  return (
    <div className="timer-screen">
      <header>
        <Link to="/service">
          <ArrowLeftOutlined /> К чек-листу
        </Link>
        <span>ПРЕДПРОСМОТР · ТИПОВОЙ ПОРЯДОК</span>
        <span>1 ВС · начало 10:00</span>
      </header>
      <main>
        <div className="eyebrow">ТЕКУЩИЙ БЛОК</div>
        <h1>{initialBlocks[index].name}</h1>
        <div className={`timer-digits ${seconds === 0 ? "expired" : ""}`}>
          {Math.floor(seconds / 60)}:
          {(seconds % 60).toString().padStart(2, "0")}
        </div>
        <p>
          {index + 1} / {initialBlocks.length} · {initialBlocks[index].owner}
        </p>
        <div className="timer-progress">
          <span
            style={{
              width: `${Math.max(0, 100 - (seconds / (initialBlocks[index].minutes * 60)) * 100)}%`,
            }}
          />
        </div>
        <div className="timer-next">
          <strong>
            Дальше: {initialBlocks[index + 1]?.name || "Собрание завершено"}
          </strong>
          <span>{running ? "Идём по плану" : "Пауза"}</span>
        </div>
      </main>
      <footer>
        <Button onClick={() => select(index - 1)} disabled={index === 0}>
          ← Назад
        </Button>
        <Button
          className="yellow-button"
          icon={running ? <PauseOutlined /> : <PlayCircleOutlined />}
          onClick={() => setRunning(!running)}
          disabled={seconds === 0}
        >
          {running ? "Пауза" : "Старт"}
        </Button>
        <Button
          onClick={() => select(index + 1)}
          disabled={index === initialBlocks.length - 1}
        >
          Следующий блок →
        </Button>
        <Button
          onClick={() => {
            setRunning(false);
            setSeconds(seconds + 60);
          }}
        >
          +1 мин
        </Button>
      </footer>
    </div>
  );
}

export function McPage() {
  const [month, setMonth] = useState(dayjs().month());
  const [rows, setRows] = useState<
    Record<
      string,
      {
        host: string;
        value: string;
        text: string;
        story: string;
        slides: string;
        done: boolean;
      }
    >
  >({});
  const values = ["Служение", "Спасение", "Духовный рост", "Слово"];
  return (
    <>
      <PageTitle
        eyebrow="КАЛЕНДАРЬ И ГОДОВОЙ ПЛАН МС"
        title={`План служения МС · ${dayjs().year()}`}
        description="Ценность недели, благодарность служениям и слова ведущего."
      />
      <PrototypeNote />
      <MonthFilter month={month} setMonth={setMonth} />
      <section className="panel spaced">
        <div className="table-wrap">
          <table className="mc-table">
            <thead>
              <tr>
                {[
                  "Воскресенье",
                  "МС",
                  "Ценность",
                  "Что говорит МС",
                  "Сторителлинг / интервью",
                  "Слайды и видео",
                  "Готово",
                ].map((t) => (
                  <th key={t}>{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sundays()
                .filter((d) => month === -1 || d.month() === month)
                .map((d) => {
                  const key = d.format("YYYY-MM-DD");
                  const row = rows[key] || {
                    host: "",
                    value: "Служение",
                    text: "",
                    story: "",
                    slides: "",
                    done: false,
                  };
                  function update(patch: Partial<typeof row>) {
                    setRows({ ...rows, [key]: { ...row, ...patch } });
                  }
                  return (
                    <tr key={key}>
                      <td>{d.format("DD.MM")}</td>
                      <td>
                        <Input
                          aria-label={`МС ${key}`}
                          placeholder="Назначить МС"
                          value={row.host}
                          onChange={(e) => update({ host: e.target.value })}
                        />
                      </td>
                      <td>
                        <Select
                          aria-label={`Ценность ${key}`}
                          value={row.value}
                          options={values.map((value) => ({
                            value,
                            label: value,
                          }))}
                          onChange={(value) => update({ value })}
                        />
                      </td>
                      <td>
                        <Input.TextArea
                          aria-label={`Слова МС ${key}`}
                          value={row.text}
                          onChange={(e) => update({ text: e.target.value })}
                        />
                      </td>
                      <td>
                        <Input.TextArea
                          aria-label={`История ${key}`}
                          value={row.story}
                          onChange={(e) => update({ story: e.target.value })}
                        />
                      </td>
                      <td>
                        <Input.TextArea
                          aria-label={`Слайды ${key}`}
                          value={row.slides}
                          onChange={(e) => update({ slides: e.target.value })}
                        />
                      </td>
                      <td>
                        <Checkbox
                          aria-label={`Готово ${key}`}
                          checked={row.done}
                          onChange={(e) => update({ done: e.target.checked })}
                        />
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel spaced">
        <h3>График ценностей</h3>
        <div className="pills">
          {values.map((v, i) => (
            <Tag color={["blue", "green", "gold", "cyan"][i]} key={v}>
              {v}
            </Tag>
          ))}
        </div>
        <p className="muted">
          Перенос текста МС в чек-лист и календарь будет подключён после
          согласования процесса.
        </p>
      </section>
    </>
  );
}
