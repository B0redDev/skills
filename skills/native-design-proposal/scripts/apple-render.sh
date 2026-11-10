#!/bin/bash
# Builds a standalone SwiftUI proposal (no Xcode project) and captures it for real: from the iOS Simulator, or as
# a macOS window. With APP set, it captures another toolkit's Mac executable instead (GPUI, Flutter, Tauri).
#
#   apple-render.sh <ios|mac> <proposal-dir> shot [-o <subdir>] <spec>...   capture PNGs, print their <figure> tags
#   apple-render.sh <ios|mac> <proposal-dir> run <spec>                     leave it running for the user to try
#   apple-render.sh ios <proposal-dir> video [-o <subdir>] <spec> [seconds] record the launch (default 4 s)
#   apple-render.sh <ios|mac> <proposal-dir> stop                           quit it; shut down the simulators it booted
#
# <spec> is variant[:state][@dark], e.g. a, b:empty, c:sheet@dark. The app receives it as launch arguments
# (-variant b -state empty -appearance dark); see assets/apple/ProposalApp.swift.
# <proposal-dir> holds the proposal's *.swift files and, optionally, Resources/ (images copied into the bundle).
#
# Environment:
#   NAME     app name, shown as the Mac window title and in the iPad status bar (default Proposal)
#   DEVICE   simulator name, e.g. "iPad Air 11-inch (M4)" (default: the first available iPhone)
#   TEXT     Dynamic Type size for the capture, e.g. accessibility-large (ios; restored afterwards)
#   SIZE     macOS window size in points (default 1100x720)
#   APP      mac: a built executable to capture instead of the SwiftUI sources. It is copied into the proposal
#            (a later build of the project cannot swap it) and launched as
#            <copy> --variant b --appearance dark [--state empty] --size 1100x720. Later runs without APP reuse the copy.
#   SETTLE   seconds between launch and capture (default 2)
set -euo pipefail

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
[ $# -ge 3 ] || usage
platform=$1 dir=$(cd "$2" && pwd) cmd=$3; shift 3
here=$(cd "$(dirname "$0")" && pwd)
build="$dir/.build/$platform"
id="proposal.$(basename "$dir" | tr -c 'A-Za-z0-9\n' '-')"
settle=${SETTLE:-2}
out="$dir"
if [ "${1:-}" = -o ]; then case $2 in /*) out=$2;; *) out="$dir/$2";; esac; shift 2; fi
mkdir -p "$build" "$out"

sources=("$dir"/*.swift)
grep -q '^@main' "${sources[@]}" 2>/dev/null || sources+=("$here/../assets/apple/ProposalApp.swift")

plist() { # <path> <platform-specific keys>
  cat > "$1" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleIdentifier</key><string>$id</string>
  <key>CFBundleExecutable</key><string>Proposal</string>
  <key>CFBundleName</key><string>${NAME:-Proposal}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  $2
</dict></plist>
EOF
}

# variant[:state][@dark] -> launch arguments in $args, file stem in $stem, caption suffix in $look
parse() {
  local spec=$1 variant state=
  look=light dark=; case $spec in *@dark) look=dark dark=-dark spec=${spec%@dark};; esac
  variant=${spec%%:*}; case $spec in *:*) state=${spec#*:};; esac
  args=(-variant "$variant" -appearance "$look"); stem=$variant
  if [ -n "$state" ]; then args+=(-state "$state"); stem+="-$state"; fi
}

figure() { # <file> <width in points> <kind> <caption>
  echo "<figure class=\"np-shot np-$3\"><img src=\"${1#"$dir"/}\" width=\"$2\" alt=\"\"><figcaption>$4</figcaption></figure>"
}

if [ "$cmd" = stop ]; then
  pkill -f "$build/" 2>/dev/null || true
  [ ! -f "$build/booted" ] || sort -u "$build/booted" | xargs -n1 xcrun simctl shutdown 2>/dev/null || true
  rm -f "$build/booted"
  exit
fi
[ $# -ge 1 ] || usage

if [ "$platform" = ios ]; then
  app="$build/Proposal.app"; mkdir -p "$app"
  sdk=$(xcrun --sdk iphonesimulator --show-sdk-path)
  target="$(uname -m)-apple-ios${IOS_TARGET:-$(xcrun --sdk iphonesimulator --show-sdk-version)}-simulator"
  xcrun --sdk iphonesimulator swiftc -parse-as-library -target "$target" -sdk "$sdk" "${sources[@]}" -o "$app/Proposal"
  # UILaunchScreen makes the app full-screen; without it iOS letterboxes it at a legacy size.
  plist "$app/Info.plist" '<key>UILaunchScreen</key><dict/><key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>'
  [ -d "$dir/Resources" ] && cp -R "$dir/Resources/." "$app/"

  line=$(xcrun simctl list devices available | grep -F "    ${DEVICE:+$DEVICE (}" | grep -F "${DEVICE:-iPhone}" | head -1 || true)
  [ -n "$line" ] || { echo "no available simulator matches '${DEVICE:-iPhone}': xcrun simctl list devices available" >&2; exit 1; }
  udid=$(grep -oE '[0-9A-F-]{36}' <<<"$line"); device=$(sed -E 's/^ +(.*) \([0-9A-F-]{36}\).*/\1/' <<<"$line")
  case $device in *iPad*) kind=ipad scale=2;; *) kind=iphone scale=3;; esac
  xcrun simctl list devices booted | grep -q "$udid" || echo "$udid" >> "$build/booted"
  xcrun simctl bootstatus "$udid" -b >/dev/null
  xcrun simctl status_bar "$udid" override --time 9:41 --batteryState charged --batteryLevel 100 --wifiBars 3 --cellularBars 4
  xcrun simctl install "$udid" "$app"
  xcrun simctl io "$udid" screenshot "$build/probe.png" 2>/dev/null
  width=$(($(sips -g pixelWidth "$build/probe.png" | awk '/pixelWidth/ {print $2}') / scale))   # the screen, in points
  if [ -n "${TEXT:-}" ]; then
    was=$(xcrun simctl ui "$udid" content_size); trap 'xcrun simctl ui "$udid" content_size "$was"' EXIT
    xcrun simctl ui "$udid" content_size "$TEXT"
  fi
  launch() { xcrun simctl launch --terminate-running-process "$udid" "$id" "${args[@]}" >/dev/null; }

  case $cmd in
    shot)
      for spec in "$@"; do
        parse "$spec"; launch; sleep "$settle"
        file="$out/$stem-$kind${TEXT:+-$TEXT}$dark.png"
        xcrun simctl io "$udid" screenshot --mask alpha "$file" 2>/dev/null
        figure "$file" "$width" "$kind" "$device · $look${TEXT:+ · $TEXT}"
      done;;
    video)
      parse "$1"; file="$out/$stem-$kind.mp4"
      xcrun simctl terminate "$udid" "$id" 2>/dev/null || true
      xcrun simctl io "$udid" recordVideo --codec h264 --force "$file" 2>/dev/null & rec=$!
      sleep 1; launch; sleep "${2:-4}"; kill -INT $rec; wait $rec || true
      echo "<figure class=\"np-shot np-$kind\"><video src=\"${file#"$dir"/}\" width=\"$width\" controls loop muted playsinline></video><figcaption>$device · motion</figcaption></figure>";;
    run)
      # The simulator's window is Simulator.app up to Xcode 26 and DeviceHub.app from Xcode 27.
      ui="$(xcode-select -p)/Applications/Simulator.app"; [ -d "$ui" ] || ui="$(xcode-select -p)/../Applications/DeviceHub.app"
      parse "$1"; open "$ui" --args -CurrentDeviceUDID "$udid"; launch
      echo "running '$1' on $device";;
    *) usage;;
  esac

