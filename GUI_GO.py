from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.figure as Figure
import sys
import material_structure as ms
import os
import ast

def stringcheck(string):

    # checks to make sure that the roughness and whatnot is in the correct format
    num = 0
    correctFormat = True
    if len(string) == 0:
        correctFormat = False
    else:
        first = True
        for char in string:
            if first:
                if char == '.':
                    correctFormat = False
                elif not char.isdigit():
                    correctFormat = False
                first = False

            elif not char.isdigit():
                if char == '.':
                    num = num + 1
                    if num > 1:
                        correctFormat = False
                else:
                    correctFormat = False


    return correctFormat


class compoundInput(QDialog):
    def __init__(self):
        super().__init__()
        self.val = []
        pagelayout = QVBoxLayout()
        infolayout = QGridLayout()
        formula = QLabel('Formula: ')
        self.formula = QLineEdit()
        self.formula.editingFinished.connect(self.formulaDone)

        thickness = QLabel('Thickness (A): ')
        self.thickness = QLineEdit()
        self.thickness.setText('10')

        density = QLabel('Density (g/cm^3): ')
        self.density = QLineEdit()

        roughness = QLabel('Roughness (A): ')
        self.roughness = QLineEdit()
        self.roughness.setText('2')

        linkedroughnesslayout = QHBoxLayout()
        #consider including a tab to select linked roughness
        linkedroughness = QLabel('Linked Roughness (A): ')
        self.linkedroughness = QLineEdit()
        self.linkedroughness.setHidden(True)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.linkedroughnessbox)
        self.checkboxstate = 0

        linkedroughnesslayout.addWidget(self.checkbox)
        linkedroughnesslayout.addWidget(linkedroughness)



        infolayout.addWidget(formula, 0,0)
        infolayout.addWidget(thickness,1,0)
        infolayout.addWidget(density,2,0)
        infolayout.addWidget(roughness,3,0)
        infolayout.addLayout(linkedroughnesslayout,4,0)

        infolayout.addWidget(self.formula,0,1)
        infolayout.addWidget(self.thickness,1,1)
        infolayout.addWidget(self.density,2,1)
        infolayout.addWidget(self.roughness,3,1)
        infolayout.addWidget(self.linkedroughness,4,1)

        enterButton = QPushButton('Enter')
        enterButton.clicked.connect(self.inputComplete)

        self.errorMessage = QLabel('')

        pagelayout.addLayout(infolayout)
        pagelayout.addWidget(enterButton)
        pagelayout.addWidget(self.errorMessage)
        self.setLayout(pagelayout)
    def formulaDone(self):
        cwd = os.getcwd()
        filename =  'Perovskite_Density.txt'

        found = False
        with open(filename) as file:
            for line in file:
                myformula = line.split()[0]
                mydensity = line.split()[1]
                if not found:
                    if self.formula.text() == myformula:
                        self.density.setText(mydensity)
                        found = True
                    else:
                        self.density.clear()

    def linkedroughnessbox(self):
        self.checkboxstate = self.checkbox.checkState()
        if self.checkboxstate > 0:
            self.linkedroughness.setHidden(False)
        else:
            self.linkedroughness.setHidden(True)

    def inputComplete(self):

        finished = True
        # gets the elements and their stoichiometry
        myElements = ms.find_stoichiometry(self.formula.text())  # gets the elements and their stoichiometry
        ele = [list(myElements[0].keys())[i] for i in range(int(myElements[1]))]
        stoich = [myElements[0][e].stoichiometry for e in ele]
        myElements = {ele[i]:stoich[i] for i in range(len(ele))}

        # gets the density
        myThickness = self.thickness.text()
        thicknessCorrect = stringcheck(myThickness)

        myDensity = self.density.text()
        densityCorrect = stringcheck(myDensity)

        myRoughness = self.roughness.text()
        roughnessCorrect = stringcheck(myRoughness)

        myLinkedroughness = self.linkedroughness.text()

        linkedroughnessCorrect = True
        if myLinkedroughness != '':
            linkedroughnessCorrect = stringcheck(myLinkedroughness)

        if not(thicknessCorrect) or not(densityCorrect) or not(roughnessCorrect) or not(linkedroughnessCorrect):
            if not(thicknessCorrect):
                self.errorMessage.setText('Please check thickness!')
            elif not(densityCorrect):
                self.errorMessage.setText('Please check density!')
            elif not (roughnessCorrect):
                self.errorMessage.setText('Please check roughness!')
            elif not (linkedroughnessCorrect):
                self.errorMessage.setText('Please check linked roughness!')
        else:
            if myLinkedroughness == '':
                self.val = [myElements, myThickness,myDensity, myRoughness, None]
            else:
                self.val = [myElements, myThickness, myDensity, myRoughness, myLinkedroughness]

            self.accept()

        # gets the roughness

        # gets the linked roughness




