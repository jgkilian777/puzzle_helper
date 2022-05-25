import edgeMatchingUtils

import cv2
import numpy as np
import inspect
import argparse

import os
from pidiContours import getPidiContours


# images = ["z1.jpg", "z2.jpg", "z3.jpg"]
print("make sure pidiIMGS folder is empty and inputimgs folder only contains the newest batch of images with the material reference image having the lowest(?) filename when sorted by name, like 0.jpg")
input("press enter...")
inputImgsPath = "inputimgs/"
images = os.listdir(inputImgsPath)

images.sort()
for i in range(len(images)):
	images[i]=inputImgsPath+images[i]


maxXDimensionJustForMachineLearningContours = 3024

imgMaximumXDimension=1512
# imgMaximumXDimension=756

allImageContours=[]

allImageContours, avgPieceMaterialColour, baseImageReferenceContourArea, baseImageReferenceContourIndPair = getPidiContours(images, maxXDimensionJustForMachineLearningContours, imgMaximumXDimension, inputImgsPath)
maxydim=0

for i, imageContours in enumerate(allImageContours):
	for j, contour in enumerate(imageContours["contours"]):
		tmpInds = []
		nothingHappened=True
		
		k=0
		while k<contour.shape[0]-1:
			if abs(contour[k][0][0]-contour[k+1][0][0])<0.0001 and abs(contour[k][0][1]-contour[k+1][0][1])<0.0001:
				tmpInds.append(k)
				k+=1
			else:
				tmpInds.append(k)
			
			k+=1
		if k==contour.shape[0]-1: # if this is true then the last 2 points in contour were DIFFERENT, if k==contour.shape[0] then they were the same
			tmpInds.append(contour.shape[0]-1)
		
		while True:
			nothingHappened=True
			tmpInds2=[]
			k=0
			while k < len(tmpInds)-1:
				ind1 = tmpInds[k]
				ind2 = tmpInds[k+1]
				if abs(contour[ind1][0][0]-contour[ind2][0][0])<0.0001 and abs(contour[ind1][0][1]-contour[ind2][0][1])<0.0001:
					tmpInds2.append(ind1)
					nothingHappened=False
					k+=1
				else:
					tmpInds2.append(ind1)
				k+=1
			if k==len(tmpInds)-1:
				tmpInds2.append(tmpInds[-1])
			if nothingHappened:
				tmpContour=np.empty([len(tmpInds2), 1, 2], dtype=np.float32)
				# tmpContour=np.empty([len(tmpInds2), 1, 2], dtype=int)
				for tmpI, tmpInd in enumerate(tmpInds2):
					tmpContour[tmpI][0][0] = contour[tmpInd][0][0]
					tmpContour[tmpI][0][1] = contour[tmpInd][0][1]
				imageContours["contours"][j] = tmpContour
				break
			else:
				tmpInds=tmpInds2


allPuzzleData = []
allMaxSideLength=0
imgAvgAreaDict = {}


baseImageReferenceContourDat = None
for imgCntrsI, imageContours in enumerate(allImageContours):
	puzzleData, maxSideLength, avgPhotoPieceArea, refCntrDat = edgeMatchingUtils.parseContours(imageContours)
	if imgCntrsI==baseImageReferenceContourIndPair[0]:
		baseImageReferenceContourDat = refCntrDat
	imgAvgAreaDict[imageContours['imgref']] = avgPhotoPieceArea
	allPuzzleData+=puzzleData
	if maxSideLength > allMaxSideLength:
		allMaxSideLength=maxSideLength
	
	
	if True:
		im = cv2.imread(imageContours["image_path"])
		
		if im.shape[1] > imgMaximumXDimension:
			im = cv2.resize(im, (imgMaximumXDimension, round((imgMaximumXDimension/im.shape[1]) * im.shape[0])))
		
		img_contours=im
		
		contours=[]
		
		drawContoursOrPts=True
		# drawContoursOrPts=False
		
		for pieceData in puzzleData:
			if len(pieceData["potentialPieceData"][0]["topEdge"][0])>0:
				contours.append(pieceData["potentialPieceData"][0]["topEdge"][0].astype(int))
		
		if drawContoursOrPts:
			cv2.drawContours(img_contours, contours, -1, (120,120,255), 1)
		else:
			for contour in contours:
				for tmpC in contour:
					cv2.circle(img_contours,(int(tmpC[0][0]), int(tmpC[0][1])),0,(120,120,255),-1)
		
		contours=[]
		for pieceData in puzzleData:
			if len(pieceData["potentialPieceData"][0]["leftEdge"][0])>0:
				contours.append(pieceData["potentialPieceData"][0]["leftEdge"][0].astype(int))
		
		if drawContoursOrPts:
			cv2.drawContours(img_contours, contours, -1, (255,120,120), 1)
		else:
			for contour in contours:
				for tmpC in contour:
					cv2.circle(img_contours,(int(tmpC[0][0]), int(tmpC[0][1])),0,(255,120,120),-1)
		
		contours=[]
		for pieceData in puzzleData:
			if len(pieceData["potentialPieceData"][0]["bottomEdge"][0])>0:
				contours.append(pieceData["potentialPieceData"][0]["bottomEdge"][0].astype(int))
		if drawContoursOrPts:
			cv2.drawContours(img_contours, contours, -1, (120,255,120), 1)
		else:
			for contour in contours:
				for tmpC in contour:
					cv2.circle(img_contours,(int(tmpC[0][0]), int(tmpC[0][1])),0,(120,255,120),-1)
		
		contours=[]
		for pieceData in puzzleData:
			if len(pieceData["potentialPieceData"][0]["rightEdge"][0])>0:
				contours.append(pieceData["potentialPieceData"][0]["rightEdge"][0].astype(int))
		if drawContoursOrPts:
			cv2.drawContours(img_contours, contours, -1, (255,255,0), 1)
		else:
			for contour in contours:
				for tmpC in contour:
					cv2.circle(img_contours,(int(tmpC[0][0]), int(tmpC[0][1])),0,(255,255,0),-1)
		defectKeys = ['topDefects', 'leftDefects', 'rightDefects', 'bottomDefects']
		contourKeys = ['topEdge', 'leftEdge', 'rightEdge', 'bottomEdge']
		for pieceData in puzzleData:
			for defectKeyI in range(4):
				defectKey = defectKeys[defectKeyI]
				contour = pieceData["potentialPieceData"][0][contourKeys[defectKeyI]][0]
				for defectIndDat in pieceData["potentialPieceData"][0][defectKey]:
					defectInd=defectIndDat[0]
					
					tmpTuple = (int(round(contour[defectInd][0][0])), int(round(contour[defectInd][0][1])))
					cv2.circle(img_contours,tmpTuple,0,(255,255,255),-1)
		
		cv2.imshow('Contours', img_contours)
		cv2.waitKey(0)
		cv2.destroyAllWindows()

hsvImgDict={}
for imgPath in images:
	tmpImg = cv2.imread(imgPath)
	
	if tmpImg.shape[1] > imgMaximumXDimension:
		tmpImg = cv2.resize(tmpImg, (imgMaximumXDimension, round((imgMaximumXDimension/tmpImg.shape[1]) * tmpImg.shape[0])))
	
	hsvImgDict[imgPath]=cv2.cvtColor(tmpImg, cv2.COLOR_BGR2HSV_FULL)

hsvImgCentrePtDict={}
for tmpImgCntrs in allImageContours:
	imgPath=tmpImgCntrs['image_path']
	hsvImgCentrePtDict[imgPath]=tmpImgCntrs['centreImgPt']

edgeMatchingUtils.mainEdgeSimilarity(allPuzzleData, allMaxSideLength, maxydim, imgAvgAreaDict, debugDat=None, hsvImgDict=hsvImgDict, avgPieceMaterialColour=avgPieceMaterialColour, hsvImgCentrePtDict=hsvImgCentrePtDict, baseImageReferenceContourArea=baseImageReferenceContourArea, baseImageReferenceContourDat=baseImageReferenceContourDat)























