bl_info = {
    "name": "Cascadeur Entangle for Blender (CEB)",
    "author": "Leader & AI",
    "version": (1, 0, 3),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > CEB",
    "description": "Zero Calibration O(1) Live Link with Cascadeur",
    "category": "Animation",
}

import bpy
import socket
import struct
import json
import threading
import queue
import mathutils

# ==========================================
# 1. プロパティ定義
# ==========================================
class CEBSlotProps(bpy.types.PropertyGroup):
    is_active: bpy.props.BoolProperty(name="Active", default=True)
    target_armature: bpy.props.PointerProperty(
        name="Armature", 
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE'
    )
    root_bone: bpy.props.StringProperty(name="Root", default="")
    pelvis_1: bpy.props.StringProperty(name="Pelvis 1", default="")
    pelvis_2: bpy.props.StringProperty(name="Pelvis 2", default="")
    pelvis_3: bpy.props.StringProperty(name="Pelvis 3", default="")

class CEBSceneProps(bpy.types.PropertyGroup):
    is_running: bpy.props.BoolProperty(default=False)
    slots: bpy.props.CollectionProperty(type=CEBSlotProps)
    prop_target: bpy.props.StringProperty(name="Target Object", default="")

# ==========================================
# 2. UI パネル (Nメニュー)
# ==========================================
class CEB_PT_MainPanel(bpy.types.Panel):
    bl_label = "CEB Live Link"
    bl_idname = "CEB_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CEB'

    def draw(self, context):
        layout = self.layout
        props = context.scene.ceb_props

        row = layout.row()
        row.scale_y = 1.5
        if not props.is_running:
            row.operator("ceb.start", text="▶ START Live Link", icon='PLAY')
        else:
            row.operator("ceb.stop", text="■ STOP", icon='PAUSE')

        layout.separator()

        for i, slot in enumerate(props.slots):
            box = layout.box()
            row = box.row()
            
            prefix_label = '""' if i == 0 else f'"character{i}:"'
            row.prop(slot, "is_active", text=f"Slot {i} (Prefix: {prefix_label})")
            
            if slot.is_active:
                col = box.column(align=True)
                col.prop(slot, "target_armature")
                col.separator()
                col.prop(slot, "root_bone")
                col.prop(slot, "pelvis_1")
                col.prop(slot, "pelvis_2")
                col.prop(slot, "pelvis_3")
                
                ss_op = box.operator("ceb.smart_swizzle", text="🔄 Smart Swizzle", icon='FILE_REFRESH')
                ss_op.slot_index = i

        layout.separator()

        box = layout.box()
        box.label(text="▼ Prop (Port: 8929)", icon='MESH_MONKEY')
        box.prop(props, "prop_target")

# ==========================================
# 3. オペレーター
# ==========================================
class CEB_OT_Start(bpy.types.Operator):
    bl_idname = "ceb.start"
    bl_label = "Start CEB"

    def execute(self, context):
        if "ceb_instance" not in globals() or globals()["ceb_instance"] is None:
            globals()["ceb_instance"] = CEB_ReceiverEngine()
            globals()["ceb_instance"].start(context)
        context.scene.ceb_props.is_running = True
        self.report({'INFO'}, "CEB Live Link Started")
        return {'FINISHED'}

class CEB_OT_Stop(bpy.types.Operator):
    bl_idname = "ceb.stop"
    bl_label = "Stop CEB"

    def execute(self, context):
        if "ceb_instance" in globals() and globals()["ceb_instance"] is not None:
            globals()["ceb_instance"].stop()
            globals()["ceb_instance"] = None
        context.scene.ceb_props.is_running = False
        self.report({'INFO'}, "CEB Live Link Stopped")
        return {'FINISHED'}

class CEB_OT_SmartSwizzle(bpy.types.Operator):
    bl_idname = "ceb.smart_swizzle"
    bl_label = "Smart Swizzle"
    slot_index: bpy.props.IntProperty()

    def execute(self, context):
        if "ceb_instance" in globals() and globals()["ceb_instance"] is not None:
            globals()["ceb_instance"].request_sync(context)
            self.report({'INFO'}, f"Requested Smart Swizzle for all Active Slots!")
        else:
            self.report({'WARNING'}, "Live Link is not running!")
        return {'FINISHED'}

