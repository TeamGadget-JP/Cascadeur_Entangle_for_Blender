bl_info = {
    "name": "Cascadeur Entangle for Blender (CEB)",
    "author": "Team Gadget",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > CEB",
    "description": "Zero Calibration O(1) Entangle, Timeline Sync & Selective Baking",
    "category": "Animation",
}

import bpy
import socket
import struct
import json
import threading
import queue
import mathutils
from bpy.app.handlers import persistent

class CEBSlotProps(bpy.types.PropertyGroup):
    is_active: bpy.props.BoolProperty(name="Active", default=True)
    apply_on_stop: bpy.props.BoolProperty(name="Apply on STOP", default=True, description="Bake the current pose to a keyframe upon stopping")
    is_bake_target: bpy.props.BoolProperty(name="Bake", default=False)
    target_armature: bpy.props.PointerProperty(
        name="Armature", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'ARMATURE'
    )
    root_bone: bpy.props.StringProperty(name="Root", default="")
    pelvis_1: bpy.props.StringProperty(name="Pelvis 1", default="")
    pelvis_2: bpy.props.StringProperty(name="Pelvis 2", default="")
    pelvis_3: bpy.props.StringProperty(name="Pelvis 3", default="")
    has_ss_data: bpy.props.BoolProperty(default=False)
    ss_data_json: bpy.props.StringProperty(default="")

class CEBSceneProps(bpy.types.PropertyGroup):
    is_running: bpy.props.BoolProperty(default=False)
    slots: bpy.props.CollectionProperty(type=CEBSlotProps)
    sync_master: bpy.props.EnumProperty(
        name="Master", items=[('BLENDER', "Blender", ""), ('CASCADEUR', "Cascadeur", "")], default='CASCADEUR'
    )
    sync_enable: bpy.props.BoolProperty(name="Sync Timeline", default=True)
    is_baking: bpy.props.BoolProperty(default=False)
    bake_start: bpy.props.IntProperty(name="Start", default=1, min=0)
    bake_end: bpy.props.IntProperty(name="End", default=100, min=1)
    bake_delay: bpy.props.FloatProperty(name="Bake Delay", default=0.2, min=0.01, max=1.0)

class CEB_PT_MainPanel(bpy.types.Panel):
    bl_label = "CEB Entangle"
    bl_idname = "CEB_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CEB'

    def draw(self, context):
        layout = self.layout
        props = context.scene.ceb_props

        row = layout.row()
        row.scale_y = 1.5
        row.enabled = not props.is_baking
        if not props.is_running:
            row.operator("ceb.start", text="▶ START Entangle", icon='PLAY', depress=False)
        else:
            row.operator("ceb.stop", text="■ Entangle Active (STOP)", icon='PAUSE', depress=True)

        layout.separator()

        for i, slot in enumerate(props.slots):
            box = layout.box()
            row = box.row()
            prefix_label = '""' if i == 0 else f'"character{i}:"'
            
            row.prop(slot, "is_active", text=f"Slot {i} (Prefix: {prefix_label})")
            if slot.is_active:
                row.prop(slot, "apply_on_stop", text=" Apply on STOP", toggle=True)
            
            if slot.is_active:
                col = box.column(align=True)
                col.prop(slot, "target_armature")
                col.separator()
                col.prop(slot, "root_bone")
                col.prop(slot, "pelvis_1")
                col.prop(slot, "pelvis_2")
                col.prop(slot, "pelvis_3")
                
                row_ss = box.row(align=True)
                if slot.has_ss_data:
                    op = row_ss.operator("ceb.smart_swizzle", text="✅ SS Cached", icon='CHECKMARK', depress=True)
                    op.slot_index = i
                    del_op = row_ss.operator("ceb.clear_ss", text="", icon='TRASH')
                    del_op.slot_index = i
                else:
                    op = row_ss.operator("ceb.smart_swizzle", text="🔄 Run SS (Not Cached)", icon='FILE_REFRESH', depress=False)
                    op.slot_index = i

        layout.separator()

        box = layout.box()
        box.label(text="▼ Timeline & Bake (Port: 8929)", icon='TIME')
        box.enabled = props.is_running
        
        row = box.row()
        row.enabled = not props.is_baking
        row.prop(props, "sync_master", expand=True)
        
        row = box.row()
        row.enabled = not props.is_baking
        row.prop(props, "sync_enable", toggle=True, icon='PLAY' if props.sync_enable else 'PAUSE')

        box.label(text="Bake Targets:")
        row = box.row()
        row.enabled = not props.is_baking
        for i, slot in enumerate(props.slots):
            if slot.is_active:
                row.prop(slot, "is_bake_target", text=f"Slot {i}")

        row = box.row(align=True)
        row.enabled = not props.is_baking
        row.prop(props, "bake_start")
        row.prop(props, "bake_end")
        
        row = box.row()
        row.enabled = not props.is_baking
        row.prop(props, "bake_delay")

        row = box.row()
        row.scale_y = 1.2
        if props.is_baking:
            row.operator("ceb.bake_animation", text="Baking... (Press ESC to stop)", icon='REC')
        else:
            row.operator("ceb.bake_animation", text="🔴 Bake Selected Targets", icon='REC')

