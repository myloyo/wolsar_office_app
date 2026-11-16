import dayjs from "dayjs";
export function planningWeek(value: string) {
  const day = dayjs(value);
  const offset = (day.day() + 4) % 7;
  return day.subtract(offset, "day").format("YYYY-MM-DD");
}
