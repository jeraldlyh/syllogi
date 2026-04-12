"use client";

import React, { useState } from "react";
import { Plus, Pencil, Trash2, Clock, Play, Info } from "lucide-react";
import { toast } from "sonner";
import useSWRMutation from "swr/mutation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CRON_PRESETS, ErrorResponse, PROVIDERS } from "@/lib/types";
import {
  createPlaylistMutation,
  deletePlaylistMutation,
  Playlist,
  updatePlaylistMutation,
  usePlaylists,
} from "@/hooks/usePlaylist";
import { capitaliseFirstLetter, cn } from "@/lib/utils";
import { Text } from "./common/text";
import { useJellyfinUsers } from "@/hooks/useUsers";
import { api } from "@/lib/api";

interface FormState {
  provider: (typeof PROVIDERS)[number]["value"];
  playlist_id: string;
  playlist_name: string;
  username: string;
  enable_sync: boolean;
  enable_download: boolean;
  cron_expression: string;
  cron_mode: "simple" | "custom";
}

interface FormErrors {
  playlist_id?: string;
  playlist_name?: string;
  username?: string;
  cron_expression?: string;
}

const DEFAULT_FORM: FormState = {
  provider: "spotify",
  playlist_id: "",
  playlist_name: "",
  username: "",
  enable_sync: true,
  enable_download: true,
  cron_expression: "0 * * * *",
  cron_mode: "simple",
};

