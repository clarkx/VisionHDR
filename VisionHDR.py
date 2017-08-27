# -*- coding:utf-8 -*-

# ***** BEGIN GPL LICENSE BLOCK *****
#
#	VisionHDR : Blender addon for Blender 3D
#	Copyright (C) 2017 Cédric Brandin
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# ***** END GPL LICENCE BLOCK *****


bl_info = {
	"name": "VisionHDR",
	"author": "Cédric Brandin (Clarkx)",
	"version": (0, 0, 1),
	"blender": (2, 78, 0),
	"location": "View3D",
	"description": "Interactive Environment Lighting Add-on",
	"warning": "Beta version",
	"wiki_url": "https://github.com/clarkx/VisionHDR/wiki",
	"tracker_url": "https://github.com/clarkx/VisionHDR/issues",
	"category": "Render"}

import bpy, bgl, os, blf
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix, Quaternion, Euler
from bpy.types import PropertyGroup, Panel, Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty, StringProperty, CollectionProperty, PointerProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d
import math

#########################################################################################################

#########################################################################################################
def update_panel(self, context):
	"""Update the UI panel of the addon from the preferences"""
	try:
		bpy.utils.unregister_class(VisionHDRPreferences)
	except:
		pass
	VisionHDRPreferences.bl_category = context.user_preferences.addons[__name__].preferences.category
	bpy.utils.register_class(VisionHDRPreferences)
	
#########################################################################################################

#########################################################################################################
class VisionHDRPrefs(bpy.types.AddonPreferences):
	"""Preferences"""
	bl_idname = __name__
					   
	#HUD Color
	bpy.types.Scene.HUD_color = FloatVectorProperty(	
								  name = "",
								  subtype = "COLOR",
								  size = 4,
								  min = 0.0,
								  max = 1.0,
								  default = (1.0, 0.09, 0.3, 0.8))								   

	category = bpy.props.StringProperty(
			name="Category",
			description="Choose a name for the category of the panel",
			default="VisionHDR",
			update=update_panel,
			)
							   
	def draw(self, context):
		scene = context.scene
		layout = self.layout
		row = layout.row()
		row.prop(self, "category")
		row.label(text="HUD Color")
		row.prop(scene, "HUD_color", text="")

#########################################################################################################

#########################################################################################################	
def draw_line_3d(color, start, end, hit, width=1):
	"""Draw a line for direction and point for hit in bgl for HUD"""
	bgl.glLineWidth(1.0)
	bgl.glColor4f(*color)
	bgl.glEnable(bgl.GL_LINE_SMOOTH)
	bgl.glBegin(bgl.GL_LINES)	
	bgl.glVertex3f(*start)
	bgl.glVertex3f(*end)
	bgl.glEnd()
	bgl.glEnable(bgl.GL_POINT_SMOOTH)
	bgl.glPointSize(15.0);
	bgl.glBegin(bgl.GL_POINTS);
	bgl.glVertex3f(*hit)
	bgl.glEnd()
	bgl.glLineWidth(1)

#########################################################################################################

#########################################################################################################	
def draw_circle_2d(color, cx, cy, r, rot = 0):
	"""Draw a circle in bgl for HUD"""
	#http://slabode.exofire.net/circle_draw.shtml
	num_segments = 20	
	if num_segments < 1:
		num_segments = 1
	theta = 2 * 3.1415926 / num_segments
	c = math.cos(theta) 
	s = math.sin(theta)
	x = r 
	y = 0
	bgl.glLineWidth(5.0)
	bgl.glColor4f(*color)
	bgl.glEnable(bgl.GL_BLEND)
	bgl.glEnable(bgl.GL_LINE_SMOOTH)
	bgl.glPushMatrix()
	bgl.glTranslatef(cx, cy,0)
	bgl.glBegin(bgl.GL_LINE_LOOP)
	for i in range (num_segments):
		bgl.glVertex2f(x , y )
		t = x
		x = c * x - s * y
		y = s * t + c * y
	bgl.glEnd() 
	bgl.glPopMatrix()
		
#########################################################################################################

#########################################################################################################	
def draw_callback_2d(self, context, event):
	"""Display and draw bgl informations"""
	obj_light = context.active_object
	txt_add_light = "Add light: CTRL+LMB"
	region = context.region
	lw = 4 // 2
	hudcol = context.scene.HUD_color[0], context.scene.HUD_color[1], context.scene.HUD_color[2], context.scene.HUD_color[3]
	bgl.glColor4f(*hudcol)
	left = 20

#---Region overlap on
	overlap = bpy.context.user_preferences.system.use_region_overlap
	t_panel_width = 0
	if context.area == self.visionHDR_area :
		if overlap:
			for region in bpy.context.area.regions:
				if region.type == 'TOOLS':
					left += region.width
					
	#---Draw frame around the view3D
		bgl.glEnable(bgl.GL_BLEND)
		bgl.glLineWidth(4)
		bgl.glBegin(bgl.GL_LINE_STRIP)
		bgl.glVertex2i(lw, lw)
		bgl.glVertex2i(region.width - lw, lw)
		bgl.glVertex2i(region.width - lw, region.height - lw)
		bgl.glVertex2i(lw, region.height - lw)
		bgl.glVertex2i(lw, lw)
		bgl.glEnd() 
														
	#---Restore opengl defaults
		bgl.glLineWidth(1)
		bgl.glDisable(bgl.GL_BLEND)
		bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
#########################################################################################################

#########################################################################################################	
def draw_callback_3d(self, context, event):
	"""Display and draw bgl informations"""
	obj_light = context.active_object
	hudcol = context.scene.HUD_color[0], context.scene.HUD_color[1], context.scene.HUD_color[2], context.scene.HUD_color[3]
	bgl.glColor4f(*hudcol)

	if context.area == self.visionHDR_area :
		
	#---Interactive mode
		if self.editmode:
		
			if obj_light is not None and obj_light.type != 'EMPTY' and obj_light.data.name.startswith("VisionHDR"):
				#---Draw circle
				color = hudcol 
				range = (math.sqrt(obj_light.location.x**2 + obj_light.location.y**2 + obj_light.location.z**2) * 0.01)
				
				if obj_light.get('hit') is not None :
					hit = Vector(obj_light['hit']) + (range * Vector(obj_light['dir']))
					draw_line_3d(hudcol, Vector(obj_light['hit']), obj_light.location, hit, width=2)
		
	#---Restore opengl defaults
		bgl.glLineWidth(1)
		bgl.glDisable(bgl.GL_BLEND)
		bgl.glColor4f(0.0, 0.0, 0.0, 1.0)	
#########################################################################################################

#########################################################################################################	
def draw_target_px(self, context, event):
	"""Get the brightest pixel """
	
	if context.area == self.visionHDR_area :	
		hudcol = context.scene.HUD_color
		uv_x, uv_y = self.mouse_path
		x, y = (event.mouse_x - context.region.x, event.mouse_y - 22)
		draw_circle_2d((hudcol[0], hudcol[1], hudcol[2], 0.4), x, y, 20) 
		
	#---Restore opengl defaults
		bgl.glLineWidth(1)
		bgl.glDisable(bgl.GL_BLEND)
		bgl.glColor4f(0.0, 0.0, 0.0, 1.0)	
	
#########################################################################################################

#########################################################################################################
def raycast_light(self, context, coord, ray_max=1000.0):
	"""Compute the location and rotation of the light from the angle or normal of the targeted face off the object"""
	scene = context.scene
	i = 0
	p = 0
	length_squared = 0
	light = context.active_object
	light['pixel_select'] = False
	self.reflect_angle = "View" if light.VisionHDR.reflect_angle == "0" else "Normal"
	v3d = context.space_data
	rv3d = v3d.region_3d
	
#---Get the ray from the viewport and mouse
	view_vector = view3d_utils.region_2d_to_vector_3d(self.region, self.rv3d, (coord))
	ray_origin = view3d_utils.region_2d_to_origin_3d(self.region, self.rv3d, (coord))
	ray_target = ray_origin + (view_vector * ray_max)

	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			rv3d = area.spaces[0].region_3d
			if rv3d is not None: 
				distance = area.spaces[0].region_3d.view_distance

	
