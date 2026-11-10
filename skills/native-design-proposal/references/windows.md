# Windows

There is no bundled harness for Windows, and nothing here was run while this skill was written: a WinUI app builds and runs only on Windows. The look rules below hold for either route; the render recipe is a starting point to confirm on the first capture.

## Render routes

1. **A Windows machine you can reach with an interactive desktop** (a VM on this machine, a PC over remote desktop). Build and run the proposal there and capture its window there. A plain SSH session has no desktop, so a window started from it cannot be captured: the capture has to run inside the logged-in session.
2. **A Windows VM whose window is on this Mac's screen** (UTM, Parallels). Run the proposal inside it and capture the VM's window from the host with `scripts/mac-shot.swift` (see `macos.md`), then crop to the app's window.
3. **No Windows machine.** Say so before designing, and offer the fallback: the `design-proposal` skill, with the page labelled as an HTML approximation of Windows and built from the metrics below. Don't call it a native render.

## What makes it look native (WinUI 3, Fluent 2)

- **Window.** The app extends into the title bar: icon and title at the left, caption buttons at the right, drawn by the system. The window background is Mica (an opaque material tinted by the wallpaper); content sits on a lighter layer above it, in cards. Acrylic, the translucent material, is for transient surfaces only: flyouts, menus, context menus.
- **Navigation.** `NavigationView`: a left pane that collapses to icons and then to a button as the window narrows, or a top bar for a few peer sections. Its settings item is at the bottom. `BreadcrumbBar` for depth, `TabView` for documents.
- **Geometry.** A 4 epx grid. Controls are 32 epx tall; touch targets 40 × 40 epx where touch matters. Corner radius is 4 epx on controls and 8 epx on windows, dialogs and flyouts. Rounder than that reads as another platform.
- **Type.** Segoe UI Variable, on the type ramp: Caption 12, Body 14, Body Strong 14 semibold, Subtitle 20 semibold, Title 28 semibold, Title Large 40, Display 68. Use the named styles, not sizes.
- **Colour.** Theme resources (`{ThemeResource …}` brushes) and the user's accent colour, so light, dark and high-contrast themes all work. No raw colours for text and surfaces.
- **Icons.** Segoe Fluent Icons, 16 epx, one weight.
- **Controls.** `CommandBar`, `ContentDialog`, `Flyout` and `MenuFlyout`, `TeachingTip`, `InfoBar` (status that stays), `ToggleSwitch` with its On/Off label, `NumberBox`, `ComboBox`, `Expander`, `ListView`, `ItemsView`, `SplitView`. Settings pages are a column of settings cards and expanders, each with an icon, a title, a description and its control at the right.
- **Input.** Pointer and keyboard first: access keys, keyboard accelerators shown in menus and tooltips, right-click context menus, tooltips on icon buttons, visible focus rectangles. Touch and pen work too.
- **Motion.** The built-in theme transitions (entrance, drill-in, slide), connected animation between a list item and its detail, and the animation duration resources of the control library. Don't hand-pick timings.

## Where variants can differ

| Axis | Options that are all native |
| --- | --- |
| Navigation | Left `NavigationView` (many sections, hierarchy); top navigation (few peers); a single page with a `CommandBar`; tabs for documents |
| Secondary task | A new page with drill-in; `ContentDialog`; a flyout from the control; a side pane (`SplitView`); a separate window |
| Collection | `ListView`; a details table; a grid of cards; a tree |
| Commands | `CommandBar` at the top of the content; inline buttons; context menu and accelerators |
| Settings-shaped content | Settings cards in one scrolling page; grouped with expanders; split across navigation items |

## Build and capture

A proposal is a minimal WinUI 3 app (`dotnet new` with the Windows App SDK templates, or a debug-only window inside the existing solution) that reads `--variant` and `--state` from its command line and switches on them, one page per variant. In the interactive session:

```powershell
dotnet build -c Debug
Start-Process .\bin\...\Proposal.exe -ArgumentList '--variant','a','--state','default'
# Capture the app's window (Snipping Tool's window mode, Alt+PrtScn, or a script using Windows.Graphics.Capture).
```

Capture light and dark (Settings › Personalization › Colors, or set `RequestedTheme` from an argument, which is the reproducible way). Write the `<figure>` tags by hand, class `np-windows`; `width` is the capture's pixel width divided by the display scale (1.0 at 100%, 1.5 at 150%).

## Tells that give a fake away

- macOS or iOS habits: traffic lights, a centred title, large rounded corners, iOS switches, a bottom tab bar, sheets sliding up.
- A web layout: a hamburger that opens an overlay drawer on a wide window, a centred max-width column, a hero banner, custom scrollbars.
- A title bar the app doesn't extend into, with a second custom header under it.
- Acrylic or blur behind the main content; heavy drop shadows; flat pages with no Mica and no layering.
- No access keys, no accelerators, no context menus, no tooltips on icon buttons.
- Fonts other than Segoe UI Variable for the interface; sizes outside the ramp.
