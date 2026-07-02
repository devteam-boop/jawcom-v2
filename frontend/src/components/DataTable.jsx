import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export default function DataTable({ columns, rows, onRowClick, emptyMessage = "No records", testId = "data-table" }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm" data-testid={testId}>
      <div className="overflow-x-auto scrollbar-thin">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              {columns.map((c) => (
                <TableHead
                  key={c.key}
                  className={cn(
                    "h-11 whitespace-nowrap text-[11px] font-semibold uppercase tracking-wider text-muted-foreground",
                    c.className
                  )}
                >
                  {c.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-32 text-center text-sm text-muted-foreground"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row, idx) => (
                <TableRow
                  key={row.id || idx}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    "border-border transition-colors",
                    onRowClick && "cursor-pointer hover:bg-secondary/50"
                  )}
                  data-testid={`row-${row.id || idx}`}
                >
                  {columns.map((c) => (
                    <TableCell key={c.key} className={cn("py-3 text-sm", c.cellClassName)}>
                      {c.render ? c.render(row) : row[c.key]}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