#---Select the object 
	def visible_objects_and_duplis():
		for obj in context.visible_objects:
			if obj.type == 'MESH' and "VisionHDR" not in obj.data.name:
				yield (obj, obj.matrix_world.copy())

#---Cast the ray
	def obj_ray_cast(obj, matrix):
	#---Get the ray relative to the object
		matrix_inv = matrix.inverted()
		ray_origin_obj = matrix_inv * ray_origin
		ray_target_obj = matrix_inv * ray_target
		ray_direction_obj = ray_target_obj - ray_origin_obj

	#---Cast the ray
		success, hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

		return	success, hit, normal

#---Find the closest object
	best_length_squared = ray_max * ray_max

#---Position of the light from the object
	for obj, matrix in visible_objects_and_duplis():
		i = 1

		success, hit, normal = obj_ray_cast(obj, matrix)

		if success :
		#---Define direction based on the normal of the object or the view angle
			if self.reflect_angle == "Normal" and (i == 1): 
				direction = (normal * matrix.inverted())
			else:
				direction = (view_vector).reflect(normal * matrix.inverted())
			
		#---Define range
			hit_world = (matrix * hit) + ((distance * .2) * direction)

			length_squared = (hit_world - ray_origin).length_squared

			if length_squared < best_length_squared:
				best_length_squared = length_squared
				self.matrix = matrix
				self.hit = hit
				self.hit_world = hit_world
				self.direction = direction
				self.target_name = obj.name
				rotation = obj.rotation_euler.to_quaternion()

			#---Parent the light to the target object
				light.parent = obj
				light.matrix_parent_inverse = obj.matrix_world.inverted()
				
#---Define location, rotation and scale
	if length_squared > 0 :
		rotaxis = (self.direction.to_track_quat('Z','Y')).to_euler()
		light['hit'] = (self.matrix * self.hit)
		light['dir'] = self.direction

	#---Rotation	
		light.rotation_euler = rotaxis

	#---Lock the rotation of the sun on the selected pixel
		if light.VisionHDR.rotation_lock_sun:
			light.rotation_euler.x = -math.radians(light.VisionHDR.hdri_rotationy)
			
		if light.VisionHDR.rotation_lock_img or light.VisionHDR.back_reflect:
			light.VisionHDR.img_rotation = light.VisionHDR.img_pix_rot + math.degrees(light.rotation_euler.z)
		else:
			light.VisionHDR.hdri_rotation = light.VisionHDR.hdri_pix_rot + math.degrees(light.rotation_euler.z)

	#---Location
		light.location = Vector((self.hit_world[0], self.hit_world[1], self.hit_world[2]))

#########################################################################################################

#########################################################################################################
def create_light_env(self, context):
	"""Cycles material nodes for the environment light"""
	
#---Create a new world if not exist
	world = ""
	for w in bpy.data.worlds:
		if w.name == "VisionHDR_world":
			world = bpy.data.worlds['VisionHDR_world']
			
	if world == "":
		bpy.context.scene.world = bpy.data.worlds.new("VisionHDR_world")
		world = bpy.context.scene.world

	world.use_nodes= True
	world.node_tree.nodes.clear() 
	cobj = bpy.context.object	

#---Use multiple importance sampling for the world
	context.scene.world.cycles.sample_as_light = True

#---Texture Coordinate
	coord = world.node_tree.nodes.new(type = 'ShaderNodeTexCoord')
	coord.location = (-1660.0, 220.0)
		
#---Mapping Node HDRI
	textmap = world.node_tree.nodes.new(type="ShaderNodeMapping")
	textmap.vector_type = "POINT"
	world.node_tree.links.new(coord.outputs[0], textmap.inputs[0])
	textmap.location = (-1480.0, 440.0)

#---Mapping Node Reflection
	textmap2 = world.node_tree.nodes.new(type="ShaderNodeMapping")
	textmap2.vector_type = "POINT"
	world.node_tree.links.new(coord.outputs[0], textmap2.inputs[0])
	textmap2.location = (-1480.0, 100.0)

#-> Blur from  Bartek Skorupa : Source https://www.youtube.com/watch?v=kAUmLcXhUj0&feature=youtu.be&t=23m58s
#---Noise Texture
	noisetext = world.node_tree.nodes.new(type="ShaderNodeTexNoise")
	noisetext.inputs[1].default_value = 1000
	noisetext.inputs[2].default_value = 16
	noisetext.inputs[3].default_value = 200
	noisetext.location = (-1120.0, -60.0)

#---Substract
	substract = world.node_tree.nodes.new(type="ShaderNodeMixRGB")
	substract.blend_type = 'SUBTRACT'
	substract.inputs[0].default_value = 1
	world.node_tree.links.new(noisetext.outputs[0], substract.inputs['Color1'])
	substract.location = (-940.0, -60.0)

#---Add
	add = world.node_tree.nodes.new(type="ShaderNodeMixRGB")
	add.blend_type = 'ADD'
	add.inputs[0].default_value = 0
	world.node_tree.links.new(textmap2.outputs[0], add.inputs['Color1'])
	world.node_tree.links.new(substract.outputs[0], add.inputs['Color2'])
	add.location = (-760.0, 100.0)

#-> End Blur

#---Environment Texture 
	envtext = world.node_tree.nodes.new(type = 'ShaderNodeTexEnvironment')
	world.node_tree.links.new(textmap.outputs[0], envtext.inputs[0])
	envtext.location = (-580,380)

#---Bright / Contrast
	bright = world.node_tree.nodes.new(type = 'ShaderNodeBrightContrast')
	world.node_tree.links.new(envtext.outputs[0], bright.inputs[0])
	bright.location = (-400,340)

#---Gamma
	gamma = world.node_tree.nodes.new(type = 'ShaderNodeGamma')
	world.node_tree.links.new(bright.outputs[0], gamma.inputs[0])
	gamma.location = (-220,320)

#---Hue / Saturation / Value
	hue = world.node_tree.nodes.new(type = 'ShaderNodeHueSaturation')
	world.node_tree.links.new(gamma.outputs[0], hue.inputs[4])
	hue.location = (-40,340)
	
#---Reflection Texture 
	imagtext = world.node_tree.nodes.new(type = 'ShaderNodeTexEnvironment')
	world.node_tree.links.new(add.outputs[0], imagtext.inputs[0])
	imagtext.location = (-580,100)

#---Bright / Contrast
	bright2 = world.node_tree.nodes.new(type = 'ShaderNodeBrightContrast')
	world.node_tree.links.new(imagtext.outputs[0], bright2.inputs[0])
	bright2.location = (-400,40)

#---Gamma
	gamma2 = world.node_tree.nodes.new(type = 'ShaderNodeGamma')
	world.node_tree.links.new(bright2.outputs[0], gamma2.inputs[0])
	gamma2.location = (-220,40)

#---Hue / Saturation / Value
	hue2 = world.node_tree.nodes.new(type = 'ShaderNodeHueSaturation')
	world.node_tree.links.new(gamma2.outputs[0], hue2.inputs[4])
	hue2.location = (-40,40)
	
#---Light path 
	lightpath = world.node_tree.nodes.new(type = 'ShaderNodeLightPath')
	lightpath.location = (-40,620)
	
#---Math 
	math = world.node_tree.nodes.new(type = 'ShaderNodeMath')
	math.use_clamp = True
	math.operation = 'SUBTRACT'
	world.node_tree.links.new(lightpath.outputs[0], math.inputs[0])
	world.node_tree.links.new(lightpath.outputs[3], math.inputs[1])
	math.location = (160,560)
				
#---Background 01
	background1 = world.node_tree.nodes.new(type = 'ShaderNodeBackground')
	background1.inputs[0].default_value = (0.8,0.8,0.8,1.0)
	background1.location = (160,280)
	background1.name = "VisionHDR_Background1"
		
#---Background 02
	background2 = world.node_tree.nodes.new(type = 'ShaderNodeBackground')
	background2.location = (160,180)
	background2.name = "VisionHDR_Background2"
	
#---Mix Shader Node
	mix = world.node_tree.nodes.new(type="ShaderNodeMixShader")
	world.node_tree.links.new(math.outputs[0], mix.inputs[0])
	world.node_tree.links.new(background1.outputs[0], mix.inputs[1])
	world.node_tree.links.new(background2.outputs[0], mix.inputs[2])
	mix.location = (340,320)
	
#---Output
	output = world.node_tree.nodes.new("ShaderNodeOutputWorld") 
	output.location = (520,300)
	
#---Links
	world.node_tree.links.new(background1.outputs[0], output.inputs[0])

	lamp = create_light_sun(self, context)

	return(lamp)

#########################################################################################################

#########################################################################################################
def create_light_sun(self, context):
	"""Create a blender light sun"""
	
	lamp_found = False
	
#---Check if the lamp already exist
	for lamp in bpy.data.lamps:	
		if lamp.name == "VisionHDR_LAMP" :
			lamp_found = True
			try:
				lamp = bpy.data.objects['VisionHDR_LAMP']
			except:
				bpy.data.objects.new('VisionHDR_LAMP', lamp)
			lamp.select = True
			break

	
#---Create the sun lamp
	if not lamp_found:
		bpy.ops.object.lamp_add(type='SUN', view_align=False, location=(0,0,0))
		lamp = context.object
		context.active_object.data.name = "VisionHDR_LAMP" 
		lamp = context.object
		lamp.name = "VisionHDR_LAMP"
	
#---Initialize MIS / Type / Name
	lamp.data.cycles.use_multiple_importance_sampling = True
	lamp.VisionHDR.lightname = context.active_object.data.name
	
#---Make the lamp sun object active
	bpy.context.scene.objects.active = bpy.data.objects[lamp.name]
	
#---Create nodes	
	create_lamp_nodes(self, context, lamp)
	
	return(lamp)

#########################################################################################################

#########################################################################################################
def create_lamp_nodes(self, context, lamp):
	"""Cysles material nodes for blender lights"""
	
#---Emission
	emit = lamp.data.node_tree.nodes["Emission"]
	emit.inputs[1].default_value = lamp.VisionHDR.sun_energy
	emit.location = (120.0, 320.0)	

#########################################################################################################

#########################################################################################################
class EditLight(bpy.types.Operator):
	"""Edit the light : Interactive mode"""
	
	bl_description = "Edit the light :\n"+\
					 "- Target a new location\n- Rotate\n- Scale\n- Transform to grid"
	bl_idname = "object.edit_light"
	bl_label = "Add Light"
	bl_options = {'REGISTER', 'UNDO'}

	#-------------------------------------------------------------------
	modif = bpy.props.BoolProperty(default=False)
	editmode = bpy.props.BoolProperty(default=False)
	scale_light = bpy.props.BoolProperty(default=False)
	strength_light = bpy.props.BoolProperty(default=False)
	act_light = bpy.props.StringProperty()
	lmb = False
	falloff_mode = False	
	offset = FloatVectorProperty(name="Offset", size=3,)
	reflect_angle = bpy.props.StringProperty()
	#-------------------------------------------------------------------

	def check(self, context):
		return True

	def check_region(self,context,event):
		if context.area != None:
			if context.area.type == "VIEW_3D" :
				t_panel = context.area.regions[1]
				n_panel = context.area.regions[3]
				view_3d_region_x = Vector((context.area.x + t_panel.width, context.area.x + context.area.width - n_panel.width))
				view_3d_region_y = Vector((context.region.y, context.region.y+context.region.height))
				
				if (event.mouse_x > view_3d_region_x[0] and event.mouse_x < view_3d_region_x[1] and event.mouse_y > view_3d_region_y[0] and event.mouse_y < view_3d_region_y[1]): # or self.modif is True:
					self.in_view_3d = True
				else:
					self.in_view_3d = False
			else:
				self.in_view_3d = False			
			
	def modal(self, context, event):
		#-------------------------------------------------------------------
		coord = (event.mouse_region_x, event.mouse_region_y)
		context.area.tag_redraw()
		obj_light = context.active_object
		#-------------------------------------------------------------------

	#---Find the limit of the view3d region
		self.check_region(context,event)
		try:
		#---Called from Edit icon
			if self.in_view_3d and context.area == self.visionHDR_area:
			
				self.rv3d = context.region_data
				self.region = context.region			
					
			#---Allow navigation
				
				if event.type in {'MIDDLEMOUSE'} or event.type.startswith("NUMPAD"): 
					return {'PASS_THROUGH'}
					
			#---Zoom Keys
				if (event.type in  {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and not 
				   (event.ctrl or event.shift or event.alt)):
					return{'PASS_THROUGH'}			
					
				if event.type == 'LEFTMOUSE':
					self.lmb = event.value == 'PRESS'
				
				if event.value == 'RELEASE':
					context.window.cursor_modal_set("DEFAULT")
					
			#---RayCast the light
				if self.editmode and not self.modif: 
					if self.lmb : 
						raycast_light(self, context, coord)
						bpy.context.window.cursor_modal_set("SCROLL_XY")

			else:
				return {'PASS_THROUGH'}

		#---Undo before creating the light
			if event.type in {'RIGHTMOUSE', 'ESC'}:
				context.area.header_text_set()
				context.window.cursor_modal_set("DEFAULT")
				self.remove_handler()
				return{'FINISHED'}
			
		#---Transform the light
			if self.editmode :
				obj_light = context.active_object
				text_header = "Left click to control position. Right click to confirm"
				context.area.header_text_set(text_header)
				return {'RUNNING_MODAL'}

			return {'PASS_THROUGH'}
			
		except Exception as error:
			if event.type not in {'RIGHTMOUSE', 'ESC'}:
				print("(EditLight) Error to report : ", error)
				context.window.cursor_modal_set("DEFAULT")
				context.area.header_text_set()
				self.remove_handler()
			return {'FINISHED'}

	def execute (self, context):
		for ob in context.scene.objects:
			if ob.type != 'EMPTY' and ob.data.name.startswith("VisionHDR"):
				ob.select = False
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		row = layout.row(align = True)
		row1 = row.split(align=True)
		row1.label("Shading")
		row2 = row.split(align=True)
		
	def remove_handler(self):

		if self._handle_2d is not None:
			bpy.types.SpaceView3D.draw_handler_remove(self._handle_2d, 'WINDOW')
			self._handle_2d = None
		if self._handle_3d is not None:
			bpy.types.SpaceView3D.draw_handler_remove(self._handle_3d, 'WINDOW')
			self._handle_3d = None
		
	@classmethod
	def poll(cls, context):
		return context.area.type == 'VIEW_3D' and context.mode == 'OBJECT'
		
	def invoke(self, context, event):

		if context.space_data.type == 'VIEW_3D':

			args = (self, context, event)
			context.area.header_text_set("Add light: CTRL+LMB || Confirm: ESC or RMB")
			if self.editmode:
				context.scene.objects.active = bpy.data.objects[self.act_light] 
				context.area.header_text_set("Left click to control position. Right click to confirm")
			obj_light = context.active_object
			
			if self.modif:
				self.first_mouse_x = event.mouse_x
				lamp_or_softbox = get_lamp(context, obj_light.VisionHDR.lightname)
				self.save_energy = (lamp_or_softbox.scale[0] * lamp_or_softbox.scale[1]) * obj_light.VisionHDR.energy
				
			self.visionHDR_area = context.area
							
			if obj_light is not None and obj_light.type != 'EMPTY' and obj_light.data.name.startswith("VisionHDR") and self.editmode:
				for ob in context.scene.objects:
					if ob.type != 'EMPTY' : 
						ob.select = False
						
				obj_light.select = True
				self.direction = obj_light.rotation_euler
				self.hit_world = obj_light.location
				obj_light['pixel_select'] = False

			context.window_manager.modal_handler_add(self)
			self._handle_3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')
			self._handle_2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, args, 'WINDOW', 'POST_PIXEL')
			return {'RUNNING_MODAL'}
		else:
			self.report({'WARNING'}, "No active View3d detected !")
			return {'CANCELLED'}
	

#########################################################################################################

#########################################################################################################
class AddLightEnv(bpy.types.Operator):
	bl_idname = "scene.addlightenv"
	bl_label = "Add a new environment"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		create_light_env(self, context)

		return {'FINISHED'}
		
#########################################################################################################

