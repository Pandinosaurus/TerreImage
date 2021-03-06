# -*- coding: utf-8 -*-

"""
/***************************************************************************
Name                 : Dockable MirrorMap
Description          : Creates a dockable map canvas
Date                 : February 1, 2011
copyright            : (C) 2011 by Giuseppe Sucameli (Faunalia)
                     : (C) 2014 by CNES
email                : brush.tyler@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QDockWidget

# from qgis.core import
# from qgis.gui import

from mirrorMap import MirrorMap


class DockableMirrorMap(QDockWidget):

    TITLE = "MirrorMap"

    def __init__(self, parent, iface, title = ""):
        QDockWidget.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.mainWidget = MirrorMap(self, iface)
        self.location = Qt.RightDockWidgetArea
        self.title = title

        self.setupUi()
        self.connect(self, SIGNAL("dockLocationChanged(Qt::DockWidgetArea)"), self.setLocation)

    def closeEvent(self, event):
        self.emit(SIGNAL("closed(PyQt_PyObject)"), self)
        del self.mainWidget
        return QDockWidget.closeEvent(self, event)

    def setNumber(self, n = -1):
        if self.title == "":
            title = "%s #%s" % (self.TITLE, n) if n >= 0 else self.TITLE
        else:
            title = self.title
        self.setWindowTitle(title)

    def getMirror(self):
        return self.mainWidget

    def getLocation(self):
        return self.location

    def setLocation(self, location):
        self.location = location

    def setupUi(self):
        self.setObjectName("dockablemirrormap_dockwidget")
        self.setNumber()
        self.setWidget(self.mainWidget)

    def __str__(self):
        return "Vue " + self.title
