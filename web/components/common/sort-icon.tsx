import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

export type SortDirection = "asc" | "desc" | null;

interface IProps {
  column: string;
  sortColumn: string | null;
  sortDirection: SortDirection;
}

export const SortIcon = ({ column, sortColumn, sortDirection }: IProps) => {
  if (sortColumn !== column) {
    return <ArrowUpDown className="ml-1 h-3 w-3 opacity-40" />;
  }
  if (sortDirection === "asc") {
    return <ArrowUp className="ml-1 h-3 w-3" />;
  }
  return <ArrowDown className="ml-1 h-3 w-3" />;
};