#########################################################################################################
def reset_options(self, context):
	"""Reset the options for HDRI or reflection maps"""
	
	for ob in bpy.data.objects:
		if ob.data.name == self.lightname:
			cobj = ob
	
#---Environment Light
	world = context.scene.world
	hdri_bright = world.node_tree.nodes['Bright/Contrast']
	hdri_gamma = world.node_tree.nodes['Gamma']
	hdri_hue = world.node_tree.nodes['Hue Saturation Value']
	img_bright = world.node_tree.nodes['Bright/Contrast.001']
	img_gamma = world.node_tree.nodes['Gamma.001']
	img_hue = world.node_tree.nodes['Hue Saturation Value.001']				
	
	
	if cobj.VisionHDR.hdri_reset:
		cobj.VisionHDR.hdri_bright = hdri_bright.inputs['Bright'].default_value = 0
		cobj.VisionHDR.hdri_contrast = hdri_bright.inputs['Contrast'].default_value = 0
		cobj.VisionHDR.hdri_gamma = hdri_gamma.inputs['Gamma'].default_value = 1
		cobj.VisionHDR.hdri_hue = hdri_hue.inputs['Hue'].default_value = 0.5
		cobj.VisionHDR.hdri_saturation = hdri_hue.inputs['Saturation'].default_value = 1
		cobj.VisionHDR.hdri_value = hdri_hue.inputs['Value'].default_value = 1
		
	if cobj.VisionHDR.img_reset:
		cobj.VisionHDR.img_bright = img_bright.inputs['Bright'].default_value = 0
		cobj.VisionHDR.img_contrast = img_bright.inputs['Contrast'].default_value = 0
		cobj.VisionHDR.img_gamma = img_gamma.inputs['Gamma'].default_value = 1
		cobj.VisionHDR.img_hue = img_hue.inputs['Hue'].default_value = 0.5
		cobj.VisionHDR.img_saturation = img_hue.inputs['Saturation'].default_value = 1
		cobj.VisionHDR.img_value = img_hue.inputs['Value'].default_value = 1

#########################################################################################################

#########################################################################################################
def update_rotation_hdri(self, context):
	"""Update the rotation of the environment image texture"""
	
	cobj = get_object(context, self.lightname)
	world = context.scene.world
	mapping = world.node_tree.nodes['Mapping']
	mapping2 = world.node_tree.nodes['Mapping.001']
	
	if cobj.VisionHDR.rotation_lock_hdri:
		mapping2.rotation[2] -= (mapping.rotation[2] + math.radians(cobj.VisionHDR.hdri_rotation))

	mapping.rotation[2] = -math.radians(cobj.VisionHDR.hdri_rotation)
	
#---Lock the rotation of the sun on the selected pixel
	if cobj.VisionHDR.rotation_lock_sun:
		cobj.rotation_euler.z = math.radians(cobj.VisionHDR.hdri_rotation - cobj.VisionHDR.hdri_pix_rot)
#########################################################################################################

#########################################################################################################
def update_rotation_hdri_lock(self, context):
	"""Lock / Unlock the rotation of the environment image texture"""
	
	cobj = get_object(context, self.lightname)
	world = context.scene.world
	mapping = world.node_tree.nodes['Mapping']
	mapping2 = world.node_tree.nodes['Mapping.001']
	
	if cobj.VisionHDR.rotation_lock_hdri == False:
		if round(-math.degrees(mapping2.rotation[2]), 2) != round(cobj.VisionHDR.img_rotation, 2) :
			cobj.VisionHDR.img_rotation = -math.degrees(mapping2.rotation[2])

#########################################################################################################

#########################################################################################################
def update_rotation_img(self, context):
	"""Update the rotation of the background image texture"""

	cobj = get_object(context, self.lightname)
	world = context.scene.world
	mapping = world.node_tree.nodes['Mapping']
	mapping2 = world.node_tree.nodes['Mapping.001']
	if cobj.VisionHDR.rotation_lock_img:
		mapping.rotation[2] -= (mapping2.rotation[2] + math.radians(cobj.VisionHDR.img_rotation))
	mapping2.rotation[2] = -math.radians(cobj.VisionHDR.img_rotation)
	
#---Lock the rotation of the sun on the selected pixel
	if cobj.VisionHDR.rotation_lock_sun:
		cobj.rotation_euler.z = math.radians(cobj.VisionHDR.img_rotation - cobj.VisionHDR.img_pix_rot)
#########################################################################################################

#########################################################################################################
def update_rotation_img_lock(self, context):
	"""Lock / Unlock the rotatin of the background image texture"""
	
	cobj = get_object(context, self.lightname)
	world = context.scene.world
	mapping = world.node_tree.nodes['Mapping']
	mapping2 = world.node_tree.nodes['Mapping.001']
	
	if cobj.VisionHDR.rotation_lock_img == False:
		if round(-math.degrees(mapping.rotation[2]), 2) != round(cobj.VisionHDR.hdri_rotation, 2) :
			cobj.VisionHDR.hdri_rotation = -math.degrees(mapping.rotation[2])

#########################################################################################################

#########################################################################################################
def update_lamp(self, context):
	"""Update the material nodes of the blender lights"""
	cobj = get_object(context, "VisionHDR_LAMP")
	mat = bpy.data.lamps["VisionHDR_LAMP"]
	emit = mat.node_tree.nodes["Emission"]
	emit.inputs[0].default_value = cobj.VisionHDR.lightcolor
	emit.inputs[1].default_value = cobj.VisionHDR.sun_energy

#########################################################################################################

#########################################################################################################
def update_mat(self, context):
	"""Update the material nodes of the lights"""
	
#---Get the duplivert
	cobj = get_object(context, self.lightname)

	if cobj.type != 'EMPTY' and cobj.data.name.startswith("VisionHDR"):

		if cobj.VisionHDR.hdri_reset == False and cobj.VisionHDR.img_reset == False:
		#---Environment Light
			world = context.scene.world
			env_output = world.node_tree.nodes['World Output']
			env_mix = world.node_tree.nodes['Mix Shader']
			hdr_text = world.node_tree.nodes['Environment Texture']
			hdri_bright = world.node_tree.nodes['Bright/Contrast']
			hdri_gamma = world.node_tree.nodes['Gamma']
			hdri_hue = world.node_tree.nodes['Hue Saturation Value']
			img_text = world.node_tree.nodes['Environment Texture.001']
			img_bright = world.node_tree.nodes['Bright/Contrast.001']
			img_gamma = world.node_tree.nodes['Gamma.001']
			img_hue = world.node_tree.nodes['Hue Saturation Value.001']				
			background1 = world.node_tree.nodes['VisionHDR_Background1']
			background2 = world.node_tree.nodes['VisionHDR_Background2']
			lightpath = world.node_tree.nodes['Light Path']
			math_path = world.node_tree.nodes['Math']
			mix = world.node_tree.nodes['Mix Shader']
			mapping = world.node_tree.nodes['Mapping']
			mapping2 = world.node_tree.nodes['Mapping.001']
				
			if cobj.VisionHDR.hdri_name != "":	
				hdr_text.image = bpy.data.images[cobj.VisionHDR.hdri_name]
				world.node_tree.links.new(hdr_text.outputs[0], hdri_bright.inputs[0])
				world.node_tree.links.new(hdri_hue.outputs[0], background1.inputs[0])
				world.node_tree.links.new(lightpath.outputs[0], math_path.inputs[0])
				world.node_tree.links.new(lightpath.outputs[3], math_path.inputs[1])
				world.node_tree.links.new(math_path.outputs[0], mix.inputs[0])
				hdri_bright.inputs['Bright'].default_value = cobj.VisionHDR.hdri_bright
				hdri_bright.inputs['Contrast'].default_value = cobj.VisionHDR.hdri_contrast
				hdri_gamma.inputs['Gamma'].default_value = cobj.VisionHDR.hdri_gamma
				hdri_hue.inputs['Hue'].default_value = cobj.VisionHDR.hdri_hue
				hdri_hue.inputs['Saturation'].default_value = cobj.VisionHDR.hdri_saturation
				hdri_hue.inputs['Value'].default_value = cobj.VisionHDR.hdri_value
			else:
			#--- Remove image HDRI links
				cobj.VisionHDR.rotation_lock_img = False
				for i in range(len(hdri_hue.outputs['Color'].links)):
					world.node_tree.links.remove(hdri_hue.outputs['Color'].links[i-1])
		
		#---HDRI for background			
			if cobj.VisionHDR.hdri_background:
				world.node_tree.links.new(background1.outputs[0], env_output.inputs[0])

			else:
				world.node_tree.links.new(env_mix.outputs[0], env_output.inputs[0])

		#---Image Background 
			if cobj.VisionHDR.img_name != "" and not cobj.VisionHDR.hdri_background: 
				img_text.image = bpy.data.images[cobj.VisionHDR.img_name]
				world.node_tree.links.new(img_text.outputs[0], background2.inputs[0])
				world.node_tree.links.new(lightpath.outputs[0], math_path.inputs[0])
				world.node_tree.links.new(lightpath.outputs[3], math_path.inputs[1])
				if cobj.VisionHDR.back_reflect:
					math_path.operation = 'ADD'
				else:
					math_path.operation = 'SUBTRACT'
				world.node_tree.links.new(math_path.outputs[0], mix.inputs[0])
				world.node_tree.links.new(img_text.outputs[0], img_bright.inputs[0])
				world.node_tree.links.new(img_hue.outputs[0], background2.inputs[0])
				img_bright.inputs['Bright'].default_value = cobj.VisionHDR.img_bright
				img_bright.inputs['Contrast'].default_value = cobj.VisionHDR.img_contrast
				img_gamma.inputs['Gamma'].default_value = cobj.VisionHDR.img_gamma
				img_hue.inputs['Hue'].default_value = cobj.VisionHDR.img_hue
				img_hue.inputs['Saturation'].default_value = cobj.VisionHDR.img_saturation
				img_hue.inputs['Value'].default_value = cobj.VisionHDR.img_value					
			else:
			#--- Remove image background links
				cobj.VisionHDR.rotation_lock_hdri = False
				for i in range(len(img_hue.outputs['Color'].links)):
					world.node_tree.links.remove(img_hue.outputs['Color'].links[i-1])						
			
			#---Color background for reflection
				if cobj.VisionHDR.back_reflect:
					math_path.operation = 'ADD'
				else:
					math_path.operation = 'SUBTRACT'

		else:
			if cobj.VisionHDR.hdri_reset: 
				cobj.VisionHDR.hdri_reset = False
			if cobj.VisionHDR.img_reset: 
				cobj.VisionHDR.img_reset = False						

#########################################################################################################

#########################################################################################################
def get_object(context, lightname):
	"""Return the object with this name"""

	for ob in context.scene.objects:
		if ob.type != 'EMPTY' and ob.VisionHDR.lightname == lightname:
			cobj = ob

	return(cobj)

#########################################################################################################

#########################################################################################################
def get_lamp(context, lightname):
	"""Return the lamp with this name"""
	
	cobj = get_object(context, lightname)
	for ob in context.scene.objects:
		if ob.type != 'EMPTY' and ob.data.name == "WORLD_" + cobj.data.name :
			cobj = ob
	return(cobj)


#########################################################################################################

#########################################################################################################
class SelectPixel(Operator):
	"""Align the environment background with the selected pixel"""
	
	bl_idname = "object.select_pixel"
	bl_description = "Target the selected pixel from the image texture and compute the rotation.\n"+\
					 "Use this to align a sun or a lamp from your image."
	bl_label = "Select pixel"
	act_light = bpy.props.StringProperty()
	img_name = bpy.props.StringProperty()
	img_type = bpy.props.StringProperty()
	img_size_x = bpy.props.FloatProperty()
	img_size_y = bpy.props.FloatProperty()

	def remove_handler(self):
		if self._handle is not None:
			bpy.types.SpaceImageEditor.draw_handler_remove(self._handle, 'WINDOW')
		self._handle = None

	def check_region(self,context,event):
		if context.area != None:
			for region in self.visionHDR_area.regions:
				if(region.type == "WINDOW" and 
					region.x <= event.mouse_x < region.x + region.width and
					region.y <= event.mouse_y < region.y + region.height):
					self.in_view_editor = True
					print("TRUE")
				else:
					self.in_view_editor = False
					print("FALSE")

				
	def execute(self, context):
		if self.act_light != "": 
			context.scene.objects.active = bpy.data.objects[self.act_light] 
			obj_light = context.active_object
		else:
			obj_light = context.active_object
		obj_light['pixel_select'] = True
		context.area.spaces.active.image = bpy.data.images[self.img_name]
		bpy.data.images[self.img_name].use_view_as_render = True

  
	def modal(self, context, event):
		context.area.tag_redraw()
		
	#---Find the limit of the view3d region
		self.check_region(context,event)
		try:
			if self.in_view_editor and context.area == self.visionHDR_area:
				
			#---Allow navigation
				if event.type in {'MIDDLEMOUSE'} or event.type.startswith("NUMPAD"): 
					return {'PASS_THROUGH'}
					
			#---Zoom Keys
				elif (event.type in	 {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and not 
				   (event.ctrl or event.shift or event.alt)):
					return{'PASS_THROUGH'}	
			
				elif event.type == 'MOUSEMOVE':
					for region in self.visionHDR_area.regions:

						if region.type == 'WINDOW':
							context.window.cursor_modal_set("EYEDROPPER")
							mouse_x = event.mouse_x - region.x
							mouse_y = event.mouse_y - region.y
							uv = region.view2d.region_to_view(mouse_x, mouse_y)
						#--- Source : https://blenderartists.org/forum/showthread.php?292866-Pick-the-color-of-a-pixel-in-the-Image-Editor
							if not math.isnan(uv[0]): 
								x = int(self.img_size_x * uv[0]) % self.img_size_x
								y = int(self.img_size_y * uv[1]) % self.img_size_y
								self.mouse_path = (x,y)

				elif event.type == 'LEFTMOUSE':
					return{'PASS_THROUGH'}	

				elif event.type == 'RIGHTMOUSE':
					obj_light = bpy.data.objects[self.act_light]
					rot_x = ((self.mouse_path[0] * 360) / self.img_size_x) - 90
					rot_y = ((self.mouse_path[1] * 180) / self.img_size_y)
					if self.img_type == "HDRI":
						obj_light.VisionHDR.hdri_rotation = rot_x - 180 + math.degrees(obj_light.rotation_euler.z)
						obj_light.VisionHDR.hdri_rotationy = rot_y - 180
						obj_light.VisionHDR.hdri_pix_rot = rot_x - 180
						obj_light.VisionHDR.hdri_pix_roty = rot_y - 180
					else:
						obj_light.VisionHDR.img_rotation = rot_x - 180 + math.degrees(obj_light.rotation_euler.z)
						obj_light.VisionHDR.img_pix_rot = rot_x - 180				

					bpy.context.window.cursor_modal_set("DEFAULT")
					self.remove_handler()
					if context.area.type == 'IMAGE_EDITOR':
						context.area.type = 'VIEW_3D'
					return {'FINISHED'}
					
				elif event.type == 'ESC':
					bpy.context.window.cursor_modal_set("DEFAULT")
					context.area.header_text_set()
					self.remove_handler()
					if context.area.type == 'IMAGE_EDITOR':
						context.area.type = 'VIEW_3D'	
					return {'CANCELLED'}
					
				return {'RUNNING_MODAL'}
				
			else:
				return{'PASS_THROUGH'}	
				
		except Exception as error:
			print("(SCENE_OT_select_pixel) Error to report : ", error)	
			bpy.context.window.cursor_modal_set("DEFAULT")
			context.area.header_text_set()
			self.remove_handler()

			return {'FINISHED'}
	

	def invoke(self, context, event):
		self.mouse_path = [0,0]
		if context.space_data.type == 'VIEW_3D':
			context.area.type = 'IMAGE_EDITOR'
			t_panel = context.area.regions[2]
			n_panel = context.area.regions[3]
			self.view_3d_region_x = Vector((context.area.x + t_panel.width, context.area.x + context.area.width - n_panel.width))

			self.execute(context)
			self.img_size = [self.img_size_x, self.img_size_y]
			args = (self, context, event)
			self.visionHDR_area = context.area

			context.window_manager.modal_handler_add(self)
			self._handle = bpy.types.SpaceImageEditor.draw_handler_add(draw_target_px, args, 'WINDOW', 'POST_PIXEL')
	
		
		return {'RUNNING_MODAL'}
				
#########################################################################################################

#########################################################################################################
class ActiveWorld(Operator):
	"""Make VisionHDR the active world if exist"""
	
	bl_idname = "scene.active_world"
	bl_label = "Active VisionHDR world"

	def execute(self, context):
		bpy.context.scene.world = bpy.data.worlds['VisionHDR_world']
		return {'FINISHED'}
#########################################################################################################

#########################################################################################################
class ActiveLamp(Operator):
	"""Make VisionHDR the active world if exist"""
	
	bl_idname = "scene.active_lamp"
	bl_label = "Active VisionHDR sun lamp"

	def execute(self, context):
		light_obj = bpy.data.objects.new('VisionHDR_LAMP', bpy.data.lamps['VisionHDR_LAMP'])
		bpy.context.scene.objects.link(light_obj)
		return {'FINISHED'}


#########################################################################################################

#########################################################################################################	

class VisionHDRObj(bpy.types.PropertyGroup):
#---Name of the light
	lightname = StringProperty(
							   name="LightName",
							   description="Light name.",)	
							   
#---A short description of the light for import / export
	definition = StringProperty(
							   name="Description",
							   description="Description.",) 

#---Strength of the sun
	sun_energy = FloatProperty(
						   name="Sun Strength",
						   description="Strength of the light.",
						   min=0.000, max=9000000000.0,
						   soft_min=0.0, soft_max=100.0,
						   default=0,
						   precision=3,
						   subtype='NONE',
						   unit='NONE',
						   update=update_lamp)
						   
#---Strength of the light
	env_energy = FloatProperty(
						   name="Env Strength",
						   description="Strength of the environment.",
						   min=0.000, max=9000000000.0,
						   soft_min=0.0, soft_max=100.0,
						   default=1,
						   precision=3,
						   subtype='NONE',
						   unit='NONE',
						   update=update_mat)

#---Base Color of the light
	lightcolor = FloatVectorProperty(	
									 name = "",
									 description="Base Color of the light.",
									 subtype = "COLOR",
									 size = 4,
									 min = 0.0,
									 max = 1.0,
									 default = (0.8,0.8,0.8,1.0),
									 update=update_lamp) 

#---Compute the reflection angle from the normal of the target or from the view of the screen.
	reflect_angle = EnumProperty(name="Reflection",
						  description="Compute the light position from the angle view or the normal of the object.\n"+\
						  "- View	: The light will be positioned from the angle of the screen 3dView and the target face of the object.\n"+\
						  "- Normal : The light will be positioned in parralel to the normal of the face of the targeted object.\n"+\
						  "Selected",
						  items=(
						  ("0", "View", "", 0),
						  ("1", "Normal", "", 1),
						  ),
						  default="0")

#---List of panels options 
	options_type = EnumProperty(name="", 
								description="List of panels options.\nSelected",
								items=(
								("Options", "Options", "", 0),
								("Environment", "Environment", "", 1),
								("Sun", "Sun", "", 2),
								), 
								default="Options")	


#---Name of the environment image texture
	hdri_name = StringProperty(
							   name="HDRI", 
							   description="Name of the environment image texture.",
							   update=update_mat)

#---Rotation of the environment image on Z axis.
	hdri_rotation = FloatProperty(
								  name="HDRI Rotation",
								  description="Rotation of the environment image on Z axis.",
								  min= -360, max= 360,
								  default=0,
								  update=update_rotation_hdri)	

#---Rotation of the environment image on Y axis.
	hdri_rotationy = FloatProperty(
								  name="HDRI Rotation",
								  description="Rotation of the environment image on Y axis.",
								  min= -360, max= 360,
								  default=0,
								  update=update_rotation_hdri)

#---Rotation on X axis computed from the selected pixel of the image texture
	hdri_pix_rot = FloatProperty(
								 name="Target pixel for rotation on X axis",
								 description="Rotation computed from the selected pixel of the image texture.",
								 min= -360, max= 360,
								 default=0) 

#---Rotation on Y axis computed from the selected pixel of the image texture
	hdri_pix_roty = FloatProperty(
								 name="Target pixel for rotation on Y axis",
								 description="Rotation on Y axis computed from the selected pixel of the image texture.",
								 min= -360, max= 360,
								 default=0)

#---Expand the environment image options.	
	hdri_expand = BoolProperty(
							   name="Environment image options",
							   description="Expand the environment image options",
							   default=False)

#---Use the environment image texture as background and/or reflection
	hdri_background = BoolProperty(
							 description="Use the environment image texture as background / reflection\n"+
							 "Disable this if you want to use another image / color background as background and/or reflection.",
							 default=True,
							 update=update_mat) 

#---Use the image background for reflection
	back_reflect = BoolProperty(
							 description="Use the image background for reflection.",
							 default=False,
							 update=update_mat)

#---Lock the rotation of the reflection map and use the rotation of the HDRI.
	rotation_lock_hdri = BoolProperty(
									  description="Lock the rotation of the reflection map.\n"+
									  "The reflection map will rotate accordingly to the rotation of the environment map.",
									  default=False,
									  update=update_rotation_hdri_lock)

#---Lock the rotation of the HDRI map and use the rotation of the reflection map.
	rotation_lock_img = BoolProperty(
									 description="Lock the rotation of the environment map.\n"+
									 "The environment map will rotate accordingly to the rotation of the reflection map.",
									 default=False,
									 update=update_rotation_img_lock)
									 
#---Lock the rotation of the Sun.
	rotation_lock_sun = BoolProperty(
									 description="Lock the rotation of the sun.\n"+
									 "The sun will rotate accordingly to the rotation of the slected pixel in the image.",
									 default=True,
									 )

#---Reset the modifications of the image modifications.
	hdri_reset = BoolProperty(
							  name="Reset",
							  description="Reset the modifications of the environment image modifications.",
							  default=False,
							  update=reset_options)

#---Brightness of the environment image.
	hdri_bright = FloatProperty(
								name="Bright",
								description="Increase the overall brightness of the image.",
								min=-10, max=10.0,
								default=0,
								precision=2,
								update=update_mat)						

#---Contrast of the environment image.
	hdri_contrast = FloatProperty(
								  name="Contrast",
								  description="Make brighter pixels brighter, but keeping the darker pixels dark.",
								  min=-10, max=10.0,
								  default=0,
								  precision=2,
								  subtype='NONE',
								  unit='NONE',
								  update=update_mat) 

#---Gamma of the environment image.
	hdri_gamma = FloatProperty(
							   name="Gamma",
							   description="Apply an exponential brightness factor to the image.",
							   min=0, max=10.0,
							   default=1,
							   precision=2,
							   subtype='NONE',
							   unit='NONE',
							   update=update_mat) 

#---Hue of the environment image.
	hdri_hue = FloatProperty(
							 name="Hue",
							 description="Specifies the hue rotation of the image from 0 to 1.",
							 min=0, max=1.0,
							 default=0.5,
							 precision=2,
							 subtype='NONE',
							 unit='NONE',
							 update=update_mat) 

#---Saturation of the environment image.
	hdri_saturation = FloatProperty(
									name="Saturation",
									description="A saturation of 0 removes hues from the image, resulting in a grayscale image.\n"+\
									"A shift greater 1.0 increases saturation.",
									min=0, max=2.0,
									default=1,
									precision=2,
									subtype='NONE',
									unit='NONE',
									update=update_mat) 

#---Value of the environment image.
	hdri_value = FloatProperty(
							   name="Value",
							   description="Value is the overall brightness of the image.\n"+\
							   "De/Increasing values shift an image darker/lighter.",
							   min=0, max=2.0,
							   default=1,
							   precision=2,
							   subtype='NONE',
							   unit='NONE',
							   update=update_mat) 

#---Name of the background image texture
	img_name = StringProperty(
							  name="Name of the background / reflection image texture",
							  update=update_mat)

#---Background rotation on X axis
	img_rotation = FloatProperty(
								 name="Reflection Rotation",
								 description="Reflection Rotation",
								 min= -360, max= 360,
								 default=0,
								 update=update_rotation_img)

#---Rotation on X axis computed from the selected pixel of the image texture
	img_pix_rot = FloatProperty(
								 name="Background brightest pixel Rotation",
								 description="Rotation computed from the selected pixel of the image texture.",
								 min= -360, max= 360,
								 default=0) 

#---Expand the background image options.							 
	img_expand = BoolProperty(
							  name="options",
							  description="Expand the background image options.",
							  default=False)

#---Reset the modifications of the image modifications.
	img_reset = BoolProperty(
							 name="Reset",
							 description="Reset the modifications of the background image modifications.",
							 default=False,
							 update=reset_options)

#---Brightness of the background image. 
	img_bright = FloatProperty(
							   name="Bright",
							   description="Increase the overall brightness of the image.",
							   min=-10, max=10.0,
							   default=0,
							   precision=2,
							   update=update_mat)						

#---Contrast of the background image.
	img_contrast = FloatProperty(
								 name="Contrast",
								 description="Make brighter pixels brighter, but keeping the darker pixels dark.",
								 min=-10, max=10.0,
								 default=0,
								 precision=2,
								 subtype='NONE',
								 unit='NONE',
								 update=update_mat) 

#---Gamma of the background image.
	img_gamma = FloatProperty(
							  name="Gamma",
							  description="Apply an exponential brightness factor to the image.",
							  min=0, max=10.0,
							  default=1,
							  precision=2,
							  subtype='NONE',
							  unit='NONE',
							  update=update_mat) 

#---Hue of the background image.
	img_hue = FloatProperty(
							name="Hue",
							description="Specifies the hue rotation of the image from 0 to 1.",
							min=0, max=1.0,
							default=0.5,
							precision=2,
							subtype='NONE',
							unit='NONE',
							update=update_mat) 

#---Saturation of the background image.
	img_saturation = FloatProperty(
								   name="Saturation",
								   description="A saturation of 0 removes hues from the image, resulting in a grayscale image.\n"+\
								   "A shift greater 1.0 increases saturation.",
								   min=0, max=2.0,
								   default=1,
								   precision=2,
								   subtype='NONE',
								   unit='NONE',
								   update=update_mat) 

#---Value of the background image.
	img_value = FloatProperty(
							  name="Value",
							  description="Value is the overall brightness of the image.\n"+\
							  "Increasing values shift an image darker/lighter.",
							  min=0, max=2.0,
							  default=1,
							  precision=2,
							  subtype='NONE',
							  unit='NONE',
							  update=update_mat)  

#########################################################################################################

#########################################################################################################

"""
#########################################################################################################
# ENVIRONMENT MAP + SUN LIGHT
#########################################################################################################
"""
class VisionHDREnvPreferences(bpy.types.Panel):
	"""Creates a Panel in the Object properties window"""
	bl_idname = "view3d.visionHDR"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "VisionHDR"
	bl_label = "VisionHDR"
	bl_context = "objectmode"

	@classmethod
	def poll(cls, context):
		return False

	def draw(self, context):
		layout = self.layout
		cobj = self.cobj
		scene = bpy.context.scene
		active_world = scene.world
		active_world_cycles = bpy.context.scene.world.cycles
		world = bpy.data.worlds[active_world.name].node_tree.nodes
		scene_cycles = bpy.data.scenes[scene.name].cycles
		scene_view = bpy.data.scenes[scene.name].view_settings

	#---Options 
		if cobj.VisionHDR.options_type == "Options" :
			box = self.col
		#---New type light
			box.prop(context.space_data, "show_world", text="Show world", toggle=True)
			col = box.column(align=True)
			row = col.row()
		#---MIS
			row.prop(active_world_cycles, "sample_as_light", text="MIS", toggle=True)
			row = col.row(align=True)	
		#---Map resolution
			row.label(text="Map resolution: ")
			row.prop(active_world_cycles, "sample_map_resolution", text="")
			row = col.row(align=True)	
		#---Samples
			row.label(text="Samples: ")
			row.prop(active_world_cycles, "samples", text="")
			row = col.row(align=True)	
		#---Max bounces
			row.label(text="Max bounces: ")
			row.prop(active_world_cycles, "max_bounces", text="")
			row = col.row(align=True)	
		#---Film Exposure
			row.label(text="Film exposure: ")
			row.prop(scene_cycles, "film_exposure", text="")
			col = box.column(align=True)
			row = col.row(align=True)	
		#---View Exposure
			row.label(text="View Exposure: ")
			row.prop(scene_view, "exposure", text="")
			row = col.row(align=True)	
		#---Color management
			row.label(text="Color management: ")
			row.prop(scene_view, "view_transform", text="")
			row = col.row(align=True)	
		#---Look color
			row.label(text="Look: ")
			row.prop(scene_view, "look", text="")
			row = col.row(align=True)	

			
		elif cobj.VisionHDR.options_type == "Sun":
			box = self.col
			col = box.column(align=True)
			row = col.row(align=True)
			lamp = bpy.data.objects["VisionHDR_LAMP"]
		#---Color
			row.label(text="Color: ")
			row.prop(cobj.VisionHDR, "lightcolor", text='')			
			row = col.row(align=True)	
		#---Energy
			row.label(text="Energy: ")
			row.prop(cobj.VisionHDR, "sun_energy", text='', slider = True)
			row = col.row(align=True)
		#---Size
			row.label(text="Size: ")
			row.prop(lamp.data, "shadow_soft_size", text='', toggle=True)
			row = col.row(align=True)
		#---Bounces
			row.label(text="Bounces: ")
			row.prop(lamp.data.cycles, "max_bounces", text='', toggle=True)
			col = box.column(align=True)
			row = col.row(align=True)
		#---Lock Rotation
			row.label(text="Lock rotation: ")
			row.prop(cobj.VisionHDR, "rotation_lock_sun", text='')
			col = box.column(align=True)
			row = col.row(align=True)
		#---MIS/Shadows/Diffuse/Specular
			row.prop(lamp.data.cycles, "use_multiple_importance_sampling", text='MIS', toggle=True)
			row.prop(lamp.data.cycles, "cast_shadow", text='Shadow', toggle=True)
			row.prop(lamp.cycles_visibility, "diffuse", text='Diff', toggle=True)
			row.prop(lamp.cycles_visibility, "glossy", text='Spec', toggle=True)

	#---Material
		elif cobj.VisionHDR.options_type == "Environment":
			box = self.col
			col = box.column(align=True)
			row = col.row(align=True)							
		#---HDRI Texture
			row.label(text="Environment: ")
			if cobj.VisionHDR.hdri_name != "":
				row = col.row(align=True)
				op = row.operator("object.select_pixel", text ='Align to Pixel', icon='EYEDROPPER')
				op.act_light = cobj.name 
				op.img_name = cobj.VisionHDR.hdri_name
				op.img_type = "HDRI"
				op.img_size_x = bpy.data.images[cobj.VisionHDR.hdri_name].size[0]
				op.img_size_y = bpy.data.images[cobj.VisionHDR.hdri_name].size[1]
				
				col = box.column()
				col = box.column(align=True)
				
			row = col.row(align=True)
			row.prop_search(cobj.VisionHDR, "hdri_name", bpy.data, "images", text='', icon='NONE')
			row.operator("image.open",text='', icon='IMASEL')
			row = col.row(align=True)
			
		#---HDRI color
			if cobj.VisionHDR.hdri_name == "":
				hdri_col = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['VisionHDR_Background1'].inputs[0] 
				row.prop(hdri_col, "default_value", text="")
			else:
			#---HDRI Rotation
				if cobj.VisionHDR.rotation_lock_img and cobj.VisionHDR.img_name != "":
					row.enabled = False
				else:
					row.enabled = True
					
				row.prop(cobj.VisionHDR, "hdri_rotation", text="Rotation", slider = True)

				if cobj.VisionHDR.img_name != "" and not cobj.VisionHDR.hdri_background:
					row.prop(cobj.VisionHDR, "rotation_lock_hdri", text="", icon="%s" % "LOCKED" if cobj.VisionHDR.rotation_lock_hdri else "UNLOCKED")
				
				row = col.row(align=True)
			
			#---HDRI options
				row.label(text="Image options:")
				row.prop(cobj.VisionHDR, "hdri_expand", text="")
						
				if cobj.VisionHDR.hdri_expand:
					#---Brightness
						col = box.column(align=True)
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "hdri_bright", text="Bright")
					#---Contrast
						row.prop(cobj.VisionHDR, "hdri_contrast", text="Contrast")
					#---Gamma
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "hdri_gamma", text="Gamma")	
					#---Hue
						row.prop(cobj.VisionHDR, "hdri_hue", text="Hue")	
					#---Saturation
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "hdri_saturation", text="Saturation")			
					#---Value
						row.prop(cobj.VisionHDR, "hdri_value", text="Value")
					#---Mirror / Equirectangular
						row = col.row(align=True)
						hdri_img = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['Environment Texture']
						row.prop(hdri_img, "projection", text="")
					#---Reset values
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "hdri_reset", text="Reset options", toggle=True)
						
		#---Hdri for background
			row = col.row(align=True)
			row.prop(cobj.VisionHDR, "hdri_background", text='Hdri for background', toggle=True)

		#---Background Texture
			if not cobj.VisionHDR.hdri_background:
				col = box.column(align=True)
				row = col.row(align=True)
				row.label(text="Background:")
				if cobj.VisionHDR.img_name != "":
					row = col.row(align=True)
					op = row.operator("object.select_pixel", text ='Align to Pixel', icon='EYEDROPPER')
					op.act_light = cobj.name 
					op.img_name = cobj.VisionHDR.img_name
					op.img_type = "IMG"
					op.img_size_x = bpy.data.images[cobj.VisionHDR.img_name].size[0]
					op.img_size_y = bpy.data.images[cobj.VisionHDR.img_name].size[1]
					col = box.column()
					col = box.column(align=True)
				
				row = col.row(align=True)
				
				row.prop_search(cobj.VisionHDR, "img_name", bpy.data, "images", text="")
				row.operator("image.open",text='', icon='IMASEL')
				row = col.row(align=True)
				
			#---Background color
				if cobj.VisionHDR.img_name == "":
					back_col = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['VisionHDR_Background2'].inputs[0] 
					row.prop(back_col, "default_value", text="")	

				else:
				#---Background Rotation
					if cobj.VisionHDR.rotation_lock_hdri and cobj.VisionHDR.hdri_name != "":
						row.enabled = False
					else:
						row.enabled = True							
					
					row.prop(cobj.VisionHDR, "img_rotation", text="Rotation", slider = True)
					if cobj.VisionHDR.hdri_name != "": 
						row.prop(cobj.VisionHDR, "rotation_lock_img", text="", icon="%s" % "LOCKED" if cobj.VisionHDR.rotation_lock_img else "UNLOCKED")
				
					row = col.row(align=True)
				#---Background options
					row.label(text="Image options:")
					row.prop(cobj.VisionHDR, "img_expand", text="")
					
					if cobj.VisionHDR.img_expand:
					#---Brightness
						col = box.column(align=True)
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "img_bright", text="Bright")
					#---Contrast
						row.prop(cobj.VisionHDR, "img_contrast", text="Contrast")
					#---Gamma
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "img_gamma", text="Gamma")	
					#---Hue
						row.prop(cobj.VisionHDR, "img_hue", text="Hue")	
					#---Saturation
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "img_saturation", text="Saturation")								
					#---Value
						row.prop(cobj.VisionHDR, "img_value", text="Value")
					#---Blur
						row = col.row(align=True)
						reflection_blur = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['Mix.001'].inputs[0] 
						row.prop(reflection_blur, "default_value", text="Blur", slider = True)
					#---Mirror / Equirectangular
						row = col.row(align=True)
						back_img = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['Environment Texture.001']
						row.prop(back_img, "projection", text="")
					#---Reset values
						row = col.row(align=True)
						row.prop(cobj.VisionHDR, "img_reset", text="Reset options", toggle=True)
			
			#---Background for reflection
				row = col.row(align=True)
				row.prop(cobj.VisionHDR, "back_reflect", text='Background for reflection', toggle=True)

"""
#########################################################################################################
# LIGHT PARAMETER
#########################################################################################################
"""
class VisionHDRLightParameterPreferences(bpy.types.Panel):
	"""Creates a Panel in the Object properties window"""
	bl_idname = "view3d.visionHDR"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "VisionHDR"
	bl_label = "VisionHDR"
	bl_context = "objectmode"

	def draw(self, context):
		layout = self.layout
		object = self.object
		row = layout.row(align=True)
		col = row.column(align=True)

		if object.type != 'EMPTY' and object.data.name.startswith("VisionHDR") :
			self.cobj = bpy.context.scene.objects[object.name]
			cobj = bpy.context.scene.objects[object.name]

		#---Edit mode
			col.scale_y = 2
			op = col.operator("object.edit_light", text ='', icon='ACTION_TWEAK')
			op.editmode = True
			op.act_light = cobj.name			

		#---Environment strength
			col = row.column(align=True)
			row = col.row(align=True)
			hdr_back = bpy.data.worlds['VisionHDR_world'].node_tree.nodes['VisionHDR_Background1'].inputs['Strength']	
			row.prop(hdr_back, "default_value", text='Env energy', slider = False)
		
		#---Light Name
			row = col.row(align=True)
			row.prop(cobj.VisionHDR, "sun_energy", text='Sun energy', slider = False)
						
		#---Menu items
			box = layout.box()
			col = box.column(align=True)				
			row = col.row(align=True)
			row.prop(cobj.VisionHDR, "options_type", text=" ", expand=True)
			row = col.row(align=True)
			self.row = row
			self.col = box.column()

		#---Environment Panel Preferences
			VisionHDREnvPreferences.draw(self, context)

							
