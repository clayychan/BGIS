#---------------------------------------------------------------------------------------
# Name:        Assignment 2
# Purpose:     Automate data conversion and manipulation of base features.
#              Base features are based on the NTS map sheet, but must be fit into an ATS
#              study area.
#              Involves projecting, merging, and clipping of feature classes.
#
# Author:      Clayton Chan
#
# Created:     03-02-2026
# Copyright:
# Licence:
#---------------------------------------------------------------------------------------

#import the arcpy module
import arcpy
import os
#set overwrite output to equal true, default is false
arcpy.env.overwriteOutput = True

#set current workspace
##workspace = r"C:\Users\985828\Documents\cchan\GEOS456\Assignments\Assignment02"
##workspace = r"E:\SAIT\cchan\Sem2\GEOS456\Assignments\Assignment2"
workspace = r"C:\GEOS456\Assign02"
arcpy.env.workspace = workspace

#variables
walk = arcpy.da.Walk(workspace)
#Geodatabase name
gdb = "Assignment02.gdb"
#for setting projections
wkid = 26912
sr = arcpy.SpatialReference(wkid)

#Function for calling geoprocesssing messages
def messages():
    print(arcpy.GetMessage(0))
    count = arcpy.GetMessageCount()
    print(arcpy.GetMessage(count -1))

#checking if gdb exists, and deleting if it does
if arcpy.Exists(gdb):
    print(f"{gdb} already exists")
    print(f"Deleting {gdb}...")
    arcpy.management.Delete(gdb)
    print(f"{gdb} deleted.")
else:
    print(f"{gdb} does not exist...")

arcpy.management.CreateFileGDB(workspace, gdb)
print(f"{gdb} created.")
gdb_path = os.path.join(workspace, gdb)
#for recalling
dls = "DLS"
base = "Base"
#feature datasets are created
arcpy.management.CreateFeatureDataset(gdb_path, dls, sr)
arcpy.management.CreateFeatureDataset(gdb_path, base, sr)

#set paths for shapefiles to be projected into feature datasets
dls_dataset = os.path.join(gdb_path, dls)
base_dataset = os.path.join(gdb_path, base)

#Determine output GPS and Study Area path
out_gps = os.path.join(dls_dataset, "GPS_Point")
study_area = os.path.join(dls_dataset, "Study_Area")

#list through feature classes in workspaceand its properties
for dirpath, dirnames, filenames in walk:
    for dir in dirnames:
        print("---------------------------------------")
        print(f"Feature classes in {dir}:")
        arcpy.env.workspace = os.path.join(dirpath, dir)
        for file in arcpy.ListFeatureClasses():
            exportFC, ext = os.path.splitext(file)
            if bool(ext):
                print("Feature Class Name:", file)
                fcDesc = arcpy.Describe(file)
                print("Data Type:", fcDesc.dataType)
                print("Geometry:", fcDesc.shapeType)
                sRef = fcDesc.SpatialReference
                print("Spatial Reference Type:", sRef.type)
                if sRef.type != "Unknown":
                    print("Spatial Reference Name:", sRef.name)
                #Exporting GPS point and determining study area
                match fcDesc.shapeType:
                    case "Point":
                        arcpy.conversion.ExportFeatures(file, out_gps)
                        print("Exporting GPS Point...")
                        messages()
                    case "Polygon":
                        if "TWP" in file:
                            twp_layer = arcpy.management.MakeFeatureLayer(file, "twp")
                            arcpy.management.SelectLayerByLocation(twp_layer, "", out_gps)
                            print("Identifying Study Area...")
                            messages()
                            arcpy.management.Project(twp_layer, study_area, sr)
                            print("Projecting...")
                            messages()
                print("")
    print("---------------------------------------")

#creating lists to determine which features are merged together
contours = []
trails = []
pipelines = []
powerlines = []
roads = []

