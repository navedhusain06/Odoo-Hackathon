"use client";

import { useState } from "react";
import dayjs from "dayjs";
import { CalendarView } from "@/components/CalendarView";

type PreventiveEvent = {
  id: number;
  title: string;
  start: Date;
  end: Date;
  equipmentName: string;
  teamName: string;
};

const initialEvents: PreventiveEvent[] = [
  {
    id: 1,
    title: "Monthly filter cleaning",
    start: dayjs().add(1, "day").toDate(),
    end: dayjs().add(1, "day").toDate(),
    equipmentName: "Air Handler 02",
    teamName: "Mechanics",
  },
  {
    id: 2,
    title: "Battery health check",
    start: dayjs().add(3, "day").toDate(),
    end: dayjs().add(3, "day").toDate(),
    equipmentName: "Forklift A1",
    teamName: "Electricians",
  },
];

export default function CalendarPage() {
  const [events, setEvents] = useState<PreventiveEvent[]>(initialEvents);

  const handleCreate = ({ date, subject }: { date: Date; subject: string }) => {
    const nextId = (events.at(-1)?.id || 0) + 1;
    setEvents((prev) => [
      ...prev,
      {
        id: nextId,
        title: subject,
        start: date,
        end: date,
        equipmentName: "TBD",
        teamName: "TBD",
      },
    ]);
    // Later: POST /requests with type=preventive, scheduled_date=date
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Preventive Calendar</h1>
        <p className="text-sm text-muted-foreground">
          Shows preventive requests. Click a date to schedule a new one.
        </p>
      </div>
      <CalendarView events={events} onCreate={handleCreate} />
    </div>
  );
}
