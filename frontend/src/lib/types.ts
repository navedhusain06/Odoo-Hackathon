export type RequestStage = "new" | "in_progress" | "repaired" | "scrap";
export type RequestType = "corrective" | "preventive";

export interface RequestCard {
  id: number;
  subject: string;
  requestType: RequestType;
  stage: RequestStage;
  scheduledDate?: string | null;
  equipmentName: string;
  teamName: string;
  assignedTo?: { id: number; name: string; avatarUrl?: string | null } | null;
  overdue: boolean;
}

export interface EquipmentItem {
  id: number;
  name: string;
  serialNumber?: string | null;
  department?: string | null;
  owner?: string | null;
  team?: string | null;
  defaultTechnician?: string | null;
  maintenanceOpenCount: number;
}