class CEB_OT_Start(bpy.types.Operator):
    bl_idname = "ceb.start"
    bl_label = "Start Entangle"
    def execute(self, context):
        if "ceb_instance" not in globals() or globals()["ceb_instance"] is None:
            globals()["ceb_instance"] = CEB_ReceiverEngine()
        globals()["ceb_instance"].start(context)
        context.scene.ceb_props.is_running = True
        return {'FINISHED'}

class CEB_OT_Stop(bpy.types.Operator):
    bl_idname = "ceb.stop"
    bl_label = "Stop Entangle"
    def execute(self, context):
        if "ceb_instance" in globals() and globals()["ceb_instance"] is not None:
            globals()["ceb_instance"].stop()
            globals()["ceb_instance"] = None
        context.scene.ceb_props.is_running = False
        self.report({'INFO'}, "CEB Entangle Stopped!")
        return {'FINISHED'}

class CEB_OT_SmartSwizzle(bpy.types.Operator):
    bl_idname = "ceb.smart_swizzle"
    bl_label = "Smart Swizzle"
    slot_index: bpy.props.IntProperty()
    def execute(self, context):
        if "ceb_instance" in globals() and globals()["ceb_instance"] is not None:
            globals()["ceb_instance"].request_sync(context, force_slot=self.slot_index)
        return {'FINISHED'}

class CEB_OT_ClearSS(bpy.types.Operator):
    bl_idname = "ceb.clear_ss"
    bl_label = "Clear SS"
    slot_index: bpy.props.IntProperty()
    def invoke(self, context, event): return context.window_manager.invoke_confirm(self, event)
    def execute(self, context):
        slot = context.scene.ceb_props.slots[self.slot_index]
        slot.has_ss_data = False; slot.ss_data_json = ""
        return {'FINISHED'}

class CEB_OT_Bake(bpy.types.Operator):
    bl_idname = "ceb.bake_animation"
    bl_label = "Bake Animation"
    
    _timer = None
    current_frame = 0
    end_frame = 0
    state = 'SEEK'

    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            scene = context.scene
            ceb_inst = globals().get("ceb_instance")
            
            if self.state == 'SEEK':
                scene.frame_set(self.current_frame)
                if ceb_inst and ceb_inst.cmd_sock:
                    try:
                        ceb_inst.cmd_sock.sendto(json.dumps({"command": "SEEK", "frame": self.current_frame}).encode('utf-8'), ("127.0.0.1", 8920))
                    except: pass
                self.state = 'RECORD'

            elif self.state == 'RECORD':
                try:
                    context.view_layer.update()
                    if ceb_inst:
                        for i, slot in enumerate(scene.ceb_props.slots):
                            if slot.is_active and slot.is_bake_target and slot.target_armature:
                                port = 8921 + i
                                if port in ceb_inst.cached_bones:
                                    for b_id, b_name in ceb_inst.cached_bones[port].items():
                                        pb = slot.target_armature.pose.bones.get(b_name)
                                        if pb:
                                            pb.keyframe_insert(data_path="location")
                                            pb.keyframe_insert(data_path="rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler")
                except Exception as e: print(f"CEB Bake Error: {e}")

                if self.current_frame >= self.end_frame:
                    self.finish(context)
                    return {'FINISHED'}
                else:
                    self.current_frame += 1
                    self.state = 'SEEK'

        return {'PASS_THROUGH'}

    def execute(self, context):
        props = context.scene.ceb_props
        if props.is_baking: return {'CANCELLED'}
        self.current_frame = props.bake_start
        self.end_frame = props.bake_end
        self.state = 'SEEK'
        props.is_baking = True
        self.prev_master = props.sync_master
        props.sync_master = 'BLENDER'

        wm = context.window_manager
        self._timer = wm.event_timer_add(props.bake_delay, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context): self._cleanup(context, "Cancelled")
    def finish(self, context): self._cleanup(context, "Completed")
        
    def _cleanup(self, context, msg):
        if self._timer: context.window_manager.event_timer_remove(self._timer)
        self._timer = None
        props = context.scene.ceb_props
        props.is_baking = False
        props.sync_master = getattr(self, 'prev_master', 'CASCADEUR')

