from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import (
    CATEGORY_ORDER,
    HISTORY_FILE,
    FileRecord,
    MovePlan,
    execute_plan,
    find_duplicates,
    format_size,
    make_plan,
    scan_folder,
    undo_last_batch,
)

COLORS = {
    "bg": "#0B1020",
    "surface": "#121A2D",
    "surface2": "#18233A",
    "line": "#293650",
    "text": "#EAF0FF",
    "muted": "#93A2BF",
    "accent": "#7CE3C3",
    "accent_dark": "#153F3C",
    "blue": "#8DBBFF",
    "danger": "#FF8B8B",
    "white": "#FFFFFF",
}


class SmartOrganizerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Smart File Organizer")
        self.geometry("1260x790")
        self.minsize(980, 650)
        self.configure(bg=COLORS["bg"])
        self.folder: Path | None = None
        self.records: list[FileRecord] = []
        self.visible_records: list[FileRecord] = []
        self.status_var = tk.StringVar(value="Choose a folder to begin. Your files stay on this computer.")
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All categories")
        self._configure_styles()
        self._build_layout()
        self.search_var.trace_add("write", lambda *_: self._refresh_table())
        self.category_var.trace_add("write", lambda *_: self._refresh_table())

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["surface"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Arial", 10))
        style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=("Arial", 9))
        style.configure("Panel.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Arial", 10))
        style.configure("PanelMuted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=("Arial", 9))
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Arial", 23, "bold"))
        style.configure("Section.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Arial", 12, "bold"))
        style.configure("CardValue.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Arial", 20, "bold"))
        style.configure("TButton", font=("Arial", 10, "bold"), padding=(12, 9), background=COLORS["surface2"], foreground=COLORS["text"], borderwidth=0)
        style.map("TButton", background=[("active", "#263653"), ("disabled", COLORS["surface"])], foreground=[("disabled", "#56627A")])
        style.configure("Accent.TButton", background=COLORS["accent"], foreground="#081A1A", padding=(14, 10))
        style.map("Accent.TButton", background=[("active", "#A0F0D9")], foreground=[("active", "#081A1A")])
        style.configure("TEntry", fieldbackground=COLORS["surface2"], foreground=COLORS["text"], insertcolor=COLORS["text"], bordercolor=COLORS["line"], padding=8)
        style.configure("TCombobox", fieldbackground=COLORS["surface2"], background=COLORS["surface2"], foreground=COLORS["text"], arrowcolor=COLORS["text"], padding=7)
        style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface2"])], foreground=[("readonly", COLORS["text"])])
        style.configure("Treeview", background=COLORS["surface"], fieldbackground=COLORS["surface"], foreground=COLORS["text"], rowheight=34, borderwidth=0, font=("Arial", 10))
        style.configure("Treeview.Heading", background=COLORS["surface2"], foreground=COLORS["muted"], font=("Arial", 9, "bold"), relief="flat", padding=(8, 11))
        style.map("Treeview", background=[("selected", "#24414D")], foreground=[("selected", COLORS["text"])])
        style.configure("Vertical.TScrollbar", background=COLORS["surface2"], troughcolor=COLORS["surface"], bordercolor=COLORS["surface"])

    def _panel(self, parent: tk.Widget, **kwargs: object) -> tk.Frame:
        return tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["line"], highlightthickness=1, **kwargs)

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=COLORS["bg"], padx=24, pady=17)
        header.pack(fill="x")
        brand = tk.Frame(header, bg=COLORS["bg"])
        brand.pack(side="left")
        mark = tk.Label(brand, text="S", bg=COLORS["accent"], fg="#071A1A", font=("Arial", 16, "bold"), width=3, height=1, padx=4, pady=4)
        mark.pack(side="left", padx=(0, 12))
        name_col = tk.Frame(brand, bg=COLORS["bg"])
        name_col.pack(side="left")
        tk.Label(name_col, text="SMART FILE ORGANIZER", bg=COLORS["bg"], fg=COLORS["text"], font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(name_col, text="Private by design · Organized by rules", bg=COLORS["bg"], fg=COLORS["muted"], font=("Arial", 9)).pack(anchor="w", pady=(3, 0))
        tk.Label(header, text="V1.0.1  •  LOCAL DESKTOP", bg=COLORS["bg"], fg=COLORS["muted"], font=("Arial", 9, "bold")).pack(side="right", pady=(7, 0))
        tk.Frame(self, bg=COLORS["line"], height=1).pack(fill="x")

        body = tk.Frame(self, bg=COLORS["bg"], padx=20, pady=18)
        body.pack(fill="both", expand=True)
        self.sidebar = self._panel(body, width=210, padx=16, pady=16)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        workspace = tk.Frame(body, bg=COLORS["bg"])
        workspace.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(self.sidebar, text="WORKSPACE", bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 9, "bold")).pack(anchor="w", pady=(3, 15))
        ttk.Button(self.sidebar, text="▣   Choose a folder", style="Accent.TButton", command=self.choose_folder).pack(fill="x", pady=(0, 8))
        ttk.Button(self.sidebar, text="↻   Scan again", command=self.refresh_scan).pack(fill="x", pady=4)
        ttk.Button(self.sidebar, text="⌕   Find duplicates", command=self.show_duplicates).pack(fill="x", pady=4)
        ttk.Button(self.sidebar, text="↶   Undo last batch", command=self.undo).pack(fill="x", pady=4)
        tk.Frame(self.sidebar, bg=COLORS["line"], height=1).pack(fill="x", pady=18)
        tk.Label(self.sidebar, text="CURRENT FOLDER", bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 8))
        self.folder_label = tk.Label(self.sidebar, text="No folder selected", bg=COLORS["surface"], fg=COLORS["text"], font=("Arial", 10), justify="left", anchor="w", wraplength=165)
        self.folder_label.pack(fill="x")
        tk.Frame(self.sidebar, bg=COLORS["line"], height=1).pack(fill="x", pady=18)
        tk.Label(self.sidebar, text="SAFETY FIRST", bg=COLORS["surface"], fg=COLORS["accent"], font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 8))
        tk.Label(self.sidebar, text="Files are never uploaded. Nothing moves until you review and confirm the plan. Undo protects existing files from overwrite.", bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 9), justify="left", wraplength=168).pack(anchor="w")
        tk.Label(self.sidebar, text="SCANS TOP-LEVEL FILES ONLY", bg=COLORS["surface"], fg=COLORS["blue"], font=("Arial", 8, "bold"), wraplength=170, justify="left").pack(anchor="w", pady=(20, 0))

        title_row = tk.Frame(workspace, bg=COLORS["bg"])
        title_row.pack(fill="x", pady=(0, 15))
        title_block = tk.Frame(title_row, bg=COLORS["bg"])
        title_block.pack(side="left", fill="x", expand=True)
        ttk.Label(title_block, text="Your files, under control", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_block, text="Review your files, preview the moves, then organize with confidence.", style="Muted.TLabel").pack(anchor="w", pady=(5, 0))
        self.preview_button = ttk.Button(title_row, text="Preview organization  →", style="Accent.TButton", command=self.preview_organization, state="disabled")
        self.preview_button.pack(side="right", padx=(12, 0), pady=(4, 0))

        self.stats_row = tk.Frame(workspace, bg=COLORS["bg"])
        self.stats_row.pack(fill="x", pady=(0, 15))
        self.stat_values: dict[str, tk.Label] = {}
        for title, key, accent in (("FILES FOUND", "files", COLORS["text"]), ("NEED SORTING", "sorting", COLORS["accent"]), ("TOTAL SIZE", "size", COLORS["text"]), ("CATEGORIES", "categories", COLORS["text"])):
            card = self._panel(self.stats_row, padx=13, pady=12)
            card.pack(side="left", fill="both", expand=True, padx=(0, 9))
            tk.Label(card, text=title, bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 8, "bold")).pack(anchor="w")
            value = tk.Label(card, text="—", bg=COLORS["surface"], fg=accent, font=("Arial", 20, "bold"))
            value.pack(anchor="w", pady=(5, 0))
            self.stat_values[key] = value
        # Last card's trailing margin removed.
        children = self.stats_row.winfo_children()
        if children:
            children[-1].pack_configure(padx=(0, 0))

        browser = self._panel(workspace, padx=13, pady=12)
        browser.pack(fill="both", expand=True)
        browser_header = tk.Frame(browser, bg=COLORS["surface"])
        browser_header.pack(fill="x", pady=(0, 12))
        tk.Label(browser_header, text="File explorer", bg=COLORS["surface"], fg=COLORS["text"], font=("Arial", 13, "bold")).pack(side="left")
        self.count_label = tk.Label(browser_header, text="0 items", bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 9))
        self.count_label.pack(side="left", padx=(10, 0), pady=(2, 0))
        filters = tk.Frame(browser_header, bg=COLORS["surface"])
        filters.pack(side="right")
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var, width=23)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.insert(0, "")
        self.category_combo = ttk.Combobox(filters, textvariable=self.category_var, values=("All categories", *CATEGORY_ORDER), state="readonly", width=16)
        self.category_combo.pack(side="left")

        table_wrap = tk.Frame(browser, bg=COLORS["surface"])
        table_wrap.pack(fill="both", expand=True)
        columns = ("name", "category", "size", "modified")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="FILE NAME")
        self.tree.heading("category", text="SUGGESTED FOLDER")
        self.tree.heading("size", text="SIZE", anchor="e")
        self.tree.heading("modified", text="LAST MODIFIED")
        self.tree.column("name", width=280, minwidth=180, anchor="w")
        self.tree.column("category", width=150, minwidth=115, anchor="w")
        self.tree.column("size", width=90, minwidth=75, anchor="e")
        self.tree.column("modified", width=145, minwidth=125, anchor="w")
        yscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._show_selected_file)

        footer = tk.Frame(self, bg=COLORS["surface"], padx=20, pady=9)
        footer.pack(fill="x")
        tk.Label(footer, textvariable=self.status_var, bg=COLORS["surface"], fg=COLORS["muted"], font=("Arial", 9), anchor="w").pack(fill="x")
        self._update_stats()

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose a folder to organize", mustexist=True)
        if not selected:
            return
        self.folder = Path(selected).resolve()
        self.folder_label.configure(text=str(self.folder))
        self.refresh_scan()

    def refresh_scan(self) -> None:
        if self.folder is None:
            messagebox.showinfo("Choose a folder", "Select a folder first. The app scans files directly inside it only.")
            return
        try:
            self.records = scan_folder(self.folder)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not scan folder", str(exc))
            return
        self._refresh_table()
        self._update_stats()
        self.preview_button.configure(state="normal" if self.records else "disabled")
        self.status_var.set(f"Scanned {len(self.records)} files in {self.folder.name or str(self.folder)}. No files were changed.")

    def _refresh_table(self) -> None:
        if not hasattr(self, "tree"):
            return
        query = self.search_var.get().strip().casefold()
        category = self.category_var.get()
        self.visible_records = [r for r in self.records if (not query or query in r.path.name.casefold() or query in r.extension) and (category == "All categories" or r.category == category)]
        self.tree.delete(*self.tree.get_children())
        for record in self.visible_records:
            modified = datetime.fromtimestamp(record.modified).strftime("%b %d, %Y")
            self.tree.insert("", "end", iid=str(record.path), values=(record.path.name, record.category, format_size(record.size), modified))
        if hasattr(self, "count_label"):
            self.count_label.configure(text=f"{len(self.visible_records)} of {len(self.records)} items")
        self._update_stats()

    def _update_stats(self) -> None:
        count = len(self.records)
        pending = len(make_plan(self.records)) if count else 0
        total_size = sum(r.size for r in self.records)
        categories = len({r.category for r in self.records})
        self.stat_values["files"].configure(text=str(count))
        self.stat_values["sorting"].configure(text=str(pending))
        self.stat_values["size"].configure(text=format_size(total_size) if count else "0 B")
        self.stat_values["categories"].configure(text=str(categories))

    def _show_selected_file(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        record = next((r for r in self.records if str(r.path) == selected[0]), None)
        if record:
            messagebox.showinfo(record.path.name, f"Full path\n{record.path}\n\nSuggested folder: {record.category}\nSize: {format_size(record.size)}\nExtension: {record.extension}\n\nNo changes have been made yet.")

    def preview_organization(self) -> None:
        if self.folder is None:
            messagebox.showinfo("Choose a folder", "Choose a folder first.")
            return
        # Rescan immediately before planning to avoid stale file information.
        try:
            self.records = scan_folder(self.folder)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not scan folder", str(exc))
            return
        plan = make_plan(self.records)
        self._refresh_table()
        if not plan:
            messagebox.showinfo("Everything is sorted", "There are no top-level files that need to be moved.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Review organization plan")
        dialog.configure(bg=COLORS["bg"])
        dialog.geometry("800x540")
        dialog.minsize(650, 430)
        dialog.transient(self)
        dialog.grab_set()
        pad = tk.Frame(dialog, bg=COLORS["bg"], padx=20, pady=18)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text="Review before moving", bg=COLORS["bg"], fg=COLORS["text"], font=("Arial", 20, "bold")).pack(anchor="w")
        tk.Label(pad, text=f"{len(plan)} files will be moved into category folders inside:\n{self.folder}", bg=COLORS["bg"], fg=COLORS["muted"], justify="left", font=("Arial", 10)).pack(anchor="w", pady=(5, 14))
        wrapper = tk.Frame(pad, bg=COLORS["surface"])
        wrapper.pack(fill="both", expand=True)
        table = ttk.Treeview(wrapper, columns=("from", "category", "to"), show="headings")
        for col, label in (("from", "CURRENT FILE"), ("category", "CATEGORY"), ("to", "NEW LOCATION")):
            table.heading(col, text=label)
        table.column("from", width=235)
        table.column("category", width=120)
        table.column("to", width=330)
        scroll = ttk.Scrollbar(wrapper, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for i, item in enumerate(plan):
            table.insert("", "end", iid=str(i), values=(item.source.name, item.category, str(item.target.relative_to(self.folder))))
        actions = tk.Frame(pad, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(14, 0))
        tk.Label(actions, text="No files move until you confirm.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Arial", 9)).pack(side="left")
        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text=f"Move {len(plan)} files", style="Accent.TButton", command=lambda: self._confirm_execute(plan, dialog)).pack(side="right")

    def _confirm_execute(self, plan: list[MovePlan], dialog: tk.Toplevel) -> None:
        if not messagebox.askyesno("Confirm file moves", f"Move {len(plan)} files into category folders?\n\nThis changes their location. You can use Undo last batch to reverse a successful batch.", parent=dialog):
            return
        completed, errors = execute_plan(plan)
        dialog.destroy()
        self.refresh_scan()
        if completed and errors:
            self.status_var.set(f"Moved {len(completed)} files; {len(errors)} issue(s) need attention.")
            details = "\n".join(f"• {err}" for _item, err in errors[:8])
            messagebox.showwarning("Organization partly completed", f"Moved {len(completed)} files.\n\nIssues:\n{details}")
        elif completed:
            self.status_var.set(f"Successfully moved {len(completed)} files. Undo history saved in the selected folder.")
            messagebox.showinfo("Organization complete", f"Successfully moved {len(completed)} files.\n\nYou can reverse this batch with Undo last batch.")
        else:
            messagebox.showerror("Nothing was moved", "No files could be moved. Check file permissions and try again.")

    def show_duplicates(self) -> None:
        if self.folder is None:
            messagebox.showinfo("Choose a folder", "Select a folder first.")
            return
        try:
            records = scan_folder(self.folder)
            groups = find_duplicates(records)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not find duplicates", str(exc))
            return
        dialog = tk.Toplevel(self)
        dialog.title("Duplicate finder")
        dialog.configure(bg=COLORS["bg"])
        dialog.geometry("710x460")
        dialog.transient(self)
        pad = tk.Frame(dialog, bg=COLORS["bg"], padx=20, pady=18)
        pad.pack(fill="both", expand=True)
        tk.Label(pad, text="Duplicate finder", bg=COLORS["bg"], fg=COLORS["text"], font=("Arial", 20, "bold")).pack(anchor="w")
        tk.Label(pad, text="Files are compared by size and SHA-256 content hash. Nothing is deleted.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Arial", 10)).pack(anchor="w", pady=(5, 12))
        wrapper = tk.Frame(pad, bg=COLORS["surface"])
        wrapper.pack(fill="both", expand=True)
        listbox = tk.Listbox(wrapper, bg=COLORS["surface"], fg=COLORS["text"], selectbackground="#24414D", font=("Menlo", 10), borderwidth=0, highlightthickness=0)
        listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scroll = ttk.Scrollbar(wrapper, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        if not groups:
            listbox.insert("end", "No duplicate files found in the selected folder.")
        else:
            for index, group in enumerate(groups, 1):
                total = sum(path.stat().st_size for path in group if path.exists())
                listbox.insert("end", f"GROUP {index}  ·  {len(group)} identical files  ·  {format_size(total)} total")
                for path in group:
                    listbox.insert("end", f"    {path.name}")
                listbox.insert("end", "")
        ttk.Button(pad, text="Close", command=dialog.destroy).pack(anchor="e", pady=(12, 0))
        self.status_var.set(f"Duplicate scan complete: {len(groups)} duplicate group(s) found. Nothing was deleted.")

    def undo(self) -> None:
        if self.folder is None:
            messagebox.showinfo("Choose a folder", "Choose the same folder where files were organized.")
            return
        if not (self.folder / HISTORY_FILE).exists():
            messagebox.showinfo("No undo history", "No saved move history exists in the selected folder.")
            return
        if not messagebox.askyesno("Undo last batch", "Restore files to their original locations? Existing files will never be overwritten."):
            return
        count, errors = undo_last_batch(self.folder)
        self.refresh_scan()
        if errors:
            messagebox.showwarning("Undo partly completed", f"Restored {count} files.\n\n" + "\n".join(errors[:8]))
            self.status_var.set(f"Undo restored {count} files with {len(errors)} issue(s).")
        else:
            self.status_var.set(f"Undo complete. Restored {count} files to their original locations.")
            messagebox.showinfo("Undo complete", f"Restored {count} files to their original locations.")
