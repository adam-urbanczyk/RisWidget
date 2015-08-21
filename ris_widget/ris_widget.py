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

import ctypes
from PyQt5 import Qt
import numpy
import sys
import weakref
#from .qwidgets.layer_stack_current_row_flipbook import ImageStackCurrentRowFlipbook
from . import om
from .image import Image
from .layer import Layer
from .qwidgets.flipbook import Flipbook
from .qwidgets.layer_stack_table import InvertingProxyModel, LayerStackTableModel, LayerStackTableView
from .qgraphicsitems.contextual_info_item import ContextualInfoItem
from .qgraphicsitems.histogram_items import HistogramItem
from .qgraphicsitems.layer_stack_item import LayerStackItem
from .qgraphicsscenes.general_scene import GeneralScene
from .qgraphicsviews.general_view import GeneralView
from .qgraphicsscenes.histogram_scene import HistogramScene
from .qgraphicsviews.histogram_view import HistogramView
from .shared_resources import FREEIMAGE, GL_QSURFACE_FORMAT, NV_PATH_RENDERING_AVAILABLE

class RisWidget(Qt.QMainWindow):
    def __init__(self, window_title='RisWidget', parent=None, window_flags=Qt.Qt.WindowFlags(0), msaa_sample_count=2,
                 layer_stack = tuple(),
                 ImageClass=Image, LayerClass=Layer,
                 LayerStackItemClass=LayerStackItem, GeneralSceneClass=GeneralScene, GeneralViewClass=GeneralView,
                 GeneralViewContextualInfoItemClass=None,
                 HistogramItemClass=HistogramItem, HistogramSceneClass=HistogramScene, HistogramViewClass=HistogramView,
                 HistgramViewContextualInfoItemClass=None,
                 FlipbookClass=Flipbook):
        """A None value for GeneralViewContextualInfoItemClass or HistgramViewContextualInfoItemClass represents 
        ContextualInfoItemNV if the GL_NV_path_rendering extension is available and ContextualInfoItem otherwise."""
        super().__init__(parent, window_flags)
        GL_QSURFACE_FORMAT(msaa_sample_count)
        if window_title is not None:
            self.setWindowTitle(window_title)
        self.setAcceptDrops(True)
        if GeneralViewContextualInfoItemClass is None or HistgramViewContextualInfoItemClass is None:
            if NV_PATH_RENDERING_AVAILABLE():
                from .qgraphicsitems.contextual_info_item_nv import ContextualInfoItemNV
            if GeneralViewContextualInfoItemClass is None:
                GeneralViewContextualInfoItemClass = ContextualInfoItemNV if NV_PATH_RENDERING_AVAILABLE() else ContextualInfoItem
            if HistgramViewContextualInfoItemClass is None:
                HistgramViewContextualInfoItemClass = ContextualInfoItemNV if NV_PATH_RENDERING_AVAILABLE() else ContextualInfoItem
        self.ImageClass = ImageClass
        self.LayerClass = LayerClass
        self.FlipbookClass = FlipbookClass
        self._init_scenes_and_views(
            ImageClass, LayerClass,
            LayerStackItemClass, GeneralSceneClass, GeneralViewClass,
            GeneralViewContextualInfoItemClass,
            HistogramItemClass, HistogramSceneClass, HistogramViewClass,
            HistgramViewContextualInfoItemClass)
        self._layer_stack = None
        self.layer_stack = layer_stack
        self._init_actions()
        self._init_toolbars()
        self._init_menus()

    def _init_actions(self):
        self.layer_stack_reset_curr_min_max = Qt.QAction(self)
        self.layer_stack_reset_curr_min_max.setText('Reset Min/Max')
        self.layer_stack_reset_curr_min_max.setShortcut(Qt.Qt.Key_M)
        self.layer_stack_reset_curr_min_max.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.layer_stack_reset_curr_min_max.triggered.connect(self._on_reset_min_max)
        self.layer_stack_toggle_curr_auto_min_max = Qt.QAction(self)
        self.layer_stack_toggle_curr_auto_min_max.setText('Toggle Auto Min/Max')
        self.layer_stack_toggle_curr_auto_min_max.setShortcut(Qt.Qt.Key_A)
        self.layer_stack_toggle_curr_auto_min_max.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.layer_stack_toggle_curr_auto_min_max.triggered.connect(self._on_toggle_auto_min_max)
        self.addAction(self.layer_stack_toggle_curr_auto_min_max) # Necessary for shortcut to work as this action does not appear in a menu or toolbar
        self.layer_stack_reset_curr_gamma = Qt.QAction(self)
        self.layer_stack_reset_curr_gamma.setText('Reset \u03b3')
        self.layer_stack_reset_curr_gamma.setShortcut(Qt.Qt.Key_G)
        self.layer_stack_reset_curr_gamma.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.layer_stack_reset_curr_gamma.triggered.connect(self._on_reset_gamma)
        if sys.platform == 'darwin':
            self.exit_fullscreen_action = Qt.QAction(self)
            # If self.exit_fullscreen_action's text were "Exit Full Screen Mode" as we desire,
            # we would not be able to add it as a menu entry (http://doc.qt.io/qt-5/qmenubar.html#qmenubar-on-os-x).
            # "Leave Full Screen Mode" is a compromise.
            self.exit_fullscreen_action.setText('Leave Full Screen Mode')
            self.exit_fullscreen_action.triggered.connect(self.showNormal)
            self.exit_fullscreen_action.setShortcut(Qt.Qt.Key_Escape)
            self.exit_fullscreen_action.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.main_view.zoom_to_fit_action.setShortcut(Qt.Qt.Key_QuoteLeft)
        self.main_view.zoom_to_fit_action.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.main_view.zoom_one_to_one_action.setShortcut(Qt.Qt.Key_1)
        self.main_view.zoom_one_to_one_action.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.main_scene.layer_stack_item.examine_layer_mode_action.setShortcut(Qt.Qt.Key_Space)
        self.main_scene.layer_stack_item.examine_layer_mode_action.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.main_scene_snapshot_action = Qt.QAction(self)
        self.main_scene_snapshot_action.setText('Main View Snapshot')
        self.main_scene_snapshot_action.setShortcut(Qt.Qt.Key_S)
        self.main_scene_snapshot_action.setShortcutContext(Qt.Qt.ApplicationShortcut)
        self.main_scene_snapshot_action.setToolTip('Append snapshot of .main_view to .flipbook.pages')

    @staticmethod
    def _format_zoom(zoom):
        if int(zoom) == zoom:
            return '{}'.format(int(zoom))
        else:
            txt = '{:.2f}'.format(zoom)
            if txt[-2:] == '00':
                return txt[:-3]
            if txt[-1:] == '0':
                return txt[:-1]
            return txt

    def _init_scenes_and_views(self, ImageClass, LayerClass, LayerStackItemClass, GeneralSceneClass, GeneralViewClass, GeneralViewContextualInfoItemClass,
                               HistogramItemClass, HistogramSceneClass, HistogramViewClass, HistgramViewContextualInfoItemClass):
        self.main_scene = GeneralSceneClass(self, ImageClass, LayerStackItemClass, self._get_primary_image_stack_current_layer_row, GeneralViewContextualInfoItemClass)
        self.main_view = GeneralViewClass(self.main_scene, self)
        self.setCentralWidget(self.main_view)
        self.histogram_scene = HistogramSceneClass(self, self.main_scene.layer_stack_item, HistogramItemClass, HistgramViewContextualInfoItemClass)
        self.histogram_dock_widget = Qt.QDockWidget('Histogram', self)
        self.histogram_view, self._histogram_frame = HistogramViewClass.make_histogram_view_and_frame(self.histogram_scene, self.histogram_dock_widget)
        self.histogram_dock_widget.setWidget(self._histogram_frame)
        self.histogram_dock_widget.setAllowedAreas(Qt.Qt.BottomDockWidgetArea | Qt.Qt.TopDockWidgetArea)
        self.histogram_dock_widget.setFeatures(
            Qt.QDockWidget.DockWidgetClosable | Qt.QDockWidget.DockWidgetFloatable |
            Qt.QDockWidget.DockWidgetMovable | Qt.QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(Qt.Qt.BottomDockWidgetArea, self.histogram_dock_widget)
        self.layer_stack_table_dock_widget = Qt.QDockWidget('Layer Stack', self)
        self.layer_stack_table_model = LayerStackTableModel(
            self.main_scene.layer_stack_item.override_enable_auto_min_max_action,
            self.main_scene.layer_stack_item.examine_layer_mode_action,
            ImageClass,
            LayerClass)
#       self.layer_stack_table_model_inverter = InvertingProxyModel(self.layer_stack_table_model)
#       self.layer_stack_table_model_inverter.setSourceModel(self.layer_stack_table_model)
        self.layer_stack_table_view = LayerStackTableView(self.layer_stack_table_model)
#       self.layer_stack_table_view.setModel(self.layer_stack_table_model_inverter)
        self.layer_stack_table_view.setModel(self.layer_stack_table_model)
        self.layer_stack_table_model.setParent(self.layer_stack_table_view)
        self.layer_stack_table_selection_model = self.layer_stack_table_view.selectionModel()
        self.layer_stack_table_selection_model.currentRowChanged.connect(self._on_layer_stack_table_current_row_changed)
        self.layer_stack_table_dock_widget.setWidget(self.layer_stack_table_view)
        self.layer_stack_table_dock_widget.setAllowedAreas(Qt.Qt.AllDockWidgetAreas)
        self.layer_stack_table_dock_widget.setFeatures(Qt.QDockWidget.DockWidgetClosable | Qt.QDockWidget.DockWidgetFloatable | Qt.QDockWidget.DockWidgetMovable)
        
        # TODO: make layer stack table widget default location be at window bottom, adjacent to histogram
        self.addDockWidget(Qt.Qt.TopDockWidgetArea, self.layer_stack_table_dock_widget)
        self._most_recently_created_flipbook = None
        self._make_main_flipbook()

    def _init_toolbars(self):
        self.main_view_toolbar = self.addToolBar('Main View')
        self.main_view_zoom_combo = Qt.QComboBox(self)
        self.main_view_toolbar.addWidget(self.main_view_zoom_combo)
        self.main_view_zoom_combo.setEditable(True)
        self.main_view_zoom_combo.setInsertPolicy(Qt.QComboBox.NoInsert)
        self.main_view_zoom_combo.setDuplicatesEnabled(True)
        self.main_view_zoom_combo.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContents)
        for zoom in GeneralView._ZOOM_PRESETS:
            self.main_view_zoom_combo.addItem(self._format_zoom(zoom * 100) + '%')
        self.main_view_zoom_combo.setCurrentIndex(GeneralView._ZOOM_ONE_TO_ONE_PRESET_IDX)
        self.main_view_zoom_combo.activated[int].connect(self._main_view_zoom_combo_changed)
        self.main_view_zoom_combo.lineEdit().returnPressed.connect(self._main_view_zoom_combo_custom_value_entered)
        self.main_view.zoom_changed.connect(self._main_view_zoom_changed)
        self.main_view_toolbar.addAction(self.main_view.zoom_to_fit_action)
        self.main_view_toolbar.addAction(self.layer_stack_reset_curr_min_max)
        self.main_view_toolbar.addAction(self.layer_stack_reset_curr_gamma)
        self.main_view_toolbar.addAction(self.main_scene.layer_stack_item.override_enable_auto_min_max_action)
        self.main_view_toolbar.addAction(self.main_scene.layer_stack_item.examine_layer_mode_action)
        self.main_view_toolbar.addAction(self.layer_stack_table_dock_widget.toggleViewAction())
        self.histogram_view_toolbar = self.addToolBar('Histogram View')
        self.histogram_view_toolbar.addAction(self.histogram_dock_widget.toggleViewAction())

    def _init_menus(self):
        mb = self.menuBar()
        m = mb.addMenu('View')
        if sys.platform == 'darwin':
            m.addAction(self.exit_fullscreen_action)
            m.addSeparator()
        m.addAction(self.main_view.zoom_to_fit_action)
        m.addAction(self.main_view.zoom_one_to_one_action)
        m.addSeparator()
        m.addAction(self.layer_stack_reset_curr_min_max)
        m.addAction(self.layer_stack_reset_curr_gamma)
        m.addAction(self.main_scene.layer_stack_item.examine_layer_mode_action)
        m.addSeparator()
        m.addAction(self.main_scene.layer_stack_item.layer_name_in_contextual_info_action)
        m.addAction(self.main_scene.layer_stack_item.image_name_in_contextual_info_action)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasImage():
            image = self.ImageClass.from_qimage(qimage=qimage, name=mime_data.urls()[0].toDisplayString() if mime_data.hasUrls() else None)
            if image is not None:
                layer = self.LayerClass(image=image)
                self.main_flipbook.pages[:] = [layer]
                event.accept()
        elif mime_data.hasUrls():
            # Note: if the URL is a "file://..." representing a local file, toLocalFile returns a string
            # appropriate for feeding to Python's open() function.  If the URL does not refer to a local file,
            # toLocalFile returns None.
            fpaths = list(map(lambda url: url.toLocalFile(), mime_data.urls()))
            if len(fpaths) > 0 and fpaths[0].startswith('file:///.file/id=') and sys.platform == 'darwin':
                e = 'In order for image file drag & drop to work on OS X >=10.10 (Yosemite), please upgrade to at least Qt 5.4.1.'
                Qt.QMessageBox.information(self, 'Qt Upgrade Required', e)
                return
            freeimage = FREEIMAGE(show_messagebox_on_error=True, error_messagebox_owner=self)
            if freeimage is None:
                return
            self.main_flipbook.pages[:] = [self.LayerClass(self.ImageClass(freeimage.read(fpath), name=fpath)) for fpath in fpaths]
            event.accept()

    @property
    def layer_stack(self):
        """If you wish to replace the current .layer_stack, it may be done by assigning to this
        property.  For example:
        rw.layer_stack = [rw.LayerClass(rw.ImageClass(freeimage.read(str(p))) for p in pathlib.Path('./').glob('*.png')]

        Modifying rw.main_scene.layer_stack_item.layer_stack directly will not cause
        rw.layer_stack_table_model.signling_list (which contains Layers and is therefore a layer
        stack) to update, leaving the contents of the main view and layer table out of sync.  The
        same is true for modifying rw.layer_stack_table_model.signling_list directly, mutatis
        mutandis.  rw.layer_stack's setter takes care of setting both."""
        return self._layer_stack

    @layer_stack.setter
    def layer_stack(self, v):
        if self._layer_stack is not None:
            self._layer_stack.name_changed.disconnect(self._on_layer_stack_name_changed)
            self._layer_stack.inserted.disconnect(self._on_inserted_into_layer_stack)
            self._layer_stack.replaced.disconnect(self._on_replaced_in_layer_stack)
        # If v is not a SignalingList and also is missing at least one list modification signal that we need, convert v
        # to a SignalingList
        if not isinstance(v, om.SignalingList) and any(not hasattr(v, signal) for signal in ('inserted', 'removed', 'replaced', 'name_changed')):
            v = om.SignalingList(v)
        self._layer_stack = v
        v.name_changed.connect(self._on_layer_stack_name_changed)
        # Must be QueuedConnection in order to avoid race condition where self._on_inserted_into_layer_stack is
        # called before self.layer_stack_table_model._on_inserted, causing self._on_inserted_into_layer_stack to
        # attempt to make row 0 in self.layer_stack_table_view current before self.layer_stack_table_model
        # is even aware that a row has been inserted.
        v.inserted.connect(self._on_inserted_into_layer_stack, Qt.Qt.QueuedConnection)
        v.replaced.connect(self._on_replaced_in_layer_stack)
        self.main_scene.layer_stack_item.layer_stack = v
        self.layer_stack_table_model.signaling_list = v

    def _get_primary_image_stack_current_layer_row(self):
        # Selection model is with reference to table view's model, which is the inverting proxy model
#       pmidx = self.layer_stack_table_selection_model.currentIndex()
#       if pmidx.isValid():
#           midx = self.layer_stack_table_model_inverter.mapToSource(pmidx)
#           if midx.isValid():
#               return midx.row()
        midx = self.layer_stack_table_selection_model.currentIndex()
        if midx.isValid():
            return midx.row()

    current_layer_row = property(_get_primary_image_stack_current_layer_row)

    @property
    def current_layer(self):
        row = self.current_layer_row
        if row is not None:
            return self.layer_stack[row]

    def replace_current_layer(self, layer):
        row = self.current_layer_row
        if row is None:
            raise IndexError('No row in .layer_stack_table_view is current/focused.')
        else:
            self.layer_stack[row] = layer

    @property
    def layer(self):
        """rw.layer: A convenience property; equivalent to rw.layer_stack[0], with the minor difference
        that assigning to rw.layer_stack[0] when len(rw.layer_stack) is 0 would raise an exception, whereas
        assigning to rw.layer in that situation causes the assigned Layer to be inserted at rw.layer_stack[0]."""
        layer_stack = self.layer_stack
        return layer_stack[0] if layer_stack else None

    @layer.setter
    def layer(self, layer):
        layer_stack = self.layer_stack
        if layer_stack:
            layer_stack[0] = layer
        else:
            layer_stack.append(layer)

    @property
    def image(self):
        """rw.image: A Convenience property; equivalent to rw.layer_stack[0].image, with minor differences:
        * Querying rw.image will not raise an exception when len(rw.layer_stack) is 0.  Instead, None is returned.
        * Assinging to rw.image when len(rw.layer_stack) is 0 does not raise an exception.  Instead, it causes
          insertion of a new Layer at rw.layer_stack[0] containing the assigned image."""
        layer_stack = self.layer_stack
        if layer_stack:
            return layer_stack[0].image

    @image.setter
    def image(self, image):
        if image is not None and not isinstance(image, Image):
            raise ValueError('The value assigned to rw.image must be an instance of Image or a subclass thereof, or None.  '
                             '(Did you mean to assign to rw.image_data?)')
        if self.bottom_layer is None:
            self.bottom_layer = self.LayerClass(image)
        else:
            self.bottom_layer.image = image

    @property
    def image_data(self):
        """rw.image_data: A convenience property; equivalent to rw.layer_stack[0].image.data, with minor
        differences:
        * Querying rw.image_data will not raise an exception when len(rw.layer_stack) is 0 or
        rw.layer_stack[0].image is None.  Instead, None is returned.
        * Assigning to rw.image_data will not raise an exception when len(rw.layer_stack) is 0 or
        rw.layer_stack[0].image is None.  Instead, it causes insertion of a new Layer at rw.layer_stack[0]
        containing a new Image that contains the assigned data."""
        layer_stack = self.layer_stack
        if layer_stack:
            return layer_stack[0].image.data

    @image_data.setter
    def image_data(self, image_data):
        if self.bottom_layer is None:
            self.bottom_layer = self.LayerClass(self.ImageClass(image_data))
        elif self.bottom_layer.image is None:
            self.bottom_layer.image = self.ImageClass(image_data)
        else:
            self.bottom_layer.image.set_data(image_data)

    @property
    def image_data_T(self):
        """rw.image_data_T: A convenience property; equivalent to rw.layer_stack[0].image.data_T, with minor
        differences:
        * Querying rw.image_data_T will not raise an exception when len(rw.layer_stack) is 0 or
        rw.layer_stack[0].image is None.  Instead, None is returned.
        * Assigning to rw.image_data_T will not raise an exception when len(rw.layer_stack) is 0 or
        rw.layer_stack[0].image is None.  Instead, it causes insertion of a new Layer at rw.layer_stack[0]
        containing a new Image that contains the assigned data."""
        layer_stack = self.layer_stack
        if layer_stack:
            return layer_stack[0].image.data_T

    @image_data.setter
    def image_data_T(self, image_data_T):
        if self.bottom_layer is None:
            self.bottom_layer = self.LayerClass(self.ImageClass(image_data, shape_is_width_height=False))
        elif self.bottom_layer.image is None:
            self.bottom_layer.image = self.ImageClass(image_data, shape_is_width_height=False)
        else:
            self.bottom_layer.image.set_data(image_data, shape_is_width_height=False)

    @property
    def main_flipbook(self):
        return self._main_flipbook

    def _make_main_flipbook(self):
        self._main_flipbook = self.FlipbookClass(self)

    def make_flipbook(self, images=None, name='Flipbook'):
        """The images argument may be any mixture of ris_widget.image.Image objects and raw data iterables of the sort that
        may be assigned to RisWidget.image_data or RisWidget.image_data_T.
        If None is supplied for images, an empty flipbook is created."""
        if images is not None:
            if not isinstance(images, SignalingList):
                images = SignalingList([image if isinstance(image, self.ImageClass) else self.ImageClass(image, name=str(image_idx)) for image_idx, image in enumerate(images)])
        flipbook = (self.layer_stack, self.layer_stack_table_selection_model, images)
        dock_widget = Qt.QDockWidget(name, self)
        dock_widget.setAttribute(Qt.Qt.WA_DeleteOnClose)
        dock_widget.setWidget(flipbook)
        flipbook.destroyed.connect(dock_widget.deleteLater) # Get rid of containing dock widget when flipbook is programatically destroyed
        dock_widget.setAllowedAreas(Qt.Qt.LeftDockWidgetArea | Qt.Qt.RightDockWidgetArea)
        dock_widget.setFeatures(Qt.QDockWidget.DockWidgetClosable | Qt.QDockWidget.DockWidgetFloatable | Qt.QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, dock_widget)
        self._most_recently_created_flipbook = weakref.ref(flipbook)
        return flipbook

    @property
    def most_recently_created_flipbook(self):
        """The .most_recently_created_flipbook property represents the flipbook most recently created by calling the
        .make_flipbook(..) method.  If that flipbook has since been closed, or if none has been created, the value of
        .most_recently_created_flipbook is None.

        Note that the main flipbook, where images dropped into the main view end up, is available via the
        main_flipbook property."""
        if self._most_recently_created_flipbook is None:
            return
        fb = self._most_recently_created_flipbook()
        if fb is not None:
            try:
                fb.objectName()
                return fb
            except RuntimeError:
                # Qt part of the object was deleted out from under the Python part
                self._most_recently_created_flipbook = None # Clean up our weakref to the Python part

    def _on_layer_stack_name_changed(self, layer_stack):
        assert layer_stack is self.layer_stack
        name = layer_stack.name
        dw_title = 'Layer Stack'
        if len(name) > 0:
            dw_title += ' "{}"'.format(name)
        self.layer_stack_table_dock_widget.setWindowTitle(dw_title)

    def _on_layer_stack_table_current_row_changed(self, midx, prev_midx):
        row = self.current_layer_row
        layer = None if row is None else self.layer_stack[row]
        self.layer_stack_table_model.on_view_current_row_changed(row)
        self.histogram_scene.histogram_item.layer = layer
        lsi = self.main_scene.layer_stack_item
        if lsi.examine_layer_mode_enabled:
            # The appearence of a layer_stack_item may depend on which layer table row is current when
            # "examine layer mode" is enabled.
            lsi.update()

    def _on_inserted_into_layer_stack(self, idx, layers):
        assert len(self.layer_stack) > 0
        if not self.layer_stack_table_selection_model.currentIndex().isValid():
#           self.layer_stack_table_selection_model.setCurrentIndex(
#               self.layer_stack_table_model_inverter.index(0, 0),
#               Qt.QItemSelectionModel.SelectCurrent | Qt.QItemSelectionModel.Rows)
            self.layer_stack_table_selection_model.setCurrentIndex(
                self.layer_stack_table_model.index(0, 0),
                Qt.QItemSelectionModel.SelectCurrent | Qt.QItemSelectionModel.Rows)

    def _on_replaced_in_layer_stack(self, idxs, old_layers, new_layers):
        current_midx = self.layer_stack_table_selection_model.currentIndex()
        if current_midx.isValid():
            try:
                change_idx = idxs.index(current_midx.row())
            except ValueError:
                return
            old_current, new_current = old_layers[change_idx], new_layers[change_idx]
            self.histogram_scene.histogram_item.image = new_current

    def _main_view_zoom_changed(self, zoom_preset_idx, custom_zoom):
        assert zoom_preset_idx == -1 and custom_zoom != 0 or zoom_preset_idx != -1 and custom_zoom == 0, \
               'zoom_preset_idx XOR custom_zoom must be set.'
        if zoom_preset_idx == -1:
            self.main_view_zoom_combo.lineEdit().setText(self._format_zoom(custom_zoom * 100) + '%')
        else:
            self.main_view_zoom_combo.setCurrentIndex(zoom_preset_idx)

    def _main_view_zoom_combo_changed(self, idx):
        self.main_view.zoom_preset_idx = idx

    def _main_view_zoom_combo_custom_value_entered(self):
        txt = self.main_view_zoom_combo.lineEdit().text()
        percent_pos = txt.find('%')
        scale_txt = txt if percent_pos == -1 else txt[:percent_pos]
        try:
            self.main_view.custom_zoom = float(scale_txt) * 0.01
        except ValueError:
            e = 'Please enter a number between {} and {}.'.format(
                self._format_zoom(GeneralView._ZOOM_MIN_MAX[0] * 100),
                self._format_zoom(GeneralView._ZOOM_MIN_MAX[1] * 100))
            Qt.QMessageBox.information(self, 'self.windowTitle() Input Error', e)
            self.main_view_zoom_combo.setFocus()
            self.main_view_zoom_combo.lineEdit().selectAll()

    def _on_reset_min_max(self):
        layer = self.current_layer
        if layer is not None:
            del layer.min
            del layer.max

    def _on_reset_gamma(self):
        layer = self.current_layer
        if layer is not None:
            del layer.gamma

    def _on_toggle_auto_min_max(self):
        layer = self.current_layer
        if layer is not None:
            layer.auto_min_max_enabled = not layer.auto_min_max_enabled

if __name__ == '__main__':
    import sys
    app = Qt.QApplication(sys.argv)
    rw = RisWidget()
    rw.show()
    app.exec_()