elif [ "$platform" = mac ]; then
  [ "$build/mac-shot" -nt "$here/mac-shot.swift" ] || swiftc -O "$here/mac-shot.swift" -o "$build/mac-shot"
  size=${SIZE:-1100x720}
  if [ -n "${APP:-}" ] || [ -x "$build/proposal-app" ]; then
    # shortcut: a bare executable only; for an .app bundle with resources, launch it yourself and call mac-shot.
    # rm first: overwriting a signed executable in place gets the next launch killed on Apple Silicon.
    bin="$build/proposal-app"; [ -z "${APP:-}" ] || { rm -f "$bin"; cp "$APP" "$bin"; }
    launch() {
      local arg long=()
      for arg in "${args[@]}"; do case $arg in -*) long+=("-$arg");; *) long+=("$arg");; esac; done
      pkill -f "$bin" 2>/dev/null || true
      nohup "$bin" "${long[@]}" --size "$size" >/dev/null 2>&1 &
      disown; sleep 1
      kill -0 $! 2>/dev/null || { echo "$bin exited at launch: run it by hand to see why" >&2; exit 1; }
    }
    # A window started from a terminal opens behind it and draws inactive: bring it forward once it exists.
    front() {
      osascript -e "tell application \"System Events\" to tell (first process whose unix id is $(pgrep -n -f "$bin"))" \
        -e 'set frontmost to true' -e 'perform action "AXRaise" of window 1' -e 'end tell' >/dev/null 2>&1 || true
      sleep 0.5
    }
  else
    app="$build/Proposal.app"; bin="$app/Contents/MacOS/Proposal"; mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
    swiftc -parse-as-library "${sources[@]}" -o "$bin"
    plist "$app/Contents/Info.plist" '<key>NSPrincipalClass</key><string>NSApplication</string><key>NSHighResolutionCapable</key><true/>'
    [ -d "$dir/Resources" ] && cp -R "$dir/Resources/." "$app/Contents/Resources/"
    launch() {
      pkill -f "$bin" 2>/dev/null || true
      defaults delete "$id" 2>/dev/null || true   # a saved window frame would override -width/-height
      open -n "$app" --args "${args[@]}" -width "${size%x*}" -height "${size#*x}" -ApplePersistenceIgnoreState YES
    }
    front() { :; }   # `open` activates the app
  fi

  case $cmd in
    shot)
      for spec in "$@"; do
        parse "$spec"; launch; sleep "$settle"; front
        file="$out/$stem-mac${SIZE:+-$SIZE}$dark.png"
        figure "$file" "$("$build/mac-shot" "$(pgrep -n -f "$bin")" "$file" "$look")" mac "Mac · $look"
      done
      pkill -f "$bin" 2>/dev/null || true;;
    run)
      parse "$1"; launch; sleep 1; front
      echo "running '$1' as a Mac window";;
    *) usage;;
  esac
else
  usage
fi
