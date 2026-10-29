extends Node3D
## Geometry inspection only: original transforms/materials/animation are omitted.
var pivot := Node3D.new()

func _ready() -> void:
	add_child(pivot)
	var names := ["M04001", "M04004_2", "M04004_3", "M04004_4", "M04002", "M04003"]
	var bounds := AABB()
	var first := true
	for i in range(names.size()):
		var mesh := load("res://assets/static_sample/" + names[i] + ".obj") as Mesh
		if mesh == null:
			push_error("Unable to import diagnostic mesh: " + names[i])
			continue
		var instance := MeshInstance3D.new()
		instance.mesh = mesh
		var material := StandardMaterial3D.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.albedo_color = Color.from_hsv(float(i) / names.size(), 0.45, 0.8)
		instance.material_override = material
		pivot.add_child(instance)
		bounds = mesh.get_aabb() if first else bounds.merge(mesh.get_aabb())
		first = false
	if first:
		return
	pivot.position = -bounds.get_center()
	var radius: float = maxf(bounds.size.length(), 1.0)
	var camera := Camera3D.new()
	add_child(camera)
	camera.set_as_top_level(true)
	camera.position = Vector3(1.0, 0.8, 1.0).normalized() * radius * 1.5
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = radius * 1.1
	camera.far = radius * 10.0
	camera.look_at(Vector3.ZERO)
	camera.make_current()
	var label := Label.new()
	label.text = "map004 — local geometry diagnostic\nNo source materials, transforms or animations\nDrag left mouse to rotate"
	label.position = Vector2(20, 20)
	add_child(label)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		rotation.y += event.relative.x * 0.005
