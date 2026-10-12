using UnityEngine;
using UnityEditor;
using System.Collections.Generic;

public class NamingCheckerWindow : EditorWindow
{
    private string allowedSpecialChars = "_.-";
    private Material defaultMaterial;

    [MenuItem("Tools/TA工具/TA 资产检查器")]
    public static void ShowWindow()
    {
        GetWindow<NamingCheckerWindow>("TA 资产检查器");
    }

    private void OnEnable()
    {
        defaultMaterial = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Material.mat");
    }

    private void OnGUI()
    {
        GUILayout.Label("Unity 端资产检查工具", EditorStyles.boldLabel);
        EditorGUILayout.Space();

        // ===== 模块① 命名检查 =====
        EditorGUILayout.BeginVertical(EditorStyles.helpBox);
        GUILayout.Label("① 命名规范检查", EditorStyles.boldLabel);
        GUILayout.Label("字母和数字始终允许。\n这里填写允许的标点符号，可以填多个，例如：_.-", EditorStyles.miniLabel);
        allowedSpecialChars = EditorGUILayout.TextField("允许的特殊字符", allowedSpecialChars);
        if (GUILayout.Button("检查命名", GUILayout.Height(28))) CheckNaming();
        EditorGUILayout.EndVertical();

        EditorGUILayout.Space();

        // ===== 模块② 材质检查 =====
        EditorGUILayout.BeginVertical(EditorStyles.helpBox);
        GUILayout.Label("② 材质完整性检查", EditorStyles.boldLabel);
        GUILayout.Label("检查选中模型及其所有子结构是否都上了真实材质。\n（Unity 自动补的 Default-Material 会被视为缺失）", EditorStyles.miniLabel);
        if (GUILayout.Button("检查材质", GUILayout.Height(28))) CheckMaterials();
        EditorGUILayout.EndVertical();

        EditorGUILayout.Space();
        if (GUILayout.Button("一键全检（命名 + 材质）", GUILayout.Height(35)))
        {
            CheckNaming();
            CheckMaterials();
        }

        EditorGUILayout.Space();
        GUILayout.Label("提示：选中 Hierarchy 里的物体后点击按钮。只有出问题的物体才会显示在控制台。", EditorStyles.helpBox);
    }

    // ============ 命名检查 ============
    private void CheckNaming()
    {
        GameObject[] selectedObjects = Selection.gameObjects;
        if (selectedObjects.Length == 0)
        {
            Debug.LogWarning("【TA工具】请先在 Hierarchy 中选中至少一个物体！");
            return;
        }

        int passCount = 0;
        int errorCount = 0;

        foreach (GameObject go in selectedObjects)
        {
            string name = go.name;
            List<char> illegalChars = new List<char>();

            foreach (char c in name)
            {
                if (IsLegalChar(c)) continue;
                if (!illegalChars.Contains(c)) illegalChars.Add(c);
            }

            if (illegalChars.Count > 0)
            {
                errorCount++;
                // 只报错的，且点击日志可以定位到物体
                Debug.LogError($"❌ 命名不规范：{name} —— 包含不允许的字符：{string.Join(", ", illegalChars)}", go);
            }
            else
            {
                // 通过的物体：只计数，不打印
                passCount++;
            }
        }

        if (errorCount == 0)
        {
            Debug.Log($"<color=green>【TA工具·命名】全部检查通过！共 {passCount} 个物体。</color>");
        }
        else
        {
            Debug.Log($"<color=red>【TA工具·命名】发现 {errorCount} 个命名不规范，通过 {passCount} 个。</color>");
        }
    }

    private bool IsLegalChar(char c)
    {
        if (c < 128 && char.IsLetterOrDigit(c)) return true;
        if (allowedSpecialChars.Contains(c.ToString())) return true;
        return false;
    }

    // ============ 材质检查 ============
    private void CheckMaterials()
    {
        GameObject[] selectedObjects = Selection.gameObjects;
        if (selectedObjects.Length == 0)
        {
            Debug.LogWarning("【TA工具】请先在 Hierarchy 中选中至少一个物体！");
            return;
        }

        int totalChecked = 0;
        int missingCount = 0;
        HashSet<GameObject> processed = new HashSet<GameObject>();

        foreach (GameObject root in selectedObjects)
        {
            foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
            {
                GameObject go = t.gameObject;
                if (processed.Contains(go)) continue;
                processed.Add(go);

                Renderer[] renderers = go.GetComponents<Renderer>();
                if (renderers == null || renderers.Length == 0) continue;

                foreach (Renderer renderer in renderers)
                {
                    totalChecked++;

                    Material[] materials = renderer.sharedMaterials;
                    bool hasMissing = false;
                    string reason = "";

                    if (materials == null || materials.Length == 0)
                    {
                        hasMissing = true;
                        reason = "没有材质槽";
                    }
                    else
                    {
                        foreach (Material mat in materials)
                        {
                            if (mat == null)
                            {
                                hasMissing = true;
                                reason = "存在空材质槽";
                                break;
                            }
                            else if (IsDefaultMaterial(mat))
                            {
                                hasMissing = true;
                                reason = "只挂载了 Unity 默认材质（占位符）";
                                break;
                            }
                        }
                    }

                    if (hasMissing)
                    {
                        missingCount++;
                        Debug.LogError($"🎨 材质缺失：{go.name} —— {reason}", go);
                    }
                }
            }
        }

        if (missingCount == 0)
            Debug.Log($"<color=green>【TA工具·材质】检查通过！共检查 {totalChecked} 个结构，无材质缺失。</color>");
        else
            Debug.Log($"<color=red>【TA工具·材质】发现 {missingCount} 个材质缺失，共检查 {totalChecked} 个结构。</color>");
    }

    private bool IsDefaultMaterial(Material mat)
    {
        if (mat == null) return true;
        if (defaultMaterial != null && mat == defaultMaterial) return true;
        if (mat.name == "Default-Material") return true;

        string path = AssetDatabase.GetAssetPath(mat);
        if (!string.IsNullOrEmpty(path) &&
            (path.Contains("unity default resources") || path.Contains("unity_builtin_extra")))
        {
            return true;
        }
        return false;
    }
}