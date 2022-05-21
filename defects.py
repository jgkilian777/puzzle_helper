from itertools import chain
from collections import deque
import math
import cv2
import numpy as np


def getDistance(p1, p2):
    diffX = abs(p2[0] - p1[0])
    diffY = abs(p2[1] - p1[1])
    return math.hypot(diffX, diffY) # sqrt a^2 + b^2


def findFirstBeforeAndAfterLine(tempxInd, tempyInd, tempzInd, contour, backwards=False):
	reverse = 1 # if reverse is 1, nothing changes, if reverse is -1, then we reverse things
	if backwards:
		reverse=-1
	
	xInd = tempxInd
	yInd = tempyInd
	zInd = tempzInd
	
	if backwards:
		xInd = tempzInd
		# yInd = tempyInd
		zInd = tempxInd
	
	contourLen = contour.shape[0]
	
	lastDupeLineChain = contour[yInd]
	nextBefore=xInd
	nextAfter=zInd
	
	while True:
		beforeLineChange = -1
		afterLineChange = -1
		
		
		while nextBefore > 0:
			nextBefore = nextBefore-1
			
			if (contour[nextBefore][0][1] - lastDupeLineChain[0][1])*(contour[nextBefore+1][0][0] - lastDupeLineChain[0][0]) - (contour[nextBefore][0][0] - lastDupeLineChain[0][0])*(contour[nextBefore+1][0][1] - lastDupeLineChain[0][1]) != 0:
				beforeLineChange = nextBefore
				break
			
		while nextAfter < contourLen-1:
			nextAfter = nextAfter+1
			
			if (contour[nextAfter][0][1] - lastDupeLineChain[0][1])*(contour[nextAfter-1][0][0] - lastDupeLineChain[0][0]) - (contour[nextAfter][0][0] - lastDupeLineChain[0][0])*(contour[nextAfter-1][0][1] - lastDupeLineChain[0][1]) != 0:
				afterLineChange = nextAfter
				break
			
		if (beforeLineChange == -1 and afterLineChange == -1):
			break
		elif beforeLineChange == -1:
			return 0
			
		elif afterLineChange == -1:
			return 0
		
		elif (contour[beforeLineChange+1][0][0] == contour[afterLineChange-1][0][0] and contour[beforeLineChange+1][0][1] == contour[afterLineChange-1][0][1]) and (contour[nextAfter][0][1] - contour[beforeLineChange+1][0][1])*(contour[nextBefore][0][0] - contour[beforeLineChange+1][0][0]) - (contour[nextAfter][0][0] - contour[beforeLineChange+1][0][0])*(contour[nextBefore][0][1] - contour[beforeLineChange+1][0][1]) == 0 and getDistance(contour[nextAfter][0], contour[nextBefore][0]) <= max(getDistance(contour[beforeLineChange+1][0], contour[nextBefore][0]), getDistance(contour[nextAfter][0], contour[beforeLineChange+1][0])):
			# if they both broke off from previous straight line at same point, and theyre now both on the same line (a new straight line that they both share) and theyre both on the same side of the line midpoint (if they split at same place but one goes left and the other goes right but they do it in such a way that it forms a line with the point that they split at, then we needed to check for that)
			lastDupeLineChain=contour[beforeLineChange+1]
		else:
			if afterLineChange-1 < zInd:
				return 0
			if beforeLineChange+1 > xInd:
				return 0
			distToSplitBefore = getDistance(contour[nextBefore+1][0], lastDupeLineChain[0])
			distToSplitAfter = getDistance(contour[nextAfter-1][0], lastDupeLineChain[0])
			if distToSplitAfter < distToSplitBefore:
				#if one split happens closer to the beginning of the line, then this will decide the outcome regardless of what the other split does later on down the line
				
				sign = (contour[nextAfter][0][1] - lastDupeLineChain[0][1])*(contour[nextAfter-1][0][0] - lastDupeLineChain[0][0]) - (contour[nextAfter][0][0] - lastDupeLineChain[0][0])*(contour[nextAfter-1][0][1] - lastDupeLineChain[0][1])
				if sign > 0: # it turned left after.. so the dupe turn was clockwise or right
					return reverse*1
				elif sign < 0:
					return reverse*-1
				else:
					print("this should never happen")
					exit()
					
			elif distToSplitBefore < distToSplitAfter:
				sign = (contour[nextBefore][0][1] - lastDupeLineChain[0][1])*(contour[(nextBefore+1)%contourLen][0][0] - lastDupeLineChain[0][0]) - (contour[nextBefore][0][0] - lastDupeLineChain[0][0])*(contour[(nextBefore+1)%contourLen][0][1] - lastDupeLineChain[0][1])
				if sign < 0: # in reverse from the dupe, it turned right, so going normally forward it turned left which means when it got to the dupe it turned right
					return reverse*1
				elif sign > 0:
					return reverse*-1
				else:
					print("this should never happen2")
					exit()
			else: #assume contour[(beforeLineChange+1)%contourLen][0] == contour[(afterLineChange-1)%contourLen][0]... if they split at the same place, find out which side the one after is from the one before (ASSUME A CONTOUR ONLY EVER PASSES ITSELF ONCE, NO DUMB STUFF LIKE GOING OVER ITSELF LIKE 3 TIMES THEN COMING OUT THE OTHER END LIKE --->, <---, ------->)
				#first check if one split to one side of line and other split to other side
				signAfter = (contour[nextAfter][0][1] - lastDupeLineChain[0][1])*(contour[nextAfter-1][0][0] - lastDupeLineChain[0][0]) - (contour[nextAfter][0][0] - lastDupeLineChain[0][0])*(contour[nextAfter-1][0][1] - lastDupeLineChain[0][1])
				signBefore = (contour[nextBefore][0][1] - lastDupeLineChain[0][1])*(contour[nextBefore+1][0][0] - lastDupeLineChain[0][0]) - (contour[nextBefore][0][0] - lastDupeLineChain[0][0])*(contour[nextBefore+1][0][1] - lastDupeLineChain[0][1])
				if signAfter < 0 and signBefore > 0:
					#left/anticlockwise turn
					return reverse*-1
				elif signAfter > 0 and signBefore < 0:
					#right/clockwise turn
					return reverse*1
				elif signAfter < 0 and signBefore < 0:
					sign = (contour[nextBefore][0][1] - contour[nextAfter-1][0][1])*(contour[nextAfter][0][0] - contour[nextAfter-1][0][0]) - (contour[nextBefore][0][0] - contour[nextAfter-1][0][0])*(contour[nextAfter][0][1] - contour[nextAfter-1][0][1])
					if sign < 0: # before is right of nextAfter w.r.t. directed line from split to nextAfter then its clockwise/right turn
						return reverse*1
					elif sign > 0:
						return reverse*-1
					else:
						print("?????")
						exit()
				elif signAfter > 0 and signBefore > 0:
					sign = (contour[nextBefore][0][1] - contour[nextAfter-1][0][1])*(contour[nextAfter][0][0] - contour[nextAfter-1][0][0]) - (contour[nextBefore][0][0] - contour[nextAfter-1][0][0])*(contour[nextAfter][0][1] - contour[nextAfter-1][0][1])
					if sign < 0: # before is right of nextAfter w.r.t. directed line from split to nextAfter then its clockwise/right turn
						return reverse*1
					elif sign > 0:
						return reverse*-1
					else:
						print(contour[nextBefore])
						print(contour[nextAfter])
						print(contour[nextAfter-1])
						print("?????222")
						exit()
				else:
					print("this should probably never happen3")
					exit()
	return 0

