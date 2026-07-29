# 外部数据本体准备教程

本教程对应项目中的 `src.data_integration` 集成层。外部数据本体不提交到
Git；下载、申请或生成完成后统一放到 `data/raw/`，再转换成项目 manifest
和资产索引。

## 0. 先确定使用边界

| 数据源 | 获取方式 | 本项目用途 | 许可处理 |
|---|---|---|---|
| Infinigen Indoors | 本地生成 | 合成 RGB、mask、深度、相机、布局、Scene IR | 代码仓库 BSD-3-Clause；保存所用版本 |
| ABO | AWS 公共桶 | 家具 GLB，限研究配置 | 官方数据为 CC BY-NC 4.0，不进入商业主资产库 |
| Objaverse 开放子集 | Hugging Face/API 按 UID 下载 | 商业主库的长尾补充 | 数据集整体 ODC-By；每个物体仍须按自己的许可证过滤 |
| DeepFurniture | 提交官方使用条款表单后获取 | 检测、分割、检索训练 | 以获批条款为准，不转成可分发资产 |
| NYUv2 | 官方页面直接下载 | 真实域验证 | 保存官方说明、引用和下载日期 |
| 自采图片 | 自行采集 | 私有真实域验证 | 取得授权并做隐私清理 |

重要：ABO 官方 AWS 页面明确标注为 **CC BY-NC 4.0**。如果项目可能商用，
请将 ABO 仅用于研究实验、对比或内部原型，单独生成
`assets/metadata/assets.research.json`。默认的
`configs/data_sources.json` 只允许 CC0-1.0 和 CC-BY-4.0。

“Objaverse-OA”在本项目中应理解为“从 Objaverse 构建的开放许可证子集”，
而不是一个可整体下载、拥有统一资产许可证的独立官方产品。

## 1. 机器和磁盘准备

推荐在 Linux/AutoDL 数据盘准备大文件；Windows 工作区只保留代码、少量样本
和 manifest。

建议起步空间：

- Infinigen 小规模试产：100–300 GB，正式生成按场景数另行扩容。
- ABO 仅 3D 模型和必要元数据：先预留约 100 GB，下载前用 AWS 列表核算。
- Objaverse 开放子集：先下载 100–1,000 个候选，预留 50–200 GB。
- DeepFurniture：以获批下载页给出的分卷大小为准。
- NYUv2 labeled：约 2.8 GB；不要先下载约 428 GB 的 raw 视频集。

Linux 创建目录：

```bash
cd "/path/to/New project 2"
mkdir -p data/raw/{infinigen_indoors,abo,objaverse_oa,deepfurniture,nyuv2,custom_real}
mkdir -p assets/models/{abo,objaverse_oa}
mkdir -p assets/licenses/{abo,objaverse_oa}
```

安装通用工具：

```bash
python -m pip install --upgrade awscli huggingface_hub objaverse scipy pillow numpy
```

每个数据源都保存：

```text
data/raw/<source>/
  SOURCE_URL.txt
  DOWNLOAD_DATE.txt
  LICENSE.txt 或 TERMS.pdf
  CHECKSUMS.sha256
  原始数据……
```

## 2. Infinigen Indoors：生成真值

官方仓库：

- https://github.com/princeton-vl/infinigen
- 当前仓库主页会指向稳定的 Indoors/Hello Room 和 ground-truth 文档。

Infinigen 是生成器，不建议寻找一个固定的“完整数据集压缩包”。使用独立环境，
不要把它装进本项目的运行环境。

### 2.1 安装

优先按照官方仓库当前 Installation 文档安装。典型 Linux 流程为：

```bash
cd /path/to/external
git clone --recursive https://github.com/princeton-vl/infinigen.git
cd infinigen
git rev-parse HEAD > "/path/to/New project 2/data/raw/infinigen_indoors/INFINIGEN_COMMIT.txt"
```

然后执行当前版本官方安装命令。Infinigen 会绑定特定 Blender 与系统依赖，
因此不要擅自替换为项目机器上的其他 Blender 版本。

### 2.2 先做一个 Hello Room

