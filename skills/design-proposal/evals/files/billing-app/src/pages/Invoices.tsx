import { useState } from "react";
import { AppShell } from "../components/AppShell";
import { useInvoices } from "../data/invoices";

export function Invoices() {
  const invoices = useInvoices();
  const [selected, setSelected] = useState<string[]>([]);

  return (
    <AppShell title="Invoices" nav={["Overview", "Invoices", "Customers", "Payouts", "Settings"]}>
      <div className="flex items-center gap-3 border-b border-border px-6 py-3">
        <input className="h-9 w-72 rounded-md border border-border bg-card px-3 text-sm" placeholder="Search by customer or number" />
        <select className="h-9 rounded-md border border-border bg-card px-2 text-sm">
          <option>All statuses</option>
          <option>Overdue</option>
          <option>Paid</option>
          <option>Draft</option>
        </select>
        <button className="ml-auto h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground">New invoice</button>
      </div>

      {/* Bulk actions: this row appears on selection and pushes the whole table down. */}
      {selected.length > 0 && (
        <div className="flex items-center gap-2 border-b border-border bg-muted px-6 py-2 text-sm">
          <span className="font-medium">{selected.length} selected</span>
          <button className="rounded-md border border-border bg-card px-2 py-1">Mark as paid</button>
          <button className="rounded-md border border-border bg-card px-2 py-1">Send reminder</button>
          <button className="rounded-md border border-border bg-card px-2 py-1">Export CSV</button>
          <button className="rounded-md px-2 py-1 text-destructive">Void</button>
        </div>
      )}

      <table className="w-full text-sm">
        <thead className="text-left text-muted-foreground">
          <tr className="border-b border-border">
            <th className="w-10 px-6 py-2" />
            <th className="py-2">Number</th>
            <th>Customer</th>
            <th>Issued</th>
            <th>Due</th>
            <th>Status</th>
            <th className="px-6 text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.id} className="border-b border-border hover:bg-muted">
              <td className="px-6 py-2.5">
                <input
                  type="checkbox"
                  checked={selected.includes(inv.id)}
                  onChange={() => setSelected((s) => (s.includes(inv.id) ? s.filter((x) => x !== inv.id) : [...s, inv.id]))}
                />
              </td>
              <td className="font-mono">{inv.number}</td>
              <td>{inv.customer}</td>
              <td>{inv.issued}</td>
              <td>{inv.due}</td>
              <td>{inv.status}</td>
              <td className="px-6 text-right tabular-nums">{inv.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </AppShell>
  );
}