def orientation(x,y,z, xInd, yInd, zInd, contour, contourOrientation=False, backwards=False):
	sign = (z[1] - x[1])*(y[0] - x[0]) - (z[0] - x[0])*(y[1] - x[1])
	
	if sign < 0:
		return 1 # z to the right
	elif sign > 0:
		return -1 # z to the left
	elif sign == 0: # check if z is actually further ahead of y or if its a fake intersection
		distZtoX = getDistance(x, z)
		distXtoY = getDistance(x, y)
		distZtoY = getDistance(y, z)
		if distZtoX <= distXtoY or distZtoX <= distZtoY:
			return findFirstBeforeAndAfterLine(xInd, yInd, zInd, contour, backwards)
		return 0
	else:
		#error
		exit()


def startingOrientation(contour):
	lowestX = contour[0][0][0]
	contourOrientation1=0
	
	x=contour[0][0]
	y=contour[1][0]
	z=contour[2][0]
	xInd=0
	yInd=1
	zInd=2
	
	sign = (z[1] - x[1])*(y[0] - x[0]) - (z[0] - x[0])*(y[1] - x[1])
	
	if sign < 0:
		contourOrientation1 = 1 # z to the right
	elif sign > 0:
		contourOrientation1 = -1 # z to the left
	elif sign == 0: # check if z is actually further ahead of y or if its a fake intersection
		
		distZtoX = getDistance(x, z)
		distXtoY = getDistance(x, y)
		distZtoY = getDistance(y, z)
		if distZtoX > distXtoY and distZtoX > distZtoY: # normal straight line with 180 degrees between, go forward until a turn
			for i in range(2,contour.shape[0]-1):
				tempOrientation = orientation(contour[0][0], contour[i][0], contour[i+1][0], 0,i,i+1, contour)
				if tempOrientation != 0:
					contourOrientation1 = tempOrientation
					break
			
		elif distZtoX <= distXtoY or distZtoX <= distZtoY:
			contourOrientation1 = findFirstBeforeAndAfterLine(xInd, yInd, zInd, contour)
		
	return contourOrientation1
	