# ==========================================
# 4. コアエンジン (O(1) & メモリ安全設計)
# ==========================================
class CEB_ReceiverEngine:
    def __init__(self):
        self.running = False
        self.sys_sock = None
        self.cmd_sock = None
        self.data_queues = {}     
        self.data_sockets = {}    
        
        self.cached_bones = {}       # { port: { id: "bone_name" } }
        self.swizzle_offsets = {}    
        self.casc_rest_pos = {}      
        
        self.slot_armature_names = {} # { port: "armature_name" }
        self.active_slots_roots = [] 
        self.prop_name = None         

    def start(self, context):
        self.running = True
        
        self.active_slots_roots = []
        self.slot_armature_names.clear()
        
        for i, slot in enumerate(context.scene.ceb_props.slots):
            if slot.is_active:
                port = 8921 + i
                if slot.target_armature:
                    self.slot_armature_names[port] = slot.target_armature.name 
                    
                for b_name in [slot.root_bone, slot.pelvis_1, slot.pelvis_2, slot.pelvis_3]:
                    if b_name: self.active_slots_roots.append(b_name)
                    
        self.prop_name = context.scene.ceb_props.prop_target 
            
        self.cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        threading.Thread(target=self._sys_listen_thread, daemon=True).start()
        
        if self.prop_name:
            self._start_data_listener(8929)
            
        bpy.app.timers.register(self._update_blender_scene)
        self.request_sync(context)

    def request_sync(self, context):
        chars_info = []
        for i, slot in enumerate(context.scene.ceb_props.slots):
            if slot.is_active:
                prefix = "" if i == 0 else f"character{i}:"
                target_port = 8921 + i
                chars_info.append({"prefix": prefix, "target_port": target_port})
                
        props_info = []
        if self.prop_name:
            props_info.append({"prop_id": self.prop_name, "target_port": 8929})
            
        payload = {
            "command": "START",
            "reply_port": 8919,
            "characters": chars_info,
            "props": props_info
        }
        self.cmd_sock.sendto(json.dumps(payload).encode('utf-8'), ("127.0.0.1", 8920))

    def stop(self):
        self.running = False
        
        # ★大修正: Cascadeur側にSTOPコマンドを送り、パケットの洪水を止める！
        if self.cmd_sock:
            try:
                self.cmd_sock.sendto(json.dumps({"command": "STOP"}).encode('utf-8'), ("127.0.0.1", 8920))
            except:
                pass
                
        if self.sys_sock: self.sys_sock.close()
        if self.cmd_sock: self.cmd_sock.close()
        for sock in self.data_sockets.values():
            sock.close()

    def _sys_listen_thread(self):
        self.sys_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ★大修正: 通信エラーを防ぐソケット再利用フラグを追加！
        self.sys_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sys_sock.bind(('0.0.0.0', 8919))
        
        while self.running:
            try:
                data, _ = self.sys_sock.recvfrom(65535)
                payload = json.loads(data.decode('utf-8'))
                if payload.get("command") == "INIT_ACK":
                    self._process_handshake(payload.get("target_port"), payload.get("bones", []))
            except:
                pass

    def _process_handshake(self, port, bones_data):
        print(f"[CEB Receiver] Handshake received for Port {port}. Calculating Smart Swizzle...")
        self.cached_bones[port] = {}
        self.swizzle_offsets[port] = {}
        self.casc_rest_pos[port] = {}
        
        arm_name = self.slot_armature_names.get(port)
        if not arm_name or arm_name not in bpy.data.objects:
            return
        armature = bpy.data.objects[arm_name]
            
        prefix = "" if port == 8921 else f"character{port - 8921}:"
        
        for b_data in bones_data:
            b_id = b_data["id"]
            b_name = b_data["name"]
            casc_rest_rot = mathutils.Quaternion((b_data["rest_rot"][3], b_data["rest_rot"][0], b_data["rest_rot"][1], b_data["rest_rot"][2]))
            
            stripped_name = b_name.replace(prefix, "") if prefix else b_name
            target_bone_name = None
            
            if b_name in armature.pose.bones:
                target_bone_name = b_name
            elif stripped_name in armature.pose.bones:
                target_bone_name = stripped_name
                
            if target_bone_name:
                self.cached_bones[port][b_id] = target_bone_name 
                self.swizzle_offsets[port][b_id] = casc_rest_rot.inverted()
                self.casc_rest_pos[port][b_id] = mathutils.Vector((b_data["rest_pos"][0], b_data["rest_pos"][1], b_data["rest_pos"][2]))
                
        self._start_data_listener(port)

    def _start_data_listener(self, port):
        if port not in self.data_sockets:
            self.data_queues[port] = queue.Queue()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # ★大修正: 通信エラーを防ぐソケット再利用フラグを追加！
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            self.data_sockets[port] = sock
            threading.Thread(target=self._data_listen_thread, args=(port, sock), daemon=True).start()

    def _data_listen_thread(self, port, sock):
        while self.running:
            try:
                data, _ = sock.recvfrom(8192)
                self.data_queues[port].put(data)
            except:
                pass

    def _update_blender_scene(self):
        if not self.running: return None
        
        try:
            # 1. キャラクターの同期
            for port in list(self.cached_bones.keys()):
                if port not in self.data_queues: continue
                
                data = None
                while not self.data_queues[port].empty():
                    data = self.data_queues[port].get_nowait()
                    
                if data:
                    arm_name = self.slot_armature_names.get(port)
                    armature = bpy.data.objects.get(arm_name) if arm_name else None
                    if not armature: continue

                    offset = 0
                    while offset < len(data):
                        chunk = data[offset:offset+29]
                        if len(chunk) < 29: break
                        
                        vals = struct.unpack('<B4f3f', chunk)
                        b_id = vals[0]
                        
                        if b_id in self.cached_bones[port]:
                            b_name = self.cached_bones[port][b_id]
                            
                            pb = armature.pose.bones.get(b_name)
                            
                            if pb:
                                offset_q = self.swizzle_offsets[port][b_id]
                                incoming_q = mathutils.Quaternion((vals[4], vals[1], vals[2], vals[3]))
                                final_q = offset_q @ incoming_q
                                
                                pb.rotation_mode = 'QUATERNION'
                                pb.rotation_quaternion = final_q
                                
                                if any(r_name in pb.name for r_name in self.active_slots_roots):
                                    curr_pos = mathutils.Vector((vals[5], vals[6], vals[7]))
                                    delta_pos = curr_pos - self.casc_rest_pos[port][b_id]
                                    swizzled_pos = offset_q @ delta_pos
                                    pb.location = (swizzled_pos.x, swizzled_pos.y, swizzled_pos.z)
                            
                        offset += 29

            # 2. プロップの同期
            prop_port = 8929
            if prop_port in self.data_queues and self.prop_name:
                data = None
                while not self.data_queues[prop_port].empty():
                    data = self.data_queues[prop_port].get_nowait()
                
                if data and len(data) >= 32 and data[:3] == b'CEP':
                    prop_obj = bpy.data.objects.get(self.prop_name)
                    if prop_obj:
                        vals = struct.unpack('<3f4f', data[4:32])
                        prop_obj.location = (vals[0], vals[1], vals[2])
                        prop_obj.rotation_mode = 'QUATERNION'
                        prop_obj.rotation_quaternion = mathutils.Quaternion((vals[6], vals[3], vals[4], vals[5]))

        except Exception as e:
            print(f"Error in CEB main loop: {e}")
            
        return 0.016

# ==========================================
# 5. 登録処理
# ==========================================
classes = (
    CEBSlotProps,
    CEBSceneProps,
    CEB_PT_MainPanel,
    CEB_OT_Start,
    CEB_OT_Stop,
    CEB_OT_SmartSwizzle,
)

def init_slots(scene):
    if len(scene.ceb_props.slots) == 0:
        for _ in range(5):
            scene.ceb_props.slots.add()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ceb_props = bpy.props.PointerProperty(type=CEBSceneProps)
    bpy.app.handlers.depsgraph_update_post.append(lambda scene, _: init_slots(scene))

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ceb_props

if __name__ == "__main__":
    register()