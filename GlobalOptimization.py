from scipy import optimize
from material_structure import *
import numpy as np
from data_structure import *
import matplotlib.pyplot as plt


# Begin with creating a function that I can use global optimization on!
def global_optimization(scans, data, sims, params, lb, ub):
    # The idea for this would be to allow the user to select the scans they would like to
    # use in the global optimization algorithm

    # We will then ask the user which parameters they would like to vary, along with the range

    # We may need a very complex function to perform the optimization...


    print('good try')

def scanCompute(x, *args):

    least_square = 0  # what we will use to determine some values

    sample = args[0]
    scans = args[1]
    data = args[2]
    sims = args[3]
    parameters = args[4]

    #sample changes
    for p in range(len(parameters)):
        params = parameters[p]
        layer = params[0]
        property = params[1]
        if property == 'STRUCTURAL':
            mode = params[2]
            if mode == 'COMPOUND':
                characteristic = params[3]
                for ele in list(sample.structure[layer].keys()):
                    if characteristic == 'THICKNESS':
                        sample.structure[layer][ele].thickness = x[p]
                    elif characteristic == 'DENSITY':
                        sample.structure[layer][ele].density = x[p]
                    elif characteristic == 'ROUGHNESS':
                        sample.structure[layer][ele].roughness = x[p]
                    elif characteristic == 'LINKED ROUGHNESS':
                        sample.structure[layer][ele].linked_roughness = x[p]

            elif mode == 'ELEMENT':
                element = params[3]
                characteristic = params[4]
                if characteristic == 'THICKNESS':
                    sample.structure[layer][element].thickness = x[p]
                elif characteristic == 'DENSITY':
                    sample.structure[layer][element].density = x[p]
                elif characteristic == 'ROUGHNESS':
                    sample.structure[layer][element].roughness = x[p]
                elif characteristic == 'LINKED ROUGHNESS':
                    sample.structure[layer][element].linked_roughness = x[p]

        elif property == 'POLYMORPHOUS':
            element = params[3]
            polymorph = params[4]

            ratio = 1 - x[p]

            poly = np.where(sample.structure[layer][element].polymorph == polymorph)

            if poly == 0:
                sample.structure[layer][element].poly_ratio[0] = x[p]
                sample.structure[layer][element].poly_ratio[1] = ratio
            elif poly == 1:
                sample.structure[layer][element].poly_ratio[0] = x[p]
                sample.structure[layer][element].poly_ratio[1] = ratio

        elif property == 'MAGNETIC':
            element = params[3]

            if len(params) == 3:
                sample.structure[layer][element].mag_density[0] = x[p]
            else:
                polymorph = params[4]
                poly = np.where(sample.structure[layer][element].polymorph == polymorph)
                sample.structure[layer][element].mag_density[poly] = x[p]


    for scan in scans:
        scanType = scan[1]
        name = scan[2]
        if scanType == 'Reflectivity':
            myDataScan = data[name]
            myData = list(myDataScan)
            E = myDataScan.attrs['Energy']
            pol = myDataScan.attrs['Polarization']
            qz = np.array(myData[0])

            Rdat = np.array(qz[2])
            qz, Rsim = sample.reflectivity(E, qz)
            Rsim = Rsim[pol]
            least_square = least_square + sum((Rdat-Rsim)**2/Rdat)


        elif scanType == 'Energy':
            myDataScan = data[name]
            myData = list(myDataScan)
            Theta = myDataScan.attrs['Angle']
            E = np.array(myData[3])
            pol = myDataScan.attrs['Polarization']

            Rdat = np.array(myData[2])
            Rsim = sample.energy_scan(Theta, E)
            Rsim = Rsim[pol]

            least_square = least_square + sum((Rdat-Rsim)**2)
    print(least_square)
    return least_square




def selectOptimize(fname):
    sample = ReadSampleHDF5(fname)  # import the sample information
    data_info, data, sims = ReadDataHDF5(fname)  # import the experimental data and simulated data

    # Sets up and prints scan table
    header = ['#', 'Scan Type', 'Scan']
    tab = PrettyTable(header)
    tab.add_rows(data_info)
    print(tab)


    sample_params = list()
    upperbound = list()
    lowerbound = list()

    # ------------------------------------------ Scan Selection ------------------------------------------------------ #
    print('SCAN SELECTION')
    print()
    scans = input('Input scans from '+str(data_info[0,0])+' to '+ str(data_info[-1,0]) + ' for global optimization. Separate each scan using a space: ')
    if scans.upper() == 'EXIT':
        quit()
    scans = scans.split()
    scans = list(dict.fromkeys(scans))  # removes any duplicates
    for scan in scans:
        if scan not in data_info[:,0]:
            val = input('This scan number ' + scan + ' does not exist. Would you like to select another scan (y/n)?')
            if val.upper() == 'EXIT':
                quit()
            scans.remove(scan)
            if val.upper() == 'Y':
                scan = input('Input the new scan number: ')
                if scan.upper() == 'EXIT':
                    quit()
                while scan not in data_info[:,0]:
                    scan = input('Please input a scan that lies on the interval '+str(data_info[0,0])+' to '+ str(data_info[-1,0])+' : ')
                    if scan.upper() == 'EXIT':
                        quit()
                scans.append(scan)
    scans = [int(scan) for scan in scans]

    # ----------------------------------------- Parameter Selection -------------------------------------------------- #
    print()
    print('PARAMETER SELECTION')
    print()

    layer_formula = list()
    idx = 0
    for temp_layer in sample.structure:
        P = list()
        M = list()
        formula = ''
        for key in list(temp_layer.keys()):
            stoich = temp_layer[key].stoichiometry
            if stoich == 1:
                formula = formula + key
            else:
                formula = formula + key + str(stoich)
            if len(temp_layer[key].polymorph) > 0:
                P.append(key)
            if len(temp_layer[key].mag_density) > 0:
                M.append(key)

        layer_formula.append([idx, formula, P, M])
        idx = idx + 1

        # Sets up and prints scan table
    header = ['Layer', 'Formula', 'Polymorphs', 'Magnetic']
    tab = PrettyTable(header)
    tab.add_rows(layer_formula)
    print(tab)
    print()
    number_layers = len(sample.structure)

    cont = 'Y'
    while cont.upper() == 'Y':
        layer = input('Select layer you would like to optimize (0-'+str(number_layers-1)+"): ")
        if layer.upper() == 'EXIT':
            quit()
        while layer.upper() == 'SHOW':
            print(tab)
            print()
            layer = input('Select layer you would like to optimize (0-' + str(number_layers - 1) + "): ")
            if layer.upper() == 'EXIT':
                quit()

        while int(layer) < 0 or int(layer) > number_layers -1:
            layer = input('Select layer you would like to optimize (0-' + str(number_layers - 1) + "): ")
            if layer.upper() == 'EXIT':
                quit()
            while layer.upper() == 'SHOW':
                print(tab)
                print()
                layer = input('Select layer you would like to optimize (0-' + str(number_layers - 1) + "): ")
                if layer.upper() == 'EXIT':
                    quit()

        poly = list()
        mag = list()

        structural = True
        polymorphous = False
        magnetic = False

        layer = int(layer)
        elements = list(sample.structure[layer].keys())
        for ele in elements:
            if len(sample.structure[layer][ele].polymorph) > 0:
                poly.append(ele)
                polymorphous = True
            if len(sample.structure[layer][ele].mag_density) > 0:
                mag.append(ele)
                magnetic = True

        s = 'structural'
        if polymorphous:
            s = s + "/polymorphous"
        if magnetic:
            s = s + "/magnetic"

        prop = input('Select the property you would like to vary ('+ s + ') : ')
        if prop.upper() == 'EXIT':
            quit()
        while prop.upper() != 'STRUCTURAL' and prop.upper() != 'POLYMORPHOUS' and prop.upper() != 'MAGNETIC':
            prop = input('Please select one of the properties (' + s + ') : ')
            if prop.upper() == 'EXIT':
                quit()

        if prop.upper() == 'STRUCTURAL':
            mode = input('Select mode (element/compound): ')
            if mode.upper() == 'EXIT':
                quit()
            while mode.upper() != 'ELEMENT' and mode.upper() != 'COMPOUND':
                mode = input('Please select (element/compound): ')
                if mode.upper() == 'EXIT':
                    quit()

            if mode.upper() == 'COMPOUND':
                char_list = ['THICKNESS','DENSITY', 'ROUGHNESS', 'LINKED ROUGHNESS']
                val = 'y'
                while val.upper() == 'Y' and len(char_list) > 0:
                    characteristic = input('Select characteristic (' + '/'.join([char.lower() for char in char_list]) + '): ')
                    if characteristic.upper() == 'EXIT':
                        quit()
                    while characteristic.upper() != 'THICKNESS' and characteristic.upper() != 'DENSITY' and characteristic.upper() != 'ROUGHNESS' and characteristic.upper() != 'LINKED ROUGHNESS':
                        characteristic = input('Select characteristic (' + '/'.join([char.lower() for char in char_list]) + '): ')
                        if characteristic.upper() == 'EXIT':
                            quit()

                    if characteristic.upper() == 'THICKNESS' and 'THICKNESS' in char_list:
                        char_list.remove('THICKNESS')
                        lw = 1
                        up = 0
                        while float(lw) > float(up):
                            lw = input('Select lower bound in units of Angstrom: ')
                            if lw.upper() == 'EXIT':
                                quit()
                            up = input('Select upper bound in units of Angstrom: ')
                            if up.upper() == 'EXIT':
                                quit()

                        lowerbound.append(lw)
                        upperbound.append(up)
                    if characteristic.upper() == 'DENSITY' and 'DENSITY' in char_list:
                        char_list.remove('DENSITY')
                        lw = 1
                        up = 0
                        while float(lw) > float(up):
                            lw = input('Select lower bound in units of g/cm^3: ')
                            if lw.upper() == 'EXIT':
                                quit()
                            up = input('Select upper bound in units of g/cm^3: ')
                            if up.upper() == 'EXIT':
                                quit()
                        lowerbound.append(lw)
                        upperbound.append(up)
                    if characteristic.upper() == 'ROUGHNESS' and 'ROUGHNESS' in char_list:
                        char_list.remove('ROUGHNESS')
                        lw = 1
                        up = 0
                        while float(lw) > float(up):
                            lw = input('Select lower bound in units of Angstrom: ')
                            if lw.upper() == 'EXIT':
                                quit()
                            up = input('Select upper bound in units of Angstrom: ')
                            if up.upper() == 'EXIT':
                                quit()
                        lowerbound.append(lw)
                        upperbound.append(up)
                    if characteristic.upper() == 'LINKED ROUGHNESS' and 'LINKED ROUGHNESS' in char_list:
                        char_list.remove('LINKED ROUGHNESS')
                        lw = 1
                        up = 0
                        while float(lw) > float(up):
                            lw = input('Select lower bound in units of Angstrom: ')
                            if lw.upper() == 'EXIT':
                                quit()
                            up = input('Select upper bound in units of Angstrom: ')
                            if up.upper() == 'EXIT':
                                quit()
                        lowerbound.append(lw)
                        upperbound.append(up)

                    print()
                    sample_params.append([layer,prop.upper(),mode.upper(),characteristic.upper()])

                    if len(char_list) > 0:
                        val = input('Would you like to select another characteristic (y/n)?')
                    else:
                        val = 'N'


            elif mode.upper() == 'ELEMENT':
                char_list = ['THICKNESS','DENSITY', 'ROUGHNESS', 'LINKED ROUGHNESS']
                val = 'y'
                while val.upper() == 'Y':
                    element = input('Select element (' + str(elements) + ") : ")
                    while element not in elements:
                        element = input('Please select element in list (' + str(elements) + ") : ")

                    again = 'y'
                    while again.upper() == 'Y' and len(char_list)>0:
                        characteristic = input('Select characteristic (' + '/'.join([char.lower() for char in char_list]) + '): ')
                        while characteristic.upper() != 'THICKNESS' and characteristic.upper() != 'DENSITY' and characteristic.upper() != 'ROUGHNESS' and characteristic.upper() != 'LINKED ROUGHNESS':
                            characteristic = input('Select characteristic (' + '/'.join([char.lower() for char in char_list]) + '): ')

                        if characteristic.upper() == 'THICKNESS' and 'THICKNESS' in char_list:
                            char_list.remove('THICKNESS')
                            lw = 1
                            up = 0
                            while float(lw) > float(up):
                                lw = input('Select lower bound in units of Angstrom: ')
                                if lw.upper() == 'EXIT':
                                    quit()
                                up = input('Select upper bound in units of Angstrom: ')
                                if up.upper() == 'EXIT':
                                    quit()
                            lowerbound.append(lw)
                            upperbound.append(up)
                        if characteristic.upper() == 'DENSITY' and 'DENSITY' in char_list:
                            char_list.remove('DENSITY')
                            lw = 1
                            up = 0
                            while float(lw) > float(up):
                                lw = input('Select lower bound in units of mol/cm^3: ')
                                if lw.upper() == 'EXIT':
                                    quit()
                                up = input('Select upper bound in units of mol/cm^3: ')
                                if up.upper() == 'EXIT':
                                    quit()
                            lowerbound.append(lw)
                            upperbound.append(up)
                        if characteristic.upper() == 'ROUGHNESS' and 'ROUGHNESS' in char_list:
                            char_list.remove('ROUGHNESS')
                            lw = 1
                            up = 0
                            while float(lw) > float(up):
                                lw = input('Select lower bound in units of Angstrom: ')
                                if lw.upper() == 'EXIT':
                                    quit()
                                up = input('Select upper bound in units of Angstrom: ')
                                if up.upper() == 'EXIT':
                                    quit()
                            lowerbound.append(lw)
                            upperbound.append(up)
                        if characteristic.upper() == 'LINKED ROUGHNESS' and 'LINKED ROUGHNESS' in char_list:
                            char_list.remove('LINKED ROUGHNESS')
                            lw = 1
                            up = 0
                            while float(lw) > float(up):
                                lw = input('Select lower bound in units of Angstrom: ')
                                if lw.upper() == 'EXIT':
                                    quit()
                                up = input('Select upper bound in units of Angstrom: ')
                                if up.upper() == 'EXIT':
                                    quit()
                            lowerbound.append(lw)
                            upperbound.append(up)

                        print()
                        sample_params.append([layer,prop.upper(),mode.upper(),element, characteristic.upper()])
                        if len(char_list) > 0:
                            again = input('Would you liked to select another characteristic for '+ element+" (y/n): ")
                        else:
                            again = 'N'
                    val = input('Would you like to select another element (y/n)?')
        elif prop.upper() == "POLYMORPHOUS":
            b= []
            for ele in elements:
                if len(sample.structure[layer][ele].polymorph) > 0:
                    b.append(ele)
            poly_cont = 'Y'
            while poly_cont.upper() == 'Y' and len(b) > 0:
                poly_ele = input('Select the polymorph '+ str(b) +' you would liked to vary: ')
                if poly_ele.upper() == 'EXIT':
                    quit()

                num_poly = len(b)

                while poly_ele not in b:
                    poly_ele = input('Please select a polymorph ' + str(b) + ' : ')
                    if poly_ele.upper() == 'EXIT':
                        quit()


                polymorph = sample.structure[layer][poly_ele].polymorph
                whichPoly = input('Select polymorph (' + str(polymorph) + ') for which density you would like to vary?')
                if whichPoly.upper() == 'EXIT':
                    quit()
                while whichPoly not in polymorph:
                    whichPoly = input('Select polymorph (' + str(polymorph) + ') for which density you would like to vary?')
                    if whichPoly.upper() == 'EXIT':
                        quit()

                lw = input("Select the lower limit of the polymorph ratio (0-1): ")
                if lw.upper() == 'EXIT':
                    quit()
                up = input("Select the upper limit of the polymorph ratio (0-1): ")
                if up.upper() == 'EXIT':
                    quit()

                while(float(lw)>float(up) or float(lw)<0 or float(up) > 1):
                    if float(lw)>float(up):
                        lw = input("Make sure that your lower bound is smaller than the upper bound. Please select a new lower limit: ")
                        if lw.upper() == 'EXIT':
                            quit()
                        up = input("Please select a new upper bound: ")
                        if up.upper() == 'EXIT':
                            quit()
                    if float(lw) < 0:
                        lw = input("Please select a lower limit between 0 and 1: ")
                        if lw.upper() == 'EXIT':
                            quit()
                    if float(up) > 1:
                        up = input("Please select an upper limit between 0 and 1: ")
                        if up.upper() == 'EXIT':
                            quit()

                lowerbound.append(lw)
                upperbound.append(up)

                sample_params.append([layer, prop.upper(), poly_ele, whichPoly])
                # As of right now we will assume that we can have a maximum of 2 polymorphs
                print()
                if len(b) != 0:
                    b.remove(poly_ele)
                    poly_cont = input('Would you like to vary another polymorph in the same layer (y/n): ')
                    if poly_cont.upper() == 'EXIT':
                        quit()

        elif prop.upper() == 'MAGNETIC':
            my_mag = list()
            for ele in elements:
                if len(sample.structure[layer][ele].mag_density) > 0:
                    my_mag.append(ele)

            mag_ele = input('Select magnetic element you would like to vary (' + str(my_mag) + ': ')
            if mag_ele.upper() == 'EXIT':
                quit()
            while mag_ele not in my_mag:
                mag_ele = input('Please select an element element in (' + str(my_mag) + ': ')
                if mag_ele.upper() == 'EXIT':
                    quit()

            mag_poly = list(sample.structure[layer][mag_ele].polymorph)
            mag_cont = 'Y'
            while(mag_cont.upper() == 'Y' and len(my_mag)>0):
                if len(mag_poly) > 0:
                    mag_poly_cont = 'Y'
                    while(mag_poly_cont.upper() == 'Y' and len(mag_poly)>0):
                        whichMag = input('Select which polymorph ('+str(mag_poly)+') for which you would like to vary the magnetic density: ')
                        if whichMag.upper() == 'EXIT':
                            quit()
                        while whichMag not in mag_poly:
                            whichMag = input('Select which polymorph ('+str(mag_poly)+') for which you would like to vary the magnetic density: ')
                            if whichMag.upper() == 'EXIT':
                                quit()

                        lw = input('Enter the lower bound of the magnetic density of order mol/cm^3: ')
                        if lw.upper() == 'EXIT':
                            quit()
                        up = input('Enter the lower bound of the magnetic density of order mol.cm^3: ')
                        if up.upper() == 'EXIT':
                            quit()
                        while float(lw) > float(up):
                            lw = input('Make sure lower bound is smaller than upper bound. Enter lower bound again: ')
                            if lw.upper() == 'EXIT':
                                quit()
                            up = input('Enter upper bound: ')
                            if up.upper() == 'EXIT':
                                quit()
                        lowerbound.append(lw)
                        upperbound.append(up)

                        sample_params.append([layer, prop.upper(), mag_ele, whichMag])
                        print()
                        if len(mag_poly) != 0:
                            mag_poly_cont = input('Would you like to vary another polymorph magnetic density (y/n)?')
                            if mag_poly_cont.upper() == 'EXIT':
                                quit()
                            mag_poly.remove(whichMag)

                else:
                    lw = input('Enter the lower bound of the magnetic density of order mol/cm^3: ')
                    if lw.upper() == 'EXIT':
                        quit()
                    up = input('Enter the lower bound of the magnetic density of order mol.cm^3: ')
                    if up.upper() == 'EXIT':
                        quit()
                    while float(lw) > float(up):
                        lw = input('Make sure lower bound is smaller than upper bound. Enter lower bound again: ')
                        if lw.upper() == 'EXIT':
                            quit()
                        up = input('Enter upper bound: ')
                        if up.upper() == 'EXIT':
                            quit()
                    lowerbound.append(lw)
                    upperbound.append(up)
                    print()
                    sample_params.append([layer, prop.upper(), mag_ele])
                if len(my_mag) != 0:
                    my_mag.remove(mag_ele)
                    mag_cont = input('Would you like to select another magnetic element to vary (y/n)?')
                    if mag_cont.upper() == 'EXIT':
                        quit()

        cont = input('Would you liked to select another layer (y/n): ')


    # printing the chosen elements
    my_params = list()

    for sp in range(len(sample_params)):
        temp_list = list()
        params = sample_params[sp]
        lw = lowerbound[sp]
        up = upperbound[sp]

        temp_list.append(params[0])  # Layer info
        temp_list.append(params[1])  # Property

        if params[1] == 'STRUCTURAL':
            mode = params[2]  # mode
            if mode == 'COMPOUND':
                formula = layer_formula[sp][1]  # formula
                characteristic = params[3]
                temp_list.append(formula)
                temp_list.append('N/A')
                temp_list.append(characteristic)
            else:
                element = params[3]
                characteristic = params[4]
                temp_list.append(element)
                temp_list.append('N/A')
                temp_list.append(characteristic)
        elif params[1] == 'POLYMORPHOUS':
            temp_list.append(params[2])  # poly element
            temp_list.append(params[3])  # which poly
            temp_list.append('DENSITY RATIO')
        elif params[1] == 'MAGNETIC':
            if len(params) == 3:
                temp_list.append(params[2])  # element
                temp_list.append('N/A')
                temp_list.append('MAGNETIC DENSITY')
            else:
                temp_list.append(params[2])  # poly element
                temp_list.append(params[3])  # polymorph
                temp_list.append('MAGNETIC DENSITY')

        temp_list.append(lw)
        temp_list.append(up)
        my_params.append(temp_list)

    print()
    print('The list of scans you requested are:' + str(scans))
    print()
    print(my_params)
    header = ['Layer', 'Property', 'Element(s)', 'Polymorph', 'Characteristic', 'Upper Bound', 'Lower Bound']
    Ntab = PrettyTable(header)
    Ntab.add_rows(my_params)
    print(Ntab)

    return data_info[scans], data, sims, sample_params, lowerbound, upperbound


if __name__ == "__main__":

    fname = 'Pim10uc.h5'
    sample = ReadSampleHDF5(fname)  # import the sample information

    data_info, data, sims = ReadDataHDF5(fname)  # import the experimental data and simulated data

    scans = data_info[[1,2]]
    parameters = [[0, 'STRUCTURAL', 'ELEMENT', 'Sr', 'DENSITY'],
                  [0, 'STRUCTURAL', 'COMPOUND', 'ROUGHNESS'],
                  [1, 'STRUCTURAL', 'ELEMENT', 'La', 'DENSITY'],
                  [1, 'STRUCTURAL', 'ELEMENT', 'Mn', 'ROUGHNESS']]

    params = [sample, scans, data, sims, parameters]
    lw = [0.02, 0.1, 0.02, 0]
    up = [0.03, 5, 0.03, 5]
    bounds = list(zip(lw,up))

    ret = optimize.differential_evolution(scanCompute,bounds, args=params, maxiter=1, popsize=2)
    print(ret.x, ret.fun)