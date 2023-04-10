import os
from datetime import datetime

# Check if ArcGIS License can be utilized for ArcPy
# This shouldnt be an issue since the user will already have ArcGIS Pro open.
try:
    import arcpy
    from arcpy import metadata as md
except RuntimeError as e:
    raise


def import_csv(
    in_csv: str,
    x_field: str,
    y_field: str,
    coordinate_system: str,
    output_fc: str,
    fc_title: str,
    fc_summary: str,
) -> None:
    SOURCE_FIELD = "gis_source"
    # Check that a default workspace exists.
    if not arcpy.Exists(arcpy.env.workspace):
        arcpy.AddError(
            "No workspace found for the current project. Try setting a default geodatabase for the project before continuing."
        )
    # Check that input file is CSV.
    if os.path.splitext(in_csv)[-1].lower() != ".csv":
        arcpy.AddError(
            f"Input file is not in CSV format ({os.path.splitext(in_csv)[-1]})."
        )
    # Import CSV to Feature Class
    arcpy.AddMessage(f"Importing: {in_csv}")
    arcpy.AddMessage(
        f"Creating Feature Class: {os.path.join(arcpy.env.workspace, output_fc)}."
    )
    arcpy.management.XYTableToPoint(
        in_table=in_csv,
        out_feature_class=output_fc,
        x_field=x_field,
        y_field=y_field,
        coordinate_system=coordinate_system,
    )
    # Add a SOURCE_FIELD field. If one already exists, add underscores to the beginning
    # and end of the SOURCE_FIELD name to make it unique.
    fields = [field.name for field in arcpy.ListFields(output_fc)]
    while True:
        if SOURCE_FIELD in fields:
            SOURCE_FIELD = f"_{SOURCE_FIELD}_"
        else:
            break
    arcpy.AddMessage(f"Adding column {SOURCE_FIELD} to store original source path.")
    arcpy.management.AddField(output_fc, SOURCE_FIELD, "TEXT", field_length=255)
    # Update the SOURCE_FIELD field with the file name and path
    with arcpy.da.UpdateCursor(output_fc, SOURCE_FIELD) as cursor:
        for row in cursor:
            row[0] = in_csv
            cursor.updateRow(row)
    # Add feature metadata
    arcpy.AddMessage("Adding feature metadata.")
    meta = md.Metadata()
    meta.title = fc_title
    arcpy.AddMessage(f"  Title: {fc_title}")
    meta.summary = fc_summary
    arcpy.AddMessage(f"  Summary: {fc_summary}")
    meta.description = f"""Data set {in_csv} was imported to {os.path.join(arcpy.env.workspace, output_fc)}. Script user: {os.getlogin()}. Created: {datetime.now().isoformat(sep=' ', timespec='seconds')}. The column {SOURCE_FIELD} was created in the data set with a value indicating the network path and file name of the source data."""
    target = md.Metadata(output_fc)
    if not target.isReadOnly:
        target.copy(meta)
        target.save()


if __name__ == "__main__":
    in_csv = arcpy.GetParameterAsText(0)
    x_field = arcpy.GetParameterAsText(1)
    y_field = arcpy.GetParameterAsText(2)
    coordinate_system = arcpy.GetParameterAsText(3)
    output_fc = arcpy.GetParameterAsText(4)
    fc_title = arcpy.GetParameterAsText(5)
    fc_summary = arcpy.GetParameterAsText(6)
    try:
        import_csv(
            in_csv,
            x_field,
            y_field,
            coordinate_system,
            output_fc,
            fc_title,
            fc_summary,
        )
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages())
