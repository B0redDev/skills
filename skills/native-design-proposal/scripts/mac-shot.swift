// Captures a process's windows the way the screen shows them (real shadows, real materials; a sheet, popover or
// menu is a window of its own) on a plain backdrop, and prints the image's width in points.
// The backdrop is a window slipped under the app's own, so whatever else is on the desktop stays out of the picture
// and translucent materials have something neutral to sample.
// Works for any toolkit (SwiftUI, AppKit, GPUI, Flutter, Tauri). Needs the terminal's Screen Recording permission.
// usage: mac-shot <pid> <out.png> [light|dark]
import AppKit

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}
let arguments = CommandLine.arguments
guard arguments.count >= 3, let pid = Int(arguments[1]) else { fail("usage: mac-shot <pid> <out.png> [light|dark]") }

// Front to back, in global coordinates with a top-left origin.
let all = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
var union = CGRect.null
var lowest = 0
for window in all where window[kCGWindowOwnerPID as String] as? Int == pid {
    guard let bounds = window[kCGWindowBounds as String], let id = window[kCGWindowNumber as String] as? Int,
          let rect = CGRect(dictionaryRepresentation: bounds as! CFDictionary), rect.width > 1 else { continue }
    union = union.union(rect)
    lowest = id
}
guard lowest != 0 else { fail("no on-screen window for pid \(pid)") }

let rect = union.insetBy(dx: -64, dy: -64).integral   // room for the shadows
let app = NSApplication.shared
app.setActivationPolicy(.accessory)
// AppKit's origin is the bottom-left corner of the primary screen. The backdrop overshoots the captured rectangle.
let frame = CGRect(x: rect.minX, y: NSScreen.screens[0].frame.height - rect.maxY, width: rect.width, height: rect.height)
let backdrop = NSWindow(contentRect: frame.insetBy(dx: -16, dy: -16), styleMask: .borderless, backing: .buffered, defer: false)
backdrop.backgroundColor = arguments.count > 3 && arguments[3] == "dark" ? NSColor(white: 0.17, alpha: 1) : NSColor(white: 0.9, alpha: 1)
backdrop.hasShadow = false
backdrop.ignoresMouseEvents = true
backdrop.order(.below, relativeTo: lowest)
RunLoop.current.run(until: Date().addingTimeInterval(0.4))   // let the window server composite it

let capture = Process()
capture.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
capture.arguments = ["-x", "-R", "\(Int(rect.minX)),\(Int(rect.minY)),\(Int(rect.width)),\(Int(rect.height))", arguments[2]]
do { try capture.run() } catch { fail("screencapture: \(error.localizedDescription)") }
capture.waitUntilExit()
guard capture.terminationStatus == 0, FileManager.default.fileExists(atPath: arguments[2]) else {
    fail("screencapture failed: grant Screen Recording to the terminal in System Settings > Privacy & Security")
}
print(Int(rect.width))
