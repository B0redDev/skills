# iPhone and iPad

The build and capture recipe below was verified with Xcode 27 on iOS 27 simulators. With impeccable installed, read its `reference/ios.md` too: it holds the conformance rules (safe areas, 44 pt targets, Dynamic Type, semantic colours, system navigation). This file adds what a *proposal* needs: where variants can differ, the stock vocabulary, and how to render.

## Contents

- What makes it look native
- Where variants can differ
- Stock vocabulary (SwiftUI)
- Motion and haptics
- Build and capture
- Tells that give a fake away

## What makes it look native

The system draws the navigation bar, the tab bar, the sheets and their materials. On current iOS these are glass layers floating over content that scrolls underneath, and their exact look changes with every release. You get all of it by using the stock containers and leaving them alone: don't set bar backgrounds, don't draw your own blur, don't pad content away from the bars (the system insets it). When a capture looks dated or flat, the cause is almost always a container that was styled by hand.

Brand shows through the tint (one colour, on interactive elements), the content cells, imagery, and at most one display typeface for a few large moments. Body text, labels and controls stay on the system font with system text styles (`.font(.body)`, never a fixed size).

## Where variants can differ

| Axis | Options that are all native |
| --- | --- |
| Top-level navigation | Tab bar (2–5 sections, with a search tab when search is central); a single stack with a toolbar; on iPad, `.tabViewStyle(.sidebarAdaptable)` or a `NavigationSplitView` |
| Secondary task | Push onto the stack; sheet with detents (`.medium` keeps the context visible); full-screen cover for immersion; popover on iPad; inline disclosure |
| Content shape | Inset grouped list (settings-shaped content); plain list (feeds, long collections); grid; one custom hero above a stock list |
| Primary action | Toolbar button; bottom bar; a prominent button pinned above the keyboard; swipe actions and context menus for per-row actions |
| Title treatment | Large title collapsing on scroll (top-level screens); inline title (detail screens) |
| Search and filter | `.searchable` in the bar; a search tab; scopes; a filter menu in the toolbar; filter chips in the content |

On iPad a variant is a different structure, not the phone layout made wider: sidebar or split view, popovers where the phone uses sheets, multi-column content.

## Stock vocabulary (SwiftUI)

Reach for these before drawing anything:

- Structure: `TabView { Tab("Today", systemImage: "sun.max") { … } }`, `Tab(role: .search)`, `NavigationStack`, `NavigationSplitView`, `.navigationTitle`, `.toolbar { ToolbarItem(placement:) }`, `.tabBarMinimizeBehavior(.onScrollDown)`.
- Lists and forms: `List`, `Form`, `Section("Header") { … } footer: { … }`, `LabeledContent`, `Label`, `Toggle`, `Picker` (menu, segmented, navigation-link styles), `Stepper`, `Slider`, `DatePicker`, `DisclosureGroup`, `.swipeActions`, `.contextMenu`, `.refreshable`, `.searchable`.
- Presentation: `.sheet` with `.presentationDetents([.medium, .large])`, `.fullScreenCover`, `.popover`, `.confirmationDialog` (destructive choices), `.alert`, `Menu`.
- States: `ContentUnavailableView` (empty and no-results), `ProgressView`, `.redacted(reason: .placeholder)` (loading skeletons).
- Custom content inside stock scaffolding: `.buttonStyle(.borderedProminent)`, `.glass` button style and `.glassEffect()` for a floating control over content (sparingly, never on content itself), `Gauge`, Swift Charts, `Color(.secondarySystemGroupedBackground)` and the other semantic `UIColor`s, `.foregroundStyle(.secondary)`, SF Symbols through `Image(systemName:)` and `Label`.

With `write-swift` installed, follow it for the Swift itself.

## Motion and haptics

Navigation pushes, sheets, popovers, menus and tab switches animate themselves; leave them alone. Custom motion, when it is part of the decision:

- Springs, not durations: `withAnimation(.snappy)` or `.smooth` for UI responding to a tap; `.spring(duration: 0.4, bounce: 0)` as an explicit critically damped default; bounce only after a gesture that carried momentum.
- Continuity between screens: `.navigationTransition(.zoom(sourceID:in:))` with `.matchedTransitionSource`, `matchedGeometryEffect`.
- Small state changes: `.contentTransition(.numericText())` for changing numbers, `.symbolEffect(.bounce, value:)` and symbol replace transitions for icons.
- Haptics on the commit, on the same frame: `.sensoryFeedback(.selection, trigger:)`, `.success`, `.impact`. Stock controls (`Toggle`, pickers) already have theirs.
- `@Environment(\.accessibilityReduceMotion)`: replace movement with a cross-fade.

Record a motion that matters with the `video` command below, and tell the user to try it with `run`: feel is judged by a finger, not by a clip.

## Build and capture

A standalone proposal is a directory of Swift files. They define one function, and `assets/apple/ProposalApp.swift` (compiled in automatically) calls it with the launch arguments:

```swift
// $dir/Proposal.swift
import SwiftUI

@MainActor @ViewBuilder func proposal(variant: String, state: String) -> some View {
    switch variant {
    case "b": TeamFirst(state: state)
    case "c": Timeline(state: state)
    default: GroupedSettings(state: state)
    }
}
```

```swift
// $dir/A.swift — one file per variant; sample data shared in $dir/Data.swift
struct GroupedSettings: View {
    let state: String                       // "default", "empty", "sheet", … whatever the decision needs
    @State private var showsPlans: Bool
    init(state: String) { self.state = state; _showsPlans = State(initialValue: state == "sheet") }
    var body: some View { … }
}
```

Images go in `$dir/Resources/` and load with `Image("name")`. A proposal that needs its own scene declares its own `@main` type, and the default entry point is left out.

```bash
render="<skill-dir>/scripts/apple-render.sh"
NAME="Matchday" "$render" ios "$dir" shot -o v1 a a@dark a:sheet b b@dark c c@dark   # prints one <figure> per capture
DEVICE="iPad Air 11-inch (M4)" "$render" ios "$dir" shot -o v1 a b c                  # a second device class
TEXT=accessibility-large "$render" ios "$dir" shot -o final a                         # Dynamic Type check
"$render" ios "$dir" video -o v1 b:sheet 4                                            # 4 s of the launch, as a <figure>
"$render" ios "$dir" run b                                                            # variant b in the simulator's window, to try
"$render" ios "$dir" stop                                                             # shut down what it booted
```

A spec is `variant[:state][@dark]`. The script compiles for the simulator without an Xcode project (a few seconds), boots the device if needed, pins the status bar to 9:41, and captures with the screen's own mask, so the PNG has the device's real corners. `DEVICE` takes a name from `xcrun simctl list devices available`; `TEXT` takes a content size category, from `extra-small` to `accessibility-extra-extra-extra-large` (`xcrun simctl ui` lists them). Compiler errors are printed as they are: fix the Swift and run again.

What it shows is the simulator's OS, which is the newest installed runtime. Lowering `IOS_TARGET` only changes which APIs compile; to see an older OS's look, capture on a device of that runtime (`xcrun simctl list runtimes`), and say in the notes which OS the captures show. If the app supports an OS older than the captures, say that the look there will differ and was not rendered.

For a video's motion to play, start it from the state: a `.task { try? await Task.sleep(for: .seconds(1)); withAnimation { … } }` on the variant when `state` asks for it.

## Tells that give a fake away

- A navigation bar, tab bar or back button drawn by hand; a title as a `Text` in the content instead of `.navigationTitle`.
- Coloured or opaque bar backgrounds; blur or "glass" built from opacity and shadows.
- Stacks of rounded shadowed cards where an inset grouped list belongs; cards inside cards.
- Fixed font sizes, raw hex colours for text and backgrounds, a non-SF icon set, emoji as icons.
- Custom switches, checkboxes, segmented controls, dropdowns that open web-style.
- A hamburger menu, a floating action button, a snackbar: another platform's idioms.
- Full-width buttons stacked at the bottom of a screen that is not a single-task flow; a hero illustration on a utility screen.
- Content laid out under the Dynamic Island or the home indicator; text that truncates in the default size.