class sampleWidget(QWidget):
    def __init__(self, sample):
        super().__init__()

        # Initializes the sample definition widget
        pagelayout = QHBoxLayout()  # page layout

        cblayout = QVBoxLayout()  # combobox and button layout

        # bottons for adding, copying, and deleteing layers
        addlayerButton = QPushButton('Add Layer')  # add layer
        addlayerButton.clicked.connect(self._addLayer)

        copylayerButton = QPushButton('Copy Layer')  # copy layer
        copylayerButton.clicked.connect(self._copyLayer)

        deletelayerButton = QPushButton('Remove Layer')  # delete layer
        deletelayerButton.clicked.connect(self._removeLayer)

        # Layer Box
        self.structInfo = sample.structure
        self.layerBox = QComboBox(self)

        layerList = []
        for i in range(len(self.structInfo)):
            if i == 0:
                layerList.append('Substrate')
            else:
                layerList.append('Layer '+str(i))
        # change this for an arbitrary sample model
        self.layerBox.addItems(layerList)

        # changes the table on the screen when new layer selected
        self.layerBox.currentIndexChanged.connect(self.changetable)

        # buttons for adding and removing layers
        cblayout.addWidget(addlayerButton)
        cblayout.addWidget(copylayerButton)
        cblayout.addWidget(deletelayerButton)

        # layer combo box
        cblayout.addWidget(self.layerBox)

        # table widget
        self.tableStacklayout = QStackedLayout()

        selectlayout = QVBoxLayout()

        # buttons for choosing which parameters to choose
        structButton = QPushButton('Structure')
        selectlayout.addWidget(structButton)
        polyButton = QPushButton('Element Variation')
        selectlayout.addWidget(polyButton)
        magButton = QPushButton('Magnetic')
        selectlayout.addWidget(magButton)
        dpButton = QPushButton('Density Profile')
        dpButton.setStyleSheet("background-color : cyan")
        selectlayout.addWidget(dpButton)

        pagelayout.addLayout(cblayout)
        pagelayout.addLayout(self.tableStacklayout)
        pagelayout.addLayout(selectlayout)

        t = np.arange(0.00, 2.0, 0.01)
        s = 1 + np.sin(2 * np.pi * t)
        fig = plt.figure()
        plt.plot(t,s)

        self.canvas = FigureCanvas(fig)
        mylayout = QVBoxLayout()
        mylayout.addLayout(pagelayout)
        mylayout.addWidget(self.canvas)

        # create the tables as predefined by the sample model
        #  We will need to consider the case when no sample model is given
        for i in range(len(self.structInfo)):
            self.tableStacklayout.addWidget(self.createElementTable(i))

        self.setLayout(mylayout)

    def createElementTable(self, idx):
        #idx = self.layerBox.currentIndex()

        elementTable = QTableWidget(self)
        # self.elementTable.resize(660, 125)
        elementTable.setRowCount(3)
        elementTable.setColumnCount(6)

        elementTable.setHorizontalHeaderLabels(
            ['Element', 'Thickness', 'Density', 'Roughness', 'Linked Roughness', 'Scattering Factor'])
        for row in range(elementTable.rowCount()):
            for column in range(elementTable.columnCount()):
                if column == 0:
                    element = list(self.structInfo[idx].keys())[row]
                    item = QTableWidgetItem(element)
                    elementTable.setItem(row,column, item)
                elif column == 1:
                    thickness = self.structInfo[idx][element].thickness
                    item = QTableWidgetItem(str(thickness))
                    elementTable.setItem(row, column, item)
                elif column == 2:
                    density = self.structInfo[idx][element].density
                    item = QTableWidgetItem(str(density))
                    elementTable.setItem(row, column, item)
                elif column == 3:
                    roughness = self.structInfo[idx][element].roughness
                    item = QTableWidgetItem(str(roughness))
                    elementTable.setItem(row, column, item)
                elif column == 4:
                    linked_roughness = self.structInfo[idx][element].linked_roughness
                    item = QTableWidgetItem(str(linked_roughness))
                    elementTable.setItem(row, column, item)
                elif column == 5:
                    scattering_factor = self.structInfo[idx][element].scattering_factor
                    item = QTableWidgetItem(scattering_factor)
                    elementTable.setItem(row, column, item)

        return elementTable

    def changetable(self):
        idx = self.layerBox.currentIndex()
        self.tableStacklayout.setCurrentIndex(idx)

    def _addLayer(self):

        num = self.layerBox.count()
        if num == 0:
            self.layerBox.addItem('Substrate')
        else:
            self.layerBox.addItem('Layer ' + str(num))


        addLayerApp = compoundInput()
        addLayerApp.show()
        addLayerApp.exec_()
        print(addLayerApp.val)
        addLayerApp.close()
    def _removeLayer(self):
        num = self.layerBox.count()

        if num != 0:
            self.layerBox.removeItem(num-1)

    def _copyLayer(self):
        num = self.layerBox.count()
        if num == 0:
            self.layerBox.addItem('Substrate')
        else:
            self.layerBox.addItem('Layer ' + str(num))

