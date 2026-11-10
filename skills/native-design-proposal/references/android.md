# Android

There is no bundled harness for Android, and the commands below come from the platform's documentation: they were not run while this skill was written. Treat them as the starting point and confirm each on the first capture. With impeccable installed, read its `reference/android.md` too: it holds the conformance rules (Material 3 navigation by window size, system Back, edge-to-edge insets, 48 dp targets, the type scale, colour roles). This file adds where variants can differ and how to render.

## What makes it look native

Material 3 is the rulebook, and the app is themed *through* it, not around it: a colour scheme of roles (dynamic colour from the wallpaper on Android 12+, with a static brand scheme as fallback), the type scale, the shape scale, the motion scheme. Components come from `androidx.compose.material3` unstyled; the theme carries the brand. The system draws the status bar and the gesture bar, and the app draws behind both (edge-to-edge is the default on current Android), with `Scaffold` handing the insets to the content.

Structure follows the window, not the device: navigation bar on compact width, navigation rail on medium, drawer or permanent rail on expanded. `NavigationSuiteScaffold` switches by itself.

## Where variants can differ

| Axis | Options that are all native |
| --- | --- |
| Top-level navigation | Navigation bar (3–5 destinations); navigation drawer (many destinations); a single screen with a top app bar; rail on larger windows |
| Top app bar | Small; centre-aligned; medium or large, collapsing on scroll; a search bar in its place |
| Secondary task | A new screen; modal bottom sheet; full-screen dialog (creation flows on phones); dialog (a decision that must interrupt); side sheet on large windows |
| Content shape | List of `ListItem`s; cards (elevated, filled, outlined) when items are self-contained objects; grid; list-detail pane on large windows |
| Primary action | FAB or extended FAB (one, the screen's main action); top app bar actions; bottom app bar; a button in the content |
| Filtering | Filter chips under the app bar; search bar with suggestions; a menu in the app bar; tabs |

## Stock vocabulary (Compose Material 3)

`Scaffold`, `NavigationSuiteScaffold`, `TopAppBar` / `CenterAlignedTopAppBar` / `LargeTopAppBar` with a scroll behaviour, `NavigationBar`, `NavigationRail`, `ModalNavigationDrawer`, `ListItem`, `Card`, `FloatingActionButton`, `Button` / `FilledTonalButton` / `OutlinedButton` / `TextButton`, `Switch`, `Checkbox`, `FilterChip`, `SegmentedButton`, `SearchBar`, `ModalBottomSheet`, `AlertDialog`, `DropdownMenu`, `Snackbar`, `PullToRefreshBox`, `ListDetailPaneScaffold`, `MaterialTheme.colorScheme` / `.typography` / `.shapes`, Material Symbols for icons.

## Motion

Container transform, shared axis and fade-through are the platform's transitions; predictive Back animates by itself when the navigation library is used as intended. Take springs and durations from the theme's motion scheme and tokens rather than hand-picked numbers, and honour the system's "Remove animations" setting with a cross-fade or a cut.

## Build and capture

Check first: `adb devices` (a running emulator or a device), `emulator -list-avds`, `$ANDROID_HOME`. Without an SDK, stop and tell the user (SKILL.md, step 1).

The proposal is a debug-only activity that reads the variant and the state from its intent:

- In an existing project, add `app/src/debug/.../ProposalActivity.kt` and declare it in `app/src/debug/AndroidManifest.xml` with `android:exported="true"`, so it never reaches a release build. It can use the app's own theme and components.
- With no project, create a minimal Compose app (Android Studio's Empty Activity template, or a copy of a project's Gradle files) in `$dir`.

```kotlin
class ProposalActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val variant = intent.getStringExtra("variant") ?: "a"
        val state = intent.getStringExtra("state") ?: "default"
        setContent { AppTheme { Proposal(variant, state) } }   // Proposal switches on the variant, one file each
    }
}
```

```bash
./gradlew :app:installDebug
# A clean status bar for every capture (demo mode); turn it off afterwards with `-e command exit`.
adb shell settings put global sysui_demo_allowed 1
adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0941
adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false
adb shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false

adb shell cmd uimode night no                      # yes for the dark captures; read and restore the user's value
adb shell am start -S -n <package>/.ProposalActivity --es variant a --es state default
sleep 2 && adb exec-out screencap -p > "$dir/v1/a-android.png"
adb shell screenrecord --time-limit 4 /sdcard/a.mp4 && adb pull /sdcard/a.mp4 "$dir/v1/a-android.mp4"   # motion
adb shell settings put system font_scale 1.3       # the large-text check on the approved variant; restore to 1.0
```

Write the `<figure>` tags by hand, class `np-android`. `width` is the capture's pixel width times 160 divided by the density (`adb shell wm density`), which gives the width in dp: a 1080 px wide screen at density 420 is 411. To try a variant live, the user runs the same `am start` line with the emulator in front.

Emulators give breadth; gesture feel, refresh rate and performance need hardware. Say which produced the captures.

## Tells that give a fake away

- An iPhone app in Android's clothes: a back chevron with a title next to it, Cupertino switches, an iOS tab bar, action sheets, large titles.
- Raw hex colours instead of roles, so dark theme and dynamic colour break; arbitrary drop shadows instead of tonal elevation.
- Several FABs, or a FAB for a secondary action; a toast where a snackbar with an action belongs.
- A phone navigation bar stretched across a tablet.
- Content cut off by the status bar, the gesture bar or the keyboard; a back gesture that the app overrides.
- Hand-picked font sizes outside the type scale; an icon set other than Material Symbols.
