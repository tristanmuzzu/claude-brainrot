# Landmines that cost hours

Moved verbatim from `CLAUDE.md` on 2026-09-02. `CLAUDE.md` keeps the dozen
most likely to cause a wrong edit today; this is the whole list, including the
Windows-only ones (`overlay/win32.py` is still shipped and still tested on a
Windows box). Read the one that matches your symptom before theorising.

- **The software rasteriser is not the GPU build, and where it differs is
  exactly where this project has guards.** RLSW (raylib 6.0's software
  renderer, which is what `raylib-software` installs and what CI runs on)
  honours **neither the depth mask nor alpha blending** — so the two tests that
  hold `no_depth_write` and the rlgl batch-order fix cannot be observed on it
  and are skipped there (`conftest.software_rasteriser`, which reads the marker
  out of the loaded `.so` rather than trusting the installed distribution list:
  `raylib-software` is force-installed *over* `raylib`, so both names are
  present afterwards and only the binary says which won). "colours/output match
  the GPU build" was true of frames and is not true of depth.
- **Do not resize the shared test window, and never open a second one.** RLSW
  allocates its framebuffer at `InitWindow` and `SetWindowSize` does not
  reallocate it, so a draw at the new size runs off the end of the old buffer.
  `test_tower` did both — its own 180x320 window, then `destroy()` on it — and
  the whole suite was green here and *dead on CI on both platforms*: a
  segfault or a glibc abort about a thousand frames later, reported against
  `GetWorldToScreen` in the spiral's haze band, which has nothing to do with
  it. Every drawing test goes through `conftest.ensure_window()` at the size it
  already is. This is the general shape: **a heap-corrupting bug is reported
  wherever the heap is next touched**, so the named frame is evidence about
  timing and not about cause.

- **Two descriptions of one surface will disagree, and the disagreement is
  invisible in both directions.** `emit_layer` drew the core's flutes a cell
  proud of `core_r` and `rock` had never heard of them, so twenty-eight of the
  fifty-six ribs -- the tower's signature forest of columns -- were drawn, lit,
  fogged and walked straight through. Measured: **3.3% of body samples along a
  course were inside a cell the tower draws**, up to 0.80 m deep. The "body
  inside the world" figure cannot see this, because it asks `blocked`, which is
  `rock`, which is exactly the half that is wrong. Every cell of skin now goes
  through `Course._paint` and is placed only if `rock` agrees, and
  `tests/test_spiral.py` holds it at zero. A margin that skipped the gate well
  inside the wall leaks: `unwrap` puts a cell near a level seam in the *other*
  level, whose band is a different width, so "comfortably inside" is not a
  local question.
- **A probe that exempts what it is measuring reads zero forever.** The walk
  probe accepted a cell belonging to either landing as ground, which exempted
  precisely the cells a walk's own bridge meant to lay -- including the ones
  `write` refused. It read 0% while `tests/test_tower.py` failed. Ask the world
  the same question the body would.
- **Check a move at the moment the body reaches it, not one step later.**
  `advance` releases the ground behind the body, so a probe that walks the
  course with `<` where `<=` was meant measures every move against a world that
  has already had its floor taken away. It reads as a catastrophic air-walk and
  it is the probe's own doing. This was made twice in one session.
- **A refusal in the middle of a written sequence is not the sequence
  failing.** Both the authored exit and the gated crossing threw away
  everything after the first landing that would not go, and in both cases the
  next landing is aimed further along the same lane and usually goes. Worth
  twenty-four landings a sweep on two levels and six passages entered.
- **Vanilla's constants are not vanilla's *result*.** The face-shade table
  (top 1.0, bottom 0.5, sides 0.6/0.8) multiplies a light level skylight has
  already filled in. Copied on its own it is 60% of nothing, and this
  renderer's frames were half again as dark as the real game's -- with three
  materials hand-brightened to compensate locally before anybody checked the
  general case.

- **A cell's `y` is its floor, its `x` and `z` are its centre.** Everything
  that reasons about standing on a block (`surface = y + 1`) depends on it, and
  a cube mesh centred on `y` instead draws a whole building half a block below
  the world it collides with. `engine/chunk.py` adds the +0.5 explicitly.
