import bpy

bl_info = {
    "name": "Bind Shapekey Driver",
    "author": "Kurotori",
    "version": (1, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Item Tab > Bind Shapekey Driver",
    "description": "Adds drivers to the active object's shapekeys to follow the second selected object's corresponding shapekeys.",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

class OBJECT_OT_bind_shapekey_driver(bpy.types.Operator):
    """Binds shapekey values of the active object to the second selected object"""
    bl_idname = "object.bind_shapekey_driver"
    bl_label = "Bind Shapekey Driver"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if exactly two mesh objects are selected
        selected_objects = context.selected_objects
        return (len(selected_objects) == 2 and
                all(obj.type == 'MESH' for obj in selected_objects) and
                context.object is not None)

    def execute(self, context):
        selected_objects = context.selected_objects
        active_obj = context.object
        target_obj = None

        # Identify the target object (the one that is not active)
        for obj in selected_objects:
            if obj != active_obj:
                target_obj = obj
                break

        if target_obj is None:
            self.report({'ERROR'}, "Could not identify target object.")
            return {'CANCELLED'}

        # Check if both objects have shape keys
        if not active_obj.data.shape_keys or not target_obj.data.shape_keys:
            self.report({'WARNING'}, "One or both objects lack shape keys.")
            return {'CANCELLED'}

        active_keys = active_obj.data.shape_keys.key_blocks
        target_keys = target_obj.data.shape_keys.key_blocks
        bound_count = 0

        # Iterate through active object's shape keys
        for active_key in active_keys:
            # Skip the Basis shape key
            if active_key.name == "Basis":
                continue

            # Check if the target object (second selected) has a shape key with the same name
            if active_key.name in target_keys:
                # The shape key on the active object (first selected) is the target for the driver
                driver_target_key = active_key
                # The shape key on the second selected object is the source
                source_key_name = active_key.name # Same name

                # Remove existing driver from the active object's shape key if any
                driver_target_key.driver_remove("value")

                # Add a new driver to the active object's shape key's value
                fcurve = driver_target_key.driver_add("value")
                driver = fcurve.driver

                # Configure the driver
                driver.type = 'AVERAGE'

                # Add a variable to the driver
                var = driver.variables.new()
                var.name = "source_value"
                var.type = 'SINGLE_PROP'

                # Set the variable target to the second selected object (target_obj)
                var.targets[0].id = target_obj # Target the second selected object
                # Set the data path relative to the second selected object's data block
                var.targets[0].data_path = f'data.shape_keys.key_blocks["{source_key_name}"].value'

                # Set the driver expression to use the variable
                # For AVERAGE type, the expression is implicitly the average of variables.
                # Since we have only one variable, it just takes that value.
                # If using SCRIPTED type, expression would be var.name (e.g., "source_value")
                # driver.expression = var.name # Not needed for AVERAGE type

                bound_count += 1
                self.report({'INFO'}, f"Bound shapekey: {active_key.name}")

        if bound_count > 0:
            self.report({'INFO'}, f"Successfully bound {bound_count} shapekeys.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No matching shapekeys (excluding Basis) found to bind.")
            return {'CANCELLED'}


class VIEW3D_PT_bind_shapekey_driver_panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Bind Shapekey Driver"
    bl_idname = "VIEW3D_PT_bind_shapekey_driver"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item' # Add to the 'Item' tab in the sidebar (N key)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # Check if the operator poll is met
        if OBJECT_OT_bind_shapekey_driver.poll(context):
            active_obj = context.object
            other_obj = None
            for obj in context.selected_objects:
                if obj != active_obj:
                    other_obj = obj
                    break
            
            if active_obj and other_obj:
                # Display the binding direction: Target ← Source
                col.label(text=f"{active_obj.name} ← {other_obj.name}")
                col.separator() # Add a small space
                col.operator(OBJECT_OT_bind_shapekey_driver.bl_idname)
            else:
                # Fallback if objects couldn't be identified (should not happen if poll passed)
                 col.label(text="Select two mesh objects.")
                 col.operator(OBJECT_OT_bind_shapekey_driver.bl_idname, text="Bind Driver (Inactive)")

        else:
            # Show message if conditions are not met
            col.label(text="Select exactly two mesh objects.")
            # Optionally disable the button or show it grayed out
            op = col.operator(OBJECT_OT_bind_shapekey_driver.bl_idname, text="Bind Driver (Inactive)")


classes = (
    OBJECT_OT_bind_shapekey_driver,
    VIEW3D_PT_bind_shapekey_driver_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
