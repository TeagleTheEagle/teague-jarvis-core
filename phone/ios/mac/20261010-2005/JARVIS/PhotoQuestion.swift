import PhotosUI
import SwiftUI
import UIKit

// Round 6, "Look at this" (the owner's "build round 6 with 1 to 5 and 7 to 10, and 11 and 12", 2026-10-10): a
// picture from the camera or from Photos, with a question, sent to the one Core as a JPEG of at most 2 MB and
// 16 million pixels (the Core's limits, core-reference/wearables-service.py). The Core takes it only when the owner has
// ticked the camera for this phone on the PC. Nothing is kept on the phone but the small copy on the Ask screen's
// line; the picture goes to the PC and, from there, to JARVIS's AI provider to be looked at. The JPEG is made by
// PhotoPrep (JARVISShared/PhotoPrep.swift), which Share to JARVIS uses too.

/// A picture to ask about, from either source: what the sheet shows, and what the JPEG is made from at SEND (the
/// file's bytes from Photos, read at the size sent and never decoded whole; the camera's own picture).
struct PickedPhoto: Identifiable {
    enum Source { case file(Data), camera(UIImage) }
    let id = UUID()
    let preview: UIImage
    let source: Source
}

/// The phone's camera, for one picture.
struct CameraPicker: UIViewControllerRepresentable {
    let done: (UIImage?) -> Void

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ controller: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(done: done) }

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let done: (UIImage?) -> Void
        init(done: @escaping (UIImage?) -> Void) { self.done = done }

        func imagePickerController(_ picker: UIImagePickerController,
                                   didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            done(info[.originalImage] as? UIImage)
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) { done(nil) }
    }
}

/// The picture, the question about it, and SEND.
struct PhotoQuestionSheet: View {
    @EnvironmentObject private var session: SessionModel
    @Environment(\.dismiss) private var dismiss
    let photo: PickedPhoto
    @State private var question = "What is this?"
    @State private var note: String?
    @State private var preparing = false

    var body: some View {
        NavigationStack {
            ZStack {
                PageBackground()
                ScrollView {
                    VStack(spacing: 14) {
                        Image(uiImage: photo.preview).resizable().scaledToFit()
                            .frame(maxHeight: 320)
                            .overlay(Rectangle().stroke(Theme.accent.opacity(0.4), lineWidth: 1))
                            .accessibilityLabel("The picture to ask about")
                        TextField("Ask about this picture", text: $question, axis: .vertical)
                            .font(.system(size: 14)).foregroundStyle(Theme.text)
                            .lineLimit(1...4)
                            .padding(12)
                            .background(Theme.ground.opacity(0.7))
                            .overlay(Rectangle().stroke(Theme.accent.opacity(0.3), lineWidth: 1))
                        if !session.mayLook {
                            Text("Pictures need the camera allowed for this phone on the PC: Settings > Devices > this phone > camera.")
                                .font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                        }
                        Text("The picture goes to your PC, and from there to JARVIS's AI provider to be looked at. Nothing is kept on this phone.")
                            .font(.system(size: 10)).foregroundStyle(Theme.muted).multilineTextAlignment(.center)
                        if let note {
                            Text(note).font(.system(size: 11)).foregroundStyle(Theme.warn).multilineTextAlignment(.center)
                        }
                        Button(action: sendIt) {
                            HStack(spacing: 8) {
                                Image(systemName: "paperplane.fill").font(.system(size: 14))
                                Text("SEND TO JARVIS").font(Theme.caption(11)).tracking(1.4)
                            }
                            .foregroundStyle(Theme.ground2)
                            .frame(maxWidth: .infinity).frame(height: 46)
                            .background(session.mayLook ? Theme.accent : Theme.muted)
                        }
                        .disabled(!session.mayLook || session.busy || session.recording || preparing)
                    }
                    .padding(16)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }.tint(Theme.accent).disabled(preparing)   // nothing half-sent
                }
                ToolbarItem(placement: .topBarTrailing) { SheetStopButton() }
            }
            .interactiveDismissDisabled(preparing)
            .toolbarBackground(Theme.ground2, for: .navigationBar)
            .navigationTitle("Look at this")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    /// The JPEG is made away from the screen's thread (a 48-million-pixel photo takes a moment), then sent.
    private func sendIt() {
        preparing = true
        let source = photo.source
        Task {
            let made: (jpeg: Data?, thumbnail: Data?) = await Task.detached(priority: .userInitiated) {
                switch source {
                case .file(let data): return (PhotoPrep.jpeg(fromImageData: data), PhotoPrep.thumbnail(fromImageData: data))
                case .camera(let image): return (PhotoPrep.jpeg(from: image), PhotoPrep.thumbnail(from: image))
                }
            }.value
            preparing = false
            guard let jpeg = made.jpeg else {
                note = "The picture could not be made small enough to send. Try another one."
                return
            }
            session.sendPhoto(jpeg, thumbnail: made.thumbnail, question: question)
            dismiss()
        }
    }
}