- **A mesh raylib will free must be allocated by raylib.** `UnloadMesh` calls
  `RL_FREE` on `mesh.vertices`; hand it a cffi buffer and the process dies
  inside libc. `chunk.py` `MemAlloc`s and memmoves; `voxel.py` takes the other
  way out and never unloads its one shared cube.
- **Checking is not reserving.** Head-room is checked when a block is placed;
  nothing stopped a *later* block, or a support post from a landing twenty
  blocks on, being built in it. On a course that comes back over itself that is
  routine, and the symptom is the body running with masonry through its head.
  See the spiral's four reservations above.
- **A texture pattern that ignores `face` was still being computed six times.**
  `_cobble_face` and `_ao_table` are cached per salt and per process; before
  them one cobble strip cost 34 ms, and the spiral bakes fifty-odd materials at
  scene construction. Also: `Image.load()[x, y] = tuple` is about two
  microseconds a texel -- that one call was 280 ms of a 315 ms build.
- **Pose-bone axes**: down-pointing bones swing SIDEWAYS on local x. All pose
  code must go through `swing()`/`lift()`/`world_axis_q()` in
  `assets/src/common.py`, which key world-space intentions.
- **Vertex colours are banned in assets**: the software rasteriser ignores
  material colour and tint when a colour attribute exists; export strips them.
- **`ClearBackground` every frame**: it also clears depth; skipping it because
  "the sky covers everything" makes every frame after the first invisible.
- **Texture lifecycle**: scene textures are evicted when the next scene is
  built (`scene_api.build`), and `assets.unload_all` must unload embedded glTF
  textures itself. Both exist because texture slots leak otherwise.
- **raylib maps glTF material i to slot i+1** (slot 0 is its default). Zone
  names come from the GLB JSON chunk; see `src/brainrot/assets/__init__.py`.
- **bpy imports once per process**: asset builds run one subprocess each.
- **Capture correction is measured, not assumed.** Which rasteriser is
  underneath decides whether captures come back flipped and BGR-swapped, and
  `os.name` cannot answer that question — assuming it wrote every `shoot`
  frame upside down on Windows for the entire life of the branch.
  `engine/rl.py:_capture_fix` draws marker frames and reads back where they
  landed. Never read the screen directly.
- **Read-back is one buffer swap behind the draw** on the GPU build here, so
  the probe above draws its marker *until the read is decisive* and runs at
  window creation. A single marker frame read back the previous frame — a blue
  sky, in which blue beats red — concluded the channels were swapped, and every
  `shoot` PNG came out with an orange sky and a brown ocean. Anything that
  wants to capture a frame must present it twice.
- **That landmine was live in a *second* copy of the capture path** until
  2026-08-12. `assets/preview.py` had its own, and it flipped vertically and
  swapped red for blue unconditionally -- right for the software rasteriser,
  wrong for a GPU build, so brown assets came back dark blue and the grid was
  above the model. It also came back solid black, because on a Wayland session
  GLFW opens a Wayland surface and `LoadImageFromScreen` reads nothing off one.
  Both fixed the same way any capture path must be: call
  `brainrot.overlay.x11.prepare()` before `InitWindow`, and go through
  `engine/rl.save_frame`, which *measures* the correction rather than assuming
  it. If another script grows a capture path, it gets these two lines or it
  lies to you.
- **rlgl batches some draws and issues others immediately.** `DrawPlane` goes
  into the render batch and is not submitted until `EndMode3D`; `DrawModelEx`
  draws at once. So a ground plane drawn first is drawn *last* and loses the
  depth test to everything above it. Opaque models hide this; transparent ones
  do not — it punched cloud-shaped holes in the parkour sea. Call `rl.flush()`
  after any batched draw whose order matters.
- **Shared block models must be left as they were found.** The parkour kit is
  built from the same `voxel` models the course is, so a `model.transform` left
  behind by the held item tilts every block of that material in the world on
  the next frame.
- **GLFW window calls block off-thread.** On the GPU build under Windows,
  `SetWindowSize` and friends post to the thread that owns the window and wait
  for it to pump messages. Calling one from a worker thread deadlocks — which
  is why `HeadlessWindow.create` skips a resize to the size it already is.
- **An owned window dies with its owner.** The overlay is owned by the Claude
  Code host window for z-order, and `DestroyWindow` on an owner destroys what
  it owns. The daemon therefore detaches whenever it goes idle. In tests,
  destroy the fake host *after* detaching or it takes the shared raylib window
  with it.
- **Two compositors on one machine both ran the extension, and the strip
  jumped side to side.** A headless gnome-shell (`--headless
  --virtual-monitor`, run by computer-use tooling for an invisible second
  session) loads the same enabled-extensions list as the real one, so two
  extensions pushed snapshots of two different desktops to the daemon's one
  port -- and every reading alternated datagram by datagram: scale 1.0/1.5,
  the work area, the focus, and the host window, which the headless snapshot
  does not contain at all, so the daemon *forgot* it once a second
  (2026-08-25). On screen: the strip flapping between two positions and two
  sizes, and a dragged placement that would not hold. Fixed twice over: the
  extension stays silent when `/proc/self/cmdline` says the compositor is
  headless, and the daemon drops extension datagrams whose *sender* -- UDP
  source port, resolved through /proc to the owning gnome-shell -- is a
  headless shell, because an already-running headless shell keeps its old
  extension code until it restarts. Diagnosed by logging `follow_host`'s
  inputs on every placement change; the two-line log alternation was the
  whole story.
- **Two daemons used to bind the same port quite happily.** UDP with
  `SO_REUSEADDR` did not refuse the second bind; the datagrams then went to
  one of them only -- the first showed the strip on a prompt, the second took
  the `Stop`, and the first left a scene on screen for the rest of the day.
  Every symptom of that reads as a bug in the overlay, and it cost an
  afternoon twice. Fixed 2026-08-09 by dropping `SO_REUSEADDR`: the second
  daemon now refuses to start. UDP has no `TIME_WAIT`, so nothing was bought
  by allowing it. `brainrot doctor`'s `instances` line counts *processes* on
  Linux rather than windows -- an idle duplicate has no window and is
  invisible to a window count right up until it steals an event. Worse, a Store
  Python's `CommandLine` is not readable through WMI, so
  `Where-Object CommandLine -like '*brainrot*'` matches **nothing** and a kill
  that reports no error can have killed no one. Count the windows instead:
  `brainrot doctor` has an `instances` check that does exactly that.