def myConvexHull(polyLine, pointCloud=False):
	if pointCloud:
		minY = float('inf')
		minX = float('inf')
		minList = []
		for i in range(polyLine.shape[0]):
			if polyLine[i][0][1] < minY:
				minList = [i]
				minY = polyLine[i][0][1]
			elif polyLine[i][0][1] == minY:
				minList.append(i)
		if len(minList) > 1:
			tempMin = None
			for ind in minList:
				if polyLine[ind][0][0] < minX:
					minX = polyLine[ind][0][0]
					tempMin = ind
			minList = [tempMin]
		
		minPt = [polyLine[minList[0]][0][0], polyLine[minList[0]][0][1]]
		angleList = []
		for i in chain(range(0, minList[0]), range(min(minList[0]+1, polyLine.shape[0]), polyLine.shape[0])):
			tempAngle = math.atan2(polyLine[i][0][1]-minPt[1], polyLine[i][0][0]-minPt[0])
			angleList.append([tempAngle, i])
		
		angleList.sort()
		tempPolyLine = [[minPt]]
		for angleDat in angleList:
			tempPolyLine.append(polyLine[angleDat[1]])
		polyLine = np.array(tempPolyLine)
	
	flipped = False
	if polyLine.shape[0] >= 3:
		startingClockwiseOrNot = startingOrientation(polyLine) # 1 is clockwise, also sign==-1 is also clockise cause sign==-1 is right turn
		
		if startingClockwiseOrNot == 0:
			hullPoints = [0, polyLine.shape[0]-1, 0]
			if pointCloud:
				return hullPoints, flipped, polyLine
			return hullPoints, flipped
		D = deque([])
		if startingClockwiseOrNot == 0:
			print("contour is just a straight line")
			exit()
			
		if startingClockwiseOrNot > 0:
			D.append(0)
			D.append(1)
		else:
			D.append(1)
			D.append(0)

		D.append(2)
		D.appendleft(2)
		
		polyLineLength = len(polyLine)
		whileBreak = 0
		i=3
		
		first=True
		while i<polyLineLength:
			v = polyLine[i]
			while i<polyLineLength-1 and orientation(polyLine[i][0], polyLine[D[0]][0], polyLine[D[1]][0], i,D[0],D[1], polyLine, backwards=True) >= 0 and orientation(polyLine[D[len(D)-2]][0], polyLine[D[len(D)-1]][0], polyLine[i][0], D[len(D)-2],D[len(D)-1],i, polyLine) >= 0:
				i+=1
				v=polyLine[i]
			
			while orientation(polyLine[D[len(D)-2]][0], polyLine[D[len(D)-1]][0], v[0], D[len(D)-2],D[len(D)-1],i, polyLine) <= 0:
				D.pop()
			D.append(i)
			
			while orientation(v[0], polyLine[D[0]][0], polyLine[D[1]][0], i,D[0],D[1], polyLine, backwards=True) <= 0:
				D.popleft()
				if len(D)<2:
					if pointCloud:
						print('why is this rare thing happening? convexmethod1')
						return None
					else:
						print('why is this rare thing happening? convexmethod2')
						return None
				
			D.appendleft(i)
			
			i+=1
			
			whileBreak+=1
			if whileBreak > polyLineLength+5:
				break
		jee = []
		for item in D:
			jee.append(80-item)
		tempo=[]
		for thing in D:
			tempo.append([[polyLine[thing][0][0], polyLine[thing][0][1]]])
		
		hullPoints = []
		for item in D:
			hullPoints.append(item)
		
		if pointCloud:
			return hullPoints, flipped, polyLine
		return hullPoints, flipped
	else:
		if polyLine.shape[0] == 2:
			if pointCloud:
				return [0,1], flipped, polyLine
			return [0,1], flipped
		elif polyLine.shape[0] == 1:
			if pointCloud:
				return [0], flipped, polyLine
			return [0], flipped
		else:
			return None


def betterSlice(list_a, start, stop):
	if (start <= stop):
		return list_a[start:stop]
	else:
		return np.concatenate([list_a[start:],list_a[:stop]])









