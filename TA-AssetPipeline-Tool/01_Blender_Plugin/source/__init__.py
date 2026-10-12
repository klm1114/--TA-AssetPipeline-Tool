bl_info = {
    "name": "TA 导出质检工具",
    "author": "TA",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D视图 > 侧边栏(N) > TA工具",
    "description": "Blender 到 Unity 的导出前质检与规范导出工具",
    "category": "Import-Export",
}

import bpy
import os


# ==============================
# 1. 属性
# ==============================
bpy.types.Scene.check_allowed_special = bpy.props.StringProperty(
    name="允许的特殊字符",
    default="_.-",
    description="字母和数字始终允许，这里填写允许的标点符号"
)

bpy.types.Scene.export_path = bpy.props.StringProperty(
    name="导出路径",
    default="//Unity_Exports/",
    description="FBX导出的目标文件夹",
    subtype='DIR_PATH'
)

bpy.types.Scene.export_root_name = bpy.props.StringProperty(
    name="整体模型名称",
    default="",
    description="导出后 FBX 的文件名和根节点名。留空则自动使用根物体名。"
)

bpy.types.Scene.export_anim = bpy.props.BoolProperty(
    name="导出动画",
    default=False
)


# ==============================
# 2. 操作符
# ==============================
class OBJECT_OT_CheckNaming(bpy.types.Operator):
    bl_idname = "object.check_naming"
    bl_label = "执行检查"

    def execute(self, context):
        allowed = context.scene.check_allowed_special
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        pass_count = 0
        error_count = 0
        for obj in selected_objects:
            name = obj.name
            illegal_chars = []
            for c in name:
                if c.isascii() and c.isalnum():
                    continue
                if c in allowed:
                    continue
                if c not in illegal_chars:
                    illegal_chars.append(c)
            if illegal_chars:
                error_count += 1
                self.report({'ERROR'}, f"❌ {name} —— 包含不允许的字符：{', '.join(illegal_chars)}")
            else:
                pass_count += 1
                self.report({'INFO'}, f"✅ 通过：{name}")

        if error_count == 0:
            self.report({'INFO'}, f"全部检查通过！共 {pass_count} 个物体。")
        else:
            self.report({'WARNING'}, f"检查完成：{error_count} 个不规范，{pass_count} 个通过。")
        return {'FINISHED'}


class OBJECT_OT_CleanMaterials(bpy.types.Operator):
    bl_idname = "object.clean_materials"
    bl_label = "清理未使用材质槽"

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "请先选中需要清理的物体")
            return {'CANCELLED'}

        cleaned_count = 0
        for obj in selected_objects:
            if obj.type == 'MESH':
                before_slots = len(obj.material_slots)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.material_slot_remove_unused()
                after_slots = len(obj.material_slots)
                cleaned_count += (before_slots - after_slots)
        self.report({'INFO'}, f"清理完成！共移除 {cleaned_count} 个未使用的材质槽")
        return {'FINISHED'}


class OBJECT_OT_ExportToUnity(bpy.types.Operator):
    bl_idname = "object.export_to_unity"
    bl_label = "导出到 Unity"

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "请先选中需要导出的物体")
            return {'CANCELLED'}

        export_dir = bpy.path.abspath(context.scene.export_path)
        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir)
            except Exception:
                self.report({'ERROR'}, f"无法创建导出目录: {export_dir}")
                return {'CANCELLED'}

        include_anim = context.scene.export_anim
        custom_name = context.scene.export_root_name.strip()

        # 找出选中的根物体
        selected_set = set(selected_objects)
        roots = [obj for obj in selected_objects if obj.parent not in selected_set]
        if not roots:
            roots = [selected_objects[0]]

        # 备份变量
        root_renamed = None           # (obj, old_name)
        created_empty = None          # 临时 Empty
        reparented = {}               # obj -> (old_parent, old_world_matrix)

        try:
            # ============ 确定根节点名 ============
            if custom_name:
                # 情况A：唯一根是 Empty，直接重命名
                if len(roots) == 1 and roots[0].type == 'EMPTY':
                    old_name = roots[0].name
                    roots[0].name = custom_name
                    root_renamed = (roots[0], old_name)
                    root_name = custom_name
                else:
                    # 情况B：创建临时 Empty
                    temp_empty = bpy.data.objects.new(custom_name, None)
                    temp_empty.empty_display_size = 0.1
                    context.scene.collection.objects.link(temp_empty)
                    created_empty = temp_empty

                    for obj in roots:
                        old_parent = obj.parent
                        old_matrix = obj.matrix_world.copy()
                        reparented[obj] = (old_parent, old_matrix)
                        obj.parent = temp_empty
                        obj.matrix_world = old_matrix   # 保持世界变换不变

                    root_name = custom_name
            else:
                root_name = roots[0].name

            # ============ 选中导出层级 ============
            for o in bpy.context.view_layer.objects:
                o.select_set(False)

            def select_hierarchy(obj):
                obj.select_set(True)
                for child in obj.children:
                    select_hierarchy(child)

            if created_empty:
                select_hierarchy(created_empty)
                bpy.context.view_layer.objects.active = created_empty
            else:
                for root in roots:
                    select_hierarchy(root)
                bpy.context.view_layer.objects.active = roots[0]

            # ============ 导出 FBX ============
            filepath = os.path.join(export_dir, f"{root_name}.fbx")
            export_kwargs = {
                'filepath': filepath,
                'use_selection': True,
                'apply_scale_options': 'FBX_SCALE_ALL',
                'axis_forward': '-Z',
                'axis_up': 'Y',
                'bake_space_transform': True,
                'object_types': {'MESH', 'ARMATURE', 'EMPTY'},
                'use_mesh_modifiers': True,
                'mesh_smooth_type': 'FACE',
                'path_mode': 'COPY',
                'embed_textures': False,
                'bake_anim': include_anim,
                'bake_anim_use_all_actions': include_anim,
            }

            bpy.ops.export_scene.fbx(**export_kwargs)
            self.report({'INFO'}, f"成功导出：{root_name}.fbx")

        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")

        finally:
            # ============ 恢复现场 ============
            if root_renamed:
                obj, old_name = root_renamed
                obj.name = old_name
            if created_empty:
                for obj, (old_parent, old_matrix) in reparented.items():
                    obj.parent = old_parent
                    obj.matrix_world = old_matrix
                bpy.data.objects.remove(created_empty, do_unlink=True)

        return {'FINISHED'}


# ==============================
# 3. 面板
# ==============================
class VIEW3D_PT_TATool(bpy.types.Panel):
    bl_label = "TA 导出质检工具"
    bl_idname = "VIEW3D_PT_ta_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TA工具"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="① 命名规范检查", icon='FILE_TEXT')
        box.label(text="字母和数字始终允许", icon='INFO')
        box.prop(scene, "check_allowed_special")
        box.operator("object.check_naming", icon='CHECKMARK')

        box = layout.box()
        box.label(text="② 材质清理", icon='MATERIAL')
        box.operator("object.clean_materials", icon='TRASH')

        box = layout.box()
        box.label(text="③ Unity 规范导出", icon='EXPORT')
        box.prop(scene, "export_path")
        box.prop(scene, "export_root_name")
        box.prop(scene, "export_anim")
        box.operator("object.export_to_unity", icon='PLAY')


# ==============================
# 4. 注册
# ==============================
classes = [OBJECT_OT_CheckNaming, OBJECT_OT_CleanMaterials, OBJECT_OT_ExportToUnity, VIEW3D_PT_TATool]

def register():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()