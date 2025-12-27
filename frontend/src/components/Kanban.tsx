"use client";

import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RequestCard, RequestStage } from "@/lib/types";
import clsx from "clsx";

type StageColumn = {
  id: RequestStage;
  title: string;
  accent: string;
};

const columns: StageColumn[] = [
  { id: "new", title: "New", accent: "border-l-slate-300" },
  { id: "in_progress", title: "In Progress", accent: "border-l-amber-400" },
  { id: "repaired", title: "Repaired", accent: "border-l-emerald-400" },
  { id: "scrap", title: "Scrap", accent: "border-l-rose-400" },
];

const stageKeys: RequestStage[] = ["new", "in_progress", "repaired", "scrap"];

function SortableItem({ request }: { request: RequestCard }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: request.id });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
  };

  const overdue =
    request.overdue &&
    request.stage !== "repaired" &&
    request.stage !== "scrap";

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="mb-3"
    >
      <Card
        className={clsx(
          "border-l-4 shadow-sm",
          overdue ? "border-l-rose-500" : "border-l-transparent",
          isDragging && "ring-2 ring-ring"
        )}
      >
        <CardHeader className="pb-2">
          <CardTitle className="text-base">{request.subject}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <Badge variant="outline">{request.requestType}</Badge>
            <span className="text-xs">{request.equipmentName}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs">{request.teamName}</span>
            {overdue && (
              <span className="text-xs text-rose-500 font-medium">Overdue</span>
            )}
          </div>
          {request.assignedTo && (
            <div className="flex items-center gap-2 pt-1">
              <Avatar className="h-7 w-7">
                {request.assignedTo.avatarUrl ? (
                  <AvatarImage
                    src={request.assignedTo.avatarUrl}
                    alt={request.assignedTo.name}
                  />
                ) : null}
                <AvatarFallback>
                  {request.assignedTo.name
                    .split(" ")
                    .map((n) => n[0] || "")
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="text-xs text-foreground">
                {request.assignedTo.name}
              </span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Column({ col, items }: { col: StageColumn; items: RequestCard[] }) {
  const { setNodeRef, isOver } = useDroppable({
    id: col.id,
  });

  return (
    <Card key={col.id} className="bg-muted/30">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm">{col.title}</CardTitle>
        <Badge variant="secondary">{items.length}</Badge>
      </CardHeader>
      <CardContent
        ref={setNodeRef}
        className={clsx(
          "min-h-[200px] border-l pl-3 transition-colors",
          col.accent,
          isOver && "bg-muted/50"
        )}
      >
        <SortableContext
          id={col.id}
          items={items.map((r) => r.id)}
          strategy={verticalListSortingStrategy}
        >
          <div className="space-y-0">
            {items.map((r) => (
              <SortableItem key={r.id} request={r} />
            ))}
          </div>
        </SortableContext>
      </CardContent>
    </Card>
  );
}

export function KanbanBoard({
  requests,
  onStageChange,
}: {
  requests: RequestCard[];
  onStageChange?: (id: number, stage: RequestStage) => void;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  );

  const itemsByStage: Record<RequestStage, RequestCard[]> = {
    new: [],
    in_progress: [],
    repaired: [],
    scrap: [],
  };
  requests.forEach((r) => {
    const stage = stageKeys.includes(r.stage) ? r.stage : "new";
    itemsByStage[stage].push(r);
  });

  const handleDragEnd = (event: DragEndEvent) => {
    const { over, active } = event;
    if (!over) return;

    const targetStage =
      (over.data.current?.sortable?.containerId as RequestStage | undefined) ||
      (over.id as RequestStage | undefined);

    if (!targetStage || !stageKeys.includes(targetStage)) return;

    const cardId = Number(active.id);
    const card = requests.find((r) => r.id === cardId);
    if (!card || card.stage === targetStage) return;

    onStageChange?.(cardId, targetStage);
  };

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="grid gap-4 md:grid-cols-4">
        {columns.map((col) => (
          <Column key={col.id} col={col} items={itemsByStage[col.id]} />
        ))}
      </div>
    </DndContext>
  );
}
