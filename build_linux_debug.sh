PYTHONOPTIMIZE=2 pyinstaller \
--hidden-import "pynput.keyboard._xorg" \
--hidden-import "pynput.mouse._xorg" \
--clean \
--noconsole \
--noupx \
--onefile \
--debug=ALL \
--name="Blender Launcher" \
source/main.py
