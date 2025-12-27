"use client";

import { useMemo, useState } from "react";
import { Calendar, dayjsLocalizer, Event, SlotInfo } from "react-big-calendar";
import dayjs from "dayjs";
import "react-big-calendar/lib/css/react-big-calendar.css";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type PreventiveEvent = Event & {
  id: number;
  equipmentName: string;
  teamName: string;
};

export function CalendarView({
  events,
  onCreate,
}: {
  events: PreventiveEvent[];
  onCreate?: (data: { date: Date; subject: string }) => void;
}) {
  const localizer = useMemo(() => dayjsLocalizer(dayjs), []);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [subject, setSubject] = useState("");

  const handleSelectSlot = (slot: SlotInfo) => {
    const date = Array.isArray(slot.start) ? slot.start[0] : slot.start;
    setSelectedDate(date);
    setSubject("");
    setDialogOpen(true);
  };

  const handleCreate = () => {
    if (!selectedDate || !subject.trim()) return;
    onCreate?.({ date: selectedDate, subject: subject.trim() });
    setDialogOpen(false);
  };

  return (
    <div>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        selectable
        views={["month", "week", "day"]}
        style={{ height: "70vh" }}
        onSelectSlot={handleSelectSlot}
      />
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule preventive maintenance</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <Label>Date</Label>
              <div className="text-sm text-muted-foreground">
                {selectedDate ? dayjs(selectedDate).format("YYYY-MM-DD") : "--"}
              </div>
            </div>
            <div className="space-y-1">
              <Label>Subject</Label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Monthly filter cleaning"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={!subject.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
