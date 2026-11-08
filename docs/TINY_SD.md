# Tiny-SD integration

The source of truth was the user's **TinySDDesk 1.8.9 source package**, specifically `TinySDDesk.Core/model-manifest.json`, `DiffusionEngine.cs`, `Samplers.cs`, `ClipTokenizer.cs` and `docs/MODEL_NOTICES.md`. This integration uses the exact same seven model files and pinned SHA-256 values, copied into `backend/tiny-sd-manifest.json`.

- Source model: https://huggingface.co/segmind/tiny-sd
- Export: `ayushmaninbox/artificial-stupidity-asif`
- Revision: `5e4997cfbea77f8b71607c00dc2db6d9c7ca311e`
- Repository folder: `tiny-sd`
- Files: INT8 CLIP text encoder, INT8 reduced UNet, TAESD decoder, four CLIP tokenizer files.
- Exact total: 455,495,310 bytes (434.4 MiB); no additional FP16 UNet downloaded.
- Local target: `models/Tiny-SD`.

`generate_image` is an offline tool exposed to LFM3 with English prompt, optional negative prompt, width/height (256, 384, 512), steps (1–50), guidance (1–15), and seed (-1 = random). PNG files and matching JSON metadata are saved to `output/images`. GUI shows a clickable preview; CLI reports the PNG path on stderr. There is no arbitrary output-path parameter.

Image inference uses ONNX Runtime 1.23.2 **CPU**, not the INT8 graph on CUDA. This keeps the download small and avoids competing with LFM3 for GPU memory. Euler sampling, SD1.5 training sigmas, CLIP BPE rules and TAESD normalization follow the existing TinySDDesk implementation. NumPy's random generator differs from C# System.Random, so the same seed is repeatable within this implementation but not guaranteed pixel-identical to TinySDDesk.

Downloads resume through `.part` files, check pinned file size and SHA-256, and persist a verification stamp. Complete unchanged files skip hashing and downloading on later runs. `Setup.cmd -TinySdPath "D:\AI\TinySDDesk\models"` reuses an existing installation directly at the target via hardlink if possible, otherwise a single copy. Hash checks protect the first import. Known sibling TinySDDesk model locations are also checked without a whole-disk scan.

Model license: CreativeML Open RAIL-M, including its use restrictions; full text supplied in `CreativeML-OpenRAIL-M.txt`. TAESD by Ollin Boer Bohan and OpenAI CLIP are MIT; their notices are included. The export format does not change those model conditions. The app makes no claim that this is the absolute smallest SD model, nor that its output quality equals a full SD1.5 checkpoint.