export const Playlists = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [playlistToSync, setPlaylistToSync] = useState<Playlist | null>(null);
  const [playlistToDelete, setPlaylistToDelete] = useState<Playlist | null>(
    null,
  );

  const { data: users } = useJellyfinUsers();
  const {
    data: playlists,
    isLoading,
    isError,
    mutate: fetchPlaylist,
  } = usePlaylists();
  const {
    trigger: createPlaylist,
    data: createPlaylistResponse,
    error: createPlaylistError,
    isMutating: isCreating,
  } = useSWRMutation("/playlist", createPlaylistMutation);
  const {
    trigger: updatePlaylist,
    data: updatePlaylistResponse,
    error: updatePlaylistError,
    isMutating: isUpdating,
  } = useSWRMutation("/playlist", updatePlaylistMutation);
  const {
    trigger: deletePlaylist,
    data: deletePlaylistResponse,
    error: deletePlaylistError,
    isMutating: isDeleting,
  } = useSWRMutation("/playlist", deletePlaylistMutation);

  const handleAddPlaylist = () => {
    setEditingId(null);
    setForm(DEFAULT_FORM);
    setErrors({});
    setDialogOpen(true);
  };

  const handleEditPlaylist = (playlist: Playlist) => {
    setEditingId(playlist.id);
    const isPreset = CRON_PRESETS.some(
      (p) => p.value === playlist.cron_expression,
    );

    setForm({
      ...playlist,
      cron_mode: isPreset ? "simple" : "custom",
    });
    setErrors({});
    setDialogOpen(true);
  };

  const isFormError = (): boolean => {
    const newErrors: FormErrors = {};
    if (!form.playlist_id.trim()) newErrors.playlist_id = "Required";
    if (!form.playlist_name.trim()) newErrors.playlist_name = "Required";
    if (!form.username) newErrors.username = "Required";
    if (!form.cron_expression.trim()) {
      newErrors.cron_expression = "Required";
    }

    const parts = form.cron_expression.trim().split(/\s+/);
    if (parts.length !== 5) {
      newErrors.cron_expression =
        "Must have exactly 5 fields (min hour dom mon dow)";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSavePlaylist = async (): Promise<void> => {
    if (!isFormError()) return;

    const { cron_mode, ...mappingData } = form;

    if (editingId) {
      await updatePlaylist({ id: editingId, ...mappingData });
      toast.success("Playlist updated");
    } else {
      await createPlaylist(mappingData);

      toast.success("Playlist created");
    }
    await fetchPlaylist();
    setDialogOpen(false);
  };

  const handleSyncPlaylist = async (playlist: Playlist): Promise<void> => {
    setPlaylistToSync(null);
    const response = await api({
      method: "POST",
      service: "sync",
      path: "",
      body: playlist,
    });

    if (response && response.statusCode !== 200) {
      const errorResponse = response.error as ErrorResponse;
      toast.error(errorResponse.name, {
        description: errorResponse.message,
      });
      return;
    }
    toast.success("Sync started", {
      description: "Running sync for the playlist...",
    });
  };

  const handleDeletePlaylist = async (id: string): Promise<void> => {
    setPlaylistToDelete(null);
    await deletePlaylist(id);
    toast.success("Playlist deleted");
  };

  const renderErrorMessage = (
    message: string | undefined,
  ): React.JSX.Element | undefined => {
    if (!message) return undefined;

    return <Text value={message} className="text-red-400 text-xs" />;
  };

  const renderPlaylists = (): React.JSX.Element => {
    if (!playlists || playlists.length === 0) {
      return (
        <p className="py-6 text-center text-sm text-muted-foreground">
          No playlist yet. Add one to get started.
        </p>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border max-h-96">
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
          <TableBody className="overflow-y-auto">
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
                  <Text value={playlist.playlist_name} />
                  <Text
                    value={playlist.playlist_id}
                    className="text-muted-foreground mt-0.5"
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
                          (cron) => cron.value === playlist.cron_expression,
                        )?.label ?? playlist.cron_expression
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
                      onClick={() => setPlaylistToSync(playlist)}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
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
                      onClick={() => setPlaylistToDelete(playlist)}
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
                htmlFor="playlist_id"
                className="flex justify-between items-center"
              >
                <Text
                  value={`${capitaliseFirstLetter(form.provider)} Playlist ID`}
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.playlist_id)}
              </Label>
              <Input
                id="playlist_id"
                value={form.playlist_id}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    playlist_id: e.target.value,
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
                htmlFor="playlist_name"
                className="flex justify-between items-center"
              >
                <Text
                  value="Playlist Name"
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.playlist_name)}
              </Label>
              <Input
                id="playlist_name"
                value={form.playlist_name}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    playlist_name: e.target.value,
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
                disabled={!users || users.length === 0}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select user" />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((user) => (
                    <SelectItem key={user.id} value={user.name}>
                      {user.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label className="flex justify-between items-center">
                <Text
                  value="Sync Schedule"
                  className="text-xs text-muted-foreground"
                />
                {renderErrorMessage(errors.cron_expression)}
              </Label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setForm((prev) => ({
                      ...prev,
                      cron_mode: "simple",
                      cron_expression: CRON_PRESETS[0].value,
                    }))
                  }
                  className={cn(
                    "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    {
                      "bg-primary text-primary-foreground":
                        form.cron_mode === "simple",
                      "bg-secondary text-secondary-foreground hover:bg-secondary/80":
                        form.cron_mode !== "simple",
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
                      cron_mode: "custom",
                    }))
                  }
                  className={cn(
                    "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    {
                      "bg-primary text-primary-foreground":
                        form.cron_mode === "custom",
                      "bg-secondary text-secondary-foreground hover:bg-secondary/80":
                        form.cron_mode !== "custom",
                    },
                  )}
                >
                  Custom
                </button>
              </div>
              {form.cron_mode === "simple" ? (
                <Select
                  value={form.cron_expression}
                  onValueChange={(value) =>
                    setForm((prev) => ({ ...prev, cron_expression: value }))
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
                    value={form.cron_expression}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        cron_expression: e.target.value,
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
                id="enable_sync"
                checked={form.enable_sync}
                onCheckedChange={(checked) =>
                  setForm((prev) => ({ ...prev, enable_sync: checked }))
                }
              />
              <Label htmlFor="enable_sync" className="text-sm text-foreground">
                Enable sync
              </Label>
            </div>
            <div className="flex items-center gap-3">
              <Switch
                id="enable_download"
                checked={form.enable_download}
                onCheckedChange={(checked) =>
                  setForm((prev) => ({ ...prev, enable_download: checked }))
                }
              />
              <Label
                htmlFor="enable_download"
                className="text-sm text-foreground"
              >
                Enable download
              </Label>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground cursor-help w-4 h-4 hover:bg-inherit hover:text-inherit"
                  >
                    <Info className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right" className="max-w-xs">
                  <p>
                    When enabled, missing tracks are automatically downloaded
                    via yt-dlp during sync and added to your Jellyfin library.
                  </p>
                </TooltipContent>
              </Tooltip>
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
      <AlertDialog
        open={!!playlistToSync}
        onOpenChange={(open) => !open && setPlaylistToSync(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Start Playlist Sync</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div>
                <p>
                  Are you sure you want to start syncing&nbsp;
                  <span className="font-bold">
                    {playlistToSync?.playlist_name}
                  </span>
                  ?
                </p>
                <p>
                  This will fetch the latest tracks and sync them to Jellyfin.
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                playlistToSync && handleSyncPlaylist(playlistToSync)
              }
              disabled={playlistToSync?.enable_sync === false}
            >
              Start Sync
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog
        open={!!playlistToDelete}
        onOpenChange={(open) => !open && setPlaylistToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Playlist</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this playlist? This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() =>
                playlistToDelete && handleDeletePlaylist(playlistToDelete.id)
              }
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