"""
#########################################################################################################
# UI
#########################################################################################################
"""		
class VisionHDRPreferences(bpy.types.Panel):
	bl_idname = "view3d.visionHDR"
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "VisionHDR"
	bl_label = "VisionHDR"
	bl_context = "objectmode"
	
	def draw(self, context):
		scene = context.scene
		cobj = context.active_object
		layout = self.layout
		row = layout.row(align=True)
		objects_on_layer = []

#----------------------------------
# ADD LIGHTS
#----------------------------------					   
		active_world = ""
		for world in bpy.data.worlds:
			if world.name == "VisionHDR_world":
				active_world = world
				break
				
		if active_world == "":
			row.operator("scene.addlightenv", text="New", icon='BLANK1')
			
		elif context.scene.world == active_world :
			world = bpy.data.worlds[active_world.name].node_tree.nodes
#----------------------------------
# EDIT MODE
#----------------------------------			
						
		#---For each layer
			l = -1	
			for layer in bpy.data.scenes[scene.name].layers:
				l += 1
				light_on_layer = [obj for obj in context.scene.objects if not obj.users_group and  obj.type != 'EMPTY' and obj.layers[l] and layer == True and obj.data.name.startswith("VisionHDR")]
				if layer == True and light_on_layer != []: 
					objects_on_layer.extend(light_on_layer)
				
			"""
			#########################################################################################################
			#########################################################################################################
			# LIGHTS
			#########################################################################################################
			#########################################################################################################
			"""

			if objects_on_layer == [] and bpy.data.lamps["VisionHDR_LAMP"]:
				print("light_on_layer: ", objects_on_layer)
				row.label(text='Sun lamp deleted.')
				row = layout.row(align=True)
				row.operator("scene.active_lamp", text="Active Sun Lamp", icon='BLANK1')
			else:
				for self.object in list(set(objects_on_layer)):
					VisionHDRLightParameterPreferences.draw(self, context)
					cobj = self.cobj
		else:
			row.operator("scene.active_world", text="Active World", icon='BLANK1')
#########################################################################################################

#########################################################################################################

def register():
	
	bpy.utils.register_module(__name__)
	bpy.types.Object.VisionHDR = bpy.props.PointerProperty(type=VisionHDRObj)
	update_panel(None, bpy.context)
	
def unregister():
	del bpy.types.Object.VisionHDR
	bpy.utils.unregister_module(__name__)	
	
if __name__ == "__main__":
	register()
