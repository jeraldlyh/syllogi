"use client";

import React, { useState } from "react";
import { Plus, Pencil, Trash2, Clock } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CRON_PRESETS, PROVIDERS } from "@/lib/types";
import { Playlist } from "@/hooks/usePlaylist";
import { capitaliseFirstLetter, cn } from "@/lib/utils";
import { Text } from "./common/text";

interface FormState {
  provider: (typeof PROVIDERS)[number]["value"];
  playlistId: string;
  playlistName: string;
  username: string;
  enabled: boolean;
  cronExpression: string;
  cronMode: "simple" | "custom";
}

interface FormErrors {
  playlistId?: string;
  playlistName?: string;
  username?: string;
  cronExpression?: string;
}

const DEFAULT_FORM: FormState = {
  provider: "spotify",
  playlistId: "",
  playlistName: "",
  username: "",
  enabled: true,
  cronExpression: "0 * * * *",
  cronMode: "simple",
};

export const Playlists = () => {
  const [playlists, setPlaylists] = useState<Playlist[]>([
    {
      id: "1",
      provider: "spotify",
      playlistId: "3cEYpjA9oz9GiPac4AsH4n",
      playlistName: "Today's Top Hits",
      username: "john_doe",
      enabled: true,
      cronExpression: "0 * * * *",
    },
  ]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [errors, setErrors] = useState<FormErrors>({});

  const handleAddPlaylist = () => {
    setEditingId(null);
    setForm(DEFAULT_FORM);
    setErrors({});
    setDialogOpen(true);
  };

  const handleEditPlaylist = (playlist: Playlist) => {
    setEditingId(playlist.id);
    const isPreset = CRON_PRESETS.some(
      (p) => p.value === playlist.cronExpression,
    );

    setForm({
      provider: playlist.provider,
      playlistId: playlist.playlistId,
      playlistName: playlist.playlistName,
      username: playlist.username,
      enabled: playlist.enabled,
      cronExpression: playlist.cronExpression,
      cronMode: isPreset ? "simple" : "custom",
    });
    setErrors({});
    setDialogOpen(true);
  };

  const isFormError = (): boolean => {
    const newErrors: FormErrors = {};
    if (!form.playlistId.trim()) newErrors.playlistId = "Required";
    if (!form.playlistName.trim()) newErrors.playlistName = "Required";
    if (!form.username) newErrors.username = "Required";
    if (!form.cronExpression.trim()) {
      newErrors.cronExpression = "Required";
    }

    const parts = form.cronExpression.trim().split(/\s+/);
    if (parts.length !== 5) {
      newErrors.cronExpression =
        "Must have exactly 5 fields (min hour dom mon dow)";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSavePlaylist = (): void => {
    if (!isFormError()) return;

    const { cronMode, ...mappingData } = form;

    if (editingId) {
      setPlaylists((prev) =>
        prev.map((playlist) =>
          playlist.id === editingId
            ? { ...playlist, ...mappingData }
            : playlist,
        ),
      );
      toast.success("Mapping updated");
    } else {
      setPlaylists((prev) => [
        ...prev,
        {
          ...mappingData,
          id: Date.now().toString(),
        },
      ]);
      toast.success("Mapping added");
    }
    setDialogOpen(false);
  };

  const handleDeletePlaylist = (id: string): void => {
    setPlaylists((prev) => prev.filter((playlist) => playlist.id !== id));
    toast.success("Mapping deleted");
  };

  const renderErrorMessage = (
    message: string | undefined,
  ): React.JSX.Element | undefined => {
    if (!message) return undefined;

    return <Text value={message} className="text-red-400 text-xs" />;
  };

  const renderPlaylists = (): React.JSX.Element => {
    if (playlists.length === 0) {
      return (
        <p className="py-6 text-center text-sm text-muted-foreground">
          No playlist yet. Add one to get started.
        </p>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead>Source</TableHead>
              <TableHead>Playlist</TableHead>
              <TableHead className="hidden sm:table-cell">User</TableHead>
              <TableHead className="hidden md:table-cell">Schedule</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {playlists.map((playlist) => (
              <TableRow key={playlist.id}>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={cn("text-xs font-medium", {
                      "border-green-500/30 text-green-400":
                        playlist.provider === "spotify",
                      "border-red-500/30 text-red-400":
                        playlist.provider === "youtube",
                    })}
                  >
                    {capitaliseFirstLetter(playlist.provider)}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Text value={playlist.playlistName} />
                  <Text
                    value={playlist.playlistId}
                    className="text-muted-foreground"
                    mono
                  />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Text
                    value={playlist.username}
                    className="text-muted-foreground"
                  />
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <Text
                      value={
                        CRON_PRESETS.find(
                          (cron) => cron.value === playlist.cronExpression,
                        )?.label ?? playlist.cronExpression
                      }
                    />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() => handleEditPlaylist(playlist)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => handleDeletePlaylist(playlist.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  };
  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium text-foreground">
            Playlist
          </CardTitle>
          <Button size="sm" onClick={handleAddPlaylist}>
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </CardHeader>
        <CardContent>{renderPlaylists()}</CardContent>
      </Card>
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md bg-card text-card-foreground">
          <DialogHeader>
            <DialogTitle className="text-foreground">
              {editingId ? "Edit Playlist" : "Add Playlist"}
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label className="text-xs text-muted-foreground">Provider</Label>
              <Select
                value={form.provider}
                onValueChange={(value) =>
                  setForm((prev) => ({
                    ...prev,
                    provider: value as (typeof PROVIDERS)[number]["value"],
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {PROVIDERS.map((provider) => (
                    <SelectItem key={provider.value} value={provider.value}>
                      {provider.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="playlistId"
                className="flex justify-between items-center"
              >
                <Text
                  value={`${capitaliseFirstLetter(form.provider)} Playlist ID`}
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.playlistId)}
              </Label>
              <Input
                id="playlistId"
                value={form.playlistId}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    playlistId: e.target.value,
                  }))
                }
                placeholder={
                  form.provider === "spotify"
                    ? "e.g. 3cEYpjA9oz9GiPac4AsH4n"
                    : "e.g. PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
                }
                className="font-mono text-sm"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="playlistName"
                className="flex justify-between items-center"
              >
                <Text
                  value="Playlist Name"
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.playlistName)}
              </Label>
              <Input
                id="playlistName"
                value={form.playlistName}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    playlistName: e.target.value,
                  }))
                }
                placeholder="e.g. Lo-Fi Beats"
                className="mt-1"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="username"
                className="flex justify-between items-center"
              >
                <Text
                  value="Username"
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.username)}
              </Label>
              <Select
                value={form.username}
                onValueChange={(val) =>
                  setForm((prev) => ({ ...prev, username: val }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select user" />
                </SelectTrigger>
                <SelectContent></SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label className="flex justify-between items-center">
                <Text
                  value="Sync Schedule"
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.cronExpression)}
              </Label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setForm((prev) => ({
                      ...prev,
                      cronMode: "simple",
                      cronExpression: CRON_PRESETS[0].value,
                    }))
                  }
                  className={cn(
                    "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    {
                      "bg-primary text-primary-foreground":
                        form.cronMode === "simple",
                      "bg-secondary text-secondary-foreground hover:bg-secondary/80":
                        form.cronMode !== "simple",
                    },
                  )}
                >
                  Simple
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setForm((prev) => ({
                      ...prev,
                      cronMode: "custom",
                    }))
                  }
                  className={cn(
                    "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    {
                      "bg-primary text-primary-foreground":
                        form.cronMode === "custom",
                      "bg-secondary text-secondary-foreground hover:bg-secondary/80":
                        form.cronMode !== "custom",
                    },
                  )}
                >
                  Custom
                </button>
              </div>
              {form.cronMode === "simple" ? (
                <Select
                  value={form.cronExpression}
                  onValueChange={(value) =>
                    setForm((prev) => ({ ...prev, cronExpression: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select schedule" />
                  </SelectTrigger>
                  <SelectContent>
                    {CRON_PRESETS.map((preset) => (
                      <SelectItem key={preset.value} value={preset.value}>
                        <span className="font-mono">{preset.label}</span>
                        <span className="ml-2 text-sm font-mono text-muted-foreground">
                          {preset.value}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div>
                  <Input
                    value={form.cronExpression}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        cronExpression: e.target.value,
                      }))
                    }
                    placeholder="*/15 * * * *"
                    className="font-mono text-sm"
                  />
                  <Text
                    value="Use standard cron format. For example, '0 * * * *' to sync every hour."
                    className="mt-1 text-xs text-muted-foreground"
                  />
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <Switch
                id="enableSync"
                checked={form.enabled}
                onCheckedChange={(checked) =>
                  setForm((prev) => ({ ...prev, enabled: checked }))
                }
              />
              <Label htmlFor="enableSync" className="text-sm text-foreground">
                Enable sync
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSavePlaylist}>
              {editingId ? "Update" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
