# SceneAutoProducer Snapshot Manifest

Snapshot created from local Git commit `182f67333358294c884e7c9602b1b4a31d629d01c`.

## Files

- Parts: `SceneAutoProducer.snapshot.zip.b64.part01` through `SceneAutoProducer.snapshot.zip.b64.part11`
- ZIP bytes: `40954`
- Base64 bytes: `54608`
- ZIP SHA256: `41ac3b7532c38230266820f88917a21a25294ab5051ef70734ca61c9fa944b8b`
- Base64 SHA256: `1f97a1e23e9286b40cb37a96870f9f9612e9d9d5f9b3837c09ad4b785f4868d5`

## Restore

```powershell
$b64 = (Get-ChildItem snapshots\SceneAutoProducer.snapshot.zip.b64.part* | Sort-Object Name | ForEach-Object { Get-Content -Raw $_.FullName }) -join ''
[IO.File]::WriteAllBytes('SceneAutoProducer.snapshot.zip', [Convert]::FromBase64String($b64))
Get-FileHash SceneAutoProducer.snapshot.zip -Algorithm SHA256
Expand-Archive SceneAutoProducer.snapshot.zip -DestinationPath . -Force
```
