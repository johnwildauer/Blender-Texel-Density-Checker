import bpy
import bmesh

from bpy.props import StringProperty

from . import utils


class Texel_Density_Copy(bpy.types.Operator):
	"""Copy Density"""
	bl_idname = "object.texel_density_copy"
	bl_label = "Copy Texel Density"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		td = context.scene.td
		
		#save current mode and active object
		start_active_obj = bpy.context.active_object
		start_selected_obj = bpy.context.selected_objects
		start_mode = bpy.context.object.mode

		#Calculate TD for Active Object and copy value to Set TD Value Field
		bpy.ops.object.select_all(action='DESELECT')
		start_active_obj.select_set(True)
		bpy.context.view_layer.objects.active = start_active_obj
		bpy.ops.object.texel_density_check()
		td.density_set = td.density

		for x in start_selected_obj:
			bpy.ops.object.select_all(action='DESELECT')
			if (x.type == 'MESH' and len(x.data.uv_layers) > 0) and not x == start_active_obj:
				x.select_set(True)
				bpy.context.view_layer.objects.active = x
				bpy.ops.object.texel_density_set()

		#Select Objects Again
		for x in start_selected_obj:
			x.select_set(True)
		bpy.context.view_layer.objects.active = start_active_obj
		
		return {'FINISHED'}


class Calculated_To_Set(bpy.types.Operator):
	"""Copy Calc to Set"""
	bl_idname = "object.calculate_to_set"
	bl_label = "Set Texel Density"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		td = context.scene.td
		
		td.density_set = td.density
		
		return {'FINISHED'}
		

class Preset_Set(bpy.types.Operator):
	"""Preset Set Density"""
	bl_idname = "object.preset_set"
	bl_label = "Set Texel Density"
	bl_options = {'REGISTER', 'UNDO'}
	td_value: StringProperty()
	
	def execute(self, context):
		td = context.scene.td
		
		td.density_set = self.td_value
		bpy.ops.object.texel_density_set()
				
		return {'FINISHED'}
		

class Select_By_TD_Space(bpy.types.Operator):
	"""Select Faces with same TD"""
	bl_idname = "object.select_by_td_space"
	bl_label = "Select Faces with same TD"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		td = context.scene.td
		
		#save current mode and active object
		start_active_obj = bpy.context.active_object
		start_selected_obj = bpy.context.selected_objects
		
		search_value = float(td.select_value)
		select_threshold = float(td.select_threshold)
		
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
		bpy.context.scene.tool_settings.uv_select_mode = 'FACE'
		
		bpy.ops.object.mode_set(mode='OBJECT')
		
		for x in start_selected_obj:
			bpy.ops.object.select_all(action='DESELECT')
			if (x.type == 'MESH' and len(x.data.uv_layers) > 0):
				x.select_set(True)
				bpy.context.view_layer.objects.active = x
				
				face_count = len(bpy.context.active_object.data.polygons)
				
				searched_faces=[]

				islands_list = []
				face_td_area_list = []

				islands_list = utils.Get_UV_Islands()
				face_td_area_list = utils.Calculate_TD_Area_To_List()

				if td.select_mode == "FACES_BY_TD":
					for face_id in range(0, face_count):
						if (face_td_area_list[face_id][0] >= (search_value - select_threshold)) and (face_td_area_list[face_id][0] <= (search_value + select_threshold)):
							searched_faces.append(face_id)

				elif td.select_mode == "ISLANDS_BY_TD":
					for uv_island in islands_list:
						island_td = 0
						island_area = 0
						#Calculate Total Island Area
						for face_id in uv_island:
							island_area += face_td_area_list[face_id][1]

						if island_area == 0:
							island_area = 0.000001

						for face_id in uv_island:						
							island_td += face_td_area_list[face_id][0] * face_td_area_list[face_id][1]/island_area

						print(str(island_td) + "\n")
						if (island_td >= (search_value - select_threshold)) and (island_td <= (search_value + select_threshold)):
							for face_id in uv_island:	
								searched_faces.append(face_id)

				elif td.select_mode == "ISLANDS_BY_SPACE":
					for uv_island in islands_list:
						island_area = 0
						for face_id in uv_island:						
							island_area += face_td_area_list[face_id][1]
							
						island_area *= 100

						print(str(island_area) + "\n")

						if (island_area >= (search_value - select_threshold)) and (island_area <= (search_value + select_threshold)):
							for face_id in uv_island:
								searched_faces.append(face_id)

				if bpy.context.area.spaces.active.type == "IMAGE_EDITOR" and bpy.context.scene.tool_settings.use_uv_select_sync == False:
					bpy.ops.object.mode_set(mode='EDIT')

					mesh = bpy.context.active_object.data
					bm_local = bmesh.from_edit_mesh(mesh)
					bm_local.faces.ensure_lookup_table()
					uv_layer = bm_local.loops.layers.uv.active

					for uv_id in range(0, len(bm_local.faces)):
						for loop in bm_local.faces[uv_id].loops:
							loop[uv_layer].select = False

					for face_id in searched_faces:
						for loop in bm_local.faces[face_id].loops:
							loop[uv_layer].select = True

					bpy.ops.object.mode_set(mode='OBJECT')

				else:
					bpy.ops.object.mode_set(mode='EDIT')
					bpy.ops.mesh.select_all(action='DESELECT')
					
					bpy.ops.object.mode_set(mode='OBJECT')

					for face_id in searched_faces:
						bpy.context.active_object.data.polygons[face_id].select = True

		#Select Objects Again
		for x in start_selected_obj:
			x.select_set(True)
		bpy.context.view_layer.objects.active = start_active_obj

		bpy.ops.object.mode_set(mode='EDIT')

		return {'FINISHED'}


classes = (
	Texel_Density_Copy,
	Calculated_To_Set,
	Preset_Set,
	Select_By_TD_Space,
)
	

def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)