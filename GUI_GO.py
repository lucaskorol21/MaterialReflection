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
import pyqtgraph as pg

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
            molar_mass = 0
            elements = list(myElements[0].keys())
            # gets the molar mass of the compound
            for ele in elements:
                stoich = myElements[0][ele].stoichiometry

                if ele[-1].isdigit():
                    ele = ele.rstrip(ele[-1])

                molar_mass = molar_mass + ms.atomic_mass(ele)*stoich

            tempArray = []
            if myLinkedroughness == '':
                for ele in elements:
                    stoich = myElements[0][ele].stoichiometry
                    density = float(myDensity)
                    if ele[-1].isdigit():
                        ff_ele = ele.rstrip(ele[-1])
                    else:
                        ff_ele = ele

                    tempArray.append([ele, myThickness, str(density*float(stoich)/molar_mass), myRoughness, False, ff_ele, stoich])
            else:
                for ele in elements:
                    stoich = myElements[0][ele].stoichiometry
                    density = float(myDensity)
                    if ele[-1].isdigit():
                        ff_ele = ele.rstrip(ele[-1])
                    else:
                        ff_ele = ele

                    tempArray.append([ele, myThickness, str(density*float(stoich)/molar_mass), myRoughness, myLinkedroughness, ff_ele, stoich])

            self.val = np.array(tempArray)
            self.accept()

        # gets the roughness

        # gets the linked roughness





class variationWidget(QDialog):
    def __init__(self, mainWidget, sample):
        super().__init__()

        pagelayout = QHBoxLayout()

        self.element_idx = 0
        self.elelayout = QVBoxLayout()
        self.mainWidget = mainWidget
        self.mainWidget.layerBox.currentIndexChanged.connect(self.changeElements)


        addButton = QPushButton('Add')
        addButton.clicked.connect(self.addVarEle)
        # Create the connect function
        deleteButton = QPushButton('Delete')
        deleteButton.clicked.connect(self.deleteVarEle)
        # create the connect function

        # buttons for adding and removing

        self.sample = sample

        self.radiobutton = QRadioButton()
        idx = self.mainWidget.layerBox.currentIndex()


        # Setting up the element variation check boxes
        for j in range(len(list(self.sample.structure[idx].keys()))):
            ele = list(self.sample.structure[idx].keys())[j]
            self.mainWidget.elementBox.addItem(ele)


        self.mainWidget.elementBox.currentIndexChanged.connect(self.setTable)
        self.elelayout.addWidget(self.mainWidget.elementBox)
        self.setTable()



        self.elelayout.addWidget(addButton)
        self.elelayout.addWidget(deleteButton)




        self.mainWidget.varTable.setRowCount(2)
        self.mainWidget.varTable.setColumnCount(3)
        self.mainWidget.varTable.setHorizontalHeaderLabels(
            ['Name', 'Ratio', 'Scattering Factor'])

        pagelayout.addLayout(self.elelayout)
        pagelayout.addWidget(self.mainWidget.varTable)

        self.setLayout(pagelayout)




    def changeElements(self):

        # this function simply changes the elements based on current layer
        # needs to be changed when adding and removing layers

        self.mainWidget.change_elements = True
        idx = self.mainWidget.layerBox.currentIndex()
        self.mainWidget.elementBox.clear()

        for j in range(len(self.mainWidget.structTableInfo[idx])):
            ele = self.mainWidget.structTableInfo[idx][j][0]
            self.mainWidget.elementBox.addItem(ele)

        self.mainWidget.change_elements = False
        self.mainWidget.elementBox.setCurrentIndex(self.element_idx)
    def addVarEle(self):
        row = self.mainWidget.varTable.rowCount()
        self.mainWidget.varTable.setRowCount(row + 1)

    def deleteVarEle(self):
        row = self.mainWidget.varTable.rowCount()
        if row != 2:
            self.mainWidget.varTable.setRowCount(row-1)

    def setTable(self):

        layer_idx = self.mainWidget.layerBox.currentIndex()
        ele_idx = self.mainWidget.elementBox.currentIndex()

        # makes sure that when we switch layers we show the same positional element
        if not self.mainWidget.change_elements:
            self.element_idx = ele_idx

        #print(layer_idx, ele_idx)
        if ele_idx != -1:
            ele = self.mainWidget.structTableInfo[layer_idx][ele_idx][0]

            info = self.mainWidget.varData[ele][layer_idx]

            # Might need to change this implementation
            if len(info[0]) != 0:
                self.mainWidget.varTable.setRowCount(len(info[0]))

                for row in range(len(info[0])):

                    # Element Name
                    item = QTableWidgetItem(info[0][row])
                    self.mainWidget.varTable.setItem(row, 0, item)

                    # Ratio
                    item = QTableWidgetItem(str(info[1][row]))
                    self.mainWidget.varTable.setItem(row, 1, item)

                    # Scattering Factor
                    item = QTableWidgetItem(info[2][row])
                    self.mainWidget.varTable.setItem(row, 2, item)
            else:
                for row in range(self.mainWidget.varTable.rowCount()):
                    item = QTableWidgetItem('')
                    self.mainWidget.varTable.setItem(row, 0, item)

                    item = QTableWidgetItem('')
                    self.mainWidget.varTable.setItem(row, 1, item)

                    item = QTableWidgetItem('')
                    self.mainWidget.varTable.setItem(row, 2, item)




class reflectivityWidget(QWidget):
    def __init__(self):
        super().__init__()
        pagelayout = QHBoxLayout()
        self.layerBox = QComboBox()
        hello = QLabel('Hello')
        pagelayout.addWidget(self.layerBox)
        pagelayout.addWidget(hello)
        self.setLayout(pagelayout)

class sampleWidget(QWidget):
    def __init__(self, sample):
        super().__init__()
        self.sample = sample  # variable used to define sample info
        self.structTableInfo = []  # used to keep track of the table info instead of constantly switching

        self.varData = {ele: [[['',''],['',''],['','']] for i in range(len(sample.structure))] for ele in sample.myelements}
        self.getPolyData()
        self.varTable = QTableWidget()
        self.elementBox = QComboBox()

        self.change_elements = False
        self.element_index = 0

        self.previousLayer = 0
        self.firstStruct = True

        # Initializes the sample definition widget
        pagelayout = QHBoxLayout()  # page layout

        cblayout = QVBoxLayout()  # combobox and button layout


        # bottons for adding, copying, and deleteing layers
        addlayerButton = QPushButton('Add Layer')  # add layer
        addlayerButton.clicked.connect(self._addLayer)

        copylayerButton = QPushButton('Copy Current Layer')  # copy layer
        copylayerButton.clicked.connect(self._copyLayer)

        deletelayerButton = QPushButton('Remove Current Layer')  # delete layer
        deletelayerButton.clicked.connect(self._removeLayer)

        # Layer Box
        self.structInfo = self.sample.structure
        self.layerBox = QComboBox(self)

        layerList = []
        for i in range(len(self.sample.structure)):
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

        self.sampleInfoLayout = QStackedLayout() # stacked layout for the different parameter types

        self.structTable = QTableWidget()


        self.structTable.setRowCount(3)
        self.structTable.setColumnCount(6)
        self.structTable.setHorizontalHeaderLabels(
            ['Element', 'Thickness', 'Density', 'Roughness', 'Linked Roughness', 'Scattering Factor'])
        for i in range(len(self.sample.structure)):
            self.setStructFromSample(i)

        # setTable
        self.setTable(0)

        # Element Variation Stuff
        elementVariation = variationWidget(self,sample)



        # Magnetic Stuff
        magVar = QLabel('bye')

        selectlayout = QVBoxLayout()


        self.sampleInfoLayout.addWidget(self.structTable)  # index 1
        self.sampleInfoLayout.addWidget(elementVariation)  # index 2
        self.sampleInfoLayout.addWidget(magVar)  # index 3

        # buttons for choosing which parameters to choose
        structButton = QPushButton('Structure')
        structButton.clicked.connect(self._structural)
        selectlayout.addWidget(structButton)

        polyButton = QPushButton('Element Variation')
        polyButton.clicked.connect(self._elementVariation)
        selectlayout.addWidget(polyButton)

        magButton = QPushButton('Magnetic')
        magButton.clicked.connect(self._magnetic)
        selectlayout.addWidget(magButton)

        self.structBool = True
        self.polyBool = False
        self.magBool = False

        dpButton = QPushButton('Density Profile')
        dpButton.clicked.connect(self.changetable)
        dpButton.clicked.connect(self._densityprofile)
        dpButton.setStyleSheet("background-color : cyan")
        selectlayout.addWidget(dpButton)

        pagelayout.addLayout(cblayout)
        pagelayout.addLayout(self.sampleInfoLayout)
        pagelayout.addLayout(selectlayout)



        mylayout = QVBoxLayout()
        mylayout.addLayout(pagelayout)


        # Adding the plotting Widget
        self.densityWidget = pg.PlotWidget()
        self.densityWidget.setBackground('w')

        self.densityWidget.addLegend()



        mylayout.addWidget(self.densityWidget)


        self.setLayout(mylayout)



    def setStructFromSample(self, idx):
        # this function will take the upon initialization and load in all parameters
        structInfo = self.sample.structure
        numLay = len(structInfo)
        tempArray = np.empty((3,7), dtype=object)
        for row in range(3):
            for col in range(7):
                if col == 0:
                    element = list(structInfo[idx].keys())[row]
                    tempArray[row,col] = str(element)
                elif col == 1:
                    element = list(structInfo[idx].keys())[row]
                    thickness = structInfo[idx][element].thickness
                    tempArray[row,col] = str(thickness)
                elif col == 2:
                    element = list(structInfo[idx].keys())[row]
                    density = structInfo[idx][element].density
                    tempArray[row,col] = str(density)
                elif col == 3:
                    element = list(structInfo[idx].keys())[row]
                    roughness = structInfo[idx][element].roughness
                    tempArray[row,col] = str(roughness)
                elif col == 4:
                    element = list(structInfo[idx].keys())[row]
                    linked_roughness = structInfo[idx][element].linked_roughness
                    tempArray[row,col] = str(linked_roughness)
                elif col == 5:
                    element = list(structInfo[idx].keys())[row]
                    scattering_factor = structInfo[idx][element].scattering_factor
                    tempArray[row,col] = str(scattering_factor)
                elif col == 6:
                    element = list(structInfo[idx].keys())[row]
                    stoichiometry = structInfo[idx][element].stoichiometry
                    tempArray[row,col] = str(stoichiometry)


        self.structTableInfo.append(tempArray)

    def setTable(self, idx):
        tableInfo = self.structTableInfo[idx]

        for row in range(3):
            for col in range(6):
                item = QTableWidgetItem(str(tableInfo[row][col]))
                self.structTable.setItem(row,col, item)

    def changetable(self):

        idx = self.layerBox.currentIndex()

        if self.structBool:
            for row in range(len(self.structTableInfo[self.previousLayer])):
                for col in range(len(self.structTableInfo[self.previousLayer][0])-1):
                    item = self.structTable.item(row,col).text()
                    self.structTableInfo[self.previousLayer][row][col] = str(item)

            self.previousLayer = idx


        if self.polyBool:
            # get information from variation table
            if not self.change_elements:
                self.element_index = self.elementBox.currentIndex()

            ele = self.structTableInfo[self.previousLayer][self.element_index][0]
            print(ele)
            print()
            name = ['' for i in range(self.varTable.rowCount())]
            ratio = ['' for i in range(self.varTable.rowCount())]
            scat = ['' for i in range(self.varTable.rowCount())]

            for row in range(self.varTable.rowCount()):
                for col in range(self.varTable.columnCount()):
                    if self.varTable.item(row, col) == None:
                        pass
                    else:
                        item = self.varTable.item(row, col).text()
                        if col == 0:
                            name[row] = item
                        elif col == 1:
                            ratio[row] = item
                        elif col == 2:
                            scat[row] = item

            # Makes sure that if the name or scattering factor is changed, that we change it throughout
            for i in range(len(self.structTableInfo)):
                for j in range(len(self.structTableInfo[i])):

                    new_ele = self.structTableInfo[i][j][0]
                    if new_ele == ele and i != self.previousLayer:
                        self.varData[ele][i][0] = name
                        self.varData[ele][i][2] = scat
            self.varData[ele][self.previousLayer] = [name, ratio, scat]
            self.previousLayer = idx

        self.setTable(idx)



    def _addLayer(self):

        addLayerApp = compoundInput()
        addLayerApp.show()
        addLayerApp.exec_()
        userinput = addLayerApp.val
        addLayerApp.close()

        # check to see if we have a new element
        num_layers = len(self.structTableInfo)

        # checks to see if we have a new element and adds it to the element variation list
        for i in range(len(userinput)):
            if userinput[i][0] not in list(self.varData.keys()):
                self.varData[userinput[i][0]] = [[] for i in range(num_layers)]


        if len(userinput) != 0:
            num = self.layerBox.count()
            idx = self.layerBox.currentIndex()
            if num == 0:
                self.varData = dict()
                self.layerBox.addItem('Substrate')
                self.structTableInfo.insert(0, userinput)
                for i in range(len(userinput)):
                    self.varData[userinput[i][0]] = [[]]

            else:
                self.layerBox.addItem('Layer ' + str(num))
                self.structTableInfo.insert(idx+1, userinput)

                for key in list(self.varData.keys()):

                    isVar = False
                    data = []

                    for info in self.varData[key]:
                        if len(info) != 0:
                            data = [info[0], [1,0], info[2]]

                    self.varData[key].insert(idx+1, data)



    def _removeLayer(self):
        num = self.layerBox.count()  # get the number of layers in the material

        idx = self.layerBox.currentIndex()  # determine which layer has been selected to remove
        if num != 0:
            self.layerBox.removeItem(num-1)

        self.structTableInfo.pop(idx)  # removes the information about that layer

        # removes the element variation data
        for key in list(self.varData.keys()):
            self.varData[key].pop(idx)

        self.setTable(idx)  # sets the table for layer that replaces the removed layer

    def _copyLayer(self):
        num = self.layerBox.count()
        if num == 0:
            self.layerBox.addItem('Substrate')
        else:
            self.layerBox.addItem('Layer ' + str(num))

        idx = self.layerBox.currentIndex()

        newLayer = self.structTableInfo[idx]
        self.structTableInfo.insert(idx+1,newLayer)

        # goes through all the
        for key in list(self.varData.keys()):

            isVar = False
            data = []

            for info in self.varData[key]:
                if len(info) != 0:
                    data = [info[0], info[1], info[2]]

            self.varData[key].insert(idx + 1, data)

    def _structural(self):
        self.structBool = True
        self.polyBool = False
        self.magBool = False

        self.sampleInfoLayout.setCurrentIndex(0)

    def _elementVariation(self):

        self.structBool = False
        self.polyBool = True
        self.magBool = False

        self.sampleInfoLayout.setCurrentIndex(1)



    def _magnetic(self):
        self.structBool = False
        self.polyBool = False
        self.magBool = True

        self.sampleInfoLayout.setCurrentIndex(2)

    def _densityprofile(self):

        sample = self._createStructSample()
        sample = self._createVarSample(sample)

        thickness, density, density_magnetic = sample.density_profile()
        self.densityWidget.clear()

        self._plotDensityProfile(thickness, density, density_magnetic)


    def _plotDensityProfile(self,thickness, density, density_magnetic):


        num = len(density)

        val = list(density.values())
        mag_val = list(density_magnetic.values())
        check = []
        for key in list(density.keys()):
            if key[-1].isdigit():
                check.append(True)
            else:
                check.append(False)

        for idx in range(len(val)):
            if check[idx]:
                self.densityWidget.plot(thickness,val[idx], pen=pg.mkPen((idx,num),width=2), name=list(density.keys())[idx])
            else:
                self.densityWidget.plot(thickness, val[idx], pen=pg.mkPen((idx,num),width=2), name=list(density.keys())[idx])



    def _createStructSample(self):

        m = len(self.structTableInfo)  # determines how many layers in the sample
        sample = ms.slab(m)  # initializes the slab class

        # loops through each layer and sets the appropriate parameters
        for idx in range(m):
            formula = ''  # used to determine the chemical formula
            thickness = []  # thickness of the layer
            density = []  # density of the layer
            roughness = []  # roughness of the layer
            linked_roughness = []  # linked roughness of the layer

            layer = self.structTableInfo[idx]  # gets the layer information

            for ele in range(len(layer)):
                element = layer[ele]  # element data

                # recreates the chemical formula string
                formula = formula + element[0]
                if element[6] != '1':
                    formula = formula + element[6]

                thickness.append(float(element[1]))  # gets thickness data
                density.append(float(element[2]))  # gets density data
                roughness.append(float(element[3]))  # gets roughness data
                if element[4].isdigit():
                    linked_roughness.append(float(element[4]))
                else:
                    linked_roughness.append(False)

                # still need to take into account sf that are different than element
            sample.addlayer(idx,formula,thickness,density=density, roughness=roughness, linked_roughness=linked_roughness)

        return sample

    def _createVarSample(self, sample):

        m = len(self.structTableInfo)  # determines how many layers in the sample
        for idx in range(m):
            layer = self.structTableInfo[idx]  # gets the layer information
            for ele in range(len(layer)):
                ele_name = layer[ele][0]

                poly = self.varData[ele_name][idx]  # retrieves the element variation data for particular layer

                names = poly[0]
                ratio = poly[1]
                scattering_factor = poly[2]

                if len(names) != 0:
                    if names[0] != '':
                        ratio = [float(ratio[i]) for i in range(len(ratio))]
                        sample.polymorphous(idx,ele_name,names,ratio,sf=scattering_factor)
        return sample

    def getPolyData(self):

        for j in range(len(self.sample.structure)):
            layer = self.sample.structure[j]
            elekeys = list(layer.keys())
            for ele in elekeys:
                if len(layer[ele].polymorph) != 0:
                    self.varData[ele][j] = [layer[ele].polymorph, layer[ele].poly_ratio,
                                            layer[ele].scattering_factor]

class ReflectometryApp(QMainWindow):
    def __init__(self, sample):
        super().__init__()

        # set the title
        self.setWindowTitle('Reflectometry of Quantum Materials')

        # set the geometry of the window
        self.setGeometry(180,60,1400,800)

        pagelayout = QVBoxLayout()
        buttonlayout = QHBoxLayout()
        self.stackedlayout = QStackedLayout()

        pagelayout.addLayout(buttonlayout)
        pagelayout.addLayout(self.stackedlayout)

        label1 = QLabel('Label 1')
        label2 = QLabel('Label 2')
        label3 = QLabel('Label 3')

        self.sampleButton = QPushButton('Sample')
        self.reflButton = QPushButton('Reflectivity')
        self.goButton = QPushButton('Global Optimization')

        _sampleWidget = sampleWidget(sample)  # initialize the sample widget
        _reflectivityWidget = reflectivityWidget()

        self.sampleButton.setStyleSheet("background-color : pink")
        self.sampleButton.clicked.connect(self.activate_tab_1)
        buttonlayout.addWidget(self.sampleButton)
        self.stackedlayout.addWidget(_sampleWidget)

        self.reflButton.setStyleSheet("background-color : pink")
        self.reflButton.clicked.connect(self.activate_tab_2)
        buttonlayout.addWidget(self.reflButton)
        self.stackedlayout.addWidget(label2)

        self.goButton.setStyleSheet("background-color : pink")
        self.goButton.clicked.connect(self.activate_tab_3)
        buttonlayout.addWidget(self.goButton)
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
    sample.polymorphous(1, 'Mn', ['Mn2+', 'Mn3+'], [0.5,0.5],['Mn','Fe'])
    sample.addlayer(2, 'LaAlO3', 5)

    app = QApplication(sys.argv)
    demo = ReflectometryApp(sample)

    demo.show()

    sys.exit(app.exec_())