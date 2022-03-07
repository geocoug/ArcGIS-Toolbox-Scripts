import csv
import os

import arcpy

"""
TO-DO
add user who ran the script
add time script was ran
"""


def writeFile():
    pass


def spatialExtent(obj):
    """Return spatial boundary for a given data object"""
    return {"XMax": obj.XMax, "XMin": obj.XMin, "YMax": obj.YMax, "YMin": obj.YMin}


def spatialSystem(obj):
    """Return spatial type, geographic, and projected coordinate
    system information for a given data object"""
    return {
        "coordType": obj.type,
        "GCSCode": obj.GCSCode,
        "GCSName": obj.GCSName,
        "PCSCode": obj.PCSCode,
        "PCSName": obj.PCSName,
        "linearUnitName": obj.linearUnitName,
        "spheroidName": obj.spheroidName,
    }


def describeData(aprx):
    meta = {
        "homeFolder": aprx.homeFolder,
        "filePath": aprx.filePath,
        "defaultGeodatabase": aprx.defaultGeodatabase,
        "dateSaved": aprx.dateSaved,
    }
    mapViews = []
    for m in aprx.listMaps():
        v = {}
        v["mapName"] = m.name
        v.update(spatialExtent(m.defaultCamera.getExtent()))
        v.update(spatialSystem(m.defaultCamera.getExtent().spatialReference))
        lyrs = []
        for l in m.listLayers():
            lyr = {}
            if l.supports("NAME"):
                lyr["layerName"] = l.name
            else:
                lyr["layerName"] = None
            if l.supports("LONGNAME"):
                lyr["longName"] = l.longName
            else:
                lyr["longName"] = None
            if l.supports("DATASOURCE"):
                lyr["dataSource"] = l.dataSource
            else:
                lyr["dataSource"] = None
            lyr["isGroupLayer"] = l.isGroupLayer
            lyr["isFeatureLayer"] = l.isFeatureLayer
            lyr["isRasterLayer"] = l.isRasterLayer
            lyr["isBasemapLayer"] = l.isBasemapLayer
            lyr["isWebLayer"] = l.isWebLayer
            lyr["visible"] = l.visible
            lyr["isBroken"] = l.isBroken
            if l.supports("DEFINITIONQUERY"):
                lyr["definitionQuery"] = l.definitionQuery
            else:
                lyr["definitionQuery"] = None

            d = arcpy.Describe(l.name)
            if hasattr(d, "datasetType"):
                lyr["datasetType"] = d.datasetType
            if hasattr(d, "DSID"):
                lyr["DSID"] = d.DSID
            if hasattr(d, "catalogPath"):
                lyr["catalogPath"] = d.catalogPath
            if hasattr(d, "path"):
                lyr["path"] = d.path
            if hasattr(d, "dataType"):
                lyr["dataType"] = d.dataType
            if hasattr(d, "shapeType"):
                lyr["shapeType"] = d.shapeType
            if hasattr(d, "hasZ"):
                lyr["hasZ"] = d.hasZ
            try:
                lyr["fields"] = [
                    [f.name, f.type, f.length] for f in arcpy.ListFields(l.name)
                ]
            except Exception as e:
                lyr["fields"] = None
            if hasattr(d, "extent"):
                lyr.update(
                    {
                        "layer" + key: value
                        for key, value in spatialExtent(d.extent).items()
                    }
                )
            if hasattr(d, "spatialReference"):
                lyr.update(
                    {
                        "layer" + key: value
                        for key, value in spatialSystem(d.spatialReference).items()
                    }
                )

            if l.isRasterLayer:
                r = arcpy.Raster(l.name)
                if hasattr(r, "bandCound"):
                    lyr["bandCount"] = r.bandCount
                else:
                    lyr["bandCound"] = None
                if hasattr(r, "format"):
                    lyr["format"] = r.format
                else:
                    lyr["format"] = None
                if hasattr(r, "compressionType"):
                    lyr["compressionType"] = r.compressionType
                else:
                    lyr["compressionType"] = None
                if hasattr(r, "bandNames"):
                    lyr["bandNames"] = r.bandNames
                else:
                    lyr["bandNames"] = None
                if hasattr(r, "height"):
                    lyr["height"] = r.height
                else:
                    lyr["height"] = None
                if hasattr(r, "width"):
                    lyr["width"] = r.width
                else:
                    lyr["width"] = None
                if hasattr(r, "minimum"):
                    lyr["minimum"] = r.minimum
                else:
                    lyr["minimum"] = None
                if hasattr(r, "maximum"):
                    lyr["maximum"] = r.maximum
                else:
                    lyr["maximum"] = None
                if hasattr(r, "mean"):
                    lyr["mean"] = r.maximum
                else:
                    lyr["mean"] = None

            lyrs.append(lyr)
        v["layers"] = lyrs
        mapViews.append(v)
    meta.update({"mapViews": v})
    # Currently overwriting map descriptions with each iteration
    return meta


def main(aprx):
    meta = describeData(aprx)


if __name__ == "__main__":
    inFile = arcpy.GetParameterAsText(0)
    outFile = arcpy.GetParameterAsText(1)
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except Exception as e:
        arcpy.AddError(e)
    arcpy.AddMessage(f"Compiling metadata for {aprx.name}")
    main(aprx)
