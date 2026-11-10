// Entry point of a standalone proposal app. scripts/apple-render.sh compiles it together with the proposal's own
// Swift files, which define:
//
//     @MainActor @ViewBuilder func proposal(variant: String, state: String) -> some View
//
// A proposal that needs another scene (Settings, MenuBarExtra, a window style) declares its own @main type, and
// the script leaves this file out.
import SwiftUI

@main
struct ProposalApp: App {
    // Launch arguments (-variant b -state empty -appearance dark) land in UserDefaults' argument domain.
    private let args = UserDefaults.standard

    var body: some Scene {
        WindowGroup {
            proposal(variant: args.string(forKey: "variant") ?? "a", state: args.string(forKey: "state") ?? "default")
                .preferredColorScheme(args.string(forKey: "appearance").map { $0 == "dark" ? .dark : .light })
        }
        #if os(macOS)
        .defaultSize(width: args.double(forKey: "width"), height: args.double(forKey: "height"))
        #endif
    }
}
