# 3D Engine Support

The DOOM 2016 combat simulator now runs on top of the [pyglet](https://pyglet.org/) 3D/2D multimedia framework.

## Dependency

The mini-game requires the optional `pyglet` package. When the launcher starts
the simulator it attempts to install the dependency automatically using `pip`.
If that step fails (for example due to networking restrictions), install it
manually with:

```bash
pip install pyglet
```

For convenience the repository also includes a helper manifest. Run:

```bash
python -m pip install -r requirements-3d.txt
```

to install the recommended `pyglet` version alongside any future 3D engine
dependencies we document.

The launcher detects the package at runtime. If it is missing, the DOOM simulator remains unavailable and the GUI provides guidance instead of raising an exception. The remainder of the launcher continues to rely on the Tkinter standard library interface, so the dependency is optional.

## Runtime Notes

* pyglet opens its own window for rendering. The Tkinter mini-game panel keeps track of the session and forwards the statistics reported by the engine.
* The engine thread is shut down automatically when the session ends or when the Tkinter window is closed.
* To troubleshoot rendering issues make sure your environment has an OpenGL-compatible driver. pyglet will fall back to software rendering when possible, but a GPU-backed context delivers the best experience.
