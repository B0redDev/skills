# Building the variants inside the project

Use this route when the decision depends on the app's own components or design system, or when the app's toolkit is not SwiftUI (UIKit, Expo / React Native, Flutter, GPUI). The GPUI recipe was run on a real GPUI Kit 0.8 app on macOS 27; the other recipes follow each toolkit's documented commands and were not run while this skill was written, so confirm them on the first capture.

## Rules for every toolkit

- **Never in the working tree's real screens.** Work on a scratch branch or, better, a git worktree of the project, so the proposal can be thrown away whole. Tell the user where it is, and remove it when the proposal is approved unless they want to keep the code.
- **A debug-only entry point that switches on `variant` and `state`**, the same inputs as the standalone route, given by whatever the toolkit offers at launch: arguments, a deep link, intent extras, an environment variable. It also takes the appearance and, for a desktop window, the size, when the toolkit doesn't follow the system for them. Variants live in their own folder, one file each, next to one file of sample data.
- **Reuse the app's theme and components, not its data layer.** Sample data in, pixels out. A proposal must not read or write the user's real library, settings, keychain or accounts, and must not start the app's servers or background jobs: give it sample data in memory or a temporary data folder.
- **The captures and the decision page are the same** as in the standalone route: `$dir` outside the repository holds `head.html`, the fragments, the captures per round, and `vN.html`.

## Xcode project (SwiftUI, UIKit, AppKit)

Add the variants under `#if DEBUG`, and read the launch arguments where the app builds its root view: `UserDefaults.standard.string(forKey: "variant")` is set by `-variant a` on the command line. When it is present, show the proposal instead of the normal root.

```bash
xcrun simctl list devices available                     # pick a device, note its UDID
xcrun simctl bootstatus <udid> -b
xcodebuild -scheme <Scheme> -configuration Debug -destination "platform=iOS Simulator,id=<udid>" -derivedDataPath "$dir/.build" build
xcrun simctl install <udid> "$dir/.build/Build/Products/Debug-iphonesimulator/<App>.app"
xcrun simctl status_bar <udid> override --time 9:41 --batteryState charged --batteryLevel 100 --wifiBars 3 --cellularBars 4
xcrun simctl ui <udid> appearance light                 # dark for the dark captures; restore the user's value afterwards
xcrun simctl launch --terminate-running-process <udid> <bundle id> -variant a -state default
sleep 2 && xcrun simctl io <udid> screenshot --mask alpha "$dir/v1/a-iphone.png"
xcrun simctl ui <udid> content_size accessibility-large  # the large-text check; restore to the previous value
```

`<figure>` class `np-iphone` (width = pixel width ÷ 3) or `np-ipad` (÷ 2). For a Mac target, build for `platform=macOS`, launch the built app with `open -n <App>.app --args -variant a`, and capture its window with `mac-shot` (see `macos.md`).

## Expo and React Native

Read `expo-native-ui`, `expo-router` and `expo-ui` first when they are installed: they decide which components are real native ones. Add a development-only route per proposal, for example `app/proposal/[variant].tsx` reading `variant` and a `state` query parameter, and open it by deep link with the dev server running:

```bash
npx expo start                                          # in the worktree; Expo Go unless the app needs a custom build
xcrun simctl openurl <udid> "exp://127.0.0.1:8081/--/proposal/a?state=default"     # Expo Go
xcrun simctl openurl <udid> "<scheme>://proposal/a?state=default"                  # a development build
adb shell am start -a android.intent.action.VIEW -d "<scheme>://proposal/a?state=default"
```

Capture with the `simctl` lines above on iOS and with the `adb` lines of `android.md` on Android. Both platforms get their own captures and their own review: one React Native tree renders two different native designs, and a variant must look right in each (SF Symbols and HIG structure on iOS, Material icons and Material structure on Android).

## GPUI

`gpui-kit-design-guides` is normative for GPUI Kit apps: read it whole before designing, and run its design review checklist on the captures. GPUI draws its own controls and its own title bar, so "native" here means the platform's conventions for a desktop app (window chrome through the kit's `TitleBar`, menus, keyboard access, density, resizable regions), per that guide.

**Entry point.** A branch at the very top of `main`, behind `#[cfg(debug_assertions)]`, that returns before the app loads its state or starts anything: `if let Some(spec) = proposal::Spec::from_args() { return proposal::run(spec); }`. `proposal::run` starts its own `application().run`, registers what the views need (`gpui_kit::init`, assets, Quit), applies the appearance (`Theme::change(ThemeMode::Dark, None, cx)`), opens one window at the requested size, and activates the app. An `examples/` binary only works when the app is a library crate: an example cannot import from a binary crate.

It reads four arguments, which is what the capture script passes: `--variant a`, `--state default`, `--appearance light|dark`, `--size 1100x720`.

**Build and capture.** In a git worktree, point `CARGO_TARGET_DIR` at the main checkout's `target`, so the dependency tree is not built a second time (seconds instead of minutes). That makes the two checkouts share one `target/debug/<app>`, so never run that path as the proposal: after the next build of the main checkout it is the real app, with the real library. Hand it to the script once, right after your own build; the script keeps a private copy in `$dir/.build` and every later command uses the copy.

```bash
render="<skill-dir>/scripts/apple-render.sh"
export CARGO_TARGET_DIR=<main checkout>/target
cargo build && APP="$CARGO_TARGET_DIR/debug/<app>" "$render" mac "$dir" shot -o v1 a a@dark b b:none c c:sheet   # prints the <figure> tags
SIZE=760x520 "$render" mac "$dir" shot -o final b      # no APP: the copy from the last build
"$render" mac "$dir" run b                             # leave it running for the user; `stop` quits it
```

The script copies a bare executable. An app that needs a bundle around it (resources beside the binary) has to be launched by you and captured with `mac-shot` directly (see `macos.md`). Load sample images from a folder next to the copy (a path relative to `current_exe()`, with the images kept in `$dir`), so the proposal still runs after the worktree is removed.

Two things about key bindings in GPUI Kit, when the proposal adds a shortcut: `gpui_kit::init` already binds some chords globally (⌥⌘I opens its debug inspector), and a binding with a key context only fires when the window's root tracks focus. A shortcut that does nothing, or opens something else, is one of these two.

## Flutter and others

The same shape: an entry point that takes the variant and the state at launch (`flutter run -d <device> --dart-define=VARIANT=a`), the platform's capture command, the platform's reference for the look. A cross-platform toolkit that draws its own widgets has to be held to each target platform's conventions separately; say in the notes where it cannot match the system's own controls.
