#!/usr/bin/python
# coding: utf-8
#
# PURPOSE
#    Scan APRX for layout, map, and layer metadata and write findings
#    to a CSV.
#
# AUTHOR(S)
#   Caleb Grant (CG)
#
# NOTES
#   1) This script is designed to be run as an ArcGIS Pro Toolbox Script.
#   2) There is one optional argument:
#       - Output CSV directory
#   3) The output CSV file is given same name as the input APRX file.
#
# HISTORY
#   DATE            REVISION
#   ----------      -------------------------------------------------------
#   2022-04-15      Created. CG.
#   2022-10-03      Link layout mapframes to map views. CG.
#                   Update function docstrings. CG.
# =========================================================================

import csv
import datetime
import getpass
import os
import re
import sys

# Check if ArcGIS License can be utilized for ArcPy
# This shouldnt be an issue since the user will already have ArcGIS Pro open.
try:
    import arcpy
except RuntimeError as e:
    raise

OS_USER = getpass.getuser()
USER = "".join([i for i in OS_USER if not i.isdigit()])
RUN_TIME = datetime.datetime.now().isoformat()


def spatialExtent(obj: dict) -> dict:
    """Return spatial boundary for a map object

    Args:
        obj (dict): map defaultCamera.getExtent()

    Returns:
        dict: bounding box for the map view
    """
    return {"XMax": obj.XMax, "XMin": obj.XMin, "YMax": obj.YMax, "YMin": obj.YMin}


def spatialSystem(obj: dict) -> dict:
    """Return spatial type, geographic, and projected coordinate
    system information for a map object

    Args:
        obj (dict): map spatialReference information

    Returns:
        dict: compiled spatial details of interest
    """
    return {
        "coordType": obj.type,
        "GCSCode": obj.GCSCode,
        "GCSName": obj.GCSName,
        "PCSCode": obj.PCSCode,
        "PCSName": obj.PCSName,
        "linearUnitName": obj.linearUnitName,
        "spheroidName": obj.spheroidName,
    }


def dict_keys(obj: dict) -> list:
    """Get all unique keys in a list of dictionaries

    Args:
        obj (dict): Any dictionary

    Returns:
        list: List of unique dictionary keys
    """
    keys = []
    for d in obj:
        for key, value in d.items():
            if key not in keys:
                keys.append(key)
    return keys


def flatten_dict(obj: dict) -> list:
    """Transform a nested dictionary into a 'flat'
    list of dictionaries, equivilant to a list of table rows.

    Args:
        obj (dict): Nested dictionary returned from the describe_data() method.

    Returns:
        list: List of record dictionaries
    """
    rows = []
    desc = {key: val for (key, val) in obj.items() if type(val) != list}
    for view in range(len(obj["maps"])):
        map_desc = {
            key: val for (key, val) in obj["maps"][view].items() if type(val) != list
        }
        for layer in range(len(obj["maps"][view]["layers"])):
            layer_desc = {
                key: val for (key, val) in obj["maps"][view]["layers"][layer].items()
            }
            rows.append({**desc, **map_desc, **layer_desc})
    return rows


def describe_data(aprx: str) -> dict:
    """Retrieve project, map, and layer attributes for a single APRX file.

    Args:
        aprx (str): APRX file path.

    Returns:
        dict: Summary of metadata for maps in an APRX.
    """
    data = {}
    maps = []
    for m in aprx.listMaps():
        arcpy.AddMessage(f"Compiling metadata for map: {m.name}")
        mapdata = {}
        mapdata["mapName"] = m.name
        mapdata.update(spatialExtent(m.defaultCamera.getExtent()))
        mapdata.update(spatialSystem(m.defaultCamera.getExtent().spatialReference))
        lyrs = []
        for l in m.listLayers():
            lyr_data = {}
            if l.supports("NAME"):
                lyr_data["layerName"] = l.name
            else:
                continue
            if l.supports("LONGNAME"):
                if re.search(r"World_Imagery\\", l.longName):
                    continue
                lyr_data["longName"] = l.longName
            if l.supports("visible"):
                lyr_data["visible"] = l.visible
            lyr_data["isBroken"] = l.isBroken
            if l.supports("DATASOURCE"):
                lyr_data["dataSource"] = l.dataSource
            lyr_data["isGroupLayer"] = l.isGroupLayer
            lyr_data["isFeatureLayer"] = l.isFeatureLayer
            lyr_data["isRasterLayer"] = l.isRasterLayer
            lyr_data["isBasemapLayer"] = l.isBasemapLayer
            lyr_data["isWebLayer"] = l.isWebLayer
            if l.supports("DEFINITIONQUERY"):
                lyr_data["definitionQuery"] = l.definitionQuery
            if l.supports("DATASOURCE"):
                try:
                    if l.supports("DATASOURCE"):
                        lyr_data["fields"] = ";".join(
                            [f.name for f in arcpy.ListFields(l.dataSource)]
                        )
                except Exception:
                    pass
            try:
                d = arcpy.Describe(l)
                if hasattr(d, "dataType"):
                    lyr_data["dataType"] = d.dataType
                if hasattr(d, "datasetType"):
                    lyr_data["datasetType"] = d.datasetType
                if hasattr(d, "hasZ"):
                    lyr_data["hasZ"] = d.hasZ
                if hasattr(d, "extent"):
                    if d.extent:
                        lyr_data.update(
                            {
                                "layer" + key: value
                                for key, value in spatialExtent(d.extent).items()
                            }
                        )
                if hasattr(d, "spatialReference"):
                    if d.spatialReference:
                        lyr_data.update(
                            {
                                "layer" + key: value
                                for key, value in spatialSystem(
                                    d.spatialReference
                                ).items()
                            }
                        )
            except Exception:
                pass
            try:
                if l.isRasterLayer:
                    r = arcpy.Raster(l.name)
                    if hasattr(r, "bandCound"):
                        lyr_data["bandCount"] = r.bandCount
                    if hasattr(r, "format"):
                        lyr_data["format"] = r.format
                    if hasattr(r, "compressionType"):
                        lyr_data["compressionType"] = r.compressionType
                    if hasattr(r, "bandNames"):
                        lyr_data["bandNames"] = r.bandNames
                    if hasattr(r, "height"):
                        lyr_data["height"] = r.height
                    if hasattr(r, "width"):
                        lyr_data["width"] = r.width
                    if hasattr(r, "minimum"):
                        lyr_data["minimum"] = r.minimum
                    if hasattr(r, "maximum"):
                        lyr_data["maximum"] = r.maximum
                    if hasattr(r, "mean"):
                        lyr_data["mean"] = r.maximum
            except Exception:
                pass
            lyrs.append(lyr_data)
        mapdata["layers"] = lyrs
        maps.append(mapdata)
    data.update({"maps": maps})
    return data


def get_layouts(aprx: str) -> list:
    """Get a list of layouts in the APRX and their mapframe elements.

    Args:
        aprx (str): APRX path

    Returns:
        list: List of layouts and their mapframe elements.
    """
    layouts = []
    arcpy.AddMessage("Merging map and layout metadata components")
    for lyt in aprx.listLayouts():
        for ele in lyt.listElements("MAPFRAME_ELEMENT"):
            try:
                mapName = ele.map.name
            except RuntimeError:
                mapName = None
            layouts.append(
                {
                    "layoutName": lyt.name,
                    "layoutMapFrame": ele.name,
                    "layoutMapFrameVisible": ele.visible,
                    "mapName": mapName,
                }
            )
    return layouts


def join_metadata(aprx: str, meta: dict, layouts: dict) -> list:
    """Join metadata information together into a list of dict records.

    Args:
        aprx (str): APRX path.
        meta (dict): Metadata dict returned from describe_data()
        layouts (dict): Layout dict returned from get_layouts()

    Returns:
        list: List of dictionaries containing record rows.
    """
    mapinfo = {
        "homeFolder": aprx.homeFolder,
        "filePath": aprx.filePath,
        "defaultGeodatabase": aprx.defaultGeodatabase,
        "dateSaved": aprx.dateSaved.strftime("%Y-%m-%d %H:%M:%S"),
    }
    rows = []
    for row in meta:
        inLayout = False
        for lyt in layouts:
            if row["mapName"] == lyt["mapName"]:
                rows.append(
                    {
                        **mapinfo,
                        **{key: lyt[key] for key in lyt if key != "mapName"},
                        **row,
                    }
                )
                inLayout = True
        if not inLayout:
            rows.append({**mapinfo, **row})
    return rows


def write_output(output_dir, rows: list, cols: list, aprx_path: str) -> str:
    """Export data to CSV file.

    Args:
        output_dir: Output directory.
        rows (list): Data rows.
        cols (list): Column headers.
        aprx_path (str): APRX file path.

    Returns:
        str: Output file created.
    """
    arcpy.AddMessage("Generating output")
    cols.extend(["Script_User", "Script_Run_Time"])
    for row in rows:
        row.update({"Script_User": USER, "Script_Run_Time": RUN_TIME})

    aprxName = os.path.splitext(os.path.basename(aprx_path))[0]
    if output_dir is None or output_dir == "":
        output_path = os.path.join(os.path.dirname(aprx_path), f"{aprxName}.csv")
    else:
        output_path = os.path.join(output_dir, f"{aprxName}.csv")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception as e:
            arcpy.AddError(e)
            raise
    try:
        with open(output_path, "w", newline="") as f:
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
        raise
    return output_path


def main(aprx, output_dir):
    """Main function"""
    aprx_path = aprx.filePath
    arcpy.AddMessage(
        f"Started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')}"
    )
    arcpy.AddMessage(f"APRX: {aprx_path}")
    meta = describe_data(aprx)
    meta = flatten_dict(meta)
    layouts = get_layouts(aprx)
    rows = join_metadata(aprx, meta, layouts)
    cols = dict_keys(rows)
    output_path = write_output(output_dir, rows, cols, aprx_path)
    arcpy.AddMessage(f"Output created: {output_path}")
    arcpy.AddMessage(
        f"Completed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')}"
    )


if __name__ == "__main__":
    output_dir = arcpy.GetParameterAsText(0)
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except Exception:
        raise
    main(aprx, output_dir)
