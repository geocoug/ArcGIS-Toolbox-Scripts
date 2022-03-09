import csv
import datetime
import getpass
import os

import arcpy

OS_USER = getpass.getuser()
USER = "".join([i for i in OS_USER if not i.isdigit()])
RUN_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")


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


def dictKeys(obj):
    """Get all unique keys in a list of dictionaries"""
    keys = []
    for dict_obj in obj:
        for key, value in dict_obj.items():
            if key not in keys:
                keys.append(key)
    return keys


def flattenDict(dict_obj):
    """Transform a nested dictionary into a 'flat'
    list of dictionaries, equivilant to a list of table rows."""
    rows = []
    project_desc = {key: val for (key, val) in dict_obj.items() if type(val) != list}
    for view in range(len(dict_obj["mapViews"])):
        map_desc = {
            key: val
            for (key, val) in dict_obj["mapViews"][view].items()
            if type(val) != list
        }
        for layer in range(len(dict_obj["mapViews"][view]["layers"])):
            layer_desc = {
                key: val
                for (key, val) in dict_obj["mapViews"][view]["layers"][layer].items()
            }
            rows.append({**project_desc, **map_desc, **layer_desc})
    return rows


def describeData(aprx):
    """Retrieve project, map, and layer attributes for a single APRX file."""
    meta = {
        "homeFolder": aprx.homeFolder,
        "filePath": aprx.filePath,
        "defaultGeodatabase": aprx.defaultGeodatabase,
        "dateSaved": aprx.dateSaved.strftime("%Y-%m-%d %H:%M:%S"),
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
            if l.supports("visible"):
                lyr["visible"] = l.visible
            lyr["isBroken"] = l.isBroken
            if l.supports("DATASOURCE"):
                lyr["dataSource"] = l.dataSource
            else:
                lyr["dataSource"] = None
            lyr["isGroupLayer"] = l.isGroupLayer
            lyr["isFeatureLayer"] = l.isFeatureLayer
            lyr["isRasterLayer"] = l.isRasterLayer
            lyr["isBasemapLayer"] = l.isBasemapLayer
            lyr["isWebLayer"] = l.isWebLayer
            if l.supports("DEFINITIONQUERY"):
                lyr["definitionQuery"] = l.definitionQuery
            else:
                lyr["definitionQuery"] = None

            try:
                d = arcpy.Describe(l.name)
            except:
                lyrs.append(lyr)
                continue

            if hasattr(d, "catalogPath"):
                lyr["catalogPath"] = d.catalogPath
            if hasattr(d, "path"):
                lyr["path"] = d.path
            if hasattr(d, "dataType"):
                lyr["dataType"] = d.dataType
            if hasattr(d, "datasetType"):
                lyr["datasetType"] = d.datasetType
            if hasattr(d, "DSID"):
                lyr["DSID"] = d.DSID
            if hasattr(d, "shapeType"):
                lyr["shapeType"] = d.shapeType
            if hasattr(d, "hasZ"):
                lyr["hasZ"] = d.hasZ
            try:
                lyr["fields"] = ";".join([f.name for f in arcpy.ListFields(l.name)])
            except:
                lyr["fields"] = None
            if hasattr(d, "extent"):
                if d.extent:
                    lyr.update(
                        {
                            "layer" + key: value
                            for key, value in spatialExtent(d.extent).items()
                        }
                    )
            if hasattr(d, "spatialReference"):
                if d.spatialReference:
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
    meta.update({"mapViews": mapViews})
    return meta


def writeFile(outDir, rows, cols, aprxPath):
    """Export data to CSV file."""
    # Append script runtime columns
    cols.extend(["Script_User", "Script_Run_Time"])
    for row in rows:
        row.update({"Script_User": USER, "Script_Run_Time": RUN_TIME})

    aprxName = os.path.splitext(os.path.basename(aprxPath))[0]
    if outDir is None or outDir == "":
        oPath = "H:\{}.csv".format(aprxName)
    else:
        oPath = os.path.join(outDir, aprxName + ".csv")
    if os.path.exists(oPath):
        try:
            os.remove(oPath)
        except Exception as e:
            arcpy.AddError(e)
    try:
        with open(oPath, "w", newline="") as f:
            writer = csv.writer(
                f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(cols)
            for row in rows:
                r = []
                for col in cols:
                    if col in row:
                        r.append(str(row[col]))
                    else:
                        r.append(None)
                writer.writerow(r)
    except Exception as e:
        arcpy.AddError(e)
    return oPath


def main(aprx, oFile):
    meta = describeData(aprx)
    rows = flattenDict(meta)
    cols = dictKeys(rows)
    aprxPath = aprx.filePath
    oPath = writeFile(oFile, rows, cols, aprxPath)
    arcpy.AddMessage("Completed: {}".format(oPath))


if __name__ == "__main__":
    outDir = arcpy.GetParameterAsText(0)
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except Exception as e:
        print(e)
        arcpy.AddError(e)
    arcpy.AddMessage("Compiling metadata.")
    main(aprx, outDir)
