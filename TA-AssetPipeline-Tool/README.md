# TA-AssetPipeline-Tool

一个为游戏美术团队设计的 **Blender → Unity 资产管线工具链**，用于解决从建模软件到引擎之间的常见交接问题：命名不规范、材质冗余、轴向错误、材质缺失排查困难。

> GitHub账号：klm1114         实习作品集         邮箱：2754129758@qq.com

---

## 一、 解决的痛点

在之前三维建模实习时，从 Blender 导资产到 Unity ，经常遇到以下问题：

| 问题                                      | 传统做法                             | 本工具做法                               |
| ----------------------------------------- | ------------------------------------ | ---------------------------------------- |
| 命名不规范，导入后要手动改                | 一个一个检查、改名                   | Blender 端一键检查，中文提示所有非法字符 |
| 材质槽冗余，Unity 里生成一堆 Material.001 | 手动设 Material Creation Mode → None | Unity 端自动拦截，导入即剥离             |
| 轴向错误，缩放变成 100 倍                 | 手动调 Import 设置                   | 导出时自动烘焙，-Z Forward / Y Up        |
| 场景模型包含几十个子结构，漏上色难发现    | 肉眼逐个翻，或引擎里一个个点开       | Unity 端一键检查，点击报错定位到具体结构 |
| 整体模型导出后，根节点名用了某个子物体    | 手动在 Unity 里改名                  | Blender 面板可自定义整体模型名称         |

---

## 二、 工具组成

### ① Blender 端插件：TA_Export_Tool

位于 `01_Blender_Plugin/`，可一键安装到 Blender（Edit → Preferences → Add-ons → Install）。

功能：
- **命名规范检查**：白名单模式，字母数字默认允许，用户可自定义允许的标点符号（如 `_.-`），其他任何字符（空格、中文、特殊标点）一律报错，并一次性列出所有非法字符。
- **清理未使用材质槽**：一键移除没有被面引用的材质槽，保留正在使用的，不破坏源文件。
- **Unity 规范导出**：
  - 支持整体层级导出，保留父子关系
  - 支持自定义整体模型名称（如 `Scene_Level01`）
  - 自动修正轴向：-Z Forward, Y Up
  - 自动烘焙变换（Bake Space Transform）
  - 可选是否导出动画
    ![1791631963511](C:\Users\peng\Desktop\TA-AssetPipeline-Tool\pictures\1791631963511.png)

### ② Unity 端工具：TA_Tools

位于 `02_Unity_Tools/`，直接拖到 Unity 项目的 `Assets/` 目录即可。

功能：
- **FBXMaterialStripper.cs**：基于 `AssetPostprocessor`，FBX 导入时自动把 Material Creation Mode 设为 None，无需手动操作。
- **NamingCheckerWindow.cs**：独立的命名检查 + 材质完整性检查窗口。
  - 命名检查：白名单模式，与 Blender 端规则完全一致
  
  - 材质检查：递归遍历所有子结构，识别 Unity 自动补的 Default-Material 作为"缺失"，点击报错可在 Hierarchy 中定位具体结构
  
    ![](C:\Users\peng\Desktop\TA-AssetPipeline-Tool\pictures\1791632029043.png)

---

## 三、 演示

### Blender 端：检查 → 清理 → 导出

![Blender Demo](03_Demo/demo_blender.gif)

### Unity 端：命名检查 + 材质缺失检查

![Unity Demo](03_Demo/demo_unity.gif)

---

## 四、 使用流程

**Blender 端：**

1. 安装 `TA_Export_Tool.zip`
2. N 面板 → TA工具
3. 选中资产 → 检查命名 → 清理材质 → 导出到 Unity

**Unity 端：**

1. 把 `TA_Tools` 拖进 `Assets/`
2. FBX 拖入项目 → 自动剥离材质
3. 打开 `Tools → TA工具 → TA 资产检查器` → 一键全检

---

## 五、 效率数据

在处理一个包含 50 个道具资产的测试项目时：

| 环节         | 传统流程                      | 使用工具            | 节省 |
| ------------ | ----------------------------- | ------------------- | ---- |
| 命名检查     | 手动逐个看，约 10 分钟        | 一键检查，5 秒      | ~99% |
| 材质清理     | 逐个 Inspector 改，约 5 分钟  | 自动拦截            | 100% |
| 轴向修正     | 逐个调 Import 设置，约 5 分钟 | 自动烘焙            | 100% |
| 材质缺失排查 | 肉眼翻子结构，约 10 分钟      | 一键检查 + 点击定位 | ~95% |

**整体约节省 25 分钟/次资产交接。**

---

## 六、 技术要点

- Blender Python API（`bpy.types.Operator` / `Panel` / `Property`）
- Blender FBX 导出器参数封装（轴向、烘焙、动画）
- Unity `AssetPostprocessor`（模型导入拦截）
- Unity `EditorWindow` 自定义编辑器工具
- 递归遍历层级、Undo 支持、日志上下文定位

---

## 七、目录说明

```
01_Blender_Plugin/   Blender 端插件源码与安装包
02_Unity_Tools/      Unity 端编辑器脚本
03_Demo/             演示 GIF 与截图
04_Docs/             详细使用说明
```