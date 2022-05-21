import math
import numpy as np
import copy
import time

from timeit import default_timer as timer
from scipy.spatial import cKDTree


def getDistance(x1, x2, y1, y2):
	diffX = abs(x2 - x1)
	diffY = abs(y2 - y1)
	return math.hypot(diffX, diffY)

def closestPtToLineSeg(start, end, point, startInd):
	
	startToEnd = (end[0]-start[0], end[1]-start[1])
	startToPoint = (point[0]-start[0], point[1]-start[1])
	
	lengthSqrStartEnd = startToEnd[0]*startToEnd[0] + startToEnd[1]*startToEnd[1]
	if lengthSqrStartEnd!=0:
		t = (startToPoint[0]*startToEnd[0]+startToPoint[1]*startToEnd[1])/lengthSqrStartEnd
		if t>0 and t<1:
			newPt = (start[0]+t*startToEnd[0], start[1]+t*startToEnd[1])
			return newPt, startInd+t
	
	return None, None


def estimateSimilarityTransform(correspondences):
	sigmav = [0,0]
	sigmaU = [0,0]
	for corr in correspondences:
		sigmav[0]+=corr[0][0]
		sigmav[1]+=corr[0][1]
		sigmaU[0]+=corr[1][0]
		sigmaU[1]+=corr[1][1]
	c1sigmaEqn19 = 0
	c2sigmaEqn19 = 0
	for corr in correspondences:
		c1sigmaEqn19+=corr[1][0]*corr[0][1]-corr[0][0]*corr[1][1]
		c2sigmaEqn19+=corr[1][0]*corr[0][0]+corr[0][1]*corr[1][1]
	
	c1Eqn19 = (1/len(correspondences))*(sigmaU[0]*sigmav[1]-sigmav[0]*sigmaU[1])-c1sigmaEqn19
	c2Eqn19 = c2sigmaEqn19-(1/len(correspondences))*(sigmaU[0]*sigmav[0]+sigmav[1]*sigmaU[1])
	
	theta = math.atan2(c1Eqn19, c2Eqn19)
	
	cosTheta = math.cos(theta)
	sinTheta = math.sin(theta)
	rotMat = [[cosTheta, -sinTheta], [sinTheta, cosTheta]]
	# print(rotMat)
	e1Eqn24=0
	e2Eqn24=(1/len(correspondences))*(sigmaU[0]*(sigmav[0]*cosTheta-sigmav[1]*sinTheta)+sigmaU[1]*(sigmav[0]*sinTheta+sigmav[1]*cosTheta))
	e3Eqn24=0
	e4Eqn24=(1/len(correspondences))*(sigmav[0]*sigmav[0]+sigmav[1]*sigmav[1])
	
	for corr in correspondences:
		e1Eqn24+=corr[1][0]*(corr[0][0]*cosTheta - corr[0][1]*sinTheta) + corr[1][1]*(corr[0][0]*sinTheta+corr[0][1]*cosTheta)
		e3Eqn24+=corr[0][0]*corr[0][0]+corr[0][1]*corr[0][1]
	
	tmpDiv = e3Eqn24-e4Eqn24
	c=None
	if tmpDiv!=0:
		c = (e1Eqn24-e2Eqn24)/tmpDiv
	elif e1Eqn24-e2Eqn24==0:
		c=1
	else:
		return None, None, None
	Av = [rotMat[0][0]*sigmav[0]+rotMat[0][1]*sigmav[1], rotMat[1][0]*sigmav[0]+rotMat[1][1]*sigmav[1]]
	cAv = [c*Av[0], c*Av[1]]
	
	d = [(1/len(correspondences))*(sigmaU[0]-cAv[0]), (1/len(correspondences))*(sigmaU[1]-cAv[1])]
	
	return c, d, rotMat


def transformCust(pcd2, c, rotMat, d, transformation):
	
	rotMat3d = np.array([[c*rotMat[0][0], c*rotMat[0][1], 0], [c*rotMat[1][0], c*rotMat[1][1], 0], [0, 0, 1]])
	translationMat3d = np.array([[1, 0, d[0]], [0, 1, d[1]], [0, 0, 1]])
	
	tmpTransformation = np.matmul(rotMat3d, transformation)
	tmpTransformation = np.matmul(translationMat3d, tmpTransformation)
	
	for tmp in pcd2.points:
		newx = c*tmp[0]
		newy = c*tmp[1]
		
		newxrot = rotMat[0][0]*newx+rotMat[0][1]*newy
		newyrot = rotMat[1][0]*newx+rotMat[1][1]*newy
		
		newx = newxrot+d[0]
		newy = newyrot+d[1]
		
		tmp[0]=newx
		tmp[1]=newy
	
	return tmpTransformation


def planeToPlaneICPTwoAtOnce(segmentDatMain1, segmentDatOther1, segmentDatMain2, segmentDatOther2, max_iterations, maxPairingToSamePtAmount, segmentDatMainSubset1=None, segmentDatOtherSubset1=None, segmentDatMainSubset2=None, segmentDatOtherSubset2=None, dontSwap=False, bothOtherPlanesAreSame=False, params=None, swapOtherMain=False):
	maxPairingToSamePtAmount=params['maxPairingToSamePtAmount']
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	if swapOtherMain:
		segmentDatMain2, segmentDatOther2 = segmentDatOther2, segmentDatMain2
		segmentDatMainSubset2, segmentDatOtherSubset2 = segmentDatOtherSubset2, segmentDatMainSubset2
	
	
	if len(segmentDatMain1)==0 or len(segmentDatMain1[0])==0:# or len(segmentDatMain1[1])==0:
		return None, None
	if len(segmentDatOther1)==0 or len(segmentDatOther1[0])==0:# or len(segmentDatOther1[1])==0:
		return None, None
	if len(segmentDatMain2)==0 or len(segmentDatMain2[0])==0:# or len(segmentDatMain2[1])==0:
		return None, None
	if len(segmentDatOther2)==0 or len(segmentDatOther2[0])==0:# or len(segmentDatOther2[1])==0:
		return None, None
	
	discardBadTransformation = params['discardBadTransformation'] # REMEMBER, THESE ARE JUST TO RULE OUT OBVIOUS HAYWIRE TRANSLATIONS, IF THIS WAS FOR DECIDING IF ITS AN ACTUAL MATCH, THE THRESHOLDS WOULD BE AT LEAST LIKE 50% MORE STRICT
	maxScaleDiffICP = params['maxScaleDiffICP'] # like 0.3 or something
	maxTranslationAsRatioOfAvgDistBetweenPlanesSegmentsPoints = params['maxTranslationAsRatioOfAvgDistBetweenPlanesSegmentsPoints'] # like 7?
	maxRotationICP = params['maxRotationICP'] # like 30 degrees?
	
	tmpTrackingP1 = (segmentDatOther1[0][0][0], segmentDatOther1[0][0][1])
	tmpTrackingP2 = (segmentDatOther1[-1][-1][0], segmentDatOther1[-1][-1][1])
	
	tmpTrackingP1b = (segmentDatOther2[0][0][0], segmentDatOther2[0][0][1])
	tmpTrackingP2b = (segmentDatOther2[-1][-1][0], segmentDatOther2[-1][-1][1])
	
	endingPtsInds1 = set()
	breakingPointsIndsBefore1 = set()
	
	rowsN = 0
	if segmentDatMainSubset1 is None:
		for segmentDat in segmentDatMain1:
			if len(segmentDat)>0:
				endingPtsInds1.add(rowsN)
				
				rowsN+=len(segmentDat)
				breakingPointsIndsBefore1.add(rowsN-1)
				endingPtsInds1.add(rowsN-1)
				
	else:
		for segmentDatIndStuff in segmentDatMainSubset1:
			segmentDat = segmentDatMain1[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				endingPtsInds1.add(rowsN)
				rowsN+=coordDatInterval[1]-coordDatInterval[0]+1
				breakingPointsIndsBefore1.add(rowsN-1)
				endingPtsInds1.add(rowsN-1)
		
	
	mainPts1 = np.empty([rowsN, 2])
	rowCtr = 0
	if segmentDatMainSubset1 is None:
		for segmentDat in segmentDatMain1:
			for coordDat in segmentDat:
				mainPts1[rowCtr][0]=coordDat[0]
				mainPts1[rowCtr][1]=coordDat[1]
				rowCtr+=1
	else:
		for segmentDatIndStuff in segmentDatMainSubset1:
			segmentDat = segmentDatMain1[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				for coordDatInd in range(coordDatInterval[0], coordDatInterval[1]+1):
					coordDat = segmentDat[coordDatInd]
					mainPts1[rowCtr][0]=coordDat[0]
					mainPts1[rowCtr][1]=coordDat[1]
					rowCtr+=1
		
	if rowCtr != rowsN:
		print("??? 12oi2ij2edd")
		exit()
	
	main_tree1 = cKDTree(mainPts1)
	
	transformation1 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
	
	endingPtsInds2 = set()
	breakingPointsIndsBefore2 = set()
	
	rowsN = 0
	if segmentDatMainSubset2 is None:
		for segmentDat in segmentDatMain2:
			if len(segmentDat)>0:
				endingPtsInds2.add(rowsN)
				
				rowsN+=len(segmentDat)
				breakingPointsIndsBefore2.add(rowsN-1)
				endingPtsInds2.add(rowsN-1)
				
	else:
		for segmentDatIndStuff in segmentDatMainSubset2:
			segmentDat = segmentDatMain2[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				endingPtsInds2.add(rowsN)
				rowsN+=coordDatInterval[1]-coordDatInterval[0]+1
				breakingPointsIndsBefore2.add(rowsN-1)
				endingPtsInds2.add(rowsN-1)
		
	
	mainPts2 = np.empty([rowsN, 2])
	rowCtr = 0
	if segmentDatMainSubset2 is None:
		for segmentDat in segmentDatMain2:
			for coordDat in segmentDat:
				mainPts2[rowCtr][0]=coordDat[0]
				mainPts2[rowCtr][1]=coordDat[1]
				rowCtr+=1
	else:
		for segmentDatIndStuff in segmentDatMainSubset2:
			segmentDat = segmentDatMain2[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				for coordDatInd in range(coordDatInterval[0], coordDatInterval[1]+1):
					coordDat = segmentDat[coordDatInd]
					mainPts2[rowCtr][0]=coordDat[0]
					mainPts2[rowCtr][1]=coordDat[1]
					rowCtr+=1
		
	
	if rowCtr != rowsN:
		print("??? 12oi2ij2edd")
		exit()
	
	main_tree2 = cKDTree(mainPts2)
	
	transformation2 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
	
	terriblecoderowsN = rowsN
	
	correspondences=None # so last iteration one is stored
	prevAvgDist=None
	for k in range(max_iterations):
		correspondences1 = []
		correspondencesTrackerDict1 = {}
		
		correspondences1 = getCorrespondencesPlaneToPlane(correspondences1, correspondencesTrackerDict1, endingPtsInds1, breakingPointsIndsBefore1, maxPairingToSamePtAmount, segmentDatOther1, mainPts1, main_tree1, segmentDatMainSubset1, segmentDatOtherSubset1, params=params)
		
		correspondences2 = []
		correspondencesTrackerDict2 = {}
		
		correspondences2 = getCorrespondencesPlaneToPlane(correspondences2, correspondencesTrackerDict2, endingPtsInds2, breakingPointsIndsBefore2, maxPairingToSamePtAmount, segmentDatOther2, mainPts2, main_tree2, segmentDatMainSubset2, segmentDatOtherSubset2, params=params)
		
		inefficientCbaSet = set()
		
		correspondences=[]
		for correspondenceTmp in correspondences1:
			if bothOtherPlanesAreSame: # very inefficient, for each correspondence1 check if exists in correspondences2 and if so, and if its closer than the pairing in corr2, add to main corr list and add corr2 index to set so know to skip in next loop
				for correspondenceTmp2I in range(len(correspondences2)):
					correspondenceTmp2 = correspondences2[correspondenceTmp2I]
					if correspondenceTmp2[0][0]==correspondenceTmp[0][0] and correspondenceTmp2[0][1]==correspondenceTmp[0][1]:
						if correspondenceTmp[5]<correspondenceTmp2[5]:
							correspondences.append(correspondenceTmp)
							inefficientCbaSet.add(correspondenceTmp2I)
						
						break
			else:
				correspondences.append(correspondenceTmp)
		for correspondenceTmpI, correspondenceTmp in enumerate(correspondences2):
			if dontSwap:
				if not(bothOtherPlanesAreSame) or (bothOtherPlanesAreSame and (correspondenceTmpI not in inefficientCbaSet)):
					correspondences.append(correspondenceTmp)
			else:
				if not(bothOtherPlanesAreSame) or (bothOtherPlanesAreSame and (correspondenceTmpI not in inefficientCbaSet)):
					correspondences.append((correspondenceTmp[1], correspondenceTmp[0], correspondenceTmp[2], correspondenceTmp[3], correspondenceTmp[4], correspondenceTmp[5])) # the points in the first pairing need to be in same position since theyre treated as a single object and vice versa
		if len(correspondences)>0:
			c, d, rotMat = estimateSimilarityTransform(correspondences)
			if c is None:
				return None, None
		else:
			return None, None
		if bothOtherPlanesAreSame:
			transformation1 = transformCustPlaneToPlane(segmentDatOther1, c, rotMat, d, transformation1)
		else: 
			
			transformation1 = transformCustPlaneToPlane(segmentDatOther1, c, rotMat, d, transformation1)
			transformation2 = transformCustPlaneToPlane(segmentDatOther2, c, rotMat, d, transformation2)
			# both transformations the same but just keeping seperate to clearly show segmentDatOther1 and segmentDatMain2 being transformed the same
			
		currAvgDist=0
		for tmpCorres in correspondences:
			currAvgDist+=tmpCorres[5]
		currAvgDist=currAvgDist/len(correspondences)
		if currAvgDist==prevAvgDist:
			break
		prevAvgDist=currAvgDist
	
	# NOT ACTUALLY DOING TRANSLATION CAUSE NOT SURE IF ITS WELL DEFINED CAUSE OF SCALING AND ROTATION
	if discardBadTransformation and (tmpTrackingP1[0]!=tmpTrackingP2[0] or tmpTrackingP1[1]!=tmpTrackingP2[1]):
		tmpTrackingP1AfterTransformation = (segmentDatOther1[0][0][0], segmentDatOther1[0][0][1])
		tmpTrackingP2AfterTransformation = (segmentDatOther1[-1][-1][0], segmentDatOther1[-1][-1][1])
		
		tmpDistBefore = getDistance(tmpTrackingP1[0], tmpTrackingP2[0], tmpTrackingP1[1], tmpTrackingP2[1])
		tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
		
		tmpScale = tmpDistAfter/tmpDistBefore
		
		if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
			return None, None
		
		tmpRotation = math.atan2(tmpTrackingP2AfterTransformation[1]-tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[0]-tmpTrackingP1AfterTransformation[0]) - math.atan2(tmpTrackingP2[1]-tmpTrackingP1[1], tmpTrackingP2[0]-tmpTrackingP1[0])
		
		if tmpRotation<=-math.pi:
			tmpRotation+=2*math.pi
		if tmpRotation>math.pi:
			tmpRotation-=2*math.pi
		if tmpRotation<-maxRotationICP or tmpRotation>maxRotationICP:
			return None, None
		
	if discardBadTransformation and (tmpTrackingP1b[0]!=tmpTrackingP2b[0] or tmpTrackingP1b[1]!=tmpTrackingP2b[1]):
		tmpTrackingP1AfterTransformation = (segmentDatOther2[0][0][0], segmentDatOther2[0][0][1])
		tmpTrackingP2AfterTransformation = (segmentDatOther2[-1][-1][0], segmentDatOther2[-1][-1][1])
		
		tmpDistBefore = getDistance(tmpTrackingP1b[0], tmpTrackingP2b[0], tmpTrackingP1b[1], tmpTrackingP2b[1])
		tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
		
		tmpScale = tmpDistAfter/tmpDistBefore
		
		if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
			return None, None
		
		tmpRotation = math.atan2(tmpTrackingP2AfterTransformation[1]-tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[0]-tmpTrackingP1AfterTransformation[0]) - math.atan2(tmpTrackingP2b[1]-tmpTrackingP1b[1], tmpTrackingP2b[0]-tmpTrackingP1b[0])
		
		if tmpRotation<=-math.pi:
			tmpRotation+=2*math.pi
		if tmpRotation>math.pi:
			tmpRotation-=2*math.pi
		if tmpRotation<-maxRotationICP or tmpRotation>maxRotationICP:
			return None, None
	
	return transformation1, correspondences




def planeToPlaneICP(segmentDatMain, segmentDatOther, max_iterations, maxPairingToSamePtAmount, segmentDatMainSubset=None, segmentDatOtherSubset=None, params=None):
	global globt1
	globt1=0
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	if len(segmentDatMain)==0 or len(segmentDatMain[0])==0:# or len(segmentDatMain[1])==0:
		print("ptpicp1")
		return None, None, [0]
	if len(segmentDatOther)==0 or len(segmentDatOther[0])==0:# or len(segmentDatOther[1])==0:
		print("ptpicp2")
		return None, None, [0]
	
	tdat=[]
	tmptimer1=0
	
	maxPairingToSamePtAmount=params['maxPairingToSamePtAmount']
	
	discardBadTransformation = params['discardBadTransformation'] # REMEMBER, THESE ARE JUST TO RULE OUT OBVIOUS HAYWIRE TRANSLATIONS, IF THIS WAS FOR DECIDING IF ITS AN ACTUAL MATCH, THE THRESHOLDS WOULD BE AT LEAST LIKE 50% MORE STRICT
	maxScaleDiffICP = params['maxScaleDiffICP'] # like 0.3 or something
	maxTranslationAsRatioOfAvgDistBetweenPlanesSegmentsPoints = params['maxTranslationAsRatioOfAvgDistBetweenPlanesSegmentsPoints'] # like 7?
	maxRotationICP = params['maxRotationICP'] # like 30 degrees?
	
	tmpTrackingP1 = (segmentDatOther[0][0][0], segmentDatOther[0][0][1])
	tmpTrackingP2 = (segmentDatOther[-1][-1][0], segmentDatOther[-1][-1][1])
	
	endingPtsInds = set()
	breakingPointsIndsBefore = set()
	
	rowsN = 0
	if segmentDatMainSubset is None:
		for segmentDat in segmentDatMain:
			if len(segmentDat)>0:
				endingPtsInds.add(rowsN)
				
				rowsN+=len(segmentDat)
				breakingPointsIndsBefore.add(rowsN-1)
				endingPtsInds.add(rowsN-1)
				
	else:
		for segmentDatIndStuff in segmentDatMainSubset:
			segmentDat = segmentDatMain[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				endingPtsInds.add(rowsN)
				rowsN+=coordDatInterval[1]-coordDatInterval[0]+1
				breakingPointsIndsBefore.add(rowsN-1)
				endingPtsInds.add(rowsN-1)
		
	mainPts = np.empty([rowsN, 2])
	rowCtr = 0
	if segmentDatMainSubset is None:
		for segmentDat in segmentDatMain:
			for coordDat in segmentDat:
				mainPts[rowCtr][0]=coordDat[0]
				mainPts[rowCtr][1]=coordDat[1]
				rowCtr+=1
	else:
		for segmentDatIndStuff in segmentDatMainSubset:
			segmentDat = segmentDatMain[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				for coordDatInd in range(coordDatInterval[0], coordDatInterval[1]+1):
					coordDat = segmentDat[coordDatInd]
					mainPts[rowCtr][0]=coordDat[0]
					mainPts[rowCtr][1]=coordDat[1]
					rowCtr+=1
		
	if rowCtr != rowsN:
		print("??? 12oi2ij2edd")
		exit()
	if len(mainPts)==0:
		print("ptpicp3")
		return None, None, [0]
	main_tree = cKDTree(mainPts)
	
	transformation = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
	
	correspondences=None # so last iteration one is stored
	prevAvgDist=None
	for k in range(max_iterations):
		correspondences = []
		correspondencesTrackerDict = {}
		
		correspondences = getCorrespondencesPlaneToPlane(correspondences, correspondencesTrackerDict, endingPtsInds, breakingPointsIndsBefore, maxPairingToSamePtAmount, segmentDatOther, mainPts, main_tree, segmentDatMainSubset, segmentDatOtherSubset, params=params)
		
		if len(correspondences)>0:
			
			c, d, rotMat = estimateSimilarityTransform(correspondences)
			
			if c is None:
				# print("123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 123 ")
				return None, None, [0]
		else:
			# print("-----")
			# print(segmentDatMain)
			# print(segmentDatOther)
			# print(" 555 777   555 777   555 777   555 777   555 777   555 777   555 777   555 777   555 777   555 777  ")
			return None, None, [0]
		
		transformation = transformCustPlaneToPlane(segmentDatOther, c, rotMat, d, transformation)
		
		currAvgDist=0
		for tmpCorres in correspondences:
			currAvgDist+=tmpCorres[5]
		currAvgDist = currAvgDist/len(correspondences)
		
		if currAvgDist==prevAvgDist:
			break
		prevAvgDist=currAvgDist
		
		
		# just checking scale after each loop transformation in case its immediately obvious that its bad, leaving rotation check for outside the loop
		# adding k>2 just incase first loop attaches badly then 1-2 more loops brings scale back to normal range
		if k>2 and discardBadTransformation and (tmpTrackingP1[0]!=tmpTrackingP2[0] or tmpTrackingP1[1]!=tmpTrackingP2[1]):
			tmpTrackingP1AfterTransformation = (segmentDatOther[0][0][0], segmentDatOther[0][0][1])
			tmpTrackingP2AfterTransformation = (segmentDatOther[-1][-1][0], segmentDatOther[-1][-1][1])
			
			tmpDistBefore = getDistance(tmpTrackingP1[0], tmpTrackingP2[0], tmpTrackingP1[1], tmpTrackingP2[1])
			tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
			
			tmpScale = tmpDistAfter/tmpDistBefore
			
			if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
				tdat.append(globt1)
				print("ptpicp4b")
				return None, None, tdat
	
	tdat.append(globt1)
	
	# NOT ACTUALLY DOING TRANSLATION CAUSE NOT SURE IF ITS WELL DEFINED CAUSE OF SCALING AND ROTATION
	if discardBadTransformation and (tmpTrackingP1[0]!=tmpTrackingP2[0] or tmpTrackingP1[1]!=tmpTrackingP2[1]):
		tmpTrackingP1AfterTransformation = (segmentDatOther[0][0][0], segmentDatOther[0][0][1])
		tmpTrackingP2AfterTransformation = (segmentDatOther[-1][-1][0], segmentDatOther[-1][-1][1])
		
		tmpDistBefore = getDistance(tmpTrackingP1[0], tmpTrackingP2[0], tmpTrackingP1[1], tmpTrackingP2[1])
		tmpDistAfter = getDistance(tmpTrackingP1AfterTransformation[0], tmpTrackingP2AfterTransformation[0], tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[1])
		
		tmpScale = tmpDistAfter/tmpDistBefore
		
		if tmpScale>1+maxScaleDiffICP or tmpScale<1-maxScaleDiffICP:
			print("ptpicp4")
			return None, None, tdat
		
		tmpRotation = math.atan2(tmpTrackingP2AfterTransformation[1]-tmpTrackingP1AfterTransformation[1], tmpTrackingP2AfterTransformation[0]-tmpTrackingP1AfterTransformation[0]) - math.atan2(tmpTrackingP2[1]-tmpTrackingP1[1], tmpTrackingP2[0]-tmpTrackingP1[0])
		
		if tmpRotation<=-math.pi:
			tmpRotation+=2*math.pi
		if tmpRotation>math.pi:
			tmpRotation-=2*math.pi
		if tmpRotation<-maxRotationICP or tmpRotation>maxRotationICP:
			print("ptpicp5")
			return None, None, tdat
		
	return transformation, correspondences, tdat


def inefficientCorrespondenceAreas(segDat1, segDat2, maxPairingToSamePtAmount, segmentDatMainSubset=None, segmentDatOtherSubset=None, params=None):
	maxPairingToSamePtAmount=params['maxPairingToSamePtAmount']
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	minPtsForArea = 2 # if theres only 1 isolated unpaired point, could just be noise
	
	endingPtsInds = set()
	breakingPointsIndsBefore = set()
	
	rowsN = 0
	
	if segmentDatMainSubset is not None or segmentDatOtherSubset is not None:
		print("yikes alert in customicp.py")
		exit()
	
	if segmentDatMainSubset is None:
		for segmentDat in segDat1:
			if len(segmentDat)>0:
				endingPtsInds.add(rowsN)
				rowsN+=len(segmentDat)
				breakingPointsIndsBefore.add(rowsN-1)
				endingPtsInds.add(rowsN-1)
	else:
		for segmentDatIndStuff in segmentDatMainSubset:
			segmentDat = segDat1[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				endingPtsInds.add(rowsN)
				rowsN+=coordDatInterval[1]-coordDatInterval[0]+1
				breakingPointsIndsBefore.add(rowsN-1)
				endingPtsInds.add(rowsN-1)
	
	mainPts = np.empty([rowsN, 2])
	rowCtr = 0
	
	if segmentDatMainSubset is None:
		for segmentDat in segDat1:
			for coordDat in segmentDat:
				mainPts[rowCtr][0]=coordDat[0]
				mainPts[rowCtr][1]=coordDat[1]
				rowCtr+=1
	else:
		for segmentDatIndStuff in segmentDatMainSubset:
			segmentDat = segDat1[segmentDatIndStuff[0]]
			for coordDatInterval in segmentDatIndStuff[1]:
				for coordDatInd in range(coordDatInterval[0], coordDatInterval[1]+1):
					coordDat = segmentDat[coordDatInd]
					mainPts[rowCtr][0]=coordDat[0]
					mainPts[rowCtr][1]=coordDat[1]
					rowCtr+=1
	if rowCtr != rowsN:
		print("??? 12oi2i13j2edd")
		exit()
	
	main_tree = cKDTree(mainPts)
	
	correspondences = []
	correspondencesTrackerDict = {}
	
	correspondences = getCorrespondencesPlaneToPlaneInefficient(correspondences, correspondencesTrackerDict, endingPtsInds, breakingPointsIndsBefore, maxPairingToSamePtAmount, segDat2, mainPts, main_tree, params=params)
	
	# below is just grouping stuff back together in order, because there are cases where (if enforcing max pairings per 1 mainPoint for example) even though i iterate otherEdge data in order, sometimes i replace an earlier correspondence with a new one if the new one is closer
	# ^^ I THINK, might be wrong...
	
	segGroupedDict = {}
	for correspondence in correspondences:
		if correspondence[2] not in segGroupedDict:
			segGroupedDict[correspondence[2]]=[correspondence[3]]
		else:
			segGroupedDict[correspondence[2]].append(correspondence[3])
	for key in segGroupedDict:
		segGroupedDict[key].sort()
	assumedUnPairedAreasIntervalsSegDat1 = []
	for i in range(len(segDat2)):
		tmpSegList = [i, []]
		if i not in segGroupedDict:
			tmpSegList[1].append((0, len(segDat2[i])-1))
		else:
			if segGroupedDict[i][0]!=0:
				if segGroupedDict[i][0]-1-0 >= minPtsForArea-1:
					tmpSegList[1].append((0, segGroupedDict[i][0]-1))
			prevInd = segGroupedDict[i][0]
			for tmpI in range(1, len(segGroupedDict[i])):
				currInd=segGroupedDict[i][tmpI]
				if currInd!=prevInd+1:
					if currInd-1 - (prevInd+1) >= minPtsForArea-1:
						tmpSegList[1].append((prevInd+1, currInd-1))
				prevInd=currInd
			if segGroupedDict[i][-1]!=len(segDat2[i])-1:
				if len(segDat2[i])-1 - (segGroupedDict[i][-1]+1) >= minPtsForArea-1:
					tmpSegList[1].append((segGroupedDict[i][-1]+1, len(segDat2[i])-1))
		if len(tmpSegList[1])>0:
			assumedUnPairedAreasIntervalsSegDat1.append(tmpSegList)
	
	return assumedUnPairedAreasIntervalsSegDat1

def getCorrespondencesPlaneToPlaneInefficient(correspondences, correspondencesTrackerDict, endingPtsInds, breakingPointsIndsBefore, maxPairingToSamePtAmount, segDat2, mainPts, main_tree, segmentDat1Subset=None, segmentDat2Subset=None, params=None): # can have paramsOverride if want different behaviour for different edgePair scenarios
	maxPairingToSamePtAmount=params['maxPairingToSamePtAmount']
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	enforceOnlyPairingToPoints = params['enforceOnlyPairingToPoints'] # if True, only pair to points in mainEdge, NOT on lineSeg between pts (which is usually where the real closest pt lies)
	enforceMaxCorrespondenceDist = params['enforceMaxCorrespondenceDist']
	
	enforceMonotony = params['enforceMonotony']
	
	avgDistBetweenPtsOtherEdge = 0 # this is the edge being transformed, choosing to use this edge rather than main or a combination of main and other because in most cases this is the edge that will be over-shrinked so this will combat that a bit since this will also shrink
	sampleDistBetweenPtsAmt = 0
	maxCorrespondenceDist = None
	if enforceMaxCorrespondenceDist:
		for segmentDat in segDat2:
			if len(segmentDat)>=2:
				tmpDist = getDistance(segmentDat[0][0], segmentDat[1][0], segmentDat[0][1], segmentDat[1][1])
				avgDistBetweenPtsOtherEdge+=tmpDist
				sampleDistBetweenPtsAmt+=1
			if sampleDistBetweenPtsAmt>3: # just doing like first 4 segments, dont need much of an average here
				break
		if sampleDistBetweenPtsAmt!=0:
			avgDistBetweenPtsOtherEdge=avgDistBetweenPtsOtherEdge/sampleDistBetweenPtsAmt
			maxCorrespondenceDist = avgDistBetweenPtsOtherEdge*params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPointsJustForInefficientCorrespondenceAreas'] # like 3 or 4 seems to work in tests
		if maxCorrespondenceDist is None:
			print("weird stuff happening with max correspondence dist, just set to not use it as backup routine")
			exit()
			enforceMaxCorrespondenceDist=False
	
	onlyEnforceMaxCorrespondencesForEndings = True
	segDat2Iter=None
	if segmentDat2Subset is not None:
		segDat2Iter=range(len(segmentDat2Subset))
	else:
		segDat2Iter=range(len(segDat2))
	for i in segDat2Iter:
		segDatI=None
		segmentDat=None
		if segmentDat2Subset is not None:
			segDatI=segmentDat2Subset[i][0]
			segmentDat=segDat2[segDatI]
		else:
			segDatI=i
			segmentDat=segDat2[segDatI]
		coordIntervalIter = None
		if segmentDat2Subset is not None:
			coordIntervalIter = range(len(segmentDat2Subset[i][1]))
		else:
			coordIntervalIter = range(1)
		for p in coordIntervalIter:
			coordIter = None
			if segmentDat2Subset is not None:
				coordInterval = segmentDat2Subset[i][1][p]
				coordIter = range(coordInterval[0], coordInterval[1]+1)
			else:
				coordIter = range(len(segmentDat))
			for j in coordIter:
				coordDat=segmentDat[j]
				point=coordDat
				dd, idx = main_tree.query([point], k=1)
				closestPt = [mainPts[idx[0]][0], mainPts[idx[0]][1]]
				closestPointIntegerIndex = idx[0]
				closerPtIndAsRatio = None
				closestPtIndAsRatio = idx[0]
				closerPt=None
				if not(enforceOnlyPairingToPoints):
					if idx[0]<mainPts.shape[0]-1 and idx[0] not in breakingPointsIndsBefore:
						closerPt, closerPtIndAsRatio = closestPtToLineSeg(closestPt, [mainPts[idx[0]+1][0], mainPts[idx[0]+1][1]], point, idx[0])
					if closerPt is None:
						if idx[0]>0 and idx[0]-1 not in breakingPointsIndsBefore:
							closerPt, closerPtIndAsRatio = closestPtToLineSeg([mainPts[idx[0]-1][0], mainPts[idx[0]-1][1]], closestPt, point, idx[0]-1)
					if closerPt is not None: # closestPt is now on lineSeg between 2 vertices, odds of multiple correspondences sharing this point is insanely low so going to disregard this case for speed
						closestPt=closerPt
						closestPointIntegerIndex=None
						closestPtIndAsRatio = closerPtIndAsRatio
					
				tmpDist = getDistance(closestPt[0], point[0], closestPt[1], point[1])
				if enforceMaxCorrespondenceDist and tmpDist<=maxCorrespondenceDist or not(enforceMaxCorrespondenceDist):
					if closestPointIntegerIndex is None:
						correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
					else:
						if idx[0] in correspondencesTrackerDict:
							
							# changing to only apply max many-to-one pairings to the endings
							closestPointIsAnEnding = False
							
							if idx[0] in endingPtsInds:
								closestPointIsAnEnding=True
							
							if (closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings)) and len(correspondencesTrackerDict[idx[0]])>=maxPairingToSamePtAmount:
								
								if tmpDist<correspondencesTrackerDict[idx[0]][0][0]:
									correspondences[correspondencesTrackerDict[idx[0]][0][1]]=(point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist)
									correspondencesTrackerDict[idx[0]][0]=(tmpDist, correspondencesTrackerDict[idx[0]][0][1])
									correspondencesTrackerDict[idx[0]].sort()
							elif (closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings)):
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
								correspondencesTrackerDict[idx[0]].append((tmpDist, len(correspondences)-1))
								correspondencesTrackerDict[idx[0]].sort()
							else: # onlyEnforceMaxCorrespondencesForEndings and this isnt an ending
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
						else:
							closestPointIsAnEnding = False
							
							if idx[0] in endingPtsInds:
								closestPointIsAnEnding=True
							if closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings):
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
								correspondencesTrackerDict[idx[0]]=[(tmpDist, len(correspondences)-1)]
							else:
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
						
	if enforceMonotony:
		newCorrespondences = []
		atLeastOne = False
		consecutiveAmt=0
		for i in range(len(correspondences)-1):
			if correspondences[i+1][4]<correspondences[i][4]: # mainEdge indAsRatio decreasing
				prevCorrSegI = correspondences[i][2]
				prevCorrCoordI = correspondences[i][3]
				currCorrSegI = correspondences[i+1][2]
				currCorrCoordI = correspondences[i+1][3]
				if currCorrSegI>prevCorrSegI or (currCorrSegI==prevCorrSegI and currCorrCoordI>prevCorrSegI): # otherEdge inds increasing
					consecutiveAmt+=1
				else:
					consecutiveAmt=0
			else:
				consecutiveAmt=0
			if consecutiveAmt>=2:
				atLeastOne=True
				break
		
		if atLeastOne:
			i=0
			while i<len(correspondences)-1:
				if correspondences[i+1][4]<correspondences[i][4]: # mainEdge indAsRatio decreasing
					prevCorrSegI = correspondences[i][2]
					prevCorrCoordI = correspondences[i][3]
					currCorrSegI = correspondences[i+1][2]
					currCorrCoordI = correspondences[i+1][3]
					if currCorrSegI>prevCorrSegI or (currCorrSegI==prevCorrSegI and currCorrCoordI>prevCorrSegI): # otherEdge inds increasing
						consecutiveAmt+=1
					else:
						if consecutiveAmt>0:
							i+=1 # skip one otherwise i'd be adding a decreasing one
						consecutiveAmt=0
				else:
					if consecutiveAmt>0:
						i+=1 # skip one otherwise i'd be adding a decreasing one
					consecutiveAmt=0
				if consecutiveAmt<=1:
					newCorrespondences.append(correspondences[i])
				i+=1
			correspondences = newCorrespondences
		
	return correspondences


def transformCustPlaneToPlane(segmentDatOther, c, rotMat, d, transformation):
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	rotMat3d = np.array([[c*rotMat[0][0], c*rotMat[0][1], 0], [c*rotMat[1][0], c*rotMat[1][1], 0], [0, 0, 1]])
	translationMat3d = np.array([[1, 0, d[0]], [0, 1, d[1]], [0, 0, 1]])
	tmpTransformation = np.matmul(rotMat3d, transformation)
	tmpTransformation = np.matmul(translationMat3d, tmpTransformation)
	
	for segmentDat in segmentDatOther:
		for coordDat in segmentDat:
			tmp = coordDat
			newx = c*tmp[0]
			newy = c*tmp[1]
			
			newxrot = rotMat[0][0]*newx+rotMat[0][1]*newy
			newyrot = rotMat[1][0]*newx+rotMat[1][1]*newy
			
			newx = newxrot+d[0]
			newy = newyrot+d[1]
			
			coordDat[0]=newx
			coordDat[1]=newy
			
	return tmpTransformation


globt1=0
def getCorrespondencesPlaneToPlane(correspondences, correspondencesTrackerDict, endingPtsInds, breakingPointsIndsBefore, maxPairingToSamePtAmount, segmentDatOther, mainPts, main_tree, segmentDatMainSubset=None, segmentDatOtherSubset=None, params=None): # can have paramsOverride if want different behaviour for different edgePair scenarios
	global globt1
	# SEGMENT DAT IS ACTUALLY PLANESSEGMENTS, NO COORDDAT, JUST COORDS !@!@!@!@!!!@@!@!@!@!@
	
	maxPairingToSamePtAmount=params['maxPairingToSamePtAmount']
	
	enforceOnlyPairingToPoints = params['enforceOnlyPairingToPoints'] # if True, only pair to points in mainEdge, NOT on lineSeg between pts (which is usually where the real closest pt lies)
	enforceMaxCorrespondenceDist = params['enforceMaxCorrespondenceDist']
	
	enforceMonotony = params['enforceMonotony']
	
	avgDistBetweenPtsOtherEdge = 0 # this is the edge being transformed, choosing to use this edge rather than main or a combination of main and other because in most cases this is the edge that will be over-shrinked so this will combat that a bit since this will also shrink
	sampleDistBetweenPtsAmt = 0
	maxCorrespondenceDist = None
	if enforceMaxCorrespondenceDist:
		for segmentDat in segmentDatOther:
			if len(segmentDat)>=2:
				tmpDist = getDistance(segmentDat[0][0], segmentDat[1][0], segmentDat[0][1], segmentDat[1][1])
				avgDistBetweenPtsOtherEdge+=tmpDist
				sampleDistBetweenPtsAmt+=1
			if sampleDistBetweenPtsAmt>3: # just doing like first 4 segments, dont need much of an average here
				break
		if sampleDistBetweenPtsAmt!=0:
			avgDistBetweenPtsOtherEdge=avgDistBetweenPtsOtherEdge/sampleDistBetweenPtsAmt
			maxCorrespondenceDist = avgDistBetweenPtsOtherEdge*params['maxCorrespondenceDistRatioOfAvgDistBetweenSegmentDatPoints'] # like 3 or 4 seems to work in tests
		if maxCorrespondenceDist is None:
			print("weird stuff happening with max correspondence dist, just set to not use it as backup routine")
			enforceMaxCorrespondenceDist=False
			exit()
	
	onlyEnforceMaxCorrespondencesForEndings = True
	
	segDatOtherIter=None
	if segmentDatOtherSubset is not None:
		segDatOtherIter=range(len(segmentDatOtherSubset))
	else:
		segDatOtherIter=range(len(segmentDatOther))
	
	for i in segDatOtherIter:
		segDatI=None
		segmentDat=None
		if segmentDatOtherSubset is not None:
			segDatI=segmentDatOtherSubset[i][0]
			segmentDat=segmentDatOther[segDatI]
		else:
			segDatI=i
			segmentDat=segmentDatOther[segDatI]
		coordIntervalIter = None
		if segmentDatOtherSubset is not None:
			coordIntervalIter = range(len(segmentDatOtherSubset[i][1]))
		else:
			coordIntervalIter = range(1)
		for p in coordIntervalIter:
			coordIter = None
			if segmentDatOtherSubset is not None:
				coordInterval = segmentDatOtherSubset[i][1][p]
				coordIter = range(coordInterval[0], coordInterval[1]+1)
			else:
				coordIter = range(len(segmentDat))
			for j in coordIter:
				coordDat=segmentDat[j]
				point=coordDat
				
				ticTemp = time.perf_counter()
				dd, idx = main_tree.query([point], k=1)
				tocTemp = time.perf_counter()
				globt1+=tocTemp-ticTemp
				
				closestPt = [mainPts[idx[0]][0], mainPts[idx[0]][1]]
				closestPointIntegerIndex = idx[0]
				closerPtIndAsRatio = None
				closestPtIndAsRatio = idx[0]
				closerPt=None
				
				if not(enforceOnlyPairingToPoints):
					if idx[0]<mainPts.shape[0]-1 and idx[0] not in breakingPointsIndsBefore:
						closerPt, closerPtIndAsRatio = closestPtToLineSeg(closestPt, [mainPts[idx[0]+1][0], mainPts[idx[0]+1][1]], point, idx[0])
					if closerPt is None:
						if idx[0]>0 and idx[0]-1 not in breakingPointsIndsBefore:
							closerPt, closerPtIndAsRatio = closestPtToLineSeg([mainPts[idx[0]-1][0], mainPts[idx[0]-1][1]], closestPt, point, idx[0]-1)
					if closerPt is not None: # closestPt is now on lineSeg between 2 vertices, odds of multiple correspondences sharing this point is insanely low so going to disregard this case for speed
						closestPt=closerPt
						closestPointIntegerIndex=None
						closestPtIndAsRatio=closerPtIndAsRatio
					
				tmpDist = getDistance(closestPt[0], point[0], closestPt[1], point[1])
				if enforceMaxCorrespondenceDist and tmpDist<=maxCorrespondenceDist or not(enforceMaxCorrespondenceDist):
					if closestPointIntegerIndex is None:
						correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
					else:
						if idx[0] in correspondencesTrackerDict:
							
							# changing to only apply max many-to-one pairings to the endings
							closestPointIsAnEnding = False
							
							if idx[0] in endingPtsInds:
								closestPointIsAnEnding=True
							if (closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings)) and len(correspondencesTrackerDict[idx[0]])>=maxPairingToSamePtAmount:
								if tmpDist<correspondencesTrackerDict[idx[0]][0][0]:
									correspondences[correspondencesTrackerDict[idx[0]][0][1]]=(point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist)
									correspondencesTrackerDict[idx[0]][0]=(tmpDist, correspondencesTrackerDict[idx[0]][0][1])
									correspondencesTrackerDict[idx[0]].sort()
							elif (closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings)):
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
								correspondencesTrackerDict[idx[0]].append((tmpDist, len(correspondences)-1))
								correspondencesTrackerDict[idx[0]].sort()
							else: # onlyEnforceMaxCorrespondencesForEndings and this isnt an ending
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
						else:
							closestPointIsAnEnding = False
							
							if idx[0] in endingPtsInds:
								closestPointIsAnEnding=True
							if closestPointIsAnEnding or not(onlyEnforceMaxCorrespondencesForEndings): # if closestPointIsAnEnding, this happens regardless of if onlyEnforceMaxCorrespondencesForEndings
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
								correspondencesTrackerDict[idx[0]]=[(tmpDist, len(correspondences)-1)]
							else:
								correspondences.append((point, closestPt, segDatI, j, closestPtIndAsRatio, tmpDist))
	
	if enforceMonotony:
		newCorrespondences = []
		atLeastOne = False
		consecutiveAmt=0
		for i in range(len(correspondences)-1):
			if correspondences[i+1][4]<correspondences[i][4]: # mainEdge indAsRatio decreasing
				prevCorrSegI = correspondences[i][2]
				prevCorrCoordI = correspondences[i][3]
				currCorrSegI = correspondences[i+1][2]
				currCorrCoordI = correspondences[i+1][3]
				if currCorrSegI>prevCorrSegI or (currCorrSegI==prevCorrSegI and currCorrCoordI>prevCorrSegI): # otherEdge inds increasing
					consecutiveAmt+=1
				else:
					consecutiveAmt=0
			else:
				consecutiveAmt=0
			if consecutiveAmt>=2:
				atLeastOne=True
				break
		
		if atLeastOne:
			i=0
			while i<len(correspondences)-1:
				if correspondences[i+1][4]<correspondences[i][4]: # mainEdge indAsRatio decreasing
					prevCorrSegI = correspondences[i][2]
					prevCorrCoordI = correspondences[i][3]
					currCorrSegI = correspondences[i+1][2]
					currCorrCoordI = correspondences[i+1][3]
					if currCorrSegI>prevCorrSegI or (currCorrSegI==prevCorrSegI and currCorrCoordI>prevCorrSegI): # otherEdge inds increasing
						consecutiveAmt+=1
					else:
						if consecutiveAmt>0:
							i+=1 # skip one otherwise i'd be adding a decreasing one
						consecutiveAmt=0
				else:
					if consecutiveAmt>0:
						i+=1 # skip one otherwise i'd be adding a decreasing one
					consecutiveAmt=0
				if consecutiveAmt<=1:
					newCorrespondences.append(correspondences[i])
				i+=1
			correspondences = newCorrespondences
	return correspondences


def getAvgDistClosestPointsFromOtherToMain(mainEdgePlanesSegments, otherEdgePlanesSegments):
	breakingPointsIndsBefore=set()
	rowsN = 0
	for planeDat in mainEdgePlanesSegments:
		for segmentDat in planeDat:
			if len(segmentDat)>0:
				rowsN+=len(segmentDat)
				breakingPointsIndsBefore.add(rowsN-1)
	
	mainPts = np.empty([rowsN, 2])
	rowCtr = 0
	for planeDat in mainEdgePlanesSegments:
		for segmentDat in planeDat:
			for coordDat in segmentDat:
				mainPts[rowCtr][0]=coordDat[0]
				mainPts[rowCtr][1]=coordDat[1]
				rowCtr+=1
	if rowCtr != rowsN:
		print("??? 12oi2i1223j2edd")
		exit()
	
	main_tree = cKDTree(mainPts)
	
	distAvg = 0
	distAmtCtr = 0
	
	tmpCorres=[]
	
	for planeDat in otherEdgePlanesSegments:
		for segmentDat in planeDat:
			for coordDat in segmentDat:
				point = coordDat
				point = np.asarray(point)
				dd, idx = main_tree.query([point], k=1)
				closestPt = [mainPts[idx[0]][0], mainPts[idx[0]][1]]
				closerPt=None
				if idx[0]<mainPts.shape[0]-1 and idx[0] not in breakingPointsIndsBefore:
					closerPt, junk = closestPtToLineSeg(closestPt, [mainPts[idx[0]+1][0], mainPts[idx[0]+1][1]], point, idx[0])
				if closerPt is None:
					if idx[0]>0 and idx[0]-1 not in breakingPointsIndsBefore:
						closerPt, junk = closestPtToLineSeg([mainPts[idx[0]-1][0], mainPts[idx[0]-1][1]], closestPt, point, idx[0]-1)
				if closerPt is not None: # closestPt is now on lineSeg between 2 vertices, odds of multiple correspondences sharing this point is insanely low so going to disregard this case for speed
					closestPt=closerPt
				tmpDist = getDistance(point[0], closestPt[0], point[1], closestPt[1])
				tmpCorres.append(((int(round(point[0])), int(round(point[1]))), (int(round(closestPt[0])), int(round(closestPt[1])))))
				distAvg+=tmpDist
				distAmtCtr+=1
	if distAmtCtr!=0:
		distAvg=distAvg/distAmtCtr
	else:
		distAvg=None
	return distAvg, tmpCorres








