# Ralf Example Pet Package

This folder keeps the minimal built-in Ralf example package used by Codex
Fursona Pet Forge documentation and tests.

Only the final installable package is published here:

```text
package/ralf/
├── pet.json
└── spritesheet.webp
```

Generated references, raw rows, intermediate frames, QA images, and experimental
atlases are intentionally not part of the public package. They are production
scratch data, not required runtime assets.

## Codex Pet Package Shape

Codex pet packages commonly contain:

```text
<pet-id>/
├── pet.json
└── spritesheet.webp
```

The Ralf example follows this common atlas layout:

```text
1536 x 1872 px
8 欄 x 9 列
每格 192 x 208 px
```
