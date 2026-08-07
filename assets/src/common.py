"""Shared toolkit for the Blender asset scripts.

Every model in ``src/brainrot/assets/data`` is produced by a script in this
directory, run under headless Blender (``pip install bpy``). The pipeline is
built around one renderer contract:

    final pixel = baked light map (texture) x zone colour (material) x tint

raylib's default shader computes exactly that product, on the GPU build and on
the software rasteriser alike. So:

* All *lighting* -- sun, sky bounce, ambient occlusion -- is baked here, once,
  into a grayscale texture per asset. Nothing at runtime computes light.
* All *colour* stays in flat per-zone materials, so the runtime can recolour a
  hoodie or a train body per seed by writing one material colour.
* Vertex colours are never exported: the software rasteriser ignores material
  colour and tint whenever a colour attribute is present, which would make CI
  frames diverge from what the GPU shows.

Scripts must run one per process: ``bpy`` can only be imported once.
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector

DATA_DIR = Path(__file__).resolve().parents[2] / "src" / "brainrot" / "assets" / "data"

# One sun direction shared by every bake so assets can be mixed in a scene
# without their shading disagreeing about where the light is. Upper front-left,
# matching the runtime sky's sun placement.
SUN_ROTATION = (math.radians(50), math.radians(-14), math.radians(135))


def reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def zone(name: str, rgb: tuple[float, float, float], rough: float = 0.7):
    """A flat-colour zone material. The colour is what the runtime recolours."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def box(name, size, loc, material, bevel=0.05, rot=None):
    """An axis-aligned beveled box. The unit of almost everything we build."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.transform(Matrix.Diagonal((*size, 1.0)))
    if rot:
        ob.rotation_euler = rot
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier="bevel")
    ob.data.materials.append(material)
    return ob


def cylinder(name, radius, depth, loc, material, rot=None, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, location=loc, vertices=vertices,
        rotation=rot or (0, 0, 0),
    )
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    return ob


def join(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object
    merged.name = name
    return merged


def _bake_lighting(objects, resolution: int) -> bpy.types.Image:
    """Bake sun + sky + AO into one grayscale image shared by ``objects``.

    DIFFUSE with the colour pass disabled bakes pure incident light, so the
    result is independent of the zone colours -- which is precisely what lets
    the runtime swap those colours without the shading going stale.
    """
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 192
    scene.render.bake.use_pass_direct = True
    scene.render.bake.use_pass_indirect = True
    scene.render.bake.use_pass_color = False
    scene.render.bake.margin = 4

    sun = bpy.data.objects.new("bake-sun", bpy.data.lights.new("bake-sun", "SUN"))
    sun.data.energy = 1.6
    sun.data.angle = math.radians(20)  # soft-edged shadows
    sun.rotation_euler = SUN_ROTATION
    scene.collection.objects.link(sun)

    world = bpy.data.worlds.new("bake-world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs[1].default_value = 0.45
    scene.world = world

    image = bpy.data.images.new("lightmap", resolution, resolution, alpha=False)
    # Every material needs an active image-texture node pointing at the target.
    for ob in objects:
        for slot in ob.material_slots:
            nodes = slot.material.node_tree.nodes
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = image
            nodes.active = tex

    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.bake(type="DIFFUSE")
    return image


def _wire_lightmap(objects, image) -> None:
    """Connect the bake to every zone material's Base Color via multiply.

    The glTF exporter recognises the ``colour factor x image`` multiply pattern
    and emits it as baseColorFactor + baseColorTexture -- the exact pair raylib
    loads into material colour and albedo texture.
    """
    for ob in objects:
        for slot in ob.material_slots:
            mat = slot.material
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            bsdf = nodes["Principled BSDF"]
            base = tuple(bsdf.inputs["Base Color"].default_value)

            tex = next(n for n in nodes if n.type == "TEX_IMAGE" and n.image == image)
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs["B"].default_value = base
            links.new(tex.outputs["Color"], mix.inputs["A"])
            links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])


def unwrap(objects) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_and_export(objects, out_name: str, resolution: int = 256,
                    export_animations: bool = False) -> Path:
    """Unwrap, bake lighting, wire materials, export GLB. The whole tail end."""
    unwrap(objects)
    image = _bake_lighting(objects, resolution)
    _wire_lightmap(objects, image)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"{out_name}.glb"
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        use_selection=True,
        export_animations=export_animations,
        export_animation_mode="ACTIONS" if export_animations else "ACTIONS",
        export_vertex_color="NONE",
        export_yup=True,
    )
    _set_factors(out)
    print(f"[assets] wrote {out}")
    return out


def _set_factors(glb_path: Path) -> None:
    """Belt-and-braces: force baseColorFactor from the zone colours.

    If a Blender release stops collapsing the multiply pattern into a factor,
    the factors silently become white and every zone renders uncoloured. Patch
    the GLB's JSON chunk directly so the contract cannot rot.
    """
    zones = {
        m.name: tuple(m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value)
        if "Principled BSDF" in m.node_tree.nodes else None
        for m in bpy.data.materials
        if m.use_nodes
    }
    # After _wire_lightmap the BSDF input is linked, so read the mix node's B.
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        for node in m.node_tree.nodes:
            if node.type == "MIX" and node.data_type == "RGBA":
                zones[m.name] = tuple(node.inputs["B"].default_value)

    import json

    blob = glb_path.read_bytes()
    length, = struct.unpack_from("<I", blob, 12)
    header = json.loads(blob[20:20 + length].decode("utf-8"))
    changed = False
    for mat in header.get("materials", []):
        color = zones.get(mat.get("name"))
        if color:
            pbr = mat.setdefault("pbrMetallicRoughness", {})
            pbr["baseColorFactor"] = [round(c, 5) for c in color[:3]] + [1.0]
            changed = True
    if not changed:
        return
    payload = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload += b" " * (-len(payload) % 4)
    rest = blob[20 + length:]
    total = 12 + 8 + len(payload) + len(rest)
    out = struct.pack("<4sII", b"glTF", 2, total)
    out += struct.pack("<I4s", len(payload), b"JSON") + payload + rest
    glb_path.write_bytes(out)


# ---------------------------------------------------------------------------
# Rigged characters
# ---------------------------------------------------------------------------

def skinned_part(name, group, size, center, material, bevel=0.03):
    """A box wholly weighted to one bone. Rigid per-part skinning is exactly
    how the boxy body should deform: joints bend, boxes stay boxes."""
    ob = box(name, size, center, material, bevel)
    vg = ob.vertex_groups.new(name=group)
    vg.add(range(len(ob.data.vertices)), 1.0, "REPLACE")
    return ob


def build_armature(bones: dict[str, tuple[tuple, tuple, str | None]]):
    """Create an armature from {name: (head, tail, parent)}."""
    arm_data = bpy.data.armatures.new("rig")
    rig = bpy.data.objects.new("rig", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (head, tail, parent) in bones.items():
        b = arm_data.edit_bones.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent:
            b.parent = arm_data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return rig


def skin(mesh_ob, rig) -> None:
    mesh_ob.parent = rig
    mod = mesh_ob.modifiers.new("armature", "ARMATURE")
    mod.object = rig


def euler_q(x=0.0, y=0.0, z=0.0):
    return Euler((x, y, z), "XYZ").to_quaternion()


def world_axis_q(pose_bone, axis, deg):
    """A pose-bone quaternion that rotates ``deg`` about a WORLD axis.

    Pose-bone rotations are expressed in the bone's rest-local frame, whose
    axes depend on which way the bone points -- keying "x" on a down-pointing
    limb swings it sideways, which is how a run cycle becomes 7 Hz jumping
    jacks. Conjugating by the rest orientation makes the intent explicit:
    (0,1,0) is always the fore-aft swing axis, whatever the bone.

    For child bones (shins, forearms) the axis is world-true in rest pose and
    rides with the parent afterwards -- which is exactly what an anatomical
    hinge should do.
    """
    from mathutils import Quaternion, Vector

    rest = pose_bone.bone.matrix_local.to_quaternion()
    return rest.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ rest


def swing(pose, name, forward_deg, side_deg=0.0):
    """Set a limb/spine bone: +forward_deg pitches toward the character's
    facing (+X), +side_deg tilts to the character's left."""
    pb = pose.bones[name]
    q = world_axis_q(pb, (0, 1, 0), -forward_deg)
    if side_deg:
        q = q @ world_axis_q(pb, (1, 0, 0), side_deg)
    pb.rotation_quaternion = q


def lift(pose, name, up=0.0, forward=0.0):
    """Translate a bone in world terms (metres), whatever its local frame."""
    from mathutils import Vector

    pb = pose.bones[name]
    rest = pb.bone.matrix_local.to_quaternion()
    pb.location = rest.inverted() @ Vector((forward, 0.0, up))


def record_action(rig, name: str, length: int, pose_fn, step: int = 2) -> None:
    """Sample ``pose_fn(pose, t01)`` into a named Action and stash it on an NLA
    track so the exporter writes every clip, not just the last active one."""
    scene = bpy.context.scene
    rig.animation_data_create()
    action = bpy.data.actions.new(name)
    rig.animation_data.action = action
    for frame in range(0, length + 1, step):
        scene.frame_set(frame)
        pose_fn(rig.pose, frame / length)
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=frame)
            pb.keyframe_insert("location", frame=frame)
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, action)
    rig.animation_data.action = None


def run_script_banner(name: str) -> None:
    print(f"[assets] building {name} (blender {bpy.app.version_string}, py {sys.version.split()[0]})")
