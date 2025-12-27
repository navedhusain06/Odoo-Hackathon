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

export interface RequestApiResponse {
  id: number;
  subject: string;
  request_type: RequestType;
  stage: RequestStage;
  equipment_id: number;
  equipment_name: string;
  team_id: number;
  team_name: string;
  assigned_to_id: number | null;
  assigned_to_name: string | null;
  scheduled_start: string | null;
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
