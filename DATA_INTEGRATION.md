# Dataset and Asset Integration

The repository contains adapters and validation gates for five external data
components. Large datasets and model files remain outside Git; only conversion
code, manifests, configuration, and license evidence belong in the repository.

## 1. Shared contracts

- Category aliases: `configs/categories.json`
- Source and license policy: `configs/data_sources.json`
- Manifest schema implementation: `src/data_integration/manifest.py`
- Integration CLI: `python -m src.data_integration.cli`

A manifest contains a source, split, stable sample id, modality paths, and
source-specific metadata. All coordinates entering Scene IR use meters and
Blender Z-up coordinates.

## 2. ABO and Objaverse-OA

ABO is officially CC BY-NC 4.0 and therefore must use a separate research-only
catalog. It is intentionally excluded from the default commercial allowlist.
“Objaverse-OA” here means a project-built open-license subset of Objaverse, not
a separately licensed official bundle.

Prepare source metadata JSON files with an `assets` array. Required production
fields are `asset_id`, `category`, `path`, `dimensions`, `license`,
`commercial_use`, `poly_count`, `front_axis`, `up_axis`, and `normalized`.

Normalize each downloaded GLB without overwriting the source:

```powershell
python -m src.data_integration.cli normalize-glb `
  --input assets/models/abo/B012345/original.glb `
  --output assets/models/abo/B012345/normalized.glb `
  --source-up Y `
  --source-front Z `
  --unit-scale 0.01
```

The Blender-side normalizer converts the declared source axes to Z-up/-Y-front,
applies the unit conversion, centers the object on the XY origin, places its
lowest point at Z=0, preserves its hierarchy, and exports a new GLB.

```powershell
python -m src.data_integration.cli build-assets `
  --abo data/raw/abo/metadata.json `
  --objaverse-oa data/raw/objaverse_oa/metadata.json `
  --output assets/metadata/assets.research.json `
  --allow-license CC-BY-NC-4.0
```

The command checks GLB headers and file presence, applies the license allowlist,
requires Z-up and a known front direction, rejects invalid dimensions and very
large meshes, gives ABO duplicate priority, and writes rejected records to
`assets/metadata/quarantine.json`.

Use `--metadata-only` while preparing a catalog before the GLBs have been
downloaded. A metadata-only catalog is not production-ready and must pass the
normal command before use.

## 3. Infinigen Indoors

Each raw scene directory must contain RGB, instance mask, depth, camera JSON,
and layout JSON. Supported conventional names are listed in
`InfinigenIndoorsAdapter`.

```powershell
python -m src.data_integration.cli convert-infinigen `
  --raw-root data/raw/infinigen_indoors `
  --output-root data/processed/infinigen_indoors `
  --split train
```

The converter writes one project-native Scene IR file per scene plus a training
manifest. Camera focal length is derived from pixel focal length when needed,
and object categories pass through the shared category registry.

## 4. DeepFurniture

Convert COCO-style detection/instance segmentation annotations:

```powershell
python -m src.data_integration.cli convert-deepfurniture `
  --annotations data/raw/deepfurniture/annotations/instances_train.json `
  --image-root data/raw/deepfurniture/images `
  --output data/processed/deepfurniture/manifests/train.json `
  --split train
```

Annotations retain their original fields and gain `canonical_category`.
DeepFurniture records are training data only and are never merged into the GLB
asset catalog. Retrieval pairs can be carried inside record metadata using
`positive_id` and `hard_negative_ids`.

## 5. NYUv2 and private captures

```powershell
python -m src.data_integration.cli build-real-validation `
  --source nyuv2 `
  --image-root data/raw/nyuv2/images `
  --depth-root data/raw/nyuv2/depth `
  --annotations data/raw/nyuv2/annotations.json `
  --output data/processed/real_validation/manifests/nyuv2.json
```

Repeat with `--source custom` for private captures. These manifests are marked
`training_allowed: false` and use the `real_val` split, preventing accidental
mixing with synthetic or furniture training data.

## 6. End-to-end preflight

```powershell
python -m src.data_integration.cli validate `
  --manifest data/processed/infinigen_indoors/manifests/train.json `
  --manifest data/processed/deepfurniture/manifests/train.json `
  --manifest data/processed/real_validation/manifests/nyuv2.json `
  --asset-metadata assets/metadata/assets.json
```

The command exits non-zero for missing modalities, duplicate sample or asset
ids, malformed Scene IR, disallowed/unknown licenses, invalid orientation,
invalid dimensions, missing GLBs, or invalid GLB headers.

## 7. Recommended execution order

1. Review the category aliases and license allowlist.
2. Normalize ABO GLBs and build the initial asset catalog.
3. Normalize and orient Objaverse-OA GLBs, then rebuild the merged catalog.
4. Convert Infinigen ground truth.
5. Convert DeepFurniture training annotations.
6. Build NYUv2 and custom real-domain validation manifests.
7. Run the complete preflight before training or scene generation.