#walking through the rest of the shapefiles to be projected and clipped
for dirpath, dirnames, filenames in arcpy.da.Walk(workspace):
    for dir in dirnames:
        arcpy.env.workspace = os.path.join(dirpath, dir)
        for file in arcpy.ListFeatureClasses():
            exportFC, ext = os.path.splitext(file)
            if bool(ext):   #prevents gdb feature classes to be processed
                if "DLS" in dir:
                    if "RA" in file:    #road allowance not to be included in gdb
                        print("")
                    elif "TWP" in file: #Township has already been processed
                        print("")
                    else:
                        #determining name of feature class
                        layer, ext = os.path.splitext(file)
                        dls_layer = arcpy.management.MakeFeatureLayer(file, layer[-3:])
                        final_layer = os.path.join(dls_dataset, layer[-3:])
                        prj_layer = final_layer + "_prj"
                        arcpy.management.Project(dls_layer, prj_layer, sr)
                        print(f"Projecting {layer[-3:]}...")
                        messages()
                        arcpy.analysis.Clip(prj_layer, study_area, final_layer)
                        print(f"Clipping {layer [-3:]}...")
                        messages()
                        arcpy.management.Delete(prj_layer)
                        print("")
                        print("--------------------------------------------")
                else:   #Sorting base features to be merged together
                    if "CONTOUR" in file:
                        feature = os.path.join(dirpath, dir, file)
                        contours.append(feature)

                    elif "TRAIL" in file:
                        feature = os.path.join(dirpath, dir, file)
                        trails.append(feature)

                    elif "PIPELINE" in file:
                        feature = os.path.join(dirpath, dir, file)
                        pipelines.append(feature)

                    elif "POWERLINE" in file:
                        feature = os.path.join(dirpath, dir, file)
                        powerlines.append(feature)

                    elif "ROAD" in file:
                        feature = os.path.join(dirpath, dir, file)
                        roads.append(feature)

#defined function for merging, projecting, and clipping base features
def merge(features, name):
    intermediate = os.path.join(gdb_path, name)
    fcMerge = intermediate + "_merge"
    print(f"Merging {name}...")
    arcpy.management.Merge(features, fcMerge)
    messages()
    wkid2 = 3401
    define = arcpy.SpatialReference(wkid2)
    arcpy.management.DefineProjection(fcMerge, define)
    messages()
    prj = intermediate + "_prj"
    print(f"Projecting {name}...")
    arcpy.management.Project(fcMerge, prj, sr)
    messages()
    destination = os.path.join(base_dataset, name)
    print(f"Clipping {name}...")
    arcpy.analysis.Clip(prj, study_area, destination)
    messages()
    print("Deleting intermediate files...")
    arcpy.management.Delete(prj)
    arcpy.management.Delete(fcMerge)
    print("")

merge(contours, "Contours")
merge(trails, "Trails")
merge(pipelines, "Pipelines")
merge(powerlines, "Powerlines")
merge(roads, "Roads")

#listing final feature classes
arcpy.env.workspace = gdb_path
datasets = arcpy.ListDatasets()

for ds in datasets:
    print(f"Final features in {ds} dataset:")
    print("--------------------------------------")
    arcpy.env.workspace = os.path.join(gdb_path, ds)
    finalList = arcpy.ListFeatureClasses()
    for file in finalList:
        print("Feature Class Name:", file)
        fcDesc = arcpy.Describe(file)
        sRef = fcDesc.SpatialReference
        print("Spatial Reference Type:", sRef.type)
        print("Spatial Reference Name:", sRef.name)
        print("")
    print("--------------------------------------")

#Identifying full DLS description of GPS point
lsd = os.path.join(dls_dataset, "LSD")
lsd_layer = arcpy.management.MakeFeatureLayer(lsd, "study_lsd")
study_dls = arcpy.management.SelectLayerByLocation(lsd_layer, "", out_gps)

dls = arcpy.da.SearchCursor(study_dls, ["MER", "RGE", "TWP", "SEC","QTR", "LSD"])
for row in dls:
    print(f"GPS point DLS description: LSD{row[5]} - {row[4]}{row[3]} - TWP{row[2]} - RGE{row[1]} - W{row[0]}")