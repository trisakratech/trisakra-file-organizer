import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from organizer import (
    VERSION as ENGINE_VERSION,
    CATEGORIES,
    scan_files,
    build_plan,
    organize_files as engine_organize_files,
    undo_last_operation as engine_undo_last_operation,
)

# ============================================================
# TRISAKRA FILE ORGANIZER
# GUI Version 1.4.0
# Simple • Private • Local
#
# IMPORTANT:
# - No command-line input is used.
# - organizer.py is the file-management engine.
# - This GUI handles all user interaction.
# ============================================================

APP_NAME = "TRISAKRA FILE ORGANIZER"
VERSION = "1.5.0"

DEFAULT_FOLDER = r"D:\Trisakra\TestFiles"
SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "trisakra_settings.json",
)

# Trisakra-style colours
TEAL = "#009688"
TEAL_DARK = "#00796B"
TEAL_LIGHT = "#E0F2F1"
TAB_BG = "#E6ECEB"
BORDER = "#CFD8DC"
MUTED = "#607D8B"
WHITE = "#FFFFFF"
PAGE_BG = "#F5F7F8"
TEXT = "#263238"
SUCCESS = "#2E7D32"
WARNING = "#F57C00"
ERROR = "#C62828"
HOVER = "#E8F5F3"


class TrisakraOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1250x760")
        self.root.minsize(1000, 650)
        self.root.configure(bg=PAGE_BG)

        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Ready. Choose a folder and scan it before organizing."
        )
        self.count_var = tk.StringVar(value="0 file(s)")

        self.files = []
        self.last_plan = []
        self.scanned_folder = None

        # Duplicate handling is deliberately safe by default.
        self.duplicate_action_var = tk.StringVar(value="Ignore duplicates")

        # GUI history remains separate from the old CLI history.
        self.history_name = "gui_history.json"

        self.setup_styles()
        self.build_ui()
        self.set_default_folder()

        self.root.after(100, self.root.focus_set)

    # --------------------------------------------------------
    # Styling
    # --------------------------------------------------------
    def setup_styles(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Trisakra.TNotebook",
            background=PAGE_BG,
            borderwidth=0,
        )

        style.configure(
            "Trisakra.TNotebook.Tab",
            font=("Segoe UI", 10),
            padding=(18, 8),
            background=TAB_BG,
            foreground=TEXT,
        )

        style.map(
            "Trisakra.TNotebook.Tab",
            background=[
                ("selected", WHITE),
                ("active", HOVER),
            ],
            foreground=[
                ("selected", TEXT),
            ],
        )

        style.configure(
            "Treeview",
            background=WHITE,
            foreground=TEXT,
            fieldbackground=WHITE,
            rowheight=30,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Treeview.Heading",
            background=TEAL,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            padding=(8, 8),
        )

        style.map(
            "Treeview",
            background=[("selected", TEAL_LIGHT)],
            foreground=[("selected", TEXT)],
        )

        style.configure(
            "Vertical.TScrollbar",
            troughcolor="#ECEFF1",
            background="#B0BEC5",
            arrowcolor=TEXT,
        )

    def make_button(self, parent, text, command, width=20):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=TEXT,
            activebackground=TEAL_LIGHT,
            activeforeground=TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            takefocus=0,
            cursor="hand2",
            width=width,
            height=2,
        )

        button.bind(
            "<Enter>",
            lambda event: button.configure(bg=HOVER),
        )
        button.bind(
            "<Leave>",
            lambda event: button.configure(bg=WHITE),
        )

        return button

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
    def build_ui(self):
        header = tk.Frame(self.root, bg=TEAL, height=118)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text=APP_NAME,
            bg=TEAL,
            fg=WHITE,
            font=("Segoe UI", 27, "bold"),
        )
        title.pack(pady=(25, 2))

        subtitle = tk.Label(
            header,
            text="Simple • Private • Local",
            bg=TEAL,
            fg=WHITE,
            font=("Segoe UI", 11),
        )
        subtitle.pack()

        main = tk.Frame(self.root, bg=PAGE_BG)
        main.pack(fill="both", expand=True, padx=28, pady=(16, 20))

        tk.Label(
            main,
            text="Folder to organize:",
            bg=PAGE_BG,
            fg=TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 7))

        folder_row = tk.Frame(main, bg=PAGE_BG)
        folder_row.pack(fill="x")

        self.folder_entry = tk.Entry(
            folder_row,
            textvariable=self.folder_var,
            font=("Segoe UI", 11),
            bg=WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
            insertbackground=TEXT,
        )
        self.folder_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=8,
        )

        browse = self.make_button(
            folder_row,
            "Browse",
            self.browse_folder,
            width=10,
        )
        browse.pack(side="left", padx=(10, 0), ipadx=12)

        button_row = tk.Frame(main, bg=PAGE_BG)
        button_row.pack(pady=(16, 18))

        scan_btn = self.make_button(
            button_row,
            "Scan & Preview",
            self.scan_folder,
        )
        scan_btn.grid(row=0, column=0, padx=6)

        organize_btn = self.make_button(
            button_row,
            "Organize Files",
            self.organize_files,
        )
        organize_btn.grid(row=0, column=1, padx=6)

        undo_btn = self.make_button(
            button_row,
            "Undo Last Operation",
            self.undo_last_operation,
        )
        undo_btn.grid(row=0, column=2, padx=6)

        duplicate_row = tk.Frame(main, bg=PAGE_BG)
        duplicate_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            duplicate_row,
            text="Duplicate handling:",
            bg=PAGE_BG,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(4, 8))

        self.duplicate_combo = ttk.Combobox(
            duplicate_row,
            textvariable=self.duplicate_action_var,
            values=("Ignore duplicates", "Move duplicates to Duplicates folder"),
            state="readonly",
            width=34,
        )
        self.duplicate_combo.pack(side="left")

        tk.Label(
            duplicate_row,
            text="Safe default: duplicates stay where they are.",
            bg=PAGE_BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=12)

        status_frame = tk.Frame(
            main,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        status_frame.pack(fill="x", pady=(0, 5))

        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        )
        status_label.pack(side="left", padx=14, pady=9)

        count_label = tk.Label(
            status_frame,
            textvariable=self.count_var,
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 10),
            anchor="e",
        )
        count_label.pack(side="right", padx=14, pady=9)

        notebook = ttk.Notebook(
            main,
            style="Trisakra.TNotebook",
        )
        notebook.pack(fill="both", expand=True)

        activity_tab = tk.Frame(notebook, bg=WHITE)
        preview_tab = tk.Frame(notebook, bg=WHITE)

        notebook.add(activity_tab, text="Activity")
        notebook.add(preview_tab, text="File Preview")

        activity_frame = tk.Frame(
            activity_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        activity_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.activity_text = tk.Text(
            activity_frame,
            bg=WHITE,
            fg=TEXT,
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            wrap="none",
            padx=12,
            pady=12,
            state="disabled",
        )
        self.activity_text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        activity_scroll = ttk.Scrollbar(
            activity_frame,
            orient="vertical",
            command=self.activity_text.yview,
            style="Vertical.TScrollbar",
        )
        activity_scroll.pack(side="right", fill="y")

        self.activity_text.configure(
            yscrollcommand=activity_scroll.set,
        )

        preview_frame = tk.Frame(
            preview_tab,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        preview_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("file", "type", "category", "status", "destination")

        self.tree = ttk.Treeview(
            preview_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("file", text="File")
        self.tree.heading("type", text="Type")
        self.tree.heading("category", text="Category")
        self.tree.heading("status", text="Status")
        self.tree.heading("destination", text="Destination")

        self.tree.column("file", width=520, anchor="w")
        self.tree.column("type", width=110, anchor="center")
        self.tree.column("category", width=200, anchor="w")
        self.tree.column("status", width=140, anchor="center")
        self.tree.column("destination", width=320, anchor="w")

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        tree_scroll = ttk.Scrollbar(
            preview_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar",
        )
        tree_scroll.pack(side="right", fill="y")

        self.tree.configure(
            yscrollcommand=tree_scroll.set,
        )

        footer = tk.Label(
            self.root,
            text="No ads • No cloud • No tracking • Your files stay on your computer",
            bg=PAGE_BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        )
        footer.pack(side="bottom", pady=(0, 7))

        self.log(
            f"{APP_NAME}\n"
            f"Version {VERSION}\n"
            f"{'=' * 55}\n"
            f"Ready. Choose a folder and scan it before organizing.\n"
        )

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------
    def load_saved_folder(self):
        """Load the last successfully used folder, falling back to the default."""
        try:
            if os.path.isfile(SETTINGS_FILE):
                import json
                with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)

                saved_folder = data.get("last_folder", "")
                if saved_folder and os.path.isdir(saved_folder):
                    self.folder_var.set(saved_folder)
                    return

        except Exception:
            # A damaged/missing settings file must never prevent the app from starting.
            pass

        if os.path.isdir(DEFAULT_FOLDER):
            self.folder_var.set(DEFAULT_FOLDER)

    def save_last_folder(self, folder):
        """Save the selected folder locally; no cloud/network access is used."""
        try:
            import json
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump({"last_folder": os.path.abspath(folder)}, file, indent=2)
        except Exception:
            # Folder memory is a convenience feature; failures must not affect organizing.
            pass

    def set_default_folder(self):
        # Backward-compatible method name; now loads the saved last-used folder.
        self.load_saved_folder()

    def log(self, message):
        self.activity_text.configure(state="normal")
        self.activity_text.insert("end", message.rstrip() + "\n")
        self.activity_text.see("end")
        self.activity_text.configure(state="disabled")

    def clear_log(self):
        self.activity_text.configure(state="normal")
        self.activity_text.delete("1.0", "end")
        self.activity_text.configure(state="disabled")

    def clear_preview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_tree_status(self, index, status):
        children = self.tree.get_children()

        if 0 <= index < len(children):
            item_id = children[index]
            values = list(self.tree.item(item_id, "values"))

            if values:
                values[3] = status
                self.tree.item(item_id, values=values)

    # --------------------------------------------------------
    # Browse
    # --------------------------------------------------------
    def browse_folder(self):
        selected = filedialog.askdirectory(
            title="Select folder to organize"
        )

        if selected:
            self.folder_var.set(selected)
            self.save_last_folder(selected)
            self.files = []
            self.last_plan = []
            self.scanned_folder = None
            self.clear_preview()
            self.count_var.set("0 file(s)")
            self.status_var.set(
                "Folder selected. Click Scan & Preview."
            )
            self.log(
                f"\nFolder selected:\n{selected}\n"
                f"Click Scan & Preview to inspect files."
            )

        self.root.after(10, self.root.focus_set)

    # --------------------------------------------------------
    # Scan
    # --------------------------------------------------------
    def scan_folder(self):
        folder = self.folder_var.get().strip()

        if not folder:
            messagebox.showwarning(
                APP_NAME,
                "Please choose a folder first.",
            )
            return

        folder = os.path.abspath(folder)

        if not os.path.isdir(folder):
            messagebox.showerror(
                APP_NAME,
                "The selected folder does not exist.",
            )
            return

        self.folder_var.set(folder)
        self.save_last_folder(folder)
        self.clear_preview()
        self.clear_log()

        self.files = []
        self.last_plan = []
        self.scanned_folder = folder

        self.log(
            f"{APP_NAME}\n"
            f"Version {VERSION}\n"
            f"{'=' * 55}\n"
            f"SCAN & PREVIEW\n"
            f"{'=' * 55}\n\n"
            f"Folder:\n{folder}\n\n"
            f"Scanning...\n"
        )

        try:
            self.files = scan_files(
                folder,
                self.history_name,
            )
        except Exception as exc:
            self.files = []
            self.scanned_folder = None
            messagebox.showerror(
                APP_NAME,
                f"Could not read the folder:\n\n{exc}",
            )
            return

        self.last_plan = build_plan(self.files)

        self.log(
            f"\n{'=' * 55}\n"
            f"PROPOSED ORGANIZATION\n"
            f"{'=' * 55}\n"
        )

        if not self.files:
            self.log("\nNo movable files were found.")
            self.status_var.set("No files found.")
            self.count_var.set("0 file(s)")
            self.root.after(10, self.root.focus_set)
            return

        for index, item in enumerate(self.last_plan):
            status = item.get("status", "Ready")
            if item.get("duplicate") and self.duplicate_action_var.get() == "Move duplicates to Duplicates folder":
                destination = f"Duplicates\\{item["name"]}"
            else:
                destination = f"{item["category"]}\\{item["name"]}"

            self.log(
                f"\n[ {item['category']} ]\n"
                f"    {item['name']}"
                + (f"\n    Status: {status}" if status != "Ready" else "")
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    item["name"],
                    item["extension"] if item["extension"] else "(none)",
                    item["category"],
                    status,
                destination,
                ),
            )

        duplicate_group_files = sum(
            1 for item in self.last_plan
            if item.get("duplicate_group_member")
        )
        duplicate_copies = sum(
            1 for item in self.last_plan
            if item.get("duplicate")
        )
        duplicate_groups = len({
            item.get("duplicate_group") for item in self.last_plan
            if item.get("duplicate_group")
        })
        other_count = sum(
            1 for item in self.last_plan
            if item.get("category") == "Other Files"
        )

        self.log(
            f"\n{'=' * 55}\n"
            f"FILES FOUND: {len(self.files)}\n"
            f"DUPLICATE GROUPS: {duplicate_groups}\n"
            f"DUPLICATE COPIES: {duplicate_copies}\n"
            f"DUPLICATE GROUP FILES: {duplicate_group_files}\n"
            f"OTHER FILES: {other_count}\n"
            f"{'=' * 55}\n\n"
            f"PREVIEW ONLY\n"
            f"No files have been moved or changed.\n"
        )

        self.status_var.set(
            f"Preview complete • {duplicate_copies} duplicate copy/copies"
            if duplicate_copies
            else "Preview complete"
        )
        self.count_var.set(f"{len(self.files)} file(s) found")
        self.root.after(10, self.root.focus_set)

    # --------------------------------------------------------
    # Organize
    # --------------------------------------------------------
    def organize_files(self):
        folder = self.folder_var.get().strip()

        if not folder or not os.path.isdir(folder):
            messagebox.showwarning(
                APP_NAME,
                "Please choose a valid folder first.",
            )
            return

        folder = os.path.abspath(folder)

        if self.scanned_folder != folder or not self.last_plan:
            messagebox.showwarning(
                APP_NAME,
                "Please click Scan & Preview first.",
            )
            return

        move_duplicates = (
            self.duplicate_action_var.get() == "Move duplicates to Duplicates folder"
        )

        for item in self.last_plan:
            if item.get("duplicate"):
                item["duplicate_action"] = "move" if move_duplicates else "ignore"

        duplicate_copies = sum(1 for item in self.last_plan if item.get("duplicate"))
        duplicate_note = (
            f"\n{duplicate_copies} duplicate copy/copies will be moved to the Duplicates folder."
            if move_duplicates and duplicate_copies
            else f"\n{duplicate_copies} duplicate copy/copies will be left in place."
            if duplicate_copies
            else ""
        )

        answer = messagebox.askyesno(
            APP_NAME,
            f"Organize {len(self.last_plan)} file(s)?\n\n"

            "Files will be moved into category folders.\n"
            "Existing files will NOT be overwritten.\n\n"
            "You can use Undo Last Operation afterward."
            + duplicate_note,
        )

        if not answer:
            self.log(
                "\nOrganization cancelled.\n"
                "No files were changed."
            )
            self.root.after(10, self.root.focus_set)
            return

        self.log(
            f"\n{'=' * 55}\n"
            f"ORGANIZING FILES\n"
            f"{'=' * 55}\n"
        )

        try:
            result = engine_organize_files(
                folder,
                self.last_plan,
                self.history_name,
            )
        except Exception as exc:
            messagebox.showerror(
                APP_NAME,
                f"Organization could not be completed:\n\n{exc}",
            )
            return

        moved = result["moved"]
        failed = result["failed"]
        created_folders = result["created_folders"]

        # Update table statuses in the same order as the preview.
        moved_by_source = {
            item["source"]: item for item in moved
        }
        failed_by_source = {
            item["source"]: item for item in failed
        }

        for index, item in enumerate(self.last_plan):
            source = item["source"]

            if source in moved_by_source:
                self.update_tree_status(index, "Moved")
                self.log(
                    f"Moved: {item['name']} -> {item['category']}"
                )
            elif item.get("duplicate") and item.get("duplicate_action") == "ignore":
                self.update_tree_status(index, "Ignored")
                self.log(
                    f"Ignored duplicate: {item['name']}"
                )
            elif source in failed_by_source:
                self.update_tree_status(index, "Skipped")
                self.log(
                    f"Skipped: {item['name']} -> "
                    f"{failed_by_source[source]['reason']}"
                )

        self.log(
            f"\n{'=' * 55}\n"
            f"ORGANIZATION COMPLETE\n"
            f"{'=' * 55}\n\n"
            f"Files moved : {len(moved)}\n"
            f"Files failed: {len(failed)}\n"
            f"Folders created: {len(created_folders)}\n"
        )

        if moved:
            self.status_var.set(
                f"Organization complete • {len(moved)} moved"
            )
        else:
            self.status_var.set("No files were moved.")

        ignored = sum(
            1 for item in self.last_plan
            if item.get("duplicate") and item.get("duplicate_action") == "ignore"
        )
        self.count_var.set(
            f"{len(moved)} moved • {ignored} ignored • {len(failed)} skipped/failed"
        )

        self.root.after(10, self.root.focus_set)

    # --------------------------------------------------------
    # Undo
    # --------------------------------------------------------
    def undo_last_operation(self):
        folder = self.folder_var.get().strip()

        if not folder or not os.path.isdir(folder):
            messagebox.showwarning(
                APP_NAME,
                "Please choose a valid folder first.",
            )
            return

        folder = os.path.abspath(folder)

        # Read history through the same backend used by organization.
        from organizer import load_history

        history = load_history(folder, self.history_name)

        if not history:
            messagebox.showinfo(
                APP_NAME,
                "No GUI organization operation was found to undo.",
            )
            return

        operation = history[-1]
        moved = operation.get("moved", [])

        if not moved:
            messagebox.showinfo(
                APP_NAME,
                "The last GUI operation contains no moved files.",
            )
            return

        answer = messagebox.askyesno(
            APP_NAME,
            f"Undo the last organization?\n\n"
            f"{len(moved)} file(s) will be restored.\n\n"
            "Files will not be overwritten.",
        )

        if not answer:
            self.log("\nUndo cancelled.")
            self.root.after(10, self.root.focus_set)
            return

        self.log(
            f"\n{'=' * 55}\n"
            f"UNDO LAST OPERATION\n"
            f"{'=' * 55}\n"
        )

        try:
            result = engine_undo_last_operation(
                folder,
                self.history_name,
            )
        except Exception as exc:
            messagebox.showerror(
                APP_NAME,
                f"Undo could not be completed:\n\n{exc}",
            )
            return

        restored = result["restored"]
        failed = result["failed"]
        empty_removed = result["empty_removed"]

        for record in restored:
            self.log(
                f"Restored: {os.path.basename(record['source'])}"
            )

        for item in failed:
            record = item["record"]
            self.log(
                f"Failed: {os.path.basename(record.get('source', 'file'))} "
                f"-> {item['reason']}"
            )

        for folder_path in empty_removed:
            self.log(
                f"Removed empty folder: "
                f"{os.path.basename(folder_path)}"
            )

        self.log(
            f"\n{'=' * 55}\n"
            f"UNDO COMPLETE\n"
            f"{'=' * 55}\n\n"
            f"Files restored: {len(restored)}\n"
            f"Files failed: {len(failed)}\n"
            f"Empty folders removed: {len(empty_removed)}\n"
        )

        self.status_var.set(
            f"Undo complete • {len(restored)} restored"
        )
        self.count_var.set(
            f"{len(restored)} restored • {len(failed)} failed"
        )

        # Clear the old preview because the folder has changed again.
        self.files = []
        self.last_plan = []
        self.scanned_folder = None
        self.clear_preview()

        self.root.after(10, self.root.focus_set)


def main():
    root = tk.Tk()
    TrisakraOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
