# PURPOSE
#   Scan MXD for layer descriptions and place output in CSV.
#
# OUTPUT
#   CSV with the following columns:
##    Data_Frame
##    Layer_Basename
##    Layer_Type
##    File_Extension
##    Layer_Catalog_Path
##    Layer_DefinitionQuery_Supported
##    Layer_DefinitionQuery
##    Field_Names
##    Feature_Type
##    Shape_Type
##    Has_Z'
##    Has_Spatial_Index
##    Layer_File
##    Layer_Path
##    Coordinate_Type
##    GCS_Name
##    GCS_Code
##    PCS_Name
##    PCS_Code
##    Linear_Unit_Name
##    Linear_Unit_Code
##    Datum_Name
##    Datum_Code
##    Spheroid_Name
##    Spheroid_Code
##    Layer_Description
##    Raster_Format
##    Raster_Band_Count
##    Raster_Compression_Type
##    Raster_Size_MB
##    Raster_Cell_Width
##    Raster_Cell_Height
##    Raster_Cell_Min
##    Raster_Cell_Max
##    Raster_Cell_Mean
##    Raster_Extent_JSON
#
# AUTHOR(S)
#   Caleb Grant, Integral Consulting, Inc. (CG)
#
# NOTES
#   1) This script takes 1 argument and 1 optional argument
#       - MXD path
#       - *Output CSV directory (optional)
#
# HISTORY
#   1) Created 2020-06-26. CG.
#
#
# ISSUES
#   - Nested layer groups where > 6 nested groups are present
#   - Layers pulled in through a connection
# =========================================================================

import sys
import os
import csv
import datetime
import getpass
import time
import arcpy


OS_USER = getpass.getuser()
USER = ''.join([i for i in OS_USER if not i.isdigit()])
RUN_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")

def mainFunction(mxd):
    def lyrDescriptions(l):
        try:
            desc = arcpy.Describe(l)
        except:
            try:
                meta.update({str(l.name): {
                    'Data_Frame': frame.name,
                    'Layer_Basename': '',
                    'Layer_Type': '',
                    'File_Extension': '',
                    'Layer_Catalog_Path': '',
                    'Layer_DefinitionQuery_Supported': '',
                    'Layer_DefinitionQuery': '',
                    'Field_Names': '',
                    'Feature_Type': '',
                    'Shape_Type': '',
                    'Has_Z': '',
                    'Has_Spatial_Index': '',
                    'Layer_File': '',
                    'Layer_Path': '',
                    'Coordinate_Type': '',
                    'GCS_Name': '',
                    'GCS_Code': '',
                    'PCS_Name': '',
                    'PCS_Code': '',
                    'Linear_Unit_Name': '',
                    'Linear_Unit_Code': '',
                    'Datum_Name': '',
                    'Datum_Code': '',
                    'Spheroid_Name': '',
                    'Spheroid_Code': '',
                    'Layer_Description': '',
                    'Raster_Format': '',
                    'Raster_Band_Count': '',
                    'Raster_Compression_Type': '',
                    'Raster_Size_MB': '',
                    'Raster_Cell_Width': '',
                    'Raster_Cell_Height': '',
                    'Raster_Cell_Min': '',
                    'Raster_Cell_Max': '',
                    'Raster_Cell_Mean': '',
                    'Raster_Extent_JSON': ''
                    }
                })
            except:
                return
            return

        if hasattr(desc, 'fieldInfo'):
            field_info = desc.fieldInfo
            fieldNames = [str(field_info.getFieldName(index)) for index in range(0, field_info.count)]
            fieldNameStr = ""
            for field in fieldNames:
                if field == fieldNames[-1]:
                    fieldNameStr = fieldNameStr + field
                else:
                    fieldNameStr = fieldNameStr + "{};".format(field)
        else:
            fieldNameStr = ""

        if hasattr(desc, 'featureType'):
            feature_type = desc.featureType
        else:
            feature_type = ""

        if hasattr(desc, 'shapeType'):
            shape_type = desc.shapeType
        else:
            shape_type = ""

        if hasattr(desc, 'hasZ'):
            has_z = desc.hasZ
        else:
            has_z = False

        if hasattr(desc, 'hasSpatialIndex'):
            has_spat_index = desc.hasSpatialIndex
        else:
            has_spat_index = False

        try:
            lyr_name = l.longName
        except:
            lyr_name = desc.nameString

        if hasattr(desc, 'file'):
            lyr_file = desc.file
        else:
            lyr_file = ""

        if hasattr(desc, 'path'):
            lyr_path = desc.path
        else:
            lyr_path = ""

        if hasattr(desc, 'extension'):
            lyr_extension = desc.extension
            if lyr_extension == "":
                lyr_extension = 'gdb'
        else:
            lyr_extension = ""

        if hasattr(desc, 'dataType'):
            lyr_dtype = desc.dataType
        else:
            lyr_dtype = ""

        if hasattr(desc, 'baseName'):
            lyr_basename = desc.baseName
        else:
            lyr_basename = ""

        if hasattr(desc, 'catalogPath'):
            lyr_catpath = desc.catalogPath
        else:
            lyr_catpath = ""

        if lyr.supports("DEFINITIONQUERY"):
            lyrDefSupport = True
            if lyr.definitionQuery == '':
                lyrDef = ''
            else:
                lyrDef = str(lyr.definitionQuery)
        else:
            lyrDefSupport = False
            lyrDef = ''

        if hasattr(desc, 'description'):
            lyr_description = lyr.description
        else:
            lyr_description = ""

        try:
            lyr_coordType = desc.spatialReference.type
        except:
            lyr_coordType = ""

        try:
            lyr_GCSName = desc.spatialReference.GCSName
            if lyr_GCSName == "":
                lyr_GCSCode = ""
            else:
                lyr_GCSCode = desc.spatialReference.GCSCode
        except:
            lyr_GCSName = ""
            lyr_GCSCode = ""

        try:
            lyr_PCSName = desc.spatialReference.PCSName
            if lyr_PCSName == "":
                lyr_PCSCode = ""
            else:
                lyr_PCSCode = desc.spatialReference.PCSCode
        except:
            lyr_PCSName = ""
            lyr_PCSCode = ""

        try:
            lyr_datumName = desc.spatialReference.datumName
            if lyr_datumName == "":
                lyr_datumCode = ""
            else:
                lyr_datumCode = desc.spatialReference.datumCode
        except:
            lyr_datumName = ""
            lyr_datumCode = ""

        try:
            lyr_spheroidName = desc.spatialReference.spheroidName
            if lyr_spheroidName == "":
                lyr_spheroidCode = ""
            else:                
                lyr_spheroidCode = desc.spatialReference.spheroidCode
        except:
            lyr_spheroidName = ""
            lyr_spheroidCode = ""

        try:
            lyr_coord_unit = desc.spatialReference.linearUnitName
            if lyr_coord_unit == "":
                lyr_coord_unit_code = ""
            else:
                lyr_coord_unit_code = desc.spatialReference.linearUnitCode
        except:
            lyr_coord_unit = ""
            lyr_coord_unit_code = ""

        if l.isRasterLayer:
            raster = arcpy.Raster(lyr_catpath)
            try:
                raster_format = raster.format
            except:
                raster_format = ""

            try:
                raster_bands = raster.bandCount
            except:
                raster_bannds = ""

            try:
                raster_compression = raster.compressionType
            except:
                raster_compression = ""

            try:
                raster_size = float(raster.uncompressedSize) / 1000000 # Byte --> Megabyte
            except:
                raster_size = ""

            try:
                raster_cell_width = raster.meanCellWidth
            except:
                raster_cell_width = ""

            try:
                raster_cell_height = raster.meanCellHeight
            except:
                raster_cell_height = ""

            try:
                raster_cell_min = raster.minimum
            except:
                raster_cell_min = ""

            try:
                raster_cell_max = raster.maximum
            except:
                raster_cell_max = ""

            try:
                raster_cell_mean = raster.mean
            except:
                raster_cell_mean = ""

            try:
                raster_extent = raster.extent.JSON
            except:
                raster_extent = ""
        else:
            raster_format = ""
            raster_bands = ""
            raster_format = ""
            raster_bands = ""
            raster_compression = ""
            raster_size = ""
            raster_cell_width = ""
            raster_cell_height = ""
            raster_cell_min = ""
            raster_cell_max = ""
            raster_cell_mean = ""
            raster_extent = ""

        meta.update({str(lyr_name): {
            'Data_Frame': frame.name,
            'Layer_Basename': lyr_basename,
            'Layer_Type': lyr_dtype,
            'File_Extension': lyr_extension,
            'Layer_Catalog_Path': lyr_catpath,
            'Layer_DefinitionQuery_Supported': lyrDefSupport,
            'Layer_DefinitionQuery': lyrDef,
            'Field_Names': fieldNameStr,
            'Feature_Type': feature_type,
            'Shape_Type': shape_type,
            'Has_Z': has_z,
            'Has_Spatial_Index': has_spat_index,
            'Layer_File': lyr_file,
            'Layer_Path': lyr_path,
            'Coordinate_Type': lyr_coordType,
            'GCS_Name': lyr_GCSName,
            'GCS_Code': lyr_GCSCode,
            'PCS_Name': lyr_PCSName,
            'PCS_Code': lyr_PCSCode,
            'Linear_Unit_Name': lyr_coord_unit,
            'Linear_Unit_Code': lyr_coord_unit_code,
            'Datum_Name': lyr_datumName,
            'Datum_Code': lyr_datumCode,
            'Spheroid_Name': lyr_spheroidName,
            'Spheroid_Code': lyr_spheroidCode,
            'Layer_Description': lyr_description,
            'Raster_Format': raster_format,
            'Raster_Band_Count': raster_bands,
            'Raster_Compression_Type': raster_compression,
            'Raster_Size_MB': raster_size,
            'Raster_Cell_Width': raster_cell_width,
            'Raster_Cell_Height': raster_cell_height,
            'Raster_Cell_Min': raster_cell_min,
            'Raster_Cell_Max': raster_cell_max,
            'Raster_Cell_Mean': raster_cell_mean,
            'Raster_Extent_JSON': raster_extent
            }
        })

    meta = {}
    cur_mxd = mxd
    df = arcpy.mapping.ListDataFrames(cur_mxd, "*")
    df_index = 0
    for frame in df:
        for lyr in arcpy.mapping.ListLayers(cur_mxd, "", frame):
            if lyr.isBasemapLayer:
                pass
            else:
                if lyr.isGroupLayer:
                    for glyr in lyr:
                        if glyr.isBasemapLayer:
                            pass
                        else:
                            if glyr.isGroupLayer:
                                for g2lyr in glyr:
                                    if g2lyr.isBasemapLayer:
                                        pass
                                    else:
                                        if g2lyr.isGroupLayer:
                                            for g3lyr in g2lyr:
                                                if g3lyr.isBasemapLayer:
                                                    pass
                                                else:
                                                    if g3lyr.isGroupLayer:
                                                        for g4lyr in g3lyr:
                                                            if g4lyr.isBasemapLayer:
                                                                pass
                                                            else:
                                                                if g4lyr.isGroupLayer:
                                                                    for g5lyr in g4lyr:
                                                                        if g5lyr.isBasemapLayer:
                                                                            pass
                                                                        else:
                                                                            if g5lyr.isGroupLayer:
                                                                                for g6lyr in g5lyr:
                                                                                    if g6lyr.isBasemapLayer:
                                                                                        pass
                                                                                    else:
                                                                                        try:
                                                                                            lyrDescriptions(g6lyr)
                                                                                        except:
                                                                                            arcpy.AddWarning('> 6 nested groups present. Skipping those.')
                                                                                            pass
                                                                            else:
                                                                                lyrDescriptions(g5lyr)
                                                                else:
                                                                    lyrDescriptions(g4lyr)
                                                    else:
                                                        lyrDescriptions(g3lyr)
                                        else:
                                            lyrDescriptions(g2lyr)
                            else:
                                lyrDescriptions(glyr)
                else:
                    lyrDescriptions(lyr)
        df_index += 1

    arcpy.AddMessage('\n')
    arcpy.AddMessage('Total dataframes: {}'.format(df_index))
    lyr_count = 0
    for lyr in meta:
        lyr_count += 1
    arcpy.AddMessage('Total layers: {}'.format(lyr_count))

    return meta

def write_output(mxdName, mxdMeta, csvPath):
    if csvPath == '':
        fPath = 'H:\{}.csv'.format(mxdName)
    else:
        fPath = os.path.join(csvPath, mxdName + '.csv')

    if os.path.exists(fPath):
        try:
            os.remove(fPath)
        except:
            sys.exit()

    headers = ['Layer_Name', 'Data_Frame', 'Layer_Basename', 'Layer_Type', 'File_Extension', 'Feature_Type', 'Shape_Type', 'Has_Z', 'Has_Spatial_Index', 'Field_Names',
                'Layer_Path', 'Layer_Catalog_Path', 'Layer_DefinitionQuery_Supported', 'Layer_DefinitionQuery', 'Coordinate_Type', 'GCS_Name', 'GCS_Code', 'PCS_Name', 'PCS_Code',
                'Linear_Unit_Name', 'Linear_Unit_Code', 'Datum_Name', 'Datum_Code', 'Spheroid_Name', 'Spheroid_Code',
                'Raster_Format', 'Raster_Band_Count', 'Raster_Compression_Type', 'Raster_Size_MB', 'Raster_Cell_Width', 'Raster_Cell_Height',
                'Raster_Cell_Min', 'Raster_Cell_Max', 'Raster_Cell_Mean', 'Raster_Extent_JSON',
                'Layer_Description', 'Script_User', 'Script_Run_Time']

    try:
        with open(fPath, 'wb') as f:
            f_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            f_writer.writerow(headers)
            for lyr in sorted(mxdMeta.keys()):
                row = []
                for header in headers:
                    if header == 'Layer_Name':
                        row.append(lyr)
                    elif header == 'Script_User':
                        row.append(USER)
                    elif header == 'Script_Run_Time':
                        row.append(RUN_TIME)
                    else:
                        row.append(mxdMeta[lyr][header])
                f_writer.writerow(row)
    except:
        arcpy.AddError('Error writing to CSV')
        sys.exit()
    return fPath

if __name__ == '__main__':
    mxd = arcpy.mapping.MapDocument("CURRENT")
    mxdMeta = mainFunction(mxd)
    mxdPath = mxd.filePath
    mxdBaseName = os.path.basename(mxdPath)
    mxdName = os.path.splitext(mxdBaseName)[0]
    csvPath = arcpy.GetParameterAsText(0)
    output_file = write_output(mxdName, mxdMeta, csvPath)
    arcpy.AddMessage('CSV generated')
    arcpy.AddMessage('Output: {}'.format(output_file))
    arcpy.AddMessage('\n')
