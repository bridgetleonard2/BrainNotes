# BrainNotes

A 3D brain notebook for keeping track of the regions you read about. Each node in MNI space records:

1. **ROI name**
2. **What it's implicated in** (tasks, functions)
3. **The paper** that reported it

You can look things up from the side panel: pick an ROI to see its tasks and papers, pick a task to highlight every region linked to it, or pick a paper to see the ROIs it reported. Every paper you add is written to a `BrainNotes.bib` file, ready to use in LaTeX or Zotero.

Everything runs locally on your computer. Your notes never leave your machine unless you choose to sync them yourself.

## Requirements

- **Python 3.8+**. Only the standard library is used, so there's nothing to `pip install`.
- A modern browser: Chrome, Edge, Firefox, or Safari 16.4+.

## Getting started

1. Download this repo: click **Use this template**, or **Code → Download ZIP**, or `git clone`.
2. *(Optional)* Choose where your notes are saved. Copy `config.example.json` to `config.json` and set `notes_dir`:
   ```json
   { "notes_dir": "~/Documents/BrainNotes-notes" }
   ```
   If you skip this step, notes go in a `notes/` folder inside BrainNotes.
3. Launch it:
   - **Windows:** double-click `BrainNotes.bat`.
   - **Mac:** double-click `BrainNotes.command`. The first time, macOS may block it. If so, right-click the file and choose **Open**, then confirm. If macOS offers to install developer tools to get `python3`, accept.
     - If double-clicking doesn't run it, open Terminal in the folder and run `chmod +x BrainNotes.command`.

The brain opens in your browser at `http://localhost:8765`. Keep the small terminal window open while you work, and close it when you're done.

> Opening `BrainNotes.html` directly doesn't work. It needs the launcher to load the brain and save your notes.

## Using it

- **Add a node:** click **+ Add node**, then either click the brain or type coordinates. You can also double-click the brain to start a node at that spot.
  - Each node has a **Left** and a **Right** coordinate row. Fill one side or both; a node with both shows a sphere in each hemisphere. Clicking the brain fills whichever side you clicked.
  - Clicks land on the cortical surface. For deep structures like the amygdala, type or nudge the coordinates.
- **Add a paper** from the node form, in one of three ways:
  - **DOI lookup:** fetches the BibTeX from doi.org (needs internet).
  - **Paste BibTeX:** keeps your own citation key.
  - **Manual:** fill in authors, title, year and journal.
- **Explore:**
  - The search box and the ROIs / Tasks / Papers tabs filter your notes.
  - Clicking a node in the brain shows its details.
  - Tasks and papers in the details are clickable, so you can jump between them.
- **View controls:**
  - L / R / Front / Back / Top / Bottom set the camera angle.
  - **Glass** changes how see-through the brain is.
  - **Export** downloads a backup of your notes.

Each ROI name gets its own pastel colour, and that colour stays the same over time. If several papers report different peaks for the same region, each peak is its own node, grouped under the shared ROI name.

Advanced: `server.py --notes DIR --port N` runs BrainNotes on a different notes folder or port, for example to keep a separate notebook.

## Your notes folder

The `notes_dir` folder contains:

| File | What it is |
|---|---|
| `notes.json` | All your nodes and papers (plain, readable JSON) |
| `BrainNotes.bib` | Generated from your papers on every save. Don't edit it by hand. Use **Edit BibTeX** in the app instead. |
| `notes.backup.json` | The previous version, kept as a safety net |

### Keeping your notes in git

The tool and your notes are separate on purpose. To version your notes, make the notes folder its own private repo:

```bash
cd ~/Documents/BrainNotes-notes
git init
echo "notes.backup.json" > .gitignore
git add . && git commit -m "My BrainNotes"
# create a private repo on GitHub, then:
git remote add origin https://github.com/<you>/BrainNotes-notes.git
git push -u origin main
```

### Updating BrainNotes

`git pull` in the BrainNotes folder updates the tool. Your notes and `config.json` are never touched.

## Files

```
BrainNotes.html        the app
server.py              tiny local server: saves notes, writes the .bib, looks up DOIs
BrainNotes.bat         Windows launcher
BrainNotes.command     Mac launcher
config.example.json    copy to config.json to choose your notes folder
assets/                brain mesh and 3D libraries (bundled so it works offline)
```

## Credits

- **Brain surface:** the MNI ICBM152 2009 template (© McConnell Brain Imaging Centre, Montreal Neurological Institute), as a mesh from the [NiiVue](https://github.com/niivue/niivue) demo images.
- **3D rendering:** [three.js](https://threejs.org) r160 and [three-mesh-bvh](https://github.com/gkjohnson/three-mesh-bvh), both MIT licensed.
