"use client";

import { Pencil, Play, Plus, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import useSWRMutation from "swr/mutation";

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
import { Badge } from "@/components/ui/badge";
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
  createRecommendationMutation,
  deleteRecommendationMutation,
  generateRecommendationMutation,
  Recommendation,
  RecommendationStrategy,
  updateRecommendationMutation,
  useRecommendations,
} from "@/hooks/useRecommendation";
import { useJellyfinUsers } from "@/hooks/useUsers";
import { cn, convertSnakeCaseToTitleCase } from "@/lib/utils";

interface FormState {
  username: string;
  strategy: RecommendationStrategy;
  lastfm_username: string;
  requested_count: number;
}

interface FormErrors {
  username?: string;
  strategy?: string;
  lastfm_username?: string;
  requested_count?: string;
}

const DEFAULT_FORM: FormState = {
  username: "",
  strategy: "recent_tracks",
  lastfm_username: "",
  requested_count: 50,
};

const STRATEGIES: { label: string; value: RecommendationStrategy }[] = [
  { label: "Recent Tracks", value: "recent_tracks" },
  { label: "Top Tracks", value: "top_tracks" },
  { label: "Mixed", value: "mixed" },
];

export const Recommendations = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [recommendationToDelete, setRecommendationToDelete] =
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
    setEditingId(recommendation.id);
    setForm({
      username: recommendation.username,
      strategy: recommendation.strategy,
      lastfm_username: recommendation.lastfm_username,
      requested_count: recommendation.requested_count,
    });
    setErrors({});
    setDialogOpen(true);
  };

  const isFormError = (): boolean => {
    const newErrors: FormErrors = {};

    if (!form.username.trim()) {
      newErrors.username = "Required";
    }

    if (!form.lastfm_username.trim()) {
      newErrors.lastfm_username = "Required";
    }

    if (form.requested_count < 1) {
      newErrors.requested_count = "Must be an integer greater than 0";
    }

    if (form.requested_count > 50) {
      newErrors.requested_count = "Must be less than or equal to 50";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSaveRecommendation = async (): Promise<void> => {
    if (!isFormError()) return;

    const payload = {
      username: form.username,
      strategy: form.strategy,
      lastfm_username: form.lastfm_username,
      requested_count: form.requested_count,
    };

    if (editingId) {
      await updateRecommendation({ id: editingId, ...payload });
      toast.success("Recommendation updated");
    } else {
      await createRecommendation(payload);
      toast.success("Recommendation created");
    }

    await fetchRecommendations();
    setDialogOpen(false);
  };

  const handleGenerateRecommendation = async (
    recommendation: Recommendation,
  ): Promise<void> => {
    await generateRecommendation(recommendation);
    toast.success("Recommendation run started", {
      description: `Generating recommendations for ${recommendation.username}`,
    });
  };

  const handleDeleteRecommendation = async (id: string): Promise<void> => {
    setRecommendationToDelete(null);
    await deleteRecommendation(id);
    toast.success("Recommendation deleted");
    await fetchRecommendations();
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
              <TableHead>Jellyfin User</TableHead>
              <TableHead className="hidden sm:table-cell">
                Last.fm User
              </TableHead>
              <TableHead>Strategy</TableHead>
              <TableHead className="hidden md:table-cell">Requested</TableHead>
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
                  <Text
                    value={recommendation.lastfm_username}
                    className="text-muted-foreground"
                  />
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={cn("text-xs font-medium", {
                      "border-blue-500/30 text-blue-400":
                        recommendation.strategy === "recent_tracks",
                      "border-purple-500/30 text-purple-400":
                        recommendation.strategy === "top_tracks",
                    })}
                  >
                    {convertSnakeCaseToTitleCase(recommendation.strategy)}
                  </Badge>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <Text
                    value={String(recommendation.requested_count)}
                    className="text-muted-foreground"
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() =>
                        handleGenerateRecommendation(recommendation)
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
        <DialogContent className="max-w-md bg-card text-card-foreground">
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
                <Text
                  value="Jellyfin Username"
                  className="text-xs text-muted-foreground"
                />
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
                htmlFor="lastfm_username"
                className="flex justify-between items-center"
              >
                <Text
                  value="Last.fm Username"
                  className="text-xs text-muted-foreground"
                />
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
            <div className="flex flex-col gap-2">
              <Label className="text-xs text-muted-foreground">Strategy</Label>
              <Select
                value={form.strategy}
                onValueChange={(value) =>
                  setForm((prev) => ({
                    ...prev,
                    strategy: value as RecommendationStrategy,
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
                <Text
                  value="Requested Count"
                  className="text-xs text-muted-foreground"
                />
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
    </>
  );
};
