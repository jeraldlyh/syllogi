"use client";
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
  createMusicServerUserConfigMutation,
  deleteMusicServerUserConfigMutation,
  MusicServerProvider,
  MusicServerUserConfig,
  updateMusicServerUserConfigMutation,
  useMusicServerUserConfigs,
} from "@/hooks/useMusicServerUsers";
import { useSettings } from "@/hooks/useSettings";
import { useMusicServerUsers } from "@/hooks/useUsers";
import { capitaliseFirstLetter, cn } from "@/lib/utils";
import { Pencil, Plus, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { toast } from "sonner";
import useSWRMutation from "swr/mutation";
import { Text } from "../common/text";
import { formatErrorMessage } from "@/lib/errors";

interface FormState {
  provider: string;
  username: string;
  password: string;
  lastfm_username: string;
}

interface FormErrors {
  username?: string;
}

const DEFAULT_FORM: FormState = {
  provider: "",
  username: "",
  password: "",
  lastfm_username: "",
};

export const UsersSettings = () => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [userToDelete, setUserToDelete] =
    useState<MusicServerUserConfig | null>(null);

  const { data: settingsData } = useSettings();
  const { data: users } = useMusicServerUsers();

  const { data: savedUsers, mutate: fetchConfigs } =
    useMusicServerUserConfigs();
  const { trigger: createUser, isMutating: isCreating } = useSWRMutation(
    "/users/provider",
    createMusicServerUserConfigMutation,
  );
  const { trigger: updateUser, isMutating: isUpdating } = useSWRMutation(
    "/users/provider",
    updateMusicServerUserConfigMutation,
  );
  const { trigger: deleteUser } = useSWRMutation(
    "/users/provider",
    deleteMusicServerUserConfigMutation,
  );

  const handleAdd = () => {
    setEditingId(null);
    setForm({ ...DEFAULT_FORM });
    setErrors({});
    setDialogOpen(true);
  };

  const handleEdit = (userConfig: MusicServerUserConfig) => {
    setEditingId(userConfig.id);
    setForm({
      provider: userConfig.provider,
      username: userConfig.username,
      password: "",
      lastfm_username: userConfig.lastfm_username,
    });
    setErrors({});
    setDialogOpen(true);
  };

  const isFormValid = (): boolean => {
    const newErrors: FormErrors = {};
    if (!form.username) newErrors.username = "Required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async (): Promise<void> => {
    if (!isFormValid()) return;

    setDialogOpen(false);

    const toastId = toast.loading(
      editingId ? "Updating user…" : "Adding user…",
    );

    try {
      if (editingId) {
        const body: {
          id: string;
          username: string;
          provider: MusicServerProvider;
          password?: string;
          lastfm_username: string;
        } = {
          id: editingId,
          username: form.username,
          provider: form.provider as MusicServerProvider,
          lastfm_username: form.lastfm_username,
        };

        if (form.password) body.password = form.password;

        await updateUser(body);
        toast.success("User updated", { id: toastId });
      } else {
        const body: {
          username: string;
          provider: MusicServerProvider;
          password?: string;
          lastfm_username: string;
        } = {
          username: form.username,
          provider: form.provider as MusicServerProvider,
          lastfm_username: form.lastfm_username,
        };

        if (form.password) body.password = form.password;

        await createUser(body);
        toast.success("User created", { id: toastId });
      }
      await fetchConfigs();
    } catch (error) {
      toast.error(
        editingId ? "Failed to update user" : "Failed to create user",
        { id: toastId, description: formatErrorMessage(error) },
      );
    }
  };

  const handleDelete = async (id: string): Promise<void> => {
    setUserToDelete(null);
    const toastId = toast.loading("Deleting user…");

    try {
      await deleteUser(id);
      toast.success("User deleted", { id: toastId });
      await fetchConfigs();
    } catch (error) {
      toast.error("Failed to delete user", {
        id: toastId,
        description: formatErrorMessage(error),
      });
    }
  };

  const renderErrorMessage = (
    message: string | undefined,
  ): React.JSX.Element | undefined => {
    if (!message) return undefined;
    return <Text value={message} className="text-red-400 text-xs" />;
  };

  const renderUsers = (): React.JSX.Element => {
    if (!savedUsers || savedUsers.length === 0) {
      return (
        <p className="py-6 text-center text-sm text-muted-foreground">
          No users yet. Add one to get started.
        </p>
      );
    }

    return (
      <div className="overflow-x-auto rounded-md border border-border max-h-96">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent text-xs text-muted-foreground">
              <TableHead>Username</TableHead>
              <TableHead>Last.fm Username</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {savedUsers.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Text value={user.username} />
                </TableCell>
                <TableCell>
                  <Text value={user.lastfm_username} />
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={cn("text-xs font-medium", {
                      "border-sky-500/30 text-sky-400":
                        user.provider === "jellyfin",
                      "border-purple-500/30 text-purple-400":
                        user.provider === "navidrome",
                    })}
                  >
                    {capitaliseFirstLetter(user.provider)}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={() => handleEdit(user)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground"
                      onClick={() => setUserToDelete(user)}
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
            Users
          </CardTitle>
          <Button size="sm" onClick={handleAdd}>
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </CardHeader>
        <CardContent>{renderUsers()}</CardContent>
      </Card>
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md bg-card text-card-foreground">
          <DialogHeader>
            <DialogTitle className="text-foreground">
              {editingId ? "Edit User" : "Add User"}
            </DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="provider"
                className="flex justify-between items-center"
              >
                <Text muted value="Provider" />
              </Label>
              <Select
                value={form.provider}
                onValueChange={(value) =>
                  setForm((prev) => ({ ...prev, provider: value }))
                }
                disabled={!!editingId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {settingsData.musicProviders.map((provider) => (
                    <SelectItem key={provider} value={provider}>
                      {capitaliseFirstLetter(provider)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="username"
                className="flex justify-between items-center"
              >
                <Text muted value="Username" />
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
            {form.provider === "navidrome" && (
              <div className="flex flex-col gap-2">
                <Label
                  htmlFor="password"
                  className="flex justify-between items-center"
                >
                  <Text muted value="Password" />
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={form.password}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      password: e.target.value,
                    }))
                  }
                  placeholder={
                    editingId ? "Leave empty to keep current" : "Enter password"
                  }
                  className="mt-1"
                />
              </div>
            )}
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="lastfm_username"
                className="flex justify-between items-center"
              >
                <Text muted value="Last.fm Username" />
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
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={isCreating || isUpdating}>
              {editingId ? "Update" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AlertDialog
        open={!!userToDelete}
        onOpenChange={(open) => !open && setUserToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this user? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => userToDelete && handleDelete(userToDelete.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
