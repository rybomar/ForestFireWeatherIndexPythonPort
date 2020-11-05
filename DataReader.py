from time import strptime

import numpy as np
import gdal
import sys
import os
import re
import glob
import datetime

class DataReader:
    # mth = None #month
    # day = None #day of month
    # temp = None #temperatur in Celsius degree
    # rhum = None #Noon relative humidity (%)
    # wind = None #Noon wind speed (km/h)
    # prcp = None #DMC (Duff Moisture Content)

    # Loads xxx data from list of .h5 files (paths)
    # returns numpy 3D array with X,Y,Z size, where X is width, Y is high and Z is count of paths
    # in case of error while reading file, values should be -100 or other "nodata values"
    # all nodata values (from metadata) are replaced with "nodata values"
    # returns None when unable to read any of the files or rasters sizes differ
    # test data: \\dt-335\H\H5_data\Tem2

    def __loadData__(self, paths, datasubset, nodataValue):
        result_list = []
        x_size = 0
        y_size = 0
        for el in paths:
            if not os.path.isfile(el) or el is None:
                result_list.append(None)
                continue
            hdf_ds = gdal.Open(el, gdal.GA_ReadOnly)
            if not hdf_ds:
                result_list.append(None)
                continue
            band_ds = gdal.Open(hdf_ds.GetSubDatasets()[datasubset][0], gdal.GA_ReadOnly)
            if not band_ds:
                result_list.append(None)
                continue
            if (x_size > 0 and x_size != band_ds.RasterXSize) or (x_size > 0 and y_size != band_ds.RasterYSize):
                print('[DataReader] Error in loading HDF5 data: Data size in given files differs', file=sys.stderr)
                return None
            x_size = band_ds.RasterXSize
            y_size = band_ds.RasterYSize
            el_nodata = hdf_ds.GetMetadataItem('what_nodata')
            to_append = band_ds.ReadAsArray()
            to_append[to_append == float(el_nodata)] = nodataValue
            result_list.append(to_append)
        if x_size == 0 and y_size == 0:
            print('[DataReader] Error in loading HDF5 data: None of given files contain a valid data', file=sys.stderr)
            return None
        i = 0
        while i < len(result_list):
            if result_list[i] is None:
                result_list[i] = np.full((y_size, x_size), nodataValue)
            i += 1
        return np.swapaxes(np.array(result_list, dtype=float), 0, 2)

    def loadTempData(self, paths):
        nodataValue = -100
        return self.__loadData__(paths, 0, nodataValue)

    def loadRhumData(self, paths):
        nodataValue = -100
        return self.__loadData__(paths, 0, nodataValue)

    # test data: \\dt-335\H\H5_data\Wind
    def loadWindDataUU(self, paths):
        nodataValue = -100
        return self.__loadData__(paths, 0, nodataValue)

    def loadWindDataVV(self, paths):
        nodataValue = -100
        return self.__loadData__(paths, 1, nodataValue)

    def loadRainData(self, paths):
        nodataValue = -100
        return self.__loadData__(paths, 0, nodataValue)

    # example: findFilesByDateType(r'\\dt-335\H\H5_data', '2018-04-02', 'wind')
    # example2: findFilesByDateType(r'C:\H5_data', '2019-05-01', 'rain', range(0,11))
    # allowed types: temp, rhum, wind, rain

    def findFilesByDateType(self, maindir, fdate, ftype, fhours=None):
        allowedTypes = {'temp': 'tem2_inca', 'rhum': 'rhum_inca', 'wind': 'wind_inca', 'rain': 'acc0010_grs'}
        if ftype not in allowedTypes:
            print('[DataReader] Error while finding files: filesType not recognized', file=sys.stderr)
            return None
        dateRegExp = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
        if not dateRegExp.match(fdate):
            print('[DataReader] Error while finding files: incorrect date format', file=sys.stderr)
            return None
        if not os.path.isdir(maindir):
            print('[DataReader] Error while finding files: maindir does not exist', file=sys.stderr)
            return None
        fdate = fdate.replace('-', '')
        files = glob.glob(maindir + '/**/' + fdate + '*' + allowedTypes[ftype] + '.h5', recursive=True)

        # data verification procedure - fill blanks, check duplicates, filter per hours (if fhours is set)
        verify_array = {}
        for f in files:
            if f not in verify_array:
                verify_array[os.path.basename(f)] = f
            else:
                print('[DataReader] Error while finding files: duplicated data found (' + verify_array[os.path.basename(f)] + ' and ' + f + ')', file=sys.stderr)
                return None
        results = []
        if ftype == 'rain':
            for i in range(0, 25):
                if (fhours is not None) and (i not in fhours):
                    continue
                for j in range(0, 6):
                    i = str(i).zfill(2)
                    j = str(j)
                    isname = fdate + i + j + '0_' + allowedTypes[ftype] + '.h5'
                    if isname not in verify_array:
                        print('[DataReader] Warning while finding files: missing data (' + isname + '), blank added', file=sys.stderr)
                        results.append(None)
                    else:
                        results.append(verify_array[isname])
        else:
            for i in range(0, 24):
                if (fhours is not None) and (i not in fhours):
                    continue
                i = str(i).zfill(2)
                isname = fdate + i + '00_' + allowedTypes[ftype] + '.h5'
                if isname not in verify_array:
                    print('[DataReader] Warning while finding files: missing data (' + isname + '), blank added', file=sys.stderr)
                    results.append(None)
                else:
                    results.append(verify_array[isname])
        return results

    def sumRainByDay(self, fdate):
        dateRegExp = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
        if not dateRegExp.match(fdate):
            print('[DataReader] Error while summing rain by day: incorrect date format', file=sys.stderr)
            return None
        fdate = strptime(fdate)
        pass
