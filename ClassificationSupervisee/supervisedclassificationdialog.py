# -*- coding: utf-8 -*-
"""
/*=========================================================================

Copyright (c) Centre National d'Etudes Spatiales
All rights reserved.

The "ClassificationSupervisee" Quantum GIS plugin is distributed
under the CeCILL licence version 2.
See Copyright/Licence_CeCILL_V2-en.txt or
http://www.cecill.info/licences/Licence_CeCILL_V2-en.txt for more details.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS ``AS IS''
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=========================================================================*/
"""

from PyQt4 import QtCore, QtGui
from RasterLayerSelectorTable import RasterLayerSelectorTable
from VectorLayerSelectorTable import VectorLayerSelectorTable
from ConfusionMatrixViewer import ConfusionMatrixViewer
from TerreImage.terre_image_run_process import TerreImageProcess
from cropVectorDataToImage import cropVectorDataToImage
import mergeVectorData

from QGisLayers import QGisLayers
from QGisLayers import QGisLayerType
from classif import full_classification

import os
import shutil
import datetime

# import logging for debug messages
from TerreImage import terre_image_logging
logger = terre_image_logging.configure_logger()

def ensure_clean_dir(d):
    #d = os.path.dirname(f)
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)


def saferemovefile(filename):
    if os.path.exists(filename):
        os.remove(filename)


def transform_spaces(filename):
    from copy import deepcopy
    ret = deepcopy(filename)
    return ret.replace(' ', '_')


def ensure_dir_exists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def get_working_dir():
    dir = os.path.join( os.getenv("HOME"), "ClassificationSupervisee", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    ensure_dir_exists(dir)
    return dir

'''
class StatusChanger():
    def __init__(self, classifdialog):
        self.classifdialog = classifdialog
        self.classifdialog.setClassifyingStatus()


    def __del__(self):
        self.classifdialog.clearStatus()
'''

'''
class GenericThread(QtCore.QThread):
 def __init__(self, function, *args, **kwargs):
  QtCore.QThread.__init__(self)
  self.function = function
  self.args = args
  self.kwargs = kwargs

 def __del__(self):
  self.wait()

 def run(self):
  self.function(*self.args,**self.kwargs)
  return
'''


class SupervisedClassificationDialog(QtGui.QDialog):
    def __init__(self, iface, working_dir=None):
        QtGui.QDialog.__init__(self)
        QtGui.QApplication.restoreOverrideCursor()

        self.app_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), "win32", "bin")
        logger.debug( "self.app_dir {}".format(self.app_dir) )

        #self.setupUi()
        QGisLayers.setInterface(iface)
        self.output_dir = None

#         if not OSIdentifier.isWindows():
#             QtGui.QMessageBox.critical( self, \
#                                         u"Erreur", \
#                                         u"Système d'exploitation non supporté" )
#             return

    def setupUi(self):
        self.setWindowTitle(u"Classification Supervisée")

        self.mainlayout = QtGui.QVBoxLayout()

        #rasterlayers = QGisLayers.getRasterLayers()
        rasterlayers = self.layers
        self.rasterlayerselector = RasterLayerSelectorTable(rasterlayers, self.output_dir, self.main_layer, self.main_layer_bands)

        vectorlayers = QGisLayers.getVectorLayers(QGisLayerType.POLYGON)
        self.vectorlayerselector = VectorLayerSelectorTable(vectorlayers)

        self.layerlayout = QtGui.QHBoxLayout()
        self.layerlayout.addWidget(self.rasterlayerselector)
        self.layerlayout.addWidget(self.vectorlayerselector)

