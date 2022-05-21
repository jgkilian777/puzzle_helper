from __future__ import division
import numpy as np
import cv2
import itertools
import copy
from matplotlib.path import Path
from colormath.color_objects import LabColor
from colormath.color_diff import delta_e_cie2000
from colormath.color_diff import delta_e_cmc
import math
from defects import myConvexHull
import time
import sys
import concurrent.futures
from customicp import getAvgDistClosestPointsFromOtherToMain, getCorrespondencesPlaneToPlane, transformCustPlaneToPlane, getCorrespondencesPlaneToPlaneInefficient, inefficientCorrespondenceAreas, planeToPlaneICP, planeToPlaneICPTwoAtOnce



def angleCalc(c1, c2, ydim):
	tempc1 = list(c1)
	tempc2 = list(c2)
	tempc1[1] = ycoords(tempc1[1], ydim)
	tempc2[1] = ycoords(tempc2[1], ydim)
	p1 = (0, 1)
	tempc2[0] = tempc2[0] - tempc1[0]
	tempc2[1] = tempc2[1] - tempc1[1]
	ang1 = np.arctan2(*p1[::-1])
	ang2 = np.arctan2(*tempc2[::-1])
	return np.rad2deg((ang1 - ang2) % (2 * np.pi))
	

def ycoords(ycoord, ydim):
	return ydim-ycoord

	
def crange(start, end, modulo):
	if start > end:
		while start < modulo:
			yield start
			start += 1
		start = 0

	while start < end:
		yield start
		start += 1

def distPointToLine(point, a, b, c, d):
	x0 = point[0]
	y0 = point[1]
	return abs(a*x0 - b*y0 + c)/d



def lessOrGreat(first, second, contourSize, segStart, segEnd):
	lessOrGreat = 0
	if segStart < segEnd:
		if first < second:
			lessOrGreat = -1
		elif first > second:
			lessOrGreat = 1
	elif segStart > segEnd: # if segment crosses contour ending e.g. starts at 400, passes through end of contour at 450 and ends at 50
		if (first >= segStart and second >= segStart) or (first <= segEnd and second <= segEnd): # both occur either before or after contour end (thus allowing normal comparison)
			if first < second:
				lessOrGreat = -1
			elif first > second:
				lessOrGreat = 1
		else:
			if first >= segStart and second <= segEnd:
				lessOrGreat = -1
			elif second >= segStart and first <= segEnd:
				lessOrGreat = 1
	return lessOrGreat



def hullEndsOnVertex(contour, hullEnding, ydim, hullEndingBeforeOrAfterDefect, debug=False):
	
	fractionOfRadiusWiggleroomAwayFromDefect = 0.75
	fractionOfRadiusWiggleroomTowardsDefect = 0.75
	
	if hullEndingBeforeOrAfterDefect == "after":
		return checkCornerOrBigChange(contour, hullEnding, hullEnding, hullEnding, ydim, [fractionOfRadiusWiggleroomTowardsDefect, fractionOfRadiusWiggleroomAwayFromDefect], debug=debug)
	elif hullEndingBeforeOrAfterDefect == "before":
		return checkCornerOrBigChange(contour, hullEnding, hullEnding, hullEnding, ydim, [fractionOfRadiusWiggleroomAwayFromDefect, fractionOfRadiusWiggleroomTowardsDefect], debug=debug)
	else:
		print("hullendsonvertex error")
		exit()
	
	

def checkCornerOrBigChange(contour, hullMin, hullMax, defectInd, ydim, hullEndsOnVertex=None, debug=False, closeCornersMethod=False, hullMinFlat=False, hullMaxFlat=False, defectIndFlat=False):
	
	
	hullMinOG = hullMin
	hullMaxOG = hullMax
	defectIndOG = defectInd
	ydimOG = ydim
	hullEndsOnVertexOG = hullEndsOnVertex
	debugOG = debug
	closeCornersMethodOG = closeCornersMethod
	hullMinFlatOG = hullMinFlat
	hullMaxFlatOG = hullMaxFlat
	defectIndFlatOG = defectIndFlat
	
	
	
	
	
	if hullEndsOnVertex is None:
		hullEndsOnVertex=[]
	
	minBigChange = 50
	minAngleForCorner = 40
	breakAfterMinBigChange = False
	radius = 10
	radiusJustForCheckingEndsOnVertex = 6
	padding = 7
	holeInMiddle = 0
	cornerInd = defectInd
	
	contourSize = contour.shape[0]
	
	angleTracker = 0
	previousAngle = False
	
	vertexBefore = False
	vertexAfter = False
	
	pointOfMaxAngleChange = []
	
	
	if len(hullEndsOnVertex) == 2:
		radius = radiusJustForCheckingEndsOnVertex
		holeInMiddle = 0
		hullMin = (defectInd-radius-round(hullEndsOnVertex[0]*radius))%contour.shape[0]
		hullMax = (defectInd+radius+1+round(hullEndsOnVertex[1]*radius))%contour.shape[0]
		
		defectInd = hullMin
		
	else:
		if (hullMax-hullMin)%contourSize > 2*padding and (hullMax-defectInd)%contourSize > padding and (defectInd-hullMin)%contourSize > padding:
			if not(hullMinFlat):
				hullMin = (hullMin+padding)%contourSize
			if not(hullMaxFlat):
				hullMax = (hullMax-padding)%contourSize
	
	if debug:
		print("hullMin hullMin hullMin hullMin hullMin hullMin ")
		print(hullMin)
		print(contour[hullMin])
		print("hullMax hullMax hullMax hullMax hullMax hullMax ")
		print(hullMax)
		print(contour[hullMax])
	
	defectInd = int(defectInd)
	
	starterAngle = angleCalc(contour[defectInd][0], contour[(defectInd+3)%contourSize][0], ydim)
	start=None
	end=None
	if (hullMax-defectInd)%contour.shape[0] < radius*2+2 and len(hullEndsOnVertex)==0 and closeCornersMethod: # Defect is too close to hull end
		mid = None
		if defectInd<=hullMax:
			mid=int(round((defectInd+hullMax)/2))
		else:
			mid = int(round((defectInd+hullMax+contour.shape[0])/2))%contour.shape[0]
		start = (mid-radius)%contour.shape[0]
		end = (mid+radius)%contour.shape[0]
	elif (hullMax-defectInd)%contour.shape[0] < radius*2+2:
		pass
	else:
		if defectIndFlat:
			start = (defectInd+1)%contour.shape[0]
		else:
			start = (defectInd+radius)%contour.shape[0]
		if hullMaxFlat:
			end = (hullMax-1)%contour.shape[0]
		else:
			end = (hullMax-radius)%contour.shape[0]
	if start is not None:
		if debug:
			print('start and end')
			print(start)
			print(end)
			print(contour[start])
			print(contour[end])
		for i in crange(start, end, contour.shape[0]):
			angleBeforePoint = angleCalc(contour[(i-radius)%contourSize][0], contour[(i-holeInMiddle)%contourSize][0], ydim)
			angleAfterPoint = angleCalc(contour[(i+holeInMiddle)%contourSize][0], contour[(i+radius)%contourSize][0], ydim)
			
			if i==end:
				print('just checking, this shouldnt be true ever')
				exit()
			
			if previousAngle == False:
				previousAngle = angleBeforePoint
			else:
				if previousAngle > 270 and angleBeforePoint < 90:
					angleTracker+=angleBeforePoint+360-previousAngle
				elif angleBeforePoint > 270 and previousAngle < 90:
					angleTracker-=360-angleBeforePoint + previousAngle
				else:
					angleTracker+=angleBeforePoint-previousAngle
				
				previousAngle = angleBeforePoint
			
			if angleTracker >= minBigChange:
				vertexAfter = True
				# if debug == True:
					# print(111)
					# print(i)
					# print(contour[i])
					# print(angleTracker)
					# print("minang AFTER")
					# print(angleBeforePoint)
					# print(angleAfterPoint)
				if breakAfterMinBigChange == True:
					break
			
			if i == ((end-1)%contour.shape[0]):
				if previousAngle > 270 and angleAfterPoint < 90:
					angleTracker+=angleAfterPoint+360-previousAngle
				elif angleAfterPoint > 270 and previousAngle < 90:
					angleTracker-=360-angleAfterPoint + previousAngle
				else:
					angleTracker+=angleAfterPoint-previousAngle
				if angleTracker >= minBigChange:
					vertexAfter = True
					# if debug == True:
						# print(222)
						# print(i)
						# print(contour[i])
						# print(angleTracker)
						# print("minang AFTER")
						# print(angleBeforePoint)
						# print(angleAfterPoint)
			
			tempCornerChecker = 0
			
			if angleAfterPoint > 270 and angleBeforePoint < 90:
				tempCornerChecker=abs(angleBeforePoint+360-angleAfterPoint)
			elif angleBeforePoint > 270 and angleAfterPoint < 90:
				tempCornerChecker=abs(360-angleBeforePoint + angleAfterPoint)
			else:
				tempCornerChecker=abs(angleBeforePoint-angleAfterPoint)
			if tempCornerChecker >= minAngleForCorner:
				vertexAfter = True
				if breakAfterMinBigChange == True:
					if len(pointOfMaxAngleChange) == 0:
						pointOfMaxAngleChange = [i,tempCornerChecker]
					elif pointOfMaxAngleChange[1] < tempCornerChecker:
						pointOfMaxAngleChange = [i,tempCornerChecker]
					break
				else:
					if len(pointOfMaxAngleChange) == 0:
						pointOfMaxAngleChange = [i,tempCornerChecker]
						if debug == True:
							print("pointOfMaxAngleChange")
							print(pointOfMaxAngleChange)
					elif pointOfMaxAngleChange[1] <= tempCornerChecker:
						pointOfMaxAngleChange = [i,tempCornerChecker]
						if debug == True:
							print("pointOfMaxAngleChange")
							print(pointOfMaxAngleChange)
					
	if len(hullEndsOnVertex) == 2:
		if len(pointOfMaxAngleChange)>0 and (pointOfMaxAngleChange[0]==(end-1)%contour.shape[0] or pointOfMaxAngleChange[0]==start): # max angle change is at the end of test zone, do this whole thing again
			# except this time with increased end incase the corner is just out of range if the current start->end range
			newHullMax = (hullMaxOG+radius)%contour.shape[0] # dont need this but keeping in case i ever copy this for when len(hullEndsOnVertex)==0
			if pointOfMaxAngleChange[0]==(end-1)%contour.shape[0]:
				hullEndsOnVertexOG[1] = (hullEndsOnVertexOG[1]+1)
			elif pointOfMaxAngleChange[0]==start:
				hullEndsOnVertexOG[0] = (hullEndsOnVertexOG[0]+1) # this is a ratio of radius, so adding 1 adds 1*radius to start/end
			
			if debug:
				print(pointOfMaxAngleChange)
				if len(pointOfMaxAngleChange)>0:
					print(contour[pointOfMaxAngleChange[0]])
				print('d3ohui3i32222')
				input(contour[0])
			
			return checkCornerOrBigChange(contour, hullMinOG, newHullMax, defectIndOG, ydimOG, hullEndsOnVertexOG, debugOG, closeCornersMethodOG, hullMinFlatOG, hullMaxFlatOG, defectIndFlatOG)
			
		if debug:
			print(pointOfMaxAngleChange)
			if len(pointOfMaxAngleChange)>0:
				print(contour[pointOfMaxAngleChange[0]])
			print('d3ohui3i3')
			input(contour[0])
		
		return pointOfMaxAngleChange
	
	angleTracker = 0
	previousAngle = False
	
	start=None
	end=None
	if (defectInd-hullMin)%contour.shape[0] < radius*2+2 and len(hullEndsOnVertex)==0 and closeCornersMethod: # Defect is too close to hull beginning
		mid = None
		if hullMin<=defectInd:
			mid=int(round((hullMin+defectInd)/2))
		else:
			mid = int(round((hullMin+defectInd+contour.shape[0])/2))%contour.shape[0]
		start = (mid-radius)%contour.shape[0]
		end = (mid+radius)%contour.shape[0]
	
	elif (defectInd-hullMin)%contour.shape[0] < radius*2+2:
		pass
	else:
		if hullMinFlat:
			start = (hullMin+1)%contour.shape[0]
		else:
			start = (hullMin+radius)%contour.shape[0]
		if defectIndFlat:
			end = (defectInd-1)%contour.shape[0]
		else:
			end = (defectInd-radius)%contour.shape[0]
	if debug==True:
		print(start)
		print(end)
		print("fu5otij52")
	if start is not None:
		for i in crange(start, end, contour.shape[0]):
			angleBeforePoint = angleCalc(contour[(i-radius)%contourSize][0], contour[(i-1)%contourSize][0], ydim)
			angleAfterPoint = angleCalc(contour[(i+1)%contourSize][0], contour[(i+radius)%contourSize][0], ydim)
			
			if previousAngle == False:
				previousAngle = angleBeforePoint
			else:
				if previousAngle > 270 and angleBeforePoint < 90:
					angleTracker+=angleBeforePoint+360-previousAngle
				elif angleBeforePoint > 270 and previousAngle < 90:
					angleTracker-=360-angleBeforePoint + previousAngle
				else:
					angleTracker+=angleBeforePoint-previousAngle
				
				previousAngle = angleBeforePoint
			
			if angleTracker >= minBigChange:
				vertexBefore = True
				# if debug == True:
					# print(444)
					# print(i)
					# print(contour[i])
					# print(angleTracker)
					# print("minbigch BEFORE")
					# print(angleBeforePoint)
					# print(angleAfterPoint)
				break
			
			if i == ((end-1)%contour.shape[0]):
				if previousAngle > 270 and angleAfterPoint < 90:
					angleTracker+=angleAfterPoint+360-previousAngle
				elif angleAfterPoint > 270 and previousAngle < 90:
					angleTracker-=360-angleAfterPoint + previousAngle
				else:
					angleTracker+=angleAfterPoint-previousAngle
				if angleTracker >= minBigChange:
					vertexBefore = True
					# if debug == True:
						# print(555)
						# print(i)
						# print(contour[i])
						# print(angleTracker)
						# print("minbigch2 BEFORE")
						# print(angleBeforePoint)
						# print(angleAfterPoint)
			tempCornerChecker = 0
			
			if angleAfterPoint > 270 and angleBeforePoint < 90:
				tempCornerChecker=abs(angleBeforePoint+360-angleAfterPoint)
			elif angleBeforePoint > 270 and angleAfterPoint < 90:
				tempCornerChecker=abs(360-angleBeforePoint + angleAfterPoint)
			else:
				tempCornerChecker=abs(angleBeforePoint-angleAfterPoint)
			
			if tempCornerChecker >= minAngleForCorner:
				vertexBefore = True
				break
		
		
		if debug == True:
			print([vertexBefore, vertexAfter, pointOfMaxAngleChange])
			print("hullMin hullMin hullMin hullMin hullMin hullMin ")
			print(hullMin)
			print("hullMax hullMax hullMax hullMax hullMax hullMax ")
			print(hullMax)
			print("f3uh2<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
	if len(pointOfMaxAngleChange) == 0:
		return [vertexBefore, vertexAfter, [-1]]
	else:
		return [vertexBefore, vertexAfter, pointOfMaxAngleChange]



def finalCornersMegaFunction(dSize, potentialSize, contour, defects1, tempPotentialOuties, ydim, storeChecked, defectDicts, debug2=True, actualdebug=False):
	
	# hullEndingsAreJoinedIfWithin = 6
	hullEndingsAreJoinedIfWithin = 2
	
	finalCorners = []
	
	if dSize == 4:
		
		tempCorners = {}
		for i in range(dSize):
			tempCorner = []
			
			beforeTempCorner = hullEndsOnVertex(contour, defects1[(i)%dSize][3], ydim, "after")
			afterTempCorner = hullEndsOnVertex(contour, defects1[(i+1)%dSize][2], ydim, "before")
			
			if len(beforeTempCorner) != 0 and len(afterTempCorner) != 0 and abs(beforeTempCorner[0] - afterTempCorner[0]) < hullEndingsAreJoinedIfWithin:
				tempCorner = [beforeTempCorner[0]]
			elif len(beforeTempCorner) != 0 and len(afterTempCorner) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeTempCorner[0], afterTempCorner[0], beforeTempCorner[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					tempCorner = [tempCheckCorner[2][0]]
				else:
					
					# NEW
					# ambiguous, but prioritise the 'corner'(big angle change) who's closest defect is the furthest away
					IndicesToClosestDefectBeforeTempCorner = None
					IndicesToClosestDefectAfterTempCorner = None
					defect1 = defects1[(i)%dSize][0]
					defect2 = defects1[(i+1)%dSize][0]
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-beforeTempCorner[0]), (defect1-beforeTempCorner[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-beforeTempCorner[0]), (defect2-beforeTempCorner[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectBeforeTempCorner=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectBeforeTempCorner=tmpIndicesToDefect2
					
					
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-afterTempCorner[0]), (defect1-afterTempCorner[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-afterTempCorner[0]), (defect2-afterTempCorner[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectAfterTempCorner=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectAfterTempCorner=tmpIndicesToDefect2
					
					if IndicesToClosestDefectBeforeTempCorner>IndicesToClosestDefectAfterTempCorner:
						tempCorner = [beforeTempCorner[0], afterTempCorner[0]]
					else:
						tempCorner = [afterTempCorner[0], beforeTempCorner[0]]
					
					
			elif len(beforeTempCorner) == 0 and len(afterTempCorner) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(i)%dSize][3], afterTempCorner[0], defects1[(i)%dSize][3], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					tempCorner = [tempCheckCorner[2][0]]
				else:
					tempCorner = [afterTempCorner[0]]
			elif len(beforeTempCorner) != 0 and len(afterTempCorner) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeTempCorner[0], defects1[(i+1)%dSize][2], beforeTempCorner[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					tempCorner = [tempCheckCorner[2][0]]
				else:
					tempCorner = [beforeTempCorner[0]]
			elif len(beforeTempCorner) == 0 and len(afterTempCorner) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(i)%dSize][3], defects1[(i+1)%dSize][2], defects1[(i)%dSize][3], ydim, closeCornersMethod=True, hullMinFlat=True, hullMaxFlat=True, defectIndFlat=True)
				if tempCheckCorner[1] == True:
					tempCorner = [tempCheckCorner[2][0]]
				else:
					print("error code 2oikppp")
					return None
			
			tempCorners[i] = tempCorner
		for corner1 in tempCorners[0]:
			for corner2 in tempCorners[1]:
				for corner3 in tempCorners[2]:
					for corner4 in tempCorners[3]:
						if corner1 == -1 or corner2 == -1 or corner3 == -1 or corner4 == -1:
							pass
						else:
							finalCorners.append([[], [corner1, corner2, corner3, corner4]])
		return finalCorners
	
	else:
		pass
	
	potentialOuties = []
	if len(tempPotentialOuties) == dSize-4: # found outie
		potentialOuties = tempPotentialOuties
		pass
	elif len(tempPotentialOuties) < dSize-4: # ???
		print(len(tempPotentialOuties))
		print("error code 83jud")
		return None
	elif len(tempPotentialOuties) >= dSize-3: # need to narrow further
		#Check if vertex appears between potential corners and next hull
		
		for i, potentialOutie in enumerate(tempPotentialOuties):
			if True:
				
				firstCornerInd = []
				secondCornerInd = []
				
				if potentialOutie[0] in defectDicts:
					firstCornerInd = defectDicts[potentialOutie[0]]["before"][0]
				else:
					print("error code 38ju")
					return None
				if potentialOutie[1] in defectDicts:
					secondCornerInd = defectDicts[potentialOutie[1]]["after"][0]
				else:
					print("error code 38ju2")
					return None
				
				hullEndingOtherSideFirstCorner = []
				hullEndingOtherSideSecondCorner = []
				
				if (potentialOutie[0]-1)%dSize in defectDicts:
					hullEndingOtherSideFirstCorner = defectDicts[(potentialOutie[0]-1)%dSize]["after"]
				else:
					hullEndingOtherSideFirstCorner = hullEndsOnVertex(contour, defects1[(potentialOutie[0]-1)%dSize][3], ydim, "after")
					defectDicts[(potentialOutie[0]-1)%dSize]["after"]=hullEndingOtherSideFirstCorner
				if (potentialOutie[1]+1)%dSize in defectDicts:
					hullEndingOtherSideSecondCorner = defectDicts[(potentialOutie[1]+1)%dSize]["before"]
				else:
					hullEndingOtherSideSecondCorner = hullEndsOnVertex(contour, defects1[(potentialOutie[1]+1)%dSize][2], ydim, "before")
					defectDicts[(potentialOutie[1]+1)%dSize]["before"]=hullEndingOtherSideSecondCorner
				
				atLeastOneVertexBefore = []
				atLeastOneVertexAfter = []
				
				if len(hullEndingOtherSideFirstCorner) != 0:
					atLeastOneVertexBefore = checkCornerOrBigChange(contour, hullEndingOtherSideFirstCorner[0], firstCornerInd, hullEndingOtherSideFirstCorner[0], ydim) # defectind is same as the starting point because we want to go from start to end to check for vertex instead of checking before and after an index like before
				else:
					atLeastOneVertexBefore = checkCornerOrBigChange(contour, defects1[(potentialOutie[0]-1)%dSize][3], firstCornerInd, defects1[(potentialOutie[0]-1)%dSize][3], ydim) # defectind is same as the starting point because we want to go from start to end to check for vertex instead of checking before and after an index like before
				
				if len(hullEndingOtherSideSecondCorner) != 0:
					atLeastOneVertexAfter = checkCornerOrBigChange(contour, secondCornerInd, hullEndingOtherSideSecondCorner[0], secondCornerInd, ydim) # ''
				else:
					atLeastOneVertexAfter = checkCornerOrBigChange(contour, secondCornerInd, defects1[(potentialOutie[1]+1)%dSize][2], secondCornerInd, ydim) # ''
				
				if atLeastOneVertexBefore[1] == False and atLeastOneVertexAfter[1] == False:
					potentialOuties.append(potentialOutie)
	
	potentialSize = len(potentialOuties)
	
	if len(potentialOuties) == dSize-4: #done
		if len(potentialOuties) == 1:
			
			corner1 = defectDicts[potentialOuties[0][0]]["before"][0]
			corner2 = defectDicts[potentialOuties[0][1]]["after"][0]
			corner3 = []
			corner4 = []
			
			beforeCorner3 = hullEndsOnVertex(contour, defects1[(potentialOuties[0][1]+1)%dSize][3], ydim, "after")
			afterCorner3 = hullEndsOnVertex(contour, defects1[(potentialOuties[0][1]+2)%dSize][2], ydim, "before")
			
			beforeCorner4 = hullEndsOnVertex(contour, defects1[(potentialOuties[0][1]+2)%dSize][3], ydim, "after")
			afterCorner4 = hullEndsOnVertex(contour, defects1[(potentialOuties[0][1]+3)%dSize][2], ydim, "before")
			
			if len(beforeCorner3) != 0 and len(afterCorner3) != 0 and abs(beforeCorner3[0] - afterCorner3[0]) < hullEndingsAreJoinedIfWithin:
				corner3 = [beforeCorner3[0]]
			elif len(beforeCorner3) != 0 and len(afterCorner3) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner3[0], afterCorner3[0], beforeCorner3[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner3 = [tempCheckCorner[2][0]]
				else:
					# NEW
					# ambiguous, but prioritise the 'corner'(big angle change) who's closest defect is the furthest away
					IndicesToClosestDefectBeforeCorner3 = None
					IndicesToClosestDefectAfterCorner3 = None
					defect1 = defects1[(potentialOuties[0][1]+1)%dSize][0]
					defect2 = defects1[(potentialOuties[0][1]+2)%dSize][0]
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-beforeCorner3[0]), (defect1-beforeCorner3[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-beforeCorner3[0]), (defect2-beforeCorner3[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectBeforeCorner3=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectBeforeCorner3=tmpIndicesToDefect2
					
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-afterCorner3[0]), (defect1-afterCorner3[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-afterCorner3[0]), (defect2-afterCorner3[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectAfterCorner3=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectAfterCorner3=tmpIndicesToDefect2
					
					if IndicesToClosestDefectBeforeCorner3>IndicesToClosestDefectAfterCorner3:
						corner3 = [beforeCorner3[0], afterCorner3[0]]
					else:
						corner3 = [afterCorner3[0], beforeCorner3[0]]
					
			elif len(beforeCorner3) == 0 and len(afterCorner3) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(potentialOuties[0][1]+1)%dSize][3], afterCorner3[0], defects1[(potentialOuties[0][1]+1)%dSize][3], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner3 = [tempCheckCorner[2][0]]
				else:
					corner3 = [afterCorner3[0]]
			elif len(beforeCorner3) != 0 and len(afterCorner3) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner3[0], defects1[(potentialOuties[0][1]+2)%dSize][2], beforeCorner3[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner3 = [tempCheckCorner[2][0]]
				else:
					corner3 = [beforeCorner3[0]]
			elif len(beforeCorner3) == 0 and len(afterCorner3) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(potentialOuties[0][1]+1)%dSize][3], defects1[(potentialOuties[0][1]+2)%dSize][2], defects1[(potentialOuties[0][1]+1)%dSize][3], ydim, closeCornersMethod=True, hullMinFlat=True, hullMaxFlat=True, defectIndFlat=True) # here defectInd==hullMin
				if tempCheckCorner[1] == True:
					corner3 = [tempCheckCorner[2][0]]
				else:
					print("error code 2oikppp")
					return None
			
			if len(beforeCorner4) != 0 and len(afterCorner4) != 0 and abs(beforeCorner4[0] - afterCorner4[0]) < hullEndingsAreJoinedIfWithin:
				corner4 = [beforeCorner4[0]]
			elif len(beforeCorner4) != 0 and len(afterCorner4) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner4[0], afterCorner4[0], beforeCorner4[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner4 = [tempCheckCorner[2][0]]
				else:
					
					# NEW
					# ambiguous, but prioritise the 'corner'(big angle change) who's closest defect is the furthest away
					IndicesToClosestDefectBeforeCorner4 = None
					IndicesToClosestDefectAfterCorner4 = None
					defect1 = defects1[(potentialOuties[0][1]+2)%dSize][0]
					defect2 = defects1[(potentialOuties[0][1]+3)%dSize][0]
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-beforeCorner4[0]), (defect1-beforeCorner4[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-beforeCorner4[0]), (defect2-beforeCorner4[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectBeforeCorner4=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectBeforeCorner4=tmpIndicesToDefect2
					
					tmpIndicesToDefect1=None
					tmpIndicesToDefect2=None
					tmpIndicesToDefect1 = min(abs(defect1-afterCorner4[0]), (defect1-afterCorner4[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
					tmpIndicesToDefect2 = min(abs(defect2-afterCorner4[0]), (defect2-afterCorner4[0])%contour.shape[0])
					if tmpIndicesToDefect1<tmpIndicesToDefect2:
						IndicesToClosestDefectAfterCorner4=tmpIndicesToDefect1
					else:
						IndicesToClosestDefectAfterCorner4=tmpIndicesToDefect2
					
					if IndicesToClosestDefectBeforeCorner4>IndicesToClosestDefectAfterCorner4:
						corner4 = [beforeCorner4[0], afterCorner4[0]]
					else:
						corner4 = [afterCorner4[0], beforeCorner4[0]]
					
			elif len(beforeCorner4) == 0 and len(afterCorner4) != 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(potentialOuties[0][1]+2)%dSize][3], afterCorner4[0], defects1[(potentialOuties[0][1]+2)%dSize][3], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner4 = [tempCheckCorner[2][0]]
				else:
					corner4 = [afterCorner4[0]]
			elif len(beforeCorner4) != 0 and len(afterCorner4) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner4[0], defects1[(potentialOuties[0][1]+3)%dSize][2], beforeCorner4[0], ydim, closeCornersMethod=True)
				if tempCheckCorner[1] == True:
					corner4 = [tempCheckCorner[2][0]]
				else:
					corner4 = [beforeCorner4[0]]
			elif len(beforeCorner4) == 0 and len(afterCorner4) == 0:
				tempCheckCorner = checkCornerOrBigChange(contour, defects1[(potentialOuties[0][1]+2)%dSize][3], defects1[(potentialOuties[0][1]+3)%dSize][2], defects1[(potentialOuties[0][1]+2)%dSize][3], ydim, closeCornersMethod=True, hullMinFlat=True, hullMaxFlat=True, defectIndFlat=True)
				if tempCheckCorner[1] == True:
					corner4 = [tempCheckCorner[2][0]]
				else:
					print("error code 2oikppp")
					return None
			for c3 in corner3:
				for c4 in corner4:
					if c3 == -1 or c4 == -1:
						pass
					else:
						finalCorners.append([[(0, 1)], [corner1, corner2, c3, c4]])
			
			return finalCorners
			
		elif len(potentialOuties) == 2:
			defectList = []
			for potPair in potentialOuties:
				if potPair[0] in defectList or potPair[1] in defectList:
					print("defunct piece1")
					return None
				defectList.append(potPair[0])
				defectList.append(potPair[1])
			if (potentialOuties[0][1]+1)%dSize == potentialOuties[1][0] or (potentialOuties[1][1]+1)%dSize == potentialOuties[0][0]: # outies next to eachother
				
				orderedPotentialOuties = []
				if (potentialOuties[0][1]+1)%dSize == potentialOuties[1][0]:
					orderedPotentialOuties = [potentialOuties[0], potentialOuties[1]]
				elif (potentialOuties[1][1]+1)%dSize == potentialOuties[0][0]:
					orderedPotentialOuties = [potentialOuties[1], potentialOuties[0]]
				
				corner1 = defectDicts[orderedPotentialOuties[0][0]]["before"][0]
				corner2 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
				corner3 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
				corner4 = []
				
				beforeCorner4 = hullEndsOnVertex(contour, defects1[(orderedPotentialOuties[1][1]+1)%dSize][3], ydim, "after")
				afterCorner4 = hullEndsOnVertex(contour, defects1[(orderedPotentialOuties[1][1]+2)%dSize][2], ydim, "before")
				
				if len(beforeCorner4) != 0 and len(afterCorner4) != 0 and abs(beforeCorner4[0] - afterCorner4[0]) < hullEndingsAreJoinedIfWithin:
					corner4 = [beforeCorner4[0]]
				elif len(beforeCorner4) != 0 and len(afterCorner4) != 0:
					tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner4[0], afterCorner4[0], beforeCorner4[0], ydim)
					if tempCheckCorner[1] == True:
						corner4 = [tempCheckCorner[2][0]]
					else:
						# NEW
						# ambiguous, but prioritise the 'corner'(big angle change) who's closest defect is the furthest away
						IndicesToClosestDefectBeforeCorner4 = None
						IndicesToClosestDefectAfterCorner4 = None
						defect1 = defects1[(orderedPotentialOuties[1][1]+1)%dSize][0]
						defect2 = defects1[(orderedPotentialOuties[1][1]+2)%dSize][0]
						tmpIndicesToDefect1=None
						tmpIndicesToDefect2=None
						tmpIndicesToDefect1 = min(abs(defect1-beforeCorner4[0]), (defect1-beforeCorner4[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
						tmpIndicesToDefect2 = min(abs(defect2-beforeCorner4[0]), (defect2-beforeCorner4[0])%contour.shape[0])
						if tmpIndicesToDefect1<tmpIndicesToDefect2:
							IndicesToClosestDefectBeforeCorner4=tmpIndicesToDefect1
						else:
							IndicesToClosestDefectBeforeCorner4=tmpIndicesToDefect2
						
						tmpIndicesToDefect1=None
						tmpIndicesToDefect2=None
						tmpIndicesToDefect1 = min(abs(defect1-afterCorner4[0]), (defect1-afterCorner4[0])%contour.shape[0]) # this is indices between them because ring of integers modulo n
						tmpIndicesToDefect2 = min(abs(defect2-afterCorner4[0]), (defect2-afterCorner4[0])%contour.shape[0])
						if tmpIndicesToDefect1<tmpIndicesToDefect2:
							IndicesToClosestDefectAfterCorner4=tmpIndicesToDefect1
						else:
							IndicesToClosestDefectAfterCorner4=tmpIndicesToDefect2
						
						if IndicesToClosestDefectBeforeCorner4>IndicesToClosestDefectAfterCorner4:
							corner4 = [beforeCorner4[0], afterCorner4[0]]
						else:
							corner4 = [afterCorner4[0], beforeCorner4[0]]
						
				elif len(beforeCorner4) == 0 and len(afterCorner4) != 0:
					tempCheckCorner = checkCornerOrBigChange(contour, defects1[(orderedPotentialOuties[1][1]+1)%dSize][3], afterCorner4[0], defects1[(orderedPotentialOuties[1][1]+1)%dSize][3], ydim, hullMinFlat=True, defectIndFlat=True)
					if tempCheckCorner[1] == True:
						corner4 = [tempCheckCorner[2][0]]
					else:
						corner4 = [afterCorner4[0]]
				elif len(beforeCorner4) != 0 and len(afterCorner4) == 0:
					tempCheckCorner = checkCornerOrBigChange(contour, beforeCorner4[0], defects1[(orderedPotentialOuties[1][1]+2)%dSize][2], beforeCorner4[0], ydim, hullMaxFlat=True)
					if tempCheckCorner[1] == True:
						corner4 = [tempCheckCorner[2][0]]
					else:
						corner4 = [beforeCorner4[0]]
				elif len(beforeCorner4) == 0 and len(afterCorner4) == 0:
					tempCheckCorner = checkCornerOrBigChange(contour, defects1[(orderedPotentialOuties[1][1]+1)%dSize][3], defects1[(orderedPotentialOuties[1][1]+2)%dSize][2], defects1[(orderedPotentialOuties[1][1]+1)%dSize][3], ydim, closeCornersMethod=True, hullMinFlat=True, hullMaxFlat=True, defectIndFlat=True)
					if tempCheckCorner[1] == True:
						corner4 = [tempCheckCorner[2][0]]
					else:
						print("error code 2oikppp")
						return None
				
				for c4 in corner4:
					if c4 == -1:
						pass
					else:
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, c4]])

				return finalCorners
				
			elif (potentialOuties[0][1]+2)%dSize == potentialOuties[1][0] or (potentialOuties[1][1]+2)%dSize == potentialOuties[0][0]:# outies opposite eachother
				corner1 = defectDicts[potentialOuties[0][0]]["before"][0]
				corner2 = defectDicts[potentialOuties[0][1]]["after"][0]
				corner3 = defectDicts[potentialOuties[1][0]]["before"][0]
				corner4 = defectDicts[potentialOuties[1][1]]["after"][0]
				finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
				return finalCorners
			else:
				print("error code j38j3")
				return None
		elif len(potentialOuties) == 3:
			
			defectList = []
			print(potentialOuties)
			for potPair in potentialOuties:
				if potPair[0] in defectList or potPair[1] in defectList:
					print("defunct piece2")
					return None
				defectList.append(potPair[0])
				defectList.append(potPair[1])
			orderedPotentialOuties = []
			if (potentialOuties[0][1]+1)%dSize == potentialOuties[1][0]:
				if (potentialOuties[1][1]+1)%dSize == potentialOuties[2][0]:
					orderedPotentialOuties = [potentialOuties[0], potentialOuties[1], potentialOuties[2]]
				elif (potentialOuties[2][1]+1)%dSize == potentialOuties[0][0]:
					orderedPotentialOuties = [potentialOuties[2], potentialOuties[0], potentialOuties[1]]
			elif (potentialOuties[1][1]+1)%dSize == potentialOuties[2][0]:
				if (potentialOuties[2][1]+1)%dSize == potentialOuties[0][0]:
					orderedPotentialOuties = [potentialOuties[1], potentialOuties[2], potentialOuties[0]]
				elif (potentialOuties[0][1]+1)%dSize == potentialOuties[1][0]:
					orderedPotentialOuties = [potentialOuties[0], potentialOuties[1], potentialOuties[2]]
			elif (potentialOuties[2][1]+1)%dSize == potentialOuties[0][0]:
				if (potentialOuties[0][1]+1)%dSize == potentialOuties[1][0]:
					orderedPotentialOuties = [potentialOuties[2], potentialOuties[0], potentialOuties[1]]
				elif (potentialOuties[1][1]+1)%dSize == potentialOuties[2][0]:
					orderedPotentialOuties = [potentialOuties[1], potentialOuties[2], potentialOuties[0]]
			
			corner1 = defectDicts[orderedPotentialOuties[0][0]]["before"][0]
			corner2 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
			corner3 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
			corner4 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
			finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
			return finalCorners
		elif len(potentialOuties) == 4:
			defectList = []
			for potPair in potentialOuties:
				if potPair[0] in defectList or potPair[1] in defectList:
					print("defunct piece3")
					return None
				defectList.append(potPair[0])
				defectList.append(potPair[1])
			orderedPotentialOuties = [potentialOuties[0]]
			remainingPotOut = []
			for potOutie in potentialOuties[1:]:
				if (potentialOuties[0][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
				else:
					remainingPotOut.append(potOutie)
			if not (len(remainingPotOut) == 2 and len(orderedPotentialOuties) == 2):
				print("this should literally never happen ever")
				return None
			
			if (orderedPotentialOuties[1][1]+1)%dSize == remainingPotOut[0][0]:
				orderedPotentialOuties.append(remainingPotOut[0])
				orderedPotentialOuties.append(remainingPotOut[1])
			elif (orderedPotentialOuties[1][1]+1)%dSize == remainingPotOut[1][0]:
				orderedPotentialOuties.append(remainingPotOut[1])
				orderedPotentialOuties.append(remainingPotOut[0])
			else:
				print("wat4g4gj")
				return None
			
			corner1 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
			corner2 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
			corner3 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
			corner4 = defectDicts[orderedPotentialOuties[3][1]]["after"][0]
			finalCorners.append([[(0, 1), (1, 2), (2, 3), (3, 0)], [corner1, corner2, corner3, corner4]])
			return finalCorners
			
	elif len(potentialOuties) < dSize-4:
		print("error code 893jll")
		print(len(potentialOuties))
		print(dSize)
		print(dSize-4)
		return None
	
	else: # need to use more advanced methods below
		pass
	
	
	nonPotentialOuties = []
	for i in range(dSize):
		if [i, (i+1)%dSize] not in potentialOuties:
			nonPotentialOuties.append([i,(i+1)%dSize])
	
	if len(nonPotentialOuties) + potentialSize != dSize:
		print("weird12124")
		print(nonPotentialOuties)
		print(potentialOuties)
		print(dSize)
		print(potentialSize)
		return None
	
	if dSize == 5:
		if potentialSize == 5:
			print("impossible")
			return None
		elif potentialSize == 4:
			firstHullEndVertex = hullEndsOnVertex(contour, defects1[nonPotentialOuties[0][0]][2], ydim, "before")
			secondHullEndVertex = hullEndsOnVertex(contour, defects1[nonPotentialOuties[0][1]][3], ydim, "after")
			
			hullEndingClosestOfHullOneAfterVertex = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+1)%dSize][2], ydim, "before")
			hullEndingClosestOfHullOneBeforeVertex = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0]-1)%dSize][3], ydim, "after")
			
			if len(hullEndingClosestOfHullOneAfterVertex) == 0 or len(hullEndingClosestOfHullOneBeforeVertex) == 0:
				print("corners have no vertex? code 1293")
				return None
			
			if len(firstHullEndVertex) == 0 or abs(firstHullEndVertex[0] - hullEndingClosestOfHullOneBeforeVertex[0]) < hullEndingsAreJoinedIfWithin:
				
				corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+2)%dSize][2], ydim, "before")[0]
				corner2 = hullEndingClosestOfHullOneBeforeVertex[0]
				corner3 = checkCornerOrBigChange(contour, defects1[(nonPotentialOuties[0][0])][3], defects1[(nonPotentialOuties[0][1])][2], defects1[(nonPotentialOuties[0][0])][3], ydim)[2][0]
				corner4 = secondHullEndVertex[0]
				
				if corner3 == -1:
					pass
				else:
					finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
			elif len(secondHullEndVertex) == 0 or abs(secondHullEndVertex[0] - hullEndingClosestOfHullOneAfterVertex[0]) < hullEndingsAreJoinedIfWithin:
				
				corner1 = hullEndingClosestOfHullOneAfterVertex[0]
				corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+2)%dSize][3], ydim, "after")[0]
				corner3 = firstHullEndVertex[0]
				corner4 = checkCornerOrBigChange(contour, defects1[(nonPotentialOuties[0][0])][3], defects1[(nonPotentialOuties[0][1])][2], defects1[(nonPotentialOuties[0][0])][3], ydim)[2][0]
				
				if corner4 == -1:
					pass
				else:
					finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
			else:
				
				corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+2)%dSize][2], ydim, "before")[0]
				corner2 = hullEndingClosestOfHullOneBeforeVertex[0]
				corner3 = checkCornerOrBigChange(contour, defects1[(nonPotentialOuties[0][0])][3], defects1[(nonPotentialOuties[0][1])][2], defects1[(nonPotentialOuties[0][0])][3], ydim)[2][0]
				corner4 = secondHullEndVertex[0]
				if corner3 == -1:
					pass
				else:
				
					finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
				corner1 = hullEndingClosestOfHullOneAfterVertex[0]
				corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+2)%dSize][3], ydim, "after")[0]
				corner3 = firstHullEndVertex[0]
				corner4 = checkCornerOrBigChange(contour, defects1[(nonPotentialOuties[0][0])][3], defects1[(nonPotentialOuties[0][1])][2], defects1[(nonPotentialOuties[0][0])][3], ydim)[2][0]
				
				if corner4 == -1:
					pass
				else:
					finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
		elif potentialSize == 3:
			
			tempNonPotentialOuties = []
			if nonPotentialOuties[0][1] == nonPotentialOuties[1][0]:
				pass
			elif nonPotentialOuties[1][1] == nonPotentialOuties[0][0]:
				tempNonPotentialOuties.append(nonPotentialOuties[1])
				tempNonPotentialOuties.append(nonPotentialOuties[0])
				nonPotentialOuties = tempNonPotentialOuties
			else:
				print("code 2iei")
				return None
			
			
			oppositeHullStartVertex = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")
			oppositeHullEndVertex = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][3], ydim, "after")
				
			hullEndingClosestOfHullOneAfterOpposite = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+1)%dSize][2], ydim, "before")
			hullEndingClosestOfHullOneBeforeOpposite = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]-1)%dSize][3], ydim, "after")
			
			if len(hullEndingClosestOfHullOneAfterOpposite) == 0 or len(hullEndingClosestOfHullOneBeforeOpposite) == 0:
				print("corners have no vertex? code 1293")
				return None
			
			if len(oppositeHullStartVertex) == 0 or abs(oppositeHullStartVertex[0] - hullEndingClosestOfHullOneBeforeOpposite[0]) < hullEndingsAreJoinedIfWithin: 
				
				corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+2)%dSize][2], ydim, "before")[0]
				corner2 = hullEndingClosestOfHullOneBeforeOpposite[0]
				corner3 = oppositeHullEndVertex[0]
				corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][3], ydim, "after")[0]
				
				finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
			elif len(oppositeHullEndVertex) == 0 or abs(oppositeHullEndVertex[0] - hullEndingClosestOfHullOneAfterOpposite[0]) < hullEndingsAreJoinedIfWithin:
				
				corner1 = hullEndingClosestOfHullOneAfterOpposite[0]
				corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+1)%dSize][3], ydim, "after")[0]
				corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][2], ydim, "before")[0]
				corner4 = oppositeHullStartVertex[0]
				
				finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
			else:
				#left
				corner1 = hullEndingClosestOfHullOneAfterOpposite[0]
				corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+1)%dSize][3], ydim, "after")[0]
				corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][2], ydim, "before")[0]
				corner4 = oppositeHullStartVertex[0]
				
				finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
				#right
				corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+2)%dSize][2], ydim, "before")[0]
				corner2 = hullEndingClosestOfHullOneBeforeOpposite[0]
				corner3 = oppositeHullEndVertex[0]
				corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][3], ydim, "after")[0]
				
				finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
				#middle
				corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+1)%dSize][2], ydim, "before")[0]
				corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+2)%dSize][3], ydim, "after")[0]
				corner3 = oppositeHullStartVertex[0]
				corner4 = oppositeHullEndVertex[0]
				
				finalCorners.append([[(0, 1)], [corner1, corner2, corner3, corner4]])
				
		elif potentialSize == 2:
			if potentialOuties[0][1] == potentialOuties[1][0] or potentialOuties[0][0] == potentialOuties[1][1]:
				
				firstPair = []
				secondPair = []
				
				if potentialOuties[0][1] == potentialOuties[1][0]:
					firstPair = potentialOuties[0]
					secondPair = potentialOuties[1]
				elif potentialOuties[0][0] == potentialOuties[1][1]:
					firstPair = potentialOuties[1]
					secondPair = potentialOuties[0]
				
				outerHullEndingFirstDefect = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][2], ydim, "before")
				outerHullEndingThirdDefect = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][3], ydim, "after")
					
				hullEndingClosestOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][3], ydim, "after")
				hullEndingClosestOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][2], ydim, "before")
		
				if len(outerHullEndingFirstDefect) == 0 or len(outerHullEndingThirdDefect) == 0:
					print("corners have no vertex? code 12923")
					return None
				
				if len(hullEndingClosestOfHullOneBeforeFirst) == 0 or abs(hullEndingClosestOfHullOneBeforeFirst[0] - outerHullEndingFirstDefect[0]) < hullEndingsAreJoinedIfWithin:
					
					if len(hullEndingClosestOfHullOneAfterThird)==0:
						print("not sure what was meant to be here 3ij")
						return None
					
					corner1 = outerHullEndingFirstDefect[0]
					corner2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")[0]
					corner3 = hullEndingClosestOfHullOneAfterThird[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[0]-1)%dSize][2], hullEndingAwayOfHullOneAfterThird[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], defects1[(firstPair[0]-1)%dSize][2], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c4 in tempcorner4:
							if c4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, corner3, c4]])
						
					else:
						print("??? 2oek")
						return None
					
				elif len(hullEndingClosestOfHullOneAfterThird) == 0 or abs(hullEndingClosestOfHullOneAfterThird[0] - outerHullEndingThirdDefect[0]) < hullEndingsAreJoinedIfWithin:
					
					if len(hullEndingClosestOfHullOneBeforeFirst)==0:
						print("not sure what was meant to be here 3ij")
						return None
					
					corner1 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")[0]
					corner2 = outerHullEndingThirdDefect[0]
					actualCorner4 = hullEndingClosestOfHullOneBeforeFirst[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[0]-1)%dSize][2], hullEndingAwayOfHullOneAfterThird[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], defects1[(firstPair[0]-1)%dSize][2], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c4 in tempcorner4:
							if c4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, c4, actualCorner4]])
						
					else:
						print("??? 2oek")
						return None
					
				else:	## ALL 4 OF ABOVE 2 SCENARIOS
					
					# SCENARIO 1 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
					
					corner1 = outerHullEndingFirstDefect[0]
					corner2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")[0]
					corner3 = hullEndingClosestOfHullOneAfterThird[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[0]-1)%dSize][2], hullEndingAwayOfHullOneAfterThird[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], defects1[(firstPair[0]-1)%dSize][2], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c4 in tempcorner4:
							if c4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, corner3, c4]])
						
					else:
						print("??? 2oek")
						return None
						
					# SCENARIO 2 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
					
					corner1 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")[0]
					corner2 = outerHullEndingThirdDefect[0]
					actualCorner4 = hullEndingClosestOfHullOneBeforeFirst[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[0]-1)%dSize][2], hullEndingAwayOfHullOneAfterThird[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[1]+1)%dSize][3], defects1[(firstPair[0]-1)%dSize][2], defects1[(secondPair[1]+1)%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c3 in tempcorner4:
							if c3 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, c3, actualCorner4]])
						
					else:
						print("??? 2oek")
						return None
					
			elif potentialOuties[0][1] != potentialOuties[1][0] and potentialOuties[1][1] != potentialOuties[0][0]: # not sharing a defect
				
				firstPair = []
				secondPair = []
				
				if potentialOuties[1][0] == potentialOuties[0][1] + 1:
					firstPair = potentialOuties[0]
					secondPair = potentialOuties[1]
				elif potentialOuties[0][0] == potentialOuties[1][1] + 1:
					firstPair = potentialOuties[1]
					secondPair = potentialOuties[0]
				else:
					print("error code 89ue")
					return None
				
				hullEndingOfUnusedTowardsFourth = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][2], ydim, "before")
				hullEndingOfUnusedTowardsFirst = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
				
				hullEndingOfFirstTowardsUnused = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][2], ydim, "before")
				hullEndingOfFourthTowardsUnused = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][3], ydim, "after")
				
				if len(hullEndingOfUnusedTowardsFirst) == 0 or abs(hullEndingOfUnusedTowardsFirst[0] - hullEndingOfFirstTowardsUnused[0]) < hullEndingsAreJoinedIfWithin:
					
					if len(hullEndingOfUnusedTowardsFourth)==0:
						print("not sure what was meant to be here 3i5j")
						return None
					
					corner1 = hullEndingOfFirstTowardsUnused[0]
					corner2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")[0]
					corner4 = hullEndingOfUnusedTowardsFourth[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1])%dSize][2], hullEndingAwayOfHullOneBeforeFirst[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[0])%dSize][3], hullEndingAwayOfHullOneAfterThird[0], defects1[(secondPair[0])%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[0])%dSize][3], defects1[(secondPair[1])%dSize][2], defects1[(secondPair[0])%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c3 in tempcorner4:
							if c3 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, c3, corner4]])
						
					else:
						print("??? 2oek")
						return None
						###
					
				elif len(hullEndingOfUnusedTowardsFourth) == 0 or abs(hullEndingOfUnusedTowardsFourth[0] - hullEndingOfFourthTowardsUnused[0]) < hullEndingsAreJoinedIfWithin:
					
					if len(hullEndingOfUnusedTowardsFirst)==0:
						print("not sure what was meant to be here 3i3j")
						return None
					
					corner1 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][2], ydim, "before")[0]
					corner2 = hullEndingOfFourthTowardsUnused[0]
					corner3 = hullEndingOfUnusedTowardsFirst[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneBeforeFirst[0], defects1[(firstPair[0])%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(firstPair[1])%dSize][2], hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[1])%dSize][2], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(firstPair[0])%dSize][3], defects1[(firstPair[1])%dSize][2], defects1[(firstPair[0])%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c4 in tempcorner4:
							if c4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, corner3, c4]])
						
					else:
						print("??? 2oek")
						return None
						
				else:
					
					#BOTH OF ABOVE SCENARIOS
					#SCENARIO 1
					
					corner1 = hullEndingOfFirstTowardsUnused[0]
					corner2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")[0]
					corner4 = hullEndingOfUnusedTowardsFourth[0]
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneBeforeFirst[0], defects1[(secondPair[1])%dSize][2], hullEndingAwayOfHullOneBeforeFirst[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[0])%dSize][3], hullEndingAwayOfHullOneAfterThird[0], defects1[(secondPair[0])%dSize][3], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(secondPair[0])%dSize][3], defects1[(secondPair[1])%dSize][2], defects1[(secondPair[0])%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c3 in tempcorner4:
							if c3 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, c3, corner4]])
						
					else:
						print("??? 2oek")
						return None
						
					#SCENARIO 2
					
					corner1 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][2], ydim, "before")[0]
					corner2 = hullEndingOfFourthTowardsUnused[0]
					corner3 = hullEndingOfUnusedTowardsFirst[0]
					
					###
					
					hullEndingAwayOfHullOneBeforeFirst = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")
					hullEndingAwayOfHullOneAfterThird = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
					
					tempcorner4 = -1
					
					if len(hullEndingAwayOfHullOneBeforeFirst) != 0 and len(hullEndingAwayOfHullOneAfterThird) != 0:
						if abs(hullEndingAwayOfHullOneBeforeFirst[0] - hullEndingAwayOfHullOneAfterThird[0]) < hullEndingsAreJoinedIfWithin:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						else:
							vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0], hullEndingAwayOfHullOneAfterThird[0], ydim)
							if vertexBetweenThem[1] == True:
								tempcorner4 = [vertexBetweenThem[2][0]]
							else:
								tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0], hullEndingAwayOfHullOneBeforeFirst[0]]
					
					elif len(hullEndingAwayOfHullOneBeforeFirst) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, hullEndingAwayOfHullOneBeforeFirst[0], defects1[(firstPair[0])%dSize][3], hullEndingAwayOfHullOneBeforeFirst[0], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneBeforeFirst[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) != 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(firstPair[1])%dSize][2], hullEndingAwayOfHullOneAfterThird[0], defects1[(firstPair[1])%dSize][2], ydim)
						if vertexBetweenThem[1] == True:
							tempcorner4 = [vertexBetweenThem[2][0]]
						else:
							tempcorner4 = [hullEndingAwayOfHullOneAfterThird[0]]
						
					elif len(hullEndingAwayOfHullOneAfterThird) == 0 and len(hullEndingAwayOfHullOneBeforeFirst) == 0:
						vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(firstPair[0])%dSize][3], defects1[(firstPair[1])%dSize][2], defects1[(firstPair[0])%dSize][3], ydim)
						if len(vertexBetweenThem[2]) == 0:
							print("neither on corner but no vertex between them?? code 2923")
							return None
						else:
							tempcorner4 = [vertexBetweenThem[2][0]]
						
					if tempcorner4 == -1:
						print("tempcorner4 -1?? code 02938")
						return None
					
					elif len(tempcorner4) == 1 or len(tempcorner4) == 2:
						for c4 in tempcorner4:
							if c4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1)], [corner1, corner2, corner3, c4]])
						
					else:
						print("??? 2oek")
						return None
						
			else:
				print("impossible? code 2991")
			
	elif dSize == 6:
		if potentialSize == 6:
			joins = []
			vertexBetweenHulls = []
			
			storeHullEndsOnVertex = []
			
			for potential in potentialOuties:
				firstEnding = hullEndsOnVertex(contour, defects1[(potential[0])%dSize][3], ydim, "after")
				secondEnding = hullEndsOnVertex(contour, defects1[(potential[1])%dSize][2], ydim, "before")
				
				storeHullEndsOnVertex.append([potential, firstEnding[0], secondEnding[0]])
				
				if len(firstEnding) != 0 and len(secondEnding) != 0 and abs(firstEnding[0] - secondEnding[0]) < hullEndingsAreJoinedIfWithin:
					joins.append([potential, firstEnding[0]])
				
				elif len(firstEnding) != 0:
					vertexBetweenThem = checkCornerOrBigChange(contour, firstEnding[0], defects1[(potential[1])%dSize][2], firstEnding[0], ydim)
					if vertexBetweenThem[1] == True:
						vertexBetweenHulls.append([potential,vertexBetweenThem[2][0]])
					
				elif len(secondEnding) != 0:
					vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(potential[0])%dSize][3], secondEnding[0], defects1[(potential[0])%dSize][3], ydim)
					if vertexBetweenThem[1] == True:
						vertexBetweenHulls.append([potential,vertexBetweenThem[2][0]])
					
				else:
					vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(potential[0])%dSize][3], defects1[(potential[1])%dSize][2], defects1[(potential[0])%dSize][3], ydim)
					if vertexBetweenThem[1] == True:
						vertexBetweenHulls.append([potential,vertexBetweenThem[2][0]])
					
			if len(joins) == 3 or len(vertexBetweenHulls) == 3 or (len(joins)==2 and (joins[0][0][1] == joins[1][0][0] or joins[1][0][1] == joins[0][0][0])) or (len(vertexBetweenHulls)==2 and not ((vertexBetweenHulls[0][0][1]+2)%dSize == vertexBetweenHulls[1][0][0])):  # outies next to eachother
				if len(joins) == 3:
					
					if len(vertexBetweenHulls) != 1:
						print("error 298k")
						return None
					else:
						corner1 = -1
						corner2 = -1
						corner3 = -1
						corner4 = -1
						for storedVertex in storeHullEndsOnVertex:
							if storedVertex[0][0] == vertexBetweenHulls[0][0][1]:
								corner1 = storedVertex[2]
							elif storedVertex[0][0] == (vertexBetweenHulls[0][0][1]+2)%dSize:
								corner2 = storedVertex[1]
							elif storedVertex[0][0] == (vertexBetweenHulls[0][0][1]+4)%dSize:
								corner3 = storedVertex[1]
						corner4 = vertexBetweenHulls[0][1]
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
				
				elif len(vertexBetweenHulls) == 3:
					if len(joins) != 1:
						print("error 29219")
						return None
					else:
						corner1 = -1
						corner2 = -1
						corner3 = -1
						corner4 = -1
						for storedVertex in storeHullEndsOnVertex:
							if storedVertex[0][0] == (joins[0][0][1]+1)%dSize:
								corner3 = storedVertex[1]
							elif storedVertex[0][0] == (joins[0][0][1]+3)%dSize:
								corner1 = storedVertex[2]
						for vertex1 in vertexBetweenHulls:
							if vertex1[0][0] == (joins[0][0][1]+2)%dSize:
								corner4 = vertex1[1]
						corner2 = joins[0][1]
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
				elif (len(joins)==2 and (joins[0][0][1] == joins[1][0][0] or joins[1][0][1] == joins[0][0][0])):
					mainVertex = []
					mainJoin = []
					for vertex1 in vertexBetweenHulls:
						if vertex1[0][0] == (joins[0][0][1]+2)%dSize:
							mainVertex = vertex1
							mainJoin = joins[0]
						elif vertex1[0][0] == (joins[1][0][1]+2)%dSize:
							mainVertex = vertex1
							mainJoin = joins[1]
					
					corner2 = mainJoin[1]
					corner4 = mainVertex[1]
					corner1 = -1
					corner3 = -1
					for storedVertex in storeHullEndsOnVertex:
						if storedVertex[0][0] == mainVertex[0][1]:
							corner1 = storedVertex[2]
						elif storedVertex[0][0] == (mainJoin[0][1]+1)%dSize:
							corner3 = storedVertex[1]
					finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
				elif (len(vertexBetweenHulls)==2 and not ((vertexBetweenHulls[0][0][1]+2)%dSize == vertexBetweenHulls[1][0][0])):
					mainVertex = []
					mainJoin = []
					for join1 in joins:
						if join1[0][0] == (vertexBetweenHulls[0][0][1]+2)%dSize:
							mainVertex = vertexBetweenHulls[0]
							mainJoin = join1
						elif join1[0][0] == (vertexBetweenHulls[1][0][1]+2)%dSize:
							mainVertex = vertexBetweenHulls[1]
							mainJoin = join1
					
					corner2 = mainJoin[1]
					corner4 = mainVertex[1]
					corner1 = -1
					corner3 = -1
					for storedVertex in storeHullEndsOnVertex:
						if storedVertex[0][0] == mainVertex[0][1]:
							corner1 = storedVertex[2]
						elif storedVertex[0][0] == (mainJoin[0][1]+1)%dSize:
							corner3 = storedVertex[1]
					finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
				
			elif len(joins) == 0 or len(vertexBetweenHulls) == 0 or (len(joins)==2 and ((joins[0][0][1]+2)%dSize == joins[1][0][0])) or (len(vertexBetweenHulls)==2 and ((vertexBetweenHulls[0][0][1]+2)%dSize == vertexBetweenHulls[1][0][0])): # outies opposite eachother
				if len(joins) == 0 or len(vertexBetweenHulls) == 0: # just try all
					for j in range(3):
						tempPotential = [j,j+1]
						corner1 = -1
						corner2 = -1
						corner3 = -1
						corner4 = -1
						for storedVertex in storeHullEndsOnVertex:
							if storedVertex[0][0] == (tempPotential[0]-1)%dSize:
								corner1 = storedVertex[2]
							elif storedVertex[0][0] == (tempPotential[0]+1)%dSize:
								corner2 = storedVertex[1]
							elif storedVertex[0][0] == (tempPotential[0]+2)%dSize:
								corner3 = storedVertex[2]
							elif storedVertex[0][0] == (tempPotential[0]-2)%dSize:
								corner4 = storedVertex[1]
						finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
				
				elif (len(joins)==2 and ((joins[0][0][1]+2)%dSize == joins[1][0][0])) or (len(vertexBetweenHulls)==2 and ((vertexBetweenHulls[0][0][1]+2)%dSize == vertexBetweenHulls[1][0][0])):
					realOuties = []
					if (len(joins)==2 and ((joins[0][0][1]+2)%dSize == joins[1][0][0])):
						realOuties = [joins[0][0], joins[1][0]]
					elif (len(vertexBetweenHulls)==2 and ((vertexBetweenHulls[0][0][1]+2)%dSize == vertexBetweenHulls[1][0][0])):
						realOuties = [vertexBetweenHulls[0][0], vertexBetweenHulls[1][0]]
					
					corner1 = -1
					corner2 = -1
					corner3 = -1
					corner4 = -1
					for storedVertex in storeHullEndsOnVertex:
						if storedVertex[0][0] == (realOuties[0][0]-1)%dSize:
							corner1 = storedVertex[2]
						elif storedVertex[0][0] == (realOuties[0][0]+1)%dSize:
							corner2 = storedVertex[1]
						elif storedVertex[0][0] == (realOuties[0][0]+2)%dSize:
							corner3 = storedVertex[2]
						elif storedVertex[0][0] == (realOuties[0][0]-2)%dSize:
							corner4 = storedVertex[1]
					finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
				
			elif len(joins) == 1 and len(vertexBetweenHulls) == 1: #either
				#try both, firstly do as if nubs are opposite eachother
				tempPotential = [joins[0][0][0], joins[0][0][1]]
				corner1 = -1
				corner2 = -1
				corner3 = -1
				corner4 = -1
				for storedVertex in storeHullEndsOnVertex:
					if storedVertex[0][0] == (tempPotential[0][0]-1)%dSize:
						corner1 = storedVertex[2]
					elif storedVertex[0][0] == (tempPotential[0][0]+1)%dSize:
						corner2 = storedVertex[1]
					elif storedVertex[0][0] == (tempPotential[0][0]+2)%dSize:
						corner3 = storedVertex[2]
					elif storedVertex[0][0] == (tempPotential[0][0]-2)%dSize:
						corner4 = storedVertex[1]
				finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
				
				corner1 = -1
				corner2 = -1
				corner3 = -1
				corner4 = -1
				for storedVertex in storeHullEndsOnVertex:
					if storedVertex[0][0] == vertexBetweenHulls[0][0][1]:
						corner1 = storedVertex[2]
					elif storedVertex[0][0] == (vertexBetweenHulls[0][0][1]+2)%dSize:
						corner2 = storedVertex[1]
					elif storedVertex[0][0] == (vertexBetweenHulls[0][0][1]+4)%dSize:
						corner3 = storedVertex[1]
				corner4 = vertexBetweenHulls[0][1]
				finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
				
		elif potentialSize == 5:
			notPotential = nonPotentialOuties[0]
			
			firstInwardsHullEnding = hullEndsOnVertex(contour, defects1[(notPotential[0])%dSize][3], ydim, "after")
			secondInwardsHullEnding = hullEndsOnVertex(contour, defects1[(notPotential[1])%dSize][2], ydim, "before")
			
			if len(firstInwardsHullEnding) != 0 and len(secondInwardsHullEnding) != 0 and abs(firstInwardsHullEnding[0] - secondInwardsHullEnding[0]) < hullEndingsAreJoinedIfWithin: # on single join of outies next to eachother
				corner1 = hullEndsOnVertex(contour, defects1[(notPotential[0]-1)%dSize][2], ydim, "before")[0]
				corner2 = firstInwardsHullEnding[0]
				corner3 = hullEndsOnVertex(contour, defects1[(notPotential[0]+2)%dSize][3], ydim, "after")[0]
				corner4 = checkCornerOrBigChange(contour, defects1[(notPotential[0]+3)%dSize][3], defects1[(notPotential[0]+4)%dSize][2], defects1[(notPotential[0]+3)%dSize][3], ydim)[2][0]
				if corner4 == -1:
					pass
				else:
					finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
			
			else:
				isVertexBetweenThem = checkCornerOrBigChange(contour, defects1[(notPotential[0])%dSize][3], defects1[(notPotential[1])%dSize][2], defects1[(notPotential[0])%dSize][3], ydim)
				if isVertexBetweenThem[1] == True:
					mainJoin = [(notPotential[0]+3)%dSize, (notPotential[1]+3)%dSize]
					corner1 = hullEndsOnVertex(contour, defects1[(mainJoin[0]-1)%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(mainJoin[0])%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(mainJoin[0]+2)%dSize][3], ydim, "after")[0]
					corner4 = isVertexBetweenThem[2][0]
					if corner4 == -1:
						pass
					else:
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
				else:
					firstPair = [(notPotential[1]+1)%dSize, (notPotential[1]+2)%dSize]
					secondPair = [(notPotential[1]+3)%dSize, (notPotential[1]+4)%dSize]
					
					firstPair1 = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
					firstPair2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")
					
					secondPair1 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")
					secondPair2 = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")
					
					joinedPair = []
					
					if len(firstPair1) != 0 and len(firstPair2) != 0 and abs(firstPair1[0] - firstPair2[0]) < hullEndingsAreJoinedIfWithin:
						joinedPair = firstPair
						joinedPair.append(firstPair1[0])
					
					elif len(secondPair1) != 0 and len(secondPair2) != 0 and abs(secondPair1[0] - secondPair2[0]) < hullEndingsAreJoinedIfWithin:
						joinedPair = secondPair
						joinedPair.append(secondPair1[0])
					
					if len(joinedPair) != 0:
						corner1 = hullEndsOnVertex(contour, defects1[(joinedPair[0]-1)%dSize][2], ydim, "before")[0]
						corner2 = joinedPair[2]
						corner3 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+2)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						if joinedPair[0] == firstPair[0]:
							tempVertexCheck1 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+4)%dSize][2], ydim, "before")
							tempVertexCheck2 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+3)%dSize][3], ydim, "after")
							if (len(tempVertexCheck1) != 0 and len(tempVertexCheck2) != 0 and abs(tempVertexCheck1[0] - tempVertexCheck2[0]) < hullEndingsAreJoinedIfWithin) or len(tempVertexCheck2) == 0:
								pass
							else:
								if len(tempVertexCheck1) == 0:
									cornerBetweenThem = checkCornerOrBigChange(contour, tempVertexCheck2[0], defects1[(joinedPair[0]+4)%dSize][2], tempVertexCheck2[0], ydim)
									corner4 = cornerBetweenThem[2][0]
									if corner4 == -1:
										pass
									else:
										finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
								else:
									cornerBetweenThem = checkCornerOrBigChange(contour, tempVertexCheck2[0], tempVertexCheck1[0], tempVertexCheck2[0], ydim)
									if cornerBetweenThem[1] == False:
										corner4 = tempVertexCheck1[0]
										finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
									else:
										corner4 = cornerBetweenThem[2][0]
										if corner4 == -1:
											pass
										else:
											finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
									
							
						elif joinedPair[0] == secondPair[0]:
							tempVertexCheck1 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+4)%dSize][2], ydim, "before")
							tempVertexCheck2 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+3)%dSize][3], ydim, "after")
							if (len(tempVertexCheck1) != 0 and len(tempVertexCheck2) != 0 and abs(tempVertexCheck1[0] - tempVertexCheck2[0]) < hullEndingsAreJoinedIfWithin) or len(tempVertexCheck1) == 0:
								pass
							else:
								if len(tempVertexCheck2) == 0:
									cornerBetweenThem = checkCornerOrBigChange(contour, defects1[(joinedPair[0]+3)%dSize][3], tempVertexCheck1[0], defects1[(joinedPair[0]+3)%dSize][3], ydim)
									corner4 = cornerBetweenThem[2][0]
									if corner4 == -1:
										pass
									else:
										finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
								else:
									cornerBetweenThem = checkCornerOrBigChange(contour, tempVertexCheck2[0], tempVertexCheck1[0], tempVertexCheck2[0], ydim)
									if cornerBetweenThem[1] == False:
										corner4 = tempVertexCheck2[0]
										finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
									else:
										corner4 = cornerBetweenThem[2][0]
										if corner4 == -1:
											pass
										else:
											finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							
							
						else:
							print("error code 1928he")
							return None
						
						
						#second one (if the join is on one of the opposite outies)
						corner1 = hullEndsOnVertex(contour, defects1[(joinedPair[0])%dSize][2], ydim, "before")[0]
						corner2 = hullEndsOnVertex(contour, defects1[(joinedPair[1])%dSize][3], ydim, "after")[0]
						corner3 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+3)%dSize][2], ydim, "before")[0]
						corner4 = hullEndsOnVertex(contour, defects1[(joinedPair[0]+4)%dSize][3], ydim, "after")[0]
						finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
						
						
					else: # outies are opposite eachother
						tempcorner1 = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][2], ydim, "before")
						tempcorner2 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")
						tempcorner3 = hullEndsOnVertex(contour, defects1[(firstPair[0]+3)%dSize][2], ydim, "before")
						tempcorner4 = hullEndsOnVertex(contour, defects1[(firstPair[0]+4)%dSize][3], ydim, "after")
						
						if len(tempcorner1) == 0 or len(tempcorner3) == 0 or len(tempcorner2) == 0 or len(tempcorner4) == 0:
							pass
						else:
							corner1 = tempcorner1[0]
							corner2 = tempcorner2[0]
							corner3 = tempcorner3[0]
							corner4 = tempcorner4[0]
							finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
						
						
						tempcorner1 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][2], ydim, "before")
						tempcorner2 = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][3], ydim, "after")
						tempcorner3 = hullEndsOnVertex(contour, defects1[(secondPair[0]+3)%dSize][2], ydim, "before")
						tempcorner4 = hullEndsOnVertex(contour, defects1[(secondPair[0]+4)%dSize][3], ydim, "after")
						
						if len(tempcorner1) == 0 or len(tempcorner3) == 0 or len(tempcorner2) == 0 or len(tempcorner4) == 0:
							pass
						else:
							corner1 = tempcorner1[0]
							corner2 = tempcorner2[0]
							corner3 = tempcorner3[0]
							corner4 = tempcorner4[0]
							finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
						
						
		elif potentialSize == 4:
			if (nonPotentialOuties[0][0]+3)%dSize == nonPotentialOuties[1][0] and (nonPotentialOuties[0][1]+3)%dSize == nonPotentialOuties[1][1]:  #if the nonpotential pairs are opposite
				firstNonPotentialHullEnding1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][3], ydim, "after")
				firstNonPotentialHullEnding2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")
				secondNonPotentialHullEnding1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][0])%dSize][3], ydim, "after")
				secondNonPotentialHullEnding2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][2], ydim, "before")
				
				if (len(firstNonPotentialHullEnding1) != 0 and len(firstNonPotentialHullEnding2) != 0 and abs(firstNonPotentialHullEnding1[0] - firstNonPotentialHullEnding2[0]) < hullEndingsAreJoinedIfWithin) or (len(secondNonPotentialHullEnding1) != 0 and len(secondNonPotentialHullEnding2) != 0 and abs(secondNonPotentialHullEnding1[0] - secondNonPotentialHullEnding2[0]) < hullEndingsAreJoinedIfWithin): #outies next to eachother
					mainJoin = []
					if (len(firstNonPotentialHullEnding1) != 0 and len(firstNonPotentialHullEnding2) != 0 and abs(firstNonPotentialHullEnding1[0] - firstNonPotentialHullEnding2[0]) < hullEndingsAreJoinedIfWithin):
						mainJoin = [nonPotentialOuties[0][0], nonPotentialOuties[0][1], firstNonPotentialHullEnding1[0]]
					elif (len(secondNonPotentialHullEnding1) != 0 and len(secondNonPotentialHullEnding2) != 0 and abs(secondNonPotentialHullEnding1[0] - secondNonPotentialHullEnding2[0]) < hullEndingsAreJoinedIfWithin):
						mainJoin = [nonPotentialOuties[1][0], nonPotentialOuties[1][1], secondNonPotentialHullEnding1[0]]
					
					corner1 = hullEndsOnVertex(contour, defects1[(mainJoin[0]-1)%dSize][2], ydim, "before")
					corner2 = mainJoin[2]
					corner3 = hullEndsOnVertex(contour, defects1[(mainJoin[1]+1)%dSize][3], ydim, "after")
					
					vertexBetweenThem = checkCornerOrBigChange(contour, defects1[(mainJoin[0]+3)%dSize][3], defects1[(mainJoin[0]+4)%dSize][2], defects1[(mainJoin[0]+3)%dSize][3], ydim)
					
					corner4 = vertexBetweenThem[2][0]
					if corner4 == -1:
						pass
					else:
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
				else: # outies opposite eachother
					#Try both 1 to left and 1 to right
					
					corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0]-1)%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][0]-1)%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][0])%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
					
					corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+1)%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
					
					
			elif nonPotentialOuties[0][0] == nonPotentialOuties[1][1] or nonPotentialOuties[0][1] == nonPotentialOuties[1][0]: # nonpotentials share a defect
				lastNonPotential = -1
				if nonPotentialOuties[0][0] == nonPotentialOuties[1][1]:
					lastNonPotential = nonPotentialOuties[0][1]
				elif nonPotentialOuties[0][1] == nonPotentialOuties[1][0]:
					lastNonPotential = nonPotentialOuties[1][1]
				
				#check the 2 pairs within the 3 defects that arent connected to the 3 that are nonpotentials
				firstPairFromOther3HullEnding1 = hullEndsOnVertex(contour, defects1[(lastNonPotential+1)%dSize][3], ydim, "after")
				firstPairFromOther3HullEnding2 = hullEndsOnVertex(contour, defects1[(lastNonPotential+2)%dSize][2], ydim, "before")
				secondPairFromOther3HullEnding1 = hullEndsOnVertex(contour, defects1[(lastNonPotential+2)%dSize][3], ydim, "after")
				secondPairFromOther3HullEnding2 = hullEndsOnVertex(contour, defects1[(lastNonPotential+3)%dSize][2], ydim, "before")
				
				if (len(firstPairFromOther3HullEnding1) != 0 and len(firstPairFromOther3HullEnding2) != 0 and abs(firstPairFromOther3HullEnding1[0] - firstPairFromOther3HullEnding2[0]) < hullEndingsAreJoinedIfWithin) or (len(secondPairFromOther3HullEnding1) != 0 and len(secondPairFromOther3HullEnding2) != 0 and abs(secondPairFromOther3HullEnding1[0] - secondPairFromOther3HullEnding2[0]) < hullEndingsAreJoinedIfWithin): #outies next to eachother
					#will usually only have 1 join but prepare for 2
					if (len(firstPairFromOther3HullEnding1) != 0 and len(firstPairFromOther3HullEnding2) != 0 and abs(firstPairFromOther3HullEnding1[0] - firstPairFromOther3HullEnding2[0]) < hullEndingsAreJoinedIfWithin):
						corner1 = hullEndsOnVertex(contour, defects1[(lastNonPotential)%dSize][2], ydim, "before")[0]
						corner2 = firstPairFromOther3HullEnding1[0]
						corner3 = hullEndsOnVertex(contour, defects1[(lastNonPotential+3)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(lastNonPotential+4)%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(lastNonPotential+5)%dSize][2], ydim, "before")
						
						if len(tempAfterCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], defects1[(lastNonPotential+5)%dSize][2], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 27yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempAfterCorner4Hull[0]
						
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						
					if (len(secondPairFromOther3HullEnding1) != 0 and len(secondPairFromOther3HullEnding2) != 0 and abs(secondPairFromOther3HullEnding1[0] - secondPairFromOther3HullEnding2[0]) < hullEndingsAreJoinedIfWithin):
						corner1 = hullEndsOnVertex(contour, defects1[(lastNonPotential+1)%dSize][2], ydim, "before")[0]
						corner2 = secondPairFromOther3HullEnding1[0]
						corner3 = hullEndsOnVertex(contour, defects1[(lastNonPotential+4)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(lastNonPotential+5)%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(lastNonPotential)%dSize][2], ydim, "before")
						
						if len(tempBeforeCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, defects1[(lastNonPotential+5)%dSize][3], tempAfterCorner4Hull[0], defects1[(lastNonPotential+5)%dSize][3], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 277yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempBeforeCorner4Hull[0]
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						
						
				else: # outies opposite eachother
					corner1 = hullEndsOnVertex(contour, defects1[(lastNonPotential)%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(lastNonPotential+1)%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(lastNonPotential+3)%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(lastNonPotential+4)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
			
			else: # the 2 nonpotential pairs dont share a defect but they are next to eachother leaving 2 unused defects.
				
				firstPair = []
				secondPair = []
				
				if (nonPotentialOuties[0][1] + 1)%dSize == nonPotentialOuties[1][0]:
					firstPair = nonPotentialOuties[0]
					secondPair = nonPotentialOuties[1]
				elif (nonPotentialOuties[1][1] + 1)%dSize == nonPotentialOuties[0][0]:
					firstPair = nonPotentialOuties[1]
					secondPair = nonPotentialOuties[0]
				
				hullEndingBeforeFirstPair = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
				hullEndingAfterFirstPair = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")
				hullEndingBeforeSecondPair = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")
				hullEndingAfterSecondPair = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")
				
				if (len(hullEndingBeforeFirstPair) != 0 and len(hullEndingAfterFirstPair) != 0 and abs(hullEndingBeforeFirstPair[0] - hullEndingAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin) or (len(hullEndingBeforeSecondPair) != 0 and len(hullEndingAfterSecondPair) != 0 and abs(hullEndingBeforeSecondPair[0] - hullEndingAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin): #outies next to eachother and one nonpotential is the main join
					if (len(hullEndingBeforeFirstPair) != 0 and len(hullEndingAfterFirstPair) != 0 and abs(hullEndingBeforeFirstPair[0] - hullEndingAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin):
						corner1 = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")[0]
						corner2 = hullEndingBeforeFirstPair[0]
						corner3 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][2], ydim, "before")
						
						if len(tempBeforeCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, defects1[(secondPair[1])%dSize][3], tempAfterCorner4Hull[0], defects1[(secondPair[1])%dSize][3], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 277yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempBeforeCorner4Hull[0]
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						
						
					elif (len(hullEndingBeforeSecondPair) != 0 and len(hullEndingAfterSecondPair) != 0 and abs(hullEndingBeforeSecondPair[0] - hullEndingAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin):
						corner1 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")[0]
						corner2 = hullEndingBeforeSecondPair[0]
						corner3 = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(secondPair[1]+2)%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(secondPair[1]+3)%dSize][2], ydim, "before")
						
						if len(tempAfterCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], defects1[(secondPair[1]+3)%dSize][2], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 27yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempAfterCorner4Hull[0]
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
				
				else:
					# just try both of the last 2 scenarios
					#scenario 1 (outies opposite)
					corner1 = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")[0]
					
					tempcorner3 = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][2], ydim, "before")
					tempcorner4 = hullEndsOnVertex(contour, defects1[(secondPair[1]+2)%dSize][3], ydim, "after")
					
					if len(tempcorner3) != 0 and len(tempcorner4) != 0:
						finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, tempcorner3, tempcorner4]])
					
					#scenario 2 (outies next to eachother)
					corner1 = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")[0]
					
					tempcorner2before = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")
					tempcorner2after = hullEndsOnVertex(contour, defects1[(secondPair[1]+2)%dSize][2], ydim, "before")
					if len(tempcorner2before) != 0 and len(tempcorner2after) != 0 and abs(tempcorner2before[0] - tempcorner2after[0]) < hullEndingsAreJoinedIfWithin:
						corner2 = tempcorner2before[0]
						corner3 = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
						
						#this can actually have 2 scenarios of its own
						
						tempcorner4before = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][3], ydim, "after")
						tempcorner4after = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][2], ydim, "before")
						
						if len(tempcorner4before) != 0 and len(tempcorner4after) != 0 and abs(tempcorner4before[0] - tempcorner4after[0]) < hullEndingsAreJoinedIfWithin:
							corner4 = tempcorner4before[0]
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						
						elif len(tempcorner4before) != 0 and len(tempcorner4after) != 0:
							checkCorner = checkCornerOrBigChange(contour, tempcorner4before[0], tempcorner4after[0], tempcorner4before[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
								if corner4 == -1:
									pass
								else:
									finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							else:
								corner4 = tempcorner4before[0]
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
								
								corner4 = tempcorner4after[0]
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
								
						elif len(tempcorner4before) == 0:
							checkCorner = checkCornerOrBigChange(contour, defects1[(firstPair[1])%dSize][3], tempcorner4after[0], defects1[(firstPair[1])%dSize][3], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
								if corner4 == -1:
									pass
								else:
									finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							else:
								corner4 = tempcorner4after[0]
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
								
						elif len(tempcorner4after) == 0:
							checkCorner = checkCornerOrBigChange(contour, tempcorner4before[0], defects1[(secondPair[0])%dSize][2], tempcorner4before[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
								if corner4 == -1:
									pass
								else:
									finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							else:
								corner4 = tempcorner4before[0]
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
		
		elif potentialSize == 3:
			unusedDefectsInNotPotential = []
			for j in range(6):
				isItUsed = False
				for notPotential in nonPotentialOuties:
					if j == notPotential[0] or j == notPotential[1]:
						isItUsed = True
				if isItUsed == False:
					unusedDefectsInNotPotential.append(j)
			
			
			if len(unusedDefectsInNotPotential) == 2: # outies next to eachother and all nonpotential pairs share a defect with another pair
				unusedPair = []
				if unusedDefectsInNotPotential[0] == (unusedDefectsInNotPotential[1]+1)%dSize:
					unusedPair = [unusedDefectsInNotPotential[1], unusedDefectsInNotPotential[0]]
				elif unusedDefectsInNotPotential[1] == (unusedDefectsInNotPotential[0]+1)%dSize:
					unusedPair = [unusedDefectsInNotPotential[0], unusedDefectsInNotPotential[1]]
				else:
					print("error code f9834j")
					return None
				
				corner1 = hullEndsOnVertex(contour, defects1[(unusedPair[0]-1)%dSize][2], ydim, "before")[0]
				corner3 = hullEndsOnVertex(contour, defects1[(unusedPair[1]+1)%dSize][3], ydim, "after")[0]
				
				tempcorner2before = hullEndsOnVertex(contour, defects1[(unusedPair[0])%dSize][3], ydim, "after")
				tempcorner2after = hullEndsOnVertex(contour, defects1[(unusedPair[1])%dSize][2], ydim, "before")
				if len(tempcorner2before) != 0 and len(tempcorner2after) != 0 and abs(tempcorner2before[0] - tempcorner2after[0]) < hullEndingsAreJoinedIfWithin:
					corner2 = tempcorner2before[0]
					
					tempcorner4before = hullEndsOnVertex(contour, defects1[(unusedPair[1]+2)%dSize][3], ydim, "after")
					tempcorner4after = hullEndsOnVertex(contour, defects1[(unusedPair[1]+3)%dSize][2], ydim, "before")
					
					if len(tempcorner4before) != 0 and len(tempcorner4after) != 0 and abs(tempcorner4before[0] - tempcorner4after[0]) < hullEndingsAreJoinedIfWithin:
						corner4 = tempcorner4before[0]
						finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
					elif len(tempcorner4before) != 0 and len(tempcorner4after) != 0:
						checkCorner = checkCornerOrBigChange(contour, tempcorner4before[0], tempcorner4after[0], tempcorner4before[0], ydim)
						if checkCorner[1] == True:
							corner4 = checkCorner[2][0]
							if corner4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						else:
							corner4 = tempcorner4before[0]
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							
							corner4 = tempcorner4after[0]
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							
					elif len(tempcorner4before) == 0 and len(tempcorner4after)!=0:
						
						checkCorner = checkCornerOrBigChange(contour, defects1[(unusedPair[1]+2)%dSize][3], tempcorner4after[0], defects1[(unusedPair[1]+2)%dSize][3], ydim)
						if checkCorner[1] == True:
							corner4 = checkCorner[2][0]
							if corner4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						else:
							corner4 = tempcorner4after[0]
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
							
					elif len(tempcorner4after) == 0 and len(tempcorner4before)!=0:
						checkCorner = checkCornerOrBigChange(contour, tempcorner4before[0], defects1[(unusedPair[1]+3)%dSize][2], tempcorner4before[0], ydim)
						if checkCorner[1] == True:
							corner4 = checkCorner[2][0]
							if corner4 == -1:
								pass
							else:
								finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						else:
							corner4 = tempcorner4before[0]
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
					else:
						print("error code h833r3duj")
						return None
					
				else:
					print("error code h83duj")
					return None
				
				
			elif len(unusedDefectsInNotPotential) == 1: # only 1 nonpotential pair share a defect, peice can be opposite outies or next to eachother outies
				#find pair that isnt sharing any
				alonePair = []
				joinedPair = []
				if nonPotentialOuties[0][1] == nonPotentialOuties[1][0]:
					alonePair = nonPotentialOuties[2]
					joinedPair = [nonPotentialOuties[0], nonPotentialOuties[1]]
				elif nonPotentialOuties[1][1] == nonPotentialOuties[2][0]:
					alonePair = nonPotentialOuties[0]
					joinedPair = [nonPotentialOuties[1], nonPotentialOuties[2]]
				elif nonPotentialOuties[2][1] == nonPotentialOuties[0][0]:
					alonePair = nonPotentialOuties[1]
					joinedPair = [nonPotentialOuties[2], nonPotentialOuties[0]]
				
				tempAlonePairBefore = hullEndsOnVertex(contour, defects1[(alonePair[0])%dSize][3], ydim, "after")
				tempAlonePairAfter = hullEndsOnVertex(contour, defects1[(alonePair[1])%dSize][2], ydim, "before")
				if len(tempAlonePairBefore) != 0 and len(tempAlonePairAfter) != 0 and abs(tempAlonePairBefore[0] - tempAlonePairAfter[0]) < hullEndingsAreJoinedIfWithin: # outies next to eachother
					
					if alonePair[0] == (joinedPair[1][1]+1)%dSize:
						corner1 = hullEndsOnVertex(contour, defects1[(joinedPair[1][1])%dSize][2], ydim, "before")[0]
						corner2 = tempAlonePairBefore[0]
						corner3 = hullEndsOnVertex(contour, defects1[(alonePair[1]+1)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(alonePair[1]+2)%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(alonePair[1]+3)%dSize][2], ydim, "before")
						
						if len(tempAfterCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], defects1[(alonePair[1]+3)%dSize][2], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 27yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempAfterCorner4Hull[0]
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
						
					elif alonePair[0] == (joinedPair[1][1]+2)%dSize:
						corner1 = hullEndsOnVertex(contour, defects1[(joinedPair[1][1]+1)%dSize][2], ydim, "before")[0]
						corner2 = tempAlonePairBefore[0]
						corner3 = hullEndsOnVertex(contour, defects1[(alonePair[1]+1)%dSize][3], ydim, "after")[0]
						corner4 = -1
						
						tempBeforeCorner4Hull = hullEndsOnVertex(contour, defects1[(alonePair[1]+2)%dSize][3], ydim, "after")
						tempAfterCorner4Hull = hullEndsOnVertex(contour, defects1[(alonePair[1]+3)%dSize][2], ydim, "before")
						
						if len(tempBeforeCorner4Hull) == 0:
							checkCorner = checkCornerOrBigChange(contour, defects1[(alonePair[1]+2)%dSize][3], tempAfterCorner4Hull[0], defects1[(alonePair[1]+2)%dSize][3], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								print("error code 277yde")
								return None
						else:
							checkCorner = checkCornerOrBigChange(contour, tempBeforeCorner4Hull[0], tempAfterCorner4Hull[0], tempBeforeCorner4Hull[0], ydim)
							if checkCorner[1] == True:
								corner4 = checkCorner[2][0]
							else:
								corner4 = tempBeforeCorner4Hull[0]
						if corner4 == -1:
							pass
						else:
							finalCorners.append([[(0, 1), (1, 2)], [corner1, corner2, corner3, corner4]])
					
					else:
						print("error code 2i8j82")
						return None
					
					
				else: # outies opposite eachother
					corner1 = hullEndsOnVertex(contour, defects1[(joinedPair[0][0]-1)%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(joinedPair[0][0])%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(joinedPair[1][1])%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(joinedPair[1][1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (2, 3)], [corner1, corner2, corner3, corner4]])
				
			else:
				print("error code 98u3")
				return None
			
		elif potentialSize == 2:
			pass
	
	elif dSize == 7:
		if potentialSize == 7:
			joinsOrNot = []
			for potential in potentialOuties:
				tempBefore = hullEndsOnVertex(contour, defects1[(potential[0])%dSize][3], ydim, "after")
				tempAfter = hullEndsOnVertex(contour, defects1[(potential[1])%dSize][2], ydim, "before")
				
				if len(tempBefore) != 0 and len(tempAfter) != 0 and abs(tempBefore[0] - tempAfter[0]) < hullEndingsAreJoinedIfWithin:
					joinsOrNot.append([potential[0], potential[1], 'J', tempBefore, tempAfter])
				else:
					joinsOrNot.append([potential[0], potential[1], 'N', tempBefore, tempAfter])
			
			for j in range(len(joinsOrNot)):
				if joinsOrNot[j][2] == "N" and joinsOrNot[(j+1)%len(joinsOrNot)][2] == "N" and joinsOrNot[(j+3)%len(joinsOrNot)][2] == "J" and joinsOrNot[(j+5)%len(joinsOrNot)][2] == "J":
					#sanity check
					if (joinsOrNot[j][0]+1)%len(joinsOrNot) == joinsOrNot[(j+1)%len(joinsOrNot)][0] and (joinsOrNot[(j+1)%len(joinsOrNot)][0]+2)%len(joinsOrNot) == joinsOrNot[(j+3)%len(joinsOrNot)][0]:
						corner1 = joinsOrNot[(j+1)%len(joinsOrNot)][4][0]
						corner2 = joinsOrNot[(j+3)%len(joinsOrNot)][3][0]
						corner3 = joinsOrNot[(j+5)%len(joinsOrNot)][3][0]
						corner4 = joinsOrNot[j][3][0]
						finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					else:
						print("error code 28u2eh")
						return None
		
		elif potentialSize == 6:
			tempBefore = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][3], ydim, "after")
			tempAfter = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")
			if len(tempBefore) != 0 and len(tempAfter) != 0 and abs(tempBefore[0] - tempAfter[0]) < hullEndingsAreJoinedIfWithin: # nonpotential joins
				pairBefore = []
				pairAfter = []
				
				for potential in potentialOuties:
					if (potential[1]+1)%dSize == nonPotentialOuties[0][0]:
						pairBefore = potential
					elif (potential[0]-1)%dSize == nonPotentialOuties[0][1]:
						pairAfter = potential
				
				hullBeforePairBefore = hullEndsOnVertex(contour, defects1[(pairBefore[0])%dSize][3], ydim, "after")
				hullAfterPairBefore = hullEndsOnVertex(contour, defects1[(pairBefore[1])%dSize][2], ydim, "before")
				hullBeforePairAfter = hullEndsOnVertex(contour, defects1[(pairAfter[0])%dSize][3], ydim, "after")
				hullAfterPairAfter = hullEndsOnVertex(contour, defects1[(pairAfter[1])%dSize][2], ydim, "before")
				
				if len(hullBeforePairBefore) != 0 and len(hullAfterPairBefore) != 0 and abs(hullBeforePairBefore[0] - hullAfterPairBefore[0]) < hullEndingsAreJoinedIfWithin:
					corner1 = hullEndsOnVertex(contour, defects1[(pairAfter[1]+1)%dSize][2], ydim, "before")[0]
					corner2 = hullBeforePairBefore[0]
					corner3 = tempBefore[0]
					corner4 = hullBeforePairAfter[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
					
				elif len(hullBeforePairAfter) != 0 and len(hullAfterPairAfter) != 0 and abs(hullBeforePairAfter[0] - hullAfterPairAfter[0]) < hullEndingsAreJoinedIfWithin:
					corner1 = hullAfterPairBefore[0]
					corner2 = tempBefore[0]
					corner3 = hullBeforePairAfter[0]
					corner4 = hullEndsOnVertex(contour, defects1[(pairAfter[1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
					
				else:
					print("error code 83h")
					return None
				
				
			elif len(tempBefore) != 0 and len(tempAfter) != 0: # nonpotential doesnt join
				twoPairsAfter = []
				twoPairsBefore = []
				tempTwoPairsAfter = []
				tempTwoPairsBefore = []
				
				for potential in potentialOuties:
					if (potential[0])%dSize == (nonPotentialOuties[0][1]+1)%dSize:
						tempTwoPairsAfter.append(potential)
					if (potential[0])%dSize == (nonPotentialOuties[0][1]+3)%dSize:
						tempTwoPairsAfter.append(potential)
					if (potential[1])%dSize == (nonPotentialOuties[0][0]-1)%dSize:
						tempTwoPairsBefore.append(potential)
					if (potential[1])%dSize == (nonPotentialOuties[0][0]-3)%dSize:
						tempTwoPairsBefore.append(potential)
				
				if len(tempTwoPairsAfter) == 2 and len(tempTwoPairsBefore) == 2:
					if (tempTwoPairsAfter[0][1] + 1)%dSize == tempTwoPairsAfter[1][0]:
						twoPairsAfter.append(tempTwoPairsAfter[0])
						twoPairsAfter.append(tempTwoPairsAfter[1])
					elif (tempTwoPairsAfter[1][1] + 1)%dSize == tempTwoPairsAfter[0][0]:
						twoPairsAfter.append(tempTwoPairsAfter[1])
						twoPairsAfter.append(tempTwoPairsAfter[0])
					if (tempTwoPairsBefore[0][1] + 1)%dSize == tempTwoPairsBefore[1][0]:
						twoPairsBefore.append(tempTwoPairsBefore[0])
						twoPairsBefore.append(tempTwoPairsBefore[1])
					elif (tempTwoPairsBefore[1][1] + 1)%dSize == tempTwoPairsBefore[0][0]:
						twoPairsBefore.append(tempTwoPairsBefore[1])
						twoPairsBefore.append(tempTwoPairsBefore[0])
					
					#check if both pairs AFTER both join
					hullBeforeFirstPair = hullEndsOnVertex(contour, defects1[(twoPairsAfter[0][0])%dSize][3], ydim, "after")
					hullAfterFirstPair = hullEndsOnVertex(contour, defects1[(twoPairsAfter[0][1])%dSize][2], ydim, "before")
					hullBeforeSecondPair = hullEndsOnVertex(contour, defects1[(twoPairsAfter[1][0])%dSize][3], ydim, "after")
					hullAfterSecondPair = hullEndsOnVertex(contour, defects1[(twoPairsAfter[1][1])%dSize][2], ydim, "before")
					
					if len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin and len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
						corner1 = tempAfter[0]
						corner2 = hullBeforeFirstPair[0]
						corner3 = hullBeforeSecondPair[0]
						corner4 = hullEndsOnVertex(contour, defects1[(twoPairsAfter[1][1]+1)%dSize][3], ydim, "after")[0]
						finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
					
					#check if both pairs BEFORE both join
					
					hullBeforeFirstPair = hullEndsOnVertex(contour, defects1[(twoPairsBefore[0][0])%dSize][3], ydim, "after")
					hullAfterFirstPair = hullEndsOnVertex(contour, defects1[(twoPairsBefore[0][1])%dSize][2], ydim, "before")
					hullBeforeSecondPair = hullEndsOnVertex(contour, defects1[(twoPairsBefore[1][0])%dSize][3], ydim, "after")
					hullAfterSecondPair = hullEndsOnVertex(contour, defects1[(twoPairsBefore[1][1])%dSize][2], ydim, "before")
					
					if len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin and len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
						corner1 = hullEndsOnVertex(contour, defects1[(twoPairsBefore[0][0]-1)%dSize][2], ydim, "before")[0]
						corner2 = hullBeforeFirstPair[0]
						corner3 = hullBeforeSecondPair[0]
						corner4 = tempBefore[0]
						finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
				else:
					print("error code 82eupd")
					return None
				
			else:
				print("error code 829ju")
				return None
		elif potentialSize == 5:
			if nonPotentialOuties[0][1] == nonPotentialOuties[1][0] or nonPotentialOuties[1][1] == nonPotentialOuties[0][0]: # share a defect
				if nonPotentialOuties[0][1] == nonPotentialOuties[1][0]:
					corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+1)%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+4)%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1]+5)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
				elif nonPotentialOuties[1][1] == nonPotentialOuties[0][0]:
					corner1 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+1)%dSize][3], ydim, "after")[0]
					corner3 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+4)%dSize][2], ydim, "before")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1]+5)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
			elif (nonPotentialOuties[0][1]+1)%dSize == nonPotentialOuties[1][0] or (nonPotentialOuties[1][1]+1)%dSize == nonPotentialOuties[0][0]:
				firstPair = []
				secondPair = []
				if (nonPotentialOuties[0][1]+1)%dSize == nonPotentialOuties[1][0]:
					firstPair = nonPotentialOuties[0]
					secondPair = nonPotentialOuties[1]
				elif (nonPotentialOuties[1][1]+1)%dSize == nonPotentialOuties[0][0]:
					firstPair = nonPotentialOuties[1]
					secondPair = nonPotentialOuties[0]
				
				hullBeforeFirstPair = hullEndsOnVertex(contour, defects1[(firstPair[0])%dSize][3], ydim, "after")
				hullAfterFirstPair = hullEndsOnVertex(contour, defects1[(firstPair[1])%dSize][2], ydim, "before")
				hullBeforeSecondPair = hullEndsOnVertex(contour, defects1[(secondPair[0])%dSize][3], ydim, "after")
				hullAfterSecondPair = hullEndsOnVertex(contour, defects1[(secondPair[1])%dSize][2], ydim, "before")
				
				if len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin and len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
					corner1 = hullEndsOnVertex(contour, defects1[(firstPair[0]-1)%dSize][2], ydim, "before")[0]
					corner2 = hullBeforeFirstPair[0]
					corner3 = hullBeforeSecondPair[0]
					corner4 = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
				elif len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin:
					corner1 = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][2], ydim, "before")[0]
					corner2 = hullEndsOnVertex(contour, defects1[(secondPair[1]+2)%dSize][3], ydim, "after")[0]
					corner3 = hullBeforeFirstPair[0]
					corner4 = hullBeforeSecondPair[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
				elif len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
					corner1 = hullAfterFirstPair[0]
					corner2 = hullBeforeSecondPair[0]
					corner3 = hullEndsOnVertex(contour, defects1[(secondPair[1]+1)%dSize][3], ydim, "after")[0]
					corner4 = hullEndsOnVertex(contour, defects1[(secondPair[1]+3)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
				else:
					print("error code 1298u")
					return None
			
			else: # pairs not sharing any and not next to eachother
				mainJoin = []
				otherPair = []
				
				hullBeforeFirstPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][3], ydim, "after")
				hullAfterFirstPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")
				hullBeforeSecondPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][0])%dSize][3], ydim, "after")
				hullAfterSecondPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][2], ydim, "before")
				
				if len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin:
					mainJoin = [nonPotentialOuties[0][0],nonPotentialOuties[0][1],hullBeforeFirstPair,hullAfterFirstPair]
					otherPair = [nonPotentialOuties[1][0],nonPotentialOuties[1][1],hullBeforeSecondPair,hullAfterSecondPair]
				elif len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
					mainJoin = [nonPotentialOuties[1][0],nonPotentialOuties[1][1],hullBeforeSecondPair,hullAfterSecondPair]
					otherPair = [nonPotentialOuties[0][0],nonPotentialOuties[0][1],hullBeforeFirstPair,hullAfterFirstPair]
				else:
					print("code 9fj03")
					return None
				
				if (mainJoin[1]+3)%dSize == otherPair[0]:
					corner1 = hullEndsOnVertex(contour, defects1[(mainJoin[0]-1)%dSize][2], ydim, "before")[0]
					corner2 = mainJoin[2][0]
					corner3 = hullEndsOnVertex(contour, defects1[(mainJoin[1]+1)%dSize][3], ydim, "after")[0]
					corner4 = otherPair[2][0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
				elif (mainJoin[1]+2)%dSize == otherPair[0]:
					corner1 = otherPair[3][0]
					corner2 = hullEndsOnVertex(contour, defects1[(otherPair[1]+1)%dSize][3], ydim, "after")[0]
					corner3 = mainJoin[2][0]
					corner4 = hullEndsOnVertex(contour, defects1[(mainJoin[1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
				else:
					print("code 923j03")
					return None
		
		elif potentialSize == 4:
			if nonPotentialOuties[0][1] == nonPotentialOuties[1][0] or nonPotentialOuties[1][1] == nonPotentialOuties[2][0] or nonPotentialOuties[2][1] == nonPotentialOuties[0][0]: # 2 pairs share defect and 1 on its own
				sharingPairs = []
				bugChecker = 0
				if nonPotentialOuties[0][1] == nonPotentialOuties[1][0]:
					bugChecker += 1
					sharingPairs = [nonPotentialOuties[0], nonPotentialOuties[1]]
					
				if nonPotentialOuties[1][1] == nonPotentialOuties[2][0]:
					bugChecker += 1
					sharingPairs = [nonPotentialOuties[1], nonPotentialOuties[2]]
					
				if nonPotentialOuties[2][1] == nonPotentialOuties[0][0]:
					bugChecker += 1
					sharingPairs = [nonPotentialOuties[2], nonPotentialOuties[0]]
					
				if bugChecker != 1:
					print("error code 84f3j")
					return None
				
				corner1 = hullEndsOnVertex(contour, defects1[(sharingPairs[1][1])%dSize][2], ydim, "before")[0]
				corner2 = hullEndsOnVertex(contour, defects1[(sharingPairs[1][1]+1)%dSize][3], ydim, "after")[0]
				corner3 = hullEndsOnVertex(contour, defects1[(sharingPairs[1][1]+4)%dSize][2], ydim, "before")[0]
				corner4 = hullEndsOnVertex(contour, defects1[(sharingPairs[1][1]+5)%dSize][3], ydim, "after")[0]
				finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
				
			else: # all pairs share none
				tempJoins = []
				
				hullBeforeFirstPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][0])%dSize][3], ydim, "after")
				hullAfterFirstPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[0][1])%dSize][2], ydim, "before")
				hullBeforeSecondPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][0])%dSize][3], ydim, "after")
				hullAfterSecondPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[1][1])%dSize][2], ydim, "before")
				hullBeforeThirdPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[2][0])%dSize][3], ydim, "after")
				hullAfterThirdPair = hullEndsOnVertex(contour, defects1[(nonPotentialOuties[2][1])%dSize][2], ydim, "before")
				
				if len(hullBeforeFirstPair) != 0 and len(hullAfterFirstPair) != 0 and abs(hullBeforeFirstPair[0] - hullAfterFirstPair[0]) < hullEndingsAreJoinedIfWithin:
					tempJoins.append([nonPotentialOuties[0][0],nonPotentialOuties[0][1],hullBeforeFirstPair,hullAfterFirstPair])
				if len(hullBeforeSecondPair) != 0 and len(hullAfterSecondPair) != 0 and abs(hullBeforeSecondPair[0] - hullAfterSecondPair[0]) < hullEndingsAreJoinedIfWithin:
					tempJoins.append([nonPotentialOuties[1][0],nonPotentialOuties[1][1],hullBeforeSecondPair,hullAfterSecondPair])
				if len(hullBeforeThirdPair) != 0 and len(hullAfterThirdPair) != 0 and abs(hullBeforeThirdPair[0] - hullAfterThirdPair[0]) < hullEndingsAreJoinedIfWithin:
					tempJoins.append([nonPotentialOuties[2][0],nonPotentialOuties[2][1],hullBeforeThirdPair,hullAfterThirdPair])
				
				if len(tempJoins) == 2:
					mainJoins = []
					if tempJoins[0][1] == tempJoins[1][0]:
						mainJoins.append(tempJoins[0])
						mainJoins.append(tempJoins[1])
					elif tempJoins[1][1] == tempJoins[0][0]:
						mainJoins.append(tempJoins[1])
						mainJoins.append(tempJoins[0])
					else:
						print("error code 8233ejp")
						return None
					
					corner1 = hullEndsOnVertex(contour, defects1[(mainJoins[0][0]-1)%dSize][2], ydim, "before")[0]
					corner2 = mainJoins[0][2][0]
					corner3 = mainJoins[1][2][0]
					corner4 = hullEndsOnVertex(contour, defects1[(mainJoins[1][1]+1)%dSize][3], ydim, "after")[0]
					finalCorners.append([[(0, 1), (1, 2), (2, 3)], [corner1, corner2, corner3, corner4]])
					
				else:
					print("error code 83ejp")
					return None
				
	
	elif dSize == 8:
		if potentialSize <= 7 and potentialSize > 4:
			
			orderedPotentialOuties = [potentialOuties[0]]
			remainingPotOut = []
			for potOutie in potentialOuties[1:]:
				if (potentialOuties[0][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
				else:
					remainingPotOut.append(potOutie)
			if len(orderedPotentialOuties) == 2:
				nextPotOut = None
				for potOutie in remainingPotOut:
					if (orderedPotentialOuties[1][1]+1)%dSize == potOutie[0]:
						orderedPotentialOuties.append(potOutie)
						nextPotOut = potOutie
				if nextPotOut is not None:
					remainingPotOut.remove(nextPotOut)
				if len(orderedPotentialOuties) == 3: #(separated from above for readability)
					nextPotOut = None
					for potOutie in remainingPotOut:
						if (orderedPotentialOuties[2][1]+1)%dSize == potOutie[0]:
							orderedPotentialOuties.append(potOutie)
							nextPotOut = potOutie
					if nextPotOut is not None:
						remainingPotOut.remove(nextPotOut)
					if len(orderedPotentialOuties) == 4: #(separated from above for readability)
					
						corner1 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
						corner2 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
						corner3 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
						corner4 = defectDicts[orderedPotentialOuties[3][1]]["after"][0]
						finalCorners.append([[(0, 1), (1, 2), (2, 3), (3, 0)], [corner1, corner2, corner3, corner4]])
						return finalCorners
			#arrive here if on wrong set of potentials, need to shift to correct set of potentials that are next to eachother without sharing defects
			correctStarter = None
			for potOutie in potentialOuties[1:]:
				if (potentialOuties[0][1])%dSize == potOutie[0]: #not potentialOuties[0][1]+1
					correctStarter = potOutie
					break
			
			orderedPotentialOuties = [correctStarter]
			remainingPotOut = []
			for potOutie in potentialOuties:
				if potOutie == correctStarter:
					pass
				elif (correctStarter[1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
				else:
					remainingPotOut.append(potOutie)
			nextPotOut = None
			if len(orderedPotentialOuties) == 2:
				for potOutie in remainingPotOut:
					if (orderedPotentialOuties[1][1]+1)%dSize == potOutie[0]:
						orderedPotentialOuties.append(potOutie)
						nextPotOut = potOutie
				remainingPotOut.remove(nextPotOut)
				
				nextPotOut = None
				if len(orderedPotentialOuties) == 3:
					for potOutie in remainingPotOut:
						if (orderedPotentialOuties[2][1]+1)%dSize == potOutie[0]:
							orderedPotentialOuties.append(potOutie)
							nextPotOut = potOutie
					remainingPotOut.remove(nextPotOut)
					if len(orderedPotentialOuties) == 4:
						corner1 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
						corner2 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
						corner3 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
						corner4 = defectDicts[orderedPotentialOuties[3][1]]["after"][0]
						finalCorners.append([[(0, 1), (1, 2), (2, 3), (3, 0)], [corner1, corner2, corner3, corner4]])
						return finalCorners
			
			
		elif potentialSize == 8:
			#all 2 cases
			
			orderedPotentialOuties = [potentialOuties[0]]
			remainingPotOut = []
			for potOutie in potentialOuties[1:]:
				if (potentialOuties[0][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
				else:
					remainingPotOut.append(potOutie)
			nextPotOut = None
			for potOutie in remainingPotOut:
				if (orderedPotentialOuties[1][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
					nextPotOut = potOutie
			remainingPotOut.remove(nextPotOut)
			
			nextPotOut = None
			for potOutie in remainingPotOut:
				if (orderedPotentialOuties[2][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
					nextPotOut = potOutie
			remainingPotOut.remove(nextPotOut)
			
			if not (len(orderedPotentialOuties) == 4 and len(remainingPotOut) == 4):
				print("this probably shouldnt happen 129")
				return None
			
			corner1 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
			corner2 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
			corner3 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
			corner4 = defectDicts[orderedPotentialOuties[3][1]]["after"][0]
			finalCorners.append([[(0, 1), (1, 2), (2, 3), (3, 0)], [corner1, corner2, corner3, corner4]])
			
			orderedPotentialOuties = [remainingPotOut[0]]
			remainingPotOut2 = []
			for potOutie in remainingPotOut[1:]:
				if (remainingPotOut[0][1]+1)%dSize == potOutie[0]:
					orderedPotentialOuties.append(potOutie)
				else:
					remainingPotOut2.append(potOutie)
			if not (len(remainingPotOut2) == 2 and len(orderedPotentialOuties) == 2):
				print("this should literally never happen ever2")
				return None
			
			if (orderedPotentialOuties[1][1]+1)%dSize == remainingPotOut2[0][0]:
				orderedPotentialOuties.append(remainingPotOut2[0])
				orderedPotentialOuties.append(remainingPotOut2[1])
			elif (orderedPotentialOuties[1][1]+1)%dSize == remainingPotOut2[1][0]:
				orderedPotentialOuties.append(remainingPotOut2[1])
				orderedPotentialOuties.append(remainingPotOut2[0])
			else:
				print("wat4g4g32j")
				return None
			
			corner1 = defectDicts[orderedPotentialOuties[0][1]]["after"][0]
			corner2 = defectDicts[orderedPotentialOuties[1][1]]["after"][0]
			corner3 = defectDicts[orderedPotentialOuties[2][1]]["after"][0]
			corner4 = defectDicts[orderedPotentialOuties[3][1]]["after"][0]
			finalCorners.append([[(0, 1), (1, 2), (2, 3), (3, 0)], [corner1, corner2, corner3, corner4]])
			return finalCorners
			
		else:
			print("defunct piece")
			return None
			
	return finalCorners

def edgeDefectsFixer(defects, start, end, innieOrOutie, contourSize):
	newDefects = []
	if start <= end:
		for defectInd in defects:
			if defectInd[0] >= start and defectInd[0] < end:
				newDefects.append([defectInd[0]-start, defectInd[1]])
			
	elif start > end:
		for defectInd in defects:
			if defectInd[0] >= start:
				newDefects.append([defectInd[0]-start, defectInd[1]])
			elif defectInd[0] < end:
				newDefects.append([contourSize-start+defectInd[0], defectInd[1]])
	
	if len(newDefects) != 0 and ((innieOrOutie=="outie" and len(newDefects)==2) or (innieOrOutie=="innie" and len(newDefects)==1)):
		return newDefects
	else:
		print("edgeDefectsFixer error")
		return None


def prepareConvexMethodEdges(contour, convexMethodCornerData, defects, centreImgPt, referenceCntrArea):
	
	puzzleData = []
	for potentialArrangement in convexMethodCornerData:
		bugChecker = False
		potentialArrangementCornerLength = len(potentialArrangement[1])
		if potentialArrangementCornerLength != 4:
			bugChecker = True
		for i in range(potentialArrangementCornerLength):
			if potentialArrangement[1][i] == -1:
				bugChecker = True
			if abs(potentialArrangement[1][i] - potentialArrangement[1][(i+1)%potentialArrangementCornerLength]) < 3:
				bugChecker = True
			
		
		if bugChecker == False:
			topEdgeData = None
			bottomEdgeData = None
			leftEdgeData = None
			rightEdgeData = None
			
			topDefects = None
			bottomDefects = None
			leftDefects = None
			rightDefects = None
			
			for tmpCoordI in range(contour.shape[0]-1):
				if contour[tmpCoordI][0][0]==contour[tmpCoordI+1][0][0] and contour[tmpCoordI][0][1]==contour[tmpCoordI+1][0][1]:
					print('?????????????????????ddddd???22')
					exit()
			
			contSize = contour.shape[0]
			if (0, 1) in potentialArrangement[0]:
				topEdgeData = [betterSlice(contour, potentialArrangement[1][0], (potentialArrangement[1][1]+1)%contour.shape[0]), "outie", (potentialArrangement[1][0], (potentialArrangement[1][1]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				topDefects = edgeDefectsFixer(defects, potentialArrangement[1][0], potentialArrangement[1][1], "outie", contSize)
			else:
				topEdgeData = [betterSlice(contour, potentialArrangement[1][0], (potentialArrangement[1][1]+1)%contour.shape[0]), "innie", (potentialArrangement[1][0], (potentialArrangement[1][1]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				topDefects = edgeDefectsFixer(defects, potentialArrangement[1][0], potentialArrangement[1][1], "innie", contSize)
			
			if (1, 2) in potentialArrangement[0]:
				rightEdgeData = [betterSlice(contour, potentialArrangement[1][1], (potentialArrangement[1][2]+1)%contour.shape[0]), "outie", (potentialArrangement[1][1], (potentialArrangement[1][2]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				rightDefects = edgeDefectsFixer(defects, potentialArrangement[1][1], potentialArrangement[1][2], "outie", contSize)
			else:
				rightEdgeData = [betterSlice(contour, potentialArrangement[1][1], (potentialArrangement[1][2]+1)%contour.shape[0]), "innie", (potentialArrangement[1][1], (potentialArrangement[1][2]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				rightDefects = edgeDefectsFixer(defects, potentialArrangement[1][1], potentialArrangement[1][2], "innie", contSize)
			if (2, 3) in potentialArrangement[0]:
				bottomEdgeData = [betterSlice(contour, potentialArrangement[1][2], (potentialArrangement[1][3]+1)%contour.shape[0]), "outie", (potentialArrangement[1][2], (potentialArrangement[1][3]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				bottomDefects = edgeDefectsFixer(defects, potentialArrangement[1][2], potentialArrangement[1][3], "outie", contSize)
			else:
				bottomEdgeData = [betterSlice(contour, potentialArrangement[1][2], (potentialArrangement[1][3]+1)%contour.shape[0]), "innie", (potentialArrangement[1][2], (potentialArrangement[1][3]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				bottomDefects = edgeDefectsFixer(defects, potentialArrangement[1][2], potentialArrangement[1][3], "innie", contSize)
			if (3, 0) in potentialArrangement[0]:
				leftEdgeData = [betterSlice(contour, potentialArrangement[1][3], (potentialArrangement[1][0]+1)%contour.shape[0]), "outie", (potentialArrangement[1][3], (potentialArrangement[1][0]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				leftDefects = edgeDefectsFixer(defects, potentialArrangement[1][3], potentialArrangement[1][0], "outie", contSize)
			else:
				leftEdgeData = [betterSlice(contour, potentialArrangement[1][3], (potentialArrangement[1][0]+1)%contour.shape[0]), "innie", (potentialArrangement[1][3], (potentialArrangement[1][0]+1)%contour.shape[0]), [centreImgPt[0], centreImgPt[1]], referenceCntrArea]
				leftDefects = edgeDefectsFixer(defects, potentialArrangement[1][3], potentialArrangement[1][0], "innie", contSize)
			
			if topEdgeData is None or leftEdgeData is None or bottomEdgeData is None or rightEdgeData is None or topDefects is None or rightDefects is None or bottomDefects is None or leftDefects is None:
				pass
			else:
				for item in [topEdgeData, leftEdgeData, bottomEdgeData, rightEdgeData]:
					for tmpCoordI in range(item[0].shape[0]-1):
						if item[0][tmpCoordI][0][0]==item[0][tmpCoordI+1][0][0] and item[0][tmpCoordI][0][1]==item[0][tmpCoordI+1][0][1]:
							print('???????????????fffff?ddddd???22')
							exit()
				
				tempPuzzleData = {
					"contour": contour,
					"topEdge": topEdgeData,
					"leftEdge": leftEdgeData,
					"bottomEdge": bottomEdgeData,
					"rightEdge": rightEdgeData,
					"topDefects": topDefects,
					"rightDefects": rightDefects,
					"bottomDefects": bottomDefects,
					"leftDefects": leftDefects,
				}
				
				
				puzzleData.append(tempPuzzleData)
		
		else:
			pass
		
	if len(puzzleData) > 0:
		return puzzleData
	else:
		print("dj38j")
		return None

debugCounter = 0
def convexMethod(contour, ydim, onlyDefects=False, skipDefects=None, tempdebug=False):
	global debugCounter
	debugCounter+=1
	# print("DEBUG COUNTER CONVEXMETHOD ----------  "+str(debugCounter))
	# if contour[0][0][0]>730 and contour[0][0][1]>750:
	# if contour[0][0][1]<575 and contour[0][0][1]>565:
		# input(contour[0])
	
	minRealDefectDistance = 8
	
	contour1 = copy.deepcopy(contour)

	actualdebug=False
	# if debugCounter==25:
		# actualdebug=True
	
	
	hull, flipped = myConvexHull(contour1)
	
	monotone = True
	decreasing = False
	if onlyDefects == False:
		if len(hull) >= 4: # at least a triangle, first and last dupe e.g. 2,1,0,2	or	2,0,1,2
			if hull[1] > hull[2]:
				decreasing=True
				for i in range(1, len(hull)-2):
					if hull[i] < hull[i+1]:
						monotone=False
						break
			else:
				for i in range(1, len(hull)-2):
					if hull[i] > hull[i+1]:
						monotone=False
						break
		else:
			return None, None # not handling right now and should never happen, nub would need look like a triangle corner
		
		if not(monotone) or hull[0] != hull[-1]:
			print("weird convex hull, check")
			return None, None
		
		# remove the dupe at [0] or [-1] such that the result is fully monotone
		if not(decreasing):
			if hull[0] > hull[1]: # hull: 2,0,1,2
				hull = hull[1:]
			elif hull[-1] < hull[-2]: # hull: 0,1,2,0 # dont think this actually happens but just covering all bases
				hull = hull[:-1]
		elif decreasing:
			if hull[0] < hull[1]: # hull: 0,2,1,0 
				hull = hull[1:]
			elif hull[-1] > hull[-2]: # hull: 2,1,0,2 # dont think this actually happens but just covering all bases
				hull = hull[:-1]
	
	
	if flipped:
		for i in range(len(hull)):
			hull[i] = contour1.shape[0]-1 - hull[i]
	
	tempHull = []
	if onlyDefects == False:
		if hull[1] > hull[2]:
			for ind1 in hull:
				tempHull.insert(0, [ind1])
		else:
			for ind1 in hull:
				tempHull.append([ind1])
		
		# double check, should be impossible not to be monotonically increasing but check anyway
		for i in range(len(tempHull)-1):
			if tempHull[i][0] >= tempHull[i+1][0]:
				print("?????? uifehw1r92")
				exit()
	else:
		for ind1 in hull[1:]:
			tempHull.append([ind1])
	
	hull = np.asarray(tempHull)
	
	defects1 = []
	
	for i in range(hull.shape[0]):
		radiusAroundPointToCheckInitially = 1
		
		maxdist = 0
		maxDefectIndex = 0
		swapHullInd = False
		
		hullMin = None
		hullMax = None
		
		if i != hull.shape[0]-1 or onlyDefects: # if onlyDefects == True i.e. contour is open, then even in the case that at the end of the contour it jumps from around len(contour) to around 0, we still want to iterate and calc dists to every point from the lower index to the higher one, only when contour is closed do we want to just iterate from higher index to len(contour) then from 0 to lower index
			hullMin = min(hull[(i+1)%hull.shape[0]][0], hull[i][0])
			hullMax = max(hull[(i+1)%hull.shape[0]][0], hull[i][0])
		else: # hull list is always monotone increasing in this case since closed contour and crange will iterate from hullMin to end of contour then from start of contour to hullMax
			hullMin = hull[i][0]
			hullMax = hull[0][0]
		
		hullSegEnd1 = contour1[hullMin][0]
		hullSegEnd2 = contour1[hullMax][0]
		
		formulaA = hullSegEnd2[1] - hullSegEnd1[1]
		formulaB = hullSegEnd2[0] - hullSegEnd1[0]
		formulaC = hullSegEnd2[0] * hullSegEnd1[1] - hullSegEnd2[1] * hullSegEnd1[0]
		formulaD = math.sqrt((hullSegEnd2[1] - hullSegEnd1[1])*(hullSegEnd2[1] - hullSegEnd1[1]) + (hullSegEnd2[0] - hullSegEnd1[0])*(hullSegEnd2[0] - hullSegEnd1[0]))
		
		#new
		largestSecondaryMinimaDistToLine=0
		
		secondaryMinimaProvenUntil = 0
		largestMaximaNeighbourhood = 0
		
		largestSecondaryMinimaIndex = 0
		largestMaximaIndex = 0
		

		lowerBoundStartChkr = (hullMin + radiusAroundPointToCheckInitially)%contour1.shape[0]
		upperBoundStartChkr = (hullMax - radiusAroundPointToCheckInitially)%contour1.shape[0]
			
		thereIsAnotherLocalMinima = False
		thereIsAnotherLocalMaxima = False
		
		
		#had to just do this seperately anyway because we need to know what global min is so we dont check it because we need second largest neighbourhood minima
		for j in crange(hullMin, hullMax+1, contour1.shape[0]):
			distToLine = distPointToLine(contour1[j][0], formulaA, formulaB, formulaC, formulaD)
			if distToLine > maxdist:
				maxdist = distToLine
				maxDefectIndex = j
		
		# this should skip the current hull segment if onlyDefects==True AND this is the same hull segment as the one containing the defects we ended up using for this innie/outie
		passOrNah = False
		if onlyDefects==True:
			
			if hullMin < hullMax:
				for skipDefect in skipDefects:
					if skipDefect[0] >= hullMin and skipDefect[0] <=hullMax and abs(distPointToLine(contour1[skipDefect[0]][0], formulaA, formulaB, formulaC, formulaD) - skipDefect[1])/max(distPointToLine(contour1[skipDefect[0]][0], formulaA, formulaB, formulaC, formulaD), skipDefect[1]) < 0.2:
						passOrNah=True
			else:
				for skipDefect in skipDefects:
					if (skipDefect[0] >= hullMin or skipDefect[0] <=hullMax) and abs(distPointToLine(contour1[skipDefect[0]][0], formulaA, formulaB, formulaC, formulaD) - skipDefect[1])/max(distPointToLine(contour1[skipDefect[0]][0], formulaA, formulaB, formulaC, formulaD), skipDefect[1]) < 0.2:
						passOrNah=True
		
		if passOrNah == False:
			
			for j in crange(hullMin, hullMax+1, contour1.shape[0]):
				
				if lessOrGreat(j, lowerBoundStartChkr, contour1.shape[0], hullMin, hullMax)==1 and lessOrGreat(j, upperBoundStartChkr, contour1.shape[0], hullMin, hullMax)==-1:
					distToLine = distPointToLine(contour1[j][0], formulaA, formulaB, formulaC, formulaD)
					distToLineLowChkr = distPointToLine(contour1[(j-radiusAroundPointToCheckInitially)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD)
					distToLineHighChkr = distPointToLine(contour1[(j+radiusAroundPointToCheckInitially)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD)
					
					if distToLineLowChkr >= distToLine and distToLineHighChkr >= distToLine:
						#local maxima
						
						if thereIsAnotherLocalMaxima == True:
							#first check if it even contends with current best
							doesContend = False
							if largestMaximaNeighbourhood == radiusAroundPointToCheckInitially:
								doesContend = True
							else:
								for k in range(radiusAroundPointToCheckInitially, largestMaximaNeighbourhood+1):
									if distPointToLine(contour1[j-k][0], formulaA, formulaB, formulaC, formulaD) < distToLine or distPointToLine(contour1[(j+k)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) < distToLine:
										break
									if k == largestMaximaNeighbourhood:
										doesContend = True
							if doesContend == True:
								#choose the one where the perimeter between it and any point that is higher is bigger
								for k in range(max(j-hullMin, hullMax+1-j)): #we wont check past the edge of the hull segment
									if distPointToLine(contour1[j-largestMaximaNeighbourhood-k][0], formulaA, formulaB, formulaC, formulaD) < distToLine or distPointToLine(contour1[(j+largestMaximaNeighbourhood+k)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) < distToLine:
										#the new prospect failed to beat the original
										if distPointToLine(contour1[largestMaximaIndex-largestMaximaNeighbourhood-k][0], formulaA, formulaB, formulaC, formulaD) < distToLine or distPointToLine(contour1[(largestMaximaIndex+largestMaximaNeighbourhood+k)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) < distToLine:
											#they actually tied so just keep original and update neighbourhood
											largestMaximaNeighbourhood = largestMaximaNeighbourhood + k - 1
											break
										else:
											largestMaximaNeighbourhood = largestMaximaNeighbourhood + k
											break
										
									if distPointToLine(contour1[largestMaximaIndex-largestMaximaNeighbourhood-k][0], formulaA, formulaB, formulaC, formulaD) < distToLine or distPointToLine(contour1[(largestMaximaIndex+largestMaximaNeighbourhood+k)%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) < distToLine:
										#the original lost
										largestMaximaIndex = j
										largestMaximaNeighbourhood = largestMaximaNeighbourhood+k
										break
									
						elif thereIsAnotherLocalMaxima == False:
							largestMaximaIndex = j
							largestMaximaNeighbourhood = radiusAroundPointToCheckInitially
							thereIsAnotherLocalMaxima = True
					
					elif distToLineLowChkr <= distToLine and distToLineHighChkr <= distToLine:
						
						if lessOrGreat(maxDefectIndex, j+secondaryMinimaProvenUntil, contour1.shape[0], hullMin, hullMax)==1 or lessOrGreat(maxDefectIndex, j-secondaryMinimaProvenUntil, contour1.shape[0], hullMin, hullMax)==-1:
							
							#we only care if the point isnt the global min and if global min isnt in radius because global min will have max neighbourhood
							if thereIsAnotherLocalMinima == True:
								#first check if it even contends with current best
								doesContend = False
								if secondaryMinimaProvenUntil == radiusAroundPointToCheckInitially:
									doesContend = True
								else:
									for k in range(radiusAroundPointToCheckInitially, secondaryMinimaProvenUntil+1):
										
										tmpInd1 = j-k
										if hullMin<=hullMax:
											tmpInd1=max(tmpInd1, hullMin)
										else:
											if tmpInd1>=0:
												tmpInd1=tmpInd1
											else:
												tmpInd1=tmpInd1%contour1.shape[0]
												tmpInd1=max(tmpInd1, hullMin)
										
										tmpInd2 = j+k
										if hullMin<=hullMax:
											tmpInd2=min(tmpInd2, hullMax)
										else:
											if tmpInd2<contour1.shape[0]:
												tmpInd2=tmpInd2
											else:
												tmpInd2=tmpInd2%contour1.shape[0]
												tmpInd2=min(tmpInd2, hullMax)
										
										if distPointToLine(contour1[tmpInd1][0], formulaA, formulaB, formulaC, formulaD) > distToLine or distPointToLine(contour1[tmpInd2][0], formulaA, formulaB, formulaC, formulaD) > distToLine:
											break
										if k == secondaryMinimaProvenUntil:
											doesContend = True
								
								if doesContend == True:
									#choose the one where the perimeter between it and any point that is lower is bigger
									
									for k in range(max(j-hullMin, hullMax+1-j)): #we wont check past the edge of the hull segment
										if distPointToLine(contour1[max(j-secondaryMinimaProvenUntil-k, hullMin)][0], formulaA, formulaB, formulaC, formulaD) > distToLine or distPointToLine(contour1[(min(j+secondaryMinimaProvenUntil+k, hullMax))%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) > distToLine:
											#the new prospect failed to beat the original
											if distPointToLine(contour1[max(largestSecondaryMinimaIndex-secondaryMinimaProvenUntil-k, hullMin)][0], formulaA, formulaB, formulaC, formulaD) > largestSecondaryMinimaDistToLine or distPointToLine(contour1[(min(largestSecondaryMinimaIndex+secondaryMinimaProvenUntil+k, hullMax))%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) > largestSecondaryMinimaDistToLine:
												#they actually tied so just keep original and update neighbourhood
												secondaryMinimaProvenUntil = secondaryMinimaProvenUntil + k - 1
												break
											else:
												secondaryMinimaProvenUntil = secondaryMinimaProvenUntil + k
												break
											
										if distPointToLine(contour1[max(largestSecondaryMinimaIndex-secondaryMinimaProvenUntil-k, hullMin)][0], formulaA, formulaB, formulaC, formulaD) > largestSecondaryMinimaDistToLine or distPointToLine(contour1[(min(largestSecondaryMinimaIndex+secondaryMinimaProvenUntil+k, hullMax))%contour1.shape[0]][0], formulaA, formulaB, formulaC, formulaD) > largestSecondaryMinimaDistToLine:
											#the original lost
											largestSecondaryMinimaIndex = j
											secondaryMinimaProvenUntil = secondaryMinimaProvenUntil+k
											largestSecondaryMinimaDistToLine=distToLine
											break
							
							elif thereIsAnotherLocalMinima == False:
								largestSecondaryMinimaIndex = j
								secondaryMinimaProvenUntil = radiusAroundPointToCheckInitially
								thereIsAnotherLocalMinima = True
								largestSecondaryMinimaDistToLine=distToLine
					
			largestMaximaDist = distPointToLine(contour1[largestMaximaIndex][0], formulaA, formulaB, formulaC, formulaD)
			largestSecondMinimaDist = distPointToLine(contour1[largestSecondaryMinimaIndex][0], formulaA, formulaB, formulaC, formulaD)
			splitFlag = 0
			if largestSecondMinimaDist-largestMaximaDist > maxdist - largestMaximaDist:
				if largestSecondMinimaDist - largestMaximaDist < 0.001:
					pass
				
				elif (maxdist - largestMaximaDist)/(largestSecondMinimaDist-largestMaximaDist) > 0.5 and ((lessOrGreat(maxDefectIndex, largestMaximaIndex, contour1.shape[0], hullMin, hullMax)==-1 and lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==-1) or (lessOrGreat(maxDefectIndex, largestMaximaIndex, contour1.shape[0], hullMin, hullMax)==1 and lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==1)) and largestMaximaDist < 0.75*largestSecondMinimaDist:
					if lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==-1 and largestSecondMinimaDist > minRealDefectDistance: # redoing these for readability
						defects1.append([int(largestSecondaryMinimaIndex), largestSecondMinimaDist, int(largestMaximaIndex), int(hullMax)])
						splitFlag = 1
					elif lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==1 and largestSecondMinimaDist > minRealDefectDistance:
						defects1.append([int(largestSecondaryMinimaIndex), largestSecondMinimaDist, int(hullMin), int(largestMaximaIndex)])
						splitFlag = -1
			else:
				
				if maxdist - largestMaximaDist < 0.001:
					pass
				
				elif (largestSecondMinimaDist-largestMaximaDist)/(maxdist - largestMaximaDist) > 0.5 and ((lessOrGreat(maxDefectIndex, largestMaximaIndex, contour1.shape[0], hullMin, hullMax)==-1 and lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==-1) or (lessOrGreat(maxDefectIndex, largestMaximaIndex, contour1.shape[0], hullMin, hullMax)==1 and lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==1)) and largestMaximaDist < 0.75*largestSecondMinimaDist:
					if lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==-1 and largestSecondMinimaDist > minRealDefectDistance: # redoing these for readability
						defects1.append([int(largestSecondaryMinimaIndex), largestSecondMinimaDist, int(largestMaximaIndex), int(hullMax)])
						splitFlag = 1
					elif lessOrGreat(largestMaximaIndex, largestSecondaryMinimaIndex, contour1.shape[0], hullMin, hullMax)==1 and largestSecondMinimaDist > minRealDefectDistance:
						defects1.append([int(largestSecondaryMinimaIndex), largestSecondMinimaDist, int(hullMin), int(largestMaximaIndex)])
						splitFlag = -1
			
			if splitFlag != 0:
				if splitFlag == 1 and maxdist > minRealDefectDistance:
					defects1.append([int(maxDefectIndex), maxdist, int(hullMin), int(largestMaximaIndex)])
				elif splitFlag == -1 and maxdist > minRealDefectDistance:
					defects1.append([int(maxDefectIndex), maxdist, int(largestMaximaIndex), int(hullMax)])
			elif maxdist > minRealDefectDistance:
				defects1.append([int(maxDefectIndex), maxdist, int(hullMin), int(hullMax)])
		
	if False:#debugCounter == 20:
		print(defects1)
		for tmpppp in defects1:
			print(tmpppp[0])
			print(contour1[tmpppp[0]])
			print("start and end coords: " + str(contour1[tmpppp[2]]) + " ... " + str(contour1[tmpppp[3]]))
			print("--------------")
	defects1.sort()
	if onlyDefects == True:
		return defects1
	
	
	defects1Size = len(defects1)
	finalCorners=[]
	
	if defects1Size == 4 or defects1Size == 5 or defects1Size == 6 or defects1Size == 7 or defects1Size == 8:
		
		defectDicts = {}
		
		for i in range(defects1Size): # end on corners?
			
			hullEndingBeforeEndsOnVertex = hullEndsOnVertex(contour, defects1[i][2], ydim, "before")
			hullEndingAfterEndsOnVertex = hullEndsOnVertex(contour, defects1[i][3], ydim, "after", debug=actualdebug)
			defectDicts[i] = {
				"before": hullEndingBeforeEndsOnVertex,
				"after": hullEndingAfterEndsOnVertex
			}
		
		storeChecked = {}
		potentialOuties = []
		for i in range(defects1Size): # no big changes or vertices between defects and hull endings furthest away?
			if len(defectDicts[i]['before']) != 0 and len(defectDicts[(i+1)%defects1Size]['after']) != 0:
				
				atLeastOneVertexFirstDefect = []
				atLeastOneVertexSecondDefect = []
				if i in storeChecked:
					atLeastOneVertexFirstDefect = storeChecked[i]
				else:
					if i == 2:
						atLeastOneVertexFirstDefect = checkCornerOrBigChange(contour1, defects1[i][2], defects1[i][3], defects1[i][0], ydim)
					else:
						atLeastOneVertexFirstDefect = checkCornerOrBigChange(contour1, defects1[i][2], defects1[i][3], defects1[i][0], ydim)
					storeChecked[i] = atLeastOneVertexFirstDefect
				if (i+1)%defects1Size in storeChecked:
					atLeastOneVertexSecondDefect = storeChecked[(i+1)%defects1Size]
				else:
					if (i+1)%defects1Size == 2:
						atLeastOneVertexSecondDefect = checkCornerOrBigChange(contour1, defects1[(i+1)%defects1Size][2], defects1[(i+1)%defects1Size][3], defects1[(i+1)%defects1Size][0], ydim)
					else:
						atLeastOneVertexSecondDefect = checkCornerOrBigChange(contour1, defects1[(i+1)%defects1Size][2], defects1[(i+1)%defects1Size][3], defects1[(i+1)%defects1Size][0], ydim)
					storeChecked[(i+1)%defects1Size] = atLeastOneVertexSecondDefect
				
				if atLeastOneVertexFirstDefect[0] == False and atLeastOneVertexSecondDefect[1] == False:
					potentialOuties.append([i,(i+1)%defects1Size])
		
		
		finalCorners = finalCornersMegaFunction(defects1Size, len(potentialOuties), contour1, defects1, potentialOuties, ydim, storeChecked, defectDicts, actualdebug=actualdebug)
		
		
		if finalCorners is None:
			return None, None
		elif len(finalCorners) == 0:
			return None, None
		elif finalCorners == False:
			print(potentialOuties)
			print("finalCorners returned False")
			return None, None
		elif len(finalCorners) == 0:
			print(potentialOuties)
			print("finalCorners empty")
			return None, None
		else:
			pass
	else:
		print("??????????????????????????????? ijdwi")
		return None, None
		# exit()
	
	
	return finalCorners, defects1



def getDistance(x1, x2, y1, y2):
	diffX = abs(x2 - x1)
	diffY = abs(y2 - y1)
	return math.hypot(diffX, diffY) # sqrt a^2 + b^2



def betterSlice(list_a, start, stop):
	if (start <= stop):
		return copy.deepcopy(list_a[start:stop])
	else:
		if list_a[0][0][0]==list_a[-1][0][0] and list_a[0][0][1]==list_a[-1][0][1]:
			if stop>0:
				return copy.deepcopy(np.concatenate([list_a[start:],list_a[1:stop]]))
			else:
				return copy.deepcopy(list_a[start:])
		else:
			return copy.deepcopy(np.concatenate([list_a[start:],list_a[:stop]]))
	


def parseContours(imageContours, debug=False):
	
	maxSideLength = 0
	puzzleData = []
	imgref = imageContours["imgref"]
	centreImgPt = imageContours["centreImgPt"]
	referenceCntrArea = imageContours["referenceCntrArea"]
	referenceCntrInd = imageContours["referenceCntrInd"]
	
	contours = []
	newReferenceCntrInd=-1
	for cntrI, contour in enumerate(imageContours["contours"]):
		
		temparea = cv2.contourArea(contour, oriented = True)
		if temparea < 0:
			temparea = abs(temparea)
			contours.append([contour[::-1].astype(float), temparea])
			if cntrI==referenceCntrInd:
				newReferenceCntrInd=len(contours)-1
		elif temparea > 0:
			temparea = abs(temparea)
			contours.append([contour.astype(float), temparea])
			if cntrI==referenceCntrInd:
				newReferenceCntrInd=len(contours)-1
		elif temparea==0 and cntrI==referenceCntrInd:
			return None, None, None, None
	if newReferenceCntrInd==-1:
		return None, None, None, None
	
	ydim = imageContours["ydim"]
	
	avgImagePieceArea = 0
	refCntrDat=None
	for cntrI, contourD in enumerate(contours):
		contour = contourD[0]
		area = contourD[1]
		
		
		if True:
			convexMethodCornerData, defects = convexMethod(contour, ydim)
			if convexMethodCornerData is None or defects is None: # if a piece fails to be parsed/processed just skip it
				
				if cntrI==newReferenceCntrInd:
					print(convexMethodCornerData)
					print(defects)
					input("ref contour FAILED111")
				pass
			else:
				
				convexMethodEdgeData = prepareConvexMethodEdges(contour, convexMethodCornerData, defects, centreImgPt, referenceCntrArea)
				
				if convexMethodEdgeData is None:
					
					if cntrI==newReferenceCntrInd:
						print(convexMethodEdgeData)
						input("ref contour FAILED222")
					
				else:
					topEdgeLength = math.sqrt(math.pow((convexMethodEdgeData[0]["topEdge"][0][0][0][0] - convexMethodEdgeData[0]["topEdge"][0][convexMethodEdgeData[0]["topEdge"][0].shape[0]-1][0][1]),2) + math.pow((convexMethodEdgeData[0]["topEdge"][0][0][0][1] - convexMethodEdgeData[0]["topEdge"][0][convexMethodEdgeData[0]["topEdge"][0].shape[0]-1][0][1]),2))
					leftEdgeLength = math.sqrt(math.pow((convexMethodEdgeData[0]["leftEdge"][0][0][0][0] - convexMethodEdgeData[0]["leftEdge"][0][convexMethodEdgeData[0]["leftEdge"][0].shape[0]-1][0][1]),2) + math.pow((convexMethodEdgeData[0]["leftEdge"][0][0][0][1] - convexMethodEdgeData[0]["leftEdge"][0][convexMethodEdgeData[0]["leftEdge"][0].shape[0]-1][0][1]),2))
					bottomEdgeLength = math.sqrt(math.pow((convexMethodEdgeData[0]["bottomEdge"][0][0][0][0] - convexMethodEdgeData[0]["bottomEdge"][0][convexMethodEdgeData[0]["bottomEdge"][0].shape[0]-1][0][1]),2) + math.pow((convexMethodEdgeData[0]["bottomEdge"][0][0][0][1] - convexMethodEdgeData[0]["bottomEdge"][0][convexMethodEdgeData[0]["bottomEdge"][0].shape[0]-1][0][1]),2))
					rightEdgeLength = math.sqrt(math.pow((convexMethodEdgeData[0]["rightEdge"][0][0][0][0] - convexMethodEdgeData[0]["rightEdge"][0][convexMethodEdgeData[0]["rightEdge"][0].shape[0]-1][0][1]),2) + math.pow((convexMethodEdgeData[0]["rightEdge"][0][0][0][1] - convexMethodEdgeData[0]["rightEdge"][0][convexMethodEdgeData[0]["rightEdge"][0].shape[0]-1][0][1]),2))
					
					if topEdgeLength > maxSideLength:
						maxSideLength = topEdgeLength
					if leftEdgeLength > maxSideLength:
						maxSideLength = leftEdgeLength
					if bottomEdgeLength > maxSideLength:
						maxSideLength = bottomEdgeLength
					if rightEdgeLength > maxSideLength:
						maxSideLength = rightEdgeLength
					
					if cntrI==newReferenceCntrInd:
						tmpCorners = []
						tmpCorners.append((convexMethodEdgeData[0]["topEdge"][0][0][0][0], convexMethodEdgeData[0]["topEdge"][0][0][0][1]))
						tmpCorners.append((convexMethodEdgeData[0]["leftEdge"][0][0][0][0], convexMethodEdgeData[0]["leftEdge"][0][0][0][1]))
						tmpCorners.append((convexMethodEdgeData[0]["bottomEdge"][0][0][0][0], convexMethodEdgeData[0]["bottomEdge"][0][0][0][1]))
						tmpCorners.append((convexMethodEdgeData[0]["rightEdge"][0][0][0][0], convexMethodEdgeData[0]["rightEdge"][0][0][0][1]))
						
						tmpCorners.sort()
						
						topLeft = tmpCorners[0]
						bottomLeft = tmpCorners[1]
						topRight = tmpCorners[2]
						bottomRight = tmpCorners[3]
						
						if topLeft[1]<bottomLeft[1]: # top and bottom in Y coord sense, which is flipped in image!
							topLeft, bottomLeft = bottomLeft, topLeft
						
						if topRight[1]<bottomRight[1]: # top and bottom in Y coord sense, which is flipped in image!
							topRight, bottomRight = bottomRight, topRight
						diag1 = getDistance(topLeft[0], bottomRight[0], topLeft[1], bottomRight[1])
						diag2 = getDistance(topRight[0], bottomLeft[0], topRight[1], bottomLeft[1])
						refCntrDat=[diag1, diag2]
						
					
					for edgeKey in ['topEdge', 'leftEdge', 'bottomEdge', 'rightEdge']:
						for tmpCoordI in range(convexMethodEdgeData[0][edgeKey][0].shape[0]-1):
							if convexMethodEdgeData[0][edgeKey][0][tmpCoordI][0][0]==convexMethodEdgeData[0][edgeKey][0][tmpCoordI+1][0][0] and convexMethodEdgeData[0][edgeKey][0][tmpCoordI][0][1]==convexMethodEdgeData[0][edgeKey][0][tmpCoordI+1][0][1]:
								print('consecutive duplicate points encountered')
								exit()
					
					puzzleData.append({"imgref": imgref, "potentialPieceData": convexMethodEdgeData, "pieceArea": area, "referenceCntrArea": referenceCntrArea})
					avgImagePieceArea += area
	
	if len(puzzleData) !=0:
		avgImagePieceArea = avgImagePieceArea/len(puzzleData)
		for pieceDat in puzzleData:
			
			notDonePieceArea = True
			for tmpConvexMethodEdgeData in pieceDat['potentialPieceData']:
				tmpConvexMethodEdgeData['distFromCameraNormalisationVal'] = pieceDat['pieceArea']
				if True:
					tmpConvexMethodEdgeData['imageSizeX'] = imageContours['imageSizeX'] # added for debug part to display in similarityController, maybe remove at end
					tmpConvexMethodEdgeData['imageSizeY'] = imageContours['imageSizeY'] # added for debug part to display in similarityController, maybe remove at end
		
		for pieceDat in puzzleData:
			for tmpConvexMethodEdgeData in pieceDat['potentialPieceData']:
				tmpConvexMethodEdgeData['distFromCameraNormalisationVal'] = tmpConvexMethodEdgeData['distFromCameraNormalisationVal']/avgImagePieceArea
				
	else:
		avgImagePieceArea=None
	
	maxSideLength+=50
	for pieceDat in puzzleData:
		pieceDat['refCntrDat'] = refCntrDat
	
	return puzzleData,maxSideLength,avgImagePieceArea,refCntrDat


def onSegment1(p, q, r):
	if ( (q[0] <= max(p[0], r[0])) and (q[0] >= min(p[0], r[0])) and
		   (q[1] <= max(p[1], r[1])) and (q[1] >= min(p[1], r[1]))):
		return True
	return False
 
def orientation1(p, q, r):
	val = (float(q[1] - p[1]) * (r[0] - q[0])) - (float(q[0] - p[0]) * (r[1] - q[1]))
	if (val > 0):
		return 1
	elif (val < 0):
		return 2
	else:
		return 0

def doIntersect1(p1,q1,p2,q2):
	o1 = orientation1(p1, q1, p2)
	o2 = orientation1(p1, q1, q2)
	o3 = orientation1(p2, q2, p1)
	o4 = orientation1(p2, q2, q1)
	if ((o1 != o2) and (o3 != o4)):
		return True
	if ((o1 == 0) and onSegment1(p1, p2, q1)):
		return True
	if ((o2 == 0) and onSegment1(p1, q2, q1)):
		return True
	if ((o3 == 0) and onSegment1(p2, p1, q2)):
		return True
	if ((o4 == 0) and onSegment1(p2, q1, q2)):
		return True
	return False


def bresenham(x1,y1,x2,y2,decide):
	coords = []
	dy = abs(y2-y1)
	dx = abs(x2-x1)
	pk = 2*dy-dx
	i=0
	
	while i<=dx:
		if decide:
			coords.append((x1, y1))
		else:
			coords.append((y1, x1))
		if x1<x2:
			x1+=1
		else:
			x1-=1
		if pk < 0:
			pk = pk+2*dy
		else:
			if y1<y2:
				y1+=1
			else:
				y1-=1
			pk=pk+2*dy-2*dx
		
		i+=1
	return coords

totalfailedcolour=0
def processColourDat(onlyStepPoints, img, params, innieOrOutie, imgCentreImgPt, avgPieceMaterialColour, tmpdebug=False):
	global totalfailedcolour
	# imgCentreImgPt is for the image, untransformed
	
	# IF OUTIE, MARGIN WILL BE ON RIGHT WHEN TRAVERSING FORWARDS THROUGH EDGE STEPCOORDS, AND ON LEFT IF INNIE
	
	stepLength = getDistance(onlyStepPoints[0][0][0], onlyStepPoints[1][0][0], onlyStepPoints[0][0][1], onlyStepPoints[1][0][1])
	margin = params['colourMarginAsRatioOfStepCoordLength']*stepLength
	
	perpenPtDist = stepLength/2
	distToInnerPt = math.sqrt(perpenPtDist*perpenPtDist + margin*margin)
	innerPtOrientationWRTLineSeg = math.acos(perpenPtDist/distToInnerPt) # this angle is absolute angle away from line from c1 to c2, always 0<=X<=90 deg, set sign based on innieOrOutie
	if innieOrOutie=='innie':
		innerPtOrientationWRTLineSeg = -innerPtOrientationWRTLineSeg
	
	
	chunksAmt = params['splitColourEdgeArcLengthInto'] # 4 for quarters
	chunkIntervals = []
	for i in range(chunksAmt):
		chunkIntervals.append((int(round(len(onlyStepPoints)*i/chunksAmt)), int(round(len(onlyStepPoints)*(i+1)/chunksAmt))))
	
	
	colourDat=[[],[]]
	
	for chunkInterval in chunkIntervals:
		
		outerPoly = []
		for i in range(chunkInterval[0], chunkInterval[1]):
			outerPoly.append((onlyStepPoints[i][0][0], onlyStepPoints[i][0][1]))
		innerPoly = []
		for i in range(len(outerPoly)-1):
			c1 = outerPoly[i]
			c2 = outerPoly[i+1]
			lineSegOrient = math.atan2(c2[1]-c1[1], c2[0]-c1[0])
			newPtOrient = lineSegOrient+innerPtOrientationWRTLineSeg
			newPtBase = (distToInnerPt, 0)
			newPtWRTOrigin = (newPtBase[0]*math.cos(newPtOrient)-newPtBase[1]*math.sin(newPtOrient), newPtBase[0]*math.sin(newPtOrient)+newPtBase[1]*math.cos(newPtOrient))
			newPt = (newPtWRTOrigin[0]+c1[0], newPtWRTOrigin[1]+c1[1])
			innerPoly.append(newPt)
			
			
			sign = (c2[1] - imgCentreImgPt[1])*(c1[0] - imgCentreImgPt[0]) - (c2[0] - imgCentreImgPt[0])*(c1[1] - imgCentreImgPt[1])
			if sign<0 and innieOrOutie=='outie' or sign>0 and innieOrOutie=='innie':
				innerPt = newPt
				outerPt = ((c1[0]+c2[0])/2, (c1[1]+c2[1])/2)
				
				# round pts to integers in a way that if the endpoints overlap at all with a pixel, we start from the beginning if the pixel and vice versa if it ends on a pixel finish at the end of that pixel
				if innerPt[0]<=outerPt[0]:
					innerPt = (math.floor(innerPt[0]), innerPt[1])
					outerPt = (math.ceil(outerPt[0]), outerPt[1])
				else:
					innerPt = (math.ceil(innerPt[0]), innerPt[1])
					outerPt = (math.floor(outerPt[0]), outerPt[1])
				if innerPt[1]<=outerPt[1]:
					innerPt = (innerPt[0], math.floor(innerPt[1]))
					outerPt = (outerPt[0], math.ceil(outerPt[1]))
				else:
					innerPt = (innerPt[0], math.ceil(innerPt[1]))
					outerPt = (outerPt[0], math.floor(outerPt[1]))
				
				coordsFromLineSegToInnerPt=None
				if abs(outerPt[0]-innerPt[0])>abs(outerPt[1]-innerPt[1]):
					coordsFromLineSegToInnerPt = bresenham(outerPt[0],outerPt[1],innerPt[0],innerPt[1], True)
				else:
					coordsFromLineSegToInnerPt = bresenham(outerPt[1],outerPt[0],innerPt[1],innerPt[0], False)
				if outerPt[0]==coordsFromLineSegToInnerPt[0][0] and outerPt[1]==coordsFromLineSegToInnerPt[0][1]:
					pass
				else:
					coordsFromLineSegToInnerPt.reverse()
				
				if tmpdebug:
					print('coordsFromLineSegToInnerPt')
					print(coordsFromLineSegToInnerPt)
				
				stopAt=None
				for tmpCoord in coordsFromLineSegToInnerPt[2:]: # skipping first 2 pts cause its a bit too close to the table material/colour
					roughColourAvgPtsAroundCoord = [tmpCoord, (tmpCoord[0]-1, tmpCoord[1]), (tmpCoord[0]+1, tmpCoord[1]), (tmpCoord[0], tmpCoord[1]-1), (tmpCoord[0]-1, tmpCoord[1]+1)] # + formation
					tmpAvgColour = 0
					tmpAvgSat = 0
					tmpAvgVal = 0
					tmpAvgColourAmt = 0
					for avgColCoord in roughColourAvgPtsAroundCoord:
						tmpColour = img[avgColCoord[1]][avgColCoord[0]] # x, y flipped when working directly with image in opencv
						
						tmpAvgColour+=tmpColour[0]
						tmpAvgSat+=tmpColour[1]
						tmpAvgVal+=tmpColour[2]
						tmpAvgColourAmt+=1
						
					if tmpAvgColourAmt>0:
						tmpAvgColour=tmpAvgColour/tmpAvgColourAmt
						tmpAvgSat=tmpAvgSat/tmpAvgColourAmt
						tmpAvgVal=tmpAvgVal/tmpAvgColourAmt
					deltaE2000 = ciede2000DeltaE(tmpAvgColour, tmpAvgSat, tmpAvgVal, None, None, None, params, avgPieceMaterialColour)
					
					if deltaE2000>params['ciede2000DeltaESimilarToPieceMaterialThreshold']:
						stopAt=tmpCoord
						break
				if stopAt is not None:
					translateBy = (stopAt[0]-outerPt[0], stopAt[1]-outerPt[1])
					outerPoly[i] = (outerPoly[i][0]+translateBy[0], outerPoly[i][1]+translateBy[1]) # not i+1 just cause
					innerPoly[-1] = (innerPoly[-1][0]+translateBy[0], innerPoly[-1][1]+translateBy[1])
				
			
		tmpdebugg = copy.deepcopy(innerPoly)
		# check for crossings amongst innerPoly and if so just remove pts until get back to overlap point, not handling weird cases
		for i in range(len(innerPoly)-1):
			c1 = innerPoly[i]
			c2 = innerPoly[i+1]
			# very rough implementation, ignoring case where immediate next lineSeg can come backwards and overlap, etc, very very rare cases and in those cases
			# can just tank the outcome which in worst case will just average colour of whole image or maybe error from matplotlib
			somethingHappened=False
			if i+2<len(innerPoly)-1:
				for j in range(len(innerPoly)-2, i+1, -1):
					c3 = innerPoly[j]
					c4 = innerPoly[j+1]
					
					if doIntersect1(c1, c2, c3, c4):
						newInnerPoly = []
						for k in range(0, i+1): # remove everything between [i+1, j] inclusive i.e. keep 0->i and j+1->end
							newInnerPoly.append(innerPoly[k])
						for k in range(j+1, len(innerPoly)):
							newInnerPoly.append(innerPoly[k])
						innerPoly=newInnerPoly
						somethingHappened=True
						break
				
			if somethingHappened:
				break
			
		# check for crossings between innerPoly and outerPoly, if exists, print and exit() cause this prob shouldnt ever happen especially after fixing for innerPoly crossings
		if True:
			for i in range(len(innerPoly)-1):
				c1 = innerPoly[i]
				c2 = innerPoly[i+1]
				
				for j in range(len(outerPoly)-1):
					c3 = outerPoly[j]
					c4 = outerPoly[j+1]
					
					if doIntersect1(c1, c2, c3, c4):
						print("inner poly intersects with outer poly??")
						
						totalfailedcolour+=1
						print('totalfailedcolour')
						print(totalfailedcolour)
						# exit()
						return None
		
		innerPoly.reverse()
		
		wholePoly = outerPoly+innerPoly
		minX = float('inf')
		minY = float('inf')
		for coord in wholePoly:
			if coord[0]<minX:
				minX = coord[0]
			if coord[1]<minY:
				minY = coord[1]
		minX-=2 # so theres buffer just incase weird stuff, i dont want points to be at (0, y) or (x, 0)
		minY-=2
		for i in range(len(wholePoly)):
			wholePoly[i] = (wholePoly[i][0]-minX, wholePoly[i][1]-minY)
		
		maxX = float('-inf')
		maxY = float('-inf')
		for coord in wholePoly:
			if coord[0]>maxX:
				maxX = coord[0]
			if coord[1]>maxY:
				maxY = coord[1]
		maxX+=2
		maxY+=2
		
		maxX=int(math.ceil(maxX))
		maxY=int(math.ceil(maxY))
		
		x, y = np.meshgrid(np.arange(maxX), np.arange(maxY))
		x, y = x.flatten(), y.flatten()
		points = np.vstack((x,y)).T 
		
		p = Path(wholePoly)
		grid = p.contains_points(points)
		
		actualPtsInside=[]
		for i in range(len(grid)):
			if grid[i]:
				actualPtsInside.append(points[i])
		
		ptsInside=actualPtsInside
		if tmpdebug:
			img_contours=img.copy()
			for coord in wholePoly:
				tupleFormat = (int(round(coord[0]+minX)), int(round(coord[1]+minY)))
				cv2.circle(img_contours,tupleFormat,0,[0,0,255],-1)
			
			for coord in ptsInside:
				tupleFormat = (int(round(coord[0]+minX)), int(round(coord[1]+minY)))
				cv2.circle(img_contours,tupleFormat,0,[255,0,0],-1)
			
			for coord in tmpdebugg:
				tupleFormat = (int(round(coord[0])), int(round(coord[1])))
				cv2.circle(img_contours,tupleFormat,0,[100,255,0],-1)
			print(tmpdebugg)
			cv2.imshow('Contours', img_contours)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
			
			
		img_contours=img.copy()
		avgColour=0
		avgColourCtr=0
		avgVal=0
		avgSat=0
		
		avgColour2=0
		avgColourCtr2=0
		avgVal2=0
		avgSat2=0
		
		
		for tmpPtInside in ptsInside:
			actualPtInside = (min(int(round(tmpPtInside[0]+minX)), img_contours.shape[1]-1), min(int(round(tmpPtInside[1]+minY)), img_contours.shape[0]-1))
			tmpColour = img_contours[actualPtInside[1]][actualPtInside[0]] # x, y flipped when working directly with image in opencv
			avgColour+=tmpColour[0]
			avgVal+=tmpColour[2]
			avgSat+=tmpColour[1]
			avgColourCtr+=1
			if avgSat>params['minSaturationForSecondColourDat']:
				avgColour2+=tmpColour[0]
				avgVal2+=tmpColour[2]
				avgSat2+=tmpColour[1]
				avgColourCtr2+=1
		if avgColourCtr!=0:
			avgColour=avgColour/avgColourCtr
			avgVal=avgVal/avgColourCtr
			avgSat=avgSat/avgColourCtr
			
			avgColour = (avgColour/255)*360 # convert from [0, 255] domain to [0, 360] domain
			
			colourDat[0].append((avgColour, avgSat, avgVal))
			
			if avgColourCtr2>=avgColourCtr*params['minColoursAboveMinSaturationAsRatioOfTotalColourDat']:
				
				avgColour2=avgColour2/avgColourCtr
				avgVal2=avgVal2/avgColourCtr
				avgSat2=avgSat2/avgColourCtr
				
				avgColour2 = (avgColour2/255)*360
				
				colourDat[1].append((avgColour2, avgSat2, avgVal2))
			else:
				colourDat[1].append(None)
	if len(colourDat[0])==chunksAmt:
		return colourDat
	else:
		totalfailedcolour+=1
		print('totalfailedcolour')
		print(totalfailedcolour)
		return None


def mainEdgeSimilarity(puzzleData, maxSideLength, globalydim, imgAvgAreaDict, debugDat=None, globalDat=None, debug=False, hsvImgDict=None, avgPieceMaterialColour=None, hsvImgCentrePtDict=None, baseImageReferenceContourArea=None, baseImageReferenceContourDat=None):
	
	params = {
		"segOrientationPartitionSize": 30*math.pi/180, # 30 degrees for now, think this is the size to partition line segments into so I can search quickly for line segments with in a specific orientation range
		"numberOfArcLengthSteps": 70, # i.e. 1% steps, 100 of them
		
		}
	
	
	params["scaleEdgeSpanTo"] = 100
	
	params['discardBadTransformation']=True # REMEMBER, THESE ARE JUST TO RULE OUT OBVIOUS HAYWIRE TRANSLATIONS, IF THIS WAS FOR DECIDING IF ITS AN ACTUAL MATCH, THE THRESHOLDS WOULD BE AT LEAST LIKE 50% MORE STRICT
	# params['maxScaleDiffICP']=0.1 # like 0.3 or something
	params['maxScaleDiffICP']=0.17 # like 0.3 or something
	params['maxTranslationAsRatioOfAvgDistBetweenPlanesSegmentsPoints']=7 # like 7?	 # NOT ACTUALLY DOING TRANSLATION CAUSE NOT SURE IF ITS WELL DEFINED CAUSE OF SCALING AND ROTATION
	params['maxRotationICP']=22*math.pi/180 # like 30 degrees?
	
	params['minArcLengthRatioForConfidentLineSegOrientation'] = 0.035 # e.g. if 1%, then if a lineSeg is >= 1% just take its word for it that there isnt enough noise for its orientation to be flipped to being on wrong side of line from centre img pt
	params['arcLengthRatioTangentRadius'] = 0.01
	params['checkArcLengthRatioInwardsFromPlaneSegmentEndingsForParallelness'] = 0.03

	params['maxClosenessToParallelWithCentreImgLine'] = 10*math.pi/180
	params['processedPlaneSegsStillContainsArcLengthRatio'] = 0.69

	# params['arcLengthRatioGoalBetweenPtsForPlaneSegDat'] = 0.005 # like 0.5% or so, 1% is stepCoords so i think i want this to be higher detail
	params['arcLengthRatioGoalBetweenPtsForPlaneSegDat'] = 0.015 # like 0.5% or so, 1% is stepCoords so i think i want this to be higher detail
	
	# params['maxICPIterations'] = 8
	params['maxICPIterations'] = 15
	# params['maxICPIterations'] = 14
	params['initialICPIterations'] = 4
	# params['initialICPIterations'] = 6
	params['maxPairingToSamePtAmountICP'] = 1
	params['maxPairingToSamePtAmount'] = 1 # idk if above is used but this one is
	
	
	params['enforceOnlyPairingToPoints'] = False # if True, only pair to points in mainEdge, NOT on lineSeg between pts (which is usually where the real closest pt lies)
	params['enforceMaxCorrespondenceDist'] = True # if dist between pointPair in ICP is larger than X, don't consider it an actual pairing
	# params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPoints'] = 4 # if avg segmentDat dist between pts is X, any pointPairs 3*X or larger dist away from eachother won't be considered as an actual pairing
	params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPoints'] = 100 # if avg segmentDat dist between pts is X, any pointPairs 3*X or larger dist away from eachother won't be considered as an actual pairing
	# params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPoints'] = 3 # if avg segmentDat dist between pts is X, any pointPairs 3*X or larger dist away from eachother won't be considered as an actual pairing
	
	params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPointsJustForInefficientCorrespondenceAreas'] = 100 # correspondence areas are usually calced after some icp so this should be smaller than max corr dist above which is used for icp
	# params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPointsJustForInefficientCorrespondenceAreas'] = 4 # correspondence areas are usually calced after some icp so this should be smaller than max corr dist above which is used for icp
	# params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPointsJustForInefficientCorrespondenceAreas'] = 1.5 # correspondence areas are usually calced after some icp so this should be smaller than max corr dist above which is used for icp
	
	params['enforceMonotony'] = True # very roughly implemented check to discard consecutive pointPairs that are paired in the wrong direction, if mainEdge in is increasing, so should its pairings inds in otherEdge
	
	params['noICP']=False # if True, skip ICP
	
	params['justDoICPAnywayEvenIfScaleFailsLastResort']=True # just do ICP raw anyway at the end if all previous attempts fail and scaling/preliminary alignment fails
	# params['justDoICPAnywayEvenIfScaleFailsLastResort']=False # just do ICP raw anyway at the end if all previous attempts fail and scaling/preliminary alignment fails
	
	params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount'] = 100 # if wacky icp transform happens on plane that's more than this % of total pts in both planes, exit the icp process early (set to like 10000 if want to do original where never exit early but actually slightly different from original cause i created new early exit lines as well as modified some existing transform is None and endEarlyICP so the modified ones will be different than before unless this is 0, not 10000)
	# params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount'] = 0.12 # if wacky icp transform happens on plane that's more than this % of total pts in both planes, exit the icp process early (set to like 10000 if want to do original where never exit early but actually slightly different from original cause i created new early exit lines as well as modified some existing transform is None and endEarlyICP so the modified ones will be different than before unless this is 0, not 10000)
	
	params['splitColourEdgeArcLengthInto']=4 # 4 for quarters
	params['colourMarginAsRatioOfStepCoordLength'] = 3 # was 2 but 2 has too much blue from piece material because of plane stuff
	params['maxColourHueAngleDiff'] = 25 # within 25 degrees on hue wheel
	
	
	# params['basicallyBlackColVal'] = 0.2*255 # basically black so hue doesnt mean anything (33 = ~13% of 255)
	params['basicallyBlackColVal'] = 0.4*255 # basically black so hue doesnt mean anything (33 = ~13% of 255)
	# params['basicallyGreyColSat'] = 0.05*255 # ~4% of 255
	params['basicallyGreyColSat'] = 0.05*255 # ~4% of 255
	# params['colourValueSimilarThresh'] = 0.2*255 # 20% of possible value range, seems alright just arbitrarily chose this
	# params['colourSaturationSimilarThresh'] = 0.2*255
	
	# params['ciede2000DeltaESimilarThresh'] = 12 # was 10
	# params['ciede2000DeltaESimilarThresh'] = 14 # was 10 latest
	# params['ciede2000DeltaESimilarThresh'] = 10 # was 10
	# params['ciede2000DeltaESimilarThresh'] = 20
	# params['ciede2000DeltaESimilarThresh'] = 10 # for new cmc ie brightness stuff
	# params['ciede2000DeltaESimilarThresh'] = 9 # for new cmc ie brightness stuff
	params['ciede2000DeltaESimilarThresh'] = 7 # for new cmc ie brightness stuff
	# params['ciede2000DeltaESimilarThresh'] = 8 # for new cmc ie brightness stuff
	
	# params['minColourMatchingQuartersAmt']=3
	params['minColourMatchingQuartersAmt']=4
	
	params['minColoursAboveMinSaturationAsRatioOfTotalColourDat']=0.25 # amount of pixels above sat threshold as a ratio of total amt of pixels
	params['minSaturationForSecondColourDat']=13 # 13/255, creating 2nd set of colourDats with only pixels above this saturation to try and combat error induced by camera flash
	
	params['scaleEstimationErrorReferencePointMethod'] = 0.05 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
	# params['scaleEstimationErrorReferencePointMethod'] = 0.08 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
	# params['scaleEstimationErrorReferencePointMethod'] = 0.045 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
	# params['scaleEstimationErrorReferencePointMethod'] = 0.039 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
	# params['scaleEstimationErrorReferencePointMethod'] = 0.045 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
	
	# params['absoluteWingRatioDiffSimilarityThreshold'] = 0.045 # since all edges are scaled to wingspan==100 pixels, if this is 3, then when projecting defect pts onto wingspan/edgespan, up to 3 pixel difference is allowed to keep compatibility, docs code i3uh2i3h
	# params['absoluteWingRatioDiffSimilarityThreshold'] = 0.07 # since all edges are scaled to wingspan==100 pixels, if this is 3, then when projecting defect pts onto wingspan/edgespan, up to 3 pixel difference is allowed to keep compatibility, docs code i3uh2i3h
	params['absoluteWingRatioDiffSimilarityThreshold'] = 0.05 # since all edges are scaled to wingspan==100 pixels, if this is 3, then when projecting defect pts onto wingspan/edgespan, up to 3 pixel difference is allowed to keep compatibility, docs code i3uh2i3h
	# params['absoluteWingRatioDiffSimilarityThreshold'] = 0.031 # since all edges are scaled to wingspan==100 pixels, if this is 3, then when projecting defect pts onto wingspan/edgespan, up to 3 pixel difference is allowed to keep compatibility, docs code i3uh2i3h
	# ^^ THIS IS ARBITRARY KINDA, just based on a match that was failing to pass compatibility, this is the value required for the matching pair to pass compatibility requirements
	
	# params['ciede2000DeltaESimilarToPieceMaterialThreshold'] = 2 # if <= this, then assume it's close enough to piece material colour to be designated as being piece material
	params['ciede2000DeltaESimilarToPieceMaterialThreshold'] = 3.5 # if <= this, then assume it's close enough to piece material colour to be designated as being piece material
	
	params['baseImageReferenceContourArea']=baseImageReferenceContourArea # ref contour area in first image, scale all results such that the main edge in the edgePair is transformed to being in first image scale space
	params['baseImageReferenceContourDat']=baseImageReferenceContourDat # ref contour dat in first image, scale all results such that the main edge in the edgePair is transformed to being in first image scale space
	
	params['wingOrientDiffThreshold'] = 10*math.pi/180 # was 10 deg now 6 deg
	
	params['lightnessConstantCMCDeltaE']=4
	params['colourConstantCMCDeltaE']=1
	
	# looseConstraints=True
	looseConstraints=False
	
	if looseConstraints:
		params['scaleEstimationErrorReferencePointMethod'] = 0.08 # like 3.5% i.e. 0.035, maybe up to 5% but that seems quite large. This technically should represent compound error from both images being tilted in ways that maximise error i.e. enlarge one edge and shrink the other edge so maybe in those cases it could be up to like 5+5=10% total scale error
		params['absoluteWingRatioDiffSimilarityThreshold'] = 0.07 # since all edges are scaled to wingspan==100 pixels, if this is 3, then when projecting defect pts onto wingspan/edgespan, up to 3 pixel difference is allowed to keep compatibility, docs code i3uh2i3h
		params['ciede2000DeltaESimilarThresh'] = 9 # for new cmc ie brightness stuff
		
	
	tightColourConstraints=True
	# tightColourConstraints=False
	
	if tightColourConstraints:
		# params['colourMarginAsRatioOfStepCoordLength']=1.5
		params['colourMarginAsRatioOfStepCoordLength']=2
		# params['colourMarginAsRatioOfStepCoordLength']=3
		
		
		params['splitColourEdgeArcLengthInto']=6
		params['minColourMatchingQuartersAmt']=5
		# params['splitColourEdgeArcLengthInto']=4
		# params['minColourMatchingQuartersAmt']=4
		
		params['lightnessConstantCMCDeltaE']=4
		params['colourConstantCMCDeltaE']=2
		params['ciede2000DeltaESimilarThresh']=7
		# params['ciede2000DeltaESimilarThresh']=9
	
	largePieceDatabase = []
	trackerAndOtherData = {'outies': [], 'innies': []}
	upToOuties = 0
	upToInnies = 0
	
	
	minAngleBetweenPts = None
	
	arcLengthStepAmount = params["numberOfArcLengthSteps"]
	
	edgeSimilarity=[]
	potentialPieceData = puzzleData
	for i in range(len(potentialPieceData)):
		
		indexToOGPieceDat = i
		
		referenceCntrArea = potentialPieceData[i]["referenceCntrArea"]
		
		refCntrDat = potentialPieceData[i]["refCntrDat"]
		
		piece1 = potentialPieceData[i]["potentialPieceData"][0]
		piece1ImgPath = potentialPieceData[i]["imgref"]
		piece1HSVImg = hsvImgDict[piece1ImgPath]
		ydim=piece1HSVImg.shape[0]
		tempPieceData = [[],[]]
		imgCentreImgPt = hsvImgCentrePtDict[piece1ImgPath]
		for key1 in ["topEdge", "leftEdge", "bottomEdge", "rightEdge"]:
			
			readability = False
			newDefects1 = None
			newDefects2 = None
			
			
			defectKey1 = None
			if key1 == "topEdge":
				defectKey1 = "topDefects"
			elif key1 == "leftEdge":
				defectKey1 = "leftDefects"
			elif key1 == "bottomEdge":
				defectKey1 = "bottomDefects"
			elif key1 == "rightEdge":
				defectKey1 = "rightDefects"
			
			
			drawPointInEdgeInOriginalPosition = copy.deepcopy(piece1[key1][0][math.floor(piece1[key1][0].shape[0]/2)][0])
			okokdebug=False
			# if i==24 and key1=="bottomEdge":
				# okokdebug=True
				# print(defectKey1)
				# print(piece1[defectKey1])
				# exit()
			defects1 = convexMethod(piece1[key1][0], ydim, onlyDefects=True, skipDefects=piece1[defectKey1], tempdebug=okokdebug)
			if defects1 is None or (piece1[key1][1] == 'outie' and len(defects1) < 1) or (piece1[key1][1] == 'innie' and len(defects1) < 2):
				print("??jee89")
				print(piece1[key1][0][0])
				if debug==True:
					exit()
			else:
				if ((piece1[key1][1] == 'outie' and len(defects1) == 1) or (piece1[key1][1] == 'innie' and len(defects1) == 2)):
					newDefects1 = piece1[defectKey1] + defects1
					readability=True
				else:
					if piece1[key1][1] == 'innie' and len(defects1) > 2:
						closestBefore = None
						closestAfter = None
						for defectData in defects1:
							if closestBefore is None and defectData[0] < piece1[defectKey1][0][0]:
								closestBefore = defectData
							elif closestBefore is not None and defectData[0] < piece1[defectKey1][0][0] and defectData[0] > closestBefore[0]:
								closestBefore = defectData
							if closestAfter is None and defectData[0] > piece1[defectKey1][0][0]:
								closestAfter = defectData
							elif closestAfter is not None and defectData[0] > piece1[defectKey1][0][0] and defectData[0] < closestAfter[0]:
								closestAfter = defectData
						if closestAfter is not None and closestBefore is not None:
							newDefects1 = [closestBefore, closestAfter, piece1[defectKey1][0]]
					elif piece1[key1][1] == 'outie' and len(defects1) > 1:
						defectBetween = None
						inbetweenCount = 0
						for defectData in defects1:
							if defectData[0] > piece1[defectKey1][0][0] and defectData[0] < piece1[defectKey1][1][0]:
								defectBetween = defectData
								inbetweenCount+=1
						if inbetweenCount == 1 and defectBetween is not None:
							newDefects1 = [piece1[defectKey1][0], defectBetween, piece1[defectKey1][1]]
						elif inbetweenCount > 1:
							print("????? INBETWEENCOUNT > 1")
							if debug==True:
								exit()
					
					if newDefects1 is not None:
						readability=True
					else:
						print("newDefects1 is None")
						print(piece1[key1][0][0])
				
			if readability == True: # continuing narrowing/if statements
				newDefects1.sort()
				
				piece1Wing1Length = cv2arcLengthReplacementFloats(piece1[key1][0][:newDefects1[0][0]])
				piece1Wing2Length = cv2arcLengthReplacementFloats(piece1[key1][0][newDefects1[2][0]:])
				piece1Perimeter = piece1Wing1Length + piece1Wing2Length + cv2arcLengthReplacementFloats(piece1[key1][0][newDefects1[0][0]-1:newDefects1[2][0]+1])
				seedsMain = {
					'edge1': 0, # should be called ending1 and ending2 not edge1 and edge2
					'nubSideDefect1': newDefects1[0][0],
					'nubDefect': newDefects1[1][0],
					'nubSideDefect2': newDefects1[2][0],
					'edge2': piece1[key1][0].shape[0]-1,
				}
				
				edgeView = piece1[key1][0]
				
				if piece1[key1][1] == 'innie':
					edgeView = np.flip(edgeView, 0)
				
				onlyStepPoints, arcLengthStep = getOnlyStepPoints(edgeView, arcLengthStepAmount)
				
				colourDat = processColourDat(onlyStepPoints, piece1HSVImg, params, piece1[key1][1], imgCentreImgPt, avgPieceMaterialColour)
				currEdgeOrientation=None
				if piece1[key1][1] == 'innie':
					currEdgeOrientation = math.atan2(piece1[key1][0][0][0][1] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][1], piece1[key1][0][0][0][0] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][0])
				else:
					currEdgeOrientation = math.atan2(piece1[key1][0][piece1[key1][0].shape[0]-1][0][1] - piece1[key1][0][0][0][1], piece1[key1][0][piece1[key1][0].shape[0]-1][0][0] - piece1[key1][0][0][0][0])
				reqTheta = -currEdgeOrientation
				cosTheta = math.cos(reqTheta)
				sinTheta = math.sin(reqTheta)
				
				
				if currEdgeOrientation !=0: # could put above sin/cos but putting here for readability to make clear that there may be other variables calced before at some other point that still need to be changed
					for coordInd in range(piece1[key1][0].shape[0]):
						tmp1 = [piece1[key1][0][coordInd][0][0]-piece1[key1][0][0][0][0], piece1[key1][0][coordInd][0][1]-piece1[key1][0][0][0][1]]
						tmp1 = [tmp1[0]*cosTheta-tmp1[1]*sinTheta, tmp1[0]*sinTheta+tmp1[1]*cosTheta]
						tmp1 = [tmp1[0]+piece1[key1][0][0][0][0], tmp1[1]+piece1[key1][0][0][0][1]]
						piece1[key1][0][coordInd][0] = tmp1
					
					
					centreImgPt = [piece1[key1][3][0]-piece1[key1][0][0][0][0], piece1[key1][3][1]-piece1[key1][0][0][0][1]]
					centreImgPt = [centreImgPt[0]*cosTheta-centreImgPt[1]*sinTheta, centreImgPt[0]*sinTheta+centreImgPt[1]*cosTheta]
					centreImgPt = [centreImgPt[0]+piece1[key1][0][0][0][0], centreImgPt[1]+piece1[key1][0][0][0][1]]
					piece1[key1][3] = centreImgPt
					
					
				# scale new, just scale edgeSpan to == 100 for now
				tmpEdgeSpan = getDistance(piece1[key1][0][0][0][0], piece1[key1][0][piece1[key1][0].shape[0]-1][0][0], piece1[key1][0][0][0][1], piece1[key1][0][piece1[key1][0].shape[0]-1][0][1])
				tmpScaleBy = params['scaleEdgeSpanTo']/tmpEdgeSpan
				for coordInd in range(piece1[key1][0].shape[0]):
					tmp1 = [piece1[key1][0][coordInd][0][0]-piece1[key1][0][0][0][0], piece1[key1][0][coordInd][0][1]-piece1[key1][0][0][0][1]]
					tmp1 = [tmp1[0]*tmpScaleBy, tmp1[1]*tmpScaleBy]
					tmp1 = [tmp1[0]+piece1[key1][0][0][0][0], tmp1[1]+piece1[key1][0][0][0][1]]
					piece1[key1][0][coordInd][0] = tmp1
				
				#########
				
				centreImgPt = [piece1[key1][3][0]-piece1[key1][0][0][0][0], piece1[key1][3][1]-piece1[key1][0][0][0][1]]
				centreImgPt = [centreImgPt[0]*tmpScaleBy, centreImgPt[1]*tmpScaleBy]
				centreImgPt = [centreImgPt[0]+piece1[key1][0][0][0][0], centreImgPt[1]+piece1[key1][0][0][0][1]]
				piece1[key1][3] = centreImgPt
				
				edgeRefCntrArea = piece1[key1][4]
				edgeRefCntrArea = tmpScaleBy*tmpScaleBy*edgeRefCntrArea
				piece1[key1][4] = edgeRefCntrArea
				
				currRefCntrDat = [tmpScaleBy*refCntrDat[0], tmpScaleBy*refCntrDat[1]]
				
				
				# NEW @@@@@@@@@@@@@@@@@@@@@@@@@@@
				
				edgeSpan1 = getDistance(piece1[key1][0][0][0][0], piece1[key1][0][piece1[key1][0].shape[0]-1][0][0], piece1[key1][0][0][0][1], piece1[key1][0][piece1[key1][0].shape[0]-1][0][1])
				
				# TREAT OUTIE AS DEFAULT, REVERSE INNIE WING ORDER
				linept1 = copy.deepcopy(piece1[key1][0][0][0])
				linept2 = copy.deepcopy(piece1[key1][0][piece1[key1][0].shape[0]-1][0])
				
				innerEndingOfWing1 = None
				innerEndingOfWing2 = None
				if piece1[key1][1] == 'outie':
					innerEndingOfWing1 = copy.deepcopy(piece1[key1][0][newDefects1[0][0]][0])
					innerEndingOfWing2 = copy.deepcopy(piece1[key1][0][newDefects1[2][0]][0])
				elif piece1[key1][1] == 'innie':
					innerEndingOfWing1 = copy.deepcopy(piece1[key1][0][newDefects1[2][0]][0])
					innerEndingOfWing2 = copy.deepcopy(piece1[key1][0][newDefects1[0][0]][0])
				
				ratioWing1 = projectPtToLine(linept1, linept2, innerEndingOfWing1, "ratioonline")
				ratioWing2 = projectPtToLine(linept1, linept2, innerEndingOfWing2, "ratioonline")
				# weird reversed stuff fix
				if piece1[key1][1] == 'outie':
					ratioWing2 = 1 - ratioWing2
				elif piece1[key1][1] == 'innie':
					ratioWing1 = 1 - ratioWing1
				
				
				spanWing1 = ratioWing1*edgeSpan1
				spanWing2 = ratioWing2*edgeSpan1
				
				# check for errors
				if ratioWing1 + ratioWing2 >=1 or ratioWing1 < 0 or ratioWing1 >=1 or ratioWing2 < 0 or ratioWing2 >=1:
					print("unexpected wing composition")
					pass
				else:
					if True:#edgeSpan1-excessErrorFromLowerPlane > 0:
						wing1IntervalAssumingWing1Error = None
						wing2IntervalAssumingWing1Error = None
						
						wing1IntervalAssumingWing2Error = None
						wing2IntervalAssumingWing2Error = None
						
						wing1Orientation = None
						wing2Orientation = None
						
						if piece1[key1][1] == 'outie':
							wing1AbsOrient = math.atan2(piece1[key1][0][newDefects1[0][0]][0][1] - piece1[key1][0][0][0][1], piece1[key1][0][newDefects1[0][0]][0][0] - piece1[key1][0][0][0][0])
							wing2AbsOrient = math.atan2(piece1[key1][0][newDefects1[2][0]][0][1] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][1], piece1[key1][0][newDefects1[2][0]][0][0] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][0])
							wing1Orientation = wing1AbsOrient - math.atan2(piece1[key1][0][piece1[key1][0].shape[0]-1][0][1] - piece1[key1][0][0][0][1], piece1[key1][0][piece1[key1][0].shape[0]-1][0][0] - piece1[key1][0][0][0][0])
							wing2Orientation = wing2AbsOrient - math.atan2(piece1[key1][0][0][0][1] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][1],	piece1[key1][0][0][0][0] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][0])
						elif piece1[key1][1] == 'innie':
							wing2AbsOrient = math.atan2(piece1[key1][0][newDefects1[0][0]][0][1] - piece1[key1][0][0][0][1], piece1[key1][0][newDefects1[0][0]][0][0] - piece1[key1][0][0][0][0])
							wing1AbsOrient = math.atan2(piece1[key1][0][newDefects1[2][0]][0][1] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][1], piece1[key1][0][newDefects1[2][0]][0][0] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][0])
							wing2Orientation = wing2AbsOrient - math.atan2(piece1[key1][0][piece1[key1][0].shape[0]-1][0][1] - piece1[key1][0][0][0][1], piece1[key1][0][piece1[key1][0].shape[0]-1][0][0] - piece1[key1][0][0][0][0])
							wing1Orientation = wing1AbsOrient - math.atan2(piece1[key1][0][0][0][1] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][1],	piece1[key1][0][0][0][0] - piece1[key1][0][piece1[key1][0].shape[0]-1][0][0])
						if wing1Orientation is not None and wing2Orientation is not None:
							while wing1Orientation <= -math.pi:
								wing1Orientation+=2*math.pi
							while wing2Orientation <= -math.pi:
								wing2Orientation+=2*math.pi
							while wing1Orientation > math.pi:
								wing1Orientation-=2*math.pi
							while wing2Orientation > math.pi:
								wing2Orientation-=2*math.pi
							
							
							if abs(wing1Orientation-math.pi)<0.0001:
								wing1Orientation=math.pi
							elif abs(wing1Orientation--math.pi)<0.0001:
								wing1Orientation=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							if abs(wing2Orientation-math.pi)<0.0001:
								wing2Orientation=math.pi
							elif abs(wing2Orientation--math.pi)<0.0001:
								wing2Orientation=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							
						
						# if minAngleBetweenPts is not None:
						if True:
							tempPieceData[0].append([key1, piece1[key1][1]]) #include whether its topedge or leftedge etc
							tempPieceData[1].append([key1, piece1[key1][1], wing1IntervalAssumingWing1Error, wing2IntervalAssumingWing1Error, wing1IntervalAssumingWing2Error, wing2IntervalAssumingWing2Error, wing1Orientation, wing2Orientation, piece1Perimeter, seedsMain, drawPointInEdgeInOriginalPosition, colourDat, ratioWing1, ratioWing2, edgeSpan1, currRefCntrDat])
						
		if len(tempPieceData[0]) > 0:
			largePieceDatabaseEntry = [indexToOGPieceDat, [[]], []]
			for tempDat in tempPieceData[0]:
				largePieceDatabaseEntry[1][0].append(tempDat) # largePieceDatabaseEntry[1][0] is the first potential representation of the piece, and only representation for now
			largePieceDatabase.append(largePieceDatabaseEntry)
			for tmpI, tempDat in enumerate(tempPieceData[1]):
				potentialCornerRepresentation = 0 # need to know which possible arrangement these edges come from, in this case the first one but will change if more are added
				if tempDat[1] == 'innie':
					trackerAndOtherData['innies'].append([len(largePieceDatabase)-1, potentialCornerRepresentation] + tempDat[0:10] + [tmpI] + [tempDat[10]] + [tempDat[11]] + [tempDat[12]] + [tempDat[13]] + [tempDat[14]] + [tempDat[15]])
				elif tempDat[1] == 'outie':
					trackerAndOtherData['outies'].append([len(largePieceDatabase)-1, potentialCornerRepresentation] + tempDat[0:10] + [tmpI] + [tempDat[10]] + [tempDat[11]] + [tempDat[12]] + [tempDat[13]] + [tempDat[14]] + [tempDat[15]])
				else:
					print('should be impossible')
					exit()
		
	for i, largePieceDatabaseEntry in enumerate(largePieceDatabase):
		mainPieceDataInd = largePieceDatabaseEntry[0]
		for j, potentialRep in enumerate(largePieceDatabaseEntry[1]): # only 1 right now i.e. largePieceDatabaseEntry[1][0]	 but doing this so it can be copied later
			for k, edgeData in enumerate(potentialRep):
				
				edgeKey = edgeData[0]
				innieOrOutie = edgeData[1]
				edgeView = potentialPieceData[mainPieceDataInd]["potentialPieceData"][j][edgeKey][0]
				if innieOrOutie == 'innie':
					edgeView = np.flip(edgeView, 0)
				
				onlyStepPoints, arcLengthStep = getOnlyStepPoints(edgeView, arcLengthStepAmount)
				
				largePieceDatabase[i][1][j][k].append(arcLengthStep)
				largePieceDatabase[i][1][j][k].append(onlyStepPoints)
				
				edgeOrientation = math.atan2(edgeView[edgeView.shape[0]-1][0][1] - edgeView[0][0][1], edgeView[edgeView.shape[0]-1][0][0] - edgeView[0][0][0])
				
				staticData, rawDat = staticEdgeStepData(onlyStepPoints, None, edgeOrientation, params) # ASSUME COORDS HAVE BEEN SHIFTED SO ORIENTATION == X AXIS!@!!@!@!@!@
				largePieceDatabase[i][1][j][k].append(staticData)
				largePieceDatabase[i][1][j][k].append(rawDat)
				
				edgeTransformedCentreImagePoint = potentialPieceData[mainPieceDataInd]["potentialPieceData"][j][edgeKey][3]
				
				edgePlaneSegmentedDat = segmentedDat(edgeView, onlyStepPoints, edgeTransformedCentreImagePoint, params, mainPieceDataInd, edgeKey)
				potentialPieceData[mainPieceDataInd]["potentialPieceData"][j][edgeKey].append(edgePlaneSegmentedDat)
				
	
	partialPieceDataSimilarityController(trackerAndOtherData, largePieceDatabase, potentialPieceData, params, hsvImgDict)
	
	return

def cv2arcLengthReplacementFloats(contour):
	arclength = 0
	
	for i in range(contour.shape[0]-1):
		arclength+=getDistance(contour[i][0][0], contour[i+1][0][0], contour[i][0][1], contour[i+1][0][1])
	
	return arclength


def unoptimisedOOB(stepCoords, rawDat, rawDatInds):
	
	tempSet = set()
	for rawDatInd in rawDatInds:
		stepCoordsIndexPair = rawDat[rawDatInd][0]
		coord1 = stepCoords[stepCoordsIndexPair[0]][0]
		coord2 = stepCoords[stepCoordsIndexPair[1]][0]
		tempSet.add((coord1[0], coord1[1])) # convert coords to tuples since they were lists and set needs immutable
		tempSet.add((coord2[0], coord2[1]))
	if len(tempSet) <= 3:
		return None # should never happen anyway but just in case
	
	# CHECK IF STRAIGHT LINE OR <=3 PTS
	straight = True
	
	arbPt1 = tempSet.pop()
	arbPt2 = tempSet.pop()
	
	for item in tempSet:
		if arbPt1[0]*(arbPt2[1] - item[1]) + arbPt2[0]*(item[1] - arbPt1[1]) + item[0]*(arbPt1[1] - arbPt2[1]) != 0:
			straight = False
			break
	if straight:
		tempDiv = arbPt2[0] - arbPt1[0]
		if tempDiv == 0:
			minY = min(arbPt1[1], arbPt2[1])
			maxY = max(arbPt1[1], arbPt2[1])
			for item in tempSet:
				if item[1] < minY:
					minY = item[1]
				if item[1] > maxY:
					maxY = item[1]
			rect = [[arbPt1[0], minY], [arbPt1[0], minY], [arbPt1[0], maxY], [arbPt1[0], maxY]]
			return rect
		else:
			minY = min(arbPt1[1], arbPt2[1])
			maxY = max(arbPt1[1], arbPt2[1])
			for item in tempSet:
				if item[1] < minY:
					minY = item[1]
				if item[1] > maxY:
					maxY = item[1]
			tempSlope = (arbPt2[1] - arbPt1[1])/tempDiv
			tempC = arbPt2[1] - tempSlope*arbPt2[0]
			corner1 = [(minY-tempC)/tempSlope, minY]
			corner2 = [(maxY-tempC)/tempSlope, maxY]
			rect = [corner1, corner1, corner2, corner2]
			return rect
			
	
	tempSet.add(arbPt1)
	tempSet.add(arbPt2)
	
	minY = float('inf')
	minX = float('inf')
	minList = []
	for item in tempSet:
		if item[1] < minY:
			minList = [item]
			minY = item[1]
		elif item[1] == minY:
			minList.append(item)
	if len(minList) > 1:
		tempMin = None
		for item in minList:
			if item[0] < minX:
				minX = item[0]
				tempMin = item
		minList = [tempMin]
	
	minPt = [minList[0][0], minList[0][1]]
	tempSet.remove(minList[0])
	
	angleList = []
	for item in tempSet:
		tempAngle = math.atan2(item[1]-minPt[1], item[0]-minPt[0])
		angleList.append([tempAngle, item])
	
	angleList.sort()
	tempPolyLine = [[minPt]]
	for angleDat in angleList:
		tempPolyLine.append([[angleDat[1][0], angleDat[1][1]]])
	tempArr = np.array(tempPolyLine)
	
	convHull = myConvexHull(tempArr, False)
	if convHull is None:
		return None
	
	hull, flipped = convHull
	
	hull = hull[1:]
	
	lowX = float('inf')
	highX = float('-inf')
	lowY = float('inf')
	highY = float('-inf')
	
	lowXind = -1
	highXind = -1
	lowYind = -1
	highYind = -1
	
	for i, tempArrInd in enumerate(hull):
		if tempArr[tempArrInd][0][0] < lowX:
			lowX = tempArr[tempArrInd][0][0]
			lowXind = i
		if tempArr[tempArrInd][0][1] < lowY:
			lowY = tempArr[tempArrInd][0][1]
			lowYind = i
		if tempArr[tempArrInd][0][0] > highX:
			highX = tempArr[tempArrInd][0][0]
			highXind = i
		if tempArr[tempArrInd][0][1] > highY:
			highY = tempArr[tempArrInd][0][1]
			highYind = i
		
	callipAorient = math.pi/2
	callipCorient = -math.pi/2
	
	callipBorient = 0
	callipDorient = math.pi
	
	callipAattached = lowXind
	callipCattached = highXind
	callipBattached = highYind
	callipDattached = lowYind
	attachedList = [callipAattached, callipBattached, callipCattached, callipDattached]
	orientList = [callipAorient, callipBorient, callipCorient, callipDorient]
	
	minArea = float('inf')
	rect = None
	for i in range(len(hull)-1):
		
		# these will give positive angles of rotation clockwise direction
		
		nextA = (attachedList[0]+1)%(len(hull))
		nextC = (attachedList[2]+1)%(len(hull))
		nextB = (attachedList[1]+1)%(len(hull))
		nextD = (attachedList[3]+1)%(len(hull))
		
		nextList = [nextA, nextB, nextC, nextD]
		
		angleToNextA = orientList[0] - math.atan2(tempArr[hull[nextA]][0][1] - tempArr[hull[attachedList[0]]][0][1], tempArr[hull[nextA]][0][0] - tempArr[hull[attachedList[0]]][0][0])
		
		angleToNextC = orientList[2] - math.atan2(tempArr[hull[nextC]][0][1] - tempArr[hull[attachedList[2]]][0][1], tempArr[hull[nextC]][0][0] - tempArr[hull[attachedList[2]]][0][0])
		angleToNextB = orientList[1] - math.atan2(tempArr[hull[nextB]][0][1] - tempArr[hull[attachedList[1]]][0][1], tempArr[hull[nextB]][0][0] - tempArr[hull[attachedList[1]]][0][0])
		angleToNextD = orientList[3] - math.atan2(tempArr[hull[nextD]][0][1] - tempArr[hull[attachedList[3]]][0][1], tempArr[hull[nextD]][0][0] - tempArr[hull[attachedList[3]]][0][0])
		
		angleToNextList = [angleToNextA, angleToNextB, angleToNextC, angleToNextD]
		
		for j in range(4):
			if angleToNextList[j] < 0:
				angleToNextList[j] = angleToNextList[j]	 + 2*math.pi
		
		minAngle = float('inf')
		minCallip = None
		for j in range(4):
			if angleToNextList[j] < minAngle:
				minAngle = angleToNextList[j]
				minCallip = j
		
		tempDiv = (tempArr[hull[nextList[minCallip]]][0][0] - tempArr[hull[attachedList[minCallip]]][0][0])
		slopeMainCallip=None
		mainCallipConstant=None
		if tempDiv !=0:
			slopeMainCallip = (tempArr[hull[nextList[minCallip]]][0][1] - tempArr[hull[attachedList[minCallip]]][0][1])/tempDiv
			mainCallipConstant = tempArr[hull[attachedList[minCallip]]][0][1] - tempArr[hull[attachedList[minCallip]]][0][0]*slopeMainCallip
		
		slopeOppositeCallip = slopeMainCallip
		oppositeCallipConstant=None
		if slopeOppositeCallip is not None:
			oppositeCallipConstant = tempArr[hull[attachedList[(minCallip+2)%4]]][0][1] - tempArr[hull[attachedList[(minCallip+2)%4]]][0][0]*slopeOppositeCallip
		
		slopeFirstAfterCallip=None
		firstAfterCallipConstant=None
		if slopeMainCallip == 0:
			pass
		elif slopeMainCallip is not None:
			slopeFirstAfterCallip = -1/slopeMainCallip
			firstAfterCallipConstant = tempArr[hull[attachedList[(minCallip+1)%4]]][0][1] - tempArr[hull[attachedList[(minCallip+1)%4]]][0][0]*slopeFirstAfterCallip
		else:
			slopeFirstAfterCallip = 0
			firstAfterCallipConstant = tempArr[hull[attachedList[(minCallip+1)%4]]][0][1]
		
		
		slopeThirdAfterCallip = slopeFirstAfterCallip
		thirdAfterCallipConstant=None
		if slopeThirdAfterCallip is not None:
			thirdAfterCallipConstant = tempArr[hull[attachedList[(minCallip+3)%4]]][0][1] - tempArr[hull[attachedList[(minCallip+3)%4]]][0][0]*slopeThirdAfterCallip
		
		if slopeThirdAfterCallip == slopeMainCallip or slopeFirstAfterCallip == slopeOppositeCallip or slopeFirstAfterCallip == slopeMainCallip or slopeThirdAfterCallip == slopeOppositeCallip:
			return None
		corner1X = 0
		corner1Y = 0
		if slopeThirdAfterCallip is None:
			corner1X = tempArr[hull[attachedList[(minCallip+3)%4]]][0][0]
			corner1Y = tempArr[hull[attachedList[minCallip]]][0][1]
		elif slopeMainCallip is None:
			corner1X = tempArr[hull[attachedList[minCallip]]][0][0]
			corner1Y = tempArr[hull[attachedList[(minCallip+3)%4]]][0][1]
		else:
			corner1X = (mainCallipConstant - thirdAfterCallipConstant)/(slopeThirdAfterCallip - slopeMainCallip)
			corner1Y = slopeThirdAfterCallip*corner1X + thirdAfterCallipConstant
		corner2X = 0
		corner2Y = 0
		if slopeFirstAfterCallip is None:
			corner2X = tempArr[hull[attachedList[(minCallip+1)%4]]][0][0]
			corner2Y = tempArr[hull[attachedList[minCallip]]][0][1]
		elif slopeMainCallip is None:
			corner2X = tempArr[hull[attachedList[minCallip]]][0][0]
			corner2Y = tempArr[hull[attachedList[(minCallip+1)%4]]][0][1]
		else:
			corner2X = (mainCallipConstant - firstAfterCallipConstant)/(slopeFirstAfterCallip - slopeMainCallip)
			corner2Y = slopeFirstAfterCallip*corner2X + firstAfterCallipConstant
		corner3X = 0
		corner3Y = 0
		if slopeFirstAfterCallip is None:
			corner3X = tempArr[hull[attachedList[(minCallip+1)%4]]][0][0]
			corner3Y = tempArr[hull[attachedList[(minCallip+2)%4]]][0][1]
		elif slopeOppositeCallip is None:
			corner3X = tempArr[hull[attachedList[(minCallip+2)%4]]][0][0]
			corner3Y = tempArr[hull[attachedList[(minCallip+1)%4]]][0][1]
		else:
			corner3X = (oppositeCallipConstant - firstAfterCallipConstant)/(slopeFirstAfterCallip - slopeOppositeCallip)
			corner3Y = slopeFirstAfterCallip*corner3X + firstAfterCallipConstant
		corner4X = 0
		corner4Y = 0
		if slopeThirdAfterCallip is None:
			corner4X = tempArr[hull[attachedList[(minCallip+3)%4]]][0][0]
			corner4Y = tempArr[hull[attachedList[(minCallip+2)%4]]][0][1]
		elif slopeOppositeCallip is None:
			corner4X = tempArr[hull[attachedList[(minCallip+2)%4]]][0][0]
			corner4Y = tempArr[hull[attachedList[(minCallip+3)%4]]][0][1]
		else:
			corner4X = (oppositeCallipConstant - thirdAfterCallipConstant)/(slopeThirdAfterCallip - slopeOppositeCallip)
			corner4Y = slopeThirdAfterCallip*corner4X + thirdAfterCallipConstant
		
		tempArea = (math.sqrt((corner2X-corner1X)**2+(corner2Y-corner1Y)**2)) * (math.sqrt((corner3X-corner2X)**2+(corner3Y-corner2Y)**2))
		if tempArea < minArea:
			rect = [[corner1X, corner1Y], [corner2X, corner2Y], [corner3X, corner3Y], [corner4X, corner4Y]]
		
		attachedList[minCallip] = nextList[minCallip]
		
		for j in range(4):
			tmpOr = orientList[j] - minAngle
			if tmpOr <= -math.pi:
				tmpOr += 2*math.pi
			orientList[j] = tmpOr
	
	return rect


def unoptimisedOOBTree(stepCoords, rawDat, tempInds, first): # for now just pick a roughly decent but mostly arbitrary way of grouping line segments and stuff, will be a lot of possible optimisations if needed
	
	tempTree = []
	
	if len(tempInds) >= 10:
		
		currOBB = None
		if first == False:
			currOBB = unoptimisedOOB(stepCoords, rawDat, tempInds)
			if currOBB is None:
				print('yeah weird @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
				return None
		
		splitAfter = 0
		maxDist = float('-inf')
		
		for i in range(len(tempInds)-1):
			rawDatInd1 = tempInds[i]
			stepCoordIndPair1 = rawDat[rawDatInd1][0]
			coord11 = stepCoords[stepCoordIndPair1[0]][0]
			coord12 = stepCoords[stepCoordIndPair1[1]][0]
			midPt1 = [(coord11[0] + coord12[0])/2, (coord11[1] + coord12[1])/2]
			
			rawDatInd2 = tempInds[i+1]
			stepCoordIndPair2 = rawDat[rawDatInd2][0]
			coord21 = stepCoords[stepCoordIndPair2[0]][0]
			coord22 = stepCoords[stepCoordIndPair2[1]][0]
			midPt2 = [(coord21[0] + coord22[0])/2, (coord21[1] + coord22[1])/2]
			
			dist = getDistance(midPt1[0], midPt2[0], midPt1[1], midPt2[1])
			
			if dist > maxDist:
				maxDist = dist
				splitAfter = i
		
		if splitAfter >= 0.2*len(tempInds) and splitAfter <= 0.8*len(tempInds):
			pass
		else:
			splitAfter = math.floor(len(tempInds)/2 - 1)
		
		
		leftBranch = unoptimisedOOBTree(stepCoords, rawDat, tempInds[:splitAfter+1], False)
		rightBranch = unoptimisedOOBTree(stepCoords, rawDat, tempInds[splitAfter+1:], False)
		
		if first:
			return [None, leftBranch, rightBranch]
		
		
		side1MagSq = (currOBB[1][0] - currOBB[0][0])*(currOBB[1][0] - currOBB[0][0]) + (currOBB[1][1] - currOBB[0][1])*(currOBB[1][1] - currOBB[0][1])
		side2MagSq = (currOBB[2][0] - currOBB[1][0])*(currOBB[2][0] - currOBB[1][0]) + (currOBB[2][1] - currOBB[1][1])*(currOBB[2][1] - currOBB[1][1])
		
		side1Slope = None
		side2Slope = None
		tempDiv = currOBB[1][0] - currOBB[0][0]
		if tempDiv != 0:
			side1Slope = (currOBB[1][1] - currOBB[0][1])/tempDiv
		
		if side1Slope is None:
			side2Slope = 0
		elif side1Slope != 0:
			side2Slope = -1/side1Slope
		
		side1C = None
		side2C = None
		side3C = None
		side4C = None
		
		if side1Slope is None:
			side1C = currOBB[1][0]
			side2C = currOBB[1][1]
			side3C = currOBB[3][0]
			side4C = currOBB[3][1]
		elif side1Slope == 0:
			side1C = currOBB[1][1]
			side2C = currOBB[1][0]
			side3C = currOBB[3][1]
			side4C = currOBB[3][0]
		else:
			side1C = currOBB[1][1]-side1Slope*currOBB[1][0]
			side2C = currOBB[1][1]-side2Slope*currOBB[1][0]
			side3C = currOBB[3][1]-side1Slope*currOBB[3][0]
			side4C = currOBB[3][1]-side2Slope*currOBB[3][0]
		
		side1LineEq = (side1Slope, side1C)
		side2LineEq = (side2Slope, side2C)
		side3LineEq = (side1Slope, side3C)
		side4LineEq = (side2Slope, side4C)
		
		obbDat = [side1MagSq, side2MagSq, side1LineEq, side2LineEq, side3LineEq, side4LineEq]
		
		tempTree = [1, leftBranch, rightBranch, currOBB, obbDat]
	
	else:
		if first:
			return [None, [0, tempInds], None]
		else:
			tempTree = [0, tempInds]
	
	return tempTree


def ciede2000DeltaE(hue1, sat1, val1, hue2, sat2, val2, params, pieceMaterialTest=None):
	lightnessConstantCMCDeltaE=params['lightnessConstantCMCDeltaE']
	colourConstantCMCDeltaE=params['colourConstantCMCDeltaE']
	
	pix1 = np.zeros([1,1,3]).astype(np.uint8)
	pix1[0][0][0] = min(int(round((hue1/360)*255)), 255)
	pix1[0][0][1] = min(int(round(sat1)), 255)
	pix1[0][0][2] = min(int(round(val1)), 255)

	pix1 = cv2.cvtColor(pix1 , cv2.COLOR_HSV2BGR_FULL)
	pix1 = cv2.cvtColor(pix1 , cv2.COLOR_BGR2Lab)
	
	labL = (pix1[0][0][0]/255)*100
	labA = pix1[0][0][1]-128
	labB = pix1[0][0][2]-128
	
	color1 = LabColor(lab_l=labL, lab_a=labA, lab_b=labB)

	pix1 = np.zeros([1,1,3]).astype(np.uint8)
	if pieceMaterialTest is None:
		pix1[0][0][0] = min(int(round((hue2/360)*255)), 255)
		pix1[0][0][1] = min(int(round(sat2)), 255)
		pix1[0][0][2] = min(int(round(val2)), 255)
		pix1 = cv2.cvtColor(pix1 , cv2.COLOR_HSV2BGR_FULL)
		pix1 = cv2.cvtColor(pix1 , cv2.COLOR_BGR2Lab)
	else:
		pix1 = pieceMaterialTest
	
	labL = (pix1[0][0][0]/255)*100
	labA = pix1[0][0][1]-128
	labB = pix1[0][0][2]-128
	
	color2 = LabColor(lab_l=labL, lab_a=labA, lab_b=labB)
	
	# delta_e = delta_e_cie2000(color1, color2)
	# delta_e = delta_e_cmc(color1, color2, pl=3, pc=1)
	# delta_e = delta_e_cmc(color1, color2, pl=4, pc=1)
	delta_e = delta_e_cmc(color1, color2, pl=lightnessConstantCMCDeltaE, pc=colourConstantCMCDeltaE)
	
	return delta_e


def updateCompatibility(trackerAndOtherData, largePieceDatabase, potentialPieceData, prelimCompatPairsInniesAndOutiesInds, params, debugdict, TAKE_SAMPLE=False):
	for i in range(len(trackerAndOtherData['innies'])-1):
		if not(TAKE_SAMPLE) or trackerAndOtherData['innies'][i][0] in samplePieceIDSet:
			for j in range(len(trackerAndOtherData['outies'])-1):
				if not(TAKE_SAMPLE) or trackerAndOtherData['outies'][j][0] in samplePieceIDSet:
				
					edgeIndInnie = trackerAndOtherData['innies'][i][12]
					edgeIndOutie = trackerAndOtherData['outies'][j][12]
					
					largePieceDbIndInnie = trackerAndOtherData['innies'][i][0]
					cornerRepInnie = trackerAndOtherData['innies'][i][1] # will always be 0 for now but accessing it from list for future
					pieceEdgeKeyInnie = trackerAndOtherData['innies'][i][2]
					potentialPieceDataIndInnie = largePieceDatabase[largePieceDbIndInnie][0]
					
					
					largePieceDbIndOutie = trackerAndOtherData['outies'][j][0]
					cornerRepOutie = trackerAndOtherData['outies'][j][1]
					pieceEdgeKeyOutie = trackerAndOtherData['outies'][j][2]
					potentialPieceDataIndOutie = largePieceDatabase[largePieceDbIndOutie][0]
					
					edgeViewInnie = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRepInnie][pieceEdgeKeyInnie][0]
					edgeViewOutie = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRepOutie][pieceEdgeKeyOutie][0]
					
					debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)] = []
					debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)] = []
					
					weirddebug=False
					# if potentialPieceDataIndInnie==32 and pieceEdgeKeyInnie=='rightEdge' and potentialPieceDataIndOutie==141 and pieceEdgeKeyOutie=='bottomEdge' or potentialPieceDataIndInnie==141 and pieceEdgeKeyInnie=='bottomEdge' and potentialPieceDataIndOutie==32 and pieceEdgeKeyOutie=='rightEdge':
						# weirddebug=True
					# if potentialPieceDataIndInnie==30 and pieceEdgeKeyInnie=='rightEdge' and potentialPieceDataIndOutie==114 and pieceEdgeKeyOutie=='bottomEdge' or potentialPieceDataIndInnie==114 and pieceEdgeKeyInnie=='bottomEdge' and potentialPieceDataIndOutie==30 and pieceEdgeKeyOutie=='rightEdge':
						# weirddebug=True
					# if potentialPieceDataIndInnie==26 and pieceEdgeKeyInnie=='leftEdge' and potentialPieceDataIndOutie==15 and pieceEdgeKeyOutie=='bottomEdge' or potentialPieceDataIndInnie==15 and pieceEdgeKeyInnie=='bottomEdge' and potentialPieceDataIndOutie==26 and pieceEdgeKeyOutie=='leftEdge':
						# weirddebug=True
					
					otherEdgeSegmentedDat = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRepInnie][pieceEdgeKeyInnie][5]
					mainEdgeSegmentedDat = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRepOutie][pieceEdgeKeyOutie][5]
					
					if weirddebug:
						if otherEdgeSegmentedDat is None or mainEdgeSegmentedDat is None:
							print(otherEdgeSegmentedDat)
							print()
							print()
							print(mainEdgeSegmentedDat)
							print(potentialPieceDataIndOutie)
							print(potentialPieceDataIndInnie)
							print('wat??')
							input("press enter")
					if otherEdgeSegmentedDat is not None and mainEdgeSegmentedDat is not None:
						
						queryDistFromCameraNormalisationVal = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRepOutie]['distFromCameraNormalisationVal']
						windowDistFromCameraNormalisationVal = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRepInnie]['distFromCameraNormalisationVal']
						
						estimatedScale = windowDistFromCameraNormalisationVal/queryDistFromCameraNormalisationVal
						
						# want innie flipped so they can be compared
						edgeViewInnie = np.flip(edgeViewInnie, 0)
						
						prelimCompat = False
						
						wingRatio1Innie = trackerAndOtherData['innies'][i][15]
						wingRatio2Innie = trackerAndOtherData['innies'][i][16]
						
						edgeSpanInnie = trackerAndOtherData['innies'][i][17]
						refCntrDatInnie = trackerAndOtherData['innies'][i][18]
						
						wingRatio1Outie = trackerAndOtherData['outies'][j][15]
						wingRatio2Outie = trackerAndOtherData['outies'][j][16]
						
						edgeSpanOutie = trackerAndOtherData['outies'][j][17]
						refCntrDatOutie = trackerAndOtherData['outies'][j][18]
						
						absoluteWingRatioDiffSimilarityThreshold = params['absoluteWingRatioDiffSimilarityThreshold']
						if abs(wingRatio1Innie-wingRatio1Outie)<=absoluteWingRatioDiffSimilarityThreshold and abs(wingRatio2Innie-wingRatio2Outie)<=absoluteWingRatioDiffSimilarityThreshold:
							prelimCompat = True
						
						if True:
							debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)].append((abs(wingRatio1Innie-wingRatio1Outie), abs(wingRatio2Innie-wingRatio2Outie), absoluteWingRatioDiffSimilarityThreshold))
							debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)].append((abs(wingRatio1Innie-wingRatio1Outie), abs(wingRatio2Innie-wingRatio2Outie), absoluteWingRatioDiffSimilarityThreshold))
						
						
						tmpNewPrelimCompat = False # for now just doing this so when debugging i can check if failed/passed this or the W1W2Err stuff above
						
						innieEdgeSpanEstimated = ((refCntrDatOutie[0]/refCntrDatInnie[0] + refCntrDatOutie[1]/refCntrDatInnie[1])/2)*edgeSpanInnie # in outie space, avg of scales between 2 diagonals
						innieEdgeSpanEstimatedInterval = [innieEdgeSpanEstimated*(1-params['scaleEstimationErrorReferencePointMethod']), innieEdgeSpanEstimated*(1+params['scaleEstimationErrorReferencePointMethod'])]
						
						
						if weirddebug:
							print(refCntrDatInnie)
							print(edgeSpanInnie)
							print(refCntrDatOutie)
							print(edgeSpanOutie)
							print(((refCntrDatOutie[0]/refCntrDatInnie[0] + refCntrDatOutie[1]/refCntrDatInnie[1])/2))
							print(((refCntrDatOutie[0]/refCntrDatInnie[0] + refCntrDatOutie[1]/refCntrDatInnie[1])/2)*edgeSpanInnie)
							print(innieEdgeSpanEstimatedInterval)
							print(refCntrDatOutie[0]/refCntrDatInnie[0])
							print(refCntrDatOutie[1]/refCntrDatInnie[1])
							# exit()
						
						if edgeSpanOutie>=innieEdgeSpanEstimatedInterval[0] and edgeSpanOutie<=innieEdgeSpanEstimatedInterval[1]:
							tmpNewPrelimCompat=True
						
						if True:
							debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)].append((innieEdgeSpanEstimatedInterval[0], edgeSpanOutie, innieEdgeSpanEstimatedInterval[1]))
							debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)].append((innieEdgeSpanEstimatedInterval[0], edgeSpanOutie, innieEdgeSpanEstimatedInterval[1]))
						
						
						if weirddebug:
							if not(prelimCompat) or not(tmpNewPrelimCompat):
								print('wat33??')
								print(prelimCompat)
								print(tmpNewPrelimCompat)
								print((wingRatio1Innie-wingRatio1Outie))
								print((wingRatio2Innie-wingRatio2Outie))
								print(absoluteWingRatioDiffSimilarityThreshold)
								input("press enter")
						
						# for now just keep both
						if not(prelimCompat) or not(tmpNewPrelimCompat): # for readability, obv if not(prelimCompat) then prelimCompat is already False
							prelimCompat=False
						
						
						if prelimCompat == True:
							prelimCompat = False
							innieW1Orient = trackerAndOtherData['innies'][i][8] # w.r.t. line of edge span
							innieW2Orient = trackerAndOtherData['innies'][i][9]
							
							outieW1Orient = trackerAndOtherData['outies'][j][8] # w.r.t. line of edge span
							outieW2Orient = trackerAndOtherData['outies'][j][9]
							
							wing1OrientDiff = innieW1Orient-outieW1Orient
							wing2OrientDiff = innieW2Orient-outieW2Orient
							
							while wing1OrientDiff <= -math.pi:
								wing1OrientDiff+=2*math.pi
							while wing2OrientDiff <= -math.pi:
								wing2OrientDiff+=2*math.pi
							while wing1OrientDiff > math.pi:
								wing1OrientDiff-=2*math.pi
							while wing2OrientDiff > math.pi:
								wing2OrientDiff-=2*math.pi
							if abs(wing1OrientDiff-math.pi)<0.0001:
								wing1OrientDiff=math.pi
							elif abs(wing1OrientDiff--math.pi)<0.0001:
								wing1OrientDiff=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							if abs(wing2OrientDiff-math.pi)<0.0001:
								wing2OrientDiff=math.pi
							elif abs(wing2OrientDiff--math.pi)<0.0001:
								wing2OrientDiff=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							
							if weirddebug:
								if not(abs(wing1OrientDiff) <= params['wingOrientDiffThreshold'] and abs(wing2OrientDiff) <= params['wingOrientDiffThreshold']):
									print(abs(wing1OrientDiff))
									print(abs(wing2OrientDiff))
									print(params['wingOrientDiffThreshold'])
									print('wat444??')
									input("press enter")
							
							if abs(wing1OrientDiff) <= params['wingOrientDiffThreshold'] and abs(wing2OrientDiff) <= params['wingOrientDiffThreshold']: # 10 degrees? if too strict maybe 15?
								
								if True:
									debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)].append((abs(wing1OrientDiff), abs(wing2OrientDiff), math.pi/18))
									debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)].append((abs(wing1OrientDiff), abs(wing2OrientDiff), math.pi/18))
								
								if largePieceDbIndInnie != largePieceDbIndOutie:
									
									innieSeedDatDict = {} # name the seeds then check if exist in both edges later when calcing similarity
									outieSeedDatDict = {}
									
									seedDictInnie = trackerAndOtherData['innies'][i][11]
									seedDictOutie = trackerAndOtherData['outies'][j][11]
									
									# NOTE!!!! the seedDict key for innie will be nubSideDefect2 and for outie nubSideDefect1
									# because they are flipped because some innie dat is flipped
									# BUT from here on at the higher level ill just name them both nubSeed1.
									
									# new
									seedDictKeyListInnie = ['nubSideDefect2', 'nubSideDefect1']
									seedDictKeyListOutie = ['nubSideDefect1', 'nubSideDefect2']
									seedNameList = ['nubSeed1', 'nubSeed2']
									
									for tmpSeedDictI in range(len(seedDictKeyListInnie)):
										
										seedDictKeyInnie = seedDictKeyListInnie[tmpSeedDictI]
										seedDictKeyOutie = seedDictKeyListOutie[tmpSeedDictI]
										
										innieSeedIndAsRatio = edgeViewInnie.shape[0]-1 - seedDictInnie[seedDictKeyInnie] # flip coordInd
										outieSeedIndAsRatio = seedDictOutie[seedDictKeyOutie]
										
										innieRatioOnLine = innieSeedIndAsRatio-math.floor(innieSeedIndAsRatio)
										tmpC1 = edgeViewInnie[math.floor(innieSeedIndAsRatio)][0]
										tmpC2 = edgeViewInnie[math.floor(innieSeedIndAsRatio)+1][0]
										seedCoordInnieX = tmpC1[0] + (tmpC2[0]-tmpC1[0])*innieRatioOnLine
										seedCoordInnieY = tmpC1[1] + (tmpC2[1]-tmpC1[1])*innieRatioOnLine
										seedCoordInnie=[seedCoordInnieX, seedCoordInnieY]
										
										
										outieRatioOnLine = outieSeedIndAsRatio-math.floor(outieSeedIndAsRatio)
										tmpC1 = edgeViewOutie[math.floor(outieSeedIndAsRatio)][0]
										tmpC2 = edgeViewOutie[math.floor(outieSeedIndAsRatio)+1][0]
										seedCoordOutieX = tmpC1[0] + (tmpC2[0]-tmpC1[0])*outieRatioOnLine
										seedCoordOutieY = tmpC1[1] + (tmpC2[1]-tmpC1[1])*outieRatioOnLine
										seedCoordOutie=[seedCoordOutieX, seedCoordOutieY]
										
										
										seedDatInnie = [innieSeedIndAsRatio, seedCoordInnie]
										seedDatOutie = [outieSeedIndAsRatio, seedCoordOutie]
										
										innieSeedDatDict[seedNameList[tmpSeedDictI]]=seedDatInnie
										outieSeedDatDict[seedNameList[tmpSeedDictI]]=seedDatOutie
									
									
									tempColourCompatibility = True
									
									avgColourDatInnie=None
									avgColourDatInnie2=None
									avgColourDatOutie=None
									avgColourDatOutie2=None
									
									if trackerAndOtherData['innies'][i][14] is not None:
										avgColourDatInnie = trackerAndOtherData['innies'][i][14][0]
										avgColourDatInnie2 = trackerAndOtherData['innies'][i][14][1]
									if trackerAndOtherData['outies'][j][14] is not None:
										avgColourDatOutie = trackerAndOtherData['outies'][j][14][0]
										avgColourDatOutie2 = trackerAndOtherData['outies'][j][14][1]
									if avgColourDatInnie is None or avgColourDatOutie is None:
										tempColourCompatibility=False
									else:
										failedMatchingQuarterAmt=0
										for colDatI in range(len(avgColourDatInnie)):
											colourAngle1 = avgColourDatInnie[colDatI][0]
											colourAngle2 = avgColourDatOutie[colDatI][0]
											colourVal1 = avgColourDatInnie[colDatI][2]
											colourVal2 = avgColourDatOutie[colDatI][2]
											colourSat1 = avgColourDatInnie[colDatI][1]
											colourSat2 = avgColourDatOutie[colDatI][1]
											
											
											thresholdedSaturationColourAngle1=None
											thresholdedSaturationColourVal1=None
											thresholdedSaturationColourSat1=None
											thresholdedSaturationColourAngle2=None
											thresholdedSaturationColourVal2=None
											thresholdedSaturationColourSat2=None
											
											if avgColourDatInnie2[colDatI] is not None:
												thresholdedSaturationColourAngle1 = avgColourDatInnie2[colDatI][0]
												thresholdedSaturationColourVal1 = avgColourDatInnie2[colDatI][2]
												thresholdedSaturationColourSat1 = avgColourDatInnie2[colDatI][1]
												
											if avgColourDatOutie2[colDatI] is not None:
												thresholdedSaturationColourAngle2 = avgColourDatOutie2[colDatI][0]
												thresholdedSaturationColourVal2 = avgColourDatOutie2[colDatI][2]
												thresholdedSaturationColourSat2 = avgColourDatOutie2[colDatI][1]
											
											basicallyBlackColVal = params['basicallyBlackColVal']
											basicallyGreyColSat = params['basicallyGreyColSat']
											
											ciede2000DeltaESimilarThresh = params['ciede2000DeltaESimilarThresh']
											
											if colourVal1>basicallyBlackColVal or colourVal2>basicallyBlackColVal: # else theyre both basically black so hue doesnt mean anything (33 = ~13% of 255)
												if colourSat1>basicallyGreyColSat or colourSat2>basicallyGreyColSat:
													
													if weirddebug:
														print(colourAngle1)
														print(colourAngle2)
														print(abs(colourAngle1 - colourAngle2))
														print(abs(colourAngle1 - colourAngle2) % 360)
														print(360 - (abs(colourAngle1 - colourAngle2) % 360))
														print(params['maxColourHueAngleDiff'])
													
													deltaE2000_2=None
													deltaE2000_3=None
													deltaE2000_4=None
													
													deltaE2000 = ciede2000DeltaE(colourAngle1, colourSat1, colourVal1, colourAngle2, colourSat2, colourVal2, params)
													if thresholdedSaturationColourAngle1 is not None:
														deltaE2000_2 = ciede2000DeltaE(thresholdedSaturationColourAngle1, thresholdedSaturationColourSat1, thresholdedSaturationColourVal1, colourAngle2, colourSat2, colourVal2, params)
													if thresholdedSaturationColourAngle2 is not None:
														deltaE2000_3 = ciede2000DeltaE(colourAngle1, colourSat1, colourVal1, thresholdedSaturationColourAngle2, thresholdedSaturationColourSat2, thresholdedSaturationColourVal2, params)
													if thresholdedSaturationColourAngle1 is not None and thresholdedSaturationColourAngle2 is not None:
														deltaE2000_4 = ciede2000DeltaE(thresholdedSaturationColourAngle1, thresholdedSaturationColourSat1, thresholdedSaturationColourVal1, thresholdedSaturationColourAngle2, thresholdedSaturationColourSat2, thresholdedSaturationColourVal2, params)
													
													if True:
														debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)].append((deltaE2000, ciede2000DeltaESimilarThresh))
														debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)].append((deltaE2000, ciede2000DeltaESimilarThresh))
													
													if weirddebug:
														print("deltaE2000")
														print(deltaE2000)
														print("deltaE2000_2")
														print(deltaE2000_2)
														print("deltaE2000_3")
														print(deltaE2000_3)
														print("deltaE2000_4")
														print(deltaE2000_4)
													
													if deltaE2000>ciede2000DeltaESimilarThresh:
														if deltaE2000_2 is None or deltaE2000_2>ciede2000DeltaESimilarThresh:
															if deltaE2000_3 is None or deltaE2000_3>ciede2000DeltaESimilarThresh:
																if deltaE2000_4 is None or deltaE2000_4>ciede2000DeltaESimilarThresh:
																	
																	failedMatchingQuarterAmt+=1
																	if failedMatchingQuarterAmt>(params['splitColourEdgeArcLengthInto']-params['minColourMatchingQuartersAmt']):
																		tempColourCompatibility=False
																		break
									
									if weirddebug:
										print(tempColourCompatibility)
										print("wat??")
										print(avgColourDatInnie)
										print(avgColourDatOutie)
										print(avgColourDatInnie2)
										print(avgColourDatOutie2)
										print(potentialPieceDataIndInnie)
										print(potentialPieceDataIndOutie)
										input("wat??e3")
									
									if True:
										debugdict[(potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie)].append('hi')
										debugdict[(potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie)].append('hi')
									
									prelimCompatPairsInniesAndOutiesInds[largePieceDbIndInnie][edgeIndInnie].append([0, i, j, largePieceDbIndOutie, edgeIndOutie, False, None, None, None, None, tempColourCompatibility, outieSeedDatDict, innieSeedDatDict])
									prelimCompatPairsInniesAndOutiesInds[largePieceDbIndOutie][edgeIndOutie].append([1, i, j, largePieceDbIndInnie, edgeIndInnie, False, None, None, None, None, tempColourCompatibility, innieSeedDatDict, outieSeedDatDict]) # None+ is bestPrelimSimScore, bestPrelimQueryStepCoordsIndsGroups, bestShiftedSeedPairDat , allTestsListInd
								
	return



totaltime=0
time1=0
time2=0
time3=0
time4=0
time5=0

def partialPieceDataSimilarityController(trackerAndOtherData, largePieceDatabase, potentialPieceData, params, hsvImgDict):
	# most of this is kinda temporary jerry-rigging, gonna forget about stuff like multiple corner represenations and stuff for now prob
	
	global totaltime
	global time1
	global time2
	global time3
	global time4
	global time5
	
	tmpt1a=time.perf_counter()
	
	prelimCompatPairsInniesAndOutiesInds = []
	
	for i in range(len(largePieceDatabase)):
		prelimCompatPairsInniesAndOutiesInds.append([])
		for j in range(len(largePieceDatabase[i][1][0])): # [0] cause only using 1 corner representation for now
			prelimCompatPairsInniesAndOutiesInds[-1].append([])
	
	# prelimCompatPairsInniesAndOutiesInds should be synced with largePieceDatabase now
	
	debugdict={}
	updateCompatibility(trackerAndOtherData, largePieceDatabase, potentialPieceData, prelimCompatPairsInniesAndOutiesInds, params, debugdict)
	
	efficientOrderCompatibilityView = []
	for i in range(len(prelimCompatPairsInniesAndOutiesInds)):
		for j in range(len(prelimCompatPairsInniesAndOutiesInds[i])):
			atLeastOneColourCompatible = False
			for k in range(len(prelimCompatPairsInniesAndOutiesInds[i][j])):
				if prelimCompatPairsInniesAndOutiesInds[i][j][k][10]==True:
					atLeastOneColourCompatible=True
					break
			if atLeastOneColourCompatible: # readability
				efficientOrderCompatibilityView.append([len(prelimCompatPairsInniesAndOutiesInds[i][j]), i, j, True])
			else:
				efficientOrderCompatibilityView.append([len(prelimCompatPairsInniesAndOutiesInds[i][j]), i, j, False])
	
	efficientOrderCompatibilityView.sort() # sort by edges with least amount of compabitilities that they have with other edges
	
	insanelyBadCodeDoneICPsimilarityTrackerSet = set()
	
	testResults = []
	
	weirdTimerTotal1=0
	weirdTimerTotal2=0
	weirdTotalTimePasseda=time.perf_counter()
	for efficientCompatDat in efficientOrderCompatibilityView:
		
		if True:
			print(weirdTimerTotal1)
			print(weirdTimerTotal2)
			print("total time passed: " + str(time.perf_counter()-weirdTotalTimePasseda))
		if efficientCompatDat[3]:
			compatDats = prelimCompatPairsInniesAndOutiesInds[efficientCompatDat[1]][efficientCompatDat[2]]
			
			for compatDat in compatDats:
				weirdTmpTimer1a=time.perf_counter()
				
				trackerAndOtherDataIndInnie=None
				trackerAndOtherDataIndOutie=None
				largePieceDbIndInnie=None
				largePieceDbIndOutie=None
				edgeIndInnie=None
				edgeIndOutie=None
				innieSeedDatDict=None
				outieSeedDatDict=None
				if compatDat[0]==0:
					trackerAndOtherDataIndInnie=compatDat[1]
					trackerAndOtherDataIndOutie=compatDat[2]
					largePieceDbIndInnie=efficientCompatDat[1]
					largePieceDbIndOutie=compatDat[3]
					edgeIndInnie=efficientCompatDat[2]
					edgeIndOutie=compatDat[4]
					outieSeedDatDict=compatDat[11]
					innieSeedDatDict=compatDat[12]
				else:
					trackerAndOtherDataIndInnie=compatDat[1]
					trackerAndOtherDataIndOutie=compatDat[2]
					largePieceDbIndInnie=compatDat[3]
					largePieceDbIndOutie=efficientCompatDat[1]
					edgeIndInnie=compatDat[4]
					edgeIndOutie=efficientCompatDat[2]
					outieSeedDatDict=compatDat[12]
					innieSeedDatDict=compatDat[11]
				
				cornerRep = 0 # just using this for now
				
				potentialPieceDataIndOutie=largePieceDatabase[largePieceDbIndOutie][0]
				potentialPieceDataIndInnie=largePieceDatabase[largePieceDbIndInnie][0]
				
				pieceEdgeKeyOutie=trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][2]
				pieceEdgeKeyInnie=trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][2]
				
				stepCoordsOutie = largePieceDatabase[largePieceDbIndOutie][1][cornerRep][edgeIndOutie][3]
				stepCoordsInnie = largePieceDatabase[largePieceDbIndInnie][1][cornerRep][edgeIndInnie][3]
				
				stepCoordsMain=stepCoordsOutie
				stepCoordsOther=stepCoordsInnie
				
				mainEdgeSegmentedDat = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRep][pieceEdgeKeyOutie][5]
				otherEdgeSegmentedDat = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRep][pieceEdgeKeyInnie][5]
				
				weirdTmpTimer1b=time.perf_counter()
				weirdTimerTotal1+=weirdTmpTimer1b-weirdTmpTimer1a
				#New
				
				seedNameList = ['nubSeed1', 'nubSeed2']
				for seedI, seedName in enumerate(seedNameList):
					if ((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)) not in insanelyBadCodeDoneICPsimilarityTrackerSet:
						
						weirdTmpTimer2a=time.perf_counter()
						
						mainSeedCoordIndRatio = outieSeedDatDict[seedName][0]
						otherSeedCoordIndRatio = innieSeedDatDict[seedName][0]
						
						mainEdgeTransformedReferenceContourDat = trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][18]
						otherEdgeTransformedReferenceContourDat = trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][18]
						
						colourCompatibility = compatDat[10]
						
						weirdTmpTimer2b=time.perf_counter()
						weirdTimerTotal2+=weirdTmpTimer2b-weirdTmpTimer2a
						
						if colourCompatibility:
							if ((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)) not in insanelyBadCodeDoneICPsimilarityTrackerSet:
								
								mainSeedCoord = outieSeedDatDict[seedName][1]
								otherSeedCoord = innieSeedDatDict[seedName][1]
								
								mainEdgeTransformedCentreImagePointBase = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRep][pieceEdgeKeyOutie][3]
								otherEdgeTransformedCentreImagePointBase = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRep][pieceEdgeKeyInnie][3]
								
								mainContourIndRatioIntervalsForPlanes = mainEdgeSegmentedDat[5]
								otherContourIndRatioIntervalsForPlanes = otherEdgeSegmentedDat[5]
								mainSeedPlane = None
								otherSeedPlane = None
								for planeDatI, planeDat in enumerate(mainContourIndRatioIntervalsForPlanes):
									for planeContourIndInterval in planeDat:
										if mainSeedCoordIndRatio>=planeContourIndInterval[0] and mainSeedCoordIndRatio<=planeContourIndInterval[1]:
											mainSeedPlane=planeDatI
											break
									if mainSeedPlane is not None:
										break
								for planeDatI, planeDat in enumerate(otherContourIndRatioIntervalsForPlanes):
									for planeContourIndInterval in planeDat:
										if otherSeedCoordIndRatio>=planeContourIndInterval[0] and otherSeedCoordIndRatio<=planeContourIndInterval[1]:
											otherSeedPlane=planeDatI
											break
									if otherSeedPlane is not None:
										break
								
								if mainSeedPlane is not None and otherSeedPlane is not None:
									rememberParams={}
									rememberParams['sampledEdgeIsSpacedEnoughToUseOnly3PointsForTangentEstimation']=True
									rememberParams['mainEdgeBarelySampled']=True
									
									tmpt2a=time.perf_counter()
									tmpSimilarityScore = icpSimilarityGeneralCase(mainEdgeSegmentedDat, otherEdgeSegmentedDat, rememberParams, mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase, mainSeedCoord, otherSeedCoord, mainSeedPlane, otherSeedPlane, mainSeedCoordIndRatio, otherSeedCoordIndRatio, stepCoordsMain, stepCoordsOther, params, potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceData, None, False, mainEdgeTransformedReferenceContourDat, otherEdgeTransformedReferenceContourDat) # SHOULD WORK IN MAJORITY OF CASES
									tmpt2b=time.perf_counter()
									time1+=tmpt2b-tmpt2a
									
									if tmpSimilarityScore is not None and tmpSimilarityScore[0]!='rerun':
										mainDrawPointInOriginalPlacement = trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][13]
										otherDrawPointInOriginalPlacement = trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][13]
										testResults.append((tmpSimilarityScore[0], potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, mainDrawPointInOriginalPlacement, otherDrawPointInOriginalPlacement, tmpSimilarityScore[1], tmpSimilarityScore[2], mainEdgeSegmentedDat, otherEdgeSegmentedDat, tmpSimilarityScore[3], tmpSimilarityScore[4], mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase))
										insanelyBadCodeDoneICPsimilarityTrackerSet.add(((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)))
										
									elif tmpSimilarityScore is not None and tmpSimilarityScore[0]=='rerun':
											
										tmpt3a=time.perf_counter()
										tmpSimilarityScore = icpSimilarityGeneralCase(otherEdgeSegmentedDat, mainEdgeSegmentedDat, rememberParams, otherEdgeTransformedCentreImagePointBase, mainEdgeTransformedCentreImagePointBase, otherSeedCoord, mainSeedCoord, otherSeedPlane, mainSeedPlane, otherSeedCoordIndRatio, mainSeedCoordIndRatio, stepCoordsOther, stepCoordsMain, params, potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceData, None, False, mainEdgeTransformedReferenceContourDat, otherEdgeTransformedReferenceContourDat) # SHOULD WORK IN MAJORITY OF CASES
										tmpt3b=time.perf_counter()
										time2+=tmpt3b-tmpt3a
										
										if tmpSimilarityScore is not None and tmpSimilarityScore[0]!='rerun':
											mainDrawPointInOriginalPlacement = trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][13]
											otherDrawPointInOriginalPlacement = trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][13]
											testResults.append((tmpSimilarityScore[0], potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, mainDrawPointInOriginalPlacement, otherDrawPointInOriginalPlacement, tmpSimilarityScore[2], tmpSimilarityScore[1], mainEdgeSegmentedDat, otherEdgeSegmentedDat, tmpSimilarityScore[3], tmpSimilarityScore[4], mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase))
											insanelyBadCodeDoneICPsimilarityTrackerSet.add(((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)))
											
										elif tmpSimilarityScore is not None and tmpSimilarityScore[0]=='rerun':
											tmpSimilarityScore = icpSimilarityGeneralCase(mainEdgeSegmentedDat, otherEdgeSegmentedDat, rememberParams, mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase, mainSeedCoord, otherSeedCoord, mainSeedPlane, otherSeedPlane, mainSeedCoordIndRatio, otherSeedCoordIndRatio, stepCoordsMain, stepCoordsOther, params, potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceData, None, False, mainEdgeTransformedReferenceContourDat, otherEdgeTransformedReferenceContourDat, disjointPlanePairs=True)
											if tmpSimilarityScore is not None and tmpSimilarityScore[0]!='rerun':
												mainDrawPointInOriginalPlacement = trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][13]
												otherDrawPointInOriginalPlacement = trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][13]
												testResults.append((tmpSimilarityScore[0], potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, mainDrawPointInOriginalPlacement, otherDrawPointInOriginalPlacement, tmpSimilarityScore[2], tmpSimilarityScore[1], mainEdgeSegmentedDat, otherEdgeSegmentedDat, tmpSimilarityScore[3], tmpSimilarityScore[4], mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase))
												insanelyBadCodeDoneICPsimilarityTrackerSet.add(((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)))
											elif seedI==len(seedNameList)-1 and tmpSimilarityScore is not None and tmpSimilarityScore[0]=='rerun':
												lastResort=True
												tmpSimilarityScore = icpSimilarityGeneralCase(mainEdgeSegmentedDat, otherEdgeSegmentedDat, rememberParams, mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase, mainSeedCoord, otherSeedCoord, mainSeedPlane, otherSeedPlane, mainSeedCoordIndRatio, otherSeedCoordIndRatio, stepCoordsMain, stepCoordsOther, params, potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceData, None, False, mainEdgeTransformedReferenceContourDat, otherEdgeTransformedReferenceContourDat, lastResort=lastResort)
												if tmpSimilarityScore is not None and tmpSimilarityScore[0]!='rerun':
													mainDrawPointInOriginalPlacement = trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][13]
													otherDrawPointInOriginalPlacement = trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][13]
													testResults.append((tmpSimilarityScore[0], potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, mainDrawPointInOriginalPlacement, otherDrawPointInOriginalPlacement, tmpSimilarityScore[2], tmpSimilarityScore[1], mainEdgeSegmentedDat, otherEdgeSegmentedDat, tmpSimilarityScore[3], tmpSimilarityScore[4], mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase))
													insanelyBadCodeDoneICPsimilarityTrackerSet.add(((potentialPieceDataIndOutie, pieceEdgeKeyOutie, cornerRep), (potentialPieceDataIndInnie, pieceEdgeKeyInnie, cornerRep)))
									
								else:
									print("rip, seed isnt anywhere within processed planes 28j1e2")
								
	
	testResults.sort()
	
	compatDatAmt=0
	if True:
		print()
		print()
		print()
		for efficientCompatDat in efficientOrderCompatibilityView:
			compatDats = prelimCompatPairsInniesAndOutiesInds[efficientCompatDat[1]][efficientCompatDat[2]]
			
			for compatDat in compatDats:
				trackerAndOtherDataIndInnie=None
				trackerAndOtherDataIndOutie=None
				largePieceDbIndInnie=None
				largePieceDbIndOutie=None
				edgeIndInnie=None
				edgeIndOutie=None
				innieSeedDatDict=None
				outieSeedDatDict=None
				if compatDat[0]==0:
					trackerAndOtherDataIndInnie=compatDat[1]
					trackerAndOtherDataIndOutie=compatDat[2]
					largePieceDbIndInnie=efficientCompatDat[1]
					largePieceDbIndOutie=compatDat[3]
					edgeIndInnie=efficientCompatDat[2]
					edgeIndOutie=compatDat[4]
					outieSeedDatDict=compatDat[11]
					innieSeedDatDict=compatDat[12]
				else:
					trackerAndOtherDataIndInnie=compatDat[1]
					trackerAndOtherDataIndOutie=compatDat[2]
					largePieceDbIndInnie=compatDat[3]
					largePieceDbIndOutie=efficientCompatDat[1]
					edgeIndInnie=compatDat[4]
					edgeIndOutie=efficientCompatDat[2]
					outieSeedDatDict=compatDat[12]
					innieSeedDatDict=compatDat[11]
				
				cornerRep = 0 # just using this for now
				
				potentialPieceDataIndOutie=largePieceDatabase[largePieceDbIndOutie][0]
				potentialPieceDataIndInnie=largePieceDatabase[largePieceDbIndInnie][0]
				
				pieceEdgeKeyOutie=trackerAndOtherData['outies'][trackerAndOtherDataIndOutie][2]
				pieceEdgeKeyInnie=trackerAndOtherData['innies'][trackerAndOtherDataIndInnie][2]
				
				print('['+str(potentialPieceDataIndOutie)+', '+str(pieceEdgeKeyOutie)+', '+str(potentialPieceDataIndInnie)+', '+str(pieceEdgeKeyInnie)+']')
				colourCompatibility = compatDat[10]
				if colourCompatibility:
					compatDatAmt+=1
		
		print()
		print()
		print()
	
	compatDatAmt=compatDatAmt/2
	
	print()
	print()
	print()
	for i in range(len(trackerAndOtherData["innies"])):
		largdbind = trackerAndOtherData["innies"][i][0]
		tmpokey = trackerAndOtherData["innies"][i][2]
		potInd = largePieceDatabase[largdbind][0]
		repPt = trackerAndOtherData['innies'][i][13]
		imgStr = potentialPieceData[potInd]["imgref"]
		
		print("["+str(repPt[0])+", "+str(repPt[1])+"]	   "+str(potInd)+"	 "+tmpokey + ", "+imgStr)
	for i in range(len(trackerAndOtherData["outies"])):
		largdbind = trackerAndOtherData["outies"][i][0]
		tmpokey = trackerAndOtherData["outies"][i][2]
		potInd = largePieceDatabase[largdbind][0]
		repPt = trackerAndOtherData['outies'][i][13]
		imgStr = potentialPieceData[potInd]["imgref"]
		
		print("["+str(repPt[0])+", "+str(repPt[1])+"]	   "+str(potInd)+"	 "+tmpokey + ", "+imgStr)
	print()
	print()
	print()
	
	
	knownMatches = []
	# knownMatches.append((9, 'topEdge', 55, 'leftEdge'))
	# knownMatches.append((51, 'bottomEdge', 129, 'leftEdge'))
	# knownMatches.append((38, 'rightEdge', 64, 'bottomEdge'))
	# knownMatches.append((76, 'rightEdge', 21, 'rightEdge'))
	# knownMatches.append((157, 'topEdge', 68, 'leftEdge'))
	# knownMatches.append((140, 'rightEdge', 48, 'leftEdge'))
	# knownMatches.append((66, 'topEdge', 63, 'leftEdge'))
	# knownMatches.append((116, 'topEdge', 135, 'leftEdge'))
	# knownMatches.append((134, 'rightEdge', 109, 'rightEdge'))
	# knownMatches.append((100, 'bottomEdge', 128, 'rightEdge'))
	# knownMatches.append((69, 'bottomEdge', 119, 'leftEdge'))
	# knownMatches.append((74, 'topEdge', 26, 'leftEdge'))
	# knownMatches.append((109, 'topEdge', 46, 'leftEdge'))
	# knownMatches.append((29, 'bottomEdge', 134, 'leftEdge'))
	# knownMatches.append(())
	# knownMatches.append(())
	
	
	totalKnownMatchesThisTime=0
	
	for testRes in testResults:
		print(list(testRes[:5]) + debugdict[(testRes[1], testRes[2], testRes[3], testRes[4])])
		for knownMatch in knownMatches:
			if testRes[1]==knownMatch[0] and testRes[2]==knownMatch[1] and testRes[3]==knownMatch[2] and testRes[4]==knownMatch[3]:
				print('^^^^^^^^^^^^^^^')
				totalKnownMatchesThisTime+=1
	
	
	
	
	tmpt1b=time.perf_counter()
	totaltime=tmpt1b-tmpt1a
	print(totaltime)
	print()
	print(time1)
	print(time2)
	print(time3)
	print(time4)
	print()
	print(time1/totaltime)
	print(time2/totaltime)
	print(time3/totaltime)
	print(time4/totaltime)
	print('totalKnownMatchesThisTime:')
	print(totalKnownMatchesThisTime)
	
	
	print("testResults")
	print(len(testResults))
	print("compatabilities")
	print(compatDatAmt)
	
	for i in range(len(testResults)):
		if True: # i<100:
			putIt = (540, 660)
			
			print(testResults[i][:5])
			print(testResults[i][12])
			
			img_contours1 = hsvImgDict[potentialPieceData[testResults[i][1]]["imgref"]]
			img_contours1 = cv2.cvtColor(img_contours1.copy(), cv2.COLOR_HSV2BGR_FULL)
			
			img_contours2 = hsvImgDict[potentialPieceData[testResults[i][3]]["imgref"]]
			img_contours2 = cv2.cvtColor(img_contours2.copy(), cv2.COLOR_HSV2BGR_FULL)
			
			tmpC1 = testResults[i][5]
			tmpC2 = testResults[i][6]
			
			tupleFormat = (int(round(tmpC1[0])), int(round(tmpC1[1])))
			cv2.circle(img_contours1,tupleFormat,8,[0,0,255],-1)
			
			tupleFormat = (int(round(tmpC2[0])), int(round(tmpC2[1])))
			cv2.circle(img_contours2,tupleFormat,8,[0,0,255],-1)
			
			modif1 = 0
			
			if len(testResults[i][7])>0 and len(testResults[i][7][0])>0 and len(testResults[i][7][0][0])>0 and len(testResults[i][7][0][0][0])>0:
				if len(testResults[i][9])>0 and len(testResults[i][9][0])>0 and len(testResults[i][9][0][0])>0 and len(testResults[i][9][0][0][0])>0:
					if len(testResults[i][10])>0 and len(testResults[i][10][0])>0 and len(testResults[i][10][0][0])>0 and len(testResults[i][10][0][0][0])>0:
						tmpTrans = (putIt[0]-int(round(testResults[i][7][0][0][0][0]))+200, putIt[1]-int(round(testResults[i][7][0][0][0][1])))
						for tmpPlane in testResults[i][7]:
							for tmpSeg in tmpPlane:
								for tmpCoord in tmpSeg:
									tupleFormat = (int(round(tmpCoord[0]))+modif1+tmpTrans[0], int(round(tmpCoord[1]))+tmpTrans[1])
									cv2.circle(img_contours1,tupleFormat,0,[0,0,255],-1)
						
						for tmpPlane in testResults[i][8]:
							for tmpSeg in tmpPlane:
								for tmpCoord in tmpSeg:
									tupleFormat = (int(round(tmpCoord[0]))+modif1+tmpTrans[0], int(round(tmpCoord[1]))+tmpTrans[1])
									cv2.circle(img_contours1,tupleFormat,0,[255,0,0],-1)
						
						
						colSwitch=False
						modif1 = 0
						
						tmpTrans = (putIt[0]-int(round(testResults[i][9][0][0][0][0][0])), putIt[1]-int(round(testResults[i][9][0][0][0][0][1])))
						for tmpPlane in testResults[i][9][0]:
							for tmpSeg in tmpPlane:
								for tmpCoord in tmpSeg:
									
									tupleFormat = (int(round(tmpCoord[0]))+tmpTrans[0], int(round(tmpCoord[1]))+tmpTrans[1])
									if colSwitch:
										cv2.circle(img_contours1,tupleFormat,0,[0,255,255],-1)
									else:
										cv2.circle(img_contours1,tupleFormat,0,[0,255,0],-1)
							colSwitch=True
						colSwitch=False
						modif1 = 0
						tmpTrans = (putIt[0]-int(round(testResults[i][10][0][0][0][0][0])), putIt[1]-int(round(testResults[i][10][0][0][0][0][1]))+70)
						for tmpPlane in testResults[i][10][0]:
							for tmpSeg in tmpPlane:
								for tmpCoord in tmpSeg:
									tupleFormat = (int(round(tmpCoord[0]))+100*modif1+tmpTrans[0], int(round(tmpCoord[1]))+50*modif1+tmpTrans[1])
									if colSwitch:
										cv2.circle(img_contours2,tupleFormat,0,[255,0,255],-1)
									else:
										cv2.circle(img_contours2,tupleFormat,0,[255,255,0],-1)
							colSwitch=True
						
						for tmpCorr in testResults[i][11]:
							tup1 = (tmpCorr[0][0]-15, tmpCorr[0][1]-15)
							tup2 = (tmpCorr[1][0]-15, tmpCorr[1][1]-15)
							cv2.line(img_contours1,tup1,tup2,(100,255,0),1)
						
						vis = np.concatenate((img_contours1, img_contours2), axis=1)
						
						# cv2.imshow('Contours', img_contours1)
						# cv2.imshow('Contours22', img_contours2)
						# cv2.waitKey(0)
						# cv2.destroyAllWindows()
						
						cv2.imshow('Contours3', vis)
						cv2.waitKey(0)
						cv2.destroyAllWindows()
			
	return


def segmentedDat(contour, stepCoords, transformedCentreImagePoint, params, mainPieceDataInd, edgeKey, segdatdebugmode=False):
	ICP_DEBUG=False
	# if mainPieceDataInd==3 and edgeKey=='topEdge':
		# ICP_DEBUG=True
	
	terribleCodeDistCache = {}
	
	
	edgeArcLength=0
	for i in range(contour.shape[0]-1):
		tmpDist = None
		if i in terribleCodeDistCache:
			tmpDist=terribleCodeDistCache[i]
		else:
			tmpDist = getDistance(contour[i][0][0], contour[i+1][0][0], contour[i][0][1], contour[i+1][0][1])
			terribleCodeDistCache[i]=tmpDist
		edgeArcLength+=tmpDist
	
	
	minArcLengthRatioForConfidentLineSegOrientation = params['minArcLengthRatioForConfidentLineSegOrientation'] # e.g. if 1%, then if a lineSeg is >= 1% just take its word for it that there isnt enough noise for its orientation to be flipped to being on wrong side of line from centre img pt
	minArcLengthForConfidence = edgeArcLength*minArcLengthRatioForConfidentLineSegOrientation
	
	arcLengthRatioTangentRadius = params['arcLengthRatioTangentRadius']
	
	checkArcLengthRatioInwardsFromPlaneSegmentEndingsForParallelness = params['checkArcLengthRatioInwardsFromPlaneSegmentEndingsForParallelness']
	checkArcLengthInwards = edgeArcLength*checkArcLengthRatioInwardsFromPlaneSegmentEndingsForParallelness
	
	maxClosenessToParallelWithCentreImgLine = params['maxClosenessToParallelWithCentreImgLine']
	
	processedPlaneSegsStillContainsArcLengthRatio = params['processedPlaneSegsStillContainsArcLengthRatio']
	
	allPlanesSegs = []
	
	prevSegSign = (contour[1][0][1] - transformedCentreImagePoint[1])*(contour[0][0][0] - transformedCentreImagePoint[0]) - (contour[1][0][0] - transformedCentreImagePoint[0])*(contour[0][0][1] - transformedCentreImagePoint[1])
	
	if prevSegSign >=0:
		allPlanesSegs.append([1, [0,1]]) # [1] is inds
	else:
		allPlanesSegs.append([-1, [0,1]])
	for i in range(1, contour.shape[0]-1):
		currSegSign = (contour[i+1][0][1] - transformedCentreImagePoint[1])*(contour[i][0][0] - transformedCentreImagePoint[0]) - (contour[i+1][0][0] - transformedCentreImagePoint[0])*(contour[i][0][1] - transformedCentreImagePoint[1])
		if currSegSign>=0 and allPlanesSegs[-1][0]==1 or currSegSign<=0 and allPlanesSegs[-1][0]==-1: # <= and >= cause if ==0 i always want to add to current plane segment
			allPlanesSegs[-1][1].append(i+1)
		else:
			tmpDist = None
			if i in terribleCodeDistCache:
				tmpDist=terribleCodeDistCache[i]
			else:
				tmpDist = getDistance(contour[i][0][0], contour[i+1][0][0], contour[i][0][1], contour[i+1][0][1])
				terribleCodeDistCache[i]=tmpDist
			
			if tmpDist>=minArcLengthForConfidence:
				if currSegSign>0:
					allPlanesSegs.append([1, [i,i+1]])
				elif currSegSign<0:
					allPlanesSegs.append([-1, [i,i+1]])
				else:
					print("isnt this case handled earlier...???")
					exit()
			else:
				currDist = tmpDist
				k=i+1
				reqCoord = None
				while k<contour.shape[0]-1:
					veryTmpDist = None
					if k in terribleCodeDistCache:
						veryTmpDist=terribleCodeDistCache[k]
					else:
						veryTmpDist = getDistance(contour[k][0][0], contour[k+1][0][0], contour[k][0][1], contour[k+1][0][1])
						terribleCodeDistCache[k]=veryTmpDist
					
					if currDist+veryTmpDist>=minArcLengthForConfidence:
						reqDist = minArcLengthForConfidence-currDist
						reqRatioOnLine = reqDist/veryTmpDist
						reqCoordX = contour[k][0][0] + (contour[k+1][0][0]-contour[k][0][0])*reqRatioOnLine
						reqCoordY = contour[k][0][1] + (contour[k+1][0][1]-contour[k][0][1])*reqRatioOnLine
						reqCoord = [reqCoordX, reqCoordY]
						break
					
					currDist+=veryTmpDist
					k+=1
				if reqCoord is not None:
					
					currSegSign2 = (reqCoord[1] - transformedCentreImagePoint[1])*(contour[i][0][0] - transformedCentreImagePoint[0]) - (reqCoord[0] - transformedCentreImagePoint[0])*(contour[i][0][1] - transformedCentreImagePoint[1])
					if currSegSign2>=0 and allPlanesSegs[-1][0]==1 or currSegSign2<=0 and allPlanesSegs[-1][0]==-1: # <= and >= cause if ==0 i always want to add to current plane segment
						allPlanesSegs[-1][1].append(i+1)
					else:
						if currSegSign2>0:
							allPlanesSegs.append([1, [i,i+1]])
						elif currSegSign2<0:
							allPlanesSegs.append([-1, [i,i+1]])
				else:
					# not enough pts left i think, like prob in last 1% of the edge
					if i < contour.shape[0]*0.9:
						print("hmmmmmmmmmmmmmmmm, pretty weird that this is happening.......")
						pass
					break
	
	for planeSeg in allPlanesSegs:
		highestTooParallelIndCanBeIndRatio = None # can be ind ratio so always floor and stuff when using
		startIndRatio = None
		startCoord = None
		planeSegIndListInd=None
		
		currDist = 0
		for i in range(len(planeSeg[1])-1):
			tmpDist = None
			if planeSeg[1][i] in terribleCodeDistCache:
				tmpDist=terribleCodeDistCache[planeSeg[1][i]]
			else:
				tmpDist = getDistance(contour[planeSeg[1][i]][0][0], contour[planeSeg[1][i]+1][0][0], contour[planeSeg[1][i]][0][1], contour[planeSeg[1][i]+1][0][1])
				terribleCodeDistCache[planeSeg[1][i]]=tmpDist
			
			if currDist+tmpDist>=checkArcLengthInwards:
				reqDist = checkArcLengthInwards-currDist
				reqRatioOnLine = reqDist/tmpDist
				reqCoordX = contour[planeSeg[1][i]][0][0] + (contour[planeSeg[1][i]+1][0][0]-contour[planeSeg[1][i]][0][0])*reqRatioOnLine
				reqCoordY = contour[planeSeg[1][i]][0][1] + (contour[planeSeg[1][i]+1][0][1]-contour[planeSeg[1][i]][0][1])*reqRatioOnLine
				startCoord = [reqCoordX, reqCoordY]
				startIndRatio=planeSeg[1][i]+reqRatioOnLine
				planeSegIndListInd=i
				break
			currDist+=tmpDist
		
		if startIndRatio is None:
			startIndRatio=planeSeg[1][-2]
			planeSegIndListInd=len(planeSeg[1])-2
		if startIndRatio-math.floor(startIndRatio)>0:
			lineSegCoord1 = contour[math.floor(startIndRatio)][0]
			lineSegCoord2 = contour[math.floor(startIndRatio)+1][0]
			lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
			centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
			orientDiff = lineSegOrientation-centreImgLineOrientation
			if orientDiff<math.pi:
				orientDiff+=2*math.pi
			if orientDiff>math.pi:
				orientDiff-=2*math.pi
			
			if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
				orientDiff+=180*math.pi/180
			if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
				orientDiff-=180*math.pi/180
			orientDiff=abs(orientDiff)
			if orientDiff<=maxClosenessToParallelWithCentreImgLine:
				highestTooParallelIndCanBeIndRatio=startIndRatio
			else:
				tmpStartInd=planeSegIndListInd # just starting from lineSeg coord1 rather than the coord on line
				
				currDist = 0
				k=tmpStartInd
				reqCoord = None
				while k<len(planeSeg[1])-1:
					m1 = planeSeg[1][k]
					m2 = m1+1
					veryTmpDist = None
					if m1 in terribleCodeDistCache:
						veryTmpDist=terribleCodeDistCache[m1]
					else:
						veryTmpDist = getDistance(contour[m1][0][0], contour[m2][0][0], contour[m1][0][1], contour[m2][0][1])
						terribleCodeDistCache[m1]=veryTmpDist
					
					if currDist+veryTmpDist>=minArcLengthForConfidence:
						reqDist = minArcLengthForConfidence-currDist
						reqRatioOnLine = reqDist/veryTmpDist
						reqCoordX = contour[m1][0][0] + (contour[m2][0][0]-contour[m1][0][0])*reqRatioOnLine
						reqCoordY = contour[m1][0][1] + (contour[m2][0][1]-contour[m1][0][1])*reqRatioOnLine
						reqCoord = [reqCoordX, reqCoordY]
						break
					
					currDist+=veryTmpDist
					k+=1
				
				if reqCoord is None:
					reqCoord=contour[planeSeg[1][-1]][0]
				
				# now do same parallelness test but with lineSeg from startCoord to a coord ~1% arcLength ahead rather than just the end of the lineSeg starting at math.floor(startIndRatio)
				lineSegCoord1 = contour[math.floor(startIndRatio)][0]
				lineSegCoord2 = reqCoord
				lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
				centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
				orientDiff = lineSegOrientation-centreImgLineOrientation
				if orientDiff<math.pi:
					orientDiff+=2*math.pi
				if orientDiff>math.pi:
					orientDiff-=2*math.pi
				
				
				if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
					orientDiff+=180*math.pi/180
				if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
					orientDiff-=180*math.pi/180
				orientDiff=abs(orientDiff)
				if orientDiff<=maxClosenessToParallelWithCentreImgLine:
					highestTooParallelIndCanBeIndRatio=startIndRatio
				
			
			if highestTooParallelIndCanBeIndRatio is None:
				
				# same as above but for all segs iterating backwards from the starting ind, stopping as soon as a lineSeg that is too parallel is encountered
				# then if one was encountered either here or above (highestTooParallelIndCanBeIndRatio not None), slice and delete from planeSeg ending to there
				# then do all again but from other ending, with iteration and stuff reversed, might be easier to temp flip contour and just keep same code but check
				
				for i in range(planeSegIndListInd-1, -1, -1):
					
					tmpCntInd=planeSeg[1][i]
					
					lineSegCoord1 = contour[tmpCntInd][0]
					lineSegCoord2 = contour[tmpCntInd+1][0]
					lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
					centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
					orientDiff = lineSegOrientation-centreImgLineOrientation
					if orientDiff<math.pi:
						orientDiff+=2*math.pi
					if orientDiff>math.pi:
						orientDiff-=2*math.pi
					
					
					if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
						orientDiff+=180*math.pi/180
					if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
						orientDiff-=180*math.pi/180
					orientDiff=abs(orientDiff)
					if orientDiff<=maxClosenessToParallelWithCentreImgLine:
						highestTooParallelIndCanBeIndRatio=tmpCntInd
						break
					else:
						tmpStartInd=i # just starting from lineSeg coord1 rather than the coord on line
						
						currDist = 0
						k=tmpStartInd
						reqCoord = None
						while k<len(planeSeg[1])-1:
							m1 = planeSeg[1][k]
							m2 = m1+1
							veryTmpDist = None
							if m1 in terribleCodeDistCache:
								veryTmpDist=terribleCodeDistCache[m1]
							else:
								veryTmpDist = getDistance(contour[m1][0][0], contour[m2][0][0], contour[m1][0][1], contour[m2][0][1])
								terribleCodeDistCache[m1]=veryTmpDist
							
							if currDist+veryTmpDist>=minArcLengthForConfidence:
								reqDist = minArcLengthForConfidence-currDist
								reqRatioOnLine = reqDist/veryTmpDist
								reqCoordX = contour[m1][0][0] + (contour[m2][0][0]-contour[m1][0][0])*reqRatioOnLine
								reqCoordY = contour[m1][0][1] + (contour[m2][0][1]-contour[m1][0][1])*reqRatioOnLine
								reqCoord = [reqCoordX, reqCoordY]
								break
							
							currDist+=veryTmpDist
							k+=1
						
						if reqCoord is None:
							reqCoord=contour[planeSeg[1][-1]][0]
						
						# now do same parallelness test but with lineSeg from startCoord to a coord ~1% arcLength ahead rather than just the end of the lineSeg starting at math.floor(startIndRatio)
						lineSegCoord1 = contour[tmpCntInd][0]
						lineSegCoord2 = reqCoord
						lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
						centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
						orientDiff = lineSegOrientation-centreImgLineOrientation
						if orientDiff<math.pi:
							orientDiff+=2*math.pi
						if orientDiff>math.pi:
							orientDiff-=2*math.pi
						
						
						if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
							orientDiff+=180*math.pi/180
						if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
							orientDiff-=180*math.pi/180
						orientDiff=abs(orientDiff)
						if orientDiff<=maxClosenessToParallelWithCentreImgLine:
							highestTooParallelIndCanBeIndRatio=tmpCntInd
							break
					
		
		lowestTooParallelIndCanBeIndRatio = None # can be ind ratio so always floor and stuff when using
		startIndRatio = None
		startCoord = None
		planeSegIndListInd=None
		
		currDist = 0
		for i in range(len(planeSeg[1])-1, 0, -1):
			tmpDist = None
			if planeSeg[1][i-1] in terribleCodeDistCache:
				tmpDist=terribleCodeDistCache[planeSeg[1][i-1]]
			else:
				tmpDist = getDistance(contour[planeSeg[1][i-1]][0][0], contour[planeSeg[1][i-1]+1][0][0], contour[planeSeg[1][i-1]][0][1], contour[planeSeg[1][i-1]+1][0][1])
				terribleCodeDistCache[planeSeg[1][i-1]]=tmpDist
			
			if currDist+tmpDist>=checkArcLengthInwards:
				reqDist = checkArcLengthInwards-currDist
				reqRatioOnLine = reqDist/tmpDist
				reqCoordX = contour[planeSeg[1][i-1]+1][0][0] + (contour[planeSeg[1][i-1]][0][0]-contour[planeSeg[1][i-1]+1][0][0])*reqRatioOnLine
				reqCoordY = contour[planeSeg[1][i-1]+1][0][1] + (contour[planeSeg[1][i-1]][0][1]-contour[planeSeg[1][i-1]+1][0][1])*reqRatioOnLine
				startCoord = [reqCoordX, reqCoordY]
				startIndRatio=planeSeg[1][i-1]+1-reqRatioOnLine
				planeSegIndListInd=i-1
				break
			currDist+=tmpDist
		
		if startIndRatio is None:
			startIndRatio=planeSeg[1][0]
			startCoord = contour[planeSeg[1][0]][0]
			planeSegIndListInd=0
		if startIndRatio-math.floor(startIndRatio)>0:
			lineSegCoord1 = startCoord
			lineSegCoord2 = contour[math.ceil(startIndRatio)][0]
			lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
			centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
			orientDiff = lineSegOrientation-centreImgLineOrientation
			if orientDiff<math.pi:
				orientDiff+=2*math.pi
			if orientDiff>math.pi:
				orientDiff-=2*math.pi
			
			if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
				orientDiff+=180*math.pi/180
			if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
				orientDiff-=180*math.pi/180
			orientDiff=abs(orientDiff)
			if orientDiff<=maxClosenessToParallelWithCentreImgLine:
				lowestTooParallelIndCanBeIndRatio=startIndRatio
			else:
				currDist = getDistance(startCoord[0], contour[planeSeg[1][planeSegIndListInd]+1][0][0], startCoord[1], contour[planeSeg[1][planeSegIndListInd]+1][0][1])
				if currDist<minArcLengthForConfidence:
					k=planeSegIndListInd+1
					reqCoord = None
					while k<len(planeSeg[1])-1:
						m1 = planeSeg[1][k]
						m2 = m1+1
						veryTmpDist = None
						if m1 in terribleCodeDistCache:
							veryTmpDist=terribleCodeDistCache[m1]
						else:
							veryTmpDist = getDistance(contour[m1][0][0], contour[m2][0][0], contour[m1][0][1], contour[m2][0][1])
							terribleCodeDistCache[m1]=veryTmpDist
						
						if currDist+veryTmpDist>=minArcLengthForConfidence:
							reqDist = minArcLengthForConfidence-currDist
							reqRatioOnLine = reqDist/veryTmpDist
							reqCoordX = contour[m1][0][0] + (contour[m2][0][0]-contour[m1][0][0])*reqRatioOnLine
							reqCoordY = contour[m1][0][1] + (contour[m2][0][1]-contour[m1][0][1])*reqRatioOnLine
							reqCoord = [reqCoordX, reqCoordY]
							break
						
						currDist+=veryTmpDist
						k+=1
					
					if reqCoord is None:
						reqCoord=contour[planeSeg[1][-1]][0]
					
					lineSegCoord1 = startCoord
					lineSegCoord2 = reqCoord
					lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
					centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
					orientDiff = lineSegOrientation-centreImgLineOrientation
					if orientDiff<math.pi:
						orientDiff+=2*math.pi
					if orientDiff>math.pi:
						orientDiff-=2*math.pi
					
					if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
						orientDiff+=180*math.pi/180
					if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
						orientDiff-=180*math.pi/180
					orientDiff=abs(orientDiff)
					if orientDiff<=maxClosenessToParallelWithCentreImgLine:
						lowestTooParallelIndCanBeIndRatio=startIndRatio
				
			
			if lowestTooParallelIndCanBeIndRatio is None:
				
				# same as above but for all segs iterating backwards from the starting ind, stopping as soon as a lineSeg that is too parallel is encountered
				# then if one was encountered either here or above (highestTooParallelIndCanBeIndRatio not None), slice and delete from planeSeg ending to there
				# then do all again but from other ending, with iteration and stuff reversed, might be easier to temp flip contour and just keep same code but check
				
				for i in range(planeSegIndListInd+1, len(planeSeg[1])-1):
					
					tmpCntInd=planeSeg[1][i]
					
					lineSegCoord1 = contour[tmpCntInd][0]
					lineSegCoord2 = contour[tmpCntInd+1][0]
					lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
					centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
					orientDiff = lineSegOrientation-centreImgLineOrientation
					if orientDiff<math.pi:
						orientDiff+=2*math.pi
					if orientDiff>math.pi:
						orientDiff-=2*math.pi
					
					if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
						orientDiff+=180*math.pi/180
					if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
						orientDiff-=180*math.pi/180
					orientDiff=abs(orientDiff)
					if orientDiff<=maxClosenessToParallelWithCentreImgLine:
						lowestTooParallelIndCanBeIndRatio=tmpCntInd
						break
					else:
						tmpStartInd=i
						
						currDist = 0
						k=tmpStartInd
						reqCoord = None
						while k<len(planeSeg[1])-1:
							m1 = planeSeg[1][k]
							m2 = m1+1
							veryTmpDist = None
							if m1 in terribleCodeDistCache:
								veryTmpDist=terribleCodeDistCache[m1]
							else:
								veryTmpDist = getDistance(contour[m1][0][0], contour[m2][0][0], contour[m1][0][1], contour[m2][0][1])
								terribleCodeDistCache[m1]=veryTmpDist
							
							if currDist+veryTmpDist>=minArcLengthForConfidence:
								reqDist = minArcLengthForConfidence-currDist
								reqRatioOnLine = reqDist/veryTmpDist
								reqCoordX = contour[m1][0][0] + (contour[m2][0][0]-contour[m1][0][0])*reqRatioOnLine
								reqCoordY = contour[m1][0][1] + (contour[m2][0][1]-contour[m1][0][1])*reqRatioOnLine
								reqCoord = [reqCoordX, reqCoordY]
								break
							
							currDist+=veryTmpDist
							k+=1
						
						if reqCoord is None:
							reqCoord=contour[planeSeg[1][-1]][0]
						
						lineSegCoord1 = contour[tmpCntInd][0]
						lineSegCoord2 = reqCoord
						lineSegOrientation = math.atan2(lineSegCoord2[1]-lineSegCoord1[1], lineSegCoord2[0]-lineSegCoord1[0])
						centreImgLineOrientation = math.atan2(lineSegCoord1[1]-transformedCentreImagePoint[1], lineSegCoord1[0]-transformedCentreImagePoint[0])
						orientDiff = lineSegOrientation-centreImgLineOrientation
						if orientDiff<math.pi:
							orientDiff+=2*math.pi
						if orientDiff>math.pi:
							orientDiff-=2*math.pi
						
						
						if orientDiff<=-90*math.pi/180: # -120 deg -> 60 deg
							orientDiff+=180*math.pi/180
						if orientDiff>90*math.pi/180: # 120 deg -> -60 deg
							orientDiff-=180*math.pi/180
						orientDiff=abs(orientDiff)
						if orientDiff<=maxClosenessToParallelWithCentreImgLine:
							lowestTooParallelIndCanBeIndRatio=tmpCntInd
							break
					
		if highestTooParallelIndCanBeIndRatio is not None and lowestTooParallelIndCanBeIndRatio is not None:
			if highestTooParallelIndCanBeIndRatio>=lowestTooParallelIndCanBeIndRatio:
				# delete whole thing
				planeSeg.append([])
			else:
				planeSeg.append([highestTooParallelIndCanBeIndRatio, lowestTooParallelIndCanBeIndRatio])
		elif highestTooParallelIndCanBeIndRatio is not None:
			planeSeg.append([highestTooParallelIndCanBeIndRatio, planeSeg[1][-1]])
		elif lowestTooParallelIndCanBeIndRatio is not None:
			planeSeg.append([planeSeg[1][0], lowestTooParallelIndCanBeIndRatio])
		else:
			planeSeg.append([planeSeg[1][0], planeSeg[1][-1]])
		
	finalPlanesSegments = [[], []]
	stepCoordIndsBeforePlanesSegmentsCoordsEdge = [[], []]
	contourIndRatiosForPlaneSegments = [[], []]
	seedCoordPlane = None
	
	totalArcLengthCovered = 0
	distBetweenPtsGoal = params['arcLengthRatioGoalBetweenPtsForPlaneSegDat']*edgeArcLength
	for planeSeg in allPlanesSegs:
		if len(planeSeg[2])==2:
			startContourIndRatio = planeSeg[2][0]
			endContourIndRatio = planeSeg[2][1]
			
			# get total planeSeg dist between start and end
			
			planeSegArcLength = 0
			if math.floor(startContourIndRatio)==math.floor(endContourIndRatio):
				tmpFloorInd = math.floor(startContourIndRatio)
				coord1Ratio = startContourIndRatio - tmpFloorInd
				coord2Ratio = endContourIndRatio - tmpFloorInd
				
				reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord1Ratio
				reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord1Ratio
				coord1 = (reqCoordX, reqCoordY)
				
				reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord2Ratio
				reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord2Ratio
				coord2 = (reqCoordX, reqCoordY)
				
				planeSegArcLength = getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
			else:
				if startContourIndRatio-math.floor(startContourIndRatio)>0:
					tmpFloorInd=math.floor(startContourIndRatio)
					coord1Ratio = startContourIndRatio - tmpFloorInd
					
					reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord1Ratio
					reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord1Ratio
					coord1 = (reqCoordX, reqCoordY)
					coord2 = contour[tmpFloorInd+1][0]
					planeSegArcLength += getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
				
				if endContourIndRatio-math.floor(endContourIndRatio)>0:
					tmpFloorInd=math.floor(endContourIndRatio)
					coord2Ratio = endContourIndRatio - tmpFloorInd
					
					reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord2Ratio
					reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord2Ratio
					coord2 = (reqCoordX, reqCoordY)
					coord1 = contour[tmpFloorInd][0]
					planeSegArcLength += getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
				
				for i in range(math.ceil(startContourIndRatio), math.floor(endContourIndRatio)):
					veryTmpDist = None
					if i in terribleCodeDistCache:
						veryTmpDist=terribleCodeDistCache[i]
					else:
						veryTmpDist = getDistance(contour[i][0][0], contour[i+1][0][0], contour[i][0][1], contour[i+1][0][1])
						terribleCodeDistCache[i]=veryTmpDist
					planeSegArcLength+=veryTmpDist
				
				
			
			if planeSegArcLength >= distBetweenPtsGoal:
				floatSpreadAmtUsingExactGoal = planeSegArcLength/distBetweenPtsGoal
				spreadOption1Amt = math.floor(floatSpreadAmtUsingExactGoal)
				spreadOption2Amt = math.ceil(floatSpreadAmtUsingExactGoal)
				spreadOption1Dist = planeSegArcLength/spreadOption1Amt
				spreadOption2Dist = planeSegArcLength/spreadOption2Amt
				# just pick whichever has length closest to goal
				distBetweenPtsForThisPlaneSeg = None
				goalPtsAmt = None # amt of pts is actually goalPtsAmt+1
				if abs(spreadOption1Dist-distBetweenPtsGoal)<abs(spreadOption2Dist-distBetweenPtsGoal):
					distBetweenPtsForThisPlaneSeg=spreadOption1Dist
					goalPtsAmt = spreadOption1Amt
				else:
					distBetweenPtsForThisPlaneSeg=spreadOption2Dist
					goalPtsAmt = spreadOption2Amt
				
				finalPlaneSeg = []
				finalStepCoordIndBeforeDat = []
				coveredDist = 0
				if math.floor(startContourIndRatio)==math.floor(endContourIndRatio):
					tmpFloorInd = math.floor(startContourIndRatio)
					coord1Ratio = startContourIndRatio - tmpFloorInd
					
					reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord1Ratio
					reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord1Ratio
					coord1 = [reqCoordX, reqCoordY]
					finalPlaneSeg.append(coord1)
					didSomethingDebug=False
					for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
						if tmpFloorInd+coord1Ratio<stepCoordDat[1]+stepCoordDat[3]:
							finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
							didSomethingDebug=True
							break
					
					veryTmpDist = None
					if tmpFloorInd in terribleCodeDistCache:
						veryTmpDist=terribleCodeDistCache[tmpFloorInd]
					else:
						veryTmpDist = getDistance(contour[tmpFloorInd][0][0], contour[tmpFloorInd+1][0][0], contour[tmpFloorInd][0][1], contour[tmpFloorInd+1][0][1])
						terribleCodeDistCache[tmpFloorInd]=veryTmpDist
					
					tmpFloorInd = math.floor(endContourIndRatio)
					coord2Ratio = endContourIndRatio - tmpFloorInd
					
					reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord2Ratio
					reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord2Ratio
					coord2 = [reqCoordX, reqCoordY]
					
					ratioBetweenPtsForThisSeg = distBetweenPtsForThisPlaneSeg/veryTmpDist
					for j in range(1, goalPtsAmt+1):
						tmpRatio = coord1Ratio+j*ratioBetweenPtsForThisSeg
						tmpReqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*tmpRatio
						tmpReqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*tmpRatio
						tmpCoord = [tmpReqCoordX, tmpReqCoordY]
						finalPlaneSeg.append(tmpCoord)
						didSomethingDebug=False
						for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
							if tmpFloorInd+tmpRatio<stepCoordDat[1]+stepCoordDat[3]:
								didSomethingDebug=True
								finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
								break
						
					coveredDist+=getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
				else:
					
					if startContourIndRatio-math.floor(startContourIndRatio)>0:
						tmpFloorInd=math.floor(startContourIndRatio)
						coord1Ratio = startContourIndRatio - tmpFloorInd
						
						reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord1Ratio
						reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord1Ratio
						coord1 = [reqCoordX, reqCoordY]
						
						finalPlaneSeg.append(coord1)
						didSomethingDebug=False
						for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
							if tmpFloorInd+coord1Ratio<stepCoordDat[1]+stepCoordDat[3]:
								didSomethingDebug=True
								finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
								break
						
						coord2 = contour[tmpFloorInd+1][0]
						tmpSegArcLength = getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
						ptsRemainingHere = math.floor(tmpSegArcLength/distBetweenPtsForThisPlaneSeg)
						
						veryTmpDist = None
						if tmpFloorInd in terribleCodeDistCache:
							veryTmpDist=terribleCodeDistCache[tmpFloorInd]
						else:
							veryTmpDist = getDistance(contour[tmpFloorInd][0][0], contour[tmpFloorInd+1][0][0], contour[tmpFloorInd][0][1], contour[tmpFloorInd+1][0][1])
							terribleCodeDistCache[tmpFloorInd]=veryTmpDist
						
						ratioBetweenPtsForThisSeg = distBetweenPtsForThisPlaneSeg/veryTmpDist
						for j in range(1, ptsRemainingHere+1):
							tmpRatio = coord1Ratio+j*ratioBetweenPtsForThisSeg
							tmpReqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*tmpRatio
							tmpReqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*tmpRatio
							tmpCoord = [tmpReqCoordX, tmpReqCoordY]
							finalPlaneSeg.append(tmpCoord)
							didSomethingDebug=False
							for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
								if tmpFloorInd+tmpRatio<stepCoordDat[1]+stepCoordDat[3]:
									didSomethingDebug=True
									finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
									break
							
						coveredDist+=tmpSegArcLength
					
					for i in range(math.ceil(startContourIndRatio), math.floor(endContourIndRatio)):
						veryTmpDist = None
						if i in terribleCodeDistCache:
							veryTmpDist=terribleCodeDistCache[i]
						else:
							veryTmpDist = getDistance(contour[i][0][0], contour[i+1][0][0], contour[i][0][1], contour[i+1][0][1])
							terribleCodeDistCache[i]=veryTmpDist
						if coveredDist+veryTmpDist>=(len(finalPlaneSeg))*distBetweenPtsForThisPlaneSeg:
							
							amtOnLine = (coveredDist+veryTmpDist)/distBetweenPtsForThisPlaneSeg - (len(finalPlaneSeg)-1) # same as above but simplified
							amtOnLine = math.floor(amtOnLine)
							if amtOnLine>=1:
								if veryTmpDist==0:
									print(contour[i])
									print(contour[i+1])
									print(i)
								
								ratioBetweenPtsForThisSeg = distBetweenPtsForThisPlaneSeg/veryTmpDist
								distToFirstPtOnLine = ((len(finalPlaneSeg)-1)+1)*distBetweenPtsForThisPlaneSeg - coveredDist # ((len(finalPlaneSeg)-1)+1) is total arcLength from start to the next point to be added
								ratioOfFirstPt = distToFirstPtOnLine/veryTmpDist
								
								for j in range(amtOnLine):
									tmpRatio = ratioOfFirstPt+j*ratioBetweenPtsForThisSeg
									tmpReqCoordX = contour[i][0][0] + (contour[i+1][0][0]-contour[i][0][0])*tmpRatio
									tmpReqCoordY = contour[i][0][1] + (contour[i+1][0][1]-contour[i][0][1])*tmpRatio
									tmpCoord = [tmpReqCoordX, tmpReqCoordY]
									finalPlaneSeg.append(tmpCoord)
									didSomethingDebug=False
									for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
										if i+tmpRatio<stepCoordDat[1]+stepCoordDat[3]:
											didSomethingDebug=True
											finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
											break
									
							else:
								pass
						
						coveredDist+=veryTmpDist
						
					
					if endContourIndRatio-math.floor(endContourIndRatio)>0:
						
						tmpFloorInd=math.floor(endContourIndRatio)
						coord2Ratio = endContourIndRatio - tmpFloorInd
						
						reqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*coord2Ratio
						reqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*coord2Ratio
						coord2 = (reqCoordX, reqCoordY)
						coord1 = contour[tmpFloorInd][0]
						
						tmpSegArcLength = getDistance(coord1[0], coord2[0], coord1[1], coord2[1])
						
						
						if coveredDist+tmpSegArcLength>=(len(finalPlaneSeg))*distBetweenPtsForThisPlaneSeg: # >= total acrLength dist needed to cover up to the next point # len(finalPlaneSeg)-1 is amount of pts done so far i.e. at end this should == goalPtsAmt
							amtOnLine = (coveredDist+tmpSegArcLength)/distBetweenPtsForThisPlaneSeg - (len(finalPlaneSeg)-1) # same as above but simplified
							amtOnLine = math.floor(amtOnLine)
							if amtOnLine>=1:
								veryTmpDist = None
								if tmpFloorInd in terribleCodeDistCache:
									veryTmpDist=terribleCodeDistCache[tmpFloorInd]
								else:
									veryTmpDist = getDistance(contour[tmpFloorInd][0][0], contour[tmpFloorInd+1][0][0], contour[tmpFloorInd][0][1], contour[tmpFloorInd+1][0][1])
									terribleCodeDistCache[tmpFloorInd]=veryTmpDist
								ratioBetweenPtsForThisSeg = distBetweenPtsForThisPlaneSeg/veryTmpDist
								distToFirstPtOnLine = ((len(finalPlaneSeg)-1)+1)*distBetweenPtsForThisPlaneSeg - coveredDist # ((len(finalPlaneSeg)-1)+1) is total arcLength from start to the next point to be added
								ratioOfFirstPt = distToFirstPtOnLine/veryTmpDist
								
								for j in range(amtOnLine):
									tmpRatio = ratioOfFirstPt+j*ratioBetweenPtsForThisSeg
									tmpReqCoordX = contour[tmpFloorInd][0][0] + (contour[tmpFloorInd+1][0][0]-contour[tmpFloorInd][0][0])*tmpRatio
									tmpReqCoordY = contour[tmpFloorInd][0][1] + (contour[tmpFloorInd+1][0][1]-contour[tmpFloorInd][0][1])*tmpRatio
									tmpCoord = [tmpReqCoordX, tmpReqCoordY]
									finalPlaneSeg.append(tmpCoord)
									didSomethingDebug=False
									for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
										if tmpFloorInd+tmpRatio<stepCoordDat[1]+stepCoordDat[3]:
											didSomethingDebug=True
											finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
											break
									
							else:
								pass
						
						if len(finalPlaneSeg)-1 < goalPtsAmt:
							finalPlaneSeg.append([coord2[0], coord2[1]])
							didSomethingDebug=False
							for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
								if endContourIndRatio<stepCoordDat[1]+stepCoordDat[3]:
									finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
									didSomethingDebug=True
									break
							
						if len(finalPlaneSeg)-1 != goalPtsAmt:
							print(len(finalPlaneSeg))
							print(goalPtsAmt)
							print("wat?i22j2ij2i")
							exit()
						
						coveredDist+=tmpSegArcLength
						
					if endContourIndRatio-math.floor(endContourIndRatio)==0:
						if len(finalPlaneSeg)-1 < goalPtsAmt:
							finalPlaneSeg.append([contour[endContourIndRatio][0][0], contour[endContourIndRatio][0][1]])
							didSomethingDebug=False
							for stepCoordDatI, stepCoordDat in enumerate(stepCoords):
								if endContourIndRatio<stepCoordDat[1]+stepCoordDat[3]:
									finalStepCoordIndBeforeDat.append(stepCoordDatI-1)
									didSomethingDebug=True
									break
							
				if len(finalPlaneSeg)-1==len(finalStepCoordIndBeforeDat):
					finalStepCoordIndBeforeDat.append(len(stepCoords)-2)
				
				if len(finalPlaneSeg)-1 < goalPtsAmt:
					print("prob not the end of the world but still very weird")
					exit()
				if len(finalPlaneSeg) != len(finalStepCoordIndBeforeDat):
					print(len(finalPlaneSeg))
					print(len(finalStepCoordIndBeforeDat))
					print("wat?wdwwddwdw??")
					exit()
				if abs(coveredDist-planeSegArcLength)>0.0001:
					print(coveredDist)
					print(planeSegArcLength)
					print("wat?d3j3poj3dd3")
					exit()
				
				totalArcLengthCovered+=coveredDist
				
				if planeSeg[0]==-1:
					finalPlanesSegments[0].append(finalPlaneSeg)
					stepCoordIndsBeforePlanesSegmentsCoordsEdge[0].append(finalStepCoordIndBeforeDat)
				else:
					finalPlanesSegments[1].append(finalPlaneSeg)
					stepCoordIndsBeforePlanesSegmentsCoordsEdge[1].append(finalStepCoordIndBeforeDat)
				
				if planeSeg[0]==-1:
					contourIndRatiosForPlaneSegments[0].append((planeSeg[2][0], planeSeg[2][1]))
				else:
					contourIndRatiosForPlaneSegments[1].append((planeSeg[2][0], planeSeg[2][1]))
	
	if totalArcLengthCovered/edgeArcLength>=processedPlaneSegsStillContainsArcLengthRatio:
		segmentedDat = [finalPlanesSegments, None, None, {}, stepCoordIndsBeforePlanesSegmentsCoordsEdge, contourIndRatiosForPlaneSegments]
		return segmentedDat
	
	
	print("edge segmentedDat contains less than like 85% of the original edge contour, removing it from the pool of edges")
	return None # planesSegments, stepCoordIndsBeforePlanesSegmentsCoordsEdge


def icpSimilarityGeneralCase(mainEdgeSegmentedDat, otherEdgeSegmentedDat, rememberParams, mainEdgeTransformedCentreImagePointBase, otherEdgeTransformedCentreImagePointBase, mainSeedCoord, otherSeedCoord, mainEdgeSeedPlane, otherEdgeSeedPlane, mainSeedCoordIndRatio, otherSeedCoordIndRatio, stepCoordsMain, stepCoordsOther, params, potentialPieceDataIndOutie, pieceEdgeKeyOutie, potentialPieceDataIndInnie, pieceEdgeKeyInnie, potentialPieceData, debugDat, debugmode, mainEdgeTransformedReferenceContourDat, otherEdgeTransformedReferenceContourDat, disjointPlanePairs=False, lastResort=False): # SHOULD WORK IN MAJORITY OF CASES
	ULTRA_DEBUG=False
	if False:
	# if potentialPieceData[3]["potentialPieceData"][0]['topEdge'][4][0][1][0][0][0] != 589.6742340189469 or potentialPieceData[3]["potentialPieceData"][0]['topEdge'][4][0][1][0][0][1] != 1232.368439020227:
		ULTRA_DEBUG=True
	
	
	global time3
	global time4
	global time5
	
	consecutiveSampledTangentPointsForConfidentPerpendicularity = 3 # for the sampled edge, i.e. otherEdge, 3 points in a row should be perpendicular enough, because if just 1 then could be a quick corner/turn and not be useful
	hardMinimumPerpendicularity = 30*math.pi/180 # 30 degrees or more in order to be perpendicular enough to consider ray shooting and then scaling the edges to eachother.
	
	arcLengthError = 0.1 # if 2 edges match, we allow up to 10% arclength difference, this means (since arclengthStep makes stepCoords scale invariant) that if 2 points on edge1 are 20 stepCoords from eachother, we'd expect them to be within roughly 18-22 stepCoords of eachother in edge2
	flatStepCoordsError = 3 # im paranoid so adding +/- 3 stepCoords error
	
	mainEdgeTransformedCentreImagePoint = copy.deepcopy(mainEdgeTransformedCentreImagePointBase) # should already have this, translated/rotated/scaled according to whatever i did to this edge in the past (think i rotate every edge to be flat and maybe translate to origin but prob not actually)
	otherEdgeTransformedCentreImagePoint = copy.deepcopy(otherEdgeTransformedCentreImagePointBase)
	
	baseImageReferenceContourDat = params['baseImageReferenceContourDat']
	
	mainEdgePlanesSegments = copy.deepcopy(mainEdgeSegmentedDat[0]) # just wasting time copying cause dont want to transform original data
	otherEdgePlanesSegments = copy.deepcopy(otherEdgeSegmentedDat[0])
	
	baseDistBetweenEndPointsFirstMainPlane=None
	if len(mainEdgePlanesSegments[0])>0:
		baseDistBetweenEndPointsFirstMainPlane = getDistance(mainEdgePlanesSegments[0][0][0][0], mainEdgePlanesSegments[0][-1][-1][0], mainEdgePlanesSegments[0][0][0][1], mainEdgePlanesSegments[0][-1][-1][1])
	baseDistBetweenEndPointsSecondMainPlane = None
	
	baseDistBetweenEndPointsFirstOtherPlane=None
	if len(otherEdgePlanesSegments[0])>0:
		baseDistBetweenEndPointsFirstOtherPlane = getDistance(otherEdgePlanesSegments[0][0][0][0], otherEdgePlanesSegments[0][-1][-1][0], otherEdgePlanesSegments[0][0][0][1], otherEdgePlanesSegments[0][-1][-1][1])
	baseDistBetweenEndPointsSecondOtherPlane = None
	
	if len(mainEdgePlanesSegments)==2 and len(mainEdgePlanesSegments[1])>0:
		baseDistBetweenEndPointsSecondMainPlane = getDistance(mainEdgePlanesSegments[1][0][0][0], mainEdgePlanesSegments[1][-1][-1][0], mainEdgePlanesSegments[1][0][0][1], mainEdgePlanesSegments[1][-1][-1][1])
	if len(otherEdgePlanesSegments)==2 and len(otherEdgePlanesSegments[1])>0:
		baseDistBetweenEndPointsSecondOtherPlane = getDistance(otherEdgePlanesSegments[1][0][0][0], otherEdgePlanesSegments[1][-1][-1][0], otherEdgePlanesSegments[1][0][0][1], otherEdgePlanesSegments[1][-1][-1][1])
	
	stepCoordIndsBeforePlanesSegmentsCoordsMain = mainEdgeSegmentedDat[4]
	stepCoordIndsBeforePlanesSegmentsCoordsOther = otherEdgeSegmentedDat[4]
	
	mainEdgeSeedCoordBase = [mainSeedCoord[0], mainSeedCoord[1]]
	otherEdgeSeedCoordBase = [otherSeedCoord[0], otherSeedCoord[1]]
	translateAmt = [mainEdgeSeedCoordBase[0]-otherEdgeSeedCoordBase[0], mainEdgeSeedCoordBase[1]-otherEdgeSeedCoordBase[1]]
	for planeDat in otherEdgePlanesSegments:
		for segmentDat in planeDat:
			for coordDat in segmentDat:
				coordDat[0]+=translateAmt[0]
				coordDat[1]+=translateAmt[1]
	
	otherEdgeTransformedCentreImagePoint[0]+=translateAmt[0]
	otherEdgeTransformedCentreImagePoint[1]+=translateAmt[1]
	
	mainEdgeSeedCoord = [mainEdgeSeedCoordBase[0], mainEdgeSeedCoordBase[1]]
	otherEdgeSeedCoord = [mainEdgeSeedCoordBase[0], mainEdgeSeedCoordBase[1]]
	stepCoordIndBeforeOtherSeed = None
	stepCoordIndBeforeMainSeed = None
	for stepCoordDatI, stepCoordDat in enumerate(stepCoordsMain):
		if mainSeedCoordIndRatio<stepCoordDat[1]+stepCoordDat[3]:
			stepCoordIndBeforeMainSeed = stepCoordDatI-1
			break
	for stepCoordDatI, stepCoordDat in enumerate(stepCoordsOther):
		if otherSeedCoordIndRatio<stepCoordDat[1]+stepCoordDat[3]:
			stepCoordIndBeforeOtherSeed = stepCoordDatI-1
			break
	
	
	amtPtsFirstMainPlane=0
	amtPtsSecondMainPlane=0
	amtPtsFirstOtherPlane=0
	amtPtsSecondOtherPlane=0
	secondMainPlaneHasPoints = False
	secondOtherPlaneHasPoints = False
	for segDat in mainEdgePlanesSegments[1-mainEdgeSeedPlane]:
		if len(segDat)>=2:
			secondMainPlaneHasPoints=True
		amtPtsSecondMainPlane+=len(segDat)
	for segDat in otherEdgePlanesSegments[1-otherEdgeSeedPlane]:
		if len(segDat)>=2:
			secondOtherPlaneHasPoints=True
		amtPtsSecondOtherPlane+=len(segDat)
	for segDat in mainEdgePlanesSegments[mainEdgeSeedPlane]:
		amtPtsFirstMainPlane+=len(segDat)
	for segDat in otherEdgePlanesSegments[otherEdgeSeedPlane]:
		amtPtsFirstOtherPlane+=len(segDat)
	
	tmpPrintCtr=0
	
	successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane = False
	
	if stepCoordIndBeforeOtherSeed is None or stepCoordIndBeforeMainSeed is None:
		return None
	if rememberParams['sampledEdgeIsSpacedEnoughToUseOnly3PointsForTangentEstimation'] and rememberParams['mainEdgeBarelySampled']: # second one is so the coords we have of main edge dont have vastly different arclength-per-point than the actual contour
		if "baseTangents" not in otherEdgeSegmentedDat[3]:
			tempBaseTangents=[]
			for planeInd, planeDat in enumerate(otherEdgeSegmentedDat[0]): # using this rather than otherEdgePlanesSegments cause this is base data
				tempBaseTangents.append([])
				for segmentDat in planeDat:
					tmpSegmentTangentDat = [None] # first and last item is None cause use 3 consecutive pts per tangent calc, one on each side of the point, so cant do first and last
					for i in range(1, len(segmentDat)-1):
						tmpOrientation=math.atan2(segmentDat[i+1][1]-segmentDat[i-1][1], segmentDat[i+1][0]-segmentDat[i-1][0])
						tmpSegmentTangentDat.append(tmpOrientation)
					tmpSegmentTangentDat.append(None)
					tempBaseTangents[planeInd].append(tmpSegmentTangentDat)
			otherEdgeSegmentedDat[3]["baseTangents"]=tempBaseTangents
		if (otherEdgeSeedCoordBase[0], otherEdgeSeedCoordBase[1]) not in otherEdgeSegmentedDat[3]: # spaghetti code, rerun this function each time setting otherEdgeSegmentedDat[1] and mainEdgeSegmentedDat[1] to new seeds/anchors, also testing using clean coord in case list object stuff is weird
				# remember this is just for one of the 2 planes for this edge since the anchor/seed is only really valid for the plane it's on
			baseTangentDatForSeedPlane = otherEdgeSegmentedDat[3]["baseTangents"][otherEdgeSeedPlane]
			tempRelativeOrientationDat = [] # tangent orientation relative to line from seed orientation
			for i in range(len(baseTangentDatForSeedPlane)):
				tmpSegEntry=[]
				for j in range(len(baseTangentDatForSeedPlane[i])):
					tmpTangentOrientation=baseTangentDatForSeedPlane[i][j]
					if tmpTangentOrientation is not None:
						tmpPoint=otherEdgeSegmentedDat[0][otherEdgeSeedPlane][i][j]
						tmpLineOrientation=math.atan2(tmpPoint[1]-otherEdgeSeedCoordBase[1], tmpPoint[0]-otherEdgeSeedCoordBase[0])
						orientationDifference = tmpTangentOrientation-tmpLineOrientation
						if orientationDifference<math.pi:
							orientationDifference+=2*math.pi
						if orientationDifference>math.pi:
							orientationDifference-=2*math.pi
						tmpSegEntry.append(orientationDifference)
					else:
						tmpSegEntry.append(None)
				tempRelativeOrientationDat.append(tmpSegEntry)
			otherEdgeSegmentedDat[3][(otherEdgeSeedCoordBase[0], otherEdgeSeedCoordBase[1])] = tempRelativeOrientationDat
		
		
		perpendicularityDat = otherEdgeSegmentedDat[3][(otherEdgeSeedCoordBase[0], otherEdgeSeedCoordBase[1])]
		
		perpendicularEnoughTuples=[]
		
		for segI, segmentDat in enumerate(perpendicularityDat):
			if len(segmentDat)-2 >= consecutiveSampledTangentPointsForConfidentPerpendicularity: # without None bits at the beginning and end
				for i in range(1, len(segmentDat)-1-(consecutiveSampledTangentPointsForConfidentPerpendicularity-1)):
					perpendicularEnough=True
					tmpInefficientList = []
					for j in range(consecutiveSampledTangentPointsForConfidentPerpendicularity):
						if segmentDat[i+j]<0:
							tmpDiffFromPerpendicular = -90*math.pi/180 - segmentDat[i+j]
							tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
							if 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
								tmpInefficientList.append(90*math.pi/180-tmpDiffFromPerpendicular) # so convoluted but exhausted, im now storing angle away from straight line with values 0<=X<=90 (in radians)
							else:
								perpendicularEnough=False
								break
						else:
							tmpDiffFromPerpendicular = 90*math.pi/180 - segmentDat[i+j]
							tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
							if 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
								tmpInefficientList.append(90*math.pi/180-tmpDiffFromPerpendicular)
							else:
								perpendicularEnough=False
								break
					if perpendicularEnough:
						tmpPerpendicularAreaPerpendicularity=0
						for tmpAngle in tmpInefficientList:
							tmpPerpendicularAreaPerpendicularity+=tmpAngle
						tmpPerpendicularAreaPerpendicularity=tmpPerpendicularAreaPerpendicularity/consecutiveSampledTangentPointsForConfidentPerpendicularity
						# if mostPerpendicularAreaPerpendicularity is None or tmpPerpendicularAreaPerpendicularity>mostPerpendicularAreaPerpendicularity:
						if True:
							tmpMostPerpendicularAreaDat=[segI, i]
							tmpMostPerpendicularPointInArea=None
							for tmpAngleI in range(len(tmpInefficientList)):
								if tmpMostPerpendicularPointInArea is None or tmpInefficientList[tmpAngleI]>tmpMostPerpendicularPointInArea[1]:
									tmpMostPerpendicularPointInArea=[i+tmpAngleI, tmpInefficientList[tmpAngleI]]
							perpendicularEnoughTuples.append((tmpPerpendicularAreaPerpendicularity, tmpMostPerpendicularAreaDat, tmpMostPerpendicularPointInArea))
		perpendicularEnoughTuples.sort()
		if len(perpendicularEnoughTuples)>0:
			for tmpPerpTuple in perpendicularEnoughTuples:
				
				idkFailure=False
				
				mostPerpendicularAreaDat = tmpPerpTuple[1]
				mostPerpendicularAreaPerpendicularity = tmpPerpTuple[0]
				mostPerpendicularPointInArea = tmpPerpTuple[2]
				
				mostPerpendicularPointInAreaCoordDat = [otherEdgePlanesSegments[otherEdgeSeedPlane][mostPerpendicularAreaDat[0]][mostPerpendicularPointInArea[0]]]
				stepCoordIndBeforeMostPerpendicularPointInArea = stepCoordIndsBeforePlanesSegmentsCoordsOther[otherEdgeSeedPlane][mostPerpendicularAreaDat[0]][mostPerpendicularPointInArea[0]]
				
				estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace = None
				
				if stepCoordIndBeforeOtherSeed<stepCoordIndBeforeMostPerpendicularPointInArea:
					tmpAmountAway=stepCoordIndBeforeMostPerpendicularPointInArea-stepCoordIndBeforeOtherSeed
					tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError)
					tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
					
					tmpInterval = [stepCoordIndBeforeMainSeed+tmpAmountAwayLower, stepCoordIndBeforeMainSeed+tmpAmountAwayUpper]
					
					tmpInterval[0]=max(tmpInterval[0], stepCoordIndBeforeMainSeed+1)
					tmpInterval[1]=min(tmpInterval[1], len(stepCoordsMain)-1)
					if tmpInterval[0]>=tmpInterval[1]:
						idkFailure=True
					estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace=tmpInterval
					
				elif stepCoordIndBeforeOtherSeed>stepCoordIndBeforeMostPerpendicularPointInArea:
					tmpAmountAway=stepCoordIndBeforeOtherSeed-stepCoordIndBeforeMostPerpendicularPointInArea
					tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError) # lower/upper here is gonna be used reversed from intuition cause its lower/upper w.r.t. outwards from seed point
					tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
					
					tmpInterval = [stepCoordIndBeforeMainSeed-tmpAmountAwayUpper, stepCoordIndBeforeMainSeed-tmpAmountAwayLower]
					
					tmpInterval[0]=max(tmpInterval[0], 0)
					tmpInterval[1]=min(tmpInterval[1], stepCoordIndBeforeMainSeed-1)
					if tmpInterval[0]>=tmpInterval[1]:
						idkFailure=True
					estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace=tmpInterval
				else:
					idkFailure=True
				if not(idkFailure):
					
					tmpCoordOther1 = otherEdgePlanesSegments[otherEdgeSeedPlane][mostPerpendicularAreaDat[0]][mostPerpendicularPointInArea[0]-1]
					tmpCoordOther2 = otherEdgePlanesSegments[otherEdgeSeedPlane][mostPerpendicularAreaDat[0]][mostPerpendicularPointInArea[0]+1]
					
					signBeforeMostPerpendicularPointInArea = (tmpCoordOther1[1] - otherEdgeSeedCoord[1])*(mostPerpendicularPointInAreaCoordDat[0][0] - otherEdgeSeedCoord[0]) - (tmpCoordOther1[0] - otherEdgeSeedCoord[0])*(mostPerpendicularPointInAreaCoordDat[0][1] - otherEdgeSeedCoord[1]) # we dont actually just want areas that cross the line, we want them to cross in same direction as in otherEdge, so need the signs from otherEdge
					signAfterMostPerpendicularPointInArea = (tmpCoordOther2[1] - otherEdgeSeedCoord[1])*(mostPerpendicularPointInAreaCoordDat[0][0] - otherEdgeSeedCoord[0]) - (tmpCoordOther2[0] - otherEdgeSeedCoord[0])*(mostPerpendicularPointInAreaCoordDat[0][1] - otherEdgeSeedCoord[1])
					
					if signBeforeMostPerpendicularPointInArea==0 or signAfterMostPerpendicularPointInArea==0 or (signBeforeMostPerpendicularPointInArea<=0 and signAfterMostPerpendicularPointInArea<=0) or (signBeforeMostPerpendicularPointInArea>=0 and signAfterMostPerpendicularPointInArea>=0):
						return
					
					signModifier=1 # so i dont have to just have 2 cases for if it goes from <0 to >0 and from >0 to <0, i can just code 1 case and multiply by signModifier to flip signs if needed, base case when signModifier==1 is when it goes from <0 before to >0 after
					if signBeforeMostPerpendicularPointInArea>0:
						signModifier=-1
					
					crossings = [] # storing all, if more than 1, choose best
					
					for mainSegDatI, mainSegDat in enumerate(mainEdgePlanesSegments[mainEdgeSeedPlane]):
						
						firstCoord = mainSegDat[0]
						prevSign = (firstCoord[1] - mainEdgeSeedCoord[1])*(mostPerpendicularPointInAreaCoordDat[0][0] - mainEdgeSeedCoord[0]) - (firstCoord[0] - mainEdgeSeedCoord[0])*(mostPerpendicularPointInAreaCoordDat[0][1] - mainEdgeSeedCoord[1]) # just using mostPerpendicularPointInAreaCoordDat here since both edges should be in same space so technically i could just use otherEdgeSeedCoord
						for mainSegDatCoordI in range(1, len(mainSegDat)):
							currCoord = mainSegDat[mainSegDatCoordI]
							currSign = (currCoord[1] - mainEdgeSeedCoord[1])*(mostPerpendicularPointInAreaCoordDat[0][0] - mainEdgeSeedCoord[0]) - (currCoord[0] - mainEdgeSeedCoord[0])*(mostPerpendicularPointInAreaCoordDat[0][1] - mainEdgeSeedCoord[1])
							if signModifier*prevSign<0 and signModifier*currSign>0:
								tmpStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][mainSegDatI][mainSegDatCoordI-1] # idk if it matters if mainSegDatCoordI-1 or mainSegDatCoordI
								if tmpStepCoordIndBefore >= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace[0] and tmpStepCoordIndBefore <= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace[1]:
									crossings.append((mainSegDatI, mainSegDatCoordI-1))
							prevSign=currSign
					
					if len(crossings)==0:
						pass
					elif len(crossings)>1:
						print("stepCoordInd INTERVAL ESTIMATE IS TOO BROAD")
						pass
					elif len(crossings)==1:
						if True:
							# ...get actual crossing then use it instead of crossings[0]...
							
							lineSegCoord1 = mainEdgePlanesSegments[mainEdgeSeedPlane][crossings[0][0]][crossings[0][1]]
							lineSegCoord2 = mainEdgePlanesSegments[mainEdgeSeedPlane][crossings[0][0]][crossings[0][1]+1]
							lineCoord1 = mainEdgeSeedCoord
							lineCoord2 = mostPerpendicularPointInAreaCoordDat[0]
							actualCrossing=simpleLineSegLineIntersect(lineSegCoord1, lineSegCoord2, lineCoord1, lineCoord2)
							if actualCrossing is not None:
								distFromSeedToPointInMainEdge = getDistance(mainEdgeSeedCoord[0], actualCrossing[0], mainEdgeSeedCoord[1], actualCrossing[1])
								distFromSeedToPointInOtherEdge = getDistance(otherEdgeSeedCoord[0], mostPerpendicularPointInAreaCoordDat[0][0], otherEdgeSeedCoord[1], mostPerpendicularPointInAreaCoordDat[0][1])
								scaleOtherToMain = distFromSeedToPointInMainEdge/distFromSeedToPointInOtherEdge
								
								for planeDat in otherEdgePlanesSegments:
									for segmentDat in planeDat:
										for coordPt in segmentDat:
											coordPt[0]-=otherEdgeSeedCoord[0]
											coordPt[1]-=otherEdgeSeedCoord[1]
											coordPt[0]=coordPt[0]*scaleOtherToMain
											coordPt[1]=coordPt[1]*scaleOtherToMain
											coordPt[0]+=otherEdgeSeedCoord[0]
											coordPt[1]+=otherEdgeSeedCoord[1]
								
								otherEdgeTransformedCentreImagePoint[0]-=otherEdgeSeedCoord[0]
								otherEdgeTransformedCentreImagePoint[1]-=otherEdgeSeedCoord[1]
								otherEdgeTransformedCentreImagePoint[0]=otherEdgeTransformedCentreImagePoint[0]*scaleOtherToMain
								otherEdgeTransformedCentreImagePoint[1]=otherEdgeTransformedCentreImagePoint[1]*scaleOtherToMain
								otherEdgeTransformedCentreImagePoint[0]+=otherEdgeSeedCoord[0]
								otherEdgeTransformedCentreImagePoint[1]+=otherEdgeSeedCoord[1]
								
								successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane = True
								break
	else:
		print("sort this, couldnt be bothered automating step size for tangent calc")
		exit()
	
	if successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane and not(disjointPlanePairs) or lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']:
		# print("successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane")
		
		mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint = [] # THESE break up each segment into monotone clockwise/anticlockwise sections w.r.t. centre img point (OTHER centre img point for both of the lists)
		otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint = []
		
		if False: # ACTUALLY CAN ONLY STORE THIS WHEN ITS W.R.T. ITS OWN CENTRE IMAGE POINT OBVIOUSLY
			mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint=mainEdgePlanesSegments[3][0]
		else:
			for segmentDatInd, segmentDat in enumerate(mainEdgePlanesSegments[mainEdgeSeedPlane]):
				currSegmentAngularDat = []
				# 1 is clockwise, -1 is anticlockwise
				prevSign=None
				for coordI in range(1, len(segmentDat)):
					prevCoordDat = segmentDat[coordI-1]
					currCoordDat = segmentDat[coordI]
					sign = (currCoordDat[1] - otherEdgeTransformedCentreImagePoint[1])*(prevCoordDat[0] - otherEdgeTransformedCentreImagePoint[0]) - (currCoordDat[0] - otherEdgeTransformedCentreImagePoint[0])*(prevCoordDat[1] - otherEdgeTransformedCentreImagePoint[1])
					if prevSign is None:
						currSegmentAngularDat.append([])
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					elif sign<=0 and prevSign<=0 or sign>=0 and prevSign>=0:
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					else:
						currSegmentAngularDat.append([])
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					if prevSign is None or sign!=0:
						prevSign=sign
				for tmpSegAngDat in currSegmentAngularDat:
					if len(tmpSegAngDat)>2:
						firstCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][tmpSegAngDat[0][1]][tmpSegAngDat[0][2]]
						secondCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][tmpSegAngDat[1][1]][tmpSegAngDat[1][2]]
						lastCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][tmpSegAngDat[-1][1]][tmpSegAngDat[-1][2]]
						startAng = math.atan2(firstCoordDat[1]-otherEdgeTransformedCentreImagePoint[1], firstCoordDat[0]-otherEdgeTransformedCentreImagePoint[0])
						secondAng = math.atan2(secondCoordDat[1]-otherEdgeTransformedCentreImagePoint[1], secondCoordDat[0]-otherEdgeTransformedCentreImagePoint[0]) # can only reliably tell direction using 1 line segment otherwise weird 360 stuff
						endAng = math.atan2(lastCoordDat[1]-otherEdgeTransformedCentreImagePoint[1], lastCoordDat[0]-otherEdgeTransformedCentreImagePoint[0])
						
						clockwiseOrAnticlockwise=0
						tmpAng = secondAng-startAng
						if tmpAng<=-math.pi:
							tmpAng+=2*math.pi
						if tmpAng>math.pi:
							tmpAng-=2*math.pi
						if tmpAng<0:
							clockwiseOrAnticlockwise=1
						elif tmpAng>0:
							clockwiseOrAnticlockwise=-1
						else:
							pass
						
						if clockwiseOrAnticlockwise!=0: # just incase
							mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint.append([(startAng, endAng, clockwiseOrAnticlockwise), tmpSegAngDat])
			
		if 1-otherEdgeSeedPlane in otherEdgeSegmentedDat[3]:
			otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint=otherEdgeSegmentedDat[3][1-otherEdgeSeedPlane]
		else:
			for segmentDatInd, segmentDat in enumerate(otherEdgeSegmentedDat[0][1-otherEdgeSeedPlane]):
				
				currSegmentAngularDat = []
				# 1 is clockwise, -1 is anticlockwise
				prevSign=None
				for coordI in range(1, len(segmentDat)):
					prevCoordDat = segmentDat[coordI-1]
					currCoordDat = segmentDat[coordI]
					sign = (currCoordDat[1] - otherEdgeTransformedCentreImagePointBase[1])*(prevCoordDat[0] - otherEdgeTransformedCentreImagePointBase[0]) - (currCoordDat[0] - otherEdgeTransformedCentreImagePointBase[0])*(prevCoordDat[1] - otherEdgeTransformedCentreImagePointBase[1])
					if prevSign is None:
						currSegmentAngularDat.append([])
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					elif sign<=0 and prevSign<=0 or sign>=0 and prevSign>=0:
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					else:
						currSegmentAngularDat.append([])
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
						currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
					if prevSign is None or sign!=0:
						prevSign=sign
					
				for tmpSegAngDat in currSegmentAngularDat:
					if len(tmpSegAngDat)>2:
						firstCoordDat = otherEdgeSegmentedDat[0][1-otherEdgeSeedPlane][tmpSegAngDat[0][1]][tmpSegAngDat[0][2]]
						secondCoordDat = otherEdgeSegmentedDat[0][1-otherEdgeSeedPlane][tmpSegAngDat[1][1]][tmpSegAngDat[1][2]]
						lastCoordDat = otherEdgeSegmentedDat[0][1-otherEdgeSeedPlane][tmpSegAngDat[-1][1]][tmpSegAngDat[-1][2]]
						startAng = math.atan2(firstCoordDat[1]-otherEdgeTransformedCentreImagePointBase[1], firstCoordDat[0]-otherEdgeTransformedCentreImagePointBase[0])
						secondAng = math.atan2(secondCoordDat[1]-otherEdgeTransformedCentreImagePointBase[1], secondCoordDat[0]-otherEdgeTransformedCentreImagePointBase[0]) # can only reliably tell direction using 1 line segment otherwise weird 360 stuff
						endAng = math.atan2(lastCoordDat[1]-otherEdgeTransformedCentreImagePointBase[1], lastCoordDat[0]-otherEdgeTransformedCentreImagePointBase[0])
						
						clockwiseOrAnticlockwise=0
						tmpAng = secondAng-startAng
						if tmpAng<=-math.pi:
							tmpAng+=2*math.pi
						if tmpAng>math.pi:
							tmpAng-=2*math.pi
						if tmpAng<0:
							clockwiseOrAnticlockwise=1
						elif tmpAng>0:
							clockwiseOrAnticlockwise=-1
						else:
							pass
						
						if clockwiseOrAnticlockwise!=0: # just incase
							otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint.append([(startAng, endAng, clockwiseOrAnticlockwise), tmpSegAngDat])
			otherEdgeSegmentedDat[3][1-otherEdgeSeedPlane]=otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint
			
		overlapDat = []
		
		tmpRoughDistFromCentreImgPtToEdges = getDistance(otherEdgeTransformedCentreImagePoint[0], mainEdgeSeedCoord[0], otherEdgeTransformedCentreImagePoint[1], mainEdgeSeedCoord[1])
		for otherEdgeAngularDatInd, otherEdgeAngularDat in enumerate(otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint):
			for mainEdgeAngularDatInd, mainEdgeAngularDat in enumerate(mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint):
				if otherEdgeAngularDat[0][2]==mainEdgeAngularDat[0][2]: # both segments/areas go in same direction
					tmpAngInt1=[]
					tmpAngInt2=[]
					overlapInt=[]
					if otherEdgeAngularDat[0][2]==1:
						tmpAngInt1=[mainEdgeAngularDat[0][1], mainEdgeAngularDat[0][0]]
						tmpAngInt2=[otherEdgeAngularDat[0][1], otherEdgeAngularDat[0][0]]
					elif otherEdgeAngularDat[0][2]==-1:
						tmpAngInt1=[mainEdgeAngularDat[0][0], mainEdgeAngularDat[0][1]]
						tmpAngInt2=[otherEdgeAngularDat[0][0], otherEdgeAngularDat[0][1]]
						
					if tmpAngInt1[0] <= tmpAngInt1[1]:
						if tmpAngInt2[0] <= tmpAngInt2[1]:
							overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
							overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
							if overlapStart<=overlapEnd:
								overlapInt=(overlapStart, overlapEnd)
							else:
								# no overlap
								pass
						else:
							if tmpAngInt1[1] >= tmpAngInt2[0]:
								overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
								overlapEnd = tmpAngInt1[1]
								overlapInt=(overlapStart, overlapEnd)
							elif tmpAngInt1[0] <= tmpAngInt2[1]:
								overlapStart = tmpAngInt1[0]
								overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
								overlapInt=(overlapStart, overlapEnd)
							else:
								# no overlap
								pass
							
					else:
						if tmpAngInt2[0] <= tmpAngInt2[1]:
							if tmpAngInt2[1] >= tmpAngInt1[0]:
								overlapStart = max(tmpAngInt2[0], tmpAngInt1[0])
								overlapEnd = tmpAngInt2[1]
								overlapInt=(overlapStart, overlapEnd)
							elif tmpAngInt2[0] <= tmpAngInt1[1]:
								overlapStart = tmpAngInt2[0]
								overlapEnd = min(tmpAngInt2[1], tmpAngInt1[1])
								overlapInt=(overlapStart, overlapEnd)
							else:
								# no overlap
								pass
							
						else:
							overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
							overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
							overlapInt=(overlapStart, overlapEnd)
					if len(overlapInt)==2 and otherEdgeAngularDat[0][2]==1:
						overlapInt=(overlapInt[1], overlapInt[0])
					
					if len(overlapInt)==2:
						
						tmpCrossingPt1 = (tmpRoughDistFromCentreImgPtToEdges, 0)
						tmpCrossingPt2 = (tmpRoughDistFromCentreImgPtToEdges, 0)
						
						tmpCrossingPt1 = (tmpCrossingPt1[0]*math.cos(overlapInt[0])-tmpCrossingPt1[1]*math.sin(overlapInt[0]), tmpCrossingPt1[0]*math.sin(overlapInt[0])+tmpCrossingPt1[1]*math.cos(overlapInt[0]))
						tmpCrossingPt2 = (tmpCrossingPt2[0]*math.cos(overlapInt[1])-tmpCrossingPt2[1]*math.sin(overlapInt[1]), tmpCrossingPt2[0]*math.sin(overlapInt[1])+tmpCrossingPt2[1]*math.cos(overlapInt[1]))
						
						tmpCrossingPt1 = (tmpCrossingPt1[0]+otherEdgeTransformedCentreImagePoint[0], tmpCrossingPt1[1]+otherEdgeTransformedCentreImagePoint[1])
						tmpCrossingPt2 = (tmpCrossingPt2[0]+otherEdgeTransformedCentreImagePoint[0], tmpCrossingPt2[1]+otherEdgeTransformedCentreImagePoint[1])
						
						crossingPt1IndBeforeOther=-1
						tmpFirstCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
						tmpFirstCoord = tmpFirstCoordDat
						prevSign = (tmpFirstCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - otherEdgeTransformedCentreImagePoint[1])
						maybeStartCrosses=False
						if abs(prevSign)<0.00001:
							maybeStartCrosses=True
						for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
							tmpCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
							tmpCoord = tmpCoordDat
							currSign = (tmpCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - otherEdgeTransformedCentreImagePoint[1])
							if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
								crossingPt1IndBeforeOther=tmpCoordDatI-1
								break
							prevSign=currSign
						if crossingPt1IndBeforeOther<0:
							if maybeStartCrosses:
								crossingPt1IndBeforeOther=0
							elif abs(prevSign)<0.00001:
								crossingPt1IndBeforeOther=len(otherEdgeAngularDat[1])-2
						
							
						crossingPt2IndBeforeOther=-1
						tmpFirstCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
						tmpFirstCoord = tmpFirstCoordDat
						prevSign = (tmpFirstCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - otherEdgeTransformedCentreImagePoint[1])
						maybeStartCrosses=False
						if abs(prevSign)<0.00001:
							maybeStartCrosses=True
						for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
							tmpCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
							tmpCoord = tmpCoordDat
							currSign = (tmpCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - otherEdgeTransformedCentreImagePoint[1])
							if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
								crossingPt2IndBeforeOther=tmpCoordDatI-1
								break
							prevSign=currSign
						if crossingPt2IndBeforeOther<0:
							if maybeStartCrosses:
								crossingPt2IndBeforeOther=0
							elif abs(prevSign)<0.00001:
								crossingPt2IndBeforeOther=len(otherEdgeAngularDat[1])-2
						
						# main pts
						
						crossingPt1IndBeforeMain=-1
						tmpFirstCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
						tmpFirstCoord = tmpFirstCoordDat
						prevSign = (tmpFirstCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - otherEdgeTransformedCentreImagePoint[1])
						maybeStartCrosses=False
						if abs(prevSign)<0.00001:
							maybeStartCrosses=True
						for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
							tmpCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
							tmpCoord = tmpCoordDat
							currSign = (tmpCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - otherEdgeTransformedCentreImagePoint[1])
							if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
								crossingPt1IndBeforeMain=tmpCoordDatI-1
								break
							prevSign=currSign
						if crossingPt1IndBeforeMain<0:
							if maybeStartCrosses:
								crossingPt1IndBeforeMain=0
							elif abs(prevSign)<0.00001:
								crossingPt1IndBeforeMain=len(mainEdgeAngularDat[1])-2
						
							
						crossingPt2IndBeforeMain=-1
						tmpFirstCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
						tmpFirstCoord = tmpFirstCoordDat
						prevSign = (tmpFirstCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - otherEdgeTransformedCentreImagePoint[1])
						maybeStartCrosses=False
						if abs(prevSign)<0.00001:
							maybeStartCrosses=True
						for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
							tmpCoordDat = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
							tmpCoord = tmpCoordDat
							currSign = (tmpCoord[1] - otherEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - otherEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - otherEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - otherEdgeTransformedCentreImagePoint[1])
							if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
								crossingPt2IndBeforeMain=tmpCoordDatI-1
								break
							prevSign=currSign
						if crossingPt2IndBeforeMain<0:
							if maybeStartCrosses:
								crossingPt2IndBeforeMain=0
							elif abs(prevSign)<0.00001:
								crossingPt2IndBeforeMain=len(mainEdgeAngularDat[1])-2
						
						if crossingPt1IndBeforeMain>=0 and crossingPt2IndBeforeMain>=0 and crossingPt1IndBeforeOther>=0 and crossingPt2IndBeforeOther>=0:
							
							tmpReduceDupeCodeList = [] # put pairs of startPt and endPt and any vars used below that change in here then loop
							windowCentreImgPtToOverlapStartLineM = None
							windowCentreImgPtToOverlapStartLineC = None
							if tmpCrossingPt1[0]-otherEdgeTransformedCentreImagePoint[0]==0:
								windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[0]
								# pass
							else:
								windowCentreImgPtToOverlapStartLineM = (tmpCrossingPt1[1]-otherEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt1[0]-otherEdgeTransformedCentreImagePoint[0])
								windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[1]-windowCentreImgPtToOverlapStartLineM*tmpCrossingPt1[0]
							
							windowCentreImgPtToOverlapEndLineM = None
							windowCentreImgPtToOverlapEndLineC = None
							if tmpCrossingPt2[0]-otherEdgeTransformedCentreImagePoint[0]==0:
								windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[0]
								# pass
							else:
								windowCentreImgPtToOverlapEndLineM = (tmpCrossingPt2[1]-otherEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt2[0]-otherEdgeTransformedCentreImagePoint[0])
								windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[1]-windowCentreImgPtToOverlapEndLineM*tmpCrossingPt2[0]
							
							startPt1 = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][2]]
							endPt1 = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][2]]
							startPt2 = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][2]]
							endPt2 = mainEdgePlanesSegments[mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][2]]
							startPt3 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][2]]
							endPt3 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][2]]
							startPt4 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][2]]
							endPt4 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][2]]
							
							# startPt, endPt, windowLineM, windowLineC, indBefore
							tmpReduceDupeCodeList.append((startPt1, endPt1, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeMain))
							tmpReduceDupeCodeList.append((startPt2, endPt2, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeMain))
							tmpReduceDupeCodeList.append((startPt3, endPt3, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeOther))
							tmpReduceDupeCodeList.append((startPt4, endPt4, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeOther))
							
							indexAsRatios = []
							for tmpVars in tmpReduceDupeCodeList:
								startPt, endPt, tmpLineM, tmpLineC, indBefore = tmpVars
								if tmpLineM is None:
									if endPt[0]-startPt[0]!=0:
										tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
										if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
											tempT=0
										if tempT>1:
											tempT=1
										indexAsRatios.append(indBefore+tempT)
								elif tmpLineM == 0:
									if endPt[1]-startPt[1]!=0:
										tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
										if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
											tempT=0
										if tempT>1:
											tempT=1
										indexAsRatios.append(indBefore+tempT)
								else:
									tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
									if tmpDiv!=0:
										tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
										if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
											tempT=0
										if tempT>1:
											tempT=1
										indexAsRatios.append(indBefore+tempT)
							if len(indexAsRatios)==4:
								overlapDat.append(( abs(indexAsRatios[1]-indexAsRatios[0]), (mainEdgeAngularDatInd, indexAsRatios[0], indexAsRatios[1]), (otherEdgeAngularDatInd, indexAsRatios[2], indexAsRatios[3])  ))
		
		overlapDat.sort(reverse=True)
		if "baseTangentsWRTcentreImgPoint" not in otherEdgeSegmentedDat[3]:
			baseTangentDat = otherEdgeSegmentedDat[3]["baseTangents"]
			# since i currently have baseTangents coded s.t. it requires a point before and after a given point to estimate tangent, i will need at least 1 point before and after a given point to calculate its tangent w.r.t. line from centre img pt
			tempBaseTangentsWRTcentreImgPointDat = []
			for planeInd, planeDat in enumerate(otherEdgeSegmentedDat[0]):
				tempBaseTangentsWRTcentreImgPointDat.append([])
				for segmentDatInd, segmentDat in enumerate(planeDat):
					tmpSegWRTCenteImgPtDat = [None]
					for i in range(1, len(segmentDat)-1):
						estTangentAtPointOrientation = baseTangentDat[planeInd][segmentDatInd][i]
						tangentPoint = otherEdgeSegmentedDat[0][planeInd][segmentDatInd][i]
						tmpLineOrientation = math.atan2(tangentPoint[1]-otherEdgeTransformedCentreImagePointBase[1], tangentPoint[0]-otherEdgeTransformedCentreImagePointBase[0])
						orientationDifference = estTangentAtPointOrientation-tmpLineOrientation
						if orientationDifference<math.pi:
							orientationDifference+=2*math.pi
						if orientationDifference>math.pi:
							orientationDifference-=2*math.pi
						if orientationDifference<0:
							tmpDiffFromPerpendicular = -90*math.pi/180 - orientationDifference
							tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
							if True: # 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
								tmpSegWRTCenteImgPtDat.append(90*math.pi/180-tmpDiffFromPerpendicular)
							
						else:
							tmpDiffFromPerpendicular = 90*math.pi/180 - orientationDifference
							tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
							if True: # 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
								tmpSegWRTCenteImgPtDat.append(90*math.pi/180-tmpDiffFromPerpendicular)
							
						
					tmpSegWRTCenteImgPtDat.append(None)
					tempBaseTangentsWRTcentreImgPointDat[planeInd].append(tmpSegWRTCenteImgPtDat)
			otherEdgeSegmentedDat[3]["baseTangentsWRTcentreImgPoint"]=tempBaseTangentsWRTcentreImgPointDat
			
		baseTangentsWRTcentreImgPointDat = otherEdgeSegmentedDat[3]["baseTangentsWRTcentreImgPoint"]
		
		overlapDatPerpendicularity = [] # could potentially find a weighting system for size of neighbourhood of perpendicularity plus perpendicularness e.g. prioritise 3 point neighbourhood of 50 deg perp over 1 point with 60 perp but for now just take single pt with highest perpendicularity
		
		for tmpOverlapDatInd, tmpOverlapDat in enumerate(overlapDat):
			
			mostPerpendicularPointSegmentDatInd = None
			mostPerpendicularPointCoordDatInd = None
			mostPerpendicularPointPerpendicularity = None
			earlyBreakBecauseGoodEnoughFound = False
			mostPerpendicularPointOverlapDatInd = None
			
			
			mainEdgeAngularDatInd, mainIndAsRatio1, mainIndAsRatio2 = tmpOverlapDat[1]
			otherEdgeAngularDatInd, otherIndAsRatio1, otherIndAsRatio2 = tmpOverlapDat[2]
			
			earlyBreakBecauseGoodEnoughFound = False
			
			if math.floor(otherIndAsRatio1) != math.floor(otherIndAsRatio2): # need at least 1 index integer between them (i.e. 1 coordDat)
				
				consecutivePerpendicularEnoughCtr = 0
				
				startInd = otherIndAsRatio1
				endInd = otherIndAsRatio2
				if startInd>endInd:
					startInd, endInd = endInd, startInd
				startInd = math.ceil(startInd)
				endInd = math.floor(endInd)
				
				### DEBUG
				prevSegmentDatInd = None
				
				for tmpInd in range(startInd, endInd+1):
					
					junk, tmpSegmentDatInd, tmpCoordInd = otherEdgeSwappedPlaneAngularDatFromOtherEdgeImageCentrePoint[otherEdgeAngularDatInd][1][tmpInd]
					
					tangentPerpendicularityOfPoint = baseTangentsWRTcentreImgPointDat[1-otherEdgeSeedPlane][tmpSegmentDatInd][tmpCoordInd] # if point has one before and after then this will usually be the angle of how different the tangent at the point is compared to line from centre img pt of other edge to the point
					if tangentPerpendicularityOfPoint is not None: # e.g. if tangent at point intersects with line from otherEdge centre img pt at a right angle, this will be 90 degrees in radians
						
						if mostPerpendicularPointPerpendicularity is None or tangentPerpendicularityOfPoint>mostPerpendicularPointPerpendicularity:
							mostPerpendicularPointPerpendicularity=tangentPerpendicularityOfPoint
							mostPerpendicularPointSegmentDatInd=tmpSegmentDatInd
							mostPerpendicularPointCoordDatInd=tmpCoordInd
							mostPerpendicularPointOverlapDatInd=tmpOverlapDatInd
						
						if tangentPerpendicularityOfPoint<hardMinimumPerpendicularity:
							consecutivePerpendicularEnoughCtr=0
						else:
							consecutivePerpendicularEnoughCtr+=1
						if consecutivePerpendicularEnoughCtr>=3:
							mostPerpendicularPointPerpendicularity=tangentPerpendicularityOfPoint
							mostPerpendicularPointSegmentDatInd=tmpSegmentDatInd
							mostPerpendicularPointCoordDatInd=tmpCoordInd-1
							mostPerpendicularPointOverlapDatInd=tmpOverlapDatInd
							
							#### DEBUG
							if tmpSegmentDatInd!=prevSegmentDatInd:
								print("huh????? ijdeo12hid")
								exit()
							
							earlyBreakBecauseGoodEnoughFound=True
							break
					else:
						consecutivePerpendicularEnoughCtr=0
					prevSegmentDatInd=tmpSegmentDatInd
			
			if mostPerpendicularPointPerpendicularity is not None:
				overlapDatPerpendicularity.append((mostPerpendicularPointPerpendicularity, mostPerpendicularPointSegmentDatInd, mostPerpendicularPointCoordDatInd, mostPerpendicularPointOverlapDatInd))
			
		if len(overlapDatPerpendicularity)>0 or secondOtherPlaneHasPoints==False or lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']: # we have the most perpendicular point, might be bad/not perpendicular at all and high error etc but just continue to scale the plane
			
			overlapDatPerpendicularity.sort(reverse=True)
			actualMainEdgeIntersectionPoint = None
			actualMostPerpendicularOtherEdgeCoordInOverlap=None
			
			for overlapDatPerpendicularityDat in overlapDatPerpendicularity:
				mostPerpendicularPointPerpendicularity, mostPerpendicularPointSegmentDatInd, mostPerpendicularPointCoordDatInd, mostPerpendicularPointOverlapDatInd = overlapDatPerpendicularityDat
				
				mainEdgeAngularDatInd, mainIndAsRatio1, mainIndAsRatio2 = overlapDat[mostPerpendicularPointOverlapDatInd][1]
				startInd = mainIndAsRatio1
				endInd = mainIndAsRatio2
				if startInd>endInd:
					startInd, endInd = endInd, startInd
				
				mostPerpendicularOtherEdgeCoordInOverlap = otherEdgePlanesSegments[1-otherEdgeSeedPlane][mostPerpendicularPointSegmentDatInd][mostPerpendicularPointCoordDatInd]
				otherEdgePointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[1-otherEdgeSeedPlane][mostPerpendicularPointSegmentDatInd][mostPerpendicularPointCoordDatInd]
				
				mainEdgeIntersectionPoint = None
				mainEdgeIntersectionPointStepCoordIndBefore = None
				
				tmpLineM = None
				tmpLineC = None
				if mostPerpendicularOtherEdgeCoordInOverlap[0]-otherEdgeTransformedCentreImagePoint[0]!=0:
					tmpLineM = (mostPerpendicularOtherEdgeCoordInOverlap[1]-otherEdgeTransformedCentreImagePoint[1])/(mostPerpendicularOtherEdgeCoordInOverlap[0]-otherEdgeTransformedCentreImagePoint[0])
					tmpLineC = mostPerpendicularOtherEdgeCoordInOverlap[1]-tmpLineM*mostPerpendicularOtherEdgeCoordInOverlap[0]
				else:
					tmpLineC = mostPerpendicularOtherEdgeCoordInOverlap[0]
				
				if math.floor(startInd)==math.floor(endInd):
					startPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(startInd)][1]
					startPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(startInd)][2]
					endPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(endInd)][1]
					endPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(endInd)][2]
					startPt = mainEdgePlanesSegments[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
					endPt = mainEdgePlanesSegments[mainEdgeSeedPlane][endPtSegInd][endPtCoordInd]
					lineRatioStart = startInd-math.floor(startInd)
					lineRatioEnd = endInd-math.floor(endInd)
					
					if tmpLineM is None:
						if endPt[0]-startPt[0]!=0:
							tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
							
							tmpIntersectionRatio = None
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
							elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
								tmpIntersectionRatio=lineRatioStart
							else:
								tmpIntersectionRatio=lineRatioEnd
							tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
							mainEdgeIntersectionPoint = [tmpLineC, tempY]
							mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							
					elif tmpLineM == 0:
						if endPt[1]-startPt[1]!=0:
							tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
							
							tmpIntersectionRatio = None
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
							elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
								tmpIntersectionRatio=lineRatioStart
							else:
								tmpIntersectionRatio=lineRatioEnd
							tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
							mainEdgeIntersectionPoint = [tempX, tmpLineC]
							mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
					else:
						tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
						if tmpDiv!=0:
							tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
							
							tmpIntersectionRatio = None
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
							elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
								tmpIntersectionRatio=lineRatioStart
							else:
								tmpIntersectionRatio=lineRatioEnd
							tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
							tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
							mainEdgeIntersectionPoint = [tempX, tempY]
							mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
					
				else:
					
					beforeRatioStart = None
					coordIfBeforeRatioStart = None
					afterRatioEnd = None
					coordIfAfterRatioEnd = None
					
					mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = None
					mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = None
					
					startPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(startInd)][1]
					startPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(startInd)][2]
					endPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(startInd)][1]
					endPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(startInd)][2]
					startPt = mainEdgePlanesSegments[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
					endPt = mainEdgePlanesSegments[mainEdgeSeedPlane][endPtSegInd][endPtCoordInd]
					
					lineRatioStart = startInd-math.floor(startInd)
					lineRatioEnd = 1
					
					######### first ind ratio to first ind
					
					if tmpLineM is None:
						if endPt[0]-startPt[0]!=0:
							tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
							
							tmpIntersectionRatio = None
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
								tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
								mainEdgeIntersectionPoint = [tmpLineC, tempY]
								mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							elif tempT<lineRatioStart:
								beforeRatioStart=lineRatioStart-tempT
								
								tmpIntersectionRatio=lineRatioStart
								tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
								coordIfBeforeRatioStart = [tmpLineC, tempY]
								mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							
							
					elif tmpLineM == 0:
						if endPt[1]-startPt[1]!=0:
							tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
							
							tmpIntersectionRatio = None
							
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
								tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
								mainEdgeIntersectionPoint = [tempX, tmpLineC]
								mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							elif tempT<lineRatioStart: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
								beforeRatioStart=lineRatioStart-tempT
								
								tmpIntersectionRatio=lineRatioStart
								tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
								coordIfBeforeRatioStart = [tempX, tmpLineC]
								mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							
							
					else:
						tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
						if tmpDiv!=0:
							tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
							
							tmpIntersectionRatio = None
							if tempT>=lineRatioStart and tempT<=lineRatioEnd:
								tmpIntersectionRatio=tempT
								tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
								tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
								mainEdgeIntersectionPoint = [tempX, tempY]
								mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							elif tempT<lineRatioStart:
								beforeRatioStart=lineRatioStart-tempT
								tmpIntersectionRatio=lineRatioStart
								tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
								tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
								coordIfBeforeRatioStart = [tempX, tempY]
								mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							
					if mainEdgeIntersectionPoint is None:
						
						startPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(endInd)][1]
						startPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.floor(endInd)][2]
						endPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(endInd)][1]
						endPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][math.ceil(endInd)][2]
						startPt = mainEdgePlanesSegments[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
						endPt = mainEdgePlanesSegments[mainEdgeSeedPlane][endPtSegInd][endPtCoordInd]
						
						lineRatioStart = 0
						lineRatioEnd = endInd-math.floor(endInd)
						
						if tmpLineM is None:
							if endPt[0]-startPt[0]!=0:
								tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
								
								tmpIntersectionRatio = None
								if tempT>=lineRatioStart and tempT<=lineRatioEnd:
									tmpIntersectionRatio=tempT
									tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
									mainEdgeIntersectionPoint = [tmpLineC, tempY]
									mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								elif tempT>lineRatioEnd: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
									afterRatioEnd=tempT-lineRatioEnd
									
									tmpIntersectionRatio=lineRatioEnd
									tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
									coordIfAfterRatioEnd = [tmpLineC, tempY]
									mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								
								
						elif tmpLineM == 0:
							if endPt[1]-startPt[1]!=0:
								tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
								
								tmpIntersectionRatio = None
								
								if tempT>=lineRatioStart and tempT<=lineRatioEnd:
									tmpIntersectionRatio=tempT
									tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
									mainEdgeIntersectionPoint = [tempX, tmpLineC]
									mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								elif tempT>lineRatioEnd:
									afterRatioEnd=tempT-lineRatioEnd
									
									tmpIntersectionRatio=lineRatioEnd
									tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
									coordIfAfterRatioEnd = [tempX, tmpLineC]
									mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								
								
						else:
							tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
							if tmpDiv!=0:
								tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
								
								tmpIntersectionRatio = None
								if tempT>=lineRatioStart and tempT<=lineRatioEnd:
									tmpIntersectionRatio=tempT
									tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
									tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
									mainEdgeIntersectionPoint = [tempX, tempY]
									mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								elif tempT>lineRatioEnd:
									afterRatioEnd=tempT-lineRatioEnd
									tmpIntersectionRatio=lineRatioEnd
									tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
									tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
									coordIfAfterRatioEnd = [tempX, tempY]
									mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
								
					######### all inds between
					
					if mainEdgeIntersectionPoint is None:
						for tmpInd in range(math.ceil(startInd), math.floor(endInd)):
							
							startPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][tmpInd][1]
							startPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][tmpInd][2]
							endPtSegInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][tmpInd+1][1]
							endPtCoordInd = mainEdgeFirstPlaneAngularDatFromOtherEdgeImageCentrePoint[mainEdgeAngularDatInd][1][tmpInd+1][2]
							startPt = mainEdgePlanesSegments[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
							endPt = mainEdgePlanesSegments[mainEdgeSeedPlane][endPtSegInd][endPtCoordInd]
							
							if tmpLineM is None:
								if endPt[0]-startPt[0]!=0:
									tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
									
									tmpIntersectionRatio = None
									if tempT>=0 and tempT<=1:
										tmpIntersectionRatio=tempT
										tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
										mainEdgeIntersectionPoint = [tmpLineC, tempY]
										mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
									
							elif tmpLineM == 0:
								if endPt[1]-startPt[1]!=0:
									tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
									tmpIntersectionRatio = None
									if tempT>=0 and tempT<=1:
										tmpIntersectionRatio=tempT
										tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
										mainEdgeIntersectionPoint = [tempX, tmpLineC]
										mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
									
							else:
								tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
								if tmpDiv!=0:
									tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
									
									tmpIntersectionRatio = None
									if tempT>=0 and tempT<=1:
										tmpIntersectionRatio=tempT
										tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
										tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
										mainEdgeIntersectionPoint = [tempX, tempY]
										mainEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[mainEdgeSeedPlane][startPtSegInd][startPtCoordInd]
									
					
					if mainEdgeIntersectionPoint is None:
						if beforeRatioStart is not None and afterRatioEnd is not None:
							if beforeRatioStart<afterRatioEnd:
								mainEdgeIntersectionPoint=coordIfBeforeRatioStart
								mainEdgeIntersectionPointStepCoordIndBefore = mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart
							else:
								mainEdgeIntersectionPoint=coordIfAfterRatioEnd
								mainEdgeIntersectionPointStepCoordIndBefore = mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd
						elif beforeRatioStart is not None:
							mainEdgeIntersectionPoint=coordIfBeforeRatioStart
							mainEdgeIntersectionPointStepCoordIndBefore = mainEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart
						elif afterRatioEnd is not None:
							mainEdgeIntersectionPoint=coordIfAfterRatioEnd
							mainEdgeIntersectionPointStepCoordIndBefore = mainEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd
					
				estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace = None
				
				idkFailure2=False
				if stepCoordIndBeforeOtherSeed<otherEdgePointStepCoordIndBefore:
					tmpAmountAway=otherEdgePointStepCoordIndBefore-stepCoordIndBeforeOtherSeed
					tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError)
					tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
					
					tmpInterval = [stepCoordIndBeforeMainSeed+tmpAmountAwayLower, stepCoordIndBeforeMainSeed+tmpAmountAwayUpper]
					
					tmpInterval[0]=max(tmpInterval[0], stepCoordIndBeforeMainSeed+1)
					tmpInterval[1]=min(tmpInterval[1], len(stepCoordsMain)-1)
					if tmpInterval[0]>=tmpInterval[1]:
						idkFailure2=True
					estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace=tmpInterval
					
				elif stepCoordIndBeforeOtherSeed>otherEdgePointStepCoordIndBefore:
					tmpAmountAway=stepCoordIndBeforeOtherSeed-otherEdgePointStepCoordIndBefore
					tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError) # lower/upper here is gonna be used reversed from intuition cause its lower/upper w.r.t. outwards from seed point
					tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
					
					tmpInterval = [stepCoordIndBeforeMainSeed-tmpAmountAwayUpper, stepCoordIndBeforeMainSeed-tmpAmountAwayLower]
					
					tmpInterval[0]=max(tmpInterval[0], 0)
					tmpInterval[1]=min(tmpInterval[1], stepCoordIndBeforeMainSeed-1)
					if tmpInterval[0]>=tmpInterval[1]:
						
						idkFailure2=True
					estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace=tmpInterval
				else:
					
					idkFailure2=True
				if not(idkFailure2):
					if mainEdgeIntersectionPointStepCoordIndBefore is not None and mainEdgeIntersectionPointStepCoordIndBefore >= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace[0] and mainEdgeIntersectionPointStepCoordIndBefore <= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInMainEdgeSpace[1]:
						actualMainEdgeIntersectionPoint = mainEdgeIntersectionPoint
						actualMostPerpendicularOtherEdgeCoordInOverlap = mostPerpendicularOtherEdgeCoordInOverlap
						break
					
				
			if actualMainEdgeIntersectionPoint is not None or secondOtherPlaneHasPoints==False or lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']:
				
				if actualMainEdgeIntersectionPoint is not None:
					
					mainEdgeIntersectionPoint = actualMainEdgeIntersectionPoint
					mostPerpendicularOtherEdgeCoordInOverlap = actualMostPerpendicularOtherEdgeCoordInOverlap
					
					distToMainEdgePt = getDistance(mainEdgeIntersectionPoint[0], otherEdgeTransformedCentreImagePoint[0], mainEdgeIntersectionPoint[1], otherEdgeTransformedCentreImagePoint[1])
					distToOtherEdgePt = getDistance(mostPerpendicularOtherEdgeCoordInOverlap[0], otherEdgeTransformedCentreImagePoint[0], mostPerpendicularOtherEdgeCoordInOverlap[1], otherEdgeTransformedCentreImagePoint[1])
					scaleOtherEdgeSwappedPlaneBy = distToMainEdgePt/distToOtherEdgePt
					
					for segmentDat in otherEdgePlanesSegments[1-otherEdgeSeedPlane]:
						for coordDat in segmentDat:
							coordX = coordDat[0] - otherEdgeTransformedCentreImagePoint[0]
							coordX = coordX*scaleOtherEdgeSwappedPlaneBy
							coordX = coordX + otherEdgeTransformedCentreImagePoint[0]
							
							coordY = coordDat[1] - otherEdgeTransformedCentreImagePoint[1]
							coordY = coordY*scaleOtherEdgeSwappedPlaneBy
							coordY = coordY + otherEdgeTransformedCentreImagePoint[1]
							
							coordDat[0]=coordX
							coordDat[1]=coordY
				
				otherEdgeFirstPlaneAngularDatFromMainEdgeImageCentrePoint = [] # THESE break up each segment into monotone clockwise/anticlockwise sections w.r.t. centre img point (OTHER centre img point for both of the lists)
				mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint = []
				
				otherEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint = [] # adding this since this plane should now be aligned so we can also check this plane for overlap
				
				verydebug=[]
				
				
				if False: # ACTUALLY CAN ONLY STORE THIS WHEN ITS W.R.T. ITS OWN CENTRE IMAGE POINT OBVIOUSLY
					otherEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint=otherEdgePlanesSegments[3][0]
				else:
					for segmentDatInd, segmentDat in enumerate(otherEdgePlanesSegments[1-otherEdgeSeedPlane]):
						currSegmentAngularDat = []
						# 1 is clockwise, -1 is anticlockwise
						prevSign=None
						for coordI in range(1, len(segmentDat)):
							prevCoordDat = segmentDat[coordI-1]
							currCoordDat = segmentDat[coordI]
							sign = (currCoordDat[1] - mainEdgeTransformedCentreImagePoint[1])*(prevCoordDat[0] - mainEdgeTransformedCentreImagePoint[0]) - (currCoordDat[0] - mainEdgeTransformedCentreImagePoint[0])*(prevCoordDat[1] - mainEdgeTransformedCentreImagePoint[1])
							if prevSign is None:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							elif sign<=0 and prevSign<=0 or sign>=0 and prevSign>=0:
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							else:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							if prevSign is None or sign!=0:
								prevSign=sign
						for tmpSegAngDat in currSegmentAngularDat:
							if len(tmpSegAngDat)>2:
								firstCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][tmpSegAngDat[0][1]][tmpSegAngDat[0][2]]
								secondCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][tmpSegAngDat[1][1]][tmpSegAngDat[1][2]]
								lastCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][tmpSegAngDat[-1][1]][tmpSegAngDat[-1][2]]
								startAng = math.atan2(firstCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], firstCoordDat[0]-mainEdgeTransformedCentreImagePoint[0])
								secondAng = math.atan2(secondCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], secondCoordDat[0]-mainEdgeTransformedCentreImagePoint[0]) # can only reliably tell direction using 1 line segment otherwise weird 360 stuff
								endAng = math.atan2(lastCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], lastCoordDat[0]-mainEdgeTransformedCentreImagePoint[0])
								
								clockwiseOrAnticlockwise=0
								tmpAng = secondAng-startAng
								if tmpAng<=-math.pi:
									tmpAng+=2*math.pi
								if tmpAng>math.pi:
									tmpAng-=2*math.pi
								if tmpAng<0:
									clockwiseOrAnticlockwise=1
								elif tmpAng>0:
									clockwiseOrAnticlockwise=-1
								else:
									pass
								
								if clockwiseOrAnticlockwise!=0: # just incase
									otherEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint.append([(startAng, endAng, clockwiseOrAnticlockwise), tmpSegAngDat])
					
				
				if False: # ACTUALLY CAN ONLY STORE THIS WHEN ITS W.R.T. ITS OWN CENTRE IMAGE POINT OBVIOUSLY
					otherEdgeFirstPlaneAngularDatFromMainEdgeImageCentrePoint=otherEdgePlanesSegments[3][0]
				else:
					for segmentDatInd, segmentDat in enumerate(otherEdgePlanesSegments[otherEdgeSeedPlane]):
						currSegmentAngularDat = []
						# 1 is clockwise, -1 is anticlockwise
						prevSign=None
						for coordI in range(1, len(segmentDat)):
							prevCoordDat = segmentDat[coordI-1]
							currCoordDat = segmentDat[coordI]
							sign = (currCoordDat[1] - mainEdgeTransformedCentreImagePoint[1])*(prevCoordDat[0] - mainEdgeTransformedCentreImagePoint[0]) - (currCoordDat[0] - mainEdgeTransformedCentreImagePoint[0])*(prevCoordDat[1] - mainEdgeTransformedCentreImagePoint[1])
							if prevSign is None:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							elif sign<=0 and prevSign<=0 or sign>=0 and prevSign>=0:
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							else:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							if prevSign is None or sign!=0:
								prevSign=sign
						for tmpSegAngDat in currSegmentAngularDat:
							if len(tmpSegAngDat)>2:
								firstCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][tmpSegAngDat[0][1]][tmpSegAngDat[0][2]]
								secondCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][tmpSegAngDat[1][1]][tmpSegAngDat[1][2]]
								lastCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][tmpSegAngDat[-1][1]][tmpSegAngDat[-1][2]]
								startAng = math.atan2(firstCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], firstCoordDat[0]-mainEdgeTransformedCentreImagePoint[0])
								secondAng = math.atan2(secondCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], secondCoordDat[0]-mainEdgeTransformedCentreImagePoint[0]) # can only reliably tell direction using 1 line segment otherwise weird 360 stuff
								endAng = math.atan2(lastCoordDat[1]-mainEdgeTransformedCentreImagePoint[1], lastCoordDat[0]-mainEdgeTransformedCentreImagePoint[0])
								
								verydebug.append(firstCoordDat)
								verydebug.append(secondCoordDat)
								verydebug.append(mainEdgeTransformedCentreImagePoint)
								
								clockwiseOrAnticlockwise=0
								tmpAng = secondAng-startAng
								if tmpAng<=-math.pi:
									tmpAng+=2*math.pi
								if tmpAng>math.pi:
									tmpAng-=2*math.pi
								if tmpAng<0:
									clockwiseOrAnticlockwise=1
								elif tmpAng>0:
									clockwiseOrAnticlockwise=-1
								else:
									pass
								
								if clockwiseOrAnticlockwise!=0: # just incase
									otherEdgeFirstPlaneAngularDatFromMainEdgeImageCentrePoint.append([(startAng, endAng, clockwiseOrAnticlockwise), tmpSegAngDat])
					
				if 1-mainEdgeSeedPlane in mainEdgeSegmentedDat[3] and not(debugmode):
					mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint=mainEdgeSegmentedDat[3][1-mainEdgeSeedPlane]
				else:
					for segmentDatInd, segmentDat in enumerate(mainEdgeSegmentedDat[0][1-mainEdgeSeedPlane]):
						currSegmentAngularDat = []
						# 1 is clockwise, -1 is anticlockwise
						prevSign=None
						for coordI in range(1, len(segmentDat)):
							prevCoordDat = segmentDat[coordI-1]
							currCoordDat = segmentDat[coordI]
							sign = (currCoordDat[1] - mainEdgeTransformedCentreImagePointBase[1])*(prevCoordDat[0] - mainEdgeTransformedCentreImagePointBase[0]) - (currCoordDat[0] - mainEdgeTransformedCentreImagePointBase[0])*(prevCoordDat[1] - mainEdgeTransformedCentreImagePointBase[1])
							if debugmode:
								print(sign)
							if prevSign is None:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							elif sign<=0 and prevSign<=0 or sign>=0 and prevSign>=0:
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							else:
								currSegmentAngularDat.append([])
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI-1))
								currSegmentAngularDat[-1].append((None, segmentDatInd, coordI))
							if prevSign is None or sign!=0:
								prevSign=sign
							
						for tmpSegAngDat in currSegmentAngularDat:
							if len(tmpSegAngDat)>2:
								firstCoordDat = mainEdgeSegmentedDat[0][1-mainEdgeSeedPlane][tmpSegAngDat[0][1]][tmpSegAngDat[0][2]]
								secondCoordDat = mainEdgeSegmentedDat[0][1-mainEdgeSeedPlane][tmpSegAngDat[1][1]][tmpSegAngDat[1][2]]
								lastCoordDat = mainEdgeSegmentedDat[0][1-mainEdgeSeedPlane][tmpSegAngDat[-1][1]][tmpSegAngDat[-1][2]]
								startAng = math.atan2(firstCoordDat[1]-mainEdgeTransformedCentreImagePointBase[1], firstCoordDat[0]-mainEdgeTransformedCentreImagePointBase[0])
								secondAng = math.atan2(secondCoordDat[1]-mainEdgeTransformedCentreImagePointBase[1], secondCoordDat[0]-mainEdgeTransformedCentreImagePointBase[0]) # can only reliably tell direction using 1 line segment otherwise weird 360 stuff
								endAng = math.atan2(lastCoordDat[1]-mainEdgeTransformedCentreImagePointBase[1], lastCoordDat[0]-mainEdgeTransformedCentreImagePointBase[0])
								
								verydebug.append(firstCoordDat)
								verydebug.append(secondCoordDat)
								verydebug.append(mainEdgeTransformedCentreImagePointBase)
								
								clockwiseOrAnticlockwise=0
								tmpAng = secondAng-startAng
								if tmpAng<=-math.pi:
									tmpAng+=2*math.pi
								if tmpAng>math.pi:
									tmpAng-=2*math.pi
								if tmpAng<0:
									clockwiseOrAnticlockwise=1
								elif tmpAng>0:
									clockwiseOrAnticlockwise=-1
								else:
									pass
								if clockwiseOrAnticlockwise!=0: # just incase
									mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint.append([(startAng, endAng, clockwiseOrAnticlockwise), tmpSegAngDat])
					mainEdgeSegmentedDat[3][1-mainEdgeSeedPlane]=mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint
				
				overlapDat = []
				
				tmpRoughDistFromCentreImgPtToEdges = getDistance(mainEdgeTransformedCentreImagePoint[0], mainEdgeSeedCoord[0], mainEdgeTransformedCentreImagePoint[1], mainEdgeSeedCoord[1])
				
				overlapOccursOnSwappedOtherPlane=False
				for mainEdgeAngularDatInd, mainEdgeAngularDat in enumerate(mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint):
					for otherEdgeAngularDatInd, otherEdgeAngularDat in enumerate(otherEdgeFirstPlaneAngularDatFromMainEdgeImageCentrePoint):
						if otherEdgeAngularDat[0][2]==mainEdgeAngularDat[0][2]: # both segments/areas go in same direction
							
							tmpAngInt1=[]
							tmpAngInt2=[]
							overlapInt=[]
							
							if mainEdgeAngularDat[0][2]==1:
								tmpAngInt1=[otherEdgeAngularDat[0][1], otherEdgeAngularDat[0][0]]
								tmpAngInt2=[mainEdgeAngularDat[0][1], mainEdgeAngularDat[0][0]]
							elif mainEdgeAngularDat[0][2]==-1:
								tmpAngInt1=[otherEdgeAngularDat[0][0], otherEdgeAngularDat[0][1]]
								tmpAngInt2=[mainEdgeAngularDat[0][0], mainEdgeAngularDat[0][1]]
							
							if tmpAngInt1[0] <= tmpAngInt1[1]:
								if tmpAngInt2[0] <= tmpAngInt2[1]:
									overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
									overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
									if overlapStart<=overlapEnd:
										overlapInt=(overlapStart, overlapEnd)
									else:
										# no overlap
										pass
								else:
									if tmpAngInt1[1] >= tmpAngInt2[0]:
										overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
										overlapEnd = tmpAngInt1[1]
										overlapInt=(overlapStart, overlapEnd)
									elif tmpAngInt1[0] <= tmpAngInt2[1]:
										overlapStart = tmpAngInt1[0]
										overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
										overlapInt=(overlapStart, overlapEnd)
									else:
										# no overlap
										pass
									
							else:
								if tmpAngInt2[0] <= tmpAngInt2[1]:
									if tmpAngInt2[1] >= tmpAngInt1[0]:
										overlapStart = max(tmpAngInt2[0], tmpAngInt1[0])
										overlapEnd = tmpAngInt2[1]
										overlapInt=(overlapStart, overlapEnd)
									elif tmpAngInt2[0] <= tmpAngInt1[1]:
										overlapStart = tmpAngInt2[0]
										overlapEnd = min(tmpAngInt2[1], tmpAngInt1[1])
										overlapInt=(overlapStart, overlapEnd)
									else:
										# no overlap
										pass
									
								else:
									overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
									overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
									overlapInt=(overlapStart, overlapEnd)
							if len(overlapInt)==2 and otherEdgeAngularDat[0][2]==1:
								overlapInt=(overlapInt[1], overlapInt[0])
							
							if len(overlapInt)==2:
								
								tmpCrossingPt1 = (tmpRoughDistFromCentreImgPtToEdges, 0)
								tmpCrossingPt2 = (tmpRoughDistFromCentreImgPtToEdges, 0)
								
								tmpCrossingPt1 = (tmpCrossingPt1[0]*math.cos(overlapInt[0])-tmpCrossingPt1[1]*math.sin(overlapInt[0]), tmpCrossingPt1[0]*math.sin(overlapInt[0])+tmpCrossingPt1[1]*math.cos(overlapInt[0]))
								tmpCrossingPt2 = (tmpCrossingPt2[0]*math.cos(overlapInt[1])-tmpCrossingPt2[1]*math.sin(overlapInt[1]), tmpCrossingPt2[0]*math.sin(overlapInt[1])+tmpCrossingPt2[1]*math.cos(overlapInt[1]))
								
								tmpCrossingPt1 = (tmpCrossingPt1[0]+mainEdgeTransformedCentreImagePoint[0], tmpCrossingPt1[1]+mainEdgeTransformedCentreImagePoint[1])
								tmpCrossingPt2 = (tmpCrossingPt2[0]+mainEdgeTransformedCentreImagePoint[0], tmpCrossingPt2[1]+mainEdgeTransformedCentreImagePoint[1])
								
								TEMPDEBUG=True
								if TEMPDEBUG:
									debugMaxDistPossibleShouldBe = getDistance(stepCoordsMain[0][0][0], stepCoordsMain[-1][0][0], stepCoordsMain[0][0][1], stepCoordsMain[-1][0][1]) # roughly wing span
									debugDistFromSeedToCrossingPoint = getDistance(tmpCrossingPt1[0], mainEdgeSeedCoord[0], tmpCrossingPt1[1], mainEdgeSeedCoord[1])
									if debugDistFromSeedToCrossingPoint>debugMaxDistPossibleShouldBe:
										print("???? maybe angle need to rotate other direction, change rotation matrix to clockwise version 23822r3938hd")
										exit()
								
								crossingPt1IndBeforeMain=-1
								tmpFirstCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
								tmpFirstCoord = tmpFirstCoordDat
								prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
								maybeStartCrosses=False
								if abs(prevSign)<0.00001:
									maybeStartCrosses=True
								for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
									tmpCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
									tmpCoord = tmpCoordDat
									currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
									if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
										crossingPt1IndBeforeMain=tmpCoordDatI-1
										break
									prevSign=currSign
								if crossingPt1IndBeforeMain<0:
									if maybeStartCrosses:
										crossingPt1IndBeforeMain=0
									elif abs(prevSign)<0.00001:
										crossingPt1IndBeforeMain=len(mainEdgeAngularDat[1])-2
								
									
								crossingPt2IndBeforeMain=-1
								tmpFirstCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
								tmpFirstCoord = tmpFirstCoordDat
								prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
								maybeStartCrosses=False
								if abs(prevSign)<0.00001:
									maybeStartCrosses=True
								for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
									tmpCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
									tmpCoord = tmpCoordDat
									currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
									if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
										crossingPt2IndBeforeMain=tmpCoordDatI-1
										break
									prevSign=currSign
								if crossingPt2IndBeforeMain<0:
									if maybeStartCrosses:
										crossingPt2IndBeforeMain=0
									elif abs(prevSign)<0.00001:
										crossingPt2IndBeforeMain=len(mainEdgeAngularDat[1])-2
								
								
								# main pts
								
								crossingPt1IndBeforeOther=-1
								tmpFirstCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
								
								tmpFirstCoord = tmpFirstCoordDat
								prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
								maybeStartCrosses=False
								if abs(prevSign)<0.00001:
									maybeStartCrosses=True
								for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
									tmpCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
									tmpCoord = tmpCoordDat
									currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
									if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
										crossingPt1IndBeforeOther=tmpCoordDatI-1
										break
									prevSign=currSign
								if crossingPt1IndBeforeOther<0:
									if maybeStartCrosses:
										crossingPt1IndBeforeOther=0
									elif abs(prevSign)<0.00001:
										crossingPt1IndBeforeOther=len(otherEdgeAngularDat[1])-2
								
									
								crossingPt2IndBeforeOther=-1
								tmpFirstCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
								tmpFirstCoord = tmpFirstCoordDat
								prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
								maybeStartCrosses=False
								if abs(prevSign)<0.00001:
									maybeStartCrosses=True
								for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
									tmpCoordDat = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
									tmpCoord = tmpCoordDat
									currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
									if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
										crossingPt2IndBeforeOther=tmpCoordDatI-1
										break
									prevSign=currSign
								if crossingPt2IndBeforeOther<0:
									if maybeStartCrosses:
										crossingPt2IndBeforeOther=0
									elif abs(prevSign)<0.00001:
										crossingPt2IndBeforeOther=len(otherEdgeAngularDat[1])-2
								
								if crossingPt1IndBeforeMain>=0 and crossingPt2IndBeforeMain>=0 and crossingPt1IndBeforeOther>=0 and crossingPt2IndBeforeOther>=0:
									
									tmpReduceDupeCodeList = [] # put pairs of startPt and endPt and any vars used below that change in here then loop
									windowCentreImgPtToOverlapStartLineM = None
									windowCentreImgPtToOverlapStartLineC = None
									if tmpCrossingPt1[0]-mainEdgeTransformedCentreImagePoint[0]==0:
										windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[0]
										# pass
									else:
										windowCentreImgPtToOverlapStartLineM = (tmpCrossingPt1[1]-mainEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt1[0]-mainEdgeTransformedCentreImagePoint[0])
										windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[1]-windowCentreImgPtToOverlapStartLineM*tmpCrossingPt1[0]
									
									windowCentreImgPtToOverlapEndLineM = None
									windowCentreImgPtToOverlapEndLineC = None
									if tmpCrossingPt2[0]-mainEdgeTransformedCentreImagePoint[0]==0:
										windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[0]
										# pass
									else:
										windowCentreImgPtToOverlapEndLineM = (tmpCrossingPt2[1]-mainEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt2[0]-mainEdgeTransformedCentreImagePoint[0])
										windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[1]-windowCentreImgPtToOverlapEndLineM*tmpCrossingPt2[0]
									
									
									startPt1 = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][2]]
									endPt1 = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][2]]
									startPt2 = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][2]]
									endPt2 = otherEdgePlanesSegments[otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][2]]
									startPt3 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][2]]
									endPt3 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][2]]
									startPt4 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][2]]
									endPt4 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][2]]
									
									# startPt, endPt, windowLineM, windowLineC, indBefore
									tmpReduceDupeCodeList.append((startPt1, endPt1, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeOther))
									tmpReduceDupeCodeList.append((startPt2, endPt2, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeOther))
									tmpReduceDupeCodeList.append((startPt3, endPt3, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeMain))
									tmpReduceDupeCodeList.append((startPt4, endPt4, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeMain))
									
									indexAsRatios = []
									for tmpVars in tmpReduceDupeCodeList:
										startPt, endPt, tmpLineM, tmpLineC, indBefore = tmpVars
										if tmpLineM is None:
											if endPt[0]-startPt[0]!=0:
												tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
												if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
													tempT=0
												if tempT>1:
													tempT=1
												indexAsRatios.append(indBefore+tempT)
										elif tmpLineM == 0:
											if endPt[1]-startPt[1]!=0:
												tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
												if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
													tempT=0
												if tempT>1:
													tempT=1
												indexAsRatios.append(indBefore+tempT)
										else:
											tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
											if tmpDiv!=0:
												tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
												if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
													tempT=0
												if tempT>1:
													tempT=1
												indexAsRatios.append(indBefore+tempT)
												
									if len(indexAsRatios)==4:
										overlapDat.append(( abs(indexAsRatios[1]-indexAsRatios[0]), (otherEdgeAngularDatInd, indexAsRatios[0], indexAsRatios[1]), (mainEdgeAngularDatInd, indexAsRatios[2], indexAsRatios[3]), overlapOccursOnSwappedOtherPlane	 ))
				
				if True:
					overlapOccursOnSwappedOtherPlane = True
					for mainEdgeAngularDatInd, mainEdgeAngularDat in enumerate(mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint):
						for otherEdgeAngularDatInd, otherEdgeAngularDat in enumerate(otherEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint):
							if otherEdgeAngularDat[0][2]==mainEdgeAngularDat[0][2]: # both segments/areas go in same direction
								
								tmpAngInt1=[]
								tmpAngInt2=[]
								overlapInt=[]
								
								if mainEdgeAngularDat[0][2]==1:
									tmpAngInt1=[otherEdgeAngularDat[0][1], otherEdgeAngularDat[0][0]]
									tmpAngInt2=[mainEdgeAngularDat[0][1], mainEdgeAngularDat[0][0]]
								elif mainEdgeAngularDat[0][2]==-1:
									tmpAngInt1=[otherEdgeAngularDat[0][0], otherEdgeAngularDat[0][1]]
									tmpAngInt2=[mainEdgeAngularDat[0][0], mainEdgeAngularDat[0][1]]
								
								if tmpAngInt1[0] <= tmpAngInt1[1]:
									if tmpAngInt2[0] <= tmpAngInt2[1]:
										overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
										overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
										if overlapStart<=overlapEnd:
											overlapInt=(overlapStart, overlapEnd)
										else:
											# no overlap
											pass
									else:
										if tmpAngInt1[1] >= tmpAngInt2[0]:
											overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
											overlapEnd = tmpAngInt1[1]
											overlapInt=(overlapStart, overlapEnd)
										elif tmpAngInt1[0] <= tmpAngInt2[1]:
											overlapStart = tmpAngInt1[0]
											overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
											overlapInt=(overlapStart, overlapEnd)
										else:
											# no overlap
											pass
										
								else:
									if tmpAngInt2[0] <= tmpAngInt2[1]:
										if tmpAngInt2[1] >= tmpAngInt1[0]:
											overlapStart = max(tmpAngInt2[0], tmpAngInt1[0])
											overlapEnd = tmpAngInt2[1]
											overlapInt=(overlapStart, overlapEnd)
										elif tmpAngInt2[0] <= tmpAngInt1[1]:
											overlapStart = tmpAngInt2[0]
											overlapEnd = min(tmpAngInt2[1], tmpAngInt1[1])
											overlapInt=(overlapStart, overlapEnd)
										else:
											# no overlap
											pass
										
									else:
										overlapStart = max(tmpAngInt1[0], tmpAngInt2[0])
										overlapEnd = min(tmpAngInt1[1], tmpAngInt2[1])
										overlapInt=(overlapStart, overlapEnd)
								if len(overlapInt)==2 and otherEdgeAngularDat[0][2]==1:
									overlapInt=(overlapInt[1], overlapInt[0])
								
								if len(overlapInt)==2:
									
									tmpCrossingPt1 = (tmpRoughDistFromCentreImgPtToEdges, 0)
									tmpCrossingPt2 = (tmpRoughDistFromCentreImgPtToEdges, 0)
									
									tmpCrossingPt1 = (tmpCrossingPt1[0]*math.cos(overlapInt[0])-tmpCrossingPt1[1]*math.sin(overlapInt[0]), tmpCrossingPt1[0]*math.sin(overlapInt[0])+tmpCrossingPt1[1]*math.cos(overlapInt[0]))
									tmpCrossingPt2 = (tmpCrossingPt2[0]*math.cos(overlapInt[1])-tmpCrossingPt2[1]*math.sin(overlapInt[1]), tmpCrossingPt2[0]*math.sin(overlapInt[1])+tmpCrossingPt2[1]*math.cos(overlapInt[1]))
									
									tmpCrossingPt1 = (tmpCrossingPt1[0]+mainEdgeTransformedCentreImagePoint[0], tmpCrossingPt1[1]+mainEdgeTransformedCentreImagePoint[1])
									tmpCrossingPt2 = (tmpCrossingPt2[0]+mainEdgeTransformedCentreImagePoint[0], tmpCrossingPt2[1]+mainEdgeTransformedCentreImagePoint[1])
									
									crossingPt1IndBeforeMain=-1
									tmpFirstCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
									tmpFirstCoord = tmpFirstCoordDat
									prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
									maybeStartCrosses=False
									if abs(prevSign)<0.00001:
										maybeStartCrosses=True
									for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
										tmpCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
										tmpCoord = tmpCoordDat
										currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
										if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
											crossingPt1IndBeforeMain=tmpCoordDatI-1
											break
										prevSign=currSign
									if crossingPt1IndBeforeMain<0:
										if maybeStartCrosses:
											crossingPt1IndBeforeMain=0
										elif abs(prevSign)<0.00001:
											crossingPt1IndBeforeMain=len(mainEdgeAngularDat[1])-2
									
										
									crossingPt2IndBeforeMain=-1
									tmpFirstCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][0][1]][mainEdgeAngularDat[1][0][2]]
									tmpFirstCoord = tmpFirstCoordDat
									prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
									maybeStartCrosses=False
									if abs(prevSign)<0.00001:
										maybeStartCrosses=True
									for tmpCoordDatI in range(1, len(mainEdgeAngularDat[1])):
										tmpCoordDat = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][tmpCoordDatI][1]][mainEdgeAngularDat[1][tmpCoordDatI][2]]
										tmpCoord = tmpCoordDat
										currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
										if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
											crossingPt2IndBeforeMain=tmpCoordDatI-1
											break
										prevSign=currSign
									if crossingPt2IndBeforeMain<0:
										if maybeStartCrosses:
											crossingPt2IndBeforeMain=0
										elif abs(prevSign)<0.00001:
											crossingPt2IndBeforeMain=len(mainEdgeAngularDat[1])-2
									
									crossingPt1IndBeforeOther=-1
									tmpFirstCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
									tmpFirstCoord = tmpFirstCoordDat
									prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
									maybeStartCrosses=False
									if abs(prevSign)<0.00001:
										maybeStartCrosses=True
									for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
										tmpCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
										tmpCoord = tmpCoordDat
										currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt1[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt1[1] - mainEdgeTransformedCentreImagePoint[1])
										if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
											crossingPt1IndBeforeOther=tmpCoordDatI-1
											break
										prevSign=currSign
									if crossingPt1IndBeforeOther<0:
										if maybeStartCrosses:
											crossingPt1IndBeforeOther=0
										elif abs(prevSign)<0.00001:
											crossingPt1IndBeforeOther=len(otherEdgeAngularDat[1])-2
									
									crossingPt2IndBeforeOther=-1
									tmpFirstCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][0][1]][otherEdgeAngularDat[1][0][2]]
									tmpFirstCoord = tmpFirstCoordDat
									prevSign = (tmpFirstCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpFirstCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
									maybeStartCrosses=False
									if abs(prevSign)<0.00001:
										maybeStartCrosses=True
									for tmpCoordDatI in range(1, len(otherEdgeAngularDat[1])):
										tmpCoordDat = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][tmpCoordDatI][1]][otherEdgeAngularDat[1][tmpCoordDatI][2]]
										tmpCoord = tmpCoordDat
										currSign = (tmpCoord[1] - mainEdgeTransformedCentreImagePoint[1])*(tmpCrossingPt2[0] - mainEdgeTransformedCentreImagePoint[0]) - (tmpCoord[0] - mainEdgeTransformedCentreImagePoint[0])*(tmpCrossingPt2[1] - mainEdgeTransformedCentreImagePoint[1])
										if prevSign<=0 and currSign>=0 or prevSign>=0 and currSign<=0:
											crossingPt2IndBeforeOther=tmpCoordDatI-1
											break
										prevSign=currSign
									if crossingPt2IndBeforeOther<0:
										if maybeStartCrosses:
											crossingPt2IndBeforeOther=0
										elif abs(prevSign)<0.00001:
											crossingPt2IndBeforeOther=len(otherEdgeAngularDat[1])-2
									
									if crossingPt1IndBeforeMain>=0 and crossingPt2IndBeforeMain>=0 and crossingPt1IndBeforeOther>=0 and crossingPt2IndBeforeOther>=0:
										
										tmpReduceDupeCodeList = [] # put pairs of startPt and endPt and any vars used below that change in here then loop
										windowCentreImgPtToOverlapStartLineM = None
										windowCentreImgPtToOverlapStartLineC = None
										if tmpCrossingPt1[0]-mainEdgeTransformedCentreImagePoint[0]==0:
											windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[0]
											# pass
										else:
											windowCentreImgPtToOverlapStartLineM = (tmpCrossingPt1[1]-mainEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt1[0]-mainEdgeTransformedCentreImagePoint[0])
											windowCentreImgPtToOverlapStartLineC = tmpCrossingPt1[1]-windowCentreImgPtToOverlapStartLineM*tmpCrossingPt1[0]
										
										windowCentreImgPtToOverlapEndLineM = None
										windowCentreImgPtToOverlapEndLineC = None
										if tmpCrossingPt2[0]-mainEdgeTransformedCentreImagePoint[0]==0:
											windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[0]
											# pass
										else:
											windowCentreImgPtToOverlapEndLineM = (tmpCrossingPt2[1]-mainEdgeTransformedCentreImagePoint[1])/(tmpCrossingPt2[0]-mainEdgeTransformedCentreImagePoint[0])
											windowCentreImgPtToOverlapEndLineC = tmpCrossingPt2[1]-windowCentreImgPtToOverlapEndLineM*tmpCrossingPt2[0]
										
										startPt1 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther][2]]
										endPt1 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt1IndBeforeOther+1][2]]
										startPt2 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther][2]]
										endPt2 = otherEdgePlanesSegments[1-otherEdgeSeedPlane][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][1]][otherEdgeAngularDat[1][crossingPt2IndBeforeOther+1][2]]
										startPt3 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain][2]]
										endPt3 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt1IndBeforeMain+1][2]]
										startPt4 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain][2]]
										endPt4 = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][1]][mainEdgeAngularDat[1][crossingPt2IndBeforeMain+1][2]]
										
										# startPt, endPt, windowLineM, windowLineC, indBefore
										tmpReduceDupeCodeList.append((startPt1, endPt1, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeOther))
										tmpReduceDupeCodeList.append((startPt2, endPt2, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeOther))
										tmpReduceDupeCodeList.append((startPt3, endPt3, windowCentreImgPtToOverlapStartLineM, windowCentreImgPtToOverlapStartLineC, crossingPt1IndBeforeMain))
										tmpReduceDupeCodeList.append((startPt4, endPt4, windowCentreImgPtToOverlapEndLineM, windowCentreImgPtToOverlapEndLineC, crossingPt2IndBeforeMain))
										
										indexAsRatios = []
										for tmpVars in tmpReduceDupeCodeList:
											startPt, endPt, tmpLineM, tmpLineC, indBefore = tmpVars
											if tmpLineM is None:
												if endPt[0]-startPt[0]!=0:
													tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
													if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
														tempT=0
													if tempT>1:
														tempT=1
													indexAsRatios.append(indBefore+tempT)
											elif tmpLineM == 0:
												if endPt[1]-startPt[1]!=0:
													tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
													if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
														tempT=0
													if tempT>1:
														tempT=1
													indexAsRatios.append(indBefore+tempT)
											else:
												tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
												if tmpDiv!=0:
													tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
													if tempT<0: # i know they intersect but small error could put on wrong side of lineSeg endings so just fixing
														tempT=0
													if tempT>1:
														tempT=1
													indexAsRatios.append(indBefore+tempT)
													
										if len(indexAsRatios)==4:
											overlapDat.append(( abs(indexAsRatios[1]-indexAsRatios[0]), (otherEdgeAngularDatInd, indexAsRatios[0], indexAsRatios[1]), (mainEdgeAngularDatInd, indexAsRatios[2], indexAsRatios[3]), overlapOccursOnSwappedOtherPlane	 ))
				
				overlapDat.sort(reverse=True)
				
				if "baseTangents" not in mainEdgeSegmentedDat[3]:
					tempBaseTangents=[]
					for planeInd, planeDat in enumerate(mainEdgeSegmentedDat[0]):
						tempBaseTangents.append([])
						for segmentDat in planeDat:
							tmpSegmentTangentDat = [None] # first and last item is None cause use 3 consecutive pts per tangent calc, one on each side of the point, so cant do first and last
							for i in range(1, len(segmentDat)-1):
								tmpOrientation=math.atan2(segmentDat[i+1][1]-segmentDat[i-1][1], segmentDat[i+1][0]-segmentDat[i-1][0])
								tmpSegmentTangentDat.append(tmpOrientation)
							tmpSegmentTangentDat.append(None)
							tempBaseTangents[planeInd].append(tmpSegmentTangentDat)
					mainEdgeSegmentedDat[3]["baseTangents"]=tempBaseTangents
				if "baseTangentsWRTcentreImgPoint" not in mainEdgeSegmentedDat[3]:
					baseTangentDat = mainEdgeSegmentedDat[3]["baseTangents"]
					tempBaseTangentsWRTcentreImgPointDat = []
					for planeInd, planeDat in enumerate(mainEdgeSegmentedDat[0]):
						tempBaseTangentsWRTcentreImgPointDat.append([])
						for segmentDatInd, segmentDat in enumerate(planeDat):
							tmpSegWRTCenteImgPtDat = [None]
							for i in range(1, len(segmentDat)-1):
								estTangentAtPointOrientation = baseTangentDat[planeInd][segmentDatInd][i]
								tangentPoint = mainEdgeSegmentedDat[0][planeInd][segmentDatInd][i]
								tmpLineOrientation = math.atan2(tangentPoint[1]-mainEdgeTransformedCentreImagePointBase[1], tangentPoint[0]-mainEdgeTransformedCentreImagePointBase[0])
								orientationDifference = estTangentAtPointOrientation-tmpLineOrientation
								if orientationDifference<math.pi:
									orientationDifference+=2*math.pi
								if orientationDifference>math.pi:
									orientationDifference-=2*math.pi
								
								if orientationDifference<0:
									tmpDiffFromPerpendicular = -90*math.pi/180 - orientationDifference
									tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
									if True: # 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
										tmpSegWRTCenteImgPtDat.append(90*math.pi/180-tmpDiffFromPerpendicular) # so convoluted but exhausted, im now storing angle away from straight line with values 0<=X<=90 (in radians)
									
								else:
									tmpDiffFromPerpendicular = 90*math.pi/180 - orientationDifference
									tmpDiffFromPerpendicular = abs(tmpDiffFromPerpendicular)
									if True: # 90*math.pi/180-tmpDiffFromPerpendicular>=hardMinimumPerpendicularity:
										tmpSegWRTCenteImgPtDat.append(90*math.pi/180-tmpDiffFromPerpendicular)
									
							tmpSegWRTCenteImgPtDat.append(None)
							tempBaseTangentsWRTcentreImgPointDat[planeInd].append(tmpSegWRTCenteImgPtDat)
					mainEdgeSegmentedDat[3]["baseTangentsWRTcentreImgPoint"]=tempBaseTangentsWRTcentreImgPointDat
				
				baseTangentsWRTcentreImgPointDat = mainEdgeSegmentedDat[3]["baseTangentsWRTcentreImgPoint"]
				
				overlapDatPerpendicularity = []
				
				for tmpOverlapDatInd, tmpOverlapDat in enumerate(overlapDat):
					
					mostPerpendicularPointSegmentDatInd = None
					mostPerpendicularPointCoordDatInd = None
					mostPerpendicularPointPerpendicularity = None
					earlyBreakBecauseGoodEnoughFound = False
					mostPerpendicularPointOverlapDatInd = None
					
					overlapOccursOnSwappedOtherPlane = tmpOverlapDat[3]
					otherEdgeAngularDatInd, otherIndAsRatio1, otherIndAsRatio2 = tmpOverlapDat[1]
					mainEdgeAngularDatInd, mainIndAsRatio1, mainIndAsRatio2 = tmpOverlapDat[2]
					
					earlyBreakBecauseGoodEnoughFound = False
					
					if math.floor(mainIndAsRatio1) != math.floor(mainIndAsRatio2): # need at least 1 index integer between them (i.e. 1 coordDat)
						
						consecutivePerpendicularEnoughCtr = 0
						
						startInd = mainIndAsRatio1
						endInd = mainIndAsRatio2
						if startInd>endInd:
							startInd, endInd = endInd, startInd
						startInd = math.ceil(startInd)
						endInd = math.floor(endInd)
						
						### DEBUG
						prevSegmentDatInd = None
						
						for tmpInd in range(startInd, endInd+1):
							
							junk, tmpSegmentDatInd, tmpCoordInd = mainEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint[mainEdgeAngularDatInd][1][tmpInd]
							
							tangentPerpendicularityOfPoint = baseTangentsWRTcentreImgPointDat[1-mainEdgeSeedPlane][tmpSegmentDatInd][tmpCoordInd] # if point has one before and after then this will usually be the angle of how different the tangent at the point is compared to line from centre img pt of other edge to the point
							if tangentPerpendicularityOfPoint is not None: # e.g. if tangent at point intersects with line from otherEdge centre img pt at a right angle, this will be 90 degrees in radians
								
								if mostPerpendicularPointPerpendicularity is None or tangentPerpendicularityOfPoint>mostPerpendicularPointPerpendicularity:
									mostPerpendicularPointPerpendicularity=tangentPerpendicularityOfPoint
									mostPerpendicularPointSegmentDatInd=tmpSegmentDatInd
									mostPerpendicularPointCoordDatInd=tmpCoordInd
									mostPerpendicularPointOverlapDatInd=tmpOverlapDatInd
								
								if tangentPerpendicularityOfPoint<hardMinimumPerpendicularity:
									consecutivePerpendicularEnoughCtr=0
								else:
									consecutivePerpendicularEnoughCtr+=1
								if consecutivePerpendicularEnoughCtr>=3:
									mostPerpendicularPointPerpendicularity=tangentPerpendicularityOfPoint
									mostPerpendicularPointSegmentDatInd=tmpSegmentDatInd
									mostPerpendicularPointCoordDatInd=tmpCoordInd-1
									mostPerpendicularPointOverlapDatInd=tmpOverlapDatInd
									
									#### DEBUG
									if tmpSegmentDatInd!=prevSegmentDatInd:
										print("huh????? ijdeo12hid")
										exit()
									
									earlyBreakBecauseGoodEnoughFound=True
									break
							else:
								consecutivePerpendicularEnoughCtr=0
							prevSegmentDatInd=tmpSegmentDatInd
					
					if mostPerpendicularPointPerpendicularity is not None:
						overlapDatPerpendicularity.append((mostPerpendicularPointPerpendicularity, mostPerpendicularPointSegmentDatInd, mostPerpendicularPointCoordDatInd, mostPerpendicularPointOverlapDatInd))
				
				if len(overlapDatPerpendicularity)>0 or secondMainPlaneHasPoints==False or lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']: # we have the most perpendicular point, might be bad/not perpendicular at all and high error etc but just continue to scale the plane
					
					overlapDatPerpendicularity.sort(reverse=True)
					actualOtherEdgeIntersectionPoint = None
					actualMostPerpendicularMainEdgeCoordInOverlap=None
					
					for overlapDatPerpendicularityDat in overlapDatPerpendicularity:
						
						mostPerpendicularPointPerpendicularity, mostPerpendicularPointSegmentDatInd, mostPerpendicularPointCoordDatInd, mostPerpendicularPointOverlapDatInd = overlapDatPerpendicularityDat
						
						overlapOccursOnSwappedOtherPlane = overlapDat[mostPerpendicularPointOverlapDatInd][3]
						
						currAngularDatFromMainEdgeImageCentrePoint=None
						currOtherPlane=None
						
						if overlapOccursOnSwappedOtherPlane:
							currAngularDatFromMainEdgeImageCentrePoint = otherEdgeSwappedPlaneAngularDatFromMainEdgeImageCentrePoint
							currOtherPlane = 1-otherEdgeSeedPlane
						else:
							currAngularDatFromMainEdgeImageCentrePoint = otherEdgeFirstPlaneAngularDatFromMainEdgeImageCentrePoint
							currOtherPlane = otherEdgeSeedPlane
						
						otherEdgeAngularDatInd, otherIndAsRatio1, otherIndAsRatio2 = overlapDat[mostPerpendicularPointOverlapDatInd][1]
						startInd = otherIndAsRatio1
						endInd = otherIndAsRatio2
						if startInd>endInd:
							startInd, endInd = endInd, startInd
						
						mostPerpendicularMainEdgeCoordInOverlap = mainEdgePlanesSegments[1-mainEdgeSeedPlane][mostPerpendicularPointSegmentDatInd][mostPerpendicularPointCoordDatInd]
						mainEdgePointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsMain[1-mainEdgeSeedPlane][mostPerpendicularPointSegmentDatInd][mostPerpendicularPointCoordDatInd]
						
						otherEdgeIntersectionPoint = None
						otherEdgeIntersectionPointStepCoordIndBefore = None
						
						tmpLineM = None
						tmpLineC = None
						if mostPerpendicularMainEdgeCoordInOverlap[0]-mainEdgeTransformedCentreImagePoint[0]!=0:
							tmpLineM = (mostPerpendicularMainEdgeCoordInOverlap[1]-mainEdgeTransformedCentreImagePoint[1])/(mostPerpendicularMainEdgeCoordInOverlap[0]-mainEdgeTransformedCentreImagePoint[0])
							tmpLineC = mostPerpendicularMainEdgeCoordInOverlap[1]-tmpLineM*mostPerpendicularMainEdgeCoordInOverlap[0]
						else:
							tmpLineC = mostPerpendicularMainEdgeCoordInOverlap[0]
						
						if math.floor(startInd)==math.floor(endInd):
							startPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(startInd)][1]
							startPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(startInd)][2]
							endPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(endInd)][1]
							endPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(endInd)][2]
							startPt = otherEdgePlanesSegments[currOtherPlane][startPtSegInd][startPtCoordInd]
							endPt = otherEdgePlanesSegments[currOtherPlane][endPtSegInd][endPtCoordInd]
							lineRatioStart = startInd-math.floor(startInd)
							lineRatioEnd = endInd-math.floor(endInd)
							##
							if tmpLineM is None:
								if endPt[0]-startPt[0]!=0:
									tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
									
									tmpIntersectionRatio = None
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
									elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
										tmpIntersectionRatio=lineRatioStart
									else:
										tmpIntersectionRatio=lineRatioEnd
									tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
									otherEdgeIntersectionPoint = [tmpLineC, tempY]
									otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
									
							elif tmpLineM == 0:
								if endPt[1]-startPt[1]!=0:
									tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
									
									tmpIntersectionRatio = None
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
									elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
										tmpIntersectionRatio=lineRatioStart
									else:
										tmpIntersectionRatio=lineRatioEnd
									tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
									otherEdgeIntersectionPoint = [tempX, tmpLineC]
									otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
							else:
								tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
								if tmpDiv!=0:
									tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
									
									tmpIntersectionRatio = None
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
									elif abs(lineRatioStart-tempT)<abs(lineRatioEnd-tempT): # unless something crazy happened, slight float error means the intersection happens JUST outside of the actual overlap
										tmpIntersectionRatio=lineRatioStart
									else:
										tmpIntersectionRatio=lineRatioEnd
									tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
									tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
									otherEdgeIntersectionPoint = [tempX, tempY]
									otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
							
						else:
							beforeRatioStart = None
							coordIfBeforeRatioStart = None
							afterRatioEnd = None
							coordIfAfterRatioEnd = None
							startPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(startInd)][1]
							startPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(startInd)][2]
							endPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(startInd)][1]
							endPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(startInd)][2]
							
							startPt = otherEdgePlanesSegments[currOtherPlane][startPtSegInd][startPtCoordInd]
							endPt = otherEdgePlanesSegments[currOtherPlane][endPtSegInd][endPtCoordInd]
							
							otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = None
							otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = None
							
							lineRatioStart = startInd-math.floor(startInd)
							lineRatioEnd = 1
							
							if tmpLineM is None:
								if endPt[0]-startPt[0]!=0:
									tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
									
									tmpIntersectionRatio = None
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
										tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
										otherEdgeIntersectionPoint = [tmpLineC, tempY]
										otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
									elif tempT<lineRatioStart: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
										beforeRatioStart=lineRatioStart-tempT
										
										tmpIntersectionRatio=lineRatioStart
										tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
										coordIfBeforeRatioStart = [tmpLineC, tempY]
										otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
							elif tmpLineM == 0:
								if endPt[1]-startPt[1]!=0:
									tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
									
									tmpIntersectionRatio = None
									
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
										tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
										otherEdgeIntersectionPoint = [tempX, tmpLineC]
										otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
									elif tempT<lineRatioStart: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
										beforeRatioStart=lineRatioStart-tempT
										
										tmpIntersectionRatio=lineRatioStart
										tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
										coordIfBeforeRatioStart = [tempX, tmpLineC]
										otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
									
							else:
								tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
								if tmpDiv!=0:
									tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
									
									tmpIntersectionRatio = None
									if tempT>=lineRatioStart and tempT<=lineRatioEnd:
										tmpIntersectionRatio=tempT
										tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
										tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
										otherEdgeIntersectionPoint = [tempX, tempY]
										otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
									elif tempT<lineRatioStart:
										beforeRatioStart=lineRatioStart-tempT
										tmpIntersectionRatio=lineRatioStart
										tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
										tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
										coordIfBeforeRatioStart = [tempX, tempY]
										otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
									
							######### last ind to last ind ratio
							if otherEdgeIntersectionPoint is None:
								
								startPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(endInd)][1]
								startPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.floor(endInd)][2]
								endPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(endInd)][1]
								endPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][math.ceil(endInd)][2]
								
								startPt = otherEdgePlanesSegments[currOtherPlane][startPtSegInd][startPtCoordInd]
								endPt = otherEdgePlanesSegments[currOtherPlane][endPtSegInd][endPtCoordInd]
								
								lineRatioStart = 0
								lineRatioEnd = endInd-math.floor(endInd)
								
								if tmpLineM is None:
									if endPt[0]-startPt[0]!=0:
										tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
										
										tmpIntersectionRatio = None
										if tempT>=lineRatioStart and tempT<=lineRatioEnd:
											tmpIntersectionRatio=tempT
											tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
											otherEdgeIntersectionPoint = [tmpLineC, tempY]
											otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
											
										elif tempT>lineRatioEnd: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
											afterRatioEnd=tempT-lineRatioEnd
											
											tmpIntersectionRatio=lineRatioEnd
											tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
											coordIfAfterRatioEnd = [tmpLineC, tempY]
											otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
								elif tmpLineM == 0:
									if endPt[1]-startPt[1]!=0:
										tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
										
										tmpIntersectionRatio = None
										
										if tempT>=lineRatioStart and tempT<=lineRatioEnd:
											tmpIntersectionRatio=tempT
											tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
											otherEdgeIntersectionPoint = [tempX, tmpLineC]
											otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
											
										elif tempT>lineRatioEnd: # if its after then i dont care cause if its after 1 i.e. tempT > 1, then it intersects later
											afterRatioEnd=tempT-lineRatioEnd
											
											tmpIntersectionRatio=lineRatioEnd
											tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
											coordIfAfterRatioEnd = [tempX, tmpLineC]
											otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
								else:
									tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
									if tmpDiv!=0:
										tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
										
										tmpIntersectionRatio = None
										if tempT>=lineRatioStart and tempT<=lineRatioEnd:
											tmpIntersectionRatio=tempT
											tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
											tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
											otherEdgeIntersectionPoint = [tempX, tempY]
											otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
											
										elif tempT>lineRatioEnd:
											afterRatioEnd=tempT-lineRatioEnd
											tmpIntersectionRatio=lineRatioEnd
											tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
											tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
											coordIfAfterRatioEnd = [tempX, tempY]
											otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
										
							######### all inds between
							
							if otherEdgeIntersectionPoint is None:
								for tmpInd in range(math.ceil(startInd), math.floor(endInd)):
									
									startPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][tmpInd][1]
									startPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][tmpInd][2]
									endPtSegInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][tmpInd+1][1]
									endPtCoordInd = currAngularDatFromMainEdgeImageCentrePoint[otherEdgeAngularDatInd][1][tmpInd+1][2]
									
									startPt = otherEdgePlanesSegments[currOtherPlane][startPtSegInd][startPtCoordInd]
									endPt = otherEdgePlanesSegments[currOtherPlane][endPtSegInd][endPtCoordInd]
									
									if tmpLineM is None:
										if endPt[0]-startPt[0]!=0:
											tempT = (tmpLineC-startPt[0])/(endPt[0]-startPt[0])
											
											tmpIntersectionRatio = None
											if tempT>=0 and tempT<=1:
												tmpIntersectionRatio=tempT
												tempY = startPt[1] + (endPt[1]-startPt[1])*tmpIntersectionRatio
												otherEdgeIntersectionPoint = [tmpLineC, tempY]
												otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
											
									elif tmpLineM == 0:
										if endPt[1]-startPt[1]!=0:
											tempT = (tmpLineC-startPt[1])/(endPt[1]-startPt[1])
											
											tmpIntersectionRatio = None
											
											if tempT>=0 and tempT<=1:
												tmpIntersectionRatio=tempT
												tempX = startPt[0] + (endPt[0]-startPt[0])*tmpIntersectionRatio
												otherEdgeIntersectionPoint = [tempX, tmpLineC]
												otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
											
									else:
										tmpDiv = (endPt[1]-startPt[1]-tmpLineM*(endPt[0]-startPt[0]))
										if tmpDiv!=0:
											tempT = (tmpLineM*startPt[0]+tmpLineC-startPt[1])/tmpDiv
											
											tmpIntersectionRatio = None
											if tempT>=0 and tempT<=1:
												tmpIntersectionRatio=tempT
												tempX = startPt[0]+(endPt[0]-startPt[0])*tmpIntersectionRatio
												tempY = startPt[1]+(endPt[1]-startPt[1])*tmpIntersectionRatio
												otherEdgeIntersectionPoint = [tempX, tempY]
												otherEdgeIntersectionPointStepCoordIndBefore = stepCoordIndsBeforePlanesSegmentsCoordsOther[currOtherPlane][startPtSegInd][startPtCoordInd]
												
							if otherEdgeIntersectionPoint is None:
								if beforeRatioStart is not None and afterRatioEnd is not None:
									if beforeRatioStart<afterRatioEnd:
										otherEdgeIntersectionPoint=coordIfBeforeRatioStart
										otherEdgeIntersectionPointStepCoordIndBefore = otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart
									else:
										otherEdgeIntersectionPoint=coordIfAfterRatioEnd
										otherEdgeIntersectionPointStepCoordIndBefore = otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd
								elif beforeRatioStart is not None:
									otherEdgeIntersectionPoint=coordIfBeforeRatioStart
									otherEdgeIntersectionPointStepCoordIndBefore = otherEdgeIntersectionPointStepCoordIndBeforeIfBeforeRatioStart
								elif afterRatioEnd is not None:
									otherEdgeIntersectionPoint=coordIfAfterRatioEnd
									otherEdgeIntersectionPointStepCoordIndBefore = otherEdgeIntersectionPointStepCoordIndBeforeIfAfterRatioEnd
						
						estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInOtherEdgeSpace = None
						
						idkFailure2=False
						if stepCoordIndBeforeMainSeed<mainEdgePointStepCoordIndBefore:
							tmpAmountAway=mainEdgePointStepCoordIndBefore-stepCoordIndBeforeMainSeed
							tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError)
							tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
							
							tmpInterval = [stepCoordIndBeforeOtherSeed+tmpAmountAwayLower, stepCoordIndBeforeOtherSeed+tmpAmountAwayUpper]
							
							tmpInterval[0]=max(tmpInterval[0], stepCoordIndBeforeOtherSeed+1)
							tmpInterval[1]=min(tmpInterval[1], len(stepCoordsOther)-1)
							if tmpInterval[0]>=tmpInterval[1]:
								idkFailure2=True
							estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInOtherEdgeSpace=tmpInterval
							
						elif stepCoordIndBeforeMainSeed>mainEdgePointStepCoordIndBefore:
							tmpAmountAway=stepCoordIndBeforeMainSeed-mainEdgePointStepCoordIndBefore
							tmpAmountAwayLower=math.floor(tmpAmountAway*(1-arcLengthError)-flatStepCoordsError) # lower/upper here is gonna be used reversed from intuition cause its lower/upper w.r.t. outwards from seed point
							tmpAmountAwayUpper=math.ceil(tmpAmountAway*(1+arcLengthError)+flatStepCoordsError)
							
							tmpInterval = [stepCoordIndBeforeOtherSeed-tmpAmountAwayUpper, stepCoordIndBeforeOtherSeed-tmpAmountAwayLower]
							
							tmpInterval[0]=max(tmpInterval[0], 0)
							tmpInterval[1]=min(tmpInterval[1], stepCoordIndBeforeOtherSeed-1)
							if tmpInterval[0]>=tmpInterval[1]:
								idkFailure2=True
							estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInOtherEdgeSpace=tmpInterval
						else:
							idkFailure2=True
						if not(idkFailure2):
							if otherEdgeIntersectionPointStepCoordIndBefore is not None and otherEdgeIntersectionPointStepCoordIndBefore >= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInOtherEdgeSpace[0] and otherEdgeIntersectionPointStepCoordIndBefore <= estimatedIntervalStepCoordIndBeforeMostPerpendicularPointInAreaInOtherEdgeSpace[1]:
								actualOtherEdgeIntersectionPoint = otherEdgeIntersectionPoint
								actualMostPerpendicularMainEdgeCoordInOverlap = mostPerpendicularMainEdgeCoordInOverlap
								break
					
					if actualOtherEdgeIntersectionPoint is not None or secondMainPlaneHasPoints==False or lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']:
						
						if actualOtherEdgeIntersectionPoint is not None:
							otherEdgeIntersectionPoint = actualOtherEdgeIntersectionPoint
							mostPerpendicularMainEdgeCoordInOverlap = actualMostPerpendicularMainEdgeCoordInOverlap
							
							distToOtherEdgePt = getDistance(otherEdgeIntersectionPoint[0], mainEdgeTransformedCentreImagePoint[0], otherEdgeIntersectionPoint[1], mainEdgeTransformedCentreImagePoint[1])
							distToMainEdgePt = getDistance(mostPerpendicularMainEdgeCoordInOverlap[0], mainEdgeTransformedCentreImagePoint[0], mostPerpendicularMainEdgeCoordInOverlap[1], mainEdgeTransformedCentreImagePoint[1])
							scaleMainEdgeSwappedPlaneBy = distToOtherEdgePt/distToMainEdgePt
							##
							for segmentDat in mainEdgePlanesSegments[1-mainEdgeSeedPlane]:
								for coordDat in segmentDat:
									coordX = coordDat[0] - mainEdgeTransformedCentreImagePoint[0]
									coordX = coordX*scaleMainEdgeSwappedPlaneBy
									coordX = coordX + mainEdgeTransformedCentreImagePoint[0]
									
									coordY = coordDat[1] - mainEdgeTransformedCentreImagePoint[1]
									coordY = coordY*scaleMainEdgeSwappedPlaneBy
									coordY = coordY + mainEdgeTransformedCentreImagePoint[1]
									
									coordDat[0]=coordX
									coordDat[1]=coordY
						
						
						tmpt4a=time.perf_counter()
						
						wackyInitialTransform=False
						
						maxScaleDiffICP = params['maxScaleDiffICP'] # like 0.3 or something
						maxRotationICP = params['maxRotationICP'] # like 30 degrees?
						for planeI in range(2):
							if len(mainEdgePlanesSegments)-1>=planeI and len(mainEdgePlanesSegments[planeI])>0:
								tmpTrackingP1AfterTransformation = (mainEdgePlanesSegments[planeI][0][0][0], mainEdgePlanesSegments[planeI][0][0][1])
								tmpTrackingP2AfterTransformation = (mainEdgePlanesSegments[planeI][-1][-1][0], mainEdgePlanesSegments[planeI][-1][-1][1])
								
								tmpTrackingP1=(mainEdgeSegmentedDat[0][planeI][0][0][0], mainEdgeSegmentedDat[0][planeI][0][0][1])
								tmpTrackingP2=(mainEdgeSegmentedDat[0][planeI][-1][-1][0], mainEdgeSegmentedDat[0][planeI][-1][-1][1])
								
								tmpDistBefore = getDistance(tmpTrackingP1[0], tmpTrackingP2[0], tmpTrackingP1[1], tmpTrackingP2[1])
								tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
								
								tmpScale = tmpDistAfter/tmpDistBefore
								
								if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
									wackyInitialTransform=True
									break
								
								tmpRotation = math.atan2(tmpTrackingP2AfterTransformation[1]-tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[0]-tmpTrackingP1AfterTransformation[0]) - math.atan2(tmpTrackingP2[1]-tmpTrackingP1[1], tmpTrackingP2[0]-tmpTrackingP1[0])
								
								if tmpRotation<=-math.pi:
									tmpRotation+=2*math.pi
								if tmpRotation>math.pi:
									tmpRotation-=2*math.pi
								if tmpRotation<-maxRotationICP or tmpRotation>maxRotationICP:
									wackyInitialTransform=True
									break
							
							if len(otherEdgePlanesSegments)-1>=planeI and len(otherEdgePlanesSegments[planeI])>0:
								tmpTrackingP1AfterTransformation = (otherEdgePlanesSegments[planeI][0][0][0], otherEdgePlanesSegments[planeI][0][0][1])
								tmpTrackingP2AfterTransformation = (otherEdgePlanesSegments[planeI][-1][-1][0], otherEdgePlanesSegments[planeI][-1][-1][1])
								
								tmpTrackingP1=(otherEdgeSegmentedDat[0][planeI][0][0][0], otherEdgeSegmentedDat[0][planeI][0][0][1])
								tmpTrackingP2=(otherEdgeSegmentedDat[0][planeI][-1][-1][0], otherEdgeSegmentedDat[0][planeI][-1][-1][1])
								
								tmpDistBefore = getDistance(tmpTrackingP1[0], tmpTrackingP2[0], tmpTrackingP1[1], tmpTrackingP2[1])
								tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
								
								tmpScale = tmpDistAfter/tmpDistBefore
								
								if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
									wackyInitialTransform=True
									break
								
								tmpRotation = math.atan2(tmpTrackingP2AfterTransformation[1]-tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[0]-tmpTrackingP1AfterTransformation[0]) - math.atan2(tmpTrackingP2[1]-tmpTrackingP1[1], tmpTrackingP2[0]-tmpTrackingP1[0])
								
								if tmpRotation<=-math.pi:
									tmpRotation+=2*math.pi
								if tmpRotation>math.pi:
									tmpRotation-=2*math.pi
								if tmpRotation<-maxRotationICP or tmpRotation>maxRotationICP:
									wackyInitialTransform=True
									break
							
						if wackyInitialTransform and not(lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']):
							return ['rerun']
						elif wackyInitialTransform and lastResort and params['justDoICPAnywayEvenIfScaleFailsLastResort']: # just reset to default and hope icp can handle default edgepair alignment
							mainEdgePlanesSegments = copy.deepcopy(mainEdgeSegmentedDat[0])
							otherEdgePlanesSegments = copy.deepcopy(otherEdgeSegmentedDat[0])
						
						if params['noICP']:
							avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
							
							# I'm just taking the scale of the largest plane in otherEdgePlanesSegments and using that as reference scale to normalise
							# the average dist (score)
							# using otherEdgePlanesSegments instead of mainEdgePlanesSegments cause im fitting otherEdge to mainEdge
							# so the score is based on pairing all otherEdge pts to a mainEdge pt so it makes sense, if otherEdge is bricked and scaled weirdly the score will be normalised correctly to handle this
							
							reqPlane1Size = 0
							reqPlane2Size = 0
							for segDat in otherEdgePlanesSegments[0]:##
								for coord in segDat:
									reqPlane1Size+=1
							if len(otherEdgePlanesSegments)==2:##
								for segDat in otherEdgePlanesSegments[1]:##
									for coord in segDat:
										reqPlane2Size+=1
							reqPlane = None
							baseDistBetweenEndPointsReqPlane = None
							if reqPlane1Size>=reqPlane2Size:
								reqPlane = otherEdgePlanesSegments[0]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
							else:
								reqPlane = otherEdgePlanesSegments[1]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
							transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
							
							inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
							
							scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
							
							scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
							
							avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
							
							return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
						
						max_iterations = params['maxICPIterations']
						initial_iterations = params['initialICPIterations']
						maxPairingToSamePtAmount = params['maxPairingToSamePtAmountICP']
						
						otherPlane1SegmentDat = copy.deepcopy(otherEdgePlanesSegments[otherEdgeSeedPlane])
						otherPlane2SegmentDat = copy.deepcopy(otherEdgePlanesSegments[1-otherEdgeSeedPlane])
						
						transformOther1ToMain1, correspondencesOther1ToMain1, tdat = planeToPlaneICP(mainEdgePlanesSegments[mainEdgeSeedPlane], otherPlane1SegmentDat, initial_iterations, 1, params=params)
						time4+=tdat[0]
						transformOther2ToMain1, correspondencesOther2ToMain1, tdat = planeToPlaneICP(mainEdgePlanesSegments[mainEdgeSeedPlane], otherPlane2SegmentDat, initial_iterations, 1, params=params)
						time4+=tdat[0]
						
						otherPlane1SegmentDat2 = copy.deepcopy(otherEdgePlanesSegments[otherEdgeSeedPlane])
						otherPlane2SegmentDat2 = copy.deepcopy(otherEdgePlanesSegments[1-otherEdgeSeedPlane])
						
						transformOther1ToMain2, correspondencesOther1ToMain2, tdat = planeToPlaneICP(mainEdgePlanesSegments[1-mainEdgeSeedPlane], otherPlane1SegmentDat2, initial_iterations, 1, params=params)
						time4+=tdat[0]
						transformOther2ToMain2, correspondencesOther2ToMain2, tdat = planeToPlaneICP(mainEdgePlanesSegments[1-mainEdgeSeedPlane], otherPlane2SegmentDat2, initial_iterations, 1, params=params)
						time4+=tdat[0]
						
						prelimCorrespondences = (correspondencesOther1ToMain1, correspondencesOther2ToMain1, correspondencesOther1ToMain2, correspondencesOther2ToMain2)
						prelimSegmentDats = (otherPlane1SegmentDat, otherPlane2SegmentDat, otherPlane1SegmentDat2, otherPlane2SegmentDat2)
						prelimTransforms = (transformOther1ToMain1, transformOther2ToMain1, transformOther1ToMain2, transformOther2ToMain2)
						prelimMainPlanes = (mainEdgeSeedPlane, mainEdgeSeedPlane, 1-mainEdgeSeedPlane, 1-mainEdgeSeedPlane)
						
						largestCorrespondences = 0
						largestCorrespondencesInd = 0
						secondLargestCorrespondences = 0
						secondLargestCorrespondencesInd = 0
						for prelimCorrespondenceInd, prelimCorrespondence in enumerate(prelimCorrespondences):
							if prelimCorrespondence is not None and len(prelimCorrespondence)>largestCorrespondences:
								secondLargestCorrespondences, secondLargestCorrespondencesInd = largestCorrespondences, largestCorrespondencesInd
								largestCorrespondences=len(prelimCorrespondence)
								largestCorrespondencesInd=prelimCorrespondenceInd
							elif prelimCorrespondence is not None and len(prelimCorrespondence)>secondLargestCorrespondences:
								secondLargestCorrespondences=len(prelimCorrespondence)
								secondLargestCorrespondencesInd=prelimCorrespondenceInd
						
						if largestCorrespondences==0:
							print("weird, no correspondences at all")
							# exit()
							return None
						
						
						if secondLargestCorrespondences==0:
							# only need 1 plane to 1 plane
							
							finishedICPTransform1, finishedICPCorrespondences1, tdat = planeToPlaneICP(mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], prelimSegmentDats[largestCorrespondencesInd], max_iterations-initial_iterations, 1, params=params) # total 15 iterations
							time4+=tdat[0]
							if finishedICPTransform1 is None:
								print("why none? oidjoij3")
								# exit()
								tmpt4b=time.perf_counter()
								time3+=tmpt4b-tmpt4a
								return None
							
							finishedICPTransform1=np.matmul(finishedICPTransform1, prelimTransforms[largestCorrespondencesInd])
							
							if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
								otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
							else:
								otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
							
							avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
							
							reqPlane1Size = 0
							reqPlane2Size = 0
							for segDat in otherEdgePlanesSegments[0]:##
								for coord in segDat:
									reqPlane1Size+=1
							if len(otherEdgePlanesSegments)==2:##
								for segDat in otherEdgePlanesSegments[1]:##
									for coord in segDat:
										reqPlane2Size+=1
							reqPlane = None
							baseDistBetweenEndPointsReqPlane = None
							if reqPlane1Size>=reqPlane2Size:
								reqPlane = otherEdgePlanesSegments[0]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
							else:
								reqPlane = otherEdgePlanesSegments[1]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
							transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
							
							inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
							scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
							
							scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
							
							avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
							
							tmpt4b=time.perf_counter()
							time3+=tmpt4b-tmpt4a
							return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
							
						# 0,3  1,2
						if largestCorrespondencesInd==0 and secondLargestCorrespondencesInd==3 or largestCorrespondencesInd==3 and secondLargestCorrespondencesInd==0 or largestCorrespondencesInd==1 and secondLargestCorrespondencesInd==2 or largestCorrespondencesInd==2 and secondLargestCorrespondencesInd==1:
							if debugmode:
								input('129ud')
							finishedICPTransform1, finishedICPCorrespondences1, tdat = planeToPlaneICP(mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], prelimSegmentDats[largestCorrespondencesInd], max_iterations-initial_iterations, 1, params=params) # total 15 iterations
							time4+=tdat[0]
							finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]], prelimSegmentDats[secondLargestCorrespondencesInd], max_iterations-initial_iterations, 1, params=params) # total 15 iterations
							time4+=tdat[0]
							
							secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts = None
							if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
								secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsFirstOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
							else:
								secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsSecondOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
							
							if finishedICPTransform1 is None or (finishedICPTransform2 is None and secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']):#
								print("why is this None...? 21ij21")
								# exit()
								tmpt4b=time.perf_counter()
								time3+=tmpt4b-tmpt4a
								return None
							
							assumedUnPairedAreasIntervalsOtherA = inefficientCorrespondenceAreas(mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], prelimSegmentDats[largestCorrespondencesInd], 1, params=params)
							assumedUnPairedAreasIntervalsOtherB = inefficientCorrespondenceAreas(mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]], prelimSegmentDats[secondLargestCorrespondencesInd], 1, params=params)
							assumedUnPairedAreasIntervalsMainA = inefficientCorrespondenceAreas(prelimSegmentDats[largestCorrespondencesInd], mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], 1, params=params)
							assumedUnPairedAreasIntervalsMainB = inefficientCorrespondenceAreas(prelimSegmentDats[secondLargestCorrespondencesInd], mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]], 1, params=params)
							
							if assumedUnPairedAreasIntervalsOtherA is None or assumedUnPairedAreasIntervalsOtherB is None or assumedUnPairedAreasIntervalsMainA is None or assumedUnPairedAreasIntervalsMainB is None:
								print("why is this None...? 2112r21")
								# exit()
								tmpt4b=time.perf_counter()
								time3+=tmpt4b-tmpt4a
								return None
								
							elif len(assumedUnPairedAreasIntervalsOtherA)==0 or len(assumedUnPairedAreasIntervalsOtherB)==0 or len(assumedUnPairedAreasIntervalsMainA)==0 or len(assumedUnPairedAreasIntervalsMainB)==0:
								avgDistClosestPointsFromOtherToMain=None
								tmpCorresp=None
								
								segDatMainA = mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]]
								segDatOtherB = prelimSegmentDats[secondLargestCorrespondencesInd]
								
								segDatMainB = mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]]
								segDatOtherA = prelimSegmentDats[largestCorrespondencesInd]
								
								if len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsOtherB)==0: # a full edge is fully paired so just find the pairings
									
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in otherEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(otherEdgePlanesSegments)==2:##
										for segDat in otherEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = otherEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
									else:
										reqPlane = otherEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
								elif len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsMainB)==0:
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in mainEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(mainEdgePlanesSegments)==2:##
										for segDat in mainEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = mainEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
									else:
										reqPlane = mainEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
								elif len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsOtherB)==0 and len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsMainB)==0:
									print('does this even happen? why did i put this here89h')
									exit()
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in otherEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(otherEdgePlanesSegments)==2:##
										for segDat in otherEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = otherEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
									else:
										reqPlane = otherEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
								else: # only bothering to handle below where 1 plane from 1 edge is fully paired, in these cases do similar to when starting with the 2 biggest correspondences being 2 main -> 1 other or 2 other-> 1 main
									if len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsOtherB)!=0 and len(assumedUnPairedAreasIntervalsMainA)!=0 and len(assumedUnPairedAreasIntervalsMainB)!=0:
										finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatMainA, segDatOtherB, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsMainA, params=params) # total 15 iterations
										time4+=tdat[0]
										# now need to also transform mainB in same way otherB was just transformed because mainB is attached to otherB
										
										if finishedICPTransform2 is None:
											print("transform is None o2if33o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										for tmpSegDatI in range(len(segDatMainB)):
											for tmpCoordI in range(len(segDatMainB[tmpSegDatI])):
												veryTmpCoord = [segDatMainB[tmpSegDatI][tmpCoordI][0], segDatMainB[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(finishedICPTransform2, veryTmpCoord)
												segDatMainB[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainB[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
										# lastly make sure to pair FROM other TO main
										
										if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
										
										if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
										
										avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
										
										reqPlane1Size = 0
										reqPlane2Size = 0
										for segDat in otherEdgePlanesSegments[0]:##
											for coord in segDat:
												reqPlane1Size+=1
										if len(otherEdgePlanesSegments)==2:##
											for segDat in otherEdgePlanesSegments[1]:##
												for coord in segDat:
													reqPlane2Size+=1
										reqPlane = None
										baseDistBetweenEndPointsReqPlane = None
										if reqPlane1Size>=reqPlane2Size:
											reqPlane = otherEdgePlanesSegments[0]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
										else:
											reqPlane = otherEdgePlanesSegments[1]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
										transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
										
										inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
										scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
										
										scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
										
										avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
										
									elif len(assumedUnPairedAreasIntervalsOtherA)!=0 and len(assumedUnPairedAreasIntervalsOtherB)==0 and len(assumedUnPairedAreasIntervalsMainA)!=0 and len(assumedUnPairedAreasIntervalsMainB)!=0:
										finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatMainB, segDatOtherA, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsMainB, params=params) # total 15 iterations
										time4+=tdat[0]
										# now need to also transform mainA in same way otherA was just transformed because mainA is attached to otherA
										
										if finishedICPTransform2 is None:
											print("transform is None o3f3f3o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										for tmpSegDatI in range(len(segDatMainA)):
											for tmpCoordI in range(len(segDatMainA[tmpSegDatI])):
												veryTmpCoord = [segDatMainA[tmpSegDatI][tmpCoordI][0], segDatMainA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(finishedICPTransform2, veryTmpCoord)
												segDatMainA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
										# lastly make sure to pair FROM other TO main
										
										if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
										
										if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
										
										avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
										
										reqPlane1Size = 0
										reqPlane2Size = 0
										for segDat in otherEdgePlanesSegments[0]:##
											for coord in segDat:
												reqPlane1Size+=1
										if len(otherEdgePlanesSegments)==2:##
											for segDat in otherEdgePlanesSegments[1]:##
												for coord in segDat:
													reqPlane2Size+=1
										reqPlane = None
										baseDistBetweenEndPointsReqPlane = None
										if reqPlane1Size>=reqPlane2Size:
											reqPlane = otherEdgePlanesSegments[0]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
										else:
											reqPlane = otherEdgePlanesSegments[1]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
										transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
										
										inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
										scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
										
										scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
										
										avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
										
									elif len(assumedUnPairedAreasIntervalsOtherA)!=0 and len(assumedUnPairedAreasIntervalsOtherB)!=0 and len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsMainB)!=0:
										finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatOtherA, segDatMainB, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsOtherA, params=params) # total 15 iterations
										time4+=tdat[0]
										if finishedICPTransform2 is None:
											print("transform is None og4g42")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										# now need to also transform otherB in same way mainB was just transformed because otherB is attached to mainB
										
										for tmpSegDatI in range(len(segDatOtherB)):
											for tmpCoordI in range(len(segDatOtherB[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherB[tmpSegDatI][tmpCoordI][0], segDatOtherB[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(finishedICPTransform2, veryTmpCoord)
												segDatOtherB[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherB[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
										# lastly make sure to pair FROM main TO other
										
										if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
										
										if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
										
										avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments)
										
										reqPlane1Size = 0
										reqPlane2Size = 0
										for segDat in mainEdgePlanesSegments[0]:##
											for coord in segDat:
												reqPlane1Size+=1
										if len(mainEdgePlanesSegments)==2:##
											for segDat in mainEdgePlanesSegments[1]:##
												for coord in segDat:
													reqPlane2Size+=1
										reqPlane = None
										baseDistBetweenEndPointsReqPlane = None
										if reqPlane1Size>=reqPlane2Size:
											reqPlane = mainEdgePlanesSegments[0]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
										else:
											reqPlane = mainEdgePlanesSegments[1]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
										transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
										
										inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
										scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
										
										scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
										
										avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
										
									elif len(assumedUnPairedAreasIntervalsOtherA)!=0 and len(assumedUnPairedAreasIntervalsOtherB)!=0 and len(assumedUnPairedAreasIntervalsMainA)!=0 and len(assumedUnPairedAreasIntervalsMainB)==0:
										finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatOtherB, segDatMainA, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsOtherB, params=params) # total 15 iterations
										time4+=tdat[0]
										if finishedICPTransform2 is None:
											print("transform is None o2g4g4o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										# now need to also transform otherA in same way mainA was just transformed because otherA is attached to mainA
										
										for tmpSegDatI in range(len(segDatOtherA)):
											for tmpCoordI in range(len(segDatOtherA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherA[tmpSegDatI][tmpCoordI][0], segDatOtherA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(finishedICPTransform2, veryTmpCoord)
												segDatOtherA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
										# lastly make sure to pair FROM main TO other
										
										if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
										
										if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
										else:
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
										
										avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments)
										
										reqPlane1Size = 0
										reqPlane2Size = 0
										for segDat in mainEdgePlanesSegments[0]:##
											for coord in segDat:
												reqPlane1Size+=1
										if len(mainEdgePlanesSegments)==2:##
											for segDat in mainEdgePlanesSegments[1]:##
												for coord in segDat:
													reqPlane2Size+=1
										reqPlane = None
										baseDistBetweenEndPointsReqPlane = None
										if reqPlane1Size>=reqPlane2Size:
											reqPlane = mainEdgePlanesSegments[0]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
										else:
											reqPlane = mainEdgePlanesSegments[1]##
											baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
										transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
										
										inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
										scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
										
										scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
										
										avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
										
									else:
										print("not handling remaining cases")
										tmpt4b=time.perf_counter()
										time3+=tmpt4b-tmpt4a
										return ['rerun']
										# return None
								
								tmpt4b=time.perf_counter()
								time3+=tmpt4b-tmpt4a
								
								return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
							
							# NOTE NAMING/LETTERING WAS FLIPPED FOR NO REASON COMPARED TO LETTERING ABOVE FOR UNPAIRED AREAS
							segDatMainA = mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]]
							segDatOtherA = prelimSegmentDats[secondLargestCorrespondencesInd]
							
							segDatMainB = mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]]
							segDatOtherB = prelimSegmentDats[largestCorrespondencesInd]
							
							lastTransform, lastCorrespondences = planeToPlaneICPTwoAtOnce(segDatMainA, segDatOtherA, segDatMainB, segDatOtherB, max_iterations, maxPairingToSamePtAmount, assumedUnPairedAreasIntervalsMainA, assumedUnPairedAreasIntervalsOtherB, assumedUnPairedAreasIntervalsMainB, assumedUnPairedAreasIntervalsOtherA, params=params, swapOtherMain=True, dontSwap=True)
							
							if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
								otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
							else:
								otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
							
							if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
								otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
							else:
								otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
							
							# correspondencs/closest points, merge all pts from both planes in mainEdge into a tree and iterate all pts in otherEdge
							# dont need to worry aboiut endings or anything cause just want closest pts dists to calc similarity
							
							avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
							
							reqPlane1Size = 0
							reqPlane2Size = 0
							for segDat in otherEdgePlanesSegments[0]:##
								for coord in segDat:
									reqPlane1Size+=1
							if len(otherEdgePlanesSegments)==2:##
								for segDat in otherEdgePlanesSegments[1]:##
									for coord in segDat:
										reqPlane2Size+=1
							reqPlane = None
							baseDistBetweenEndPointsReqPlane = None
							if reqPlane1Size>=reqPlane2Size:
								reqPlane = otherEdgePlanesSegments[0]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
							else:
								reqPlane = otherEdgePlanesSegments[1]##
								baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
							transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
							
							inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
							scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
							
							scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
							
							avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
							
							tmpt4b=time.perf_counter()
							time3+=tmpt4b-tmpt4a
							
							return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
							
						# ugh, even more confusing case, 2 mains to 1 other or 2 others to 1 main, ... (4 unique cases for this)
						else: # just splitting these too cause can get confusing
							
							# if its 2 other to 1 main
							if largestCorrespondencesInd==0 and secondLargestCorrespondencesInd==1 or largestCorrespondencesInd==1 and secondLargestCorrespondencesInd==0 or largestCorrespondencesInd==2 and secondLargestCorrespondencesInd==3 or largestCorrespondencesInd==3 and secondLargestCorrespondencesInd==2:
								
								finishedICPTransform1, finishedICPCorrespondences1, tdat = planeToPlaneICP(mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], prelimSegmentDats[largestCorrespondencesInd], max_iterations-initial_iterations, 1, params=params) # total 15 iterations
								time4+=tdat[0]
								if finishedICPTransform1 is None:
									print("why none? oidjoij3")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								finishedICPTransform1=np.matmul(finishedICPTransform1, prelimTransforms[largestCorrespondencesInd])
								
								assumedUnPairedAreasIntervalsMainA = inefficientCorrespondenceAreas(prelimSegmentDats[largestCorrespondencesInd], mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]], 1, params=params)
								
								segDatMainA = mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]]
								segDatMainB = None
								if largestCorrespondencesInd==0 or largestCorrespondencesInd==1:
									segDatMainB=mainEdgePlanesSegments[prelimMainPlanes[2]]
								else:
									segDatMainB=mainEdgePlanesSegments[prelimMainPlanes[0]]
								
								segDatOtherA = prelimSegmentDats[largestCorrespondencesInd]
								segDatOtherB = prelimSegmentDats[secondLargestCorrespondencesInd]
								
								if len(assumedUnPairedAreasIntervalsMainA)==0:
									print("hmmm, 2 other to 1 main, but 1 other fully corresponds to 1 main, leaving the 2nd other plane on its own... o23ijo3i")
								
								if assumedUnPairedAreasIntervalsMainA is None:
									print("why none? oid2332joij3")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								finishedICPTransform2=None
								if len(assumedUnPairedAreasIntervalsMainA)!=0: # REMEMBER!!! segDatMainA == mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]] == mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]]
									finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatMainA, segDatOtherB, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsMainA, params=params) # restrict mainPlane1 based on pairing with first otherPlane1, then pair remaining with otherPlane2
									time4+=tdat[0]
								
								secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts = None
								if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
									secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsFirstOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
								else:
									secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsSecondOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
								endEarlyICP=secondLargestCorrespondencesIndReleventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
								
								if len(assumedUnPairedAreasIntervalsMainA)!=0 and finishedICPTransform2 is None and endEarlyICP:
								# if len(assumedUnPairedAreasIntervalsMainA)!=0 or finishedICPTransform2 is None:
									print("why none? oid23525j3")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								assumedUnPairedAreasIntervalsOtherB=None
								assumedUnPairedAreasIntervalsOtherA = inefficientCorrespondenceAreas(segDatMainA, segDatOtherA, 1, params=params)
								if len(assumedUnPairedAreasIntervalsMainA)!=0:
									assumedUnPairedAreasIntervalsOtherB = inefficientCorrespondenceAreas(segDatMainA, segDatOtherB, 1, params=params) # remember, in this case largestCorrespondencesInd==secondLargestCorrespondencesInd
								
								if assumedUnPairedAreasIntervalsOtherA is None or (len(assumedUnPairedAreasIntervalsMainA)!=0 and assumedUnPairedAreasIntervalsOtherB is None):
									print("why none? ot32t44t")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								if len(assumedUnPairedAreasIntervalsMainA)!=0:# and len(assumedUnPairedAreasIntervalsOtherA)!=0 and len(assumedUnPairedAreasIntervalsOtherB)!=0:
									
									if len(assumedUnPairedAreasIntervalsOtherA)!=0 and len(assumedUnPairedAreasIntervalsOtherB)!=0:
										lastTransform, lastCorrespondences = planeToPlaneICPTwoAtOnce(segDatOtherA, segDatMainB, segDatOtherB, segDatMainB, max_iterations, maxPairingToSamePtAmount, segmentDatMainSubset1=assumedUnPairedAreasIntervalsOtherA, segmentDatMainSubset2=assumedUnPairedAreasIntervalsOtherB, dontSwap=True, bothOtherPlanesAreSame=True, params=params)
										# if lastCorrespondences is None:
											# return None
									elif len(assumedUnPairedAreasIntervalsOtherA)!=0:
										lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatMainB, segDatOtherA, max_iterations, 1, segmentDatOtherSubset=assumedUnPairedAreasIntervalsOtherA, params=params) # restrict mainPlane1 based on pairing with first otherPlane1, then pair remaining with otherPlane2
										time4+=tdat[0]
										
										if lastTransform is None:
											print("transform is None o2ij1o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										for tmpSegDatI in range(len(segDatOtherB)):
											for tmpCoordI in range(len(segDatOtherB[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherB[tmpSegDatI][tmpCoordI][0], segDatOtherB[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatOtherB[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherB[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										for tmpSegDatI in range(len(segDatMainA)):
											for tmpCoordI in range(len(segDatMainA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatMainA[tmpSegDatI][tmpCoordI][0], segDatMainA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatMainA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
									elif len(assumedUnPairedAreasIntervalsOtherB)!=0:
										lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatMainB, segDatOtherB, max_iterations, 1, segmentDatOtherSubset=assumedUnPairedAreasIntervalsOtherB, params=params) # restrict mainPlane1 based on pairing with first otherPlane1, then pair remaining with otherPlane2
										time4+=tdat[0]
										if lastTransform is None:
											print("transform is None o2ij123r3o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										for tmpSegDatI in range(len(segDatOtherA)):
											for tmpCoordI in range(len(segDatOtherA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherA[tmpSegDatI][tmpCoordI][0], segDatOtherA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatOtherA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										for tmpSegDatI in range(len(segDatMainA)):
											for tmpCoordI in range(len(segDatMainA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatMainA[tmpSegDatI][tmpCoordI][0], segDatMainA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatMainA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
										
									elif len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsOtherB)==0:
										pass
									else:
										print("is this even a case? 3idj3")
										exit()
									
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments) # kinda arbitrary order
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in mainEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(mainEdgePlanesSegments)==2:##
										for segDat in mainEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = mainEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
									else:
										reqPlane = mainEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
								elif len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsOtherA)!=0:
									lastTransform, lastCorrespondences = planeToPlaneICPTwoAtOnce(segDatOtherA, segDatMainB, segDatOtherB, segDatMainB, max_iterations, maxPairingToSamePtAmount, segmentDatMainSubset1=assumedUnPairedAreasIntervalsOtherA, dontSwap=True, bothOtherPlanesAreSame=True, params=params)
									
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in mainEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(mainEdgePlanesSegments)==2:##
										for segDat in mainEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = mainEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
									else:
										reqPlane = mainEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
								elif len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsOtherA)==0:
									lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatMainB, segDatOtherB, max_iterations, 1, params=params) # total 15 iterations
									
									#segDatOtherB
									releventPlaneAsRatioOfTotalSegmentedDatPts = None
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsFirstOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
									else:
										releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsSecondOtherPlane/(amtPtsFirstOtherPlane+amtPtsSecondOtherPlane)
									endEarlyICP=releventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
									
									if lastCorrespondences is None and endEarlyICP:
										return None
									time4+=tdat[0]
									if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[largestCorrespondencesInd]
									
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==2:
										otherEdgePlanesSegments[otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									else:
										otherEdgePlanesSegments[1-otherEdgeSeedPlane] = prelimSegmentDats[secondLargestCorrespondencesInd]
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in otherEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(otherEdgePlanesSegments)==2:##
										for segDat in otherEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = otherEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
									else:
										reqPlane = otherEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
								else:
									print("nt sure whats left here but tired 983jd3i2")
									exit()
									# return None
								
							# 2 main to 1 other
							elif largestCorrespondencesInd==0 and secondLargestCorrespondencesInd==2 or largestCorrespondencesInd==2 and secondLargestCorrespondencesInd==0 or largestCorrespondencesInd==1 and secondLargestCorrespondencesInd==3 or largestCorrespondencesInd==3 and secondLargestCorrespondencesInd==1:
								
								segDatOtherA = None
								segDatOtherB = None
								
								if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
									segDatOtherA = otherEdgePlanesSegments[otherEdgeSeedPlane]
									segDatOtherB = otherEdgePlanesSegments[1-otherEdgeSeedPlane]
								elif largestCorrespondencesInd==1 or largestCorrespondencesInd==3:
									segDatOtherA = otherEdgePlanesSegments[1-otherEdgeSeedPlane]
									segDatOtherB = otherEdgePlanesSegments[otherEdgeSeedPlane]
								
								segDatMainA = mainEdgePlanesSegments[prelimMainPlanes[largestCorrespondencesInd]]
								segDatMainB = mainEdgePlanesSegments[prelimMainPlanes[secondLargestCorrespondencesInd]]
								
								finishedICPTransform1, finishedICPCorrespondences1, tdat = planeToPlaneICP(segDatOtherA, segDatMainA, max_iterations, 1, params=params) # total 15 iterations
								time4+=tdat[0]
								assumedUnPairedAreasIntervalsOtherA = inefficientCorrespondenceAreas(segDatMainA, segDatOtherA, 1, params=params)
								if len(assumedUnPairedAreasIntervalsOtherA)==0:
									print("hmmm, 2 main to 1 other, but 1 main fully corresponds to 1 other, leaving the 2nd main plane on its own... o23ijo3i")
								
								if finishedICPTransform1 is None or assumedUnPairedAreasIntervalsOtherA is None:
									print("why none? otf2f3")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								finishedICPTransform2=None
								if len(assumedUnPairedAreasIntervalsOtherA)!=0: # if this ==0 then there are no remaining points available in segDatOtherA to pair main plane 2 points to
									finishedICPTransform2, finishedICPCorrespondences2, tdat = planeToPlaneICP(segDatOtherA, segDatMainB, max_iterations, 1, segmentDatMainSubset=assumedUnPairedAreasIntervalsOtherA, params=params) # restrict mainPlane1 based on pairing with first otherPlane1, then pair remaining with otherPlane2
									time4+=tdat[0]
								
								assumedUnPairedAreasIntervalsMainB=None
								assumedUnPairedAreasIntervalsMainA = inefficientCorrespondenceAreas(segDatOtherA, segDatMainA, 1, params=params)
								if len(assumedUnPairedAreasIntervalsOtherA)!=0:
									assumedUnPairedAreasIntervalsMainB = inefficientCorrespondenceAreas(segDatOtherA, segDatMainB, 1, params=params) # remember, in this case largestCorrespondencesInd==secondLargestCorrespondencesInd
								
								#segDatMainB
								releventPlaneAsRatioOfTotalSegmentedDatPts = None
								if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==1:
									releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsFirstMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
								else:
									releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsSecondMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
								endEarlyICP=releventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
								
								if (len(assumedUnPairedAreasIntervalsOtherA)!=0 and finishedICPTransform2 is None and endEarlyICP) or assumedUnPairedAreasIntervalsMainA is None or (len(assumedUnPairedAreasIntervalsOtherA)!=0 and assumedUnPairedAreasIntervalsMainB is None):
									print("why none? of323fgg2f3")
									# exit()
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return None
								
								# DONT NEED TO REASSIGN segDats TO PLANESSEGMENTS HERE, SINCE THEY ARE ALREADY THE OGJECTS BEING ALTERED (see right above)
								lastTransform=None
								lastCorrespondences=None
								if len(assumedUnPairedAreasIntervalsOtherA)!=0:# and len(assumedUnPairedAreasIntervalsMainA)!=0 and len(assumedUnPairedAreasIntervalsMainB)!=0: # original normal scenario
									if len(assumedUnPairedAreasIntervalsMainA)!=0 and len(assumedUnPairedAreasIntervalsMainB)!=0:
										lastTransform, lastCorrespondences = planeToPlaneICPTwoAtOnce(segDatMainA, segDatOtherB, segDatMainB, segDatOtherB, max_iterations, 1, segmentDatMainSubset1=assumedUnPairedAreasIntervalsMainA, segmentDatMainSubset2=assumedUnPairedAreasIntervalsMainB, dontSwap=True, bothOtherPlanesAreSame=True, params=params)
										
										if largestCorrespondencesInd==0 or largestCorrespondencesInd==2:
											# segDatOtherA = otherEdgePlanesSegments[otherEdgeSeedPlane]
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherA
											# segDatOtherB = otherEdgePlanesSegments[1-otherEdgeSeedPlane]
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherB
										elif largestCorrespondencesInd==1 or largestCorrespondencesInd==3:
											# segDatOtherA = otherEdgePlanesSegments[1-otherEdgeSeedPlane]
											otherEdgePlanesSegments[1-otherEdgeSeedPlane] = segDatOtherA
											# segDatOtherB = otherEdgePlanesSegments[otherEdgeSeedPlane]
											otherEdgePlanesSegments[otherEdgeSeedPlane] = segDatOtherB
										
									elif len(assumedUnPairedAreasIntervalsMainA)!=0:
										lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatOtherB, segDatMainA, max_iterations, 1, segmentDatOtherSubset=assumedUnPairedAreasIntervalsMainA, params=params)
										time4+=tdat[0]
										# apply lastTransform to segDatMainB and segDatOtherA
										
										if lastTransform is None:
											print("transform is None o2ijj7j1o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										
										for tmpSegDatI in range(len(segDatMainB)):
											for tmpCoordI in range(len(segDatMainB[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatMainB[tmpSegDatI][tmpCoordI][0], segDatMainB[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatMainB[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainB[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										for tmpSegDatI in range(len(segDatOtherA)):
											for tmpCoordI in range(len(segDatOtherA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherA[tmpSegDatI][tmpCoordI][0], segDatOtherA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatOtherA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
									elif len(assumedUnPairedAreasIntervalsMainB)!=0:
										lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatOtherB, segDatMainB, max_iterations, 1, segmentDatOtherSubset=assumedUnPairedAreasIntervalsMainB, params=params)
										time4+=tdat[0]
										# apply lastTransform to segDatMainA and segDatOtherA
										
										if lastTransform is None:
											print("transform is None of3f32ij1o2")
											tmpt4b=time.perf_counter()
											time3+=tmpt4b-tmpt4a
											return None
										
										for tmpSegDatI in range(len(segDatMainA)):
											for tmpCoordI in range(len(segDatMainA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatMainA[tmpSegDatI][tmpCoordI][0], segDatMainA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatMainA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatMainA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										for tmpSegDatI in range(len(segDatOtherA)):
											for tmpCoordI in range(len(segDatOtherA[tmpSegDatI])):
												# arr2[i] = np.matmul(transformation, (arr2[i][0], arr2[i][1], 1))
												veryTmpCoord = [segDatOtherA[tmpSegDatI][tmpCoordI][0], segDatOtherA[tmpSegDatI][tmpCoordI][1], 1]
												veryTmpCoord = np.matmul(lastTransform, veryTmpCoord)
												segDatOtherA[tmpSegDatI][tmpCoordI][0] = veryTmpCoord[0]
												segDatOtherA[tmpSegDatI][tmpCoordI][1] = veryTmpCoord[1]
										
									elif len(assumedUnPairedAreasIntervalsMainA)==0 and len(assumedUnPairedAreasIntervalsMainB)==0: # for readability
										pass
									else:
										print("is there even anything left here? 32ojio3")
										exit()
										
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments) # main to other is esp important for last case
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in mainEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(mainEdgePlanesSegments)==2:##
										for segDat in mainEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = mainEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
									else:
										reqPlane = mainEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
								elif len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsMainA)!=0: # 
									lastTransform, lastCorrespondences = planeToPlaneICPTwoAtOnce(segDatMainA, segDatOtherB, segDatMainB, segDatOtherB, max_iterations, 1, segmentDatMainSubset1=assumedUnPairedAreasIntervalsMainA, dontSwap=True, bothOtherPlanesAreSame=True, params=params)
									
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in otherEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(otherEdgePlanesSegments)==2:##
										for segDat in otherEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = otherEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstOtherPlane##
									else:
										reqPlane = otherEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondOtherPlane##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/otherEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/otherEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
									
								elif len(assumedUnPairedAreasIntervalsOtherA)==0 and len(assumedUnPairedAreasIntervalsMainA)==0: # shouldve been 2 disjoint paired planes like one of the other conditionals
									lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatOtherB, segDatMainB, max_iterations, 1, params=params) # total 15 iterations
									
									#segDatMainB
									releventPlaneAsRatioOfTotalSegmentedDatPts = None
									if secondLargestCorrespondencesInd==0 or secondLargestCorrespondencesInd==1:
										releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsFirstMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
									else:
										releventPlaneAsRatioOfTotalSegmentedDatPts=amtPtsSecondMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
									endEarlyICP=releventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
									
									if lastCorrespondences is None and endEarlyICP:
										return None
									time4+=tdat[0]
									avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments)
									
									reqPlane1Size = 0
									reqPlane2Size = 0
									for segDat in mainEdgePlanesSegments[0]:##
										for coord in segDat:
											reqPlane1Size+=1
									if len(mainEdgePlanesSegments)==2:##
										for segDat in mainEdgePlanesSegments[1]:##
											for coord in segDat:
												reqPlane2Size+=1
									reqPlane = None
									baseDistBetweenEndPointsReqPlane = None
									if reqPlane1Size>=reqPlane2Size:
										reqPlane = mainEdgePlanesSegments[0]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
									else:
										reqPlane = mainEdgePlanesSegments[1]##
										baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
									transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
									
									inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
									scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
									
									scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
									
									avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									
									return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
								else:
									
									tmpt4b=time.perf_counter()
									time3+=tmpt4b-tmpt4a
									return ['rerun']
									# return None
								
								if lastTransform is None:
									print("why none? od3f323ffgg2f3")
									exit()
									# return None
								
							else:
								print("??D3j3d983hi3")
								exit()
						
						print("wat?e3j3jjjj")
						tmpt4b=time.perf_counter()
						time3+=tmpt4b-tmpt4a
						return ['rerun']
						# return None
		else:
			# rerun but with edges swapped
			return ['rerun']
		return None
		
	elif successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane and disjointPlanePairs:
		max_iterations=params['maxICPIterations']
		
		segDatMainA = mainEdgePlanesSegments[mainEdgeSeedPlane]
		segDatMainB = mainEdgePlanesSegments[1-mainEdgeSeedPlane]
		segDatOtherA = otherEdgePlanesSegments[otherEdgeSeedPlane]
		segDatOtherB = otherEdgePlanesSegments[1-otherEdgeSeedPlane]
		lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatOtherA, segDatMainA, max_iterations, 1, params=params)
		
		#segDatMainA
		releventPlaneAsRatioOfTotalSegmentedDatPts = amtPtsFirstMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
		endEarlyICP=releventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
		
		if lastCorrespondences is None and endEarlyICP:
			return ['rerun'] # returning rerun here cause if i dont then there's never option to reach lastResort if successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane
			# return None
		lastTransform, lastCorrespondences, tdat = planeToPlaneICP(segDatOtherB, segDatMainB, max_iterations, 1, params=params)
		
		#segDatMainB
		releventPlaneAsRatioOfTotalSegmentedDatPts = amtPtsSecondMainPlane/(amtPtsFirstMainPlane+amtPtsSecondMainPlane)
		endEarlyICP=releventPlaneAsRatioOfTotalSegmentedDatPts>=params['endICPMethodIfBadTransformHappensOnPlaneWithAtLeastRatioPtsAmount']
		
		if lastCorrespondences is None and endEarlyICP:
			return ['rerun']
			# return None
		
		avgDistClosestPointsFromOtherToMain, tmpCorresp = getAvgDistClosestPointsFromOtherToMain(otherEdgePlanesSegments, mainEdgePlanesSegments) # main to other is esp important for last case
		
		reqPlane1Size = 0
		reqPlane2Size = 0
		for segDat in mainEdgePlanesSegments[0]:##
			for coord in segDat:
				reqPlane1Size+=1
		if len(mainEdgePlanesSegments)==2:##
			for segDat in mainEdgePlanesSegments[1]:##
				for coord in segDat:
					reqPlane2Size+=1
		reqPlane = None
		baseDistBetweenEndPointsReqPlane = None
		if reqPlane1Size>=reqPlane2Size:
			reqPlane = mainEdgePlanesSegments[0]##
			baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsFirstMainPlane ##
		else:
			reqPlane = mainEdgePlanesSegments[1]##
			baseDistBetweenEndPointsReqPlane = baseDistBetweenEndPointsSecondMainPlane ##
		transformedDistBetweenEndPointsReqPlane = getDistance(reqPlane[0][0][0], reqPlane[-1][-1][0], reqPlane[0][0][1], reqPlane[-1][-1][1])
		
		if transformedDistBetweenEndPointsReqPlane==0:
			return ['rerun']
			# return None
		
		inverseScaleIncurredByThisFunction = baseDistBetweenEndPointsReqPlane/transformedDistBetweenEndPointsReqPlane # to get from avgDistClosestPoints scale space to scale space at start of this function
		scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace = (baseImageReferenceContourDat[0]/mainEdgeTransformedReferenceContourDat[0] + baseImageReferenceContourDat[1]/mainEdgeTransformedReferenceContourDat[1])/2 ##
		
		scaleAvgDistBetweenPtsToBaseImage = inverseScaleIncurredByThisFunction*scaleFromOriginalPlanesSegmentsToBaseImageReferenceContourSpace
		
		avgDistClosestPointsFromOtherToMain = avgDistClosestPointsFromOtherToMain*scaleAvgDistBetweenPtsToBaseImage
		
		return [avgDistClosestPointsFromOtherToMain, mainEdgePlanesSegments, otherEdgePlanesSegments, tmpCorresp, scaleAvgDistBetweenPtsToBaseImage]
		
	elif not(successfullyScaledOtherEdgeSoThatOtherSeedPlaneFitsMainSeedPlane):
		# rerun but with edges swapped
		return ['rerun']
	
	return None


def simpleLineSegLineIntersect(lineSegCoord1, lineSegCoord2, lineCoord1, lineCoord2):
	lineSegSlope = None
	lineSegC = None
	lineSegSlopeDiv = lineSegCoord2[0]-lineSegCoord1[0]
	if lineSegSlopeDiv!=0:
		lineSegSlope=(lineSegCoord2[1]-lineSegCoord1[1])/lineSegSlopeDiv
		lineSegC=lineSegCoord1[1]-lineSegSlope*lineSegCoord1[0]
	else:
		lineSegC=lineSegCoord1[0]
	
	lineSlope = None
	lineC = None
	lineSlopeDiv = lineCoord2[0]-lineCoord1[0]
	if lineSlopeDiv!=0:
		lineSlope=(lineCoord2[1]-lineCoord1[1])/lineSlopeDiv
		lineC=lineCoord1[1]-lineSlope*lineCoord1[0]
	else:
		lineC=lineCoord1[0]
	
	intersection = None
	if lineSegSlope != lineSlope: # \/ if intersection is outside line-segment part of inf line
		if lineSegSlope is not None and lineSlope is not None:
			intersectionSide1X = (lineC-lineSegC)/(lineSegSlope-lineSlope)
			intersection = [intersectionSide1X, lineSlope*intersectionSide1X + lineC]
		elif lineSegSlope is not None:
			# x = c1 is the line so if this intersects with anything itll be at x=c1
			intersection = [lineC, lineSegSlope*lineC+lineSegC]
		elif lineSlope is not None: 
			intersection = [lineSegC, lineSlope*lineSegC+lineC]
		if abs(lineSegCoord1[0]-intersection[0])<0.0000001:
			intersection[0]=lineSegCoord1[0]
		if abs(lineSegCoord1[1]-intersection[1])<0.0000001:
			intersection[1]=lineSegCoord1[1]
		if abs(lineSegCoord2[0]-intersection[0])<0.0000001:
			intersection[0]=lineSegCoord2[0]
		if abs(lineSegCoord2[1]-intersection[1])<0.0000001:
			intersection[1]=lineSegCoord2[1]
		
		if lineSegCoord1[0] != lineSegCoord2[0]:
			if lineSegCoord1[0] < lineSegCoord2[0]:
				if intersection[0] < lineSegCoord1[0] or intersection[0] > lineSegCoord2[0]:
					intersection = None
			else:
				if intersection[0] > lineSegCoord1[0] or intersection[0] < lineSegCoord2[0]:
					intersection = None
		else:
			if lineSegCoord1[1] < lineSegCoord2[1]:
				if intersection[1] < lineSegCoord1[1] or intersection[1] > lineSegCoord2[1]:
					intersection = None
			else:
				if intersection[1] > lineSegCoord1[1] or intersection[1] < lineSegCoord2[1]:
					intersection = None
		
	return intersection


def staticEdgeStepData(stepCoords, estimatedSize, edgeOrientation, params): # ASSUME COORDS HAVE BEEN SHIFTED SO ORIENTATION == X AXIS!
	rawDat = []
	tempStepData = {}
	
	for i in range(len(stepCoords)-2):
		subAreaOrient = math.atan2(stepCoords[i+1][0][1] - stepCoords[i][0][1], stepCoords[i+1][0][0] - stepCoords[i][0][0]) # edge orientation is already x axis so no point subtracting is cause itd be 0
		rawDat.append([[i, i+1], subAreaOrient])# ...]) # rawDat[j][0] are inds for stepCoords items
	
	# PARTITIONS ARE [CLOSED, OPEN)
	
	# partitionSize = 10*math.pi/180
	partitionSize = params['segOrientationPartitionSize']
	partitionAmt = int(math.ceil(math.pi*2/partitionSize)) # should always divide 360 degrees but just ceil in case I set it to something else to test something or something
	if "segOrientationPartitionAmt" not in params:
		params["segOrientationPartitionAmt"] = partitionAmt
	for i in range(partitionAmt):
		tempStepData[i] = [[partitionSize*i, partitionSize*(i+1)], []]
	for i in range(len(rawDat)):
		temp2PiRep = rawDat[i][1]
		if temp2PiRep<0:
			temp2PiRep+=math.pi*2
		partitionId = temp2PiRep/partitionSize
		partitionId = int(math.floor(partitionId))
		tempStepData[partitionId][1].append(i)
	
	for key, val in tempStepData.items(): # add extra for loop for each partition depth added
		tempInds = val[1]
		tempTree = unoptimisedOOBTree(stepCoords, rawDat, tempInds, True)
		tempStepData[key][1] = tempTree
		
	return tempStepData, rawDat


def getOnlyStepPoints(edge, arcLengthStepAmount, returnContour=False):
	arcLengthStepAmountCounter = arcLengthStepAmount-1 # cause add start manually and stuff
	
	edgeArcLength = cv2arcLengthReplacementFloats(edge)
	arcLengthStep = edgeArcLength/arcLengthStepAmountCounter
	
	onlyStepPoints = []
	
	if returnContour:
		onlyStepPoints.append([copy.deepcopy(edge[0][0])])
	else:
		onlyStepPoints.append([copy.deepcopy(edge[0][0]), 0, 0, 0, 0])
	
	currArclength = 0
	prevArclength = 0
	currStep = 1
	
	for i in range(1, edge.shape[0]):
		if currStep > arcLengthStepAmountCounter-1:
			break
		tempArclengthDist = getDistance(edge[i][0][0], edge[i-1][0][0], edge[i][0][1], edge[i-1][0][1])
		prevArclength=currArclength
		currArclength+=tempArclengthDist
		numberOfSteps = math.floor(currArclength/arcLengthStep)
		
		if numberOfSteps >= currStep:
			
			if True: #inbetweenLine:
				
				# not even going to handle case where 2 consecutive points have the same coordinates because opencv must not allow this
				tempMag = (math.sqrt((edge[i][0][0] - edge[i-1][0][0])**2 + (edge[i][0][1] - edge[i-1][0][1])**2))
				unitVecX = (edge[i][0][0] - edge[i-1][0][0])/tempMag
				unitVecY = (edge[i][0][1] - edge[i-1][0][1])/tempMag
				tempCurrStep = currStep
				for k in range(tempCurrStep, numberOfSteps+1):
					
					if k > arcLengthStepAmountCounter-1:
						currStep = arcLengthStepAmountCounter
						break
					distOnLine = k*arcLengthStep - prevArclength
					newX = edge[i-1][0][0] + distOnLine*unitVecX
					newY = edge[i-1][0][1] + distOnLine*unitVecY
					
					if returnContour:
						onlyStepPoints.append([[newX, newY]])
					else:
						onlyStepPoints.append([[newX, newY], i-1, distOnLine, distOnLine/tempArclengthDist, distOnLine/tempMag])
					
					currStep+=1
	# do final one manually in case small rounding errors affect desync the final point from the point that is arcLengthStep * arcLengthStepAmount from beginning
	lastDist = getDistance(edge[edge.shape[0]-2][0][0], edge[edge.shape[0]-1][0][0], edge[edge.shape[0]-2][0][1], edge[edge.shape[0]-1][0][1])
	
	if returnContour:
		onlyStepPoints.append([copy.deepcopy(edge[edge.shape[0]-1][0])])
	else:
		onlyStepPoints.append([copy.deepcopy(edge[edge.shape[0]-1][0]), edge.shape[0]-2, lastDist, 1,1])
	if returnContour:
		onlyStepPoints=np.asarray(onlyStepPoints)
	return onlyStepPoints, arcLengthStep


def projectPtToLine(lpt1, lpt2, pt3, returnWhat):
	
	if returnWhat == "ratioonline":
		x1, y1 = lpt1
		x2, y2 = lpt2
		x3, y3 = pt3
		dx, dy = x2-x1, y2-y1
		det = dx*dx + dy*dy
		a = (dy*(y3-y1)+dx*(x3-x1))/det
		
		return a
		
		# return x1+a*dx, y1+a*dy
	
	
	return None
































