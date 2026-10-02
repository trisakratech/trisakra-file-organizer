from pathlib import Path
from datetime import datetime
import shutil
import json
import hashlib

# ============================================================
# TRISAKRA FILE ORGANIZER
# Backend / File Engine
# Version 1.3.0
# ============================================================

VERSION = "1.5.0"

CATEGORIES = {
    "Images": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff",
        ".webp", ".svg", ".ico", ".heic", ".heif"
    },
    "Videos": {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".3gp", ".mpeg", ".mpg"
    },
    "PDFs": {".pdf"},
    "Documents": {".doc", ".docx", ".odt", ".rtf", ".pages"},
    "Spreadsheets": {".xls", ".xlsx", ".ods", ".csv"},
    "Presentations": {".ppt", ".pptx", ".odp", ".key"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg", ".wma"},
    "Text": {".txt", ".md", ".log"},
}


def get_category(extension):
    extension = extension.lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return "Other Files"


def get_safe_destination(destination):
    """Return a non-conflicting destination without overwriting."""
    destination = Path(destination)

    if not destination.exists():
        return destination

    counter = 1
    while True:
        candidate = (
            destination.parent
            / f"{destination.stem} ({counter}){destination.suffix}"
        )
        if not candidate.exists():
            return candidate
        counter += 1


def get_history_file(folder_path, history_name="gui_history.json"):
    return Path(folder_path) / history_name


def load_history(folder_path, history_name="gui_history.json"):
    path = get_history_file(folder_path, history_name)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_history(folder_path, operation, history_name="gui_history.json"):
    path = get_history_file(folder_path, history_name)
    data = load_history(folder_path, history_name)

    data.append(operation)
    data = data[-20:]

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def remove_last_history(folder_path, history_name="gui_history.json"):
    path = get_history_file(folder_path, history_name)
    data = load_history(folder_path, history_name)

    if data:
        data.pop()

    if data:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def scan_files(folder_path, history_name="gui_history.json"):
    """
    Scan only files directly inside the selected folder.
    Existing category folders are never scanned.
    """
    folder = Path(folder_path).resolve()

    if not folder.exists():
        raise FileNotFoundError("The selected folder does not exist.")

    if not folder.is_dir():
        raise NotADirectoryError("The selected path is not a folder.")

    excluded = {
        history_name.lower(),
        "organizer_history.json",
        "organizer_log.txt",
    }

    files = []
    for item in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if item.is_file() and item.name.lower() not in excluded:
            files.append(item)

    return files


def get_file_hash(file_path, chunk_size=1024 * 1024):
    """Return a SHA-256 hash for a file without loading it all into memory."""
    digest = hashlib.sha256()

    with Path(file_path).open("rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def build_plan(files):
    """Build the preview plan and identify exact-content duplicate groups.

    The first file in each duplicate group is treated as the Original.
    Remaining files in that group are treated as Duplicate copies.
    No files are changed during planning.
    """
    file_hashes = {}
    hash_groups = {}

    for file in files:
        try:
            file_hash = get_file_hash(file)
        except Exception:
            file_hash = None

        file_hashes[str(file)] = file_hash

        if file_hash:
            hash_groups.setdefault(file_hash, []).append(file)

    plan = []
    duplicate_group_number = 0

    for file_hash, group in hash_groups.items():
        if len(group) > 1:
            duplicate_group_number += 1
            # Files are already sorted by name by scan_files().
            for index, file in enumerate(group):
                pass

    # Build a quick lookup for each file's duplicate-group role.
    roles = {}
    for file_hash, group in hash_groups.items():
        if len(group) <= 1:
            continue

        group_id = f"DUP-{list(hash_groups).index(file_hash) + 1:03d}"
        for index, file in enumerate(group):
            roles[str(file)] = {
                "group_id": group_id,
                "is_duplicate_group": True,
                "is_original": index == 0,
                "duplicate": index != 0,
                "status": "Original" if index == 0 else "Duplicate",
            }

    for file in files:
        file_hash = file_hashes.get(str(file))
        role = roles.get(str(file), {})

        plan.append({
            "source": str(file),
            "name": file.name,
            "extension": file.suffix.lower(),
            "category": get_category(file.suffix.lower()),
            "file_hash": file_hash,
            "duplicate": role.get("duplicate", False),
            "is_original": role.get("is_original", False),
            "duplicate_group": role.get("group_id"),
            "duplicate_group_member": role.get("is_duplicate_group", False),
            "status": role.get("status", "Ready"),
            "duplicate_action": "ignore",
        })

    return plan


def write_log(folder_path, message):
    log_file = Path(folder_path) / "organizer_log.txt"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(message.rstrip() + "\n")


def organize_files(
    folder_path,
    plan,
    history_name="gui_history.json",
):
    """
    Perform an already-previewed organization.
    This function NEVER asks for console input and NEVER overwrites files.

    Returns:
        {
            "moved": [...],
            "failed": [...],
            "created_folders": [...]
        }
    """
    folder = Path(folder_path).resolve()

    moved = []
    failed = []
    created_folders = []

    operation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    write_log(folder, "")
    write_log(folder, f"TRISAKRA FILE ORGANIZER v{VERSION}")
    write_log(folder, f"Operation ID: {operation_id}")
    write_log(folder, f"Operation started: {datetime.now().isoformat(timespec='seconds')}")
    write_log(folder, "-" * 60)

    for item in plan:
        source = Path(item["source"])
        name = item["name"]
        category = item["category"]
        duplicate_action = item.get("duplicate_action", "ignore")

        # Duplicate copies are safe-by-default: leave them where they are
        # unless the GUI explicitly requests moving them.
        if item.get("duplicate") and duplicate_action == "ignore":
            write_log(folder, f"IGNORED_DUPLICATE|{name}|{category}")
            continue

        destination_category = category
        if item.get("duplicate") and duplicate_action == "move":
            destination_category = "Duplicates"

        destination_folder = folder / destination_category
        destination = destination_folder / name

        try:
            if item.get("duplicate"):
                write_log(
                    folder,
                    f"DUPLICATE_ACTION|{name}|{duplicate_action}|{destination_category}"
                )

            if not source.exists():
                failed.append({
                    "source": str(source),
                    "destination": str(destination),
                    "reason": "Source file no longer exists",
                })
                continue

            folder_existed = destination_folder.exists()

            if not folder_existed:
                destination_folder.mkdir(parents=True, exist_ok=True)
                created_folders.append(str(destination_folder))

            # Never overwrite. If the exact name exists, create a safe
            # alternate name such as "file (1).pdf".
            safe_destination = get_safe_destination(destination)

            shutil.move(str(source), str(safe_destination))

            moved.append({
                "source": str(source),
                "destination": str(safe_destination),
                "original_name": name,
                "destination_name": safe_destination.name,
                "category": destination_category,
                "original_category": category,
                "duplicate": bool(item.get("duplicate")),
            })

            write_log(
                folder,
                f"MOVED|{name}|{destination_category}|{safe_destination.name}"
            )

        except Exception as exc:
            failed.append({
                "source": str(source),
                "destination": str(destination),
                "reason": str(exc),
            })

            write_log(
                folder,
                f"ERROR|{name}|{category}|{exc}"
            )

    operation = {
        "version": VERSION,
        "id": operation_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "folder": str(folder),
        "moved": moved,
        "failed": failed,
        "created_folders": sorted(set(created_folders)),
    }

    if moved:
        save_history(folder, operation, history_name)

    write_log(folder, "-" * 60)
    write_log(folder, f"Files moved: {len(moved)}")
    write_log(folder, f"Files failed: {len(failed)}")
    write_log(folder, f"Operation completed: {datetime.now().isoformat(timespec='seconds')}")

    return {
        "moved": moved,
        "failed": failed,
        "created_folders": sorted(set(created_folders)),
        "operation": operation,
    }


def undo_last_operation(folder_path, history_name="gui_history.json"):
    """
    Undo the latest GUI organization operation.

    Safety:
    - Never overwrites a file at its original location.
    - Stops individual restores that cannot be safely completed.
    - Removes only empty folders created by that operation.
    """
    folder = Path(folder_path).resolve()
    history = load_history(folder, history_name)

    if not history:
        return {
            "restored": [],
            "failed": [],
            "empty_removed": [],
            "operation": None,
        }

    operation = history[-1]
    moved = operation.get("moved", [])

    if not moved:
        return {
            "restored": [],
            "failed": [],
            "empty_removed": [],
            "operation": operation,
        }

    restored = []
    failed = []

    # Safety pre-check for every file.
    for record in moved:
        source = Path(record.get("source", ""))
        destination = Path(record.get("destination", ""))

        if not destination.exists():
            failed.append({
                "record": record,
                "reason": "Organized file is missing",
            })
            continue

        if source.exists():
            failed.append({
                "record": record,
                "reason": "Original location already contains a file",
            })

    # Restore only records that pass the safety check.
    failed_keys = {
        id(item["record"])
        for item in failed
    }

    for record in reversed(moved):
        if id(record) in failed_keys:
            continue

        source = Path(record["source"])
        destination = Path(record["destination"])

        try:
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))

            restored.append(record)

        except Exception as exc:
            failed.append({
                "record": record,
                "reason": str(exc),
            })

    empty_removed = []

    if not failed:
        for folder_string in reversed(operation.get("created_folders", [])):
            created_folder = Path(folder_string)

            try:
                if created_folder.is_dir() and not any(created_folder.iterdir()):
                    created_folder.rmdir()
                    empty_removed.append(str(created_folder))
            except OSError:
                pass

    if not failed:
        remove_last_history(folder, history_name)

    write_log(folder, "")
    write_log(folder, f"UNDO OPERATION: {operation.get('id', 'unknown')}")
    write_log(folder, f"Files restored: {len(restored)}")
    write_log(folder, f"Files failed: {len(failed)}")

    return {
        "restored": restored,
        "failed": failed,
        "empty_removed": empty_removed,
        "operation": operation,
    }