严格使用该 commit 自带的 Hello Room 命令生成一个室内场景。先确认：

- RGB 能正常渲染；
- ground-truth 阶段能输出深度和实例/语义标注；
- 相机和场景文件存在；
- 同一 seed 能重复执行；
- GPU/CPU 渲染路径均无缺失材质。

由于 Infinigen 的命令和配置文件会随版本变化，本教程不硬编码可能过期的模块名；
以所固定 commit 的 `README`、Hello Room 和 Ground Truth 文档为准。

### 2.3 整理到项目约定

每个场景整理为：

```text
data/raw/infinigen_indoors/
  scene_000001/
    rgb.png
    instance_mask.png
    semantic_mask.png
    depth.exr
    cameras.json
    layout.json
    native_scene.json
    scene.blend
```

如果原始输出使用多相机、多帧目录，先为每个视角建立独立 sample，或者把适配器
扩展为多视角 manifest；不要把多个视角覆盖成同一个文件。

转换：

```bash
python -m src.data_integration.cli convert-infinigen \
  --raw-root data/raw/infinigen_indoors \
  --output-root data/processed/infinigen_indoors \
  --split train
```

先生成 10 个场景并通过预检，再扩大规模：

```bash
python -m src.data_integration.cli validate \
  --manifest data/processed/infinigen_indoors/manifests/train.json
```

## 3. ABO：研究用途家具 GLB

官方入口：

- https://registry.opendata.aws/amazon-berkeley-objects/
- `s3://amazon-berkeley-objects/`

官方页面列出约 7,953 个 glTF 2.0 三维模型，AWS CLI 可匿名访问。

### 3.1 查看桶，不要立即同步全部内容

```bash
aws s3 ls --no-sign-request s3://amazon-berkeley-objects/
aws s3 ls --no-sign-request --recursive s3://amazon-berkeley-objects/ > data/raw/abo/s3_inventory.txt
```

阅读桶内 README，并只选择 3D 模型、3D 元数据和类别映射。不要为本项目下载
全部商品图片与 360° 图像。

下载时按照 `s3_inventory.txt` 中的真实键名执行，例如：

```bash
aws s3 cp --no-sign-request \
  s3://amazon-berkeley-objects/<官方README中列出的3D元数据键> \
  data/raw/abo/
```

模型若按压缩分卷发布，保持原始压缩包，解压到：

```text
assets/models/abo/<asset_id>/original.glb
```

### 3.2 保存非商业许可证据

```text
assets/licenses/abo/
  CC-BY-NC-4.0.txt
  AWS_DATASET_PAGE.html
  ACCESS_DATE.txt
```

ABO 元数据中的许可证字段统一写成：

```json
{
  "license": "CC-BY-NC-4.0",
  "commercial_use": false,
  "license_source": "https://registry.opendata.aws/amazon-berkeley-objects/"
}
```

### 3.3 标准化和构建研究索引

单个模型：

```bash
python -m src.data_integration.cli normalize-glb \
  --input assets/models/abo/ASSET_ID/original.glb \
  --output assets/models/abo/ASSET_ID/normalized.glb \
  --source-up Y \
  --source-front Z \
  --unit-scale 1.0 \
  --blender-exe blender
```

源轴和单位必须来自模型/元数据检查，不能对全部 ABO 盲目套用示例参数。

研究索引必须显式允许非商业许可证，并使用独立输出：

```bash
python -m src.data_integration.cli build-assets \
  --abo data/raw/abo/metadata.project.json \
  --output assets/metadata/assets.research.json \
  --quarantine-report assets/metadata/quarantine.abo.json \
  --allow-license CC-BY-NC-4.0
```

不要把该文件替换成商业配置使用的 `assets.json`。

## 4. Objaverse 开放许可证子集

官方入口：

- https://huggingface.co/datasets/allenai/objaverse
- https://objaverse.allenai.org/docs/objaverse-1.0/

官方数据卡说明：数据集整体采用 ODC-By，但单个对象可能是 CC0、CC-BY、
CC-BY-SA、CC-BY-NC 或 CC-BY-NC-SA。项目默认只接收 CC0 和 CC-BY。

