"use client";

import { useState } from "react";
import { KanbanBoard } from "@/components/Kanban";
import { RequestCard, RequestStage } from "@/lib/types";

const initialData: RequestCard[] = [
  {
    id: 1,
    subject: "Leaking oil",
    requestType: "corrective",
    stage: "new",
    equipmentName: "CNC Machine 01",
    teamName: "Mechanics",
    assignedTo: null,
    scheduledDate: null,
    overdue: false,
  },
  {
    id: 2,
    subject: "Laptop annual check",
    requestType: "preventive",
    stage: "in_progress",
    equipmentName: "Laptop-IT-44",
    teamName: "IT Support",
    assignedTo: { id: 10, name: "Aisha Khan", avatarUrl: "" },
    scheduledDate: "2024-12-01",
    overdue: true,
  },
  {
    id: 3,
    subject: "Hydraulic pressure low",
    requestType: "corrective",
    stage: "repaired",
    equipmentName: "Press-12",
    teamName: "Mechanics",
    assignedTo: { id: 11, name: "Luis M", avatarUrl: "" },
    scheduledDate: "2024-12-15",
    overdue: false,
  },
  {
    id: 4,
    subject: "Broken hinge",
    requestType: "corrective",
    stage: "scrap",
    equipmentName: "Gate-03",
    teamName: "Electricians",
    assignedTo: { id: 12, name: "Chen Li", avatarUrl: "" },
    scheduledDate: null,
    overdue: false,
  },
];

export default function RequestsPage() {
  const [data, setData] = useState<RequestCard[]>(initialData);

  const handleStageChange = (id: number, stage: RequestStage) => {
    setData((prev) => prev.map((r) => (r.id === id ? { ...r, stage } : r)));
    // Later: call API PATCH /requests/{id}/stage
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Requests (Kanban)</h1>
        <p className="text-sm text-muted-foreground">
          Drag cards to change stage. Overdue = red bar if scheduled date is
          past and not repaired/scrap.
        </p>
      </div>
      <KanbanBoard requests={data} onStageChange={handleStageChange} />
    </div>
  );
}
