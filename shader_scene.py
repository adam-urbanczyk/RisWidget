# The MIT License (MIT)
#
# Copyright (c) 2014-2015 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum <ice.rikh@gmail.com>

from .gl_resources import GL
from pathlib import Path
from PyQt5 import Qt

#from ._qt_debug import qevent_type_value_enum_string #TODO: remove

class ShaderScene(Qt.QGraphicsScene):
    """update_mouseover_info_signal serves to relay mouseover info plaintext/html change requests
    from any items in the ShaderScene to every attached Viewport's ViewportOverlayScene's
    mouseover_text_item (which is part of ViewportOverlayScene so that the text is view-relative
    rather than scaling with the shader item).  The clear_mouseover_info(self, requester) and
    update_mouseover_info(self, string, is_html, requester) member functions provide an interface that
    relieves the need to ensure that a single pair of mouse-exited-so-clear-the-text and
    mouse-over-new-thing-so-display-some-other-text events are handled in order.

    If the second parameter is True, the first parameter is interpreted as html, and is treated
    as a plaintext string otherwise."""
    update_mouseover_info_signal = Qt.pyqtSignal(str, bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.requester_of_current_nonempty_mouseover_info = None

    def clear_mouseover_info(self, requester):
        self.update_mouseover_info(None, False, requester)

    def update_mouseover_info(self, string, is_html, requester):
        if string is None or len(string) == 0:
            if self.requester_of_current_nonempty_mouseover_info is None or self.requester_of_current_nonempty_mouseover_info is requester:
                self.requester_of_current_nonempty_mouseover_info = None
                self.update_mouseover_info_signal.emit('', False)
        else:
            self.requester_of_current_nonempty_mouseover_info = requester
            self.update_mouseover_info_signal.emit(string, is_html)

#   def event(self, event): #TODO: remove
#       print(type(event), qevent_type_value_enum_string(event))
#       return super().event(event)

class ShaderItem(Qt.QGraphicsItem):
    def __init__(self, parent_item=None):
        super().__init__(parent_item)
        self.view_resources = {}
        self._image = None
        self._image_id = 0

    def build_shader_prog(self, desc, vert_fn, frag_fn, shader_view):
        source_dpath = Path(__file__).parent / 'shaders'
        prog = Qt.QOpenGLShaderProgram(shader_view)
        if not prog.addShaderFromSourceFile(Qt.QOpenGLShader.Vertex, str(source_dpath / vert_fn)):
            raise RuntimeError('Failed to compile vertex shader "{}" for {} {} shader program.'.format(vert_fn, type(self).__name__, desc))
        if not prog.addShaderFromSourceFile(Qt.QOpenGLShader.Fragment, str(source_dpath / frag_fn)):
            raise RuntimeError('Failed to compile fragment shader "{}" for {} {} shader program.'.format(frag_fn, type(self).__name__, desc))
        if not prog.link():
            raise RuntimeError('Failed to link {} {} shader program.'.format(type(self).__name__, desc))
        vrs = self.view_resources[shader_view]
        if 'progs' not in vrs:
            vrs['progs'] = {desc : prog}
        else:
            vrs['progs'][desc] = prog

    def free_shader_view_resources(self, shader_view):
        for item in self.childItems():
            if issubclass(type(item), ShaderItem):
                item.free_shader_view_resources(shader_view)
        if shader_view in self.view_resources:
            vrs = self.view_resources[shader_view]
            if 'tex' in vrs:
                vrs['tex'].destroy()
            if 'progs' in vrs:
                for prog in vrs['progs'].values():
                    prog.removeAllShaders()
            del self.view_resources[shader_view]

    def on_image_changing(self, image):
        self._image = image
        self._image_id += 1
        self.update()

    def _normalize_min_max(self, min_max):
        r = self._image.range
        min_max -= r[0]
        min_max /= r[1] - r[0]

class ShaderTexture:
    """QOpenGLTexture does not support support GL_LUMINANCE*_EXT as specified by GL_EXT_texture_integer,
    which is required for integer textures in OpenGL 2.1 (QOpenGLTexture does support GL_RGB*U/I formats,
    but these were introduced with OpenGL 3.0 and should not be relied upon in 2.1 contexts).  So, in
    cases where GL_LUMINANCE*_EXT format textures may be required, we use ShaderTexture rather than
    QOpenGLTexture."""
    def __init__(self, target):
        self.texture_id = GL().glGenTextures(1)
        self.target = target

    def bind(self):
        GL().glBindTexture(self.target, self.texture_id)

    def release(self):
        GL().glBindTexture(self.target, 0)

    def free(self):
        GL().glDeleteTextures(1, self.texture_id)
        del self.texture_id