### 4.1 只拉元数据并筛选

先安装官方 API：

```bash
python -m pip install --upgrade objaverse
```

在独立 Python 脚本或 notebook 中：

```python
import objaverse

annotations = objaverse.load_annotations()

allowed = []
for uid, item in annotations.items():
    license_code = item.get("license")
    tags = " ".join(tag.get("name", "") for tag in item.get("tags", []))
    text = f"{item.get('name', '')} {tags}".lower()
    is_furniture = any(
        word in text
        for word in ("chair", "table", "sofa", "bed", "cabinet", "lamp", "shelf")
    )
    if license_code in {"cc0", "by"} and is_furniture:
        allowed.append(uid)

allowed = allowed[:500]
paths = objaverse.load_objects(uids=allowed, download_processes=8)
```

官方文档示例使用 `by` 表示 CC-BY。导入项目元数据前将许可证正规化：

```text
cc0 -> CC0-1.0
by  -> CC-BY-4.0
```

不要把 `by-nc`、`by-nc-sa` 加入商业主库。对于 `by-sa`，是否接受取决于项目
分发方式和法律评估，默认拒绝。

### 4.2 移动所选 GLB 并保留署名

```text
assets/models/objaverse_oa/<uid>/
  original.glb
  normalized.glb
  attribution.json
```

`attribution.json` 至少保存：

- UID；
- 原作者/用户名；
- 原始模型页；
- 单体许可证；
- 模型名称；
- 下载日期；
- 原始 annotation；
- SHA-256。

标准化后，生成 `data/raw/objaverse_oa/metadata.project.json`，再执行：

```bash
python -m src.data_integration.cli build-assets \
  --objaverse-oa data/raw/objaverse_oa/metadata.project.json \
  --output assets/metadata/assets.objaverse.json \
  --quarantine-report assets/metadata/quarantine.objaverse.json
```

最后再与允许的其他商业资产源合并。不要一次下载完整 Objaverse；Hugging Face
数据卡显示全库规模达到 TB 级。

## 5. DeepFurniture：申请后下载

官方入口：

- https://www.kujiale.com/festatic/furnitureSetRetrieval

官方页面要求先同意使用条款并提交 Google Form，获批后由维护方发送完整下载链接。
数据包含 image、instance 和 identity 三层标注。

### 5.1 申请

1. 打开官方页面的 “HERE” 使用条款表单。
2. 使用真实姓名、机构和研究目的填写。
3. 说明用途为家具检测、实例分割和检索训练。
4. 不要声称将原始图像或家具身份库重新分发。
5. 保存提交时间、条款副本和获批邮件。

未获批之前，不要从网盘转载、Kaggle 镜像或不明 Hugging Face 镜像替代。

### 5.2 解压但保留原结构

```text
data/raw/deepfurniture/
  TERMS.pdf
  APPROVAL.txt
  original/
    images/
    image_level/
    instance_level/
    identity_level/
```

检查是否具备：

- 图像文件；
- 图像到室内场景/深度的映射；
- 每个实例的 bbox 与 segmentation；
- 实例到家具 identity 的映射；
- identity 的类别和风格字段；
- 官方 train/val/test split（如果提供）。

当前项目转换器接收 COCO 风格 JSON。如果官方文件不是 COCO 格式，先制作：

```text
data/raw/deepfurniture/annotations/instances_train.json
data/raw/deepfurniture/annotations/instances_val.json
```

COCO JSON 至少包含 `images`、`annotations`、`categories`，并保留原
identity ID 作为额外字段。

转换：

```bash
python -m src.data_integration.cli convert-deepfurniture \
  --annotations data/raw/deepfurniture/annotations/instances_train.json \
  --image-root data/raw/deepfurniture/original/images \
  --output data/processed/deepfurniture/manifests/train.json \
  --split train
```

## 6. NYUv2：只下载 labeled 集

官方入口：

- https://cs.nyu.edu/~fergus/datasets/nyu_depth_v2.html

官方页面提供约 2.8 GB 的 labeled `.mat` 文件，包含 1,449 对对齐 RGB/深度，
以及 instance、label、scene 等字段。项目做真实域验证时不需要约 428 GB 的
raw 视频数据。

### 6.1 下载

从官方页面点击 “Labeled dataset (~2.8 GB)” 下载到：

```text
data/raw/nyuv2/nyu_depth_v2_labeled.mat
```

同时下载 Toolbox 或至少保存官方相机参数说明。下载后计算校验：

```bash
sha256sum data/raw/nyuv2/nyu_depth_v2_labeled.mat \
  > data/raw/nyuv2/CHECKSUMS.sha256
```

### 6.2 解包为项目格式

使用 `scipy.io.loadmat`；如果文件是 MATLAB v7.3/HDF5，则使用 `h5py`。导出：

```text
data/raw/nyuv2/exported/
  images/000001.png
  depth/000001.npy
  instances/000001.png
  labels/000001.png
  annotations.json
```

注意官方矩阵维度可能需要转置；先人工对比 5 张 RGB、depth、instance overlay，
确认没有左右翻转或宽高交换。官方页面说明深度单位为米。

构建验证 manifest：

```bash
python -m src.data_integration.cli build-real-validation \
  --source nyuv2 \
  --image-root data/raw/nyuv2/exported/images \
  --depth-root data/raw/nyuv2/exported/depth \
  --annotations data/raw/nyuv2/exported/annotations.json \
  --output data/processed/real_validation/manifests/nyuv2.json
```

## 7. 少量自采图片

建议采集 20–50 个房间，每个房间 3–8 个视角。固定规则：

- 拍摄前获得场地和人员授权；
- 避免人脸、证件、地址、家庭照片和屏幕内容；
- 保留原图 EXIF 的副本，但训练/评估版本应清理敏感 EXIF；
- 不使用社交平台或房产网站图片冒充“自采”；
- 记录相机型号、焦距、裁剪和缩放；
- 同一房间的所有视角必须进入同一个 split，防止数据泄漏。

目录：

```text
data/raw/custom_real/
  images/
  annotations.json
  CONSENT_TEMPLATE.md
  COLLECTION_LOG.csv
```

构建：

```bash
python -m src.data_integration.cli build-real-validation \
  --source custom \
  --image-root data/raw/custom_real/images \
  --annotations data/raw/custom_real/annotations.json \
  --output data/processed/real_validation/manifests/custom.json
```

## 8. 最终验收

先分别验收，再合并训练：

```bash
python -m src.data_integration.cli validate \
  --manifest data/processed/infinigen_indoors/manifests/train.json \
  --manifest data/processed/deepfurniture/manifests/train.json \
  --manifest data/processed/real_validation/manifests/nyuv2.json \
  --manifest data/processed/real_validation/manifests/custom.json \
  --asset-metadata assets/metadata/assets.json
```

还应人工抽查：

1. 随机打开 20 个 GLB，确认朝向、尺度、纹理和原点。
2. 随机叠加 20 组 mask/instance，确认实例 ID 一致。
3. 随机可视化 20 张 NYUv2 depth，确认米制深度和方向。
4. 检查所有 Objaverse 资产都有 attribution 文件。
5. 确认商业 `assets.json` 中不存在 `CC-BY-NC`、`unknown` 或空许可证。
6. 确认 ABO 只存在于研究索引。

## 9. 官方依据

- Infinigen 官方 GitHub：BSD-3-Clause，并提供 Indoors、Hello Room 和扩展
  ground-truth 文档。
- AWS Open Data 的 ABO 页面：GLB 格式、公开 S3 桶及 CC BY-NC 4.0。
- Objaverse 官方文档/Hugging Face 数据卡：API 按 UID 下载，整体 ODC-By，
  单体许可证不同。
- DeepFurniture 官方项目页：需提交条款表单后获取，包含 24k 室内图像、
  170k 家具实例和 20k identity。
- NYUv2 官方页面：1,449 个 labeled RGB-D 对、约 2.8 GB labeled 文件，
  深度以米为单位。