#         self.outputlayout = QtGui.QHBoxLayout()
#
#         self.outputdirwidget = QtGui.QLineEdit()
#         self.outputdirselectorbutton = QtGui.QPushButton("...")
#         #self.setOutputDir( tempfile.mkdtemp(prefix='ClassificationSupervisee_', dir=None) )
#         self.setOutputDir( self.output_dir )
#
#         self.outputlayout.addWidget( QtGui.QLabel(u"Répertoire de sortie") )
#         self.outputlayout.addWidget( self.outputdirwidget )
#         self.outputlayout.addWidget( self.outputdirselectorbutton )

        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)

        self.classifButton = QtGui.QPushButton("Classification")
        self.cancelButton = QtGui.QPushButton("Annuler")

        self.bottomLayout = QtGui.QHBoxLayout()
        self.statusLabel = QtGui.QLabel()
        self.buttonBox.addButton(self.classifButton, QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.cancelButton, QtGui.QDialogButtonBox.RejectRole)
        self.bottomLayout.addWidget(self.statusLabel)
        self.bottomLayout.addStretch()
        self.bottomLayout.addWidget(self.buttonBox)

        self.mainlayout.addLayout(self.layerlayout)
        # self.mainlayout.addLayout(self.outputlayout)
        self.mainlayout.addLayout(self.bottomLayout)
        self.setLayout(self.mainlayout)

        QtCore.QObject.connect(self.classifButton, QtCore.SIGNAL("clicked()"), self.setClassifyingStatus)
        QtCore.QObject.connect(self.classifButton, QtCore.SIGNAL("clicked()"), self.classify)

        QtCore.QObject.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelPressed)

        # QtCore.QObject.connect(self.outputdirselectorbutton, QtCore.SIGNAL("clicked()"), self.selectOutputDir)

    def set_layers(self, layers, main_layer=None, main_layer_bands = None):
        self.main_layer = main_layer
        self.main_layer_bands = main_layer_bands
        self.layers = [self.main_layer] + layers

    def set_directory(self, working_dir):
        if working_dir is not None:
            self.output_dir = os.path.join( working_dir, "Classification" )
            ensure_dir_exists( self.output_dir )
        else:
            self.output_dir = get_working_dir()

    def update_layers(self, layers):
        self.layers = layers
        # for layer in self.layers:
        #    logger.debug(layer.name())
        vectorlayers = QGisLayers.getVectorLayers(QGisLayerType.POLYGON)
        self.vectorlayerselector.set_layers(vectorlayers)
        rasterlayers = layers
        self.rasterlayerselector.set_layers(rasterlayers)

    def cancelPressed(self):
        self.close()

    def setOutputDir(self, dirname):
        self.outputdirwidget.setText(dirname)

    def getOutputDir(self):
        return self.output_dir #outputdirwidget.text())

    def selectOutputDir(self):
        filedialog = QtGui.QFileDialog()
        filedialog.setConfirmOverwrite(True);
        filedialog.setFileMode(QtGui.QFileDialog.Directory);
        filedialog.setNameFilter(u"Répertoire");
        if filedialog.exec_():
            self.setOutputDir(filedialog.selectedFiles()[0])

    def setClassifyingStatus(self):
        self.statusLabel.setText(u"<font color=\"Red\">Classification en cours...</font>")
        QtGui.QApplication.processEvents()
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

    def clearStatus(self):
        self.statusLabel.setText("")

    def classify(self):
        dirDest = QtGui.QFileDialog.getExistingDirectory( None, u"Répertoire de destination des fichiers de la classification", self.output_dir )
        if dirDest :
            self.output_dir = dirDest


        logger.debug( "classify" )
        simulation = False
        try:
            # Get rasters
            selectedrasterlayers = self.rasterlayerselector.getSelectedOptions()
            logger.debug( "selectedrasterlayers {}".format(selectedrasterlayers) )
            if len(selectedrasterlayers) < 1:
                QtGui.QMessageBox.critical( self, \
                                            u"Erreur", \
                                            u"Aucune couche raster sélectionnée" )
                return

            # Get vectors
            selectedvectorlayers = self.vectorlayerselector.getSelectedOptions()
            if len(selectedvectorlayers) < 2:
                QtGui.QMessageBox.critical( self, \
                                            u"Erreur", \
                                            u"Au minimum deux couches vecteur doivent être sélectionnées" )
                return

            errorDuringClassif = False
            outputdir = self.getOutputDir()

            # Build list of input vector files
            vectorlist = []
            labeldescriptor = {}
            label = 0

            logger.info("Crop and reproject vector data")
            for i in range(len(selectedvectorlayers)):
                v = selectedvectorlayers[i]
                inputshpfilepath = v[0].source()
                classcolor = v[1]
                classlabel = v[2]

                labeldescriptor[label] = (classcolor, classlabel)
                logger.debug( "labeldescriptor {}".format(labeldescriptor) )
                label += 1

                # Reprocess input shp file to crop it to firstraster extent
                vectordir = os.path.join(outputdir, 'class%s' % (str(i)))
                ensure_clean_dir(vectordir)

                preprocessedshpfile = cropVectorDataToImage(selectedrasterlayers[0].source(), inputshpfilepath, vectordir)
                vectorlist.append(preprocessedshpfile)

            logger.info("Merge vector data")
            union = mergeVectorData.unionPolygonsWithOGR(vectorlist, outputdir)

            logger.info("Run classification")
            # Build classifcommand
            outputlog = os.path.join(outputdir, 'output.log')
            outputclassification = os.path.join(outputdir, 'classification.tif')
            out_pop = os.path.join(outputdir, 'classification.resultats.txt')

            confmat, kappa = full_classification([r.source() for r in selectedrasterlayers],
                                                 union, outputclassification, out_pop, outputdir)

            logger.info("Run confusion matrix viewer")
            if (not simulation and not errorDuringClassif):
                QGisLayers.loadLabelImage(outputclassification, labeldescriptor)

                notificationDialog = ConfusionMatrixViewer(selectedvectorlayers, confmat, kappa, out_pop)

                self.clearStatus()
                QtGui.QApplication.restoreOverrideCursor()

                notificationDialog.setModal(True)
                notificationDialog.show()

                pixmap = QtGui.QPixmap(notificationDialog.size())
                notificationDialog.render(pixmap)
                pixmap.save(os.path.join(outputdir, 'resultats.png'))

                notificationDialog.exec_()

#        except:
#            raise

        finally:
            self.clearStatus()
            QtGui.QApplication.restoreOverrideCursor()
        #     return # this discards exception
