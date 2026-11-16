import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  App,
  Button,
  Checkbox,
  DatePicker,
  Input,
  InputNumber,
  Select,
  Space,
  Tag,
} from "antd";
import dayjs from "dayjs";
import { api, type Bootstrap } from "../api";
import { PageTitle } from "../components/PageTitle";
import { DataEditor, Load, useResource } from "./shared";
import type { Ceremony, ChurchEvent, Mc } from "./types";

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
  "Сторителлинг",
  "Молитва на сцене",
  "Режиссёр",
  "Трансляция",
];
export function WorshipPage({
  user,
  data,
  mode = "service",
}: {
  user: number;
  data: Bootstrap;
  mode?: "service" | "schedule" | "mc";
}) {
  const [year, setYear] = useState(dayjs().year());
  const list = useResource<ChurchEvent[]>(`/services?year=${year}`, user);
  const [params, setParams] = useSearchParams();
  const selected = Number(params.get("service")) || list.data?.[0]?.id || 0;
  const detail = useResource<Ceremony>(`/services/${selected}`, user);
  const [adding, setAdding] = useState(false);
  const actor = data.users.find((u) => u.id === user);
  const canWrite =
    !!actor &&
    (actor.roles.includes("admin") ||
      (actor.roles.includes("office") && actor.department_ids.includes(1)));
  return (
    <>
      <PageTitle
        eyebrow="ОТДЕЛЕНИЕ БОГОСЛУЖЕНИЯ"
        title={
          mode === "mc"
            ? "Годовой план МС"
            : mode === "schedule"
              ? "Расписание служителей"
              : "Чек-лист собрания"
        }
        description="Программа, назначения и план МС используют одну запись собрания."
        action={
          canWrite && (
            <Button type="primary" onClick={() => setAdding(true)}>
              Создать собрание
            </Button>
          )
        }
      />
      <div className="toolbar">
        <DatePicker
          picker="year"
          allowClear={false}
          value={dayjs().year(year)}
          onChange={(date) => {
            if (date) {
              setYear(date.year());
              setParams({});
            }
          }}
        />
        <Select
          style={{ minWidth: 280 }}
          value={selected || undefined}
          options={list.data?.map((e) => ({
            value: e.id,
            label: `${dayjs(e.starts_at).format("DD.MM HH:mm")} · ${e.title}`,
          }))}
          onChange={(id) => setParams({ service: String(id) })}
        />
        <Button
          onClick={() => {
            void list.reload();
            void detail.reload();
          }}
        >
          Обновить
        </Button>
      </div>
      {mode !== "service" && (
        <section className="panel spaced">
          <div className="table-wrap">
            <table style={{ minWidth: mode === "schedule" ? 1500 : 900 }}>
              <thead>
                <tr>
                  <th>Собрание</th>
                  {mode === "schedule" ? (
                    positions.map((p) => <th key={p}>{p}</th>)
                  ) : (
                    <>
                      <th>МС</th>
                      <th>Ценность</th>
                      <th>Что говорит МС</th>
                      <th>Готово</th>
                    </>
                  )}
                  <th />
                </tr>
              </thead>
              <tbody>
                {list.data?.map((event) => (
                  <tr key={event.id}>
                    <td>
                      {dayjs(event.starts_at).format("DD.MM HH:mm")} ·{" "}
                      {event.title}
                    </td>
                    {mode === "schedule" ? (
                      positions.map((p) => (
                        <td key={p}>
                          {data.users.find(
                            (u) => u.id === event.assignments?.[p],
                          )?.name || "—"}
                        </td>
                      ))
                    ) : (
                      <>
                        <td>
                          {data.users.find((u) => u.id === event.mc?.host_id)
                            ?.name || "Не назначен"}
                        </td>
                        <td>{event.mc?.value}</td>
                        <td>{event.mc?.text.slice(0, 100)}</td>
                        <td>{event.mc?.ready ? "Готово" : "Нет"}</td>
                      </>
                    )}
                    <td>
                      <Button
                        size="small"
                        onClick={() => setParams({ service: String(event.id) })}
                      >
                        Открыть
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <div className="pills spaced">
        <Link to={`/service?service=${selected}`}>
          <Button type={mode === "service" ? "primary" : "default"}>
            Чек-лист
          </Button>
        </Link>
        <Link to={`/schedule?service=${selected}`}>
          <Button type={mode === "schedule" ? "primary" : "default"}>
            Назначения
          </Button>
        </Link>
        <Link to={`/mc?service=${selected}`}>
          <Button type={mode === "mc" ? "primary" : "default"}>План МС</Button>
        </Link>
        {selected > 0 && (
          <Link to={`/timer?service=${selected}`}>
            <Button>Таймер на экран</Button>
          </Link>
        )}
      </div>
      <Load loading={list.loading} error={list.error}>
        {!list.data?.length ? (
          <section className="panel spaced">
            <p>Собрания на этот год ещё не созданы.</p>
          </section>
        ) : (
          <Load loading={detail.loading} error={detail.error}>
            {detail.data && (
              <ProgramEditor
                key={`${selected}-${detail.data.version}`}
                ceremony={detail.data}
                user={user}
                data={data}
                canWrite={canWrite}
                mode={mode}
                onSaved={async () => {
                  await detail.reload();
                  await list.reload();
                }}
              />
            )}
          </Load>
        )}
      </Load>
      {adding && (
        <DataEditor
          title="Новое собрание"
          fields={[
            { name: "day", label: "Дата", type: "date", required: true },
            {
              name: "kind",
              label: "Собрание",
              type: "select",
              required: true,
              options: ["1 ВС", "2 ВС", "ОП", "ВХМ"].map((value) => ({
                value,
                label: value,
              })),
            },
          ]}
          initial={{ day: dayjs().format("YYYY-MM-DD"), kind: "1 ВС" }}
          onClose={() => setAdding(false)}
          save={async (values) => {
            const result = await api<Ceremony>(
              "/services",
              user,
              "POST",
              values,
            );
            setYear(dayjs(result.event.starts_at).year());
            setParams({ service: String(result.event.id) });
            await list.reload();
          }}
        />
      )}
    </>
  );
}
function ProgramEditor({
  ceremony,
  user,
  data,
  canWrite,
  mode,
  onSaved,
}: {
  ceremony: Ceremony;
  user: number;
  data: Bootstrap;
  canWrite: boolean;
  mode: string;
  onSaved: () => Promise<void>;
}) {
  const [program, setProgram] = useState(() =>
    structuredClone(ceremony.program),
  );
  const [saving, setSaving] = useState(false);
  const { message } = App.useApp();
  const options = data.users.map((u) => ({ value: u.id, label: u.name }));
  const disabled = !canWrite || saving || ceremony.timer.running;
  function mc(patch: Partial<Mc>) {
    setProgram({ ...program, mc: { ...program.mc, ...patch } });
  }
  function move(index: number, delta: number) {
    const copy = [...program.blocks];
    const next = index + delta;
    if (next < 0 || next >= copy.length) return;
    [copy[index], copy[next]] = [copy[next], copy[index]];
    setProgram({ ...program, blocks: copy });
  }
  let elapsed = 0;
  return (
    <section className="panel spaced">
      <div className="section-heading">
        <h3>
          {ceremony.event.title} ·{" "}
          {dayjs(ceremony.event.starts_at).format("D MMMM HH:mm")}
        </h3>
        <Tag color={ceremony.timer.running ? "orange" : "green"}>
          {ceremony.timer.running ? "Идёт собрание" : "Можно планировать"}
        </Tag>
      </div>
      {mode === "service" && (
        <>
          <h3>Ход собрания</h3>
          <div className="table-wrap">
            <table className="rundown">
              <thead>
                <tr>
                  <th>Порядок</th>
                  <th>Время</th>
                  <th>Блок</th>
                  <th>Мин</th>
                  <th>Ответственный</th>
                  <th>Что сделать</th>
                </tr>
              </thead>
              <tbody>
                {program.blocks.map((block, index) => {
                  const at = dayjs(ceremony.event.starts_at).add(
                    elapsed,
                    "minute",
                  );
                  elapsed += block.minutes;
                  return (
                    <tr key={block.id}>
                      <td>
                        <Space size={2}>
                          <Button
                            disabled={disabled || index === 0}
                            size="small"
                            onClick={() => move(index, -1)}
                          >
                            ↑
                          </Button>
                          <Button
                            disabled={
                              disabled || index === program.blocks.length - 1
                            }
                            size="small"
                            onClick={() => move(index, 1)}
                          >
                            ↓
                          </Button>
                          <Button
                            disabled={disabled || program.blocks.length === 1}
                            size="small"
                            onClick={() =>
                              setProgram({
                                ...program,
                                blocks: program.blocks.filter(
                                  (b) => b.id !== block.id,
                                ),
                              })
                            }
                          >
                            ×
                          </Button>
                        </Space>
                      </td>
                      <td>{at.format("HH:mm")}</td>
                      <td>
                        <Input
                          aria-label={`Название блока ${index + 1}`}
                          disabled={disabled}
                          value={block.name}
                          onChange={(e) =>
                            setProgram({
                              ...program,
                              blocks: program.blocks.map((b) =>
                                b.id === block.id
                                  ? { ...b, name: e.target.value }
                                  : b,
                              ),
                            })
                          }
                        />
                      </td>
                      <td>
                        <InputNumber
                          disabled={disabled}
                          min={1}
                          max={180}
                          value={block.minutes}
                          onChange={(value) =>
                            setProgram({
                              ...program,
                              blocks: program.blocks.map((b) =>
                                b.id === block.id
                                  ? { ...b, minutes: value || 1 }
                                  : b,
                              ),
                            })
                          }
                        />
                      </td>
                      <td>
                        <Select
                          disabled={disabled}
                          allowClear
                          style={{ minWidth: 180 }}
                          value={block.owner_id ?? undefined}
                          options={options}
                          onChange={(value) =>
                            setProgram({
                              ...program,
                              blocks: program.blocks.map((b) =>
                                b.id === block.id
                                  ? { ...b, owner_id: value ?? null }
                                  : b,
                              ),
                            })
                          }
                        />
                      </td>
                      <td>
                        <Input.TextArea
                          disabled={disabled}
                          value={block.note}
                          onChange={(e) =>
                            setProgram({
                              ...program,
                              blocks: program.blocks.map((b) =>
                                b.id === block.id
                                  ? { ...b, note: e.target.value }
                                  : b,
                              ),
                            })
                          }
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Button
            className="spaced"
            disabled={disabled}
            onClick={() =>
              setProgram({
                ...program,
                blocks: [
                  ...program.blocks,
                  {
                    id: crypto.randomUUID(),
                    name: "Новый блок",
                    minutes: 5,
                    owner_id: null,
                    note: "",
                  },
                ],
              })
            }
          >
            Добавить блок
          </Button>
        </>
      )}
      {(mode === "schedule" || mode === "service") && (
        <>
          <h3 className="spaced">Кто служит</h3>
          <div className="two-col">
            {positions.map((position) => (
              <div className="list-row" key={position}>
                <span>{position}</span>
                <Select
                  aria-label={`Назначение ${position}`}
                  disabled={disabled}
                  allowClear
                  style={{ minWidth: 190 }}
                  placeholder="Не назначен"
                  value={program.assignments[position] ?? undefined}
                  options={options}
                  onChange={(value) =>
                    setProgram({
                      ...program,
                      assignments: {
                        ...program.assignments,
                        [position]: value ?? null,
                      },
                    })
                  }
                />
              </div>
            ))}
          </div>
        </>
      )}
      {mode === "mc" && (
        <>
          <h3>План МС</h3>
          <div className="two-col">
            <div>
              <p>Ведущий</p>
              <Select
                disabled={disabled}
                allowClear
                style={{ width: "100%" }}
                options={options}
                value={program.mc.host_id ?? undefined}
                onChange={(value) => mc({ host_id: value ?? null })}
              />
            </div>
            <div>
              <p>Ценность</p>
              <Select
                disabled={disabled}
                style={{ width: "100%" }}
                options={["Служение", "Спасение", "Духовный рост", "Слово"].map(
                  (value) => ({ value, label: value }),
                )}
                value={program.mc.value}
                onChange={(value) => mc({ value })}
              />
            </div>
          </div>
          <p className="spaced">Что говорит МС</p>
          <Input.TextArea
            disabled={disabled}
            rows={5}
            value={program.mc.text}
            onChange={(e) => mc({ text: e.target.value })}
          />
          <p className="spaced">Сторителлинг / интервью</p>
          <Input.TextArea
            disabled={disabled}
            rows={3}
            value={program.mc.story}
            onChange={(e) => mc({ story: e.target.value })}
          />
          <p className="spaced">Слайды и видео</p>
          <Input.TextArea
            disabled={disabled}
            value={program.mc.slides}
            onChange={(e) => mc({ slides: e.target.value })}
          />
          <Checkbox
            className="spaced"
            disabled={disabled}
            checked={program.mc.ready}
            onChange={(e) => mc({ ready: e.target.checked })}
          >
            Материалы готовы
          </Checkbox>
        </>
      )}
      {canWrite && (
        <Button
          className="spaced"
          type="primary"
          loading={saving}
          disabled={disabled}
          onClick={async () => {
            setSaving(true);
            try {
              await api(`/services/${ceremony.event.id}/program`, user, "PUT", {
                ...program,
                expected_version: ceremony.version,
              });
              await onSaved();
              message.success("Собрание сохранено");
            } catch (e) {
              message.error((e as Error).message);
            } finally {
              setSaving(false);
            }
          }}
        >
          Сохранить изменения
        </Button>
      )}
      <p className="muted spaced">
        Сохранение программы возвращает таймер к первому блоку. Во время
        запущенного таймера редактирование заблокировано.
      </p>
    </section>
  );
}
export function LiveTimer({ user, data }: { user: number; data?: Bootstrap }) {
  const [params] = useSearchParams();
  const id = Number(params.get("service"));
  const [ceremony, setCeremony] = useState<Ceremony>();
  const [error, setError] = useState("");
  const [received, setReceived] = useState(Date.now());
  const lastVersion = useRef(0);
  const [clock, setClock] = useState(Date.now());
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();
  const actor = data?.users.find((u) => u.id === user);
  const canWrite =
    actor?.roles.includes("admin") ||
    (actor?.roles.includes("office") && actor.department_ids.includes(1));
  useEffect(() => {
    if (!id) return;
    lastVersion.current = 0;
    let active = true;
    const load = async () => {
      try {
        const next = await api<Ceremony>(`/services/${id}`, user);
        if (active && next.version >= lastVersion.current) {
          lastVersion.current = next.version;
          setCeremony((previous) =>
            !previous || next.version >= previous.version ? next : previous,
          );
          setReceived(Date.now());
          setError("");
        }
      } catch (e) {
        if (active) setError((e as Error).message);
      }
    };
    void load();
    const poll = setInterval(() => void load(), 3000);
    const tick = setInterval(() => setClock(Date.now()), 250);
    return () => {
      active = false;
      clearInterval(poll);
      clearInterval(tick);
    };
  }, [id, user]);
  const seconds = ceremony
    ? Math.max(
        0,
        ceremony.timer.remaining -
          (ceremony.timer.running
            ? Math.floor(Math.max(0, clock - received) / 1000)
            : 0),
      )
    : 0;
  const block = ceremony?.program.blocks[ceremony.timer.index];
  async function action(action: string) {
    if (!ceremony) return;
    setBusy(true);
    try {
      const next = await api<Ceremony>(`/services/${id}/timer`, user, "POST", {
        action,
        expected_version: ceremony.version,
      });
      lastVersion.current = next.version;
      setCeremony(next);
      setReceived(Date.now());
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="timer-screen">
      <header>
        <Link to={`/service?service=${id}`}>← К чек-листу</Link>
        <span>{ceremony?.event.title || "Таймер собрания"}</span>
        <span>Синхронизация каждые 3 секунды</span>
      </header>
      <main>
        {error && <p>{error}</p>}
        {!id ? (
          <Link to="/service">Откройте таймер из выбранного собрания</Link>
        ) : (
          <>
            <div className="eyebrow">ТЕКУЩИЙ БЛОК</div>
            <h1>{block?.name || "Загрузка"}</h1>
            <div className={`timer-digits ${seconds === 0 ? "expired" : ""}`}>
              {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}
            </div>
            <p>{block?.note}</p>
            <div className="timer-next">
              <strong>
                Дальше:{" "}
                {ceremony?.program.blocks[(ceremony?.timer.index || 0) + 1]
                  ?.name || "Завершение"}
              </strong>
              <span>{ceremony?.timer.running ? "Идём по плану" : "Пауза"}</span>
            </div>
          </>
        )}
      </main>
      {canWrite && ceremony && (
        <footer>
          <Button disabled={busy} onClick={() => void action("previous")}>
            ← Назад
          </Button>
          <Button
            className="yellow-button"
            disabled={busy}
            onClick={() =>
              void action(ceremony.timer.running ? "pause" : "start")
            }
          >
            {ceremony.timer.running ? "Пауза" : "Старт"}
          </Button>
          <Button disabled={busy} onClick={() => void action("next")}>
            Следующий блок →
          </Button>
          <Button disabled={busy} onClick={() => void action("minute")}>
            +1 мин
          </Button>
          <Button disabled={busy} onClick={() => void action("reset")}>
            Сначала
          </Button>
        </footer>
      )}
    </div>
  );
}