class ReflectometryApp(QMainWindow):
    def __init__(self, sample):
        super().__init__()

        # set the title
        self.setWindowTitle('Reflectometry of Quantum Materials')

        # set the geometry of the window
        self.setGeometry(200,80,1000,600)

        pagelayout = QVBoxLayout()
        buttonlayout = QHBoxLayout()
        self.stackedlayout = QStackedLayout()

        pagelayout.addLayout(buttonlayout)
        pagelayout.addLayout(self.stackedlayout)

        label1 = QLabel('Label 1')
        label2 = QLabel('Label 2')
        label3 = QLabel('Label 3')

        _sampleWidget = sampleWidget(sample)  # initialize the sample widget
        sampleButton = QPushButton('Sample')
        sampleButton.setStyleSheet("background-color : pink")
        sampleButton.clicked.connect(self.activate_tab_1)
        buttonlayout.addWidget(sampleButton)
        self.stackedlayout.addWidget(_sampleWidget)

        reflButton = QPushButton('Reflectivity')
        reflButton.setStyleSheet("background-color : pink")
        reflButton.clicked.connect(self.activate_tab_2)
        buttonlayout.addWidget(reflButton)
        self.stackedlayout.addWidget(label2)

        goButton = QPushButton('Global Optimization')
        goButton.setStyleSheet("background-color : pink")
        goButton.clicked.connect(self.activate_tab_3)
        buttonlayout.addWidget(goButton)
        self.stackedlayout.addWidget(label3)

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)

    def activate_tab_1(self):
        self.stackedlayout.setCurrentIndex(0)
    def activate_tab_2(self):
        self.stackedlayout.setCurrentIndex(1)
    def activate_tab_3(self):
        self.stackedlayout.setCurrentIndex(2)





if __name__ == '__main__':
    sample = ms.slab(3)
    sample.addlayer(0,'SrTiO3', 50)
    sample.addlayer(1,'LaMnO3', 20)
    sample.addlayer(2, 'LaAlO3', 5)

    app = QApplication(sys.argv)
    demo = ReflectometryApp(sample)

    demo.show()

    sys.exit(app.exec_())