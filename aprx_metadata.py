import csv
import datetime
import getpass
import os
import re
import sys

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
        arcpy.AddMessage("Compiling metadata for map: {m.name}")
        v = {}
        v["mapName"] = m.name
        v.update(spatialExtent(m.defaultCamera.getExtent()))
        v.update(spatialSystem(m.defaultCamera.getExtent().spatialReference))
        lyrs = []
        for l in m.listLayers():
            lyr = {}
            if l.supports("NAME"):
                if l.supports("LONGNAME"):
                    if re.search(r"World_Imagery\\", l.longName):
                        continue
                lyr["layerName"] = l.name
            else:
                continue
            if l.supports("LONGNAME"):
                lyr["longName"] = l.longName
            if l.supports("visible"):
                lyr["visible"] = l.visible
            lyr["isBroken"] = l.isBroken
            if l.supports("DATASOURCE"):
                lyr["dataSource"] = l.dataSource
            lyr["isGroupLayer"] = l.isGroupLayer
            lyr["isFeatureLayer"] = l.isFeatureLayer
            lyr["isRasterLayer"] = l.isRasterLayer
            lyr["isBasemapLayer"] = l.isBasemapLayer
            lyr["isWebLayer"] = l.isWebLayer
            try:
                d = arcpy.Describe(l.name)
            except Exception:
                lyrs.append(lyr)
                continue
            if hasattr(d, "dataType"):
                lyr["dataType"] = d.dataType
            if hasattr(d, "datasetType"):
                lyr["datasetType"] = d.datasetType
            if hasattr(d, "hasZ"):
                lyr["hasZ"] = d.hasZ
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
            if l.supports("DEFINITIONQUERY"):
                lyr["definitionQuery"] = l.definitionQuery
            if l.supports("DATASOURCE"):
                try:
                    if l.supports("DATASOURCE"):
                        lyr["fields"] = ";".join(
                            [f.name for f in arcpy.ListFields(l.dataSource)]
                        )
                except Exception:
                    pass
            if l.isRasterLayer:
                r = arcpy.Raster(l.name)
                if hasattr(r, "bandCound"):
                    lyr["bandCount"] = r.bandCount
                if hasattr(r, "format"):
                    lyr["format"] = r.format
                if hasattr(r, "compressionType"):
                    lyr["compressionType"] = r.compressionType
                if hasattr(r, "bandNames"):
                    lyr["bandNames"] = r.bandNames
                if hasattr(r, "height"):
                    lyr["height"] = r.height
                if hasattr(r, "width"):
                    lyr["width"] = r.width
                if hasattr(r, "minimum"):
                    lyr["minimum"] = r.minimum
                if hasattr(r, "maximum"):
                    lyr["maximum"] = r.maximum
                if hasattr(r, "mean"):
                    lyr["mean"] = r.maximum
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
        oPath = os.path.join(os.getcwd(), f"{aprxName}.csv")
    else:
        oPath = os.path.join(outDir, f"{aprxName}.csv")
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


def main(aprx, outDir):
    """Main function"""
    meta = describeData(aprx)
    rows = flattenDict(meta)
    cols = dictKeys(rows)
    aprxPath = aprx.filePath
    oPath = writeFile(outDir, rows, cols, aprxPath)
    arcpy.AddMessage("Completed: {}".format(oPath))


if __name__ == "__main__":
    outDir = arcpy.GetParameterAsText(0)
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except Exception as e:
        arcpy.AddError(e)
        sys.exit()
    main(aprx, outDir)
