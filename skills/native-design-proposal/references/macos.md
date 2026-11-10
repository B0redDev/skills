# Mac

The build and capture recipe below was verified with Xcode 27 on macOS 27. A Mac app is not a large iPad app: it is a resizable window driven by a pointer and a keyboard, on a screen that shows many things at once. Most of what makes a Mac design feel wrong is iOS habit.

## Contents

- What makes it look native
- Where variants can differ
- Stock vocabulary (SwiftUI)
- Motion
- Build and capture
- Tells that give a fake away

## What makes it look native

- **Window anatomy.** Sidebar (navigation), content, optional inspector (properties of the selection), under one unified toolbar. The system draws the title bar, the traffic lights, the sidebar material and the toolbar; a `NavigationSplitView` with `.toolbar` gets all of it. Don't draw a custom title bar or put a logo in it. (A toolkit that draws everything itself, like GPUI, uses its own title bar component for the same job: see `in-project.md`.)
- **Density.** Body text is 13 pt, rows are compact, controls are small. There are no 44 pt targets: the pointer is precise. iOS-sized paddings and controls are the fastest way to look ported. Let stock controls size themselves (`.controlSize` when a tighter or looser region is wanted).
- **The menu bar is the full command set.** Every command has a menu item, frequent ones a keyboard shortcut; the toolbar repeats the few most used, and context menus repeat what applies to the selection. A proposal names the menus and shortcuts in its notes even though the capture doesn't show the menu bar.
- **Selection is a first-class state.** Lists and tables have a selected row, keyboard navigation, multiple selection, double-click to open, right-click for the context menu. Show a row selected in the primary capture.
- **Windows resize.** Design a default size and a minimum size, and capture both for the approved variant. Columns collapse; content reflows; nothing clips.
- **Settings are their own window** (`Settings` scene, ⌘,), with toolbar tabs or a sidebar, a grouped `Form`, changes applied at once and no Save button.
- **Colour.** Semantic colours and the user's accent colour. Tint the app only when the brand requires it; a Mac app that overrides the accent everywhere looks foreign.

## Where variants can differ

| Axis | Options that are all native |
| --- | --- |
| Window structure | Two columns (sidebar + detail); three columns (sidebar + list + detail); one pane with a toolbar and tabs; a compact utility window; a menu bar extra |
| Detail and editing | In the detail column; an inspector on the right; a sheet on the window for a bounded task; a popover from the control; a separate window |
| Collection | `Table` with sortable columns (data to compare); `List` (items to pick); grid (visual items); outline (hierarchy) |
| Primary actions | Toolbar; a bottom bar under a list (`+`/`−`); inline in the content; menu bar and shortcuts only |
| Filtering | Sidebar sections; toolbar search field; scope bar; a segmented control in the toolbar |

## Stock vocabulary (SwiftUI)

- Structure: `NavigationSplitView { sidebar } content: { … } detail: { … }`, `.navigationSplitViewColumnWidth(min:ideal:)`, `.inspector(isPresented:) { … }` with `.inspectorColumnWidth`, `.navigationTitle` (the window title; without one it shows the app's name), `.navigationSubtitle`, `.toolbar { ToolbarItem { … } }`, `.searchable`.
- Collections: `List(selection:)` (in the sidebar it takes the sidebar style by itself), `Table(rows, selection:) { TableColumn("Team", value: \.name) }`, `OutlineGroup`, `LazyVGrid`.
- Forms: `Form { … }.formStyle(.grouped)`, `LabeledContent`, `Toggle` (let the form pick switch or checkbox), `Picker`, `Stepper`, `TextField`, `GroupBox`.
- Presentation: `.sheet`, `.popover`, `.alert`, `.confirmationDialog`, `Menu`, `.contextMenu`, `.help("…")` for tooltips, `.keyboardShortcut`.
- Scenes, in a proposal that declares its own `@main`: `WindowGroup`, `Settings { … }`, `MenuBarExtra("…", systemImage:) { … }.menuBarExtraStyle(.window)`, `.windowToolbarStyle(.unified)`, `.commands { CommandMenu("Match") { … } }`.

## Motion

A Mac app moves less than a phone app. Windows, sheets, popovers and menus animate themselves. Selection changes, sidebar switches and anything triggered from the keyboard are instant. Custom motion is rare and small (a disclosure, an inspector sliding in, a number changing with `.contentTransition(.numericText())`), on a critically damped spring. There are no haptics to design for.

## Build and capture

The code contract is the one in `ios.md` (a `proposal(variant:state:)` function, one file per variant), and the same directory can serve both platforms: put platform-specific variants behind `#if os(macOS)`.

```bash
render="<skill-dir>/scripts/apple-render.sh"
NAME="Matchday" "$render" mac "$dir" shot -o v1 a a@dark b:inspector c     # prints one <figure> per capture
SIZE=760x480 NAME="Matchday" "$render" mac "$dir" shot -o final a          # the minimum window size
NAME="Matchday" "$render" mac "$dir" run b                                 # leave the window open for the user
"$render" mac "$dir" stop                                                  # quit it
```

The script builds a real `.app`, opens it at `SIZE` (default `1100x720`, in points), and captures what the screen shows: the window with its real shadow and materials, and any sheet, popover or menu it has open, on a plain backdrop that keeps the rest of the desktop out of the picture. Two things to know:

- The capture needs the terminal to have Screen Recording permission (System Settings › Privacy & Security). If it fails, tell the user which app to allow; nothing else replaces it.
- Each capture brings the proposal's window to the front for a couple of seconds, on the user's own screen. Tell them before a batch.
- It is a capture of the screen, so another app's window lying over the proposal ends up in the picture. The helper warns when it sees one. Don't touch that window: give the proposal's window another position (another display works) or ask the user, and capture again.

With `SIZE` set, the size is part of the file name (`a-mac-760x480.png`), so the check at the minimum size doesn't overwrite the normal capture.

A capture is at the display's scale: on a non-Retina display it is 1x and will look soft when viewed on a Retina one. Say so if it applies.

**Other toolkits' windows** (GPUI, Flutter, Tauri, an existing AppKit app). With `APP=<executable>` the same commands launch that executable instead of building SwiftUI, as `<executable> --variant b --appearance dark [--state empty] --size 1100x720`, from a private copy kept in `$dir/.build`; `in-project.md` has the recipe. For anything the script can't launch, the capture helper works on any process: `swiftc -O "<skill-dir>/scripts/mac-shot.swift" -o "$dir/.build/mac-shot"`, then `"$dir/.build/mac-shot" <pid> out.png [light|dark]` prints the image's width in points for the `<figure>` tag (class `np-mac`). Its `light|dark` only picks the backdrop's shade; the app's appearance is the app's business.

## Tells that give a fake away

- iOS proportions: large titles, 44 pt rows, full-width buttons, big paddings, a bottom tab bar, bottom sheets.
- A custom title bar, a centred logo, hand-drawn traffic lights, a hamburger button.
- A centred, max-width column of cards in a large window, like a web page.
- A push-and-back stack as the only navigation where a sidebar and a detail belong.
- No selection state, hover-only actions with no menu or shortcut equivalent.
- A Save button in settings; settings shown inside the main window as a page.
- Accent colour overridden everywhere; raw hex backgrounds that ignore dark mode and the sidebar's material.
- Toggles, pickers and steppers redrawn in an iOS or web style.
