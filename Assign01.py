#-------------------------------------------------------------------------------
# Name:        Assignment01
# Purpose:     Automating the intersection of cycle networks and townships for further
#              spatial analysis
#
# Author:      Clayton Chan
#
# Created:     19/01/2026
# Copyright:   (c) 985828 2026
# Licence:
#-------------------------------------------------------------------------------


#import the arcpy module
import arcpy
import os
#set overwrite output to equal true, default is false
arcpy.env.overwriteOutput = True

#set current workspace
##workspace = r"C:\Users\985828\Documents\cchan\Sem2\GEOS456\Assignments\Assignment01_Data"
workspace = r"D:\ArcTemp\Assignments\GEOS456_Assign01_Chan\Assignment01_Data"
##workspace = r"C:\GEOS456\Assign01"

#Present feature classes are listed with relevant folders
#shapefiles are then projected and output in the gdb

walk = arcpy.da.Walk(workspace)
gdb = "Toulouse.gdb"
gdb_env = os.path.join(workspace, gdb)

for dirpath, dirnames, filenames in walk:
    for dir in dirnames:
        print(f"Feature classes in {dir}:")
        arcpy.env.workspace = os.path.join(dirpath, dir)
        for file in arcpy.ListFeatureClasses():

            exportFC, ext = os.path.splitext(file)
            if bool(ext) == True:
                print(file)
                output = os.path.join(gdb_env, exportFC)
                sr = arcpy.SpatialReference(27563)
                arcpy.management.Project(exportFC, output, sr)
            else:
                print("----------------------------")
                break


arcpy.env.workspace = gdb_env
gdbFC = arcpy.ListFeatureClasses()

#gdb feature classes are now listed
print("Exported feature classes in Tolouse.gdb:")
for FC in gdbFC:
    print(FC)
    #arcpy.Delete_management(FC)

#intersect cycling networks to Toulouse Townships
township = "communes"
cycle = arcpy.ListFeatureClasses("", "Line")

for network in cycle:
    if "_township" in network:
        pass
    else:
        arcpy.analysis.Intersect([network, township], network + "_township")


#listing through intersected feature classes

cycleNetList = arcpy.ListFeatureClasses("*_township")


#Intersected networks are listed
print("Intersected feature classes:")
for cycleNet in cycleNetList:
    print(cycleNet)

    #variables for the new field creation and geometry calculation for each network
    calcField = cycleNet[:3] + "_"
    newField = calcField + "Length_km"
    statsField = [[newField, "SUM"]]
    caseField = "libelle"

    #new field created for geometry calculation
    arcpy.management.AddField(cycleNet, newField, "FLOAT")
    #calculate length in km
    arcpy.management.CalculateGeometryAttributes(cycleNet, [[newField, "LENGTH"]], "KILOMETERS")
    #summary table created for each network within each township
    arcpy.analysis.Statistics(cycleNet, cycleNet + "_sum", statsField, caseField)
    #join table fields to commune feature class
    arcpy.management.JoinField(township, caseField, cycleNet + "_sum", caseField)


#List summary tables
print("Summary tables:")
tblList = arcpy.ListTables()
for tbl in tblList:
    print(tbl)



