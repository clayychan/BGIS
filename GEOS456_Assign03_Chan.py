#-------------------------------------------------------------------------------
# Name:        Assignment03
# Purpose:     Geology and watershed management through raster analysis
#
# Author:      Clayton Chan
#
# Created:     11/03/2026
# Copyright:   (c) SAIT
#-------------------------------------------------------------------------------

import arcpy
from arcpy import env #OPTIONAL
from arcpy.sa import *

# workspace = r"C:\Users\985828\Documents\cchan\GEOS456\Assignments\Assignment03\Assignment03_Data\Spatial_Decisions.gdb"
workspace = r"C:\GEOS456\Assign03\Spatial_Decisions.gdb"
env.workspace = workspace
env.overwriteOutput = True

# check out extension for spatial tasks
arcpy.CheckOutExtension("Spatial")

#Function for calling geoprocesssing messages
def messages():
    print(arcpy.GetMessage(0))
    count = arcpy.GetMessageCount()
    print(arcpy.GetMessage(count -1))
    print("")

# Describing dem properties
print("Rasters in workspace:")
for raster in arcpy.ListRasters():
    print(raster)
    if raster == "dem":
        desc = arcpy.Describe(raster)
        print("Format:", desc.format)
        print("Cell Size:", desc.meanCellWidth)
        print("Coordinate System:", desc.spatialReference.name)
        slope = Slope(raster, "DEGREE")
        slope.save("slope")
        messages()
        print(f"Slope generated from {raster}")
    print("")

# Raster Criteria
dem = arcpy.Raster("dem")
slope = arcpy.Raster("slope")
geo = arcpy.Raster("geolgrid")

print("Calculating criteria...")
dem_criteria = (dem >= 1000) & (dem <= 1550)
dem_criteria.save("criteria_dem")

slope_criteria = (slope <= 18)
slope_criteria.save("criteria_slope")

geo_criteria = (geo == 7)
geo_criteria.save = ("criteria_geo")

# Combining rasters
final_raster = dem_criteria * slope_criteria * geo_criteria
final_raster.save("geology")

print("Final criteria calculated.")

# Final raster statistics table creation and cursor
stats = ZonalStatisticsAsTable(final_raster, "VALUE", dem, "final_table", "#", "MEAN")
messages()
fields = ["VALUE", "COUNT", "AREA", "MEAN"]

with arcpy.da.SearchCursor(stats, fields) as cursor:
    for row in cursor:
        if row[0] == 1:
            print("Met criteria statistics:")
            print(f"Number of cells:", row[1])
            print(f"Area in square metres", row[2])
            print("Average elevation:", row[3])
            print("")

#determine average slope in the watersheds

ws = "wshds2c"  #watershed feature class
ws_selection = arcpy.management.SelectLayerByAttribute(ws, "NEW_SELECTION", "WSHDS2C_ID IN(291, 313, 525)")

ws_stats = ZonalStatisticsAsTable(ws_selection, "WSHDS2C_ID", slope, "ws_slope", "#", "MEAN")
messages()
fields = ["WSHDS2C_ID", "MEAN"]

with arcpy.da.SearchCursor(ws_stats, fields) as cursor:
    for row in cursor:
        print(f"Watershed ID:", row[0]) 
        print(f"Average slope:", row[1])

arcpy.CheckInExtension("Spatial")