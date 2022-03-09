# PURPOSE
#   Export all MXD files in a directory to PDF.
#
# AUTHOR(S)
#   Caleb Grant (CG)
#
# NOTES
#   1) This script takes 2 arguments:
#       - MXD directory
#       - Output PDF directory
#
# HISTORY
#   1) Created 2020-07-28. CG.
# =========================================================================

import os
import sys

# Check if ArcGIS License can be utilized for ArcPy
# This shouldnt be an issue since the user will already have ArcMap open
try:
    import arcpy
except RuntimeError as e:
    print("RuntimeError:", e)
    sys.exit()

# Retrieve input parameters (MXD directory, Output directory)
working_dir = arcpy.GetParameterAsText(0)  # input workspace
arcpy.env.workspace = working_dir
output_dir = arcpy.GetParameterAsText(1)  # output PDF location

arcpy.AddMessage("\nWorking MXD Directory: {}".format(working_dir))
arcpy.AddMessage("\nOutput PDF Directory: {}".format(output_dir))

# Get list of MXDs in a directory
mxd_list = arcpy.ListFiles("*.mxd")
# Count number of MXDs in directory
mxd_count = len(mxd_list)
arcpy.AddMessage("\nTotal MXDs to export: {}\n".format(mxd_count))

# Iterate through each MXD in directory
index = 1
for mxd in mxd_list:
    # Retrieve map name without extension
    map_name = mxd.split(".")[0]

    # Pretty format for script messages...
    if mxd_count < 10:
        arcpy.AddMessage("({}/{}) Exporting: {}".format(index, mxd_count, map_name))
    elif mxd_count >= 10 and mxd_count < 100:
        if index < 10:
            arcpy.AddMessage(
                " ({}/{}) Exporting: {}".format(index, mxd_count, map_name)
            )
        else:
            arcpy.AddMessage("({}/{}) Exporting: {}".format(index, mxd_count, map_name))
    else:
        if index < 10:
            arcpy.AddMessage(
                "  ({}/{}) Exporting: {}".format(index, mxd_count, map_name)
            )
        elif index >= 10 and mxd_count < 100:
            arcpy.AddMessage(
                " ({}/{}) Exporting: {}".format(index, mxd_count, map_name)
            )
        else:
            arcpy.AddMessage("({}/{}) Exporting: {}".format(index, mxd_count, map_name))

    # Use map name as output PDF name
    pdf_name = map_name + ".pdf"
    pdf_loc = os.path.join(output_dir, pdf_name)

    # Check if PDF already exists. If so, delete it.
    if os.path.exists(pdf_loc):
        arcpy.AddWarning("    PDF already exists: {}".format(pdf_name))
        arcpy.AddWarning("    Deleting existing PDF.")
        try:
            os.remove(pdf_loc)
        except:
            arcpy.AddError("    PDF could not be deleted. Skipping.")
            index += 1
            continue

    # Load map document
    cur_mxd = arcpy.mapping.MapDocument(os.path.join(working_dir, mxd))
    # Try to export map document to PDF
    try:
        arcpy.mapping.ExportToPDF(
            cur_mxd, pdf_loc, image_quality="BETTER", picture_symbol="VECTORIZE_BITMAP"
        )
    except:
        arcpy.AddError("    Could not export to PDF.")
        index += 1
        continue
    index += 1

arcpy.AddMessage("\n")
