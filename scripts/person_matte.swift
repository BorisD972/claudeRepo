// person_matte — détoure la personne sur une suite d'images PNG (macOS, framework Vision).
//
// Usage :  person_matte <dossier_png_source> <dossier_png_masque>
// Pour chaque image, écrit un masque en niveaux de gris de même taille (blanc = personne)
// avec VNGeneratePersonSegmentationRequest en qualité .accurate.
// Compilation (fait par gen-matte.sh) :  swiftc -O scripts/person_matte.swift -o scripts/bin/person_matte

import CoreImage
import Foundation
import ImageIO
import UniformTypeIdentifiers
import Vision

let args = CommandLine.arguments
guard args.count == 3 else {
    FileHandle.standardError.write("usage: person_matte <png_in_dir> <png_out_dir>\n".data(using: .utf8)!)
    exit(2)
}
let inDir = URL(fileURLWithPath: args[1])
let outDir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

let files = (try FileManager.default.contentsOfDirectory(at: inDir, includingPropertiesForKeys: nil))
    .filter { $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }
let context = CIContext(options: [.workingColorSpace: NSNull()])
let gray = CGColorSpaceCreateDeviceGray()

let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8

for (i, url) in files.enumerated() {
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        FileHandle.standardError.write("lecture impossible: \(url.path)\n".data(using: .utf8)!)
        exit(1)
    }
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])
    guard let mask = request.results?.first?.pixelBuffer else {
        FileHandle.standardError.write("pas de masque: \(url.path)\n".data(using: .utf8)!)
        exit(1)
    }
    // Le masque sort en basse résolution : on le remet à la taille de l'image.
    var ci = CIImage(cvPixelBuffer: mask)
    let sx = CGFloat(image.width) / ci.extent.width
    let sy = CGFloat(image.height) / ci.extent.height
    ci = ci.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
    let rect = CGRect(x: 0, y: 0, width: image.width, height: image.height)
    guard let cg = context.createCGImage(ci, from: rect, format: .L8, colorSpace: gray) else { exit(1) }

    let dst = outDir.appendingPathComponent(url.lastPathComponent)
    guard let out = CGImageDestinationCreateWithURL(dst as CFURL, UTType.png.identifier as CFString, 1, nil) else { exit(1) }
    CGImageDestinationAddImage(out, cg, nil)
    CGImageDestinationFinalize(out)
    if i % 30 == 0 { print("\(i + 1)/\(files.count)") }
}
print("ok: \(files.count) masques -> \(outDir.path)")