- **A Microsoft Store Python cannot see `%APPDATA%`.** The whole subtree is
  redirected into `…\Local\Packages\<pkg>\LocalCache\Roaming\`, for *reads as
  well as writes*: `(state_dir()/"config.toml").exists()` is False for the
  file you are looking at in Explorer. The owner's `hotkey` setting had never
  once been read. There are several such copies here — the Claude desktop app
  is a packaged app too, so anything it launches gets its own. `Config.load`
  swallows the miss (`except OSError: raw = {}`) and every value silently
  reverts to a default that looks plausible. `brainrot doctor`'s `config`
  check prints the path that is genuinely being read; trust that, not the
  path printed next to "state dir".
- **Showing the window through raylib steals the keyboard.** `set_visible`
  must go through `win32.set_window_shown` (`SW_SHOWNA`), never
  `FLAG_WINDOW_HIDDEN`: raylib unhides via `glfwShowWindow`, GLFW's
  `GLFW_FOCUS_ON_SHOW` defaults on, and `WS_EX_NOACTIVATE` does **not** stop
  it. Measured with `GetGUIThreadInfo`: strip visible at 1.62s, foreground at
  1.64s, *keyboard focus* at 1.69s. Anyone mid-sentence lost the rest of it.
- **That one only reproduces when the owner is in another process**, and it
  cost the fix a whole round trip. A harness whose fake host was a window in
  its own process showed no theft at all, twice, and was believed over the
  live daemon; the correct fix was reverted on the strength of it. If a
  reproduction disagrees with the running system, the reproduction is wrong
  until proven otherwise. `/tmp`-style scratch harness that *does* reproduce
  it: run the real `Overlay` in-process with an `OverlayWindow` subclass that
  checks `foreground_root()` after each window call, and pass it the handle
  of a real window belonging to some other application.
- **A session whose `Stop` never arrives used to think forever**, and the
  strip stayed up with it. The transport cannot promise delivery, and "the
  next event corrects it" is no correction when there is no next event for
  that session. `max_thinking_seconds` (default 900) gives up on one that has
  said nothing for that long; any event from it refreshes the clock.
- **A leaked daemon looks exactly like a window bug.** The same investigation
  first blamed the show path for a 10Hz flap that was really three daemons
  fighting. Check `brainrot doctor`'s `instances` line before theorising.
- **A blend mode does not stop a draw writing depth**, and the symptom is
  *missing geometry* with nothing pointing at what removed it. Additive glows
  stamped their whole quad -- soft, mostly transparent, and at alpha 0 for an
  orb right at the lens -- into the depth buffer, deleting every block drawn
  after them and further away. Measured at up to 1,678 px of the frame for the
  lanterns and **25,589 px (8%) for the landing dust burst**, which nobody had
  suspected. Everything emissive now goes through `fx.no_depth_write` /
  `fx.emissive`, and parkour queues its glows and issues them in one pass after
  all the opaque geometry -- depth writing off is not enough on its own,
  because a glow drawn between two blocks is still *composited* between them.
  Both flushes inside those context managers are load-bearing in opposite
  directions: rlgl issues batched draws late, the depth mask changes at once.
  Audited the whole class with `tools/depth_probe.py`: glows, bursts, cloud
  shelves and reef discs were all guilty and are all fixed; the haze band is 2D
  and writes no depth; islands are solid land and *must* write depth, and
  cannot reach the course anyway because everything in the world below tops out
  at least 7 m under the lowest altitude the course may use (now a test).
- **A head-hitter sits at *three* above the take-off, not the genre's two.**
  The `2bc` -- a lid two blocks over the floor that the head strikes, killing
  the rise and keeping the run -- is the most-used obstacle in serious
  Minecraft parkour, and this motion model cannot have one. A body is 1.8 m
  tall and a jump reaches 1.25, so its head sweeps the two cells above *every*
  take-off: a lid at two is a lid inside the player, and the arc's clearance
  test then correctly refuses every jump under it. At three it is honest and
  mild -- it refuses the arcs that climb hardest and passes the flat and
  descending ones. Making it faithful means adding the game's jump-cancel
  response to `parkourkit`, which does not exist and is a change to the
  physics, not to `spiralplan._ceiling_cells`.
- **A booked action can only fire on a frame boundary.** The planner solves a
  take-off window in continuous time and the loop fires it on the next frame,
  so the body always leaves the ground a little late — and near the ends of an
  arc the feet move most of a third of a metre in one frame at top speed,
  against a nine-centimetre clearance margin. `solve_jump`/`solve_roll` take a
  `late` argument for exactly this and the scene passes it the real `dt`. The
  margin cannot be asked to absorb it: inflating the required height instead
  makes the window vanish entirely.
- **The reflex is a last resort, not a competitor.** It fires at the *edge* of
  a take-off window; the planner books the middle of one. Letting it fire when
  a take-off was already booked replaced a good jump with a marginal one, and
  the feet came down three millimetres inside the hurdle it had cleared.
- **Gantries are only scenery if a *jumping* body clears them.** The height
  was typed in, and the test that guarded it asked for half a metre over a
  standing runner — against an apex of over a metre and a half. `GANTRY_Y` is
  derived from the apex now, and typing it in is no longer possible.
- **`id()` is reused.** A probe that counts live entities by identity
  undercounts by an order of magnitude, because a retired entity's id is
  handed straight back to the next one. The scene counts spawns itself
  (`RunnerScene.spawned`).
- **Blender exits 0 when the script raises.** `blender -b -P thing.py` reports
  success for a build that built nothing, which for a build script is the one
  unforgivable failure mode. `--python-exit-code 1` fixes it and
  `assets/build.py` always passes it — along with `--factory-startup`, so a
  stray add-on or preference cannot change what comes out of a bake.
- **Numbers the gameplay depends on live in `metrics.json`.** Rebuild an asset
  and you must re-run `python assets/measure.py`; `tests/test_assets.py` fails
  if they drift apart. Moving a hoarding's beam moves whether a slide fits
  under it.
- **An asset name is a filename, and a clash is silent.** The spiral's
  Minecraft fence is called `mcfence` because `props.py` already exports the
  runner's trackside `fence`; building it as `fence` replaces that one with no
  error anywhere. Check the names in `src/brainrot/assets/data/` before adding
  a builder.
- **`vinehang`, `dripstone` and `chain` have their origin at the *top*** and
  hang downward (`spiralplan.HANGING`). Dropped on a floor cell like every other
  prop they are underneath it, which looks exactly like a prop that failed to
  load.

