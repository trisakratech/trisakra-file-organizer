# TRISAKRA FILE ORGANIZER

**A simple, private, local Python desktop application to organize files and manage duplicates.**

TRISAKRA FILE ORGANIZER helps you organize files into categorized folders on your computer. It includes file preview, duplicate detection, duplicate management, and an undo feature.

## Features

* **Simple GUI:** Easy-to-use desktop interface built with Python and Tkinter.
* **Local file organization:** Organizes files directly on your computer.
* **Scan & Preview:** Review files and their proposed destinations before organizing.
* **Automatic categorization:** Sorts files into categories such as:

  * PDFs
  * Documents
  * Archives
  * Images
  * Videos
  * Text
  * Other Files
* **Duplicate detection:** Identifies duplicate files based on their content.
* **Duplicate management:** Ignore duplicates or move them to a separate `Duplicates` folder.
* **Searchable preview:** Search files in the preview list.
* **Undo:** Restore files from the last organization operation.
* **Folder memory:** Remembers the previously selected folder.
* **No automatic deletion:** Duplicate files are moved or left in place, not automatically deleted.

## Requirements

* Windows
* Python 3.x
* Tkinter (usually included with standard Python installations)

## Getting Started

1. Download or clone this repository.
2. Make sure Python 3 is installed.
3. Open a terminal in the project folder.
4. Run:

   ```bash
   python gui.py
   ```

The application window should open.

## How to Use

1. Select the folder you want to organize using **Browse**.
2. Click **Scan & Preview** to review the files and their proposed destinations.
3. Choose how duplicates should be handled.
4. Click **Organize Files** to start organizing.
5. Use **Undo Last Operation** if you need to reverse the most recent organization operation.

**Tip:** Review the preview carefully before organizing files. Consider testing with a sample folder first.

## Project Structure

```text
trisakra-file-organizer/
├── gui.py
└── organizer.py
```

* `gui.py` — Desktop user interface.
* `organizer.py` — File organization and related operations.

## Privacy

TRISAKRA FILE ORGANIZER is designed to work locally on your computer. It organizes files in the folders you select and does not require a cloud account to perform its core functions.

## Version

**Current source version: v1.5.1**

## About

Developed by **Trisakra Technologies**
**Technology Infrastructure Partner**
BUILD • SUPPORT • SECURE • RECOVER

GitHub: https://github.com/trisakratech

## Contributions

Suggestions, bug reports, and contributions are welcome. Please use the repository's Issues section to report problems or propose improvements.

## License

A license has not yet been selected for this project. Until a license is added, the source code is publicly viewable, but reuse and redistribution are not automatically permitted.
