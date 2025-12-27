"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EquipmentItem } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

const mockEquipment: EquipmentItem[] = [
  {
    id: 1,
    name: "CNC Machine 01",
    serialNumber: "CNC-001",
    department: "Production",
    owner: "Ali K.",
    team: "Mechanics",
    defaultTechnician: "Aisha Khan",
    maintenanceOpenCount: 3,
  },
  {
    id: 2,
    name: "Laptop-IT-44",
    serialNumber: "LT-44",
    department: "IT",
    owner: "Sara M.",
    team: "IT Support",
    defaultTechnician: "Chen Li",
    maintenanceOpenCount: 1,
  },
  {
    id: 3,
    name: "Forklift A1",
    serialNumber: "FL-A1",
    department: "Logistics",
    owner: "Depot Lead",
    team: "Electricians",
    defaultTechnician: "Luis M",
    maintenanceOpenCount: 0,
  },
];

export default function EquipmentPage() {
  const [department, setDepartment] = useState<string | undefined>();
  const [owner, setOwner] = useState<string | undefined>();
  const [query, setQuery] = useState("");

  const departments = useMemo(
    () =>
      Array.from(
        new Set(mockEquipment.map((e) => e.department).filter(Boolean))
      ),
    []
  );
  const owners = useMemo(
    () =>
      Array.from(new Set(mockEquipment.map((e) => e.owner).filter(Boolean))),
    []
  );

  const filtered = mockEquipment.filter((e) => {
    return (
      (!department || e.department === department) &&
      (!owner || e.owner === owner) &&
      (!query ||
        e.name.toLowerCase().includes(query.toLowerCase()) ||
        (e.serialNumber || "").toLowerCase().includes(query.toLowerCase()))
    );
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Equipment</h1>
        <p className="text-sm text-muted-foreground">
          Filter by department/owner. Smart button shows maintenance requests
          for the equipment.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <CardTitle className="text-base">Filters</CardTitle>
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
            <Input
              placeholder="Search name or serial"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full md:w-56"
            />
            <Select
              onValueChange={(v) => setDepartment(v === "all" ? undefined : v)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {departments.map((d) => (
                  <SelectItem key={d} value={d}>
                    {d}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              onValueChange={(v) => setOwner(v === "all" ? undefined : v)}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Owner" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {owners.map((o) => (
                  <SelectItem key={o} value={o}>
                    {o}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {filtered.map((e) => (
            <Card key={e.id}>
              <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>{e.name}</CardTitle>
                  <CardDescription>
                    Serial: {e.serialNumber || "—"} · Dept:{" "}
                    {e.department || "—"} · Owner: {e.owner || "—"}
                  </CardDescription>
                  <div className="text-xs text-muted-foreground">
                    Team: {e.team || "—"} · Default tech:{" "}
                    {e.defaultTechnician || "—"}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      e.maintenanceOpenCount > 0 ? "secondary" : "outline"
                    }
                  >
                    {e.maintenanceOpenCount} open
                  </Badge>
                  <Button size="sm" variant="outline">
                    Maintenance
                  </Button>
                </div>
              </CardHeader>
            </Card>
          ))}
          {filtered.length === 0 && (
            <div className="text-sm text-muted-foreground">
              No equipment found.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
