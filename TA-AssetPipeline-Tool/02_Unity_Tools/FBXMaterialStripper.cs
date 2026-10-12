using UnityEngine;
using UnityEditor;

public class FBXMaterialStripper : AssetPostprocessor
{
    // 当模型导入前，Unity 会自动调用这个方法
    void OnPreprocessModel()
    {
        // 获取正在导入的模型导入器
        ModelImporter importer = assetImporter as ModelImporter;

        if (importer != null)
        {
            // 将 Material Creation Mode 设置为 None
            // 效果完全等同于你在 Inspector 里手动选择 None
            importer.materialImportMode = ModelImporterMaterialImportMode.None;

            // 可选：如果你希望它同时不导入动画（如果你在 Blender 里没勾选动画，这里也可以强制关掉）
            // importer.importAnimation = false; 

            Debug.Log($"【TA工具】已自动剥离材质: {importer.assetPath}");
        }
    }
}