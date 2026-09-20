# 6402_HorribleG

**3D First‑Person Horror Game Demo**

Unreal Engine **5.6** project: `Art_Tech_UE5_6.uproject`.

## 打开项目

双击仓库根目录的 `Art_Tech_UE5_6.uproject`，使用 Unreal Engine 5.6 打开。
当前电脑上的项目路径是 `/Users/panjiang/6402_HorribleG/Art_Tech_UE5_6.uproject`。
后续在此副本中编辑、保存，再从本仓库提交；原项目目录与此副本不会自动同步。

最近编辑的恐怖场景关卡位于内容浏览器的
`Content/HorrorWhitebox/Maps/L_Horror_Floorplan_codex`。
项目保留原来的默认启动地图；若首先进入第一人称模板场景，可在内容浏览器中双击上述关卡。

## 提交到 GitHub

`.gitattributes` 已将 UE 地图、资源及主要二进制素材配置为 Git LFS。
`.gitignore` 排除 `Saved`、`Intermediate`、`DerivedDataCache` 等本机生成内容；
地图的 `*_BuiltData.uasset` 会随项目提交。

在 GitHub Desktop 中选择 `6402_HorribleG`，检查 Changes，填写提交说明，
点击 **Commit to main**，然后点击 **Push origin**。

新电脑克隆仓库前请安装 Git LFS，并执行：

```sh
git lfs install
git clone https://github.com/zeng-yuhao/6402_HorribleG.git
cd 6402_HorribleG
git lfs pull
```

首次打开前需下载完成 LFS 资源，并安装 Unreal Engine 5.6。

## 脚本和历史记录

`Scripts` 保留了场景制作脚本及检查记录。部分历史脚本包含原项目的绝对路径，
重新运行前应调整路径；正常打开项目和编辑现有关卡不需要运行这些脚本。
