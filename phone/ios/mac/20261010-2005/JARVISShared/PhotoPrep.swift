import ImageIO
import UIKit

// A picture made ready for the Core (round 6): a JPEG of at most 2 MB and 16 million pixels, the Core's limits
// (core-reference/wearables-service.py). Shared by "Look at this" in the app and Share to JARVIS. The Core takes a
// picture only when the owner has ticked the camera for this phone on the PC.

enum PhotoPrep {
    static let maxBytes = 1_900_000            // under the Core's 2 MB, with room
    static let longestSide: CGFloat = 1600     // 2.6 million pixels at most, far under the Core's 16 million

    /// The picture made smaller (1600 px on its longest side at most), upright, as a JPEG under the limit.
    static func jpeg(from image: UIImage) -> Data? {
        let scaled = resized(image, longest: longestSide)
        var quality: CGFloat = 0.75
        while quality >= 0.3 {
            if let data = scaled.jpegData(compressionQuality: quality), data.count <= maxBytes { return data }
            quality -= 0.15
        }
        guard let data = resized(image, longest: 1000).jpegData(compressionQuality: 0.5), data.count <= maxBytes else { return nil }
        return data
    }

    /// The small copy shown on the line of the Ask screen.
    static func thumbnail(from image: UIImage) -> Data? {
        resized(image, longest: 360).jpegData(compressionQuality: 0.6)
    }

    /// A picture handed over as a file's bytes (Share to JARVIS, from Photos or another app), read straight at
    /// 1600 px on its longest side: a photo of 48 million pixels is never decoded whole, which an extension's small
    /// memory could not hold. Turned upright as the file says; JPEG, HEIC or PNG in, a JPEG under the limit out.
    static func jpeg(fromImageData data: Data) -> Data? {
        for side in [Int(longestSide), 1000] {
            guard let image = downsampled(data, longest: side) else { return nil }
            var quality: CGFloat = 0.75
            while quality >= 0.3 {
                if let out = image.jpegData(compressionQuality: quality), out.count <= maxBytes { return out }
                quality -= 0.15
            }
        }
        return nil
    }

    /// A copy to show on screen (Share to JARVIS, the "Look at this" sheet), from the same bytes.
    static func preview(fromImageData data: Data, longest: Int = 480) -> UIImage? {
        downsampled(data, longest: longest)
    }

    /// The small copy for the line of the Ask screen, from the same bytes.
    static func thumbnail(fromImageData data: Data) -> Data? {
        downsampled(data, longest: 360)?.jpegData(compressionQuality: 0.6)
    }

    /// A picture handed over as a file (Share to JARVIS): read from the file itself, so the bytes are never all held
    /// in the extension's memory, at the size it is sent at, with a copy to show.
    static func prepared(fromImageAt url: URL) -> (jpeg: Data, preview: UIImage)? {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, [kCGImageSourceShouldCache: false] as CFDictionary),
              let preview = downsampled(source, longest: 480) else { return nil }
        for side in [Int(longestSide), 1000] {
            guard let image = downsampled(source, longest: side) else { return nil }
            var quality: CGFloat = 0.75
            while quality >= 0.3 {
                if let out = image.jpegData(compressionQuality: quality), out.count <= maxBytes { return (out, preview) }
                quality -= 0.15
            }
        }
        return nil
    }

    /// The picture at `longest` pixels at most on its longest side, decoded from the file at that size only.
    private static func downsampled(_ data: Data, longest: Int) -> UIImage? {
        guard let source = CGImageSourceCreateWithData(data as CFData, [kCGImageSourceShouldCache: false] as CFDictionary)
        else { return nil }
        return downsampled(source, longest: longest)
    }

    private static func downsampled(_ source: CGImageSource, longest: Int) -> UIImage? {
        let options: [CFString: Any] = [kCGImageSourceCreateThumbnailFromImageAlways: true,
                                        kCGImageSourceCreateThumbnailWithTransform: true,
                                        kCGImageSourceShouldCacheImmediately: true,
                                        kCGImageSourceThumbnailMaxPixelSize: longest]
        guard let picture = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else { return nil }
        return UIImage(cgImage: picture)
    }

    /// Drawn again at one pixel per point: the camera's orientation is baked in, and the size is at most `longest`.
    private static func resized(_ image: UIImage, longest: CGFloat) -> UIImage {
        let size = image.size
        let factor = min(1, longest / max(size.width, size.height, 1))
        let target = CGSize(width: max(1, (size.width * factor).rounded()), height: max(1, (size.height * factor).rounded()))
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        return UIGraphicsImageRenderer(size: target, format: format).image { _ in
            image.draw(in: CGRect(origin: .zero, size: target))
        }
    }
}
