"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/Kanban";
import { api } from "@/lib/api";
import {
  RequestApiResponse,
  RequestCard,
  RequestStage,
  RequestType,
} from "@/lib/types";

function mapRequest(r: RequestApiResponse): RequestCard {
  const overdue =
    !!r.scheduled_start &&
    ["new", "in_progress"].includes(r.stage) &&
    new Date(r.scheduled_start) < new Date();

  return {
    id: r.id,
    subject: r.subject,
    requestType: r.request_type,
    stage: r.stage,
    scheduledDate: r.scheduled_start,
    equipmentName: r.equipment_name,
    teamName: r.team_name,
    assignedTo: r.assigned_to_id
      ? { id: r.assigned_to_id, name: r.assigned_to_name || "" }
      : null,
    overdue,
  };
}

export default function RequestsPage() {
  const [data, setData] = useState<RequestCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api<RequestApiResponse[]>("/requests");
      setData(res.map(mapRequest));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load requests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleStageChange = async (id: number, stage: RequestStage) => {
    // optimistic update
    setData((prev) => prev.map((r) => (r.id === id ? { ...r, stage } : r)));
    try {
      const updated = await api<RequestApiResponse>(
        `/requests/${id}/stage`,
        {
          method: "PATCH",
          body: { stage, actual_duration_hours: stage === "repaired" ? 1 : undefined },
        }
      );
      setData((prev) =>
        prev.map((r) => (r.id === id ? mapRequest(updated) : r))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update stage");
      // reload to resync
      void load();
    }
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
      {error ? (
        <div className="text-sm text-rose-600">{error}</div>
      ) : null}
      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : (
        <KanbanBoard requests={data} onStageChange={handleStageChange} />
      )}
    </div>
  );
}
