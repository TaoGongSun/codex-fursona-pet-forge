# Pet Package Spec

This records the current repo assumption for Codex desktop pet packages. Check official docs or current renderer examples before relying on it for public releases.

## Current Package Shape

```text
<pet-id>/
├── pet.json
└── spritesheet.webp
```

`pet.json` should reference `spritesheet.webp` with the package-relative path used by the renderer.

## Current Atlas Assumption

- 8 columns x 9 rows.
- 192 x 208 pixels per cell.
- 1536 x 1872 pixels total.
- Rows map to the current action order:
  1. `idle`
  2. `running-right`
  3. `running-left`
  4. `waving`
  5. `jumping`
  6. `failed`
  7. `waiting`
  8. `running`
  9. `review`

Unused cells must be transparent and must not retain hidden RGB residue.

When exporting `spritesheet.webp`, preserve RGB values under fully transparent pixels. With Pillow, use lossless WebP plus `exact=True`:

```python
image.save(path, "WEBP", lossless=True, method=6, exact=True)
```

Without the exact/preserve-transparent-RGB option, the encoded WebP can reintroduce hidden RGB residue even when the source PNG atlas has clean transparent pixels.

## Before Packaging

- Confirm current official docs if network access and time are available, especially before a release or public guide.
- Confirm existing renderer/package examples when official docs are incomplete.
- If docs or examples changed, update this file, validators, and row prompts before generating the final package.

## Package Validation

At minimum, validation should check:

- `pet.json` exists.
- `spritesheet.webp` exists.
- Spritesheet dimensions are 1536 x 1872 under the current assumption.
- `pet.json` points to the delivered spritesheet.
- Alpha exists.
- Unused cells are transparent.
- QA previews and validation report exist alongside the generated run artifacts.