@persistent
def ceb_frame_change_handler(scene):
    ceb_inst = globals().get("ceb_instance")
    if ceb_inst and ceb_inst.running and not scene.ceb_props.is_baking:
        ceb_inst._apply_latest_pose_to_bones()

class CEB_ReceiverEngine:
    def __init__(self):
        self.running = False
        self.sys_sock = self.cmd_sock = self.tl_sock = None
        self.data_queues, self.data_sockets = {}, {}
        self.cached_bones, self.swizzle_offsets, self.casc_rest_pos = {}, {}, {}
        self.slot_armature_names = {} 
        self.active_slots_roots = [] 
        self.save_queue = queue.Queue()
        self.latest_char_poses = {} 
        self.connection_lost = False

    def _create_bound_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        sock.setblocking(False)
        try:
            while True: sock.recv(65535)
        except BlockingIOError: pass
        sock.setblocking(True)
        return sock

    def start(self, context):
        self.running = True
        self.connection_lost = False
        self.active_slots_roots = []
        self.slot_armature_names.clear()
        self.latest_char_poses.clear()
        
        for i, slot in enumerate(context.scene.ceb_props.slots):
            if slot.is_active:
                port = 8921 + i
                if slot.target_armature: self.slot_armature_names[port] = slot.target_armature.name 
                for b_name in [slot.root_bone, slot.pelvis_1, slot.pelvis_2, slot.pelvis_3]:
                    if b_name: self.active_slots_roots.append(b_name)
                    
        self.cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sys_sock = self._create_bound_socket(8919)
        threading.Thread(target=self._sys_listen_thread, daemon=True).start()
        
        self.tl_sock = self._create_bound_socket(8929)
        self.tl_sock.setblocking(False)
        
        bpy.app.timers.register(self._update_blender_scene)
        
        if ceb_frame_change_handler not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(ceb_frame_change_handler)
            
        self.request_sync(context)

    def request_sync(self, context, force_slot=-1):
        chars_info = []
        for i, slot in enumerate(context.scene.ceb_props.slots):
            if slot.is_active:
                port = 8921 + i
                req_init = True
                if i == force_slot: req_init = True 
                elif slot.has_ss_data and slot.ss_data_json:
                    try:
                        self._load_ss_from_json(port, slot.ss_data_json)
                        self._start_data_listener(port)
                        req_init = False
                    except: pass
                chars_info.append({"prefix": "" if i == 0 else f"character{i}:", "target_port": port, "request_init": req_init})
                
        try:
            self.cmd_sock.sendto(json.dumps({"command": "START", "reply_port": 8919, "characters": chars_info}).encode('utf-8'), ("127.0.0.1", 8920))
        except ConnectionResetError:
            self.connection_lost = True
        except: pass

    def stop(self):
        self.running = False
        self._apply_current_pose_as_keyframe()
        
        if self.cmd_sock:
            try: self.cmd_sock.sendto(json.dumps({"command": "STOP"}).encode('utf-8'), ("127.0.0.1", 8920))
            except: pass
        if self.sys_sock: self.sys_sock.close()
        if self.cmd_sock: self.cmd_sock.close()
        if self.tl_sock: self.tl_sock.close()
        for sock in self.data_sockets.values(): sock.close()
        
        if ceb_frame_change_handler in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.remove(ceb_frame_change_handler)

    def _apply_current_pose_as_keyframe(self):
        curr_frame = bpy.context.scene.frame_current
        for i, slot in enumerate(bpy.context.scene.ceb_props.slots):
            if slot.is_active and slot.apply_on_stop:
                port = 8921 + i
                if port in self.cached_bones:
                    arm_name = self.slot_armature_names.get(port)
                    armature = bpy.data.objects.get(arm_name) if arm_name else None
                    if not armature: continue
                    
                    for b_id, b_name in self.cached_bones[port].items():
                        pb = armature.pose.bones.get(b_name)
                        if pb:
                            pb.keyframe_insert(data_path="rotation_quaternion" if pb.rotation_mode == 'QUATERNION' else "rotation_euler", frame=curr_frame)
                            if any(r_name in pb.name for r_name in self.active_slots_roots):
                                pb.keyframe_insert(data_path="location", frame=curr_frame)

    def _sys_listen_thread(self):
        while self.running:
            try:
                data, _ = self.sys_sock.recvfrom(65535)
                payload = json.loads(data.decode('utf-8'))
                if payload.get("command") == "INIT_ACK":
                    self._process_handshake(payload.get("target_port"), payload.get("bones", []))
            except ConnectionResetError:
                self.connection_lost = True
            except: pass

    def _process_handshake(self, port, bones_data):
        arm_name = self.slot_armature_names.get(port)
        if not arm_name or arm_name not in bpy.data.objects: return
        armature = bpy.data.objects[arm_name]
        prefix = "" if port == 8921 else f"character{port - 8921}:"
        
        self.cached_bones[port], self.swizzle_offsets[port], self.casc_rest_pos[port] = {}, {}, {}
        ss_save_dict = {}
        
        for b_data in bones_data:
            b_id, b_name = b_data["id"], b_data["name"]
            casc_rest_rot = mathutils.Quaternion((b_data["rest_rot"][3], b_data["rest_rot"][0], b_data["rest_rot"][1], b_data["rest_rot"][2])).inverted()
            rest_pos = mathutils.Vector((b_data["rest_pos"][0], b_data["rest_pos"][1], b_data["rest_pos"][2]))
            
            stripped_name = b_name.replace(prefix, "") if prefix else b_name
            t_bone = b_name if b_name in armature.pose.bones else stripped_name if stripped_name in armature.pose.bones else None
                
            if t_bone:
                self.cached_bones[port][b_id] = t_bone 
                self.swizzle_offsets[port][b_id] = casc_rest_rot
                self.casc_rest_pos[port][b_id] = rest_pos
                ss_save_dict[str(b_id)] = {"name": t_bone, "q": [casc_rest_rot.w, casc_rest_rot.x, casc_rest_rot.y, casc_rest_rot.z], "p": [rest_pos.x, rest_pos.y, rest_pos.z]}
                
        self.save_queue.put({"port": port, "data": json.dumps(ss_save_dict)})
        self._start_data_listener(port)

    def _load_ss_from_json(self, port, json_str):
        self.cached_bones[port], self.swizzle_offsets[port], self.casc_rest_pos[port] = {}, {}, {}
        data = json.loads(json_str)
        for b_id_str, d in data.items():
            b_id = int(b_id_str)
            self.cached_bones[port][b_id] = d["name"]
            self.swizzle_offsets[port][b_id] = mathutils.Quaternion(d["q"])
            self.casc_rest_pos[port][b_id] = mathutils.Vector(d["p"])

    def _start_data_listener(self, port):
        if port not in self.data_sockets:
            self.data_queues[port] = queue.Queue()
            sock = self._create_bound_socket(port)
            self.data_sockets[port] = sock
            threading.Thread(target=self._data_listen_thread, args=(port, sock), daemon=True).start()

    def _data_listen_thread(self, port, sock):
        while self.running:
            try:
                data, _ = sock.recvfrom(8192)
                self.data_queues[port].put(data)
            except ConnectionResetError:
                self.connection_lost = True
            except: pass

    def _apply_latest_pose_to_bones(self):
        for port, poses in self.latest_char_poses.items():
            arm_name = self.slot_armature_names.get(port)
            armature = bpy.data.objects.get(arm_name) if arm_name else None
            if not armature: continue
            
            for b_id, pose_data in poses.items():
                if b_id in self.cached_bones[port]:
                    pb = armature.pose.bones.get(self.cached_bones[port][b_id])
                    if pb:
                        pb.rotation_mode = 'QUATERNION'
                        pb.rotation_quaternion = pose_data["rot"]
                        if "loc" in pose_data:
                            pb.location = pose_data["loc"]

    def _update_blender_scene(self):
        if not self.running: return None
        
        # Auto-Disconnect Safety Net
        if self.connection_lost:
            bpy.ops.ceb.stop()
            self.connection_lost = False
            return None
            
        props = bpy.context.scene.ceb_props
        
        while not self.save_queue.empty():
            save_info = self.save_queue.get_nowait()
            slot = props.slots[save_info["port"] - 8921]
            slot.ss_data_json = save_info["data"]; slot.has_ss_data = True
            
        if props.sync_enable and props.sync_master == 'CASCADEUR' and not props.is_baking and self.tl_sock:
            latest_frame = None
            while True:
                try:
                    data, _ = self.tl_sock.recvfrom(1024)
                    if len(data) >= 9:
                        header, cmd, frame = struct.unpack('<4s B i', data[:9])
                        if header == b'GTLB' and cmd == 0x03: latest_frame = frame
                except: break
            if latest_frame is not None and latest_frame != bpy.context.scene.frame_current:
                bpy.context.scene.frame_set(latest_frame)
                
        if props.sync_enable and props.sync_master == 'BLENDER' and not props.is_baking and self.cmd_sock:
            curr = bpy.context.scene.frame_current
            if not hasattr(self, 'last_sent_frame') or self.last_sent_frame != curr:
                try:
                    self.cmd_sock.sendto(json.dumps({"command": "SEEK", "frame": curr}).encode('utf-8'), ("127.0.0.1", 8920))
                    self.last_sent_frame = curr
                except ConnectionResetError:
                    self.connection_lost = True
                except: pass

        try:
            for port in list(self.cached_bones.keys()):
                if port not in self.data_queues: continue
                data = None
                while not self.data_queues[port].empty(): data = self.data_queues[port].get_nowait()
                if data:
                    if port not in self.latest_char_poses: self.latest_char_poses[port] = {}
                    offset = 0
                    while offset < len(data):
                        chunk = data[offset:offset+29]
                        if len(chunk) < 29: break
                        vals = struct.unpack('<B4f3f', chunk)
                        b_id = vals[0]
                        
                        offset_q = self.swizzle_offsets[port].get(b_id)
                        if offset_q:
                            incoming_q = mathutils.Quaternion((vals[4], vals[1], vals[2], vals[3]))
                            final_q = offset_q @ incoming_q
                            
                            pose_dict = {"rot": final_q}
                            b_name = self.cached_bones[port].get(b_id, "")
                            if any(r_name in b_name for r_name in self.active_slots_roots):
                                swizzled_pos = offset_q @ (mathutils.Vector((vals[5], vals[6], vals[7])) - self.casc_rest_pos[port][b_id])
                                pose_dict["loc"] = swizzled_pos
                                
                            self.latest_char_poses[port][b_id] = pose_dict
                        offset += 29
            self._apply_latest_pose_to_bones()
        except Exception: pass
        return 0.016

classes = ( CEBSlotProps, CEBSceneProps, CEB_PT_MainPanel, CEB_OT_Start, CEB_OT_Stop, CEB_OT_SmartSwizzle, CEB_OT_ClearSS, CEB_OT_Bake )
def init_slots(scene):
    if len(scene.ceb_props.slots) == 0:
        for _ in range(5): scene.ceb_props.slots.add()

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.ceb_props = bpy.props.PointerProperty(type=CEBSceneProps)
    bpy.app.handlers.depsgraph_update_post.append(lambda scene, _: init_slots(scene))

def unregister():
    if ceb_frame_change_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(ceb_frame_change_handler)
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ceb_props

if __name__ == "__main__": register()