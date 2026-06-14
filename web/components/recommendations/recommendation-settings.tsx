"use client";
import { Text } from "@/components/common/text";
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
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BlendUser,
  createRecommendationMutation,
  deleteRecommendationMutation,
  generateRecommendationMutation,
  Recommendation,
  updateRecommendationMutation,
  useRecommendations,
} from "@/hooks/useRecommendation";
import { useJellyfinUsers } from "@/hooks/useUsers";
import { CRON_PRESETS } from "@/lib/types";
import { cn } from "@/lib/utils";
import { X, Pencil, Play, Plus, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import useSWRMutation from "swr/mutation";
import { RecommendationStrategyBadge } from "./recommendation-strategy-badge";
import { RecommendationStrategy } from "@/hooks/useRecommendationSessions";

interface FormState {
  username: string;
  strategy: RecommendationStrategy;
  lastfm_username: string;
  requested_count: number;
  cron_expression: string;
  cron_mode: "simple" | "custom";
  is_public: boolean;
  playlist_name: string;
  blend_users?: BlendUser[] | null;
}

interface FormErrors {
  username?: string;
  strategy?: string;
  lastfm_username?: string;
  requested_count?: string;
  cron_expression?: string;
  playlist_name?: string;
  blend_users?: string;
}

const DEFAULT_FORM: FormState = {
  username: "",
  strategy: "recent_tracks",
  lastfm_username: "",
  requested_count: 50,
  cron_expression: "0 * * * *",
  cron_mode: "simple",
  is_public: false,
  playlist_name: "",
  blend_users: null,
};

const STRATEGIES: { label: string; value: RecommendationStrategy }[] = [
  { label: "Recent Tracks", value: "recent_tracks" },
  { label: "Top Tracks", value: "top_tracks" },
  { label: "Mixed", value: "mixed" },
  { label: "Blend", value: "blend" },
];

export const Recommendations = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [recommendationToDelete, setRecommendationToDelete] =
    useState<Recommendation | null>(null);
  const [recommendationToGenerate, setRecommendationToGenerate] =
    useState<Recommendation | null>(null);

  const { data: users } = useJellyfinUsers();
  const {
    data: recommendations,
    isLoading,
    isError,
    mutate: fetchRecommendations,
  } = useRecommendations();

  const { trigger: createRecommendation, isMutating: isCreating } =
    useSWRMutation("/recommendation", createRecommendationMutation);
  const { trigger: updateRecommendation, isMutating: isUpdating } =
    useSWRMutation("/recommendation", updateRecommendationMutation);
  const { trigger: deleteRecommendation, isMutating: isDeleting } =
    useSWRMutation("/recommendation", deleteRecommendationMutation);
  const { trigger: generateRecommendation, isMutating: isGenerating } =
    useSWRMutation("/recommendation/generate", generateRecommendationMutation);

  const handleAddRecommendation = () => {
    setEditingId(null);
    setForm(DEFAULT_FORM);
    setErrors({});
    setDialogOpen(true);
  };

  const handleEditRecommendation = (recommendation: Recommendation) => {
    const isPreset = CRON_PRESETS.some(
      (p) => p.value === recommendation.cron_expression,
    );

    setEditingId(recommendation.id);
    setForm({
      username: recommendation.username,
      strategy: recommendation.strategy,
      lastfm_username: recommendation.lastfm_username,
      requested_count: recommendation.requested_count,
      cron_expression: recommendation.cron_expression,
      cron_mode:
        isPreset || !recommendation.cron_expression ? "simple" : "custom",
      is_public: recommendation.is_public,
      playlist_name: recommendation.playlist_name,
      blend_users: recommendation.blend_users,
    });
    setErrors({});
    setDialogOpen(true);
  };

  const isFormError = (): boolean => {
    const newErrors: FormErrors = {};

    if (!form.username.trim()) {
      newErrors.username = "Required";
    }

    if (form.strategy === "blend" && form.blend_users) {
      if (form.blend_users.length < 2) {
        newErrors.blend_users = "Select at least 2 users";
      }

      if (form.blend_users.some((user) => !user.lastfm_username.trim())) {
        newErrors.blend_users = "Enter a Last.fm username for each user";
      }
    }

    if (form.strategy !== "blend" && !form.lastfm_username.trim()) {
      newErrors.lastfm_username = "Required";
    }

    if (!form.playlist_name.trim()) {
      newErrors.playlist_name = "Required";
    }

    if (form.requested_count < 1) {
      newErrors.requested_count = "Must be an integer greater than 0";
    }

    if (form.requested_count > 50) {
      newErrors.requested_count = "Must be less than or equal to 50";
    }

    if (form.cron_expression.trim()) {
      const parts = form.cron_expression.trim().split(/\s+/);
      if (parts.length !== 5) {
        newErrors.cron_expression =
          "Must have exactly 5 fields (min hour dom mon dow)";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSaveRecommendation = async (): Promise<void> => {
    if (!isFormError()) return;

    const { cron_mode, ...formData } = form;
    const payload = {
      username: formData.username,
      strategy: formData.strategy,
      lastfm_username:
        formData.strategy === "blend" ? "" : formData.lastfm_username,
      requested_count: formData.requested_count,
      cron_expression: formData.cron_expression,
      is_public: formData.is_public,
      playlist_name: formData.playlist_name,
      blend_users: formData.strategy === "blend" ? formData.blend_users : null,
    };

    setDialogOpen(false);

    const toastId = toast.loading(
      editingId ? "Updating recommendation..." : "Creating recommendation...",
    );

    try {
      if (editingId) {
        await updateRecommendation({ id: editingId, ...payload });
        toast.success("Recommendation updated", { id: toastId });
      } else {
        await createRecommendation(payload);
        toast.success("Recommendation created", { id: toastId });
      }
      await fetchRecommendations();
    } catch {
      toast.error(
        editingId
          ? "Failed to update recommendation"
          : "Failed to create recommendation",
        { id: toastId },
      );
    }
  };

  const handleGenerateRecommendation = async (
    recommendation: Recommendation,
  ): Promise<void> => {
    setRecommendationToGenerate(null);
    const toastId = toast.loading("Starting recommendation generation...");

    try {
      await generateRecommendation(recommendation);
      toast.success("Recommendation run started", {
        description: `Generating recommendations for ${recommendation.username}`,
        id: toastId,
      });
    } catch {
      toast.error("Failed to start recommendation generation", {
        id: toastId,
      });
    }
  };

  const handleDeleteRecommendation = async (id: string): Promise<void> => {
    setRecommendationToDelete(null);
    const toastId = toast.loading("Deleting recommendation…");

    try {
      await deleteRecommendation(id);
      toast.success("Recommendation deleted", { id: toastId });
      await fetchRecommendations();
    } catch {
      toast.error("Failed to delete recommendation", { id: toastId });
    }
  };

  const renderErrorMessage = (
    message: string | undefined,
  ): React.JSX.Element | undefined => {
    if (!message) return undefined;

    return <Text value={message} className="text-red-400 text-xs" />;
  };

  const renderTable = (): React.JSX.Element => {
    if (isError) {
      return (
        <div className="py-6 text-center text-sm text-red-400">
          Failed to load recommendations.
        </div>
      );
    }

    if (isLoading) {
      return (
        <div className="py-6 text-center text-sm text-muted-foreground">
          Loading recommendations...
        </div>
      );
    }

    if (!recommendations || recommendations.length === 0) {
      return (
        <p className="py-6 text-center text-sm text-muted-foreground">
          No recommendations yet. Add one to get started.
        </p>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border max-h-96">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead className="text-nowrap">Jellyfin User</TableHead>
              <TableHead className="hidden sm:table-cell">Playlist</TableHead>
              <TableHead>Strategy</TableHead>
              <TableHead className="hidden md:table-cell">Requested</TableHead>
              <TableHead className="hidden md:table-cell">Schedule</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {recommendations.map((recommendation) => (
              <TableRow key={recommendation.id}>
                <TableCell>
                  <Text value={recommendation.username} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Text muted value={recommendation.playlist_name} />
                </TableCell>
                <TableCell>
                  <RecommendationStrategyBadge
                    strategy={recommendation.strategy}
                  />
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <Text muted value={String(recommendation.requested_count)} />
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  {recommendation.cron_expression ? (
                    <Text
                      muted
                      value={
                        CRON_PRESETS.find(
                          (cron) =>
                            cron.value === recommendation.cron_expression,
                        )?.label ?? recommendation.cron_expression
                      }
                    />
                  ) : (
                    <Text muted value="Manual" />
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() =>
                        setRecommendationToGenerate(recommendation)
                      }
                      disabled={isGenerating}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() => handleEditRecommendation(recommendation)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => setRecommendationToDelete(recommendation)}
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

  const renderBlendUserChips = (): React.JSX.Element => {
    if (!users || users.length === 0) {
      return (
        <Text
          muted
          className="text-xs py-2 text-center w-full"
          value="No users available"
        />
      );
    }

    return (
      <div className="flex flex-wrap gap-1.5">
        {users.map((user) => {
          const isSelected =
            (form.blend_users ?? []).find((u) => u.name === user.name) !==
            undefined;
          return (
            <button
              key={user.id}
              type="button"
              onClick={() =>
                setForm((prev) => ({
                  ...prev,
                  blend_users: isSelected
                    ? (prev.blend_users ?? []).filter(
                        (u) => u.name !== user.name,
                      )
                    : [
                        ...(prev.blend_users ?? []),
                        {
                          name: user.name,
                          lastfm_username: "",
                        },
                      ],
                }))
              }
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium select-none cursor-pointer transition-colors duration-150",
                isSelected
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80",
              )}
            >
              {user.name}
              {isSelected && <X className="h-3 w-3" />}
            </button>
          );
        })}
      </div>
    );
  };

  const renderBlendUserInputs = (): React.JSX.Element => {
    if (!form.blend_users || form.strategy !== "blend" || !form.blend_users)
      return <></>;

    return (
      <div className="flex flex-col gap-2 border-t border-border pt-2 mt-1">
        {form.blend_users.map((user) => (
          <div key={user.name} className="flex items-center gap-2 text-sm">
            <span className="text-foreground font-medium whitespace-nowrap min-w-[80px]">
              {user.name}
            </span>
            <Input
              value={user.lastfm_username}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  blend_users: (prev.blend_users ?? []).map((new_user) =>
                    new_user.name === user.name
                      ? { ...new_user, lastfm_username: e.target.value }
                      : new_user,
                  ),
                }))
              }
              placeholder="Last.fm username"
              className="h-7 text-xs"
            />
          </div>
        ))}
      </div>
    );
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-medium text-foreground">
            Settings
          </CardTitle>
          <Button size="sm" onClick={handleAddRecommendation}>
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </CardHeader>
        <CardContent>{renderTable()}</CardContent>
      </Card>
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg bg-card text-card-foreground">
          <DialogHeader>
            <DialogTitle className="text-foreground">
              {editingId ? "Edit Recommendation" : "Add Recommendation"}
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="username"
                className="flex justify-between items-center"
              >
                <Text muted value="Jellyfin Username" />
                {renderErrorMessage(errors.username)}
              </Label>
              <Select
                value={form.username}
                onValueChange={(value) =>
                  setForm((prev) => ({ ...prev, username: value }))
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
              <Label
                htmlFor="playlist_name"
                className="flex justify-between items-center"
              >
                <Text muted value="Playlist Name" />
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
                placeholder="e.g. Daily Recommendations"
              />
            </div>
            {form.strategy === "blend" ? (
              <div className="flex flex-col gap-2">
                <Label className="flex justify-between items-center">
                  <Text muted value="Blend Users" />
                  {renderErrorMessage(errors.blend_users)}
                </Label>
                {renderBlendUserChips()}
                {renderBlendUserInputs()}
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <Label
                  htmlFor="lastfm_username"
                  className="flex justify-between items-center"
                >
                  <Text muted value="Last.fm Username" />
                  {renderErrorMessage(errors.lastfm_username)}
                </Label>
                <Input
                  id="lastfm_username"
                  value={form.lastfm_username}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      lastfm_username: e.target.value,
                    }))
                  }
                  placeholder="e.g. john_doe"
                />
              </div>
            )}
            <div className="flex flex-col gap-2">
              <Label className="text-xs text-muted-foreground">Strategy</Label>
              <Select
                value={form.strategy}
                onValueChange={(value) =>
                  setForm((prev) => ({
                    ...prev,
                    strategy: value as RecommendationStrategy,
                    is_public: value === "blend" ? true : false,
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent>
                  {STRATEGIES.map((strategy) => (
                    <SelectItem key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="requested_count"
                className="flex justify-between items-center"
              >
                <Text muted value="Requested Count" />
                {renderErrorMessage(errors.requested_count)}
              </Label>
              <Input
                id="requested_count"
                type="number"
                min={1}
                max={50}
                step={1}
                value={form.requested_count}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    requested_count: Number(e.target.value),
                  }))
                }
                placeholder="e.g. 50"
              />
            </div>
            {form.strategy !== "blend" && (
              <div className="flex flex-col gap-2">
                <Label className="text-xs text-muted-foreground">
                  Visibility
                </Label>
                <Select
                  value={form.is_public ? "true" : "false"}
                  onValueChange={(value) =>
                    setForm((prev) => ({
                      ...prev,
                      is_public: value === "true",
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select visibility" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">Private</SelectItem>
                    <SelectItem value="true">Public</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="flex flex-col gap-2">
              <Label className="flex justify-between items-center">
                <Text muted value="Schedule" />
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
                    muted
                    className="mt-1"
                    value="Use standard cron format. For example, '0 0 * * *' to generate daily."
                  />
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveRecommendation}
              disabled={isCreating || isUpdating}
            >
              {editingId ? "Update" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog
        open={recommendationToDelete !== null}
        onOpenChange={(open) => !open && setRecommendationToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete recommendation?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will remove the recommendation
              configuration for&nbsp;
              <span className="font-medium">
                {recommendationToDelete?.username}
              </span>
              .
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() =>
                recommendationToDelete &&
                handleDeleteRecommendation(recommendationToDelete.id)
              }
              disabled={isDeleting}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <AlertDialog
        open={!!recommendationToGenerate}
        onOpenChange={(open) => !open && setRecommendationToGenerate(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Start Recommendation Generation</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div>
                <p>
                  Are you sure you want to start generating recommendations
                  for&nbsp;
                  <span className="font-medium">
                    {recommendationToGenerate?.username}
                  </span>
                  ?
                </p>
                <br />
                <p>
                  This will fetch tracks from Last.fm and add them to Jellyfin.
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                recommendationToGenerate &&
                handleGenerateRecommendation(recommendationToGenerate)
              }
              disabled={isGenerating}
            >
              Start Generation
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
