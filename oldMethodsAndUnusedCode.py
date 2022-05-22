


def compareWithSeedsUsingOrientation(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, mainFullContour, mainPieceFullIndices):
	
	otherPiece = np.flip(otherPiece, 0)
	for key in seedsOther:
		seedsOther[key] = otherPiece.shape[0]-1 - seedsOther[key]
	
	
	### PARAMS
	
	firstStepCheckAmount = 32 # distribute mostly around and between the nub, only like 2 before and after because we first use a corner as seed to points on the ~straight line edges wont be accurate when using angle/orientation
	pointsBeforeAfterNub = 6
	
	tangentNeighbourhoodRadius = 3
	tangentDifference = 0.349066 # 20 degrees in radians, tangent at point must be at least this different from orientation of seed to point
	
	maxDistToSnapMain = 0.002*arcLengthMain # if the distance between 2 contour points is less than 0.2% of arclength then don't bother finding the perfect point on the line between the 2 points
	###
	
	## rough scale, maybe use low res arclength or something instead
	
	distDefect1To1 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["edge1"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["edge1"]][0][1])
	distDefect1To2 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["nubDefect"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["nubDefect"]][0][1])
	distDefect1To3 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["nubSideDefect2"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["nubSideDefect2"]][0][1])
	distDefect1To4 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["edge2"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["edge2"]][0][1])
	
	distDefect2To1 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["edge1"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["edge1"]][0][1])
	distDefect2To2 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["nubDefect"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["nubDefect"]][0][1])
	distDefect2To3 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["nubSideDefect2"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["nubSideDefect2"]][0][1])
	distDefect2To4 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["edge2"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["edge2"]][0][1])
	
	scaleOtherBy2 = (distDefect1To1/distDefect2To1 + distDefect1To2/distDefect2To2 + distDefect1To3/distDefect2To3 + distDefect1To4/distDefect2To4)/4
	
	### for some reason im using otherpiece as the standard, then comparing mainpiece to that
	
	# get points from other piece
	otherOrient = math.atan2(otherPiece[otherPiece.shape[0]-1][0][1] - otherPiece[0][0][1], otherPiece[otherPiece.shape[0]-1][0][0] - otherPiece[0][0][0])
	otherPoints = []
	
	# set seed as first corner rather than just using first corner directly, so that if i want to use this for other seeds its easier to port
	currentSeedOther = seedsOther["edge1"] # 0
	currentSeedMain = seedsMain["edge1"] # 0
	
	# points before nub
	for i in range(1, pointsBeforeAfterNub+1): # take the points that make up the 60% of points that are between the first 20% and last 20% (the middle 60%) and take an evenly "spaced" points amounting to pointsBeforeAfterNub
		ind = seedsOther["nubSideDefect1"]*0.2+i*seedsOther["nubSideDefect1"]*0.6/pointsBeforeAfterNub
		point = otherPiece[math.floor(ind)][0]
		angle = math.atan2(point[1] - otherPiece[currentSeedOther][0][1], point[0] - otherPiece[currentSeedOther][0][0]) - otherOrient
		dist = getDistance(otherPiece[currentSeedOther][0][0], point[0], otherPiece[currentSeedOther][0][1], point[1])
		tempDict = {'ind': math.floor(ind), 'point': point, 'orientation': angle, 'dist': dist, 'distScaled': dist*scaleOtherBy2, 'currentPotentialMatches': []}
		otherPoints.append(tempDict)
	
	#points around/between nub
	for i in range(1, firstStepCheckAmount-(2*pointsBeforeAfterNub)+1): # a bit before and after nub, then split that chunk evenly for remaining points
		start = 0.9*seedsOther["nubSideDefect1"]
		end = seedsOther["nubSideDefect2"] + (otherPiece.shape[0]-1 - seedsOther["nubSideDefect2"])*0.1
		amountOfPoints = end-start
		ind = start+i*amountOfPoints/(firstStepCheckAmount-(2*pointsBeforeAfterNub))
		point = otherPiece[math.floor(ind)][0]
		angle = math.atan2(point[1] - otherPiece[currentSeedOther][0][1], point[0] - otherPiece[currentSeedOther][0][0]) - otherOrient
		dist = getDistance(otherPiece[currentSeedOther][0][0], point[0], otherPiece[currentSeedOther][0][1], point[1])
		tempDict = {'ind': math.floor(ind), 'point': point, 'orientation': angle, 'dist': dist, 'distScaled': dist*scaleOtherBy2, 'currentPotentialMatches': []}
		otherPoints.append(tempDict)
	
	#points after nub
	for i in range(1, pointsBeforeAfterNub+1): # take the points that make up the 60% of points that are between the first 20% and last 20% (the middle 60%) and take an evenly "spaced" points amounting to pointsBeforeAfterNub
		ind = seedsOther["nubSideDefect2"] + (otherPiece.shape[0]-1 - seedsOther["nubSideDefect2"])*0.2+i*(otherPiece.shape[0]-1 - seedsOther["nubSideDefect2"])*0.6/pointsBeforeAfterNub
		point = otherPiece[math.floor(ind)][0]
		angle = math.atan2(point[1] - otherPiece[currentSeedOther][0][1], point[0] - otherPiece[currentSeedOther][0][0]) - otherOrient
		dist = getDistance(otherPiece[currentSeedOther][0][0], point[0], otherPiece[currentSeedOther][0][1], point[1])
		tempDict = {'ind': math.floor(ind), 'point': point, 'orientation': angle, 'dist': dist, 'distScaled': dist*scaleOtherBy2, 'currentPotentialMatches': []}
		otherPoints.append(tempDict)
	
	otherPoints = sorted(otherPoints, key = lambda i: i['ind']) # just to be sure
	
	mainOrient = math.atan2(mainPiece[mainPiece.shape[0]-1][0][1] - mainPiece[0][0][1], mainPiece[mainPiece.shape[0]-1][0][0] - mainPiece[0][0][0])
	
	firstPlaneData = None
	
	# chains = [ ( (1, 2.1), (2, 5), (3, 2.1), (4, 2.1) ),	 ( (1, 2.1), (2, 5), (3, 2.1), (4, 3.3) ), .. ]
	
	chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius)
	
	valChains = validateChains(chains, totalOtherPoints, ...)
	
	currentBest = None
	
	
	newSeed = None
	seedFoundUpOrDown = 0
	overShotDist = 0
	arcLengthTrackerUp = 0
	arcLengthTrackerDown = 0
	if valChains is None:
		
		shiftOrient = 3*0.0174533 # +/- 3 degrees, might need smaller than this or to break it up into 2+ steps
		shiftSeedSteps = 3 # +/- 3% in steps of 1%? maybe need more range than this
		shiftSeedArclength = 0.0115*arcLengthMain # bit above 1% in case noise increases arclength sometimes
		currentSeedMainUp = currentSeedMain
		currentSeedMainDown = currentSeedMain
		mainOrient+=shiftOrient
		chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius)
		valChains = validateChains(chains, totalOtherPoints, ...)
		if valChains is None:
			mainOrient-=2*shiftOrient
			chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius)
			valChains = validateChains(chains, totalOtherPoints, ...)
			if valChains is None:
				shiftStepsCompleted = 0
				while shiftSeedSteps > 0:
					currSeedMainUpPoint = None
					currSeedMainUpPointm1 = None
					while arcLengthTrackerUp < shiftSeedArclength*(1+shiftStepsCompleted):
						currentSeedMainUp+=1
						if currentSeedMainUp > mainPiece.shape[0]-1:
							#get point from next edge/main contour next point
							indInFullContour = ((currentSeedMainUp - (mainPiece.shape[0]-1)) + mainPieceFullIndices[1])%mainFullContour.shape[0]
							currSeedMainUpPoint = mainFullContour[indInFullContour][0]
							currSeedMainUpPointm1 = mainFullContour[(indInFullContour-1)%mainFullContour.shape[0]][0]
						
						else:
							currSeedMainUpPoint = mainPiece[currentSeedMainUp][0]
							currSeedMainUpPointm1 = mainPiece[currentSeedMainUp-1][0]
							
						arcLengthTrackerUp += getDistance(currSeedMainUpPointm1[0], currSeedMainUpPoint[0], currSeedMainUpPointm1[1], currSeedMainUpPoint[1])
					overShotDist = arcLengthTrackerUp - shiftSeedArclength*(1+shiftStepsCompleted)
					vectorBackwards = [currSeedMainUpPointm1[0] - currSeedMainUpPoint[0], currSeedMainUpPointm1[1] - currSeedMainUpPoint[1]]
					vecMag = math.sqrt(vectorBackwards[0]*vectorBackwards[0] + vectorBackwards[1]*vectorBackwards[1])
					unitVecBackwards = [vectorBackwards[0]/vecMag, vectorBackwards[1]/vecMag]
					newSeed = [currSeedMainUpPoint[0] + overShotDist*unitVecBackwards[0], currSeedMainUpPoint[1] + overShotDist*unitVecBackwards[1]]
					
					
					
					mainOrient+=shiftOrient # back to normal
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = 1
						break
					mainOrient+=shiftOrient
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = 1
						break
					mainOrient-=2*shiftOrient
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = 1
						break
					
					currSeedMainDownPoint = None
					currSeedMainDownPointp1 = None
					while arcLengthTrackerDown < shiftSeedArclength*(1+shiftStepsCompleted):
						currentSeedMainDown-=1
						
						if currentSeedMainDown < 0:
							# same as above
							indInFullContour = (mainPieceFullIndices[0] + currentSeedMainDown)%mainFullContour.shape[0]
							currSeedMainDownPoint = mainFullContour[indInFullContour][0]
							currSeedMainDownPointp1 = mainFullContour[(indInFullContour+1)%mainFullContour.shape[0]][0]
						else:
							currSeedMainDownPoint = mainPiece[currentSeedMainDown][0]
							currSeedMainDownPointp1 = mainPiece[currentSeedMainDown+1][0]
						arcLengthTrackerDown += getDistance(currSeedMainDownPointp1[0], currSeedMainDownPoint[0], currSeedMainDownPointp1[1], currSeedMainDownPoint[1])
					overShotDist = arcLengthTrackerDown - shiftSeedArclength*(1+shiftStepsCompleted)
					vectorForwards = [currSeedMainDownPointp1[0] - currSeedMainDownPoint[0], currSeedMainDownPointp1[1] - currSeedMainDownPoint[1]]
					vecMag = math.sqrt(vectorForwards[0]*vectorForwards[0] + vectorForwards[1]*vectorForwards[1])
					unitVecForwards = [vectorForwards[0]/vecMag, vectorForwards[1]/vecMag]
					newSeed = [currSeedMainDownPoint[0] + overShotDist*unitVecForwards[0], currSeedMainDownPoint[1] + overShotDist*unitVecForwards[1]]
					
					mainOrient+=shiftOrient # back to normal
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = -1
						break
					mainOrient+=shiftOrient
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = -1
						break
					mainOrient-=2*shiftOrient
					chains, currentOtherPoints = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains = validateChains(chains, totalOtherPoints, ...)
					if valChains is not None:
						seedFoundUpOrDown = -1
						break
					
					shiftSeedSteps-=1
					shiftStepsCompleted+=1
	
	arcLengthTrackerDown = 0
	arcLengthTrackerUp = 0
	curIteration = 1
	currentSeedMainUp = currentSeedMain
	currentSeedMainDown = currentSeedMain
	previousVariationUp = None
	previousVariationDown = None
	bestDataUp = None
	bestDataDown = None
	
	if seedFoundUpOrDown == 1:
		arcLengthTrackerUp = overShotDist
		arcLengthTrackerDown = -overShotDist
	elif seedFoundUpOrDown == -1:
		arcLengthTrackerUp = -overShotDist
		arcLengthTrackerDown = overShotDist
	
	if valChains is not None:
		
		shiftSeedArclength = 0.0075*arcLengthMain # bit above 0.7% in case noise increases arclength sometimes
		
		continueUp = True
		continueDown = True
		goingUp = True
		firstLoop = True
		
		while continueUp or continueDown: # swap to failsafe version
			# shift mainOrient 1 degree or so in each direction and getMatchingOrientPoints for both
			bestChainsUp = None
			bestValChainsUp = None
			bestChainsDown = None
			bestValChainsDown = None
			bestOtherPointsUp = None
			bestOtherPointsDown = None
			
			degreeCounter = 0
			currentVariation = valChains[0]
			mainOrient2 = mainOrient + 0.0174533
			chains2, currentOtherPoints2 = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient2, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
			valChains2 = validateChains(chains2, totalOtherPoints, ...)
			if valChains2[0] < currentVariation:
				currentVariation = valChains2[0]
				degreeCounter+=1
				bestChainsUp = chains2.copy()
				bestValChainsUp = valChains2.copy()
				bestOtherPointsUp = currentOtherPoints2.copy()
				for i in range(1, 4): # including above, total max shift of 4 degrees upwards
					mainOrient2 += 0.0174533
					chains2, currentOtherPoints2 = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient2, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains2 = validateChains(chains2, totalOtherPoints, ...)
					if valChains2[0] >= currentVariation:
						break
					else:
						currentVariation = valChains2[0]
						degreeCounter+=1
						bestChainsUp = chains2.copy()
						bestValChainsUp = valChains2.copy()
						bestOtherPointsUp = currentOtherPoints2.copy()
			
			
			degreeCounter = 0
			currentVariation = valChains[0]
			mainOrient3 = mainOrient - 0.0174533
			chains2, currentOtherPoints2 = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient3, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
			valChains2 = validateChains(chains2, totalOtherPoints, ...)
			if valChains2[0] < currentVariation:
				currentVariation = valChains2[0]
				degreeCounter+=1
				bestChainsDown = chains2.copy()
				bestValChainsDown = valChains2.copy()
				bestOtherPointsDown = currentOtherPoints2.copy()
				for i in range(1, 4): # including above, total max shift of 4 degrees upwards
					mainOrient3 -= 0.0174533
					chains2, currentOtherPoints2 = getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient3, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed)
					valChains2 = validateChains(chains2, totalOtherPoints, ...)
					if valChains2[0] >= currentVariation:
						break
					else:
						currentVariation = valChains2[0]
						degreeCounter+=1
						bestChainsDown = chains2.copy()
						bestValChainsDown = valChains2.copy()
						bestOtherPointsDown = currentOtherPoints2.copy()
			
			if bestChainsUp is not None and bestChainsDown is not None:
				if bestValChainsDown[0] < bestValChainsUp[0]:
					mainOrient = mainOrient3
					valChains = bestValChainsDown.copy()
					chains = bestChainsDown.copy()
					currentOtherPoints = bestOtherPointsDown.copy()
					if previousVariationUp is None:
						previousVariationUp = bestValChainsDown[0]
						previousVariationDown = bestValChainsDown[0]
						bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
						bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
				else:
					mainOrient = mainOrient2
					valChains = bestValChainsUp.copy()
					chains = bestChainsUp.copy()
					currentOtherPoints = bestOtherPointsUp.copy()
					if previousVariationUp is None:
						previousVariationUp = bestValChainsUp[0]
						previousVariationDown = bestValChainsUp[0]
						bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
						bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
			elif bestChainsUp is not None:
				mainOrient = mainOrient2
				valChains = bestValChainsUp.copy()
				chains = bestChainsUp.copy()
				currentOtherPoints = bestOtherPointsUp.copy()
				if previousVariationUp is None:
					previousVariationUp = bestValChainsUp[0]
					previousVariationDown = bestValChainsUp[0]
					bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
					bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
			elif bestChainsDown is not None:
				mainOrient = mainOrient3
				valChains = bestValChainsDown.copy()
				chains = bestChainsDown.copy()
				currentOtherPoints = bestOtherPointsDown.copy()
				if previousVariationUp is None:
					previousVariationUp = bestValChainsDown[0]
					previousVariationDown = bestValChainsDown[0]
					bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
					bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
			else: # already at the best orientation
				
				if previousVariationUp is None:
					previousVariationUp = valChains[0]
					previousVariationDown = valChains[0]
					bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
					bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
				pass
			
			if not(firstLoop):
				if not(goingUp) and continueUp: # just finished a goingUp calculation
					if valChains[0] >= previousVariationUp: # not improved
						continueUp = False
					else:
						previousVariationUp = valChains[0]
						bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
				elif goingUp and continueDown: # just finished a going down calculation
					if valChains[0] >= previousVariationDown: # not improved
						continueDown = False
					else:
						previousVariationDown = valChains[0]
						bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
				
				elif goingUp and not(continueDown): # just finished going up calculation and going down has been disabled for the calculation above so it was done for goingUp
					if valChains[0] >= previousVariationUp: # not improved
						continueUp = False
					else:
						previousVariationUp = valChains[0]
						bestDataUp = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
				elif not(goingUp) and not(continueUp): # same as above but for other
					if valChains[0] >= previousVariationDown: # not improved
						continueDown = False
					else:
						previousVariationDown = valChains[0]
						bestDataDown = [mainOrient, valChains, chains, newSeed, currentOtherPoints]
			if goingUp:
				currSeedMainUpPoint = None
				currSeedMainUpPointm1 = None
				while arcLengthTrackerUp < shiftSeedArclength*curIteration:
					currentSeedMainUp+=1
					if currentSeedMainUp > mainPiece.shape[0]-1:
						#get point from next edge/main contour next point
						indInFullContour = ((currentSeedMainUp - (mainPiece.shape[0]-1)) + mainPieceFullIndices[1])%mainFullContour.shape[0]
						currSeedMainUpPoint = mainFullContour[indInFullContour][0]
						currSeedMainUpPointm1 = mainFullContour[(indInFullContour-1)%mainFullContour.shape[0]][0]
					# elif currentSeedMainUp < 0:
						# same as above
					else:
						currSeedMainUpPoint = mainPiece[currentSeedMainUp][0]
						currSeedMainUpPointm1 = mainPiece[currentSeedMainUp-1][0]
					arcLengthTrackerUp += getDistance(currSeedMainUpPointm1[0], currSeedMainUpPoint[0], currSeedMainUpPointm1[1], currSeedMainUpPoint[1])
				overShotDist = arcLengthTrackerUp - shiftSeedArclength*curIteration
				vectorBackwards = [currSeedMainUpPointm1[0] - currSeedMainUpPoint[0], currSeedMainUpPointm1[1] - currSeedMainUpPoint[1]]
				vecMag = math.sqrt(vectorBackwards[0]*vectorBackwards[0] + vectorBackwards[1]*vectorBackwards[1])
				unitVecBackwards = [vectorBackwards[0]/vecMag, vectorBackwards[1]/vecMag]
				newSeed = [currSeedMainUpPoint[0] + overShotDist*unitVecBackwards[0], currSeedMainUpPoint[1] + overShotDist*unitVecBackwards[1]]
				if continueDown:
					goingUp = False
				else:
					curIteration+=1
				
				currentSeedMain = currentSeedMainUp
				
			else:
				currSeedMainDownPoint = None
				currSeedMainDownPointp1 = None
				while arcLengthTrackerDown < shiftSeedArclength*curIteration:
					currentSeedMainDown-=1
					
					if currentSeedMainDown < 0:
						# same as above
						indInFullContour = (mainPieceFullIndices[0] + currentSeedMainDown)%mainFullContour.shape[0]
						currSeedMainDownPoint = mainFullContour[indInFullContour][0]
						currSeedMainDownPointp1 = mainFullContour[(indInFullContour+1)%mainFullContour.shape[0]][0]
					else:
						currSeedMainDownPoint = mainPiece[currentSeedMainDown][0]
						currSeedMainDownPointp1 = mainPiece[currentSeedMainDown+1][0]
					arcLengthTrackerDown += getDistance(currSeedMainDownPointp1[0], currSeedMainDownPoint[0], currSeedMainDownPointp1[1], currSeedMainDownPoint[1])
				overShotDist = arcLengthTrackerDown - shiftSeedArclength*curIteration
				vectorForwards = [currSeedMainDownPointp1[0] - currSeedMainDownPoint[0], currSeedMainDownPointp1[1] - currSeedMainDownPoint[1]]
				vecMag = math.sqrt(vectorForwards[0]*vectorForwards[0] + vectorForwards[1]*vectorForwards[1])
				unitVecForwards = [vectorForwards[0]/vecMag, vectorForwards[1]/vecMag]
				newSeed = [currSeedMainDownPoint[0] + overShotDist*unitVecForwards[0], currSeedMainDownPoint[1] + overShotDist*unitVecForwards[1]]
				if continueUp:
					goingUp = True
					# currentSeedMain = currentSeedMainUp
				# else:
					# currentSeedMain = currentSeedMainDown
				currentSeedMain = currentSeedMainDown
				
				curIteration+=1
			
			firstLoop = False
			
			...
			
			# if validateChains or validateChains2 or whatever improves:
				# shift in that direction until validateChains or whatever stops improving
				# potentialConfigurations.append()
				# shift start point
			# else:
				# potentialConfigurations.append()
				# shift start point
	
	# previousVariationDown and previousVariationUp arebest valchains now
	# bestDataDown = (mainOrient, valChains, chains, newSeed) and bestdataup best
	
	# if bad, shift start point more than if good?
	# check if nearly perfect then maybe shift a tiny bit of orient and start then just stop?
	# bother handling good and very good/perfect differently?
	# put in failsafes for when its obviously not a match to save resources, think about the average match comparison, surely even from wrong starting point the ratios would 99% of the time be not toooo far off?
	
	bestData = None
	if bestDataDown[3] == bestDataUp[3]: # no shifting of seed gave better results
		bestData = bestDataUp
	else: # either do both or pick best and do that one
		if bestDataDown[1][0] < bestDataUp[1][0]:
			bestData = bestDataDown
		else:
			bestData = bestDataUp
	
	
	# CONFUSING LISTS !@!@!@ --------------------------------------------------------------------------------------------
	# valchains = (minToMax, tempChain, tightestKnitSliceInd)

	# tempChain = sorted(chain[1])

	# chain[1] = biggestGroup
	# biggestGroup = (point[1]-point2[1], point2), (point[1]-point2[1], point2) ,(point[1]-point2[1], point2)
	# point = item in chain from chains:

	# chains: [ ( (1, 2.1), (2, 5), (3, 2.1), (4, 2.1) ),	( (1, 2.1), (2, 5), (3, 2.1), (4, 3.3) ), .. ]
	# therefore point = (1, 2.1) (index in otherPoints, ratio)
	# -------------------------------------------------------------------------------------------------------------------
	
	
	getFirstPlane(mainPiece, otherPiece, corrospondenciesMainToOther, arcLengthOther, arcLengthMain, bestData)
	
	# PART BELOW "THIS PART" MAY BE CHANGED TO PAUSE AFTER FINDING THE FIRST finalMatchingConfiguration THAT IS >= X THRESHOLD ACCURACY THEN CHECK OTHER CONTOURS, IF NO OTHER CONTOUR BEATS THIS SCORE FOR EITHER EDGE, THEN DEFAULT TO THESE BEING A MATCH, NO POINT REFINING TO FIND PERFECT POINT CORROSPONDENCES
	finalMatchingConfiguration = None
	shift until max shift (to shift backwards, find original contour and use that rather than doing weird forward shift on both
	if >=1 good chain exists, iterate chain or get best chains or something
		euclidian distance similarity using ratio consensus
		find chunks that match, maybe a bit more leniant on what counts as point corrospondence and count it as match with noise, these chunks form a plane
		if chunks found:
			find starting point on other plane and do again
				when both planes found, if its better than finalMatchingConfiguration then update, else skip # THIS PART @@@@@@@@@
		if no chunks found:
			chain isnt a match so skip
	
	return finalMatchingConfiguration


def getFirstPlane(mainPiece, otherPiece, corrospondenciesMainToOther, arcLengthOther, arcLengthMain, bestData):
	
	# TO GET LOCAL CLOSEST POINT:
	# iterate pairs of points locally

	# draw line between 2 points then find point on that line closest (perpendicular) to the test point, if this point occurs on the line, BUT between the 2 points, then store that dist
	# also store the dist from the test point to the actual points (not the line between them)
	
	# get local closest points which should be global closest points
	generalPointCorrospondencies = [] # all, or evenly distributed points corrospondencies
	
	# get all closest dists then sort low to high, ones on low end will be on same plane, ones on high end will be either bad, or on other plane
	# find points on other plane and do whole process again (maybe slightly differently? could be easier if theres any info so far that can be used to help)
	# sort that one from low to high, then compare, place points in whichever plane they are closest to, potentially with a threshold for obviously bad
	# analyse results
	
	# use global arclength for now, might not be good if theres e.g. excess arclength between 2 anchors then normal between another 2 but should be good enough in general
	# for now do 100 pts 1% arclength each? if there are 2 candidates that contradict with close similarity scores then maybe do 200 at 0.5% etc?
	
	#1: get points from otherPiece 1% arclength apart, THIS SHOULD BE MOVED TO EARLIER WHEN ARCLENGTH WAS CALCULATED, NO NEED TO REDO THIS!	 @@@@@@@@@@@@@@@@@@@@@@
	# wont be exactly 100 because need to snip edges so they end at same time? or just don't consider points close to endings
	
	
	otherPoints = bestData[4]
	
	arcLengthOtherStep = arcLengthOther*0.0075 # ~133 pts now
	stepTracker = 1
	arcLengthTracker = 0
	# previousArcLength = 0
	for i in range(otherPiece.shape[0]-1):
		if arcLengthTracker < stepTracker*arcLengthOtherStep:
			# previousArcLength = arcLengthTracker
			arcLengthTracker += getDistance(otherPiece[i][0][0], otherPiece[i+1][0][0], otherPiece[i][0][1], otherPiece[i+1][0][1])
		if arcLengthTracker == stepTracker*arcLengthOtherStep:
			generalPointCorrospondencies.append({'otherPieceInd': i, 'otherPoint': otherPiece[i][0], 'ratioAlongLineBetweenPointsOther': 0, 'mainPieceInd': None, 'mainPoint': None, 'ratioAlongLineBetweenPointsMain': None, 'dist': None})
			stepTracker+=1
		elif arcLengthTracker > stepTracker*arcLengthOtherStep:
			# get point inbetween the 2 indices that give correct arcLength
			overShotDist = arcLengthTracker - stepTracker*arcLengthOtherStep
			vectorForwards = [otherPiece[i+1][0][0] - otherPiece[i][0][0], otherPiece[i+1][0][1] - otherPiece[i][0][1]]
			vecMag = math.sqrt(vectorForwards[0]*vectorForwards[0] + vectorForwards[1]*vectorForwards[1])
			unitVecForwards = [vectorForwards[0]/vecMag, vectorForwards[1]/vecMag]
			tempPoint = [otherPiece[i][0][0] + overShotDist*unitVecForwards[0], otherPiece[i][0][1] + overShotDist*unitVecForwards[1]]
			
			generalPointCorrospondencies.append({'otherPieceInd': i, 'otherPoint': tempPoint, 'ratioAlongLineBetweenPointsOther': overShotDist/getDistance(otherPiece[i][0][0], otherPiece[i+1][0][0], otherPiece[i][0][1], otherPiece[i+1][0][1]), 'mainPieceInd': None, 'mainPoint': None, 'ratioAlongLineBetweenPointsMain': None, 'dist': None})
			# generalPointCorrospondencies.append([tempPoint])
			stepTracker+=1
	
	
	
	# get average ratio and required rotation then rotate NEW: dont bother avg rotation, just rotate based on one of the pts
	ratioMainToOther = 0
	tightestKnitRatiosSlice = bestData[1][1][bestData[1][2][0]:bestData[1][2][1]]
	for pointData in tightestKnitRatiosSlice:
		ratioMainToOther+=pointData[1][1]
	
	# use the 2 points that are furthest away from eachother so very small variances in orientation are minimised
	# bestDataDown = (mainOrient, valChains, chains, newSeed, currentOtherPoints) and bestdataup best
	furthestAwayPair = []
	furthestDist = 0
	furthestAwayPairTightestKnitIndices = []
	for i in range(len(tightestKnitRatiosSlice)):
		for j in range(len(tightestKnitRatiosSlice)):
			if i != j:
				otherPieceInd1 = otherPoints[tightestKnitRatiosSlice[i][1][0]]['ind']
				otherPieceInd2 = otherPoints[tightestKnitRatiosSlice[j][1][0]]['ind']
				tempDist = getDistance(otherPiece[otherPieceInd1][0][0], otherPiece[otherPieceInd2][0][0], otherPiece[otherPieceInd1][0][1], otherPiece[otherPieceInd2][0][1])
				if tempDist > furthestDist:
					furthestDist = tempDist
					if otherPieceInd1 < otherPieceInd2:
						furthestAwayPair = [otherPieceInd1, otherPieceInd2]
						furthestAwayPairTightestKnitIndices = [i,j]
					else:
						furthestAwayPair = [otherPieceInd2, otherPieceInd1]
						furthestAwayPairTightestKnitIndices = [j,i]
					
	ratioMainToOther = ratioMainToOther/len(tightestKnitRatiosSlice)
	# avgRotation = None
	
	centerPointOther = otherPiece[furthestAwayPair[0]][0]
	secondPointOther = otherPiece[furthestAwayPair[1]][0]
	centerPointMain = None
	secondPointMain = None
	# tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[0]][1] = point2 in biggestGroup = item from chain in chains
	if len(tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[0]][1][2][1]) > 0:
		centerPointMain = tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[0]][1][2][1]
	else:
		tempMainInd = tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[0]][1][2][0]
		centerPointMain = [mainPiece[tempMainInd][0][0], mainPiece[tempMainInd][0][1]]
	if len(tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[1]][1][2][1]) > 0:
		secondPointMain = tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[1]][1][2][1]
	else:
		# secondPointMain = None
		tempMainInd = tightestKnitRatiosSlice[furthestAwayPairTightestKnitIndices[1]][1][2][0]
		secondPointMain = [mainPiece[tempMainInd][0][0], mainPiece[tempMainInd][0][1]]
	
	translateBy = [centerPointMain[0]-centerPointOther[0], centerPointMain[1]-centerPointOther[1]]
	centerPointOther = [centerPointOther[0] + translateBy[0], centerPointOther[1] + translateBy[1]]
	secondPointOther = [secondPointOther[0] + translateBy[0], secondPointOther[1] + translateBy[1]]
	
	tempOtherOrient = math.atan2(secondPointOther[1] - centerPointOther[1], secondPointOther[0] - centerPointOther[0])
	tempMainOrient = math.atan2(secondPointMain[1] - centerPointMain[1], secondPointMain[0] - centerPointMain[0])
	
	rotateBy = tempMainOrient - tempOtherOrient
	
	rotMatCos = math.cos(rotateBy)
	rotMatSin = math.sin(rotateBy)
	
	secondPointOther = [secondPointOther[0]*rotMatCos - secondPointOther[1]*rotMatSin, secondPointOther[0]*rotMatSin + secondPointOther[1]*rotMatCos]
	
	for i in range(len(generalPointCorrospondencies)): # IF THIS PART IS NEGLIGIBLE, DO IT FOR ALL POINTS INSTEAD OF ONLY THE CHOSEN ~100 FROM OTHERPIECE, WILL INCREASE ACCURACY BELOW/getClumpsFirstTime BY ALLOWING CHECKING ALL POINTS INSTEAD OF JUST THE ~100
		tempPoint = generalPointCorrospondencies[i]['otherPoint']
		tempPoint[0] = tempPoint[0] + translateBy[0]
		tempPoint[1] = tempPoint[1] + translateBy[1]
		tempPoint = [tempPoint[0]*rotMatCos - tempPoint[1]*rotMatSin, tempPoint[0]*rotMatSin + tempPoint[1]*rotMatCos]
		
		# scale
		tempPointVec = [centerPointOther[0] - tempPoint[0], centerPointOther[1] - tempPoint[1]]
		tempPointVec = [tempPointVec[0]*ratioMainToOther, tempPointVec[1]*ratioMainToOther]
		tempPoint = [centerPointOther[0] + tempPointVec[0], centerPointOther[1] + tempPointVec[1]]
		
		generalPointCorrospondencies[i]['otherPoint'] = tempPoint
	
	# {'otherPieceInd': i, 'otherPoint': otherPiece[i][0], 'ratioAlongLineBetweenPointsOther': 0, 'mainPieceInd': None, 'mainPoint': None, 'ratioAlongLineBetweenPointsMain': None, 'dist': }
	
	
	# queue of 5 points, check distance from these to every point pair in main, when we're closer to first than last, pop last and add next
	otherQueue = generalPointCorrospondencies[:5]
	bestDistList = [[], [], [], [], []]
	otherQueueTrackInd = [0,4]
	# for each step, check neighbourhood 5 contour points, and the 4 lines connecting them then take smallest dist, this might be excessive, or it might even be too small for large scale contours
	for i in range(mainPiece.shape[0]-1):
		for j, pointDat in enumerate(otherQueue):
			for k in range(5):
				if i+k < mainPiece.shape[0]:
					tempDist = getDistance(mainPiece[i+k][0][0], pointDat['otherPoint'][0], mainPiece[i+k][0][1], pointDat['otherPoint'][1])
					if len(bestDistList[j]) == 0:
						bestDistList[j] = [tempDist, i+k, mainPiece[i+k][0], 0]
					elif tempDist < bestDistList[j][0]:
						bestDistList[j] = [tempDist, i+k, mainPiece[i+k][0], 0]
					
			for k in range(4):
				# HERE HERE HERE
				if i+k+1 < mainPiece.shape[0]:
					point1 = mainPiece[i+k][0]
					point2 = mainPiece[i+k+1][0]
					if point1[0] == point2[0] and point1[1] == point2[1]:
						pass
					else:
						# v = [point2[0]-point1[0], point2[1]-point1[1]]
						# u = [point1[0]-pointDat['otherPoint'][0], point1[1]-pointDat['otherPoint'][1]]
						# t = -(v[0]*u[0] + v[1]*u[1])/(v[0]*v[0] + v[1]*v[1])
						# tempDist = None
						point3 = pointDat['otherPoint']
						numerator = (point3[0] - point1[0])*(point2[0] - point1[0]) + (point3[1] - point1[1])*(point2[1]-point1[1])
						denominator = [point2[0] - point1[0], point2[1] - point1[1]]
						denominator = denominator[0]*denominator[0] + denominator[1]*denominator[1]
						u = numerator/denominator
						
						if u > 0 and u < 1: # closest point is on the line segment
							# firstHalfEq = [(1-t)*point1[0], (1-t)*point1[1]]
							# secondHalfEq = [t*point2[0] - pointDat['otherPoint'][0], t*point2[1] - pointDat['otherPoint'][1]]
							# shortestDistVec = [firstHalfEq[0] + secondHalfEq[0], firstHalfEq[1] + secondHalfEq[1]]
							# tempDist = math.sqrt(shortestDistVec[0]*shortestDistVec[0] + shortestDistVec[1]*shortestDistVec[1])
							
							pointOnLine = [point1[0]+u*(point2[0]-point1[0]), point1[1]+u*(point2[1]-point1[1])]
							tempDist = getDistance(pointOnLine[0], pointDat['otherPoint'][0], pointOnLine[1], pointDat['otherPoint'][1])
							if len(bestDistList[j]) == 0:
								bestDistList[j] = [tempDist, i+k, pointOnLine, u]
							elif tempDist < bestDistList[j][0]:
								bestDistList[j] = [tempDist, i+k, pointOnLine, u]
						else: # closest point is either point1 or point2
							distToP1 = getDistance(point1[0], pointDat['otherPoint'][0], point1[1], pointDat['otherPoint'][1])
							distToP2 = getDistance(point2[0], pointDat['otherPoint'][0], point2[1], pointDat['otherPoint'][1])
							if distToP1 < distToP2:
								if len(bestDistList[j]) == 0:
									bestDistList[j] = [distToP1, i+k, mainPiece[i+k][0], 0]
								elif distToP1 < bestDistList[j][0]:
									bestDistList[j] = [distToP1, i+k, mainPiece[i+k][0], 0]
							else:
								if len(bestDistList[j]) == 0:
									bestDistList[j] = [distToP2, i+k+1, mainPiece[i+k+1][0], 0]
								elif distToP2 < bestDistList[j][0]:
									bestDistList[j] = [distToP2, i+k+1, mainPiece[i+k+1][0], 0]
						
		if otherQueueTrackInd[1] < len(generalPointCorrospondencies)-1 and getDistance(mainPiece[i][0][0], otherQueue[4][0], mainPiece[i][0][1], otherQueue[4][1]) < getDistance(mainPiece[i][0][0], otherQueue[0][0], mainPiece[i][0][1], otherQueue[0][1]):
			# generalPointCorrospondencies[otherQueueTrackInd[0]] = [bestDistList[0], generalPointCorrospondencies[otherQueueTrackInd[0]]]
			generalPointCorrospondencies[otherQueueTrackInd[0]]['mainPieceInd'] = bestDistList[0][1]
			generalPointCorrospondencies[otherQueueTrackInd[0]]['mainPoint'] = bestDistList[0][2]
			generalPointCorrospondencies[otherQueueTrackInd[0]]['ratioAlongLineBetweenPointsMain'] = bestDistList[0][3]
			generalPointCorrospondencies[otherQueueTrackInd[0]]['dist'] =  bestDistList[0][0]
			
			otherQueueTrackInd[0] = otherQueueTrackInd[0] + 1
			otherQueueTrackInd[1] = otherQueueTrackInd[1] + 1
			
			otherQueue.popleft()
			bestDistList.popleft()
			
			otherQueue.append(generalPointCorrospondencies[otherQueueTrackInd[1]])
			bestDistList.append([])
	
	for i in range(otherQueueTrackInd[0], otherQueueTrackInd[1]+1):
		generalPointCorrospondencies[i]['mainPieceInd'] = bestDistList[i-otherQueueTrackInd[0]][1]
		generalPointCorrospondencies[i]['mainPoint'] = bestDistList[i-otherQueueTrackInd[0]][2]
		generalPointCorrospondencies[i]['ratioAlongLineBetweenPointsMain'] = bestDistList[i-otherQueueTrackInd[0]][3]
		generalPointCorrospondencies[i]['dist'] =  bestDistList[i-otherQueueTrackInd[0]][0]
	
	# generalPointCorrospondencies = sorted(generalPointCorrospondencies, key = lambda i: i['dist'])
	
	clumps = getClumpsFirstTime(generalPointCorrospondencies)
	
	# HERE HERE HERE HERE analyse now and do next stuff
	
	# for now dont actually analyse much, do a failsafe to make sure it has bare minimum characteristics of a plane (not just fluke 4 points that matched from earlier)
	# but after that, find best candidate for other plane then do it for that plane, then sort points as being either top plane or bottom plane based on whichever it has lowest dist to, then analyse at that stage
	
	if bare minimum for plane:
		pass
	else:
		return none or go back and try another seed
	
	
	
	find best clump for other plane, based on size of clump and std dev or something variation
	take a point from that clump and somehow find a close enough point on other piece so itll pass the previous functions where seed is shifted
	
def getClumpsFirstTime(generalPointCorrospondencies):
	
	for i in range(len(generalPointCorrospondencies)):
		generalPointCorrospondencies[i]["id"] = i
	
	generalPointCorrospondenciesSorted = sorted(generalPointCorrospondencies, key = lambda i: i['dist'])
	
	# good clumps should have low variance/std dev AND low avg dist (variance around a good dist)
	# bad clumps is not(above) i.e. high variance OR bad average dist
	
	# good clump: take current best point, 5 point shifting window around this calcing variance and avg dist
	# choose best, only way i can think of for now is by comparing to worst, top 10% to bottom 10%
	
	# best 10% first (storing best and worst for each top and bottom 10%) , not sure if I'll end up using the worst windows for the top 10%
	
	checkAmount = math.ceil(len(generalPointCorrospondencies)*0.12) # 12% now
	
	topSliceBestWindows = []
	topSliceWorstWindows = []
	
	for i in range(checkAmount):
		bestWindow = {'generalPointCorrospondenciesInd': None, 'averageDist': None, 'variance': None, 'generalPointCorrospondenciesInterval': None}
		worstWindow = {'generalPointCorrospondenciesInd': None, 'averageDist': None, 'variance': None, 'generalPointCorrospondenciesInterval': None}
		currentGPCInd = generalPointCorrospondenciesSorted[i]["id"]
		for j in range(5):
			if currentGPCInd-4+j > 0 and currentGPCInd+j < len(generalPointCorrospondencies):
				tempAverage = 0
				for k in range(currentGPCInd-4+j, currentGPCInd+j+1):
					tempAverage+=generalPointCorrospondencies[k]['dist']
				tempAverage = tempAverage/5
				
				## variance
				##
				##
				############
				
				# only take the best averageDist, we dont compare variance here, only later
				
				if bestWindow['averageDist'] is None:
					bestWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				elif tempAverage < bestWindow['averageDist']:
					bestWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				
				if worstWindow['averageDist'] is None:
					worstWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				elif tempAverage > worstWindow['averageDist']:
					worstWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				
				
		topSliceBestWindows.append(bestWindow)
		topSliceWorstWindows.append(worstWindow)
	
	botSliceBestWindows = []
	botSliceWorstWindows = []
	
	for i in range(checkAmount):
		bestWindow = {'generalPointCorrospondenciesInd': None, 'averageDist': None, 'variance': None, 'generalPointCorrospondenciesInterval': None}
		worstWindow = {'generalPointCorrospondenciesInd': None, 'averageDist': None, 'variance': None, 'generalPointCorrospondenciesInterval': None}
		currentGPCInd = generalPointCorrospondenciesSorted[len(generalPointCorrospondencies)-1-i]["id"]
		for j in range(5):
			if currentGPCInd-4+j > 0 and currentGPCInd+j < len(generalPointCorrospondencies):
				tempAverage = 0
				for k in range(currentGPCInd-4+j, currentGPCInd+j+1):
					tempAverage+=generalPointCorrospondencies[k]['dist']
				tempAverage = tempAverage/5
				
				## variance
				##
				##
				############
				
				# only take the best averageDist, we dont compare variance here, only later
				
				if bestWindow['averageDist'] is None:
					bestWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				elif tempAverage < bestWindow['averageDist']:
					bestWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				
				if worstWindow['averageDist'] is None:
					worstWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				elif tempAverage > worstWindow['averageDist']:
					worstWindow = {'generalPointCorrospondenciesInd': currentGPCInd, 'averageDist': tempAverage, 'variance': tempVariance, 'generalPointCorrospondenciesInterval': [currentGPCInd-4+j, currentGPCInd+j]}
				
				
		botSliceBestWindows.append(bestWindow)
		botSliceWorstWindows.append(worstWindow)
	
	# MAYBE CHECK IF THE INTERVALS ARE CLOSE TOGETHER CAUSE PROB GONNA END UP WITH INTERVALS NEXT TO EACHOTHER THAT ARE PRETTY MUCH THE SAME, I WANT MIDDLE POINT TO BE 2 AWAY FROM ANY OTHER INTERVAL PROB
	
	bestTopListNoDupes = [topSliceBestWindows[0]['generalPointCorrospondenciesInterval']]
	for window in topSliceBestWindows[1:]:
		for i in range(len(bestTopListNoDupes)):
			lowBound = bestTopListNoDupes[i][0]
			upBound = bestTopListNoDupes[i][1]
			windowLowBound = window['generalPointCorrospondenciesInterval'][0]
			windowUpBound = window['generalPointCorrospondenciesInterval'][1]
			if windowLowBound >= lowBound-1 and windowLowBound <= upBound+1:
				if windowUpBound > upBound:
					bestTopListNoDupes[i] = [lowBound, windowUpBound]
			elif windowUpBound >= lowBound-1 and windowUpBound <= upBound+1:
				if windowLowBound < lowBound:
					bestTopListNoDupes[i] = [windowLowBound, upBound]
			
	bestBotListNoDupes = [botSliceBestWindows[0]['generalPointCorrospondenciesInterval']]
	for window in botSliceBestWindows[1:]:
		for i in range(len(bestBotListNoDupes)):
			lowBound = bestBotListNoDupes[i][0]
			upBound = bestBotListNoDupes[i][1]
			windowLowBound = window['generalPointCorrospondenciesInterval'][0]
			windowUpBound = window['generalPointCorrospondenciesInterval'][1]
			if windowLowBound >= lowBound-1 and windowLowBound <= upBound+1:
				if windowUpBound > upBound:
					bestBotListNoDupes[i] = [lowBound, windowUpBound]
			elif windowUpBound >= lowBound-1 and windowUpBound <= upBound+1:
				if windowLowBound < lowBound:
					bestBotListNoDupes[i] = [windowLowBound, upBound]
	
	if False: # think i forgot to implement this properly, implementing it earlier instead? not yet, might not need
		topSliceAverageDist = 0
		botSliceAverageDist = 0
		topSliceAverageVariance = 0
		botSliceAverageVariance = 0
		
		tracker = 0
		for interval in bestTopListNoDupes:
			for i in range(interval[0], interval[1]+1):
				topSliceAverageDist+=generalPointCorrospondencies[i]['dist']
				topSliceAverageVariance+=generalPointCorrospondencies[i]['variance']
				tracker+=1
		topSliceAverageDist = topSliceAverageDist/tracker
		topSliceAverageVariance = topSliceAverageVariance/tracker
		
		tracker = 0
		for interval in bestBotListNoDupes:
			for i in range(interval[0], interval[1]+1):
				botSliceAverageDist+=generalPointCorrospondencies[i]['dist']
				botSliceAverageVariance+=generalPointCorrospondencies[i]['variance']
				tracker+=1
		botSliceAverageDist = botSliceAverageDist/tracker
		botSliceAverageVariance = botSliceAverageVariance/tracker
		
		planeMatchThresholdDist = topSliceAverageDist + (botSliceAverageDist - topSliceAverageDist)*0.12
		# planeMatchThresholdVariance = topSliceAverageVariance + (topSliceAverageVariance - botSliceAverageVariance)*0.12
		
		# we wont check definite plane matches at all
		
		planeNotMatchThresholdDist = botSliceAverageDist - (botSliceAverageDist - topSliceAverageDist)*0.12
	
	# get all points with dist < planeMatchThresholdDist, sort into clumps by allowing for max of 2 (or whatever this is in % so its relative to points chosen? like max(2, floor(0.01*133)) whatever 133 comes from)
	# ... max of 2 (or whatever) points to be outside this threshold in a row. These clumps will now be set and immune to further testing
	
	# same for points dist > planeNotMatchThresholdDist although this might not work, if not just widen threshold or something
	# find a matching seed either by brute force shape matching, or MORE IMPORTANTLY, by a method that uses info we now have, think about this
	# whats the worst case (for a correct match) of how far away 2 new matching seeds will be? e.g. if first ending seed corrospondence was on bottom plane for one piece and top plane for other piece
	# then the next stage we pick a random euclidean location and take the point closest to this from each contour, how far will this choice be from actual corrospondence in worst case?
	
	# using sed seed corrospondence, do whole method again OR new method thats less intensive somehow using info we have now
	
	# once done stage 2, do a check somehow to rule out all 1 plane/perfect match or only 2 simple planes like already done 95%+ by stage 2, is there a way to also check if terrible match? if so do that too
	# rule out perfect by taking bottom and top 12% or whatever like above and comparing to bottom and top from stage 1, if pretty much same or something then done
	
	# ALL INTERVALS ABOVE AND BELOW ARE INCLUSIVE
	
	goodClumps = []
	bestTopListNoDupes.sort()
	goodClumps.append(bestTopListNoDupes[0])
	for interval in bestTopListNoDupes[1:]:
		if interval[0] <= goodClumps[-1][1] + 3 and interval[0] >= goodClumps[-1][1]-1:
			goodClumps[-1] = [goodClumps[-1][0], interval[1]]
		else:
			goodClumps.append(interval)
	
	badClumps = []
	bestBotListNoDupes.sort()
	badClumps.append(bestBotListNoDupes[0])
	for interval in bestBotListNoDupes[1:]:
		if interval[0] <= badClumps[-1][1] + 3 and interval[0] >= badClumps[-1][1]-1:
			badClumps[-1] = [badClumps[-1][0], interval[1]]
		else:
			badClumps.append(interval)
	
	# get general orientation of known good chunks and check if useful
	# consider chunks >=3, turn into straight lines of best fit, if >=7, split into straight lines of 3-4 so if only 7, can only split around the middle into 3, 4 or 4, 3 (could do 5, 2 then not consider the little 2 line but not for now)
	# if 6 split 3,3 if 8 split 3,5 or 4,4 or 5,3 if 9 3,3,3 or 4,5 etc.. whichever gives the 1 sharpest angle
	# nevermind too many tests maybe, for now just half if >=6
	
	goodLines = []
	for clump in goodClumps:
		# can probably use maths to do this in a calculation instead of simulating but too much work for too little savings atm
		tempSim = [clump[1]-clump[0]+1]
		while tempSim[0] >=6:
			tempTempSim = []
			for item in tempSim:
				tempTempSim.append(math.floor(item/2))
				tempTempSim.append(item-math.floor(item/2))
			tempSim = tempTempSim.copy()
		goodLinesIndices = [[0,tempSim[0]-1]]
		for amount in tempSim[1:]:
			goodLinesIndices.append([goodLinesIndices[-1][1]+1, goodLinesIndices[-1][1]+amount]) # gives actual indices for slices INCLUSIVE, so since its python add 1
		for interval in goodLinesIndices:
			point1 = generalPointCorrospondencies[interval[0]]['otherPoint']
			point2 = generalPointCorrospondencies[interval[1]]['otherPoint']
			orientation = math.atan2(point2[1]-point1[1], point2[0]-point1[0])
			orientation = orientation%math.pi
			goodLines.append([orientation, interval])
	
	# badLines = [] # IF I DONT USE THIS THEN DELETE AND REMOVE FROM BELOW LOOPS
	badLinesClumped = []
	for clump in badClumps:
		tempBadLinesClump = []
		# can probably use maths to do this in a calculation instead of simulating but too much work for too little savings atm
		tempSim = [clump[1]-clump[0]+1]
		while tempSim[0] >=6:
			tempTempSim = []
			for item in tempSim:
				tempTempSim.append(math.floor(item/2))
				tempTempSim.append(item-math.floor(item/2))
			tempSim = tempTempSim.copy()
		
		badLinesIndices = [[0,tempSim[0]-1]]
		for amount in tempSim[1:]:
			badLinesIndices.append([badLinesIndices[-1][1]+1, badLinesIndices[-1][1]+amount]) # gives actual indices for slices INCLUSIVE, so since its python add 1 if slicing or using range
		for interval in badLinesIndices:
			point1 = generalPointCorrospondencies[interval[0]]['otherPoint']
			point2 = generalPointCorrospondencies[interval[1]]['otherPoint']
			orientation = math.atan2(point2[1]-point1[1], point2[0]-point1[0])
			orientation = orientation%math.pi
			# badLines.append([orientation, interval[1]-interval[0]+1])
			tempBadLinesClump.append([orientation, interval])
		badLinesClumped.append([len(tempBadLinesClump), tempBadLinesClump])
	
	# take into account orientations and lengths (second index) to get general picture of goodLines
	
	# sort both by orientation (track clump theyre from for the method)
	# starting in the center of the biggest clump? take a badLine, get interval of goodLines that are same orientation +/- 20 degrees? (taking into account modulo, so 10 +/- 20 includes 170+)
	# check the goodLines in this interval, if line between the center of the 2 lines has orientation within +/-45 degrees of angle orthogonal to badLine, (maybe more conditions here)
	# => then continue checking the goodLines within interval, else if fails condition, go next badLine
	# if badLine passes, add to a list of potential starts
	# CHECK ABOVE WORKS FOR ALL SKIPS EXAMPLES
	# if nonempty potentials, narrow down with next priorities until best starting point
	# else check other lines from other bad clumps and do above
	# if none found anywhere, skip this priority and find best for next priority
	# FAILSAFE FOR VERY BAD CASES? LIKE TOP 25% SIZE CLUMPS OR SOMETHING?
	
	sorted(goodLines)
	sorted(badLinesClumped, reverse=True)
	
	# IF THIS TAKES TOO LONG, CHANGE IMPLEMENTATION FROM CHECKING ALL AND TAKING MINIMUM DIST => TO ENDING IF GOOD-BAD-GOOD FOUND I.E. "A GOOD ENOUGH CANDIDATE", potentially with failsafe to end early if looking bad
	
	currentBestPotential = [] # [dist, potential]
	finishClumpThenEnd = False # dont use this, for now just take smallest out of all possible lines
	for badLinesClump in badLinesClumped:
		for badLine in badLinesClump[1]:
			# if len(currentBestPotential) == 2 and badLine best dist out of first and last point isnt better than currentBestPotential[0] then skip, else continue <<<<<<<<<<<<<<
			tempDist = math.min(generalPointCorrospondencies[badLine[1][0]]['dist'], generalPointCorrospondencies[badLine[1][1]]['dist'])
			if len(currentBestPotential) == 0 or (len(currentBestPotential) != 0 and tempDist < currentBestPotential[0]): # remove this and put it back further down if changing to finishClumpThenEnd or doing more than just taking smallest dist
				badLineOrient = badLine[0]
				lowRange = (badLineOrient-(20*math.pi/180))%math.pi
				highRange = (badLineOrient+(20*math.pi/180))%math.pi
				# binary search
				goodLinesIter = None
				if lowRange < highRange:
					goodLinesIter = range(binary_search_goodlines(goodLines, lowRange, False), binary_search_goodlines(goodLines, highRange, True)+1)
				else:
					goodLinesIter = range(binary_search_goodlines(goodLines, lowRange, False), len(goodLines)) + range(binary_search_goodlines(goodLines, highRange, True)+1)
				middleOfBadLine = generalPointCorrospondencies[round(badLine[1][0]+(badLine[1][1]-badLine[1][0])/2)]['otherPoint']
				# badLineActual
				skip = False
				for i in goodLinesIter:
					
					middleOfGoodLine = generalPointCorrospondencies[round(goodLines[i][1][0]+(goodLines[i][1][1]-goodLines[i][1][0])/2)]['otherPoint']
					lineFromBadToGoodOrient = ((math.atan2(middleOfGoodLine[1] - middleOfBadLine[1], middleOfGoodLine[0] - middleOfBadLine[0])) - badLineOrient)%math.pi
					if lineFromBadToGoodOrient >= 45*math.pi/180 and lineFromBadToGoodOrient <= 135*math.pi/180:
						pass
					else:
						skip = True
						break
				if skip == False: # no good lines on the same side of the piece edge as bad line so good candidate
					# if len(currentBestPotential) == 0:
						# currentBestPotential = [math.min(generalPointCorrospondencies[badLine[1][0]]['dist'], generalPointCorrospondencies[badLine[1][1]]['dist']), badLine]
					# else:
						# tempDist = math.min(generalPointCorrospondencies[badLine[1][0]]['dist'], generalPointCorrospondencies[badLine[1][1]]['dist'])
						# if tempDist < currentBestPotential[0]:
						# currentBestPotential = [tempDist, badLine]
					currentBestPotential = [tempDist, badLine]
	
	# get respective point in mainPiece then return or whatever continue
	# HERE HERE HERE HERE ~@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
	# sign = (z[1] - x[1])*(y[0] - x[0]) - (z[0] - x[0])*(y[1] - x[1])
	badLinep1 = generalPointCorrospondencies[currentBestPotential[1][1][0]]
	badLinep2 = generalPointCorrospondencies[currentBestPotential[1][1][1]]
	centerOfBadLineSeg = [(badLinep2[0] + badLinep1[0])/2, (badLinep2[1] + badLinep1[1])/2]
	badLineSlope = (badLinep2[1]-badLinep1[1])/(badLinep2[0]-badLinep1[0])
	orthoSlope = -1/badLineSlope
	
	# orthoEq: y = orthoSlope*x + b
	# b = y-orthoSlope*x, [x,y] = centerOfBadLineSeg
	# newX = centerOfBadLineSeg[0]+1
	# newY = orthoSlope*newX + b
	
	orthoPoint = [centerOfBadLineSeg[0]+1, (centerOfBadLineSeg[0]+1)*orthoSlope + centerOfBadLineSeg[1]-centerOfBadLineSeg[0]*orthoSlope]
	
	# sign = (z[1] - x[1])*(y[0] - x[0]) - (z[0] - x[0])*(y[1] - x[1])
	brack1 = orthoPoint[0] - centerOfBadLineSeg[0] # (y[0] - x[0])
	brack2 = orthoPoint[1] - centerOfBadLineSeg[1] # (y[1] - x[1])
	
	closestOrthogonal = []
	prevSign = (generalPointCorrospondencies[0]['mainPoint'][1]-centerOfBadLineSeg[1])*brack1 - (generalPointCorrospondencies[0]['mainPoint'][0]-centerOfBadLineSeg[0])*brack2
	prevSignInd = 0
	for i in range(1, len(generalPointCorrospondencies)): # IF THIS PART IS TOO INNACURATE WITH JUST THE ~100 POINTS WE CHECKED/TRANSLATED/SCALED/MATCHED EARLIER THEN CONVERT ALL POINTS IN OTHER FUNCTION
		tempDist = getDistance(generalPointCorrospondencies[i]['mainPoint'][0], centerOfBadLineSeg[0], generalPointCorrospondencies[i]['mainPoint'][1], centerOfBadLineSeg[1])
		if len(closestOrthogonal) != 0 and tempDist >= closestOrthogonal[0]:
			pass
		else:
			
			sign = (generalPointCorrospondencies[i]['mainPoint'][1]-centerOfBadLineSeg[1])*brack1 - (generalPointCorrospondencies[i]['mainPoint'][0]-centerOfBadLineSeg[0])*brack2
			if prevSignInd != i-1:
				prevSign = (generalPointCorrospondencies[i-1]['mainPoint'][1]-centerOfBadLineSeg[1])*brack1 - (generalPointCorrospondencies[i-1]['mainPoint'][0]-centerOfBadLineSeg[0])*brack2
				prevSignInd = i-1
			
			if sign == 0 or (sign > 0 and prevSign < 0) or (sign < 0 and prevSign > 0):
				closestOrthogonal = [tempDist, i]
			
			
			prevSign = sign
			prevSignInd = i
	
	# instead of all the checks, just check if dist is way different from closestDist==generalPointCorrospondencies'dist', if so just use the "matched" point from generalPointCorrospondencies
	# THINK: worst case? think worst case seed match might be worse than the starting seed match, if so, can i combine a more fleshed out check (which increases resource usage) with knowledge i now have (to reduce it)?
	# if not, in most cases will there be a decent chunk less points to check so maybe itll balance out?
	
	# just use the point, dont bother getting exact point on line between this point and previous point that is orthogonal to badLine from center
	
	# point1 = generalPointCorrospondencies[interval[0]]['otherPoint']
	# point2 = generalPointCorrospondencies[interval[1]]['otherPoint']
	# orientation = math.atan2(point2[1]-point1[1], point2[0]-point1[0])
	# orientation = orientation%math.pi
	# tempBadLinesClump.append([orientation, interval])
	
	# badLine = [orientation, interval]
	# currentBestPotential = [tempDist, badLine]
	
	newSeedOtherCorrospondenceInd = round(currentBestPotential[1][1][0] + (currentBestPotential[1][1][1] - currentBestPotential[1][1][0])/2) # do point in the middle of the contour slice given by interval in badLine and the index, might not even need the actual point given by index actually
	newSeedMainCorrospondenceInd = None
	if closestOrthogonal[0]/generalPointCorrospondencies[closestOrthogonal[1]]['dist'] >= 1.15 or closestOrthogonal[0]/generalPointCorrospondencies[closestOrthogonal[1]]['dist'] <= 0.85:
		newSeedMainCorrospondenceInd = closestOrthogonal[1] # THIS IS THE CLOSEST POINT TO THE ORTHOGONAL POINT, ORTHOGONAL WILL ACTUALLY BE BETWEEN THIS POINT AND PREVIOUS POINT
	else:
		newSeedMainCorrospondenceInd = newSeedOtherCorrospondenceInd
	

def matchPlanesGivenSeed(arcLengthMain, ratioMainToOther, aabbBVHMain, aabbBVHOther, otherSeed, mainSeed, mainPiece, otherPiece, mainIntervals, otherIntervals, mainOrient, otherOrient, otherPoints):
	### PARAMS
	maxDistToSnapMain = 0.002*arcLengthMain # if the distance between 2 contour points is less than 0.2% of arclength then don't bother finding the perfect point on the line between the 2 points
	ratioError = 0.1 # expect our calculated ratioMainToOther to be within +/- 10% accuracy, use this to discard wildly incorrect guesses
	angleStep = math.pi/180 # 1 degree angle step
	###
	
	angleMatches = []
	angleMatchesUnrestricted = []
	
	for interval in otherIntervals:
		for i in range(interval[0], interval[1]+1):
			otherPointAngle = otherPoints[i]['angle']
			dist = getDistance(otherSeed['coords'][0], otherPoints[i]['coords'][0], otherSeed['coords'][1], otherPoints[i]['coords'][1])
			results, resultsUnrestricted = searchOrientBVH(ratioMainToOther, aabbBVHMain, otherPointAngle, mainPiece, mainOrient, maxDistToSnapMain, mainIntervals, dist)
			angleMatches.append([i, results])
			angleMatchesUnrestricted.append([i, resultsUnrestricted])
	
	# narrow down to 1 chain of pairs: if more than 1 point in mainPiece matches the angle we looked for, throw out any possibilities where the index is BEFORE the previous index (indices should be consecutive increasing)
	# if still more than 1 possibility, choose the point which minimises variability/std dev or whatever, or in simpler but similar way, whichever gives min(abs(ratio - average ratio of sliding windows around point))
	
	prev = None
	next = 0
	start = None
	
	for i in range(len(angleMatches)):
		if len(angleMatches[i][1]) > 0:
			start=i
			break
	
	breakpls = False
	for i in range(start, len(angleMatches)):
		if len(angleMatches[i][1]) == 1:
			prev = i
		elif len(angleMatches[i][1]) >= 2:
			if next < i:
				for j in range(i+1, len(angleMatches)):
					if len(angleMatches[j][1]) == 1:
						next = j
						break
					
			if next < i:
				break
			if next = i+1 and prev = i-1: # specific case not too relevant to this for loop, choose possibility thats closest to direct neighbours
				closerInd = [0,0]
				closerDat = [abs(angleMatches[i][1][0]['ratio'] - angleMatches[i-1][1][0]['ratio']), abs(angleMatches[i][1][0]['ratio'] - angleMatches[i+1][1][0]['ratio'])]
				# failed = False
				for j in range(1,len(angleMatches[i][1])):
					tempDat1 = abs(angleMatches[i][1][j]['ratio'] - angleMatches[i-1][1][j]['ratio'])
					tempDat2 = abs(angleMatches[i][1][j]['ratio'] - angleMatches[i+1][1][j]['ratio'])
					if tempDat1 < closerDat[0]:
						closerInd[0] = j
						closerDat[0] = tempDat1
					if tempDat2 < closerDat[1]:
						closerInd[1] = j
						closerDat[1] = tempDat2
				if closerInd[0] == closerInd[1]:
					angleMatches[i][1] = [angleMatches[i][1][closerInd[0]]]
					prev = i
			else:
				goodInds = []
				for j in range(len(angleMatches[i][1])):
					if angleMatches[i][1][j]['ind'] >= angleMatches[prev][1][0]['ind'] and angleMatches[i][1][j]['ind'] <= angleMatches[next][1][0]['ind']:
						goodInds.append(j)
				if len(goodInds) < len(len(angleMatches[i][1])):
					tempPossibilities = []
					for j in goodInds:
						tempPossibilities.append(angleMatches[i][1][j])
					angleMatches[i][1] = tempPossibilities
	
	for i in range(len(angleMatches)):
		if len(angleMatches[i][1]) > 1 and len(angleMatchesUnrestricted[i][1]) < 6: # second condition in case on a straight line and gives like 100 pts or something silly
			otherInd = angleMatches[i][0]
			tempMainMatches = angleMatchesUnrestricted[i][1]
			
			otherPointAngle = otherPoints[otherInd]['angle']
			dist = otherPoints[otherInd]['dist']
			tempOtherMatches, tempOtherMatchesUnrestricted = searchOrientBVH(1, aabbBVHOther, otherPointAngle, otherPiece, otherOrient, maxDistToSnapMain, otherIntervals, dist)
			
			# find the point in question from otherbvh (should be pretty much exact same dist and stuff but just "take closest" incase tiny change)
			# if same amount of points, order by dist or something, order by ind? order by whatevers best (dist might not be good cause might have same dist forward and backward but having it be obvious that we want forward one)
			# and take the correct point e.g. if other point in question is 2nd then take 2nd from main point possibilities
			# if missmatch, take most similar
			# but think how to define most similar, maybe 2 possibilities with 1 being closer to expected ratio (wrongly), but if we look at bigger picture the other one fits better when compared to the 2nd
			
			if len(tempMainMatches) == len(tempOtherMatchesUnrestricted):
				sorted(tempMainMatches, key = lambda k: k['dist'])
				sorted(tempOtherMatchesUnrestricted, key = lambda k: k['dist'])
				currOtherPt = 0
				currOtherDiff = abs(tempOtherMatchesUnrestricted[0]['dist']-dist)
				for j in range(1, len(tempOtherMatchesUnrestricted)):
					tempDiff = abs(tempOtherMatchesUnrestricted[j]['dist']-dist)
					if tempDiff < currOtherDiff:
						currOtherPt = j
						currOtherDiff = tempDiff
				angleMatches[i][1] = [tempMainMatches[currOtherPt]]
			elif len(tempOtherMatchesUnrestricted) > 1 and len(tempOtherMatchesUnrestricted) < 6:
				currOtherPt = 0
				currOtherDiff = abs(tempOtherMatchesUnrestricted[0]['dist']-dist)
				for j in range(1, len(tempOtherMatchesUnrestricted)):
					tempDiff = abs(tempOtherMatchesUnrestricted[j]['dist']-dist)
					if tempDiff < currOtherDiff:
						currOtherPt = j
						currOtherDiff = tempDiff
				otherRatios = []
				currBestMainMatchesInd = 0
				currClosest = abs(otherRatios[0] - tempMainMatches[0]['dist']/tempMainMatches[1]['dist'])
				for j in range(len(tempOtherMatchesUnrestricted)):
					if j != currOtherPt:
						otherRatios.append(dist/tempOtherMatchesUnrestricted[j]['dist'])
				for j in range(len(tempMainMatches)):
					for k in range(len(tempMainMatches)):
						if j != k:
							tempFrac = tempMainMatches[j]['dist']/tempMainMatches[k]['dist']
							for l in range(len(otherRatios)):
								tempDiff = abs(otherRatios[l] - tempFrac)
								if tempDiff < currClosest:
									currBestMainMatchesInd = j
									currClosest = tempDiff
				angleMatches[i][1] = [tempMainMatches[currBestMainMatchesInd]]
	
	for i in range(len(angleMatches)): # cleanup remaining by setting to empty or picking random one
		if len(angleMatches[i][1]) > 1:
			angleMatches[i][1] = []
	# make sure everythings in order, if there is a section where we get set back like 5 points then go back forward, pick whichever section (which covers same contour index interval) has most matches
	
	start = 0
	for i in range(len(angleMatches)):
		if len(angleMatches[i][1]) == 1:
			start = i
			break
	if start >= len(angleMatches)-1:
		return None
	
	startsDecreasing = None
	previousInd = angleMatches[start][1][0]['ind']
	for i in range(start+1, len(angleMatches)): # AMOUNT TO AND FROM BOTTOM ARE INCLUSIVE OF ROCK BOTTOM AND STARTING POINT
		if len(angleMatches[i][1]) == 1 and angleMatches[i][1][0]['ind'] < previousInd:
			startsDecreasing = previousInd
			rockBottom = angleMatches[i][1][0]['ind']
			rockBottomAngleMatchesInd = i
			amountFromBottom = 1 # DOES THIS PART WORK IF AT END OF MATCHES LIST? vvvv
			for j in range(i+1, len(angleMatches)):
				if len(angleMatches[j][1]) == 1:
					if angleMatches[j][1][0]['ind'] < rockBottom:
						rockBottom = angleMatches[j][1][0]['ind']
						rockBottomAngleMatchesInd = j
						amountFromBottom=1
					elif angleMatches[j][1][0]['ind'] >= rockBottom and angleMatches[j][1][0]['ind'] <= previousInd:
						amountFromBottom+=1
					elif angleMatches[j][1][0]['ind'] > previousInd:
						break
			amountToBottom = 1
			secondRockBottomAngleMatchesInd = previousAngleMatchesInd
			for j in range(1, previousAngleMatchesInd+1):
				if len(angleMatches[previousAngleMatchesInd-j][1]) == 1:
					if angleMatches[previousAngleMatchesInd-j][1][0]['ind'] < rockBottom:
						break
					amountToBottom+=1
					secondRockBottomAngleMatchesInd = previousAngleMatchesInd-j
			# amountFromBottom is bottom forward back to where we started, amountToBottom is from where we started backwards to another point thats same depth, choose whichever of the 2 overlaps has most pts
			# handle cases, especially if amountFromBottom == 0 and stuff
			# at end check if enough matches are even left in angleMatches cause couldve deleted like 90% matches by now
			
			if amountToBottom < amountFromBottom: # clear everything from rockBottomAngleMatchesInd to secondRockBottomAngleMatchesInd excluding rockBottomAngleMatchesInd
				for j in range(secondRockBottomAngleMatchesInd, rockBottomAngleMatchesInd):
					if len(angleMatches[j][1]) >= 1:
						angleMatches[j][1] = []
				# if len(angleMatches[i][1]) == 1:
				previousAngleMatchesInd = rockBottomAngleMatchesInd+amountFromBottom-1
				previousInd = angleMatches[previousAngleMatchesInd][1][0]['ind']
				skipUntil = previousAngleMatchesInd+1
				
			elif amountToBottom >= amountFromBottom: # clear everything from previousAngleMatchesInd to rockBottomAngleMatchesInd+amountFromBottom-1 excluding previousAngleMatchesInd
				for j in range(previousAngleMatchesInd+1, rockBottomAngleMatchesInd+amountFromBottom):
					if len(angleMatches[j][1]) >= 1:
						angleMatches[j][1] = []
				# if len(angleMatches[i][1]) == 1:
					# pass # same previousInd except next time for a (hopefully) monotone next point
				skipUntil = rockBottomAngleMatchesInd+amountFromBottom
				
		elif len(angleMatches[i][1]) == 1:
			previousInd = angleMatches[i][1][0]['ind']
			previousAngleMatchesInd = i
		
	# GLOBAL CACHE FOR BVH'S
	
	if less than % of intervals then return None? but we arent actually expecting 100% of intervals so idk, some condition here think
	
	return interval data, etc


def validateChains(chains, totalOtherPoints, ...): # PROBLEM: I TAKE THE BIGGEST GROUP, I DONT BOTHER BALANCING SIZE OF GROUP WITH VARIABILITY OF GROUP, E.G. IT WOULD CHOOSE 5 POINTS WITH RATIOS VARYING +/-2% OVER 4 POINTS PERFECTLY MATCHING RATIOS
	# PARAMS
	radiusMultiplier = 0.02
	###
	valChains = []
	for chain in chains:
		biggestGroup = []
		biggestCenterInd = -1
		for ind, point in enumerate(chain): # insanely inefficient for now hopefully temporary
			radius = radiusMultiplier*point[1]
			# tempGroup = [point]
			tempGroup = []
			for point2 in chain:
				# if point == point2:
					# pass
				if point2[1] <= point[1] + radius and point2[1] >= point[1] - radius:
					tempGroup.append([point[1]-point2[1], point2])
			# if len(tempGroup) > math.max(1, len(biggestGroup)):
			if len(tempGroup) > math.max(3, len(biggestGroup)):
				biggestGroup = tempGroup.copy()
				biggestCenterInd = ind
		if biggestCenterInd != -1:
			valChains.append([biggestCenterInd,biggestGroup])
	if len(valChains) > 1:
		tightestKnit = []
		for chain in valChains:
			if len(tightestKnit) == 0:
				tempChain = sorted(chain[1])
				centerInd = 0
				for i, val in enumerate(tempChain):
					if val[0] == 0:
						centerInd = i
						break
				minToMax = -1
				tightestKnitSliceInd = []
				for i in range(4):
					start = centerInd - (3-i)
					end = centerInd + i
					if start < 0 or end > len(tempChain)-1:
						pass
					else:
						if minToMax == -1:
							minToMax = tempChain[end] - tempChain[start]
							tightestKnitSliceInd = [start, end]
						elif tempChain[end] - tempChain[start] < minToMax:
							minToMax = tempChain[end] - tempChain[start]
							tightestKnitSliceInd = [start, end]
				# minToMax = tempChain[3][0] - tempChain[1][0] # tempChain[0] is the center point
				tightestKnit = [minToMax, tempChain, tightestKnitSliceInd]
			else:
				tempChain = sorted(chain[1])
				centerInd = 0
				for i, val in enumerate(tempChain):
					if val[0] == 0:
						centerInd = i
						break
				minToMax = -1
				tightestKnitSliceInd = []
				for i in range(4):
					start = centerInd - (3-i)
					end = centerInd + i
					if start < 0 or end > len(tempChain)-1:
						pass
					else:
						if minToMax == -1:
							minToMax = tempChain[end] - tempChain[start]
							tightestKnitSliceInd = [start, end]
						elif tempChain[end] - tempChain[start] < minToMax:
							minToMax = tempChain[end] - tempChain[start]
							tightestKnitSliceInd = [start, end]
				# minToMax = tempChain[3][0] - tempChain[1][0] # tempChain[0] is the center point
				# tightestKnit = (minToMax, tempChain, tightestKnitSliceInd)
				if minToMax < tightestKnit[0] and minToMax != -1:
					tightestKnit = [minToMax, tempChain, tightestKnitSliceInd]
		return tightestKnit # actually return what i need instead of this
	return None
	
	
def getMatchingOrientPoints(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther, otherPoints, mainOrient, currentSeedOther, currentSeedMain, maxDistToSnapMain, tangentDifference, tangentNeighbourhoodRadius, newSeed=None):
	currentSeedMainPoint = -1
	if newSeed is not None:
		currentSeedMainPoint = newSeed
	else:
		currentSeedMainPoint = mainPiece[currentSeedMain][0]
	tempOtherPoints = copy.deepcopy(otherPoints)
	nextOrient = math.atan2(mainPiece[1][0][1] - currentSeedMainPoint[1], mainPiece[1][0][0] - currentSeedMainPoint[0]) - mainOrient
	# prevOrient
	for mainInd in range(1, mainPiece.shape[0]-2): # from here, generic "point" refers to the current point we're testing from mainPiece
		# check if tangent is different enough from line given from seed to point, if not just disregard
		# orientationDifferentEnough = False
		
		#### tangent check
		# tangentStart = math.max(0, mainInd - tangentNeighbourhoodRadius)
		# tangentEnd = math.min(mainPiece.shape[0]-1, mainInd + tangentNeighbourhoodRadius)
		# tangentOrient = math.atan2(mainPiece[tangentEnd][0][1] - mainPiece[tangentStart][0][1], mainPiece[tangentEnd][0][0] - mainPiece[tangentStart][0][0]) - mainOrient
		####
		currPointOrient = nextOrient
		
		
		nextPointOrient = math.atan2(mainPiece[mainInd+1][0][1] - currentSeedMainPoint[1], mainPiece[mainInd+1][0][0] - currentSeedMainPoint[0]) - mainOrient
		
		### tangent check
		if False: #difference < tangentDifference or difference > math.pi - tangentDifference: # TEST
			pass
		else: # tangent is different enough
			
			for i, otherPoint in enumerate(otherPoints):
				# if angle same and dist within resonable scale and neighbourhood angle not straight line from seed: # instead of angle same, check if angle same at mainind, or angle at mainind < and angle at nextind >, then find point inbetween
				pointDist = getDistance(currentSeedMainPoint[0], mainPiece[mainInd][0][0], currentSeedMainPoint[1], mainPiece[mainInd][0][1])
				# if dist same (within scale error)
				if abs(otherPoint['distScaled'] - pointDist)/max(otherPoint['distScaled'], pointDist) < 0.07: # assume scale is within 7% accuracy
					# if angle same (accounting for it being between the 2 contour pts)
					
					# TEST
					
					passed = False
					if currPointOrient > math.pi*0.7 and nextPointOrient < -math.pi*0.7: # edge case where orientation passes negative x axis
						if currPointOrient < otherPoint['orientation'] or otherPoint['orientation'] < nextPointOrient:
							passed = True
					elif nextPointOrient > math.pi*0.7 and currPointOrient < -math.pi*0.7: # edge case where orientation passes negative x axis
						if currPointOrient > otherPoint['orientation'] or otherPoint['orientation'] > nextPointOrient:
							passed = True
					else:
						if (currPointOrient < otherPoint['orientation'] and otherPoint['orientation'] < nextPointOrient) or (currPointOrient > otherPoint['orientation'] and otherPoint['orientation'] > nextPointOrient):
							passed = True
					
					if (getDistance(mainPiece[mainInd][0][0], mainPiece[mainInd+1][0][0], mainPiece[mainInd][0][1], mainPiece[mainInd+1][0][1]) <= maxDistToSnapMain and passed==True) or currPointOrient == otherPoint['orientation']: # ACTUALLY CHECK IF ITS CLOSE ENOUGH THEN JUST 'SNAP' TO THIS POINT
						tempOtherPoints[i]['currentPotentialMatches'].append([mainInd, []])
					elif passed: #	use triangle shenannigans to get point on line between these 2 pts
						seedAngle = currPointOrient - nextPointOrient
						nextCurrSeedAngle = math.atan2(mainPiece[mainInd+1][0][1] - mainPiece[mainInd][0][1], mainPiece[mainInd+1][0][0] - mainPiece[mainInd][0][0]) - math.atan2(mainPiece[mainInd][0][1] - currentSeedMainPoint[1], mainPiece[mainInd][0][0] - currentSeedMainPoint[0])
						lastAngle = math.pi - (seedAngle + nextCurrSeedAngle)
						# pointDist/math.sin(lastAngle) = X/math.sin(seedAngle)
						distCurrToNext = math.sin(seedAngle)*(pointDist/math.sin(lastAngle))
						
						vec = [mainPiece[mainInd+1][0][0]-mainPiece[mainInd][0][0], mainPiece[mainInd+1][0][1]-mainPiece[mainInd][0][1]]
						mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
						unitVec = [vec[0]/mag, vec[1]/mag]
						finalcoord = [mainPiece[mainInd][0][0] + distCurrToNext*unitVec[0], mainPiece[mainInd][0][1] + distCurrToNext*unitVec[1]]
						
						tempOtherPoints[i]['currentPotentialMatches'].append([mainInd, finalcoord])
		
		nextOrient = nextPointOrient
	
	#tempOtherPoints now has all potentials
	
	chains = []
	#populate with initial chain
	startInd = 0
	for ind, otherPoint in enumerate(tempOtherPoints):
		if len(otherPoint['currentPotentialMatches']) > 0:
			for potential in otherPoint['currentPotentialMatches']:
				tempDist = 0
				if len(potential[1]) > 0:
					tempDist = getDistance(currentSeedMainPoint[0], potential[1][0], currentSeedMainPoint[1], potential[1][1])
				else:
					tempDist = getDistance(currentSeedMainPoint[0], mainPiece[potential[0]][0][0], currentSeedMainPoint[1], mainPiece[potential[0]][0][1])
				chains.append([[ind, tempDist/otherPoint['dist'], potential]])
			startInd = ind+1
			break
	
	
	##### PUT IN A FAILSAFE? IN CASE AN INSANELY LARGE AMOUNT OF POTENTIALS???
	
	# chains.append()
	if startInd < len(tempOtherPoints):
		for ind2, otherPoint in enumerate(tempOtherPoints[startInd:]):
			if len(chains) > 145:
				print("exponential amount of chains, exceeded 145 chains aka encountered roughly more than 6 double potentials")
				return None
			if True: # DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG DEBUG 
				if len(chains) > 4:
					print("chains error 2ej2dji")
					exit()
			ind = ind2+startInd
			tempNewChains = []
			for potential in otherPoint['currentPotentialMatches']:
				# tempNewChains = []
				tempDist = 0
				if len(potential[1]) > 0:
					tempDist = getDistance(currentSeedMainPoint[0], potential[1][0], currentSeedMainPoint[1], potential[1][1])
				else:
					tempDist = getDistance(currentSeedMainPoint[0], mainPiece[potential[0]][0][0], currentSeedMainPoint[1], mainPiece[potential[0]][0][1])
				for chain in chains:
					if potential[0] > chain[-1][0]:
						tempNewChains.append(chain + [[ind, tempDist/otherPoint['dist'], potential]])
					## instead of storing points or whatever, store ratios so we can start comparing ratios straight from chains
			chains = copy.deepcopy(tempNewChains)
	# chains = [ ( (1, 2.1), (2, 5), (3, 2.1), (4, 2.1) ),	 ( (1, 2.1), (2, 5), (3, 2.1), (4, 3.3) ), .. ]
	
	return chains, tempOtherPoints



def compareWithSeeds(mainPiece, otherPiece, seedsMain, seedsOther, arcLengthMain, arcLengthOther, firstStepCheckAmountListMain, firstStepCheckAmountListOther):
	
	### PARAMS
	maximumShiftAroundSeed = 0.02 # 2% of arclength? maybe more, depending on maximum realistic error between corresponding seeds
	maximumShiftInScale = 0.05 # 5% up or down
	shiftScaleSteps = 5
	shiftAroundSeedSteps = 5
	maximumOutliers = 3
	atomicSegments = 0.008 # split other piece into 0.8% segments, the higher this is, the faster this will run (less comparisons to make) and less accurate it will be, use this to split ARCLENGTH BETWEEN SEEDS INSTEAD OF ARCLENGTH
	
	minimumSimilarBeforeStarting = 3
	
	###
	
	scaleOtherBy = arcLengthMain/arcLengthOther
	
	# seedsMain = {
		# 'edge1': 0,
		# 'nubSideDefect1': newDefects1[0][0],
		# 'nubDefect': newDefects1[1][0],
		# 'nubSideDefect2' newDefects1[2][0],
		# 'edge2': piece1[key1][0].shape[0]-1,
	# }
	
	otherPiece = np.flip(otherPiece, 0)
	for key in seedsOther:
		seedsOther[key] = otherPiece.shape[0]-1 - seedsOther[key]
	
	## other idea for scale prob better or something similar cause if lower res/less curves, arclength will be less even if the seeds match perfectly
	
	distDefect1To1 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["edge1"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["edge1"]][0][1])
	distDefect1To2 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["nubDefect"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["nubDefect"]][0][1])
	distDefect1To3 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["nubSideDefect2"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["nubSideDefect2"]][0][1])
	distDefect1To4 = getDistance(mainPiece[seedsMain["nubSideDefect1"]][0][0], mainPiece[seedsMain["edge2"]][0][0], mainPiece[seedsMain["nubSideDefect1"]][0][1], mainPiece[seedsMain["edge2"]][0][1])
	
	distDefect2To1 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["edge1"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["edge1"]][0][1])
	distDefect2To2 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["nubDefect"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["nubDefect"]][0][1])
	distDefect2To3 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["nubSideDefect2"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["nubSideDefect2"]][0][1])
	distDefect2To4 = getDistance(otherPiece[seedsOther["nubSideDefect1"]][0][0], otherPiece[seedsOther["edge2"]][0][0], otherPiece[seedsOther["nubSideDefect1"]][0][1], otherPiece[seedsOther["edge2"]][0][1])
	
	scaleOtherBy2 = (distDefect1To1/distDefect2To1 + distDefect1To2/distDefect2To2 + distDefect1To3/distDefect2To3 + distDefect1To4/distDefect2To4)/4
	
	##
	
	baseAtomicRuler = scaleOtherBy2*(distDefect2To1 + distDefect2To2 + distDefect2To3 + distDefect2To4) * atomicSegments
	
	# first edge
	stop = False
	outliers = 0
	while not(stop):
		break
	
	#### PARAMS
	# firstStepCheckAmount = 12 # just divide contour index amount rather than do ruler thing here, this will end with bais towards dense parts of edge but should be fine
	obviouslyBadIf = 0.33 # if we do this percentage of the firstStepCheckAmount and its already looking obviously bad then just skip
	individualBadThreshhold = 0.03 # if its less than this accurate then its obviously bad (% of arclength)
	arclengthStop = 0.02 # e.g. if we're checking the point 2/10ths arclengths into each, only check forward and backwards up to this % of main total arclength
	angleWithin = (5/360)*3.14 # assume end to end orientations of each are roughly within this angle of eachother
	####
	
	# tempStep = math.floor(otherPiece.shape[0]/firstStepCheckAmount)
	points = []
	for ind in firstStepCheckAmountListOther:
		points.append(otherPiece[ind][0])
	
	# trackerDict = {}
	obviouslyBad = False
	#assume scale correct and point 0 is correct, if not then shift point 0 on main:
	stop = arclengthStop*arcLengthMain
	mainPieceStep = 2 # has to be >=2
	mainPieceStep = mainPieceStep * math.floor(mainPiece.shape[0]/otherPiece.shape[0])
	if mainPieceStep < 2:
		mainPieceStep=2
	mainOrient = math.atan2(mainPiece[mainPiece.shape[0]-1][0][1] - mainPiece[0][0][1], mainPiece[mainPiece.shape[0]-1][0][0] - mainPiece[0][0][0])
	otherOrient = math.atan2(otherPiece[otherPiece.shape[0]-1][0][1] - otherPiece[0][0][1], otherPiece[otherPiece.shape[0]-1][0][0] - otherPiece[0][0][0])
	# lastInd=seedsMain["edge1"] # or whatever start ind is
	# lastIndOther=seedsOther["edge1"]
	# lastCoordOther = otherPiece[seedsOther["edge1"]][0]
	# lastCoordMain = mainPiece[seedsMain["edge1"]][0]
	
	# foundList = []
	strands = [[]]
	
	#foundList list of dicts dict{"pointNumber":, "coord":, "ind":}
	# foundList.append({"pointNumber":ind, "coord":bestCoords, "ind":bestInd})
	# foundList.append() # dont actually add initial point to foundList to keep consistant that we iterate and focus on only the following points WRONG, I WILL ADD in strands
	
	# worryAboutExponential = False
	# if len(firstStepCheckAmountListMain) > N:
		# worryAboutExponential = True
	
	for ind, point in enumerate(points): # REMEMBER, ORIENTATION ALWAYS USES FIRST AND LAST POINT, DOESNT CHANGE WITH START INDEX CHANGE AND STUFF (second part of angleOther etc)
		tempStrands = []
		if len(strands) > 4 and ind > 1: # CULL STRANDS. if this whole part is taking long, could maybe reduce by heaps by culling to 2 or even 1 when we have enough data to see if good or not e.g. past halfway through points
			indicesToKeep = []
			maxLength = 0
			for k, strand in enumerate(strands):
				if len(strand) >=2:
					indicesToKeep.append(k)
				if len(strand) > maxLength:
					maxLength = len(strand)
			
			if len(indicesToKeep) > 4 and maxLength > 2:
				indicesToKeep2 = []
				for index1 in indicesToKeep:
					limit = max(math.floor(0.8*maxLength), 3)
					if len(strands[index1]) >=limit:
						indicesToKeep2.append(index1)
				if len(indicesToKeep2) > 0:
					indicesToKeep = copy.deepcopy(indicesToKeep2)
			
			if len(indicesToKeep) > 4:
				# HERE check std dev or something else first if i can think of other things to rule out first, check below
				# conditionals, i want to keep doing stuff until len(indicesToKeep) <=4 and >0
				# MAKE SURE TO CHECK IF == 0 AT EACH CONDITION INCLUDING ABOVE CONDITIONS BECAUSE WE MIGHT BE MAKING GOOD DELETIONS UNTIL ONE WHICH MAKES IT 0 BUT THAT DOESNT MEAN WE WANT TO PICK FIRST 4
				# INSTEAD, AS SOON AS ITS == 0, UNDO WHATEVER CONDITIONAL MADE IT 0 OR SOMETHING
				stdDevs = []
				for index1 in indicesToKeep:
					angleDiffs = []
					for potentialMatch1 in strands[index1]:
						angleDiffs.append(potentialMatch1[1])
					mean = 0
					for angleDiff in angleDiffs:
						mean+=angleDiff
					mean = mean/len(angleDiff)
					variance = 0
					for angleDiff in angleDiffs:
						variance+=(mean-angleDiff)*(mean-angleDiff)
					variance = variance/len(angleDiff)
					stdDev = math.sqrt(variance)
					stdDevs.append([stdDev, index1])
				stdDevs.sort()
				for k in range(4):
					tempStrands.append(strands[stdDevs[k][1]])
				strands = copy.deepcopy(tempStrands)
				tempStrands = []
			elif len(indicesToKeep) == 0:
				tempStrands = strands[:4] # theres not really much else we can do here than just take the first 4
				strands = copy.deepcopy(tempStrands)
				tempStrands = []
			# elif len(indicesToKeep) > 4:
				
			else:
				for index1 in indicesToKeep:
					tempStrands.append(strands[index1])
				strands = copy.deepcopy(tempStrands)
				tempStrands = []
			
			#remove any with length < 2 UNLESS THAT REMOVES EVERY SINGLE ONE
			#until <=4 and > 0, remove worst std dev ones or whatever i mean by this
		elif len(strands) > 4 and ind == 1:
			# until <=4 and > 0, remove ones furthest from goal orientation
			# ACTUALLY just take first 4 encountered like in above case
			tempStrands = strands[:4]
			strands = copy.deepcopy(tempStrands)
			tempStrands = []
		elif len(strands) > 4:
			print("literally impossible")
			return None
			# exit()
		# elif
		for strand in strands:
			#find corresponding for point firstly by finding the point/s with same dist, when searching for corrosponding points, start at rough guess then work outward
			if len(strand) > 0:
				lastCoordMain = strand[-1][2] # here -1 is end, nothing to do with "pointNumber":-1, above
				lastCoordOther = points[strand[-1][0]] # strand is list of ordered lists of the form (pointNumber, angleDiff, finalcoord, finalInd)
			else:
				lastCoordOther = otherPiece[seedsOther["edge1"]][0]
				lastCoordMain = mainPiece[seedsMain["edge1"]][0]
			
			roughStart = firstStepCheckAmountListMain[ind]
			# angleOther = 0
			# distOther = 0
			# distStartToPointOther = getDistance(otherPiece[0][0][0], point[0], otherPiece[0][0][1], point[1])
			# distStartToEndOther = getDistance(otherPiece[0][0][0], otherPiece[otherPiece.shape[0]-1][0][0], otherPiece[0][0][1], otherPiece[otherPiece.shape[0]-1][0][1])
			
			angleOther = math.atan2(point[1] - lastCoordOther[1], point[0] - lastCoordOther[0]) - otherOrient
			
			distOther = getDistance(lastCoordOther[0], point[0], lastCoordOther[1], point[1])
			
			
			# bestInd = None
			# bestOrientDiff = 360
			# bestCoords = None # this will usually be somewhere between bestInd and bestInd+1!
			potentialMatches = [] # ordered lists (pointNumber, angleDiff, coord, ind) where ind is the one before coord if coord is somewhere between 2 contour points
			prevUp = getDistance(lastCoordMain[0], mainPiece[roughStart][0][0], lastCoordMain[1], mainPiece[roughStart][0][1])
			prevDown = prevUp
			
			if prevUp == distOther: # check roughStart
				angleMain = math.atan2(mainPiece[roughStart][0][1] - lastCoordMain[1], mainPiece[roughStart][0][0] - lastCoordMain[0]) - mainOrient
				angleDiff = angleMain-angleOther
				# if angleDiff <= angleWithin:
				# bestInd = roughStart
				# bestCoords = [mainPiece[roughStart][0][0], mainPiece[roughStart][0][1]]
				# bestOrientDiff = angleDiff # THIS SHOULD PROBABLY BE SIGNED INSTEAD OF ABS VALUE SO WE CAN ANALYSE LATER
				potentialMatches.append([ind, angleDiff, [mainPiece[roughStart][0][0], mainPiece[roughStart][0][1]], roughStart])
			
			arcLengthUp = 0
			arcLengthDown = 0
			i=roughStart+mainPieceStep
			while i >= 0 and i <= mainPiece.shape[0] and arcLengthUp < stop:
				finalcoord = None
				finalInd = 0
				dist = getDistance(lastCoordMain[0], mainPiece[i][0][0], lastCoordMain[1], mainPiece[i][0][1])
				if dist > distOther and prevUp < distOther: # we passed the == dist
					#getDistance(lastCoordMain[0], mainPiece[i][0][0], lastCoordMain[1], mainPiece[i][0][1]) too large
					#getDistance(lastCoordMain[0], mainPiece[i-mainPieceStep][0][0], lastCoordMain[1], mainPiece[i-mainPieceStep][0][1]) too small
					if mainPieceStep == 2:
						j=0
						if getDistance(lastCoordMain[0], mainPiece[i-1][0][0], lastCoordMain[1], mainPiece[i-1][0][1]) > distOther:
							j=i-1
						else:
							j=i
						side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
						side2 = distOther
						angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
						# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - mainPiece[lastInd][0][1], mainPiece[j-1][0][0] - mainPiece[lastInd][0][0]) - math.atan2(P2.y - mainPiece[lastInd][0][1], mainPiece[j][0][0] - mainPiece[lastInd][0][0])
						angle2 = math.asin(side1*math.sin(angle1)/side2)
						# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
						
						side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
						if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
							side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
						
						vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
						mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
						unitVec = [vec[0]/mag, vec[1]/mag]
						finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
						finalInd=j-1
					else:
						for j in range(i-mainPieceStep+1, i):
							tempDist = getDistance(lastCoordMain[0], mainPiece[j][0][0], lastCoordMain[1], mainPiece[j][0][1])
							if tempDist > distOther: # make triangle and get coords of unknown corner which has dist from lastInd == distOther
								side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
								side2 = distOther
								angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
								# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - mainPiece[lastInd][0][1], mainPiece[j-1][0][0] - mainPiece[lastInd][0][0]) - math.atan2(P2.y - mainPiece[lastInd][0][1], mainPiece[j][0][0] - mainPiece[lastInd][0][0])
								angle2 = math.asin(side1*math.sin(angle1)/side2)
								# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
								
								side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
								if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
									side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
								
								vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
								mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
								unitVec = [vec[0]/mag, vec[1]/mag]
								finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
								finalInd = j-1
								break
								
				elif dist < distOther and prevUp > distOther:
					if mainPieceStep == 2:
						j=0
						if getDistance(lastCoordMain[0], mainPiece[i-1][0][0], lastCoordMain[1], mainPiece[i-1][0][1]) < distOther:
							j=i-1
						else:
							j=i
						side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
						side2 = distOther
						angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
						# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - mainPiece[lastInd][0][1], mainPiece[j-1][0][0] - mainPiece[lastInd][0][0]) - math.atan2(P2.y - mainPiece[lastInd][0][1], mainPiece[j][0][0] - mainPiece[lastInd][0][0])
						angle2 = math.asin(side1*math.sin(angle1)/side2)
						# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
						
						side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
						if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
							side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
						
						vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
						mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
						unitVec = [vec[0]/mag, vec[1]/mag]
						finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
						finalInd = j-1
					else:
						for j in range(i-mainPieceStep+1, i):
							tempDist = getDistance(lastCoordMain[0], mainPiece[j][0][0], lastCoordMain[1], mainPiece[j][0][1])
							if tempDist < distOther: # make triangle and get coords of unknown corner which has dist from lastInd == distOther
								side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
								side2 = distOther
								angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
								# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - mainPiece[lastInd][0][1], mainPiece[j-1][0][0] - mainPiece[lastInd][0][0]) - math.atan2(P2.y - mainPiece[lastInd][0][1], mainPiece[j][0][0] - mainPiece[lastInd][0][0])
								angle2 = math.asin(side1*math.sin(angle1)/side2)
								# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
								
								side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
								if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
									side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
								
								vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
								mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
								unitVec = [vec[0]/mag, vec[1]/mag]
								finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
								finalInd = j-1
								break
				elif dist == distOther:
					finalcoord = [mainPiece[i][0][0], mainPiece[i][0][1]]
					finalInd=i
				else:
					pass
				
				if finalcoord is not None:
					angleMain = math.atan2(finalcoord[1] - lastCoordMain[1], finalcoord[0] - lastCoordMain[0]) - mainOrient
					angleDiff = angleMain-angleOther
					# if angleDiff <= angleWithin:
					potentialMatches.append([ind, angleDiff, finalcoord, finalInd])
				prevUp = dist
				arcLengthUp+=dist # just using lower resolution arclength to save time/resources
				i+=mainPieceStep
			
			i=roughStart-mainPieceStep
			while i >= 0 and i <= mainPiece.shape[0] and arcLengthDown < stop:
				finalcoord = None
				finalInd = 0
				dist = getDistance(lastCoordMain[0], mainPiece[i][0][0], lastCoordMain[1], mainPiece[i][0][1])
				if dist < distOther and prevDown > distOther: # we passed the == dist
					#getDistance(mainPiece[lastInd][0][0], mainPiece[i][0][0], mainPiece[lastInd][0][1], mainPiece[i][0][1]) too large
					#getDistance(mainPiece[lastInd][0][0], mainPiece[i-mainPieceStep][0][0], mainPiece[lastInd][0][1], mainPiece[i-mainPieceStep][0][1]) too small
					if mainPieceStep == 2:
						j=0
						if getDistance(lastCoordMain[0], mainPiece[i+1][0][0], lastCoordMain[1], mainPiece[i+1][0][1]) > distOther:
							j=i+1
						else:
							j=i+2
						side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
						side2 = distOther
						angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
						# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - lastCoordMain[1], mainPiece[j-1][0][0] - lastCoordMain[0]) - math.atan2(P2.y - lastCoordMain[1], mainPiece[j][0][0] - lastCoordMain[0])
						angle2 = math.asin(side1*math.sin(angle1)/side2)
						# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
						
						side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
						if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
							side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
						
						vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
						mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
						unitVec = [vec[0]/mag, vec[1]/mag]
						finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
						finalInd=j-1
					else:
						for j in range(i+1,i+mainPieceStep):
							tempDist = getDistance(lastCoordMain[0], mainPiece[j][0][0], lastCoordMain[1], mainPiece[j][0][1])
							if tempDist > distOther: # make triangle and get coords of unknown corner which has dist from lastInd == distOther
								side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
								side2 = distOther
								angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
								# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - lastCoordMain[1], mainPiece[j-1][0][0] - lastCoordMain[0]) - math.atan2(P2.y - lastCoordMain[1], mainPiece[j][0][0] - lastCoordMain[0])
								angle2 = math.asin(side1*math.sin(angle1)/side2)
								# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
								
								side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
								if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
									side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
								
								vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
								mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
								unitVec = [vec[0]/mag, vec[1]/mag]
								finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
								finalInd = j-1
								break
								
					
				elif dist > distOther and prevDown < distOther:
					if mainPieceStep == 2:
						j=0
						if getDistance(lastCoordMain[0], mainPiece[i-1][0][0], lastCoordMain[1], mainPiece[i-1][0][1]) < distOther:
							j=i+1
						else:
							j=i+2
						side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
						side2 = distOther
						angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
						# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - lastCoordMain[1], mainPiece[j-1][0][0] - lastCoordMain[0]) - math.atan2(P2.y - lastCoordMain[1], mainPiece[j][0][0] - lastCoordMain[0])
						angle2 = math.asin(side1*math.sin(angle1)/side2)
						# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
						
						side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
						if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
							side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
						
						vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
						mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
						unitVec = [vec[0]/mag, vec[1]/mag]
						finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
						finalInd = j-1
					else:
						for j in range(i+1, i+mainPieceStep):
							tempDist = getDistance(lastCoordMain[0], mainPiece[j][0][0], lastCoordMain[1], mainPiece[j][0][1])
							if tempDist < distOther: # make triangle and get coords of unknown corner which has dist from lastInd == distOther
								side1 = getDistance(lastCoordMain[0], mainPiece[j-1][0][0], lastCoordMain[1], mainPiece[j-1][0][1])
								side2 = distOther
								angle1 = math.atan2(mainPiece[j][0][1] - mainPiece[j-1][0][1], mainPiece[j][0][0] - mainPiece[j-1][0][0]) - math.atan2(lastCoordMain[1] - mainPiece[j-1][0][1], lastCoordMain[0] - mainPiece[j-1][0][0])
								# anotherAngleUnknown = math.atan2(mainPiece[j-1][0][1] - lastCoordMain[1], mainPiece[j-1][0][0] - lastCoordMain[0]) - math.atan2(P2.y - lastCoordMain[1], mainPiece[j][0][0] - lastCoordMain[0])
								angle2 = math.asin(side1*math.sin(angle1)/side2)
								# angle2 = 180 - math.asin(side1*math.sin(angle1)/side2)
								
								side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(angle2))
								if side3 > getDistance(mainPiece[j-1][0][0], mainPiece[j][0][0], mainPiece[j-1][0][1], mainPiece[j][0][1]):
									side3 = math.sqrt(side1*side1 + side2*side2 - 2*side1*side2*math.cos(180-angle2))
								
								vec = [mainPiece[j][0][0]-mainPiece[j-1][0][0], mainPiece[j][0][1]-mainPiece[j-1][0][1]]
								mag = math.sqrt(vec[0]*vec[0] + vec[1]*vec[1])
								unitVec = [vec[0]/mag, vec[1]/mag]
								finalcoord = [mainPiece[j-1][0][0] + side3*unitVec[0], mainPiece[j-1][0][1] + side3*unitVec[1]]
								finalInd = j-1
								break
				elif dist == distOther:
					finalcoord = [mainPiece[i][0][0], mainPiece[i][0][1]]
					finalInd=i
				else:
					pass
				
				if finalcoord is not None:
					angleMain = math.atan2(finalcoord[1] - lastCoordMain[1], finalcoord[0] - lastCoordMain[0]) - mainOrient
					angleDiff = abs(angleMain-angleOther)
					potentialMatches.append([ind, angleDiff, finalcoord, finalInd])
					
				prevDown = dist
				arcLengthDown+=dist
				i-=mainPieceStep
			
			if len(potentialMatches) == 0:
				tempStrands.append(strand)
			else:
				for potentialMatch in potentialMatches:
					tempStrands.append(strand + [potentialMatch])
			
			#HERE HERE @@@@ roughstart +/- stop is hard cap, but try and stop sooner by checking if dist diverges heaps or something, maybe pause when decent potential found then check other first decent potentials
			#then if not perfect go back, rather than storing list of potentials then testing all permutations and choosing best?
			#make sure to throw out any potentials that are out of max realistic error in overall edge orientation 
			
			#end of individual strand in strands iteration
		#after for strand in strands
		strands = copy.deepcopy(tempStrands)
	
	bestMatch = None
	tempStrands = []
	maxLength = 0
	for strand in strands:
		if len(strand) > maxLength:
			maxLength = len(strand)
	
	if maxLength > 2:
		# indicesToKeep2 = []
		for strand in strands:
			limit = max(math.floor(0.9*maxLength), 3)
			if len(strand) >=limit:
				tempStrands.append(strand)
		# if len(indicesToKeep) > 0:
			# indicesToKeep = indicesToKeep.copy()
	if len(tempStrands) > 1:
		stdDevs = []
		for strand in tempStrands:
			angleDiffs = []
			for potentialMatch1 in strand:
				angleDiffs.append(potentialMatch1[1])
			mean = 0
			for angleDiff in angleDiffs:
				mean+=angleDiff
			mean = mean/len(angleDiff)
			variance = 0
			for angleDiff in angleDiffs:
				variance+=(mean-angleDiff)*(mean-angleDiff)
			variance = variance/len(angleDiff)
			stdDev = math.sqrt(variance)
			stdDevs.append([stdDev, index1])
		stdDevs.sort()
		bestMatch = tempStrands[stdDevs[0][1]]
	elif len(tempStrands) == 1:
		bestMatch = tempStrands[0]
	#bestMatch exists if maxLength > 2
	
	# store foundList and try other starting places or scales
	# foundList
	
	#####
	
	return


def bendCurvature(wing, edgeStartEnd, ratioWing, ratioAtStartOfWing, wing1Or2, innieOrOutie=False):
	
	potentiallyStraightLine = 5 # degrees if bend less than this, include in straight line category
	
	# innieOrOutie True => innie and need to reverse
	if innieOrOutie:
		wing = np.flip(wing, 0)
	
	wingOrient = math.atan2(wing[wing.shape[0]-1][0][1] - wing[0][0][1], wing[wing.shape[0]-1][0][0] - wing[0][0][0]) - math.atan2(edgeStartEnd[1][1] - edgeStartEnd[0][1], edgeStartEnd[1][0] - edgeStartEnd[0][0])
	
	# set each of the 2 moving lines to be 1% edge diameter, so 2% coverage each step
	movingLineDiameter = getDistance(edgeStartEnd[0][0], edgeStartEnd[1][0], edgeStartEnd[0][1], edgeStartEnd[1][1])/100
	
	# step is 0.5%, might be way too small but thats what im setting it for now
	step = movingLineDiameter/2
	
	# since we're using arclength instead of straight line, slightly increase step to make up for average/expected extra dist
	step = step*1.25
	
	##################################################### SWAP FOR CIRCLE-BASED CURVATURE METHOD ############################
	
	values = []
	if step == 0:
		print("should never happen but paranoid about infinite loops")
		exit()
	queueList1 = [[wing[0][0]]]
	queueList2 = []
	finishedData = []
	
	currArclength = 0
	prevArclength = 0
	for i in range(1, wing.shape[0]):
		tempArclengthDist = getDistance(wing[i][0][0], wing[i-1][0][0], wing[i][0][1], wing[i-1][0][1])
		currArclength = prevArclength + tempArclengthDist
		
		tempQueueList1 = []
		
		#too tired to think of compact way so adding morethan1
		# morethan1 = False
		# while currArclength >= step:
			# if current or previous coord is close enough just use that to save time, if not then calculate exact coordinate on line between them
		# veryTempbefore = 
		# veryTempafter = 
		if currArclength >= step:
			inbetweenLine = False
			if prevArclength >= step*0.9 and currArclength <= step*1.1:
				if step - prevArclength < currArclength - step:
					tempQueueList1.append([wing[i-1][0]])
					currArclength = tempArclengthDist
				else:
					tempQueueList1.append([wing[i][0]])
					currArclength = 0
			elif prevArclength >= step*0.9:
				tempQueueList1.append([wing[i-1][0]])
				prevArclength = 0
				currArclength = tempArclengthDist 
				if tempArclengthDist >= step:
					inbetweenLine = True
			elif currArclength <= step*1.1:
				tempQueueList1.append([wing[i][0]])
				currArclength = 0
			else:
				inbetweenLine = True
			
			if inbetweenLine:
				# calculate all points on line between the 2 pts that give n*step = prevArclength + dist from prev pt to pt on line, dont do loop or anything just hard calc 
				#MAKE SURE CURRARCLENGTH ENDS BEING LESS THAN STEP! or itll break
				
				numberOfSteps = math.floor((prevArclength + tempArclengthDist)/step)
				
				#do first one
				# distOnLine = step - prevArclength
				# ...
				# append
				# numberOfSteps-=1
				# if numberOfSteps > 0:
				# not even going to handle case where 2 consecutive points have the same coordinates because opencv must not allow this
				unitVecX = (wing[i][0][0] - wing[i-1][0][0])/(math.sqrt((wing[i][0][0] - wing[i-1][0][0])**2 + (wing[i][0][1] - wing[i-1][0][1])**2))
				unitVecY = (wing[i][0][1] - wing[i-1][0][1])/(math.sqrt((wing[i][0][0] - wing[i-1][0][0])**2 + (wing[i][0][1] - wing[i-1][0][1])**2))
				for k in range(1, numberOfSteps+1):
					distOnLine = k*step - prevArclength
					newX = wing[i-1][0][0] + distOnLine*unitVecX
					newY = wing[i-1][0][1] + distOnLine*unitVecY
					tempQueueList1.append([[newX, newY]])
				currArclength -= currArclength*numberOfSteps
		if currArclength >= step: # just in case overflow/rounding stuff causes issues
			currArclength = step*0.99
		
		prevArclength = currArclength
		tempQueueList2 = []
		tempMoveListIndices = []
		tempMoveListIndicesTemp = []
		for j, bendInstance in enumerate(tempQueueList1): # same as below except line segment is between bendInstance coord and end of line seg (maybe other changes but prob not)
			tempDist = getDistance(wing[i][0][0], bendInstance[0][0], wing[i][0][1], bendInstance[0][1])
			if tempDist >= movingLineDiameter:
				vecLineSeg = [wing[i][0][0] - bendInstance[0][0], wing[i][0][1] - bendInstance[0][1]]
				tempRatio = movingLineDiameter/tempDist
				tempQueueList2.append(bendInstance.append([bendInstance[0][0] + tempRatio*vecLineSeg[0], bendInstance[0][1] + tempRatio*vecLineSeg[1]]))
				tempMoveListIndicesTemp.append(j)
		for j, bendInstance in enumerate(queueList1):
			tempDist = getDistance(wing[i][0][0], bendInstance[0][0], wing[i][0][1], bendInstance[0][1])
			if tempDist >= movingLineDiameter:
				vecLineSeg = [wing[i][0][0] - wing[i-1][0][0], wing[i][0][1] - wing[i-1][0][1]]
				vecBendStartToLineSegStart = [wing[i-1][0][0] - bendInstance[0][0], wing[i-1][0][1] - bendInstance[0][1]]
				circleRadius = movingLineDiameter
				
				a = vecLineSeg[0]**2 + vecLineSeg[1]**2
				b = 2*(vecBendStartToLineSegStart[0]*vecLineSeg[0] + vecBendStartToLineSegStart[1]*vecLineSeg[1])
				c = vecBendStartToLineSegStart[0]**2 + vecBendStartToLineSegStart[1]**2 - circleRadius**2
				
				discriminant = sqrt(b**2-4*a*c)
				
				t1 = (-b - discriminant)/(2*a)
				t2 = (-b + discriminant)/(2*a)
				
				if t1 >= 0 and t1 <= 1 and t2 >=0 and t2 <= 1:
					print("euclidean geometry broken?")
					exit()
				elif t1 >= 0 and t1 <= 1:
					tempQueueList2.append(bendInstance.append([wing[i-1][0][0] + t1*vecLineSeg[0], wing[i-1][0][1] + t1*vecLineSeg[1]]))
					tempMoveListIndices.append(j)
					
				elif t2 >=0 and t2 <= 1:
					tempQueueList2.append(bendInstance.append([wing[i-1][0][0] + t2*vecLineSeg[0], wing[i-1][0][1] + t2*vecLineSeg[1]]))
					tempMoveListIndices.append(j)
				else:
					print("should never ever happen ever")
					exit()
				
		# SAME FOR QUEUELIST3 STUFF EXCEPT MOVE TO FINAL LIST OR WHATEVER
		# REMOVE ALL OF THE MOVEINDICES BEFORE CONCATENATIONS
		
		########
		tempQueueList2RemoveIndices = []
		queueList2RemoveIndices = []
		
		for j, bendInstance in enumerate(tempQueueList2): # same as below except line segment is between bendInstance coord and end of line seg (maybe other changes but prob not)
			tempDist = getDistance(wing[i][0][0], bendInstance[0][0], wing[i][0][1], bendInstance[0][1])
			if tempDist >= movingLineDiameter:
				vecLineSeg = [wing[i][0][0] - bendInstance[0][0], wing[i][0][1] - bendInstance[0][1]]
				tempRatio = movingLineDiameter/tempDist
				finishedData.append(bendInstance.append([bendInstance[0][0] + tempRatio*vecLineSeg[0], bendInstance[0][1] + tempRatio*vecLineSeg[1]]))
				tempQueueList2RemoveIndices.append(j)
		for j, bendInstance in enumerate(queueList2):
			tempDist = getDistance(wing[i][0][0], bendInstance[0][0], wing[i][0][1], bendInstance[0][1])
			if tempDist >= movingLineDiameter:
				vecLineSeg = [wing[i][0][0] - wing[i-1][0][0], wing[i][0][1] - wing[i-1][0][1]]
				vecBendStartToLineSegStart = [wing[i-1][0][0] - bendInstance[0][0], wing[i-1][0][1] - bendInstance[0][1]]
				circleRadius = movingLineDiameter
				
				a = vecLineSeg[0]**2 + vecLineSeg[1]**2
				b = 2*(vecBendStartToLineSegStart[0]*vecLineSeg[0] + vecBendStartToLineSegStart[1]*vecLineSeg[1])
				c = vecBendStartToLineSegStart[0]**2 + vecBendStartToLineSegStart[1]**2 - circleRadius**2
				
				discriminant = sqrt(b**2-4*a*c)
				
				t1 = (-b - discriminant)/(2*a)
				t2 = (-b + discriminant)/(2*a)
				
				if t1 >= 0 and t1 <= 1 and t2 >=0 and t2 <= 1:
					print("euclidean geometry broken?")
					exit()
				elif t1 >= 0 and t1 <= 1:
					finishedData.append(bendInstance.append([wing[i-1][0][0] + t1*vecLineSeg[0], wing[i-1][0][1] + t1*vecLineSeg[1]]))
					queueList2RemoveIndices.append(j)
					
				elif t2 >=0 and t2 <= 1:
					finishedData.append(bendInstance.append([wing[i-1][0][0] + t2*vecLineSeg[0], wing[i-1][0][1] + t2*vecLineSeg[1]]))
					queueList2RemoveIndices.append(j)
				else:
					print("should never ever happen ever")
					exit()
		#######
		# terrible way of doing this but dont have time
		# this assumes remove index lists are sorted and increasing which is always true
		amtDel = 0
		for ind in tempMoveListIndices:
			del queueList1[ind-amtDel]
			amtDel+=1
		amtDel = 0
		for ind in tempMoveListIndicesTemp:
			del tempQueueList1[ind-amtDel]
			amtDel+=1
		amtDel = 0
		for ind in queueList2RemoveIndices:
			del queueList2[ind-amtDel]
			amtDel+=1
		amtDel = 0
		for ind in tempQueueList2RemoveIndices:
			del tempQueueList2[ind-amtDel]
			amtDel+=1
		
		queueList1 = queueList1 + tempQueueList1
		queueList2 = queueList2 + tempQueueList2
	
	finishedDataProcessed = []
	for data in finishedData:
		secondLineOrient = math.atan2(data[2][1] - data[1][1], data[2][0] - data[1][0])
		firstLineOrient = math.atan2(data[1][1] - data[0][1], data[1][0] - data[0][0])
		angle = secondLineOrient - firstLineOrient
		
		ratioOnEdgeLine = projectPtToLine(edgeStartEnd[0], edgeStartEnd[1], data[1], "ratioonline")
		ratioOnWingLine = (1/ratioWing)*(ratioOnEdgeLine - ratioAtStartOfWing)
		finishedDataProcessed.append([ratioOnWingLine, angle])
		
	# HERE
	# take the top min(5, totalDistinctBends) w.r.t. length of bend, and store length and middle location
	# calculate total % pos/neg/"straight"
	
	#wing1or2 should tell us where we're starting. To get rid of duplicates (assert it's a function, 1 y for each x, vertical line test)
	# we want to start from the outer edge of each wing then first come first serve monotone
	deleteInds = []
	
	# terrible way to code but dont have time
	if wing1Or2 == 'wing1':
		maxX = 0
		for i in range(len(finishedDataProcessed)):
			if finishedDataProcessed[i][0] > maxX:
				maxX = finishedDataProcessed[i][0]
			else:
				deleteInds.append(i)
		
	elif wing1Or2 == 'wing2':
		minX = 1
		finishedDataProcessed.reverse()
		for i in range(len(finishedDataProcessed)):
			if finishedDataProcessed[i][0] < minX:
				minX = finishedDataProcessed[i][0]
			else:
				deleteInds.append(i)
		
	amtDel=0
	for ind in deleteInds:
		del finishedDataProcessed[ind-amtDel]
		amtDel+=1
	
	##################################################### SWAP FOR CIRCLE-BASED CURVATURE METHOD
	
	# iterate and store any consecutive +/- finishedDataProcessed[i][1] as +/- areas then sort and take largest 5 or all if theres less than 5 and store the center or whatever
	# BUT only store if area covers at least 5% of wing span or something so if its noisy straight then we dont store and sort every item as an area
	
	# then, or at the same time as above, whatever is most efficient, store total % +/-/'straight' as planned
	# then make sure to handle small wings seperately/differently (before this function is called?) and make sure wing orientation is implemented if not already cant remember
	# and store results of this function as planned, range tree or something
	
	# assuming the bend angle of the contour changes linearly, which should suffice since our data points are quite close together, we interpolate the roots then use them as the boundaries for the +/- areas

 
def similarityController(largePieceDatabase, trackerAndOtherData, potentialPieceData, params, non=None, innieIndTracker=0, outieIndTracker=0): # call functions for each seed instance, shift seeds and everything, maybe also pre-check shortest graph for optimal pair tests?
	# global timesPastWiggleLen2
	global tmpdebug1
	global tmpdebug2
	global tmpdebug3
	global tmpdebug4
	global tmpdebug5
	global tmpdebuglist
	global windowMatchesGlobalTracker
	global limwigroomFast
	global limwigroomSlow
	global limwigroomSlowBeforeFirstPair
	global literallyTemp
	global similarityInstanceCall
	global windowSlide
	global allWhileLoopChains
	global allChainsAtLeastSize2
	global allChainsAtLeastSize3
	global allChainsAtLeastSize4
	global allChainsAtLeastSize5
	global allChainsAtLeastSize1
	global allChainsAtLeastSize6
	global windowMatchesAmount
	
	global idktempTimeKeep
	global tempTimeKeep
	global tempTimeKeepAmount
	
	global idktempCalls
	global idktempConditional
	
	global totalTimeSimilarityInstanceCall # add timeafter-timebefore to this and +=1 the amount
	global amountSimilarityInstanceCall
	global totalTimeLastSectionOfSimilarityInstance
	global amountLastSectionOfSimilarityInstance
	
	# edgeIDkey <-> edgeIDint, largePieceDatabase uses keys, cache or whatever in firstSweepCompatibility uses int/index, VERY bad coding
	edgeIDKeyToInt = {
		'topEdge': 0,
		'rightEdge': 1,
		'bottomEdge': 2,
		'leftEdge': 3
	}
	
	compatCache = [[], []]
	
	
	# Different ways this could happen, for now do fastest implementation which will prob just be same shifts for each seed and take best or whatever
	# much more efficient would be something greedy prob or at least something that does different detail levels and stuff
	
	# queryEdgeID, windowEdgeID, queryPieceID, windowPieceID, querySeedCoord, windowSeedCoord, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace
	
	windowAmount = params['windowAmount']
	
	# might need to do stuff before this but the rest is:
	
	# IN similarityInstance edge1 IS WINDOW, where spaced out pts are being best fit to edge2 (query), shiftWindowBy is added to edge1 pts to get to edge2 space, impliedScale was window/query but changed it to query/window so it can be used
	
	# iterate trackerAndOtherData['innies'] and trackerAndOtherData['outies'] <<<<<<<<<<<<<
	
	matchRankings = [] # just to sort matches by score, any other data should go in other lists/structures so we can more easily query stuff like "for a given edge, what other edges has it been compared to and with what scores"
	# or graph traversal or whatever for the final stage of piecing everything together into 1 puzzle
	tmpDebugCounter=0
	# for 2 edges that should be compared:
	# PROB NEED VARS/CHECKER FOR WHEN A NEW BATCH IS ADDED TO RE-COMPARE PREVIOUS BATCHES OF INNIES/OUTIES TO NEW OUTIES/INNIES @@@@@@@@@@@@@@@@@@@
	for i in range(innieIndTracker, len(trackerAndOtherData['innies'])-1):
	# if 2 edges should be compared... (this might already be done in main function)
		for j in range(outieIndTracker, len(trackerAndOtherData['outies'])-1):
			edgeIndInnie = trackerAndOtherData['innies'][i][12]
			edgeIndOutie = trackerAndOtherData['outies'][j][12]
			
			literallyTemp+=1
			
			largePieceDbIndInnie = trackerAndOtherData['innies'][i][0]
			cornerRepInnie = trackerAndOtherData['innies'][i][1] # will always be 0 for now but accessing it from list for future
			pieceEdgeKeyInnie = trackerAndOtherData['innies'][i][2]
			potentialPieceDataIndInnie = largePieceDatabase[largePieceDbIndInnie][0]
			
			
			largePieceDbIndOutie = trackerAndOtherData['outies'][j][0]
			cornerRepOutie = trackerAndOtherData['outies'][j][1]
			pieceEdgeKeyOutie = trackerAndOtherData['outies'][j][2]
			potentialPieceDataIndOutie = largePieceDatabase[largePieceDbIndOutie][0]
			
			# innieEdge = potentialPieceData[i]["potentialPieceData"][0][key1][0]
			
			# largePieceDatabase[largePieceDbIndInnie][1]
			# print(potentialPieceDataIndOutie)
			# print(cornerRepOutie)
			# print(pieceEdgeKeyOutie)
			# exit()
			edgeViewInnie = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRepInnie][pieceEdgeKeyInnie][0]
			edgeViewOutie = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRepOutie][pieceEdgeKeyOutie][0]
			
			queryDistFromCameraNormalisationVal = potentialPieceData[potentialPieceDataIndOutie]["potentialPieceData"][cornerRepOutie]['distFromCameraNormalisationVal']
			windowDistFromCameraNormalisationVal = potentialPieceData[potentialPieceDataIndInnie]["potentialPieceData"][cornerRepInnie]['distFromCameraNormalisationVal']
			
			estimatedScale = windowDistFromCameraNormalisationVal/queryDistFromCameraNormalisationVal
			
			# want innie flipped so they can be compared
			edgeViewInnie = np.flip(edgeViewInnie, 0)
			
			prelimCompat = False
			
			# wing1IntervalAssumingWing1Error = [(ratioWing1*edgeSpan1-excessErrorFromLowerPlane)/(edgeSpan1-excessErrorFromLowerPlane), ratioWing1]
			# wing2IntervalAssumingWing1Error = [ratioWing2, ratioWing2*edgeSpan1/(edgeSpan1-excessErrorFromLowerPlane)]
			
			innieW1W1Err = trackerAndOtherData['innies'][i][4]
			innieW2W1Err = trackerAndOtherData['innies'][i][5]
			innieW1W2Err = trackerAndOtherData['innies'][i][6]
			innieW2W2Err = trackerAndOtherData['innies'][i][7]
			
			outieW1W1Err = trackerAndOtherData['outies'][j][4]
			outieW2W1Err = trackerAndOtherData['outies'][j][5]
			outieW1W2Err = trackerAndOtherData['outies'][j][6]
			outieW2W2Err = trackerAndOtherData['outies'][j][7]
			
			# wing ratios already normalised (divided by edge span) and accounted for error, so its prob enough to just check if calculated (normalised for edge span but no error stuff) is within interval of other edge wing interval
			# but actually lower plane error might throw off the other edge wing ratios so just check for interval overlap
			
			# if innieW1W1Err and innieW2W1Err compatWith outieW1W1Err and outieW2W1Err OR innieW1W1Err and innieW2W1Err compatWith outieW1W2Err and outieW2W2Err OR other 2 cases permutations
			
			# compatWingRatios = False
			
			print("ok here now! 111111111")
			# print(innieW1W1Err)
			# print(outieW1W1Err)
			# print(innieW2W1Err)
			# print(outieW2W1Err)
			if (innieW1W1Err[1] >= outieW1W1Err[0] and outieW1W1Err[1] >= innieW1W1Err[0]) and (innieW2W1Err[1] >= outieW2W1Err[0] and outieW2W1Err[1] >= innieW2W1Err[0]):
				prelimCompat = True
			elif (innieW1W1Err[1] >= outieW1W2Err[0] and outieW1W2Err[1] >= innieW1W1Err[0]) and (innieW2W1Err[1] >= outieW2W2Err[0] and outieW2W2Err[1] >= innieW2W1Err[0]): # instead of 'or' because might want to use assumed error later but mainly for readability rather than massive conditional line
				prelimCompat = True
			elif (innieW1W2Err[1] >= outieW1W1Err[0] and outieW1W1Err[1] >= innieW1W2Err[0]) and (innieW2W2Err[1] >= outieW2W1Err[0] and outieW2W1Err[1] >= innieW2W2Err[0]):
				prelimCompat = True
			elif (innieW1W2Err[1] >= outieW1W2Err[0] and outieW1W2Err[1] >= innieW1W2Err[0]) and (innieW2W2Err[1] >= outieW2W2Err[0] and outieW2W2Err[1] >= innieW2W2Err[0]):
				prelimCompat = True
			
			if prelimCompat == True:
				# print("here22222222222222222")
				prelimCompat = False
				innieW1Orient = trackerAndOtherData['innies'][i][8] # w.r.t. line of edge span
				innieW2Orient = trackerAndOtherData['innies'][i][9]
				
				outieW1Orient = trackerAndOtherData['outies'][j][8] # w.r.t. line of edge span
				outieW2Orient = trackerAndOtherData['outies'][j][9]
				
				# print(innieW1Orient)
				# print(outieW1Orient)
				# print(innieW2Orient)
				# print(outieW2Orient)
				
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
				
				if abs(wing1OrientDiff) <= math.pi/18 and abs(wing2OrientDiff) <= math.pi/18: # 10 degrees? if too strict maybe 15?
					# any more checks here? almost certainly but maybe add later
					prelimCompat = True
			
			if prelimCompat == True:
				tmpDebugCounter+=1
				# CONTINUE FURTHER
				arcLengthWindow = trackerAndOtherData['innies'][i][10] # innie
				arcLengthQuery = trackerAndOtherData['outies'][j][10] # outie
				# .....
				pieceRepresentation = 0 # only one for now # IF THIS EVER CHANGES, NEED TO HAVE 2 SEPERATE FOR OUTIE/INNIE @@@@@@@@@@
				
				# onlyStepPoints.append([[newX, newY], i-1, distOnLine, distOnLine/tempArclengthDist, distOnLine/tempMag])
				
				stepCoordsWindow = largePieceDatabase[largePieceDbIndInnie][1][pieceRepresentation][edgeIndInnie][3]
				stepCoordsQuery = largePieceDatabase[largePieceDbIndOutie][1][pieceRepresentation][edgeIndOutie][3]
				
				iWantDebugTmp = ([813, 849], [361, 140])
				if stepCoordsWindow[1][0][0] == 1087.1233787381448 or stepCoordsQuery[1][0][0] == 1087.1233787381448:
					print(stepCoordsWindow[:3])
					print("")
					print(stepCoordsWindow[-3:])
					print("")
					print(stepCoordsQuery[:3])
					print("")
					print(stepCoordsQuery[-3:])
					
				for ok in range(5):
					print(literallyTemp)
				# if literallyTemp>=220:# True:# stepCoordsWindow[0][0][0] == iWantDebugTmp[0][0] and stepCoordsWindow[0][0][1] == iWantDebugTmp[0][1] and stepCoordsQuery[0][0][0] == iWantDebugTmp[1][0] and stepCoordsQuery[0][0][1] == iWantDebugTmp[1][1]:
				if literallyTemp<=12:
					
					stepLengthWindow = largePieceDatabase[largePieceDbIndInnie][1][pieceRepresentation][edgeIndInnie][2]
					stepLengthQuery = largePieceDatabase[largePieceDbIndOutie][1][pieceRepresentation][edgeIndOutie][2]
					
					mainSeedPairs = []
					# add more later
					seedDictWindow = trackerAndOtherData['innies'][i][11]
					seedDictQuery = trackerAndOtherData['outies'][j][11]
					# NEED TO DO SHAPE-X or something since one edge has been flipped but seed dict was constructed before any flips? anyway do seedDictQuery['nub1seed'], seedDictWindow['nub2seed'] or whatever the actual keys are, 0 ratioonline prob, etc...
					
					# just using a defect for now, in future either use other simple defects as seeds or some other better method for stable/reliable seeds
					# but if not on a contour point, we'll need similar to below representations for seeds, [coord, indbefore, distOnLine]
					# junk/verbose for readability cause will need to add here later
					seedDictKey = 'nubSideDefect1'
					queryInd = seedDictQuery[seedDictKey]
					coordQuery = copy.deepcopy(edgeViewOutie[queryInd][0])
					
					seedDictKey = 'nubSideDefect2'
					windowInd = edgeViewInnie.shape[0]-1 - seedDictWindow[seedDictKey]
					coordWindow = copy.deepcopy(edgeViewInnie[windowInd][0])
					
					
					tmpWindowSeedDat = []
					if windowInd == edgeViewInnie.shape[0]-1: # when i use seeds that arent simply contour coords, then flipped instead of distonline being ind->ind+1 itd be ind->ind-1 so will need to do disttotalLine-distonline
															# basically all nonzero distonline seeds do ind-=1 and distonline = totaldistonline-olddistonline
						tmpWindowSeedDat = [coordWindow, windowInd-1, getDistance(edgeViewInnie[windowInd-1][0][0], coordWindow[0], edgeViewInnie[windowInd-1][0][1], coordWindow[1])] # always need to be able to use index+1 without error in a few different functions
					else:
						tmpWindowSeedDat = [coordWindow, windowInd, 0]
					tmpQuerySeedDat = []
					if queryInd == edgeViewOutie.shape[0]-1:
						tmpQuerySeedDat = [coordQuery, queryInd-1, getDistance(edgeViewOutie[queryInd-1][0][0], coordQuery[0], edgeViewOutie[queryInd-1][0][1], coordQuery[1])]
					else:
						tmpQuerySeedDat = [coordQuery, queryInd, 0]
					mainSeedPairs.append([tmpWindowSeedDat, tmpQuerySeedDat])
					
					# seedPairDatPerDistinctSeed = [] # each item contains all data up to shift for a distinct seedpair
					testDat = []
					
					for mainSeedPair in mainSeedPairs:
						# print(mainSeedPair)
						windowMainSeed = mainSeedPair[0] # [coord, indbefore, distOnLine, ... like stepCoords format]
						queryMainSeed = mainSeedPair[1]
						shiftedSeedPairs = []
						seedIsAfterStepCoordNwindow = None
						seedIsAfterStepCoordNquery = None
						for stepCoordInd in range(1, len(stepCoordsWindow)):
							if windowMainSeed[1] < stepCoordsWindow[stepCoordInd][1] or (windowMainSeed[1] == stepCoordsWindow[stepCoordInd][1] and windowMainSeed[2] < stepCoordsWindow[stepCoordInd][2]):
								# shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], ])
								seedIsAfterStepCoordNwindow = stepCoordInd-1
								break
						if seedIsAfterStepCoordNwindow is None and (windowMainSeed[1] > stepCoordsWindow[-1][1] or (windowMainSeed[1] == stepCoordsWindow[-1][1] and  windowMainSeed[2] >= stepCoordsWindow[-1][2]) ):
							seedIsAfterStepCoordNwindow = len(stepCoordsWindow)-1
						
						###
						for stepCoordInd in range(1, len(stepCoordsQuery)):
							if queryMainSeed[1] < stepCoordsQuery[stepCoordInd][1] or (queryMainSeed[1] == stepCoordsQuery[stepCoordInd][1] and queryMainSeed[2] < stepCoordsQuery[stepCoordInd][2]):
								
								seedIsAfterStepCoordNquery = stepCoordInd-1
								break
						if seedIsAfterStepCoordNquery is None and (queryMainSeed[1] > stepCoordsQuery[-1][1] or (queryMainSeed[1] == stepCoordsQuery[-1][1] and	 queryMainSeed[2] >= stepCoordsQuery[-1][2]) ):
							seedIsAfterStepCoordNquery = len(stepCoordsQuery)-1
						
						if seedIsAfterStepCoordNwindow is not None and seedIsAfterStepCoordNquery is not None: # should ALWAYS be true
							shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], seedIsAfterStepCoordNwindow, seedIsAfterStepCoordNquery, windowMainSeed[1], queryMainSeed[1], windowMainSeed[2], queryMainSeed[2]])
						shiftAmtRadius = params['seedShiftAmtRadius'] # like 3 before/after
						
						
						shiftArclengthStepWindow = arcLengthWindow*params['seedShiftArclengthStepPercentageAsDecimal'] # like less than half of 1% arclength maybe? idk
						shiftArclengthStepQuery = arcLengthQuery*params['seedShiftArclengthStepPercentageAsDecimal']
						
						baseSeedIsAfterContourIndWindow = windowMainSeed[1] # store in data somewhere then access here
						baseSeedIsAfterContourIndQuery = queryMainSeed[1]
						
						# VVV  /\/\/\  VERY MISLEADING naming, should probably have been "distance towards next coord" because im talking about dists and ratios FROM the first coord/ind TO the next coord/ind
						distToNextCoordWindow = windowMainSeed[2] # baseSeedIsAfterContourIndWindow to baseSeedIsAfterContourIndWindow+1 in contour/edge
						distToNextCoordQuery = queryMainSeed[2]
						
						# go 1 way then the other way then if one failed extend the other way
						
						# shift seed backward in window so shifting window whole edge forwards
						tmpCtrBackward = shiftAmtRadius
						tmpInd = baseSeedIsAfterContourIndWindow
						# tmpLineDist = getDistance(...) between tmpInd and tmpInd+1
						# tmpLineRatio = ratioToNextCoordWindow
						tmpLineRatioDist = distToNextCoordWindow
						
						tmpArcLength = 0
						while tmpCtrBackward > 0 and tmpInd >= 0:
							# lineDist = getDistance(...) between tmpInd and tmpInd+1
							# currLineRatioDist = lineDist*tmpLineRatio
							if tmpArcLength + tmpLineRatioDist > shiftArclengthStepWindow:
								# dont change ind but change remaining tmpLineRatioDist and maybe other stuff and lower tmpCtr etc
								lengthNeeded = shiftArclengthStepWindow - tmpArcLength
								lengthRemaining = tmpLineRatioDist - lengthNeeded # left over length from tmpInd to tmpInd+1
								
								p1 = copy.deepcopy(edgeViewInnie[tmpInd][0])
								p2 = copy.deepcopy(edgeViewInnie[tmpInd+1][0])
								distBetween = getDistance(p1[0], p2[0], p1[1], p2[1])
								tmpRatio = lengthRemaining/distBetween
								
								tmpShiftCoord = [p1[0] + (p2[0] - p1[0])*tmpRatio, p1[1] + (p2[1] - p1[1])*tmpRatio]
								seedIsAfterStepCoordN = None
								
								for stepCoordInd in range(1, len(stepCoordsWindow)):
									if tmpInd < stepCoordsWindow[stepCoordInd][1] or (tmpInd == stepCoordsWindow[stepCoordInd][1] and lengthRemaining < stepCoordsWindow[stepCoordInd][2]):
										# shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], ])
										seedIsAfterStepCoordN = stepCoordInd-1
										break
								if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsWindow[-1][1] or (tmpInd == stepCoordsWindow[-1][1] and  lengthRemaining >= stepCoordsWindow[-1][2]) ):
									seedIsAfterStepCoordN = len(stepCoordsWindow)-1
								
								if seedIsAfterStepCoordN is not None:
									shiftedSeedPairs.insert(0, [tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery, tmpInd, queryMainSeed[1], lengthRemaining, queryMainSeed[2]]) # what other dat was needed again? how do i get isAfterStepCoordN from this??? manually iterate??
								
								tmpLineRatioDist = lengthRemaining
								tmpArcLength = 0
								tmpCtrBackward-=1
							elif tmpArcLength + tmpLineRatioDist == shiftArclengthStepWindow:
								tmpShiftCoord = copy.deepcopy(edgeViewInnie[tmpInd][0])
								seedIsAfterStepCoordN = None
								
								for stepCoordInd in range(1, len(stepCoordsWindow)):
									if tmpInd < stepCoordsWindow[stepCoordInd][1] or (tmpInd == stepCoordsWindow[stepCoordInd][1] and 0 < stepCoordsWindow[stepCoordInd][2]): # lengthRemaining is 0 in this case
										
										seedIsAfterStepCoordN = stepCoordInd-1
										break
								if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsWindow[-1][1] or (tmpInd == stepCoordsWindow[-1][1] and  0 >= stepCoordsWindow[-1][2]) ): # >= for readability but is effectively ==
									seedIsAfterStepCoordN = len(stepCoordsWindow)-1
								
								if seedIsAfterStepCoordN is not None: # should always be true
									shiftedSeedPairs.insert(0, [tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery, tmpInd, queryMainSeed[1], 0, queryMainSeed[2]])
								tmpCtrBackward-=1
								tmpInd-=1
								tmpArcLength=0
								if tmpInd >=0 and tmpCtrBackward > 0:
									tmpLineRatioDist = getDistance(edgeViewInnie[tmpInd][0][0], edgeViewInnie[tmpInd+1][0][0], edgeViewInnie[tmpInd][0][1], edgeViewInnie[tmpInd+1][0][1])
							else:
								# add tmpLineRatioDist to tmpArcLength and lower ind
								tmpArcLength+=tmpLineRatioDist
								tmpInd-=1
								if tmpInd >=0 and tmpCtrBackward > 0:
									tmpLineRatioDist = getDistance(edgeViewInnie[tmpInd][0][0], edgeViewInnie[tmpInd+1][0][0], edgeViewInnie[tmpInd][0][1], edgeViewInnie[tmpInd+1][0][1])
							
						
						############# now reverse
						
						
						tmpCtrForward = shiftAmtRadius
						tmpInd = baseSeedIsAfterContourIndWindow #
						
						tmpLineRatioDist = getDistance(edgeViewInnie[baseSeedIsAfterContourIndWindow][0][0], edgeViewInnie[baseSeedIsAfterContourIndWindow+1][0][0], edgeViewInnie[baseSeedIsAfterContourIndWindow][0][1], edgeViewInnie[baseSeedIsAfterContourIndWindow+1][0][1]) - distToNextCoordWindow # want dist from seed to the next ind after, not before like last time
						tmpArcLength = 0
						while tmpCtrForward > 0 and tmpInd < edgeViewInnie.shape[0]-1:
							# lineDist = getDistance(...) between tmpInd and tmpInd+1
							# currLineRatioDist = lineDist*tmpLineRatio
							if tmpArcLength + tmpLineRatioDist > shiftArclengthStepWindow:
								# dont change ind but change remaining tmpLineRatioDist and maybe other stuff and lower tmpCtr etc
								lengthNeeded = shiftArclengthStepWindow - tmpArcLength
								lengthRemaining = tmpLineRatioDist - lengthNeeded # left over length from tmpInd to tmpInd+1
								
								p1 = copy.deepcopy(edgeViewInnie[tmpInd][0])
								p2 = copy.deepcopy(edgeViewInnie[tmpInd+1][0])
								distBetween = getDistance(p1[0], p2[0], p1[1], p2[1])
								tmpRatio = lengthRemaining/distBetween # this time, its from ind+1 to ind!
								
								tmpShiftCoord = [p1[0] + (p2[0] - p1[0])*(1-tmpRatio), p1[1] + (p2[1] - p1[1])*(1-tmpRatio)] #........ VECTOR STUFF, DISTANCE LENGTHREMAINING FROM TMPIND IN DIRECTION OF TMPIND+1
								seedIsAfterStepCoordN = None
								
								for stepCoordInd in range(1, len(stepCoordsWindow)):
									if tmpInd < stepCoordsWindow[stepCoordInd][1] or (tmpInd == stepCoordsWindow[stepCoordInd][1] and (distBetween-lengthRemaining) < stepCoordsWindow[stepCoordInd][2]):
										# shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], ])
										seedIsAfterStepCoordN = stepCoordInd-1
										break
								if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsWindow[-1][1] or (tmpInd == stepCoordsWindow[-1][1] and  (distBetween-lengthRemaining) >= stepCoordsWindow[-1][2]) ):
									seedIsAfterStepCoordN = len(stepCoordsWindow)-1
								
								if seedIsAfterStepCoordN is not None: # should always be true
									shiftedSeedPairs.append([tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery, tmpInd, queryMainSeed[1], distBetween-lengthRemaining, queryMainSeed[2]]) # what other dat was needed again? how do i get isAfterStepCoordN from this??? manually iterate??
								
								tmpLineRatioDist = lengthRemaining
								tmpArcLength = 0
								tmpCtrForward-=1
							elif tmpArcLength + tmpLineRatioDist == shiftArclengthStepWindow:
								tmpShiftCoord = copy.deepcopy(edgeViewInnie[tmpInd+1][0])
								seedIsAfterStepCoordN = None
								
								for stepCoordInd in range(1, len(stepCoordsWindow)):
									if tmpInd+1 < stepCoordsWindow[stepCoordInd][1] or (tmpInd+1 == stepCoordsWindow[stepCoordInd][1] and 0 < stepCoordsWindow[stepCoordInd][2]): # lengthRemaining is 0 in this case
										
										seedIsAfterStepCoordN = stepCoordInd-1
										break
								if seedIsAfterStepCoordN is None and (tmpInd+1 > stepCoordsWindow[-1][1] or (tmpInd+1 == stepCoordsWindow[-1][1] and  0 >= stepCoordsWindow[-1][2]) ): # >= for readability but is effectively ==
									seedIsAfterStepCoordN = len(stepCoordsWindow)-1
								
								if seedIsAfterStepCoordN is not None: # should always be true
									shiftedSeedPairs.append([tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery, tmpInd, queryMainSeed[1], getDistance(edgeViewInnie[tmpInd][0][0], edgeViewInnie[tmpInd+1][0][0], edgeViewInnie[tmpInd][1], edgeViewInnie[tmpInd+1][0][1]), queryMainSeed[2]])
								tmpCtrForward-=1
								tmpInd+=1
								tmpArcLength=0
								if tmpCtrForward > 0 and tmpInd < edgeViewInnie.shape[0]-1:
									tmpLineRatioDist = getDistance(edgeViewInnie[tmpInd][0][0], edgeViewInnie[tmpInd+1][0][0], edgeViewInnie[tmpInd][0][1], edgeViewInnie[tmpInd+1][0][1])
							else:
								# add tmpLineRatioDist to tmpArcLength and lower ind
								tmpArcLength+=tmpLineRatioDist
								tmpInd+=1
								if tmpCtrForward > 0 and tmpInd < edgeViewInnie.shape[0]-1:
									tmpLineRatioDist = getDistance(edgeViewInnie[tmpInd][0][0], edgeViewInnie[tmpInd+1][0][0], edgeViewInnie[tmpInd][0][1], edgeViewInnie[tmpInd+1][0][1])
						
						# NOW CHECK IF ONE SIDE FAILED I.E. COUNTER DIDNT REACH 0, AND HANDLE ACCORDINGLY
						
						if tmpCtrBackward != 0 and len(shiftedSeedPairs)==( 1 + shiftAmtRadius + (shiftAmtRadius-tmpCtrBackward) ): # shift other edge forward to compensate, we should have 1 base seedpair + full shifts from other side + however many were completed on this side
							# HERE       set the index in the query so it carries on from where we got up to, so
							# if we only got 1 our of the 3 required shifts backwards previously, then first new pair would be main seed from window with 2 shifts of query
							# OR !!!! BETTER? instead just keep the last/most recent seed in that direction from window then only need to shift 1+ times from the main seed in query? <<< yeah doing this
							# ALSO FIX APPENDS BELOW!!!!! AND ABOVE!!!! (COPIED BELOW FROM ABOVE)
							
							pseudoMainSeedWindow = shiftedSeedPairs[0] # we will only be using the window part of this, this actually contains data about a query seed instance that we dont need right now
							
							tmpCtrForward = tmpCtrBackward
							tmpInd = queryMainSeed[1] # indbefore query seed in query edge
							# tmpLineDist = getDistance(...) between tmpInd and tmpInd+1
							# tmpLineRatio = ratioToNextCoordWindow
							tmpLineRatioDist = getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][0][1], edgeViewOutie[tmpInd+1][0][1]) - queryMainSeed[2] # want dist from seed to the next ind after, not before like last time
							tmpArcLength = 0
							while tmpCtrForward > 0 and tmpInd < edgeViewOutie.shape[0]-1:
								# lineDist = getDistance(...) between tmpInd and tmpInd+1
								# currLineRatioDist = lineDist*tmpLineRatio
								if tmpArcLength + tmpLineRatioDist > shiftArclengthStepQuery:
									# dont change ind but change remaining tmpLineRatioDist and maybe other stuff and lower tmpCtr etc
									lengthNeeded = shiftArclengthStepQuery - tmpArcLength
									lengthRemaining = tmpLineRatioDist - lengthNeeded # left over length from tmpInd to tmpInd+1
									
									p1 = copy.deepcopy(edgeViewOutie[tmpInd][0])
									p2 = copy.deepcopy(edgeViewOutie[tmpInd+1][0])
									distBetween = getDistance(p1[0], p2[0], p1[1], p2[1])
									tmpRatio = lengthRemaining/distBetween # this time, its from ind+1 to ind!
									
									tmpShiftCoord = [p1[0] + (p2[0] - p1[0])*(1-tmpRatio), p1[1] + (p2[1] - p1[1])*(1-tmpRatio)] #........ VECTOR STUFF, DISTANCE LENGTHREMAINING FROM TMPIND IN DIRECTION OF TMPIND+1
									seedIsAfterStepCoordN = None
									
									for stepCoordInd in range(1, len(stepCoordsQuery)):
										if tmpInd < stepCoordsQuery[stepCoordInd][1] or (tmpInd == stepCoordsQuery[stepCoordInd][1] and (distBetween-lengthRemaining) < stepCoordsQuery[stepCoordInd][2]):
											# shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], ])
											seedIsAfterStepCoordN = stepCoordInd-1
											break
									if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsQuery[-1][1] or (tmpInd == stepCoordsQuery[-1][1] and	(distBetween-lengthRemaining) >= stepCoordsQuery[-1][2]) ):
										seedIsAfterStepCoordN = len(stepCoordsQuery)-1
									
									if seedIsAfterStepCoordN is not None: # should always be true
										shiftedSeedPairs.append([pseudoMainSeedWindow[0], tmpShiftCoord, pseudoMainSeedWindow[2], seedIsAfterStepCoordN, pseudoMainSeedWindow[4], tmpInd, pseudoMainSeedWindow[6], distBetween-lengthRemaining]) # remember, query is every 2nd value, keep format same as in first 2 shift attempts above@@@
									
									tmpLineRatioDist = lengthRemaining
									tmpArcLength = 0
									tmpCtrForward-=1
								elif tmpArcLength + tmpLineRatioDist == shiftArclengthStepQuery:
									tmpShiftCoord = copy.deepcopy(edgeViewOutie[tmpInd+1][0])
									seedIsAfterStepCoordN = None
									
									for stepCoordInd in range(1, len(stepCoordsQuery)):
										if tmpInd+1 < stepCoordsQuery[stepCoordInd][1] or (tmpInd+1 == stepCoordsQuery[stepCoordInd][1] and 0 < stepCoordsQuery[stepCoordInd][2]): # lengthRemaining is 0 in this case
											
											seedIsAfterStepCoordN = stepCoordInd-1
											break
									if seedIsAfterStepCoordN is None and (tmpInd+1 > stepCoordsQuery[-1][1] or (tmpInd+1 == stepCoordsQuery[-1][1] and	0 >= stepCoordsQuery[-1][2]) ): # >= for readability but is effectively ==
										seedIsAfterStepCoordN = len(stepCoordsQuery)-1
									
									if seedIsAfterStepCoordN is not None: # should always be true
										shiftedSeedPairs.append([pseudoMainSeedWindow[0], tmpShiftCoord, pseudoMainSeedWindow[2], seedIsAfterStepCoordN, pseudoMainSeedWindow[4], tmpInd, pseudoMainSeedWindow[6], getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][1], edgeViewOutie[tmpInd+1][0][1])]) # remember, query is every 2nd value, keep format same as in first 2 shift attempts above@@@
									tmpCtrForward-=1
									tmpInd+=1
									tmpArcLength=0
									if tmpCtrForward > 0 and tmpInd < edgeViewOutie.shape[0]-1:
										tmpLineRatioDist = getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][0][1], edgeViewOutie[tmpInd+1][0][1])
								else:
									# add tmpLineRatioDist to tmpArcLength and lower ind
									tmpArcLength+=tmpLineRatioDist
									tmpInd+=1
									if tmpCtrForward > 0 and tmpInd < edgeViewOutie.shape[0]-1:
										tmpLineRatioDist = getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][0][1], edgeViewOutie[tmpInd+1][0][1])
								
						elif tmpCtrForward != 0 and len(shiftedSeedPairs)==( 1 + shiftAmtRadius + (shiftAmtRadius-tmpCtrForward) ):
							tmpCtrBackward = tmpCtrForward
							tmpInd = queryMainSeed[1]
							# tmpLineDist = getDistance(...) between tmpInd and tmpInd+1
							# tmpLineRatio = ratioToNextCoordWindow
							tmpLineRatioDist = queryMainSeed[2] # dist from edge[ind] -> to seed, and in loop its from edge[ind-1] -> to edge[ind] (I do ind-=1 just before calcs so it actually said ind,ind+1 below)
							tmpArcLength = 0
							while tmpCtrBackward > 0 and tmpInd >= 0:
								# lineDist = getDistance(...) between tmpInd and tmpInd+1
								# currLineRatioDist = lineDist*tmpLineRatio
								if tmpArcLength + tmpLineRatioDist > shiftArclengthStepQuery:
									# dont change ind but change remaining tmpLineRatioDist and maybe other stuff and lower tmpCtr etc
									lengthNeeded = shiftArclengthStepQuery - tmpArcLength
									lengthRemaining = tmpLineRatioDist - lengthNeeded # left over length from tmpInd to tmpInd+1
									
									p1 = copy.deepcopy(edgeViewOutie[tmpInd][0])
									p2 = copy.deepcopy(edgeViewOutie[tmpInd+1][0])
									distBetween = getDistance(p1[0], p2[0], p1[1], p2[1])
									tmpRatio = lengthRemaining/distBetween
									
									tmpShiftCoord = [p1[0] + (p2[0] - p1[0])*tmpRatio, p1[1] + (p2[1] - p1[1])*tmpRatio] #........ VECTOR STUFF, DISTANCE LENGTHREMAINING FROM TMPIND IN DIRECTION OF TMPIND+1
									seedIsAfterStepCoordN = None
									
									for stepCoordInd in range(1, len(stepCoordsQuery)):
										if tmpInd < stepCoordsQuery[stepCoordInd][1] or (tmpInd == stepCoordsQuery[stepCoordInd][1] and lengthRemaining < stepCoordsQuery[stepCoordInd][2]):
											# shiftedSeedPairs.append([windowMainSeed[0], queryMainSeed[0], ])
											seedIsAfterStepCoordN = stepCoordInd-1
											break
									if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsQuery[-1][1] or (tmpInd == stepCoordsQuery[-1][1] and	lengthRemaining >= stepCoordsQuery[-1][2]) ):
										seedIsAfterStepCoordN = len(stepCoordsQuery)-1
									
									
									
									if seedIsAfterStepCoordN is not None: # should always be true		   MOST UP TO DATE FORMAT VVVVVVVVVVVVVVVVVVVVVVVV		  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
										# shiftedSeedPairs.insert(0, [tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery, tmpInd, queryMainSeed[1], lengthRemaining, queryMainSeed[2]]) # not sure if insert at 0, order gets a bit blurry/arbitrary when I've swapped the edge thats being shifted
										shiftedSeedPairs.insert(0, [pseudoMainSeedWindow[0], tmpShiftCoord, pseudoMainSeedWindow[2], seedIsAfterStepCoordN, pseudoMainSeedWindow[4], tmpInd, pseudoMainSeedWindow[6], lengthRemaining]) # not sure if insert at 0, order gets a bit blurry/arbitrary when I've swapped the edge thats being shifted
									
									tmpLineRatioDist = lengthRemaining
									tmpArcLength = 0
									tmpCtrBackward-=1
								elif tmpArcLength + tmpLineRatioDist == shiftArclengthStepQuery:
									tmpShiftCoord = copy.deepcopy(edgeViewOutie[tmpInd][0])
									seedIsAfterStepCoordN = None
									
									for stepCoordInd in range(1, len(stepCoordsQuery)):
										if tmpInd < stepCoordsQuery[stepCoordInd][1] or (tmpInd == stepCoordsQuery[stepCoordInd][1] and 0 < stepCoordsQuery[stepCoordInd][2]): # lengthRemaining is 0 in this case
											
											seedIsAfterStepCoordN = stepCoordInd-1
											break
									if seedIsAfterStepCoordN is None and (tmpInd > stepCoordsQuery[-1][1] or (tmpInd == stepCoordsQuery[-1][1] and	0 >= stepCoordsQuery[-1][2]) ): # >= for readability but is effectively ==
										seedIsAfterStepCoordN = len(stepCoordsQuery)-1
									
									
									if seedIsAfterStepCoordN is not None: # should always be true
										# shiftedSeedPairs.insert(0, [tmpShiftCoord, queryMainSeed[0], seedIsAfterStepCoordN, seedIsAfterStepCoordNquery])
										shiftedSeedPairs.insert(0, [pseudoMainSeedWindow[0], tmpShiftCoord, pseudoMainSeedWindow[2], seedIsAfterStepCoordN, pseudoMainSeedWindow[4], tmpInd, pseudoMainSeedWindow[6], 0])
									tmpCtrBackward-=1
									tmpInd-=1
									tmpArcLength=0
									if tmpInd >=0 and tmpCtrBackward > 0:
										tmpLineRatioDist = getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][0][1], edgeViewOutie[tmpInd+1][0][1])
								else:
									# add tmpLineRatioDist to tmpArcLength and lower ind
									tmpArcLength+=tmpLineRatioDist
									tmpInd-=1
									if tmpInd >=0 and tmpCtrBackward > 0:
										tmpLineRatioDist = getDistance(edgeViewOutie[tmpInd][0][0], edgeViewOutie[tmpInd+1][0][0], edgeViewOutie[tmpInd][0][1], edgeViewOutie[tmpInd+1][0][1])
						
						staticDataQuery = largePieceDatabase[largePieceDbIndOutie][1][pieceRepresentation][edgeIndOutie][4] # edge2
						staticDataWindow = largePieceDatabase[largePieceDbIndInnie][1][pieceRepresentation][edgeIndInnie][4] # edge1 [1] for data, [2] for staticData, DONT CHANGE ORDER OF DATA IN largePieceDatabase !! or will have to change stuff like this when its accessed
						
						rawDataQuery = largePieceDatabase[largePieceDbIndOutie][1][pieceRepresentation][edgeIndOutie][5] # edge2
						rawDataWindow = largePieceDatabase[largePieceDbIndInnie][1][pieceRepresentation][edgeIndInnie][5] # edge1 [1] for data, [2] for staticData, DONT CHANGE ORDER OF DATA IN largePieceDatabase !! or will have to change stuff like this when its accessed
						
						
						windowEdgeOrient = math.atan2(edgeViewInnie[edgeViewInnie.shape[0]-1][0][1] - edgeViewInnie[0][0][1], edgeViewInnie[edgeViewInnie.shape[0]-1][0][0] - edgeViewInnie[0][0][0]) # both should be 0 but adding in case changes in future
						queryEdgeOrient = math.atan2(edgeViewOutie[edgeViewOutie.shape[0]-1][0][1] - edgeViewOutie[0][0][1], edgeViewOutie[edgeViewOutie.shape[0]-1][0][0] - edgeViewOutie[0][0][0])
						
						while windowEdgeOrient <= -math.pi:
							windowEdgeOrient+=2*math.pi
						while windowEdgeOrient > math.pi:
							windowEdgeOrient-=2*math.pi
						while queryEdgeOrient <= -math.pi:
							queryEdgeOrient+=2*math.pi
						while queryEdgeOrient > math.pi:
							queryEdgeOrient-=2*math.pi
						
						if abs(windowEdgeOrient-math.pi)<0.0001:
							windowEdgeOrient=math.pi
						elif abs(windowEdgeOrient--math.pi)<0.0001:
							windowEdgeOrient=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
						
						if abs(queryEdgeOrient-math.pi)<0.0001:
							queryEdgeOrient=math.pi
						elif abs(queryEdgeOrient--math.pi)<0.0001:
							queryEdgeOrient=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
						
						baseWindowShift = queryEdgeOrient - windowEdgeOrient
						
						
						edge1PixelationError = params["edge1PixelationError"] # 1 pixel, I'm 99% sure nothing has been scaled or changed between contour detection and here, if weight is ever given to edge thickness then this will need to scale with size/area (pseudo dist from camera) of the piece/edge
						edge2PixelationError = params["edge2PixelationError"]
						
						tempDistinctSeedPairDatUpToShift = []
						
						for shiftedSeedPairDat in shiftedSeedPairs:
							
							# topNinstanceDat = similarityInstance(seedCoord1, seedCoord2, staticData1, staticData2, angleWiggleRoom, orientationWiggleRoom, windowAmount, stepCoords1, rawDat1, stepCoords2, rawDat2, stepLength1, stepLength2, estimatedScale, edge1PixelationError, edge2PixelationError, edge1SeedIsAfterStepCoordIndN, edge2SeedCntIndDat, edge2SeedIsAfterStepCoordIndN)
							orientationWiggleRoom = None
							stepLength1 = stepLengthWindow
							stepLength2 = stepLengthQuery
							edge2SeedCntIndDat = None # \/ is this here for readability? why not out of loop, cant remember
							angleWiggleRoom = [baseWindowShift-params['maxAngleShiftFromAssumedMatch'], baseWindowShift+params['maxAngleShiftFromAssumedMatch']] # range that window edge orientation can be shifted by, if both edges are same orientation then (in deg here for readability) [-30, 30], if window edge appears in photo 90 degrees clockwise to query edge then need to also shift by +90 deg [60, 120]
							
							if angleWiggleRoom[0] <= math.pi:
								angleWiggleRoom[0] += 2*math.pi
							if angleWiggleRoom[0] > math.pi:
								angleWiggleRoom[0] -= 2*math.pi
							if angleWiggleRoom[1] <= math.pi:
								angleWiggleRoom[1] += 2*math.pi
							if angleWiggleRoom[1] > math.pi:
								angleWiggleRoom[1] -= 2*math.pi
							if abs(angleWiggleRoom[0]-math.pi)<0.0001:
								angleWiggleRoom[0]=math.pi
							elif abs(angleWiggleRoom[0]--math.pi)<0.0001:
								angleWiggleRoom[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							if abs(angleWiggleRoom[1]-math.pi)<0.0001:
								angleWiggleRoom[1]=math.pi
							elif abs(angleWiggleRoom[1]--math.pi)<0.0001:
								angleWiggleRoom[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

							
							windowSeedCoord, querySeedCoord, edge1SeedIsAfterStepCoordIndN, edge2SeedIsAfterStepCoordIndN, contourIndBeforeSeedWindow, contourIndBeforeSeedQuery, distOnLineWindow, distOnLineQuery = shiftedSeedPairDat
							
							tic = time.perf_counter()
							
							topNinstanceDat = similarityInstance(windowSeedCoord, querySeedCoord, staticDataWindow, staticDataQuery, angleWiggleRoom, orientationWiggleRoom, windowAmount, stepCoordsWindow, rawDataWindow, stepCoordsQuery, rawDataQuery, stepLength1, stepLength2, estimatedScale, edge1PixelationError, edge2PixelationError, edge1SeedIsAfterStepCoordIndN, edge2SeedCntIndDat, edge2SeedIsAfterStepCoordIndN, edgeViewInnie, edgeViewOutie, params, None) # None = ...
							
							toc = time.perf_counter()
							
							totalTimeSimilarityInstanceCall+=toc-tic
							amountSimilarityInstanceCall+=1
							
							# items: [finalVariance, shiftWindowBy, impliedScale]
							# add this dat to a list, but i think testDat is actually indices or something just convert into whatever input does to firstSweepCompatibility.. @@@@@@@@@@@@@
							
							# testDat:
							# each item is a list of schemas for a distinct seedpair being shifted where the schemas are a list:
							# queryEdgeID, windowEdgeID, queryPieceID, windowPieceID, querySeedCoord, windowSeedCoord, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace = seedInstance
							# largePieceDatabase[i][1][j][k].append(staticData)
							#largePieceDatabase[i][1][j][k] = [edgeKey, innieOrOutie]
							# trackerAndOtherData['innies'].append([len(largePieceDatabase)-1, potentialCornerRepresentation] + tempDat)
							
							
							windowPieceID = largePieceDbIndInnie # currently no corner representation considered in firstSweepCompatibility !@@!!@
							windowEdgeID = edgeIDKeyToInt[pieceEdgeKeyInnie]
							
							queryPieceID = largePieceDbIndOutie
							queryEdgeID = edgeIDKeyToInt[pieceEdgeKeyOutie]
							
							# think im merging all topNinstanceDats for now?
							if topNinstanceDat is not None:
								for instanceDat in topNinstanceDat: # tempDistinctSeedPairDatUpToShift is uniqueSeedUpToShift in testDat in firstSweepCompatibility !@!@!!@!@!@
									tempDistinctSeedPairDatUpToShift.append([windowEdgeID, queryEdgeID, windowPieceID, queryPieceID, windowSeedCoord, querySeedCoord, instanceDat[1], instanceDat[2], instanceDat[3]])
									
							
						# seedPairDatPerDistinctSeed.append([ [windowMainSeed, queryMainSeed], tempDistinctSeedPairDatUpToShift ]) # mainseeds currently just to be used as a unique identifier, prob better to use whatever their indices are or something
						testDat.append([ [windowMainSeed, queryMainSeed], tempDistinctSeedPairDatUpToShift ]) # mainseeds currently just to be used as a unique identifier, prob better to use whatever their indices are or something
					
					groupedSeedsIntervals, topResult = firstSweepCompatibility(testDat, compatCache, params, stepCoordsQuery, stepCoordsWindow, edgeViewOutie, edgeViewInnie) # ...
					if topResult is not None:
						
						# topResult[-1] (meanTotal) is the average dist between roughly closest pts in query space (window stepcoords scaled to query space), so need to normalise this w.r.t. query edge size so it can be compared
						# to other results that have also been normalised to their query edges
						
						normalisedEuclidDistDiff = topResult[-1]/queryDistFromCameraNormalisationVal # goal is so all pieces normalised to effectively be same dist from camera. if this value is dist from camera then theyd all be normalised to 1 unit of distance, if all pieces had same area we could instead use that and theyd all be normalised to the same value, probably whatever dist from camera would make the area == 1 unit
						matchRankings.append([normalisedEuclidDistDiff, windowPieceID, queryPieceID, windowEdgeID, queryEdgeID, pieceRepresentation, pieceRepresentation]) # change to specific window/query rep in future
						
						
						largePieceDatabase[largePieceDbIndInnie][2].append([normalisedEuclidDistDiff, windowPieceID, queryPieceID, windowEdgeID, queryEdgeID, pieceRepresentation, pieceRepresentation]) # add more data if needed
						largePieceDatabase[largePieceDbIndOutie][2].append([normalisedEuclidDistDiff, windowPieceID, queryPieceID, windowEdgeID, queryEdgeID, pieceRepresentation, pieceRepresentation]) # might not need to put in both, remove this if worth
						# maybe do stuff here when thresholds can be established
						
				
	matchRankings.sort()
	#...
	print(tmpDebugCounter)
	print("matchRankings: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
	print(matchRankings)
	# print(timesPastWiggleLen2)
	# print(tmpdebug1)
	# print(tmpdebug2)
	# print(tmpdebug3)
	# print(tmpdebug4)
	# print(tmpdebug5)
	# print(tmpdebuglist)
	# print("windowMatchesGlobalTracker:")
	# print(windowMatchesGlobalTracker)
	# print("limwigroom slow before first pair, slow after first pair and fast:")
	# print(limwigroomSlowBeforeFirstPair)
	# print(limwigroomSlow)
	# print(limwigroomFast)
	# exit()
	
	
	
	
	print("windowSlide")
	print(windowSlide)
	
	print("allWhileLoopChains")
	print(allWhileLoopChains)
	
	print("allChainsAtLeastSize1")
	print(allChainsAtLeastSize1)
	
	print("allChainsAtLeastSize2")
	print(allChainsAtLeastSize2)
	
	print("allChainsAtLeastSize3")
	print(allChainsAtLeastSize3)
	
	print("allChainsAtLeastSize4")
	print(allChainsAtLeastSize4)
	
	print("allChainsAtLeastSize5")
	print(allChainsAtLeastSize5)
	
	print("allChainsAtLeastSize6")
	print(allChainsAtLeastSize6)
	
	print("totalTimeSimilarityInstanceCall")
	print(totalTimeSimilarityInstanceCall)
	
	print("amountSimilarityInstanceCall")
	print(amountSimilarityInstanceCall)
	
	print("totalTimeLastSectionOfSimilarityInstance")
	print(totalTimeLastSectionOfSimilarityInstance)
	
	print("amountLastSectionOfSimilarityInstance")
	print(amountLastSectionOfSimilarityInstance)
	
	print("tempTimeKeep")
	print(tempTimeKeep)
	
	print("tempTimeKeepAmount")
	print(tempTimeKeepAmount)
	
	print("idktempCalls")
	print(idktempCalls)
	
	print("idktempConditional")
	print(idktempConditional)
	
	print("idktempTimeKeep")
	print(idktempTimeKeep)
	
	exit()
	
	
	chooseCurrentBestSolutionAndThresholds(matchRankings, None)
	
	return


def matchingThreshold(allTestsList, largePieceDatabase, samplePieceAmt, totalPieces):
	onlyScores = []
	for test in allTestsList:
		onlyScores.append(test[0])
	
	onlyScores = np.asarray(onlyScores).reshape(-1, 1)
	
	# putting this here instead, hopefully doesnt mess up anything
	onlyScores = np.sort(onlyScores)
	onlyScores = onlyScores[:round(onlyScores.size/10)] # slice off last 10% of array, no outliers and since last 75%+ of the array is non-matching pairs this wont change distributions or statistics much, even in perfect detail with 100% matches itll just leave 90% of the matches which is fine
	
	gmm = mixture.GaussianMixture(n_components=2, max_iter=1000, covariance_type='full').fit(onlyScores)
	
	print('means')
	print(gmm.means_)
	#print(gmm.covariances_)
	print('std')
	print(np.sqrt(gmm.covariances_))
	
	# onlyScores = np.sort(onlyScores)
	# onlyScores = onlyScores[:round(onlyScores.size/10)] # slice off last 10% of array, no outliers and since last 75%+ of the array is non-matching pairs this wont change distributions or statistics much, even in perfect detail with 100% matches itll just leave 90% of the matches which is fine
	
	# if: lower mean (i.e. better sim score) + 1 or 2 std deviations (i.e. neighbourhood) contains more scores OR has wider std deviation/spread, OR ... too much overlap? 
	# set threshold to something simple like top quartile or something, should be mostly right (erring on less matches->less false positives rather than capturing more matches but also more false positives)
	# for most cases INCLUDING only a few matches with the rest fails, thats why cant do top N or top X%, need to take advantage of the gap (or low density gaussian mixture overlap) between group of matches and group of non-matches
	
	# else:
	# use the means and std dev info to set threshold. err on side of no false positives because I want to use the assumption that these are most likely matches, but that assumption moreso comes into play when
	# these same principles in this if/else are used for scores calced from full edges with a bit more detail. maybe assess if theres a pseudo gap (low density zone if not real gap) between the 2 clusters
	# if so, set threshold to edge of matching cluster, if not, set in a way that avoids uncertain zone in overlap between the clusters or something, defintiely closer to 0 than first gap scenario, maybe somewhere between
	# 1-2 std dev from matching cluster mean, depending on std dev defn for gaussian distributions
	
	matchMeanAssumed = None
	matchStdDevAssumed = None
	noMatchMeanAssumed = None
	noMatchStdDevAssumed = None
	
	if gmm.means_[0][0] < gmm.means_[1][0]:
		matchMeanAssumed = gmm.means_[0][0]
		matchStdDevAssumed = gmm.covariances_[0][0][0]
		noMatchMeanAssumed = gmm.means_[1][0]
		noMatchStdDevAssumed = gmm.covariances_[1][0][0]
	else:
		matchMeanAssumed = gmm.means_[1][0]
		matchStdDevAssumed = gmm.covariances_[1][0][0]
		noMatchMeanAssumed = gmm.means_[0][0]
		noMatchStdDevAssumed = gmm.covariances_[0][0][0]
	
	matchStdDevAssumed=math.sqrt(matchStdDevAssumed)
	noMatchStdDevAssumed=math.sqrt(noMatchStdDevAssumed)
	
	amountInMatchingNeighbourhood = 0
	amountInNonMatchingNeighbourhood = 0
	
	# match1stdDevRange = (matchMeanAssumed-matchStdDevAssumed, matchMeanAssumed+matchStdDevAssumed)
	# noMatch1stdDevRange = (noMatchMeanAssumed-noMatchStdDevAssumed, noMatchMeanAssumed+noMatchStdDevAssumed)
	
	match1StdDevThreshold = matchMeanAssumed+matchStdDevAssumed # was going to do a radius neighbourhood of 1 std dev but since matches capped at 0 difference just doing all better than matchMeanAssumed+matchStdDevAssumed and all worse than noMatchMeanAssumed-noMatchStdDevAssumed
	noMatch1StdDevThreshold = noMatchMeanAssumed-noMatchStdDevAssumed
	
	for test in allTestsList:
		if test[0] <= match1StdDevThreshold:
			amountInMatchingNeighbourhood+=1
		if test[0] >= noMatch1StdDevThreshold:
			amountInNonMatchingNeighbourhood+=1
	
	maxPairsForSampleSize = min(math.ceil(2*(len(largePieceDatabase)-math.sqrt(len(largePieceDatabase)))), len(allTestsList))
	expectedPairsForSampleSize = 2*(samplePieceAmt - math.sqrt(samplePieceAmt))*(samplePieceAmt/totalPieces)
	
	currMatchingScoreEstimate = None
	
	if matchStdDevAssumed >= noMatchStdDevAssumed or amountInMatchingNeighbourhood >= amountInNonMatchingNeighbourhood: # maybe add more conditions for an incorrect result from clustering like overlap or something if needed
		print("weird result from clustering via expectation maximisation, default to rough estimate")
		
		# notes, or simply max pairs for sample size given
		currMatchingScoreEstimate=onlyScores[max(round((maxPairsForSampleSize+expectedPairsForSampleSize)/2), 1)]
		# rather than iterating until no conflicts, have a soft goal of minimising conflicts but pause and get human feedback at intervals/checkpoints prob based on time passed or something
		# resolve highest score conflicts first since lower score conflicts could just be junk edges from assumed match list/topN list being too big
		
	else:
		# notes
		if matchMeanAssumed-2*matchStdDevAssumed > noMatchMeanAssumed+2*noMatchStdDevAssumed: # this is expected case so just do average between those 2 values as threshold
			currMatchingScoreEstimate = (matchMeanAssumed-2*matchStdDevAssumed + noMatchMeanAssumed+2*noMatchStdDevAssumed)/2
		else: # use between 1 and 2 stddev below matchingcentre
			currMatchingScoreEstimate = (matchMeanAssumed-1*matchStdDevAssumed + matchMeanAssumed-2*matchStdDevAssumed)/2
	
	return currMatchingScoreEstimate

def computeTopBlocks(topScoresView, largePieceDatabase, ...):
	topBlocks = [] # items: [blockSize(or degree), blockStructure(the pieces and their arrangement)]
	
	# first check if even 1 single 2x2 or bigger block with perfect constraints i.e. no conflicts, each pair is the best pair for both of the edges in the pair, etc
	# if none, pass through again with different constraints
	
	alreadyInAblockSet = set()
	
	# build clockwise
	# WILL PROBABLY BE SOME DUPE LOOPS since a test in topScoresView could occur somewhere in chain for another test starting pair but rare enough to not matter
	for test in topScoresView:
		# iterate the 4 sides to try and find 3 clockwise pieces that can be chained and satisfy requirements
		
		# get list of tests wherever I stored them for each edge in each piece, then AS WELL AS REQUIREMENTS, check if each test is in topScoresView! Here we can simply check if test[0] > currMatchingScoreEstimate
		# BUT later might have to store/track this in a set() for fast checks.
		
		edgeSideKey1 = largePieceDatabase[test[1]][1][0][test[2]][0] # topEdge leftEdge etc
		edgeSideKey2 = largePieceDatabase[test[3]][1][0][test[4]][0] # topEdge leftEdge etc
		
		nextEdgeKeyPiece2 = None
		if edgeSideKey2 == "topEdge":
			nextEdgeKeyPiece2="leftEdge"
		elif edgeSideKey2 == "rightEdge":
			nextEdgeKeyPiece2="topEdge"
		elif edgeSideKey2 == "bottomEdge":
			nextEdgeKeyPiece2="rightEdge"
		elif edgeSideKey2 == "leftEdge":
			nextEdgeKeyPiece2="bottomEdge"
		else:
			print("edge key issue 29wuj12")
			exit()
		
		nextEdgeKeyPiece1 = None
		if edgeSideKey1 == "topEdge":
			nextEdgeKeyPiece1="leftEdge"
		elif edgeSideKey1 == "rightEdge":
			nextEdgeKeyPiece1="topEdge"
		elif edgeSideKey1 == "bottomEdge":
			nextEdgeKeyPiece1="rightEdge"
		elif edgeSideKey1 == "leftEdge":
			nextEdgeKeyPiece1="bottomEdge"
		else:
			print("edge key issue 88wut5j1")
			exit()
		
		nextEdgePiece2PrelimCompatListInd = None
		for tmpI, tmpEdge in enumerate(largePieceDatabase[test[3]][1][0]):
			if tmpEdge[0] == nextEdgeKeyPiece2:
				nextEdgePiece2PrelimCompatListInd=tmpI
				break
		if nextEdgePiece2PrelimCompatListInd is None:
			print("wat?dd3k3k3")
			exit()
		
		nextEdgePiece1PrelimCompatListInd = None
		for tmpI, tmpEdge in enumerate(largePieceDatabase[test[1]][1][0]):
			if tmpEdge[0] == nextEdgeKeyPiece1:
				nextEdgePiece1PrelimCompatListInd=tmpI
				break
		if nextEdgePiece1PrelimCompatListInd is None:
			print("wat?dt44t")
			exit()
		
		bestBlockStartingWithCurrentPair = None
		bestBlockScoreStartingWithCurrentPair = float("inf")
		
		nextEdgeTestList2 = prelimCompatPairsInniesAndOutiesInds[test[3]][nextEdgePiece2PrelimCompatListInd] # right-hand edge in the 2nd piece (if 1st piece is bottom and 2nd piece is stacked ontop)**
		for piece2EdgeTest in nextEdgeTestList2:
			# if in topN i.e. test[0] <= currMatchingScoreEstimate
			if piece2EdgeTest[6] <= currMatchingScoreEstimate:
				# if passes other reqs
					# find another piece that fits in the last empty space
				if True:
					largePieceDbInd3 = piece2EdgeTest[3]
					edgeInd3 = piece2EdgeTest[4]
					edgeSideKey3 = largePieceDatabase[largePieceDbInd3][1][0][edgeInd3][0]
					nextEdgeKeyPiece3 = None
					if edgeSideKey3 == "topEdge":
						nextEdgeKeyPiece3="leftEdge"
					elif edgeSideKey3 == "rightEdge":
						nextEdgeKeyPiece3="topEdge"
					elif edgeSideKey3 == "bottomEdge":
						nextEdgeKeyPiece3="rightEdge"
					elif edgeSideKey3 == "leftEdge":
						nextEdgeKeyPiece3="bottomEdge"
					else:
						print("edge key issue 88w2r3ut5j1")
						exit()
					nextEdgePiece3PrelimCompatListInd = None
					for tmpI, tmpEdge in enumerate(largePieceDatabase[largePieceDbInd3][1][0]):
						if tmpEdge[0] == nextEdgeKeyPiece3:
							nextEdgePiece3PrelimCompatListInd=tmpI
							break
					if nextEdgePiece3PrelimCompatListInd is None:
						print("wat?d2r3d3k3k3")
						exit()
					nextEdgeTestList3 = prelimCompatPairsInniesAndOutiesInds[largePieceDbInd3][nextEdgePiece3PrelimCompatListInd]
					for piece3EdgeTest in nextEdgeTestList3:
						if piece3EdgeTest[6] <= currMatchingScoreEstimate:
							
							if True:
								largePieceDbInd4 = piece3EdgeTest[3]
								edgeInd4 = piece3EdgeTest[4]
								edgeSideKey4 = largePieceDatabase[largePieceDbInd4][1][0][edgeInd4][0]
								nextEdgeKeyPiece4 = None
								if edgeSideKey4 == "topEdge":
									nextEdgeKeyPiece4="leftEdge"
								elif edgeSideKey4 == "rightEdge":
									nextEdgeKeyPiece4="topEdge"
								elif edgeSideKey4 == "bottomEdge":
									nextEdgeKeyPiece4="rightEdge"
								elif edgeSideKey4 == "leftEdge":
									nextEdgeKeyPiece4="bottomEdge"
								else:
									print("edge key issue 88w2r3ut5j1")
									exit()
								nextEdgePiece4PrelimCompatListInd = None
								for tmpI, tmpEdge in enumerate(largePieceDatabase[largePieceDbInd4][1][0]):
									if tmpEdge[0] == nextEdgeKeyPiece4:
										nextEdgePiece4PrelimCompatListInd=tmpI
										break
								if nextEdgePiece4PrelimCompatListInd is None:
									print("wat?d2r3d3k3k3")
									exit()
								nextEdgeTestList4 = prelimCompatPairsInniesAndOutiesInds[largePieceDbInd4][nextEdgePiece3PrelimCompatListInd]
								
								# since this is the connection between the 3rd and 4th piece, the last connection between the 4th and the 1st piece must also pass requirements
								finalRequiredNextEdgeKeyPiece1 = None
								if edgeSideKey1 == "topEdge":
									finalRequiredNextEdgeKeyPiece1="rightEdge"
								elif edgeSideKey1 == "rightEdge":
									finalRequiredNextEdgeKeyPiece1="bottomEdge"
								elif edgeSideKey1 == "bottomEdge":
									finalRequiredNextEdgeKeyPiece1="leftEdge"
								elif edgeSideKey1 == "leftEdge":
									finalRequiredNextEdgeKeyPiece1="topEdge"
								else:
									print("edge key issue 88wut5j1")
									exit()
								finalRequiredEdgePiece1PrelimCompatListInd = None
								for tmpI, tmpEdge in enumerate(largePieceDatabase[test[1]][1][0]):
									if tmpEdge[0] == finalRequiredNextEdgeKeyPiece1:
										finalRequiredEdgePiece1PrelimCompatListInd=tmpI
										break
								if finalRequiredEdgePiece1PrelimCompatListInd is None:
									print("wat?dt44t")
									exit()
								for piece4EdgeTest in nextEdgeTestList4:
									if piece4EdgeTest[6] <= currMatchingScoreEstimate:
										if piece4EdgeTest[3]==test[1] and piece4EdgeTest[4]==finalRequiredEdgePiece1PrelimCompatListInd:
											if True:
												tmpBlockScore = (test[0]+piece2EdgeTest[6]+piece3EdgeTest[6]+piece4EdgeTest[6])/4
												if tmpBlockScore<bestBlockScoreStartingWithCurrentPair:
													bestBlockScoreStartingWithCurrentPair=tmpBlockScore
													pair1PieceEdgeInds = (test[1], test[2], test[3], test[4])
													pair2PieceEdgeInds = (test[3], nextEdgePiece2PrelimCompatListInd, largePieceDbInd3, edgeInd3)
													pair3PieceEdgeInds = (largePieceDbInd3, nextEdgePiece3PrelimCompatListInd, largePieceDbInd4, edgeInd4)
													pair4PieceEdgeInds = (edgeInd4, nextEdgePiece4PrelimCompatListInd, test[1], finalRequiredEdgePiece1PrelimCompatListInd)
													
													bestBlockStartingWithCurrentPair=[tmpBlockScore, pair1PieceEdgeInds, pair2PieceEdgeInds, pair3PieceEdgeInds, pair4PieceEdgeInds]
													
		# NUMBERING BELOW CAN BE CONFUSING. 3 denotes the first piece left of piece1, it's the 3rd piece being added but it's being attached to piece1 this time rather than piece2 since its clockwise starting from piece1->piece3->piece4->piece2
		
		nextEdgeTestList1 = prelimCompatPairsInniesAndOutiesInds[test[1]][nextEdgePiece1PrelimCompatListInd] # left-hand edge in 1st piece (if 1st piece is bottom and 2nd piece is stacked ontop)**
		for piece1EdgeTest in nextEdgeTestList1:
			# if in topN i.e. test[0] <= currMatchingScoreEstimate
			if piece1EdgeTest[6] <= currMatchingScoreEstimate:
				# if passes other reqs
					# find another piece that fits in the last empty space
				if True:
					largePieceDbInd3 = piece1EdgeTest[3]
					edgeInd3 = piece1EdgeTest[4]
					edgeSideKey3 = largePieceDatabase[largePieceDbInd3][1][0][edgeInd3][0]
					nextEdgeKeyPiece3 = None
					if edgeSideKey3 == "topEdge":
						nextEdgeKeyPiece3="leftEdge"
					elif edgeSideKey3 == "rightEdge":
						nextEdgeKeyPiece3="topEdge"
					elif edgeSideKey3 == "bottomEdge":
						nextEdgeKeyPiece3="rightEdge"
					elif edgeSideKey3 == "leftEdge":
						nextEdgeKeyPiece3="bottomEdge"
					else:
						print("edge key issue 88w2r3ut5j1")
						exit()
					nextEdgePiece3PrelimCompatListInd = None
					for tmpI, tmpEdge in enumerate(largePieceDatabase[largePieceDbInd3][1][0]):
						if tmpEdge[0] == nextEdgeKeyPiece3:
							nextEdgePiece3PrelimCompatListInd=tmpI
							break
					if nextEdgePiece3PrelimCompatListInd is None:
						print("wat?d2r3d3k3k3")
						exit()
					nextEdgeTestList3 = prelimCompatPairsInniesAndOutiesInds[largePieceDbInd3][nextEdgePiece3PrelimCompatListInd]
					for piece3EdgeTest in nextEdgeTestList3:
						if piece3EdgeTest[6] <= currMatchingScoreEstimate:
							
							if True:
								largePieceDbInd4 = piece3EdgeTest[3]
								edgeInd4 = piece3EdgeTest[4]
								edgeSideKey4 = largePieceDatabase[largePieceDbInd4][1][0][edgeInd4][0]
								nextEdgeKeyPiece4 = None
								if edgeSideKey4 == "topEdge":
									nextEdgeKeyPiece4="leftEdge"
								elif edgeSideKey4 == "rightEdge":
									nextEdgeKeyPiece4="topEdge"
								elif edgeSideKey4 == "bottomEdge":
									nextEdgeKeyPiece4="rightEdge"
								elif edgeSideKey4 == "leftEdge":
									nextEdgeKeyPiece4="bottomEdge"
								else:
									print("edge key issue 88w2r3ut5j1")
									exit()
								nextEdgePiece4PrelimCompatListInd = None
								for tmpI, tmpEdge in enumerate(largePieceDatabase[largePieceDbInd4][1][0]):
									if tmpEdge[0] == nextEdgeKeyPiece4:
										nextEdgePiece4PrelimCompatListInd=tmpI
										break
								if nextEdgePiece4PrelimCompatListInd is None:
									print("wat?d2r3d3k3k3")
									exit()
								nextEdgeTestList4 = prelimCompatPairsInniesAndOutiesInds[largePieceDbInd4][nextEdgePiece4PrelimCompatListInd]
								
								# since this is the connection between the 3rd and 4th piece, the last connection between the 4th and the 1st piece must also pass requirements
								finalRequiredNextEdgeKeyPiece2 = None
								if edgeSideKey2 == "topEdge":
									finalRequiredNextEdgeKeyPiece2="rightEdge"
								elif edgeSideKey2 == "rightEdge":
									finalRequiredNextEdgeKeyPiece2="bottomEdge"
								elif edgeSideKey2 == "bottomEdge":
									finalRequiredNextEdgeKeyPiece2="leftEdge"
								elif edgeSideKey2 == "leftEdge":
									finalRequiredNextEdgeKeyPiece2="topEdge"
								else:
									print("edge key issue 88wut5j1")
									exit()
								finalRequiredEdgePiece2PrelimCompatListInd = None
								for tmpI, tmpEdge in enumerate(largePieceDatabase[test[3]][1][0]):
									if tmpEdge[0] == finalRequiredNextEdgeKeyPiece2:
										finalRequiredEdgePiece2PrelimCompatListInd=tmpI
										break
								if finalRequiredEdgePiece2PrelimCompatListInd is None:
									print("wat?dt44t")
									exit()
								for piece4EdgeTest in nextEdgeTestList4:
									if piece4EdgeTest[6] <= currMatchingScoreEstimate:
										if piece4EdgeTest[3]==test[3] and piece4EdgeTest[4]==finalRequiredEdgePiece2PrelimCompatListInd:
											if True:
												tmpBlockScore = (test[0]+piece1EdgeTest[6]+piece3EdgeTest[6]+piece4EdgeTest[6])/4
												if tmpBlockScore<bestBlockScoreStartingWithCurrentPair:
													bestBlockScoreStartingWithCurrentPair=tmpBlockScore
													pair1PieceEdgeInds = (test[1], nextEdgePiece1PrelimCompatListInd, largePieceDbInd3, edgeInd3)
													pair2PieceEdgeInds = (largePieceDbInd3, nextEdgePiece3PrelimCompatListInd, largePieceDbInd4, edgeInd4)
													pair3PieceEdgeInds = (largePieceDbInd4, nextEdgePiece4PrelimCompatListInd, test[3], finalRequiredEdgePiece2PrelimCompatListInd)
													pair4PieceEdgeInds = (test[3], test[4], test[1], test[2]) # THIS SHOULD TECHNICALLY BE 1,2,3,4 since its from 1,2 TO 3,4 but I don't think I'll be using the order of these pairs to infer anything
													
													bestBlockStartingWithCurrentPair=[tmpBlockScore, pair1PieceEdgeInds, pair2PieceEdgeInds, pair3PieceEdgeInds, pair4PieceEdgeInds]
													
		if bestBlockScoreStartingWithCurrentPair is not None:
			topBlocks.append(bestBlockScoreStartingWithCurrentPair)

def realSimilarityController(...):
	# samplePieceAmt, totalPieces, ...
	
	# basic data, if needed later more readable data can be created using these
	# will prob need trackers and stuff for tracking stuff such as which pieces have been temporarily ruled out as prob not being next to eachother and stuff so add that later
	
	# currentTestDat items are a list for each piece, that contains piece data and a list for edges
	# edges list contains each edge which is a list containing edge data and a list for tests with other compatible edges in other pieces
	# tests list contains items where each item is a list with test data e.g. a pointer/way to find the other edge/piece, the detail level that the test occured in, the results, etc
	currentTestDat = [	[pieceID, maybemorepiecedat, [ [edge1ID, maybemoreEdgedat, [  [otherPieceID, otherPieceEdgeID, detailLevel, results...], [another piece and edge test...], ...	] ], [edge2ID, ...], ... ]	]  ]
	
	# NEW just use prelimCompatPairsInniesAndOutiesInds, could also use a structure similar to it but since I want exact same structure I'll just use that for both compat and test dat
	# "The structure" being same piece/edge order and heirarchy as largePieceDatabase. Append test dat to this AND allTestsList cause want to sort allTestsList as well as sorting testDat for each specific edge in prelimCompatPairsInniesAndOutiesInds
	# PROB CHANGE NAME OF prelimCompatPairsInniesAndOutiesInds AT SOME POINT
	
	#^^^ will probably be sorting test data list for each edge so never point to that data using an index for that list, use data about the pair of edges then just iterate the test data list for each edge to find the sublist if needed
	
	# bit of data duplication but makes it easier to have this data freely available and sorted by best scores
	allTestsList = [ [simScore, piece1Ptr, edge1Ptr, piece2Ptr, edge2Ptr], [simScore_b, piece1Ptr_b, edge1Ptr_b, piece2Ptr_b, edge2Ptr_b], ... ]
	
	# continue..........
	
	# do loops later, for now hardcode
	
	### preliminary passthrough
	
	TAKE_SAMPLE = False
	samplePieceIDSet = None
	if something, doing sample (e.g. like <X% of the total pieces are in our photos, etc):
		create sample largePieceDatabase pieceID set
	
	copy innies/outies iteration and compat tests from current similarityController or wherever it is, but add sample checks
	
	for ...
		if TAKE_SAMPLE and pieceID1 in sample pieceID set:
			for ...
				if TAKE_SAMPLE and pieceID2 in sample pieceID set:
					if compatible:
						... prelim low detail tests
	
	#######################################################################################################
	
	# HEAVILY EDIT BELOW TO NEW PLAN
	
	# THINK OF WHAT THE FUNCTION TO DO FAST LOW DETAIL COMPARISON WILL LOOK LIKE
	
	# SEE IF A BUNCH OF STUFF CAN BE STORED IN A CACHE IF ANY CALCULATIONS ARE UNIQUE TO THE EDGE RATHER THAN THE PAIR OF EDGES
	
	^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
	
	# calc this then re-iterate rather than doing old method of testing compatibility and computing similarity in same loop
	# this way we can see if its way too big (then raise bar for compatibility to lower the pool of pairs to test)
	# but more importantly so we have this data for higher detail iterations and stuff, only need to test compatibility once per pair except in cases where detail level is raised we might also
	# want to change compatibility requirements
	
	prelimCompatPairsInniesAndOutiesInds = []
	
	for i in range(len(largePieceDatabase)):
		prelimCompatPairsInniesAndOutiesInds.append([])
		for j in range(len(largePieceDatabase[i][1][0])): # [0] cause only using 1 corner representation for now
			prelimCompatPairsInniesAndOutiesInds[-1].append([])
	
	# prelimCompatPairsInniesAndOutiesInds should be synced with largePieceDatabase now
	
	### Slicing compatibility
	compatibilityLevel = 0
	updateCompatibility(prelimCompatPairsInniesAndOutiesInds, trackerAndOtherData, compatibilityLevel, ...)
	
	### Slicing	compatibility
	
	### Slicing similarity 0
	detailLevel = 0
	updateSimilarityScore(..., dataRequired, similarityThreshold, detailLevel, ...) # similarityThreshold isnt actually used at detailLevel==0 obviously
	
	# MAKE SURE SIM SCORE/DIST AVG IS NORMALISED !!!!
	
	currMatchingScoreEstimate = matchingThreshold(allTestsList, largePieceDatabase, samplePieceAmt, totalPieces)
	
	topScoresView = []
	for test in allTestsList:
		if test[0] > currMatchingScoreEstimate:
			break
		topScoresView.append(test)
	
	# topScoresView should now be a view of the top N tests from allTestsList that have passed current compatibility constraints and have been updated to current detail level
	# ^ First we just tested the top N when allTestsList ordered by previous detail level, then we test down the list until 2 consecutive current detail level tests have no effect on top N composition
	
	
	topBlocks = computeTopBlocks(topScoresView, largePieceDatabase, ...)
	
	# Loop until topBlocks has at least 1 starting block
	# PROBABLY HAVE A SECTION IN THE LOOP TO PROMPT USER WITH CURRENT BEST MATCHES TO AVOID INFINITE LOOPS IN UNSOLVABLE CASE AND SINCE TESTS WILL BE HAPPENING THAT CHANGE BEST MATCHES
	
	while True:
		
		if len(topBlocks) > 0:
			topBlocks.sort()
			
			# prune dupes
			allEdgePairs = set()
			removeDupes = set()
			dupesDone = set()
			for blockInd, block in enumerate(topBlocks):
				if blockInd not in removeDupes:
					for edgePairInds in block[1:]:
						if edgePairInds in allEdgePairs or (edgePairInds[2], edgePairInds[3], edgePairInds[0], edgePairInds[1]) in allEdgePairs:
							if edgePairInds not in dupesDone and (edgePairInds[2], edgePairInds[3], edgePairInds[0], edgePairInds[1]) not in dupesDone:
								# iterate full list adding all dupe indices to removeDupes then remove the best index from removeDupes
								
								# DONT ADD CURRENT BEST IND TO removeDupes, AND ONLY ALLOW CURRENT BEST TO BE CURRENT BEST IF ITS IND IS NOT ALREADY IN removeDupes
								# this makes it so there's no conflict between previous removed dupes and whichever best block we re-add back, whatever is added to removeDupes will stay there
								# also, this method makes it possible for us to skip potentially valid groups of blocks since I don't retroactively go back and re-add valid non-dupe blocks if the best block from a previous dupe class is removed due to another dupe class
								# but will be rare enough to not matter
								
								tmpCurrentBestScore = block[0]
								tmpCurrentBestInd = blockInd
								for tmpBlockInd, tmpBlock in enumerate(topBlocks):
									if tmpBlockInd not in removeDupes:
										for tmpEdgePairInds in tmpBlock[1:]:
											if tmpEdgePairInds == edgePairInds or tmpEdgePairInds == (edgePairInds[2], edgePairInds[3], edgePairInds[0], edgePairInds[1]):
												if tmpBlock[0]<tmpCurrentBestScore:
													removeDupes.add(tmpCurrentBestInd)
													tmpCurrentBestInd=tmpBlockInd
													tmpCurrentBestScore=tmpBlock[0]
												else:
													removeDupes.add(tmpBlockInd)
												break
								
								# add edgePairInds to dupesDone (DONT add to allEdgePairs in above scan)
								dupesDone.add(edgePairInds)
								
								if blockInd in removeDupes: # if current block just got removed due to another pair in this block
									break
								
						else:
							# add edgePairInds to allEdgePairs
							allEdgePairs.add(edgePairInds)
						
			# create new list without dupes
			# something like (copied from stackoverflow) [ value for (i, value) in enumerate(lst) if i not in set(indices) ]
			noDupeTopBlocks = [ value for (i, value) in enumerate(topBlocks) if i not in removeDupes ]
			# topBlocks = new non-dupe list
			topBlocks = noDupeTopBlocks
			if len(topBlocks) > 0: # If there's at least 1 perfect block (just in case dupe method removed everything)
				
				break
				
		if True: # SANITY CHECK
			if len(topBlocks)>0:
				print("waytt??2i2i")
				exit()
		
		# topBlocks is currently empty so do more tests or whatever so we can try and find blocks again <<<<<<<<<<<<<<<<<<
		
		...
		
		# there should be new data now that changed the scenario in a way that improves the chances of finding at least 1 perfect starting block
		topBlocks = computeTopBlocks(topScoresView, largePieceDatabase, ...)
		
		# next loop, back to start of loop where dupes removed ...
		#END
		
	# first exhaust the 4 pairs in the block, and by 4 pairs i mean 1 edge from each pair?
	
	# expand blocks starting with best, making sure to update/prune topBlocks when blocks are absorbed into eachother
				# check notes for specifics about how to expand, next detail level test etc
	
	
	# \/\/\/\/\/
	# will prob need to put part of above and below in yet another while loop so if we dont get anywhere even if len(topBlocks)>0, we search for better topBlocks
	
	topBlocksInd = 0
	...initialise stuff...
	expansionTrees=[]
	while True:
		currentTree
		currentBlock
		...
		while True:
			# expand current block
			...
			
		
		compare all completed blocks up to current expansion...
		...
		
	
	Now top N similarity scores/top N pairs have been tested at medium detail level, and most of the pairs below the top N have only been tested at preliminary detail level.
	Potentially prompt user to see if a solution has been found at each iteration.
	Iteratively, check top N for conflicts, if conflict/s exist, seek to resolve the lowest detail level one? (how is this defined since a conflict arrises between 2 pairs, check notes,
	maybe trace to weakest assumption, i.e. instead of focussing where conflict occurred, find the single pair that could be removed from top N that would solve conflict and whose sim score is lowest)
	Resolve by discussion in notes, stuff like 2+ pairs to 1 piece for high confidence etc.
	If no conflict exists, ..., probably prompt user or have user decide at start what to do out of these 2: terminate, or arbitrarily search for more matches/conflictless puzzle layouts
	If all compatible edges tested, raise detail level of top N and start again solving conflicts and doing stuff when no conflict exists.
	
	Note: should compatibility requirements ever be lowered in the cases where tests exhausted?
	Cant use detail level to track which 
	### prelim passthrough done
	
	return


def expandBlock(startingBlock, largePieceDatabase, prelimCompatPairsInniesAndOutiesInds, params, ...):
	# structure similar to largePieceDatabase and prelimCompatPairsInniesAndOutiesInds
	# simple index to other piece, edge.
	# every time we create a new leaf/branch or retreat back in the tree we need to add/delete from this structure so it's consistent with current path/position in tree
	
	# THIS STRUCTURE IS DIFFERENT since there'll only be 1 other edge assigned to each edge we dont need a list at each structure[pieceID][edgeID], so instead setting it to None or (otherPieceID, otherEdgeID)
	
	localEdgeOrientationRepresentations = params["localEdgeOrientationRepresentations"]
	localEdgeOrientationRepresentationsReversed = params["localEdgeOrientationRepresentationsReversed"]
	
	currentLayoutData = []
	
	for i in range(len(largePieceDatabase)):
		currentLayoutData.append([None, []]) # None will turn into a data tuple (pieceCoord, pieceOrientation, ...)
		for j in range(len(largePieceDatabase[i][1][0])): # [0] cause only using 1 corner representation for now
			currentLayoutData[-1][1].append(None)
			
	
	while True: # constantly iterate to the next clockwise border piece until done (will be up to amount_of_border_pieces - 1 duplicate or wasted tests because of the way I'm deciding to track if we have done a full loop around without any changes, note I cant iterate full border in 1 step since if the branch splits the set of pieces in the border will also change so the 1 passthrough border iteration will break a bit so need to loop once per border piece without tracking the full border)
		# if iterated full boundary without any change:
		if current border piece is same as first border piece in current border passthrough: (going to store at current node i think)
			
			# check if this path (that reached dead end) is good enough to store, and if so store any required data about the path
			...
			
			# go to next fresh node to test
			while True:
				if len(currentPath) <= 0:
					break
				currentPath[-1]-=1
				# UPDATE STUFF TO REFLECT RETREATING BACK PATH e.g. remove from currentLayoutData any existing pairings to the piece being removed, etc... DONT POP FROM expansionTree YET
				if currentPath[-1] < 0:
					currentPath.pop(-1)
			
			if len(currentPath) <= 0:
					break
		
		# stuff at start of loop to prep for rest of this loop <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		
		get current empty node of tree that we will add data to?
		
		if the node at tree up to currentPath[-1]+1 exists, pop it, any paths going through it have been exhausted
		
		# currentPath should lead to a branch in expansionTree like [data..., piecesAdded, []] where the list within the branch will contain the next branches.. AND where piecesAdded is the 1 or 2 pieces added in this step, since sometimes 2 pieces have to be added together
		
		TEST ALL EDGES OF THE CURRENT BORDER PIECE BEING EXPANDED FROM. ADD A BRANCH FOR EACH SCENARIO FOR EACH EDGE AND ONLY MOVE FORWARD WHEN ALL EDGES ARE DONE (because I'm not tracking which edge I left off on when returning back down the path)
		
		# WHEN ADDING PIECE/S, CARRY ON THE BORDER from the most anticlockwise edge of the newly added piece/s AND SET "first border piece in current border passthrough" to this piece AFTER testing all edges for it and adding any potential branches (BEFORE entering into the first new branch), also probably default to the leftmost piece if somehow none of the 1-2 newly added pieces are a border piece MAKE SURE THIS CANT CAUSE INFINITE LOOPS!!
		
		# update first border piece in current border passthrough whenever path[-1] is decremented? i.e. whenever current assumed schema is changed?
		# AND when currentPath.append()? i.e. when going deeper/adding peice to current assumed schema?
		
		# iterate
	
	currentPath = [] # not [0], since currentPath iteration starts with first element being used at expansionTree[1][X] which is the first node AFTER this base node
	
	# expansionTree = [] # store stuff, also store current x,y location w.r.t. first piece in starting block, ACTUALLY JUST STORE POINTER TO currentLayoutData AND STORE ALL THE INFO THERE
	layoutCoordDict = {}
	
	currentLayoutData[startingBlock[1][0]][1][startingBlock[1][1]] = (startingBlock[1][2], startingBlock[1][3])
	currentLayoutData[startingBlock[1][2]][1][startingBlock[1][3]] = (startingBlock[1][0], startingBlock[1][1])
	
	currentLayoutData[startingBlock[1][0]][0] = ((0,0), 0)
	
	tmpFirstPieceEdgeKey = largePieceDatabase[startingBlock[1][0]][1][0][startingBlock[1][1]][0]
	tmpFirstPieceEdgeOrientation = localEdgeOrientationRepresentations[tmpFirstPieceEdgeKey] # global and local since first piece is basis of plane
	tmpSecondPieceGlobalEdgeOrientation = (tmpFirstPieceEdgeOrientation+2)%4
	tmpSecondPieceEdgeKey = largePieceDatabase[startingBlock[1][2]][1][0][startingBlock[1][3]][0]
	tmpSecondPieceLocalEdgeOrientation = localEdgeOrientationRepresentations[tmpSecondPieceEdgeKey]
	tmpSecondPieceOrientation = (tmpSecondPieceGlobalEdgeOrientation-tmpSecondPieceLocalEdgeOrientation)%4
	# tmpSecondPieceCoord = (0tmpFirstPieceEdgeOrientation)
	xOrientationModifier = abs((tmpFirstPieceEdgeOrientation+1)%4-2)-1
	yOrientationModifier = abs((tmpFirstPieceEdgeOrientation)%4-2)-1
	tmpSecondPieceCoord = (0+xOrientationModifier, 0+yOrientationModifier)
	
	currentLayoutData[startingBlock[1][2]][0] = (tmpSecondPieceCoord, tmpSecondPieceOrientation)
	layoutCoordDict[(0,0)]=startingBlock[1][0]
	layoutCoordDict[tmpSecondPieceCoord]=startingBlock[1][2]
	
	remainingPairingsInds = [2,3,4] # in case the first pair done uses 2 different pieces from the second pair done, I need at least one of the pieces in each pair to already be stored so I know orientations and coords
	paranoidInfiniteLoopTracker=0
	while len(remainingPairingsInds)>0 and paranoidInfiniteLoopTracker<30:
		tmpP1ID = startingBlock[paranoidInfiniteLoopTracker%len(remainingPairingsInds)][0]
		tmpP1EdgeID = startingBlock[paranoidInfiniteLoopTracker%len(remainingPairingsInds)][1]
		tmpP2ID = startingBlock[paranoidInfiniteLoopTracker%len(remainingPairingsInds)][2]
		tmpP2EdgeID = startingBlock[paranoidInfiniteLoopTracker%len(remainingPairingsInds)][3]
		if currentLayoutData[tmpP1ID][0] is None:
			tmpP1ID, tmpP1EdgeID, tmpP2ID, tmpP2EdgeID = tmpP2ID, tmpP2EdgeID, tmpP1ID, tmpP1EdgeID
		if currentLayoutData[tmpP1ID][0] is not None:
			tmpP1Orientation = currentLayoutData[tmpP1ID][0][1]
			tmpP1GlobalEdgeOrientation = (tmpP1Orientation+localEdgeOrientationRepresentations[largePieceDatabase[tmpP1ID][1][0][tmpP1EdgeID][0]])%4
			tmpP2GlobalEdgeOrientation = (tmpP1GlobalEdgeOrientation+2)%4
			tmpP2Orientation = (tmpP2GlobalEdgeOrientation-localEdgeOrientationRepresentations[largePieceDatabase[tmpP2ID][1][0][tmpP2EdgeID][0]])%4
			tmpP1Coord = currentLayoutData[tmpP1ID][0][0]
			# tmpP2Coord = (tmpP1Coord[0], tmpP1Coord[1])
			xOrientationModifier = abs((tmpP1GlobalEdgeOrientation+1)%4-2)-1
			yOrientationModifier = abs((tmpP1GlobalEdgeOrientation)%4-2)-1
			tmpP2Coord = (tmpP1Coord[0]+xOrientationModifier, tmpP1Coord[1]+yOrientationModifier)
			
			currentLayoutData[tmpP1ID][1][tmpP1EdgeID] = (tmpP2ID, tmpP2EdgeID)
			currentLayoutData[tmpP2ID][1][tmpP2EdgeID] = (tmpP1ID, tmpP1EdgeID)
			# currentLayoutData[startingBlock[1][0]][0] = ((0,0), 0)
			currentLayoutData[tmpP2ID][0] = (tmpP2Coord, tmpP2Orientation)
			layoutCoordDict[tmpP2Coord] = tmpP2ID
			remainingPairingsInds.pop(paranoidInfiniteLoopTracker%len(remainingPairingsInds))
		else: # rather than every single loop, because I pop items out of remainingPairingsInds so wouldn't make sense to increment index at the same time since it'd skip an item
			paranoidInfiniteLoopTracker+=1
			# DEBUG
			if paranoidInfiniteLoopTracker>10:
				print("wat??doi3j")
				exit()
	
	tmpNewNodePieceIDs = []
	for pieceCoord in layoutCoordDict:
		tmpNewNodePieceIDs.append((layoutCoordDict[pieceCoord]))
	expansionTree = [ [ tmpNewNodePieceIDs ], [] ] # [[[(pieceID1), (pieceID2)], nodedata...], []]
	
	# actually maybe just iterate empty edges rather than traversing border?
	
	# currentLayoutData now has a list for each piece [(edgedat...), [edge1, edge2, ...]]
	
	bestLayoutCoordDict={}
	bestCurrentLayoutData=[]
	
	# slightly scuffed since its -1 instead of 0, should work though
	opspPathDepth = -1 # one piece single possibility
	opmpPathDepth = -1 # one piece multiple possibilities
	tpspPathDepth = -1 # two pieces single possibility
	tpmpPathDepth = -1 # two peices multiple possibilities
	
	opspPieceInd = len(expansionTree[0][0])-1 # PIECE IND IN TREE, NOT pieceID!!!
	opmpPieceInd = len(expansionTree[0][0])-1
	tpspPieceInd = len(expansionTree[0][0])-1
	tpmpPieceInd = len(expansionTree[0][0])-1
	
	opspEdgeInd = len(currentLayoutData[expansionTree[0][0][opspPieceInd][0]][1])-1 # expansionTree[0][0][pieceInd] is [pieceID]
	opmpEdgeInd = len(currentLayoutData[expansionTree[0][0][opmpPieceInd][0]][1])-1
	tpspEdgeInd = len(currentLayoutData[expansionTree[0][0][tpspPieceInd][0]][1])-1
	tpmpEdgeInd = len(currentLayoutData[expansionTree[0][0][tpmpPieceInd][0]][1])-1
	
	deepestNode = expansionTree
	opspCurrentNode = expansionTree
	opmpCurrentNode = expansionTree
	tpspCurrentNode = expansionTree
	tpmpCurrentNode = expansionTree
	
	
	while True:
		
		
		...
		...
		...
		
		# 1 single potential
		
		didAnythingHappen = False
		# while True:
		while opspEdgeInd!=-1:
		
			currentPieceID = opspCurrentNode[0][0][opspPieceInd][0]
			currentEdgeID = opspEdgeInd
			
				# onlyOnePieceRequirements = None # in multiple potential ghost pieces this will need to be some kind of list/data that stores requirements to fit 2 pieces in at once or something I think
			if currentLayoutData[currentPieceID][1][currentEdgeID] is None: # if edge has no piece connecting to it, there must be an empty space for a piece next to this edge
				
				# .. check if there exists a piece at any possible coord that can form either a 1 piece addition or a 2 piece addition (by checking a coord dictionary with key being coords)
				
				# tmpCount = 1 # already have 1 edge connection with current edge, looking for this to be at least 2
				
				potentialPieceRequirements = [] # list of requirements for each edge of a perspective piece in clockwise order, if an edge has no requirements then append empty list
				# ORDER FROM QUICKEST TO LONGEST COMPATIBILITY REQS, WITH LAST REQ BEING SHAPE (THE BIG TEST), if i do colour thatd prob be 2nd last
				# ACTUALLY I ALREADY TEST ALL THE QUICK COMPATIBILITY STUFF EARLIER WHICH EVEN INCLUDES INNIE-OUTIE PAIRINGS so just check if compatible with all edges, then check if similar to all edges
				
				mainConnectionPieceCoord = currentLayoutData[currentPieceID][0][0]
				
				globalOrientationFirstRealPiece = currentLayoutData[currentPieceID][0][1]
				firstRealPieceEdgeKey = largePieceDatabase[currentPieceID][1][0][currentEdgeID][0]
				localOrientationFirstRealPieceEdge = localEdgeOrientationRepresentationsReversed[firstRealPieceEdgeKey]
				globalOrientationFirstRealPieceEdge = (localOrientationFirstRealPieceEdge + globalOrientationFirstRealPiece)%4
				
				xOrientationModifier = abs((globalOrientationFirstRealPieceEdge+1)%4-2)-1
				yOrientationModifier = abs((globalOrientationFirstRealPieceEdge)%4-2)-1
				ghostPieceCoord = (mainConnectionPieceCoord[0]+xOrientationModifier, mainConnectionPieceCoord[1]+yOrientationModifier)
				
				# Just going to iterate all 4 sides of potential piece/ghost piece even though I already know 1 (the mainConnectionPiece)
				totalPossibleConnections = 0
				for tmpN in range(0, 4):
					xOrientationModifier = abs((tmpN+1)%4-2)-1
					yOrientationModifier = abs((tmpN)%4-2)-1
					coordAtCurrentSideOfGhostPiece = (ghostPieceCoord[0]+xOrientationModifier, ghostPieceCoord[1]+yOrientationModifier) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
					if coordAtCurrentSideOfGhostPiece in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
						tmpPieceAtCoordID = layoutCoordDict[coordAtCurrentSideOfGhostPiece]
						tmpPieceAtCoordOrientationN = currentLayoutData[tmpPieceAtCoordID][0][1]
						tmpPieceAtCoordRelevantSide = None
						needSideAtOrientation = (tmpN+2)%4 # if the piece at current side of ghost piece is orientated n=0 or topEdge pointing up, this is the n of the side we need to connect to ghost piece
						actualSideAtOrientation = (needSideAtOrientation-tmpPieceAtCoordOrientationN)%4 # orientation of the required side of the piece RELATIVE to the orientation of the piece that the side belongs to
						# e.g. ghost piece which has orientation 0 and we are looking at its left side, if the other piece has topEdge facing downwards then its orientation is 2 and if it were facing up with orientation 0 then we would need right side to match ghost i.e. side 3, then w.r.t. other piece we need side 1
						if actualSideAtOrientation==0:
							tmpPieceAtCoordRelevantSide="topEdge"
						elif actualSideAtOrientation==1:
							tmpPieceAtCoordRelevantSide="leftEdge"
						elif actualSideAtOrientation==2:
							tmpPieceAtCoordRelevantSide="bottomEdge"
						elif actualSideAtOrientation==3:
							tmpPieceAtCoordRelevantSide="rightEdge"
						
						# MIGHT BE A BIT CONFUSING but I'm using orientation to describe the orientation of a piece (i.e. where topEdge is pointing) AND to describe a specific edge of a piece, they're closely tied values
						
						tmpRelevantSideAtCoordID = None
						for tmpI, tmpEdge in enumerate(largePieceDatabase[tmpPieceAtCoordID][1][0]):
							if tmpEdge[0] == tmpPieceAtCoordRelevantSide:
								tmpRelevantSideAtCoordID=tmpI
								break
						if tmpRelevantSideAtCoordID is None:
							print("wat?d2r3y77d3k3k3")
							exit()
						
						potentialPieceRequirements.append((tmpPieceAtCoordID, tmpRelevantSideAtCoordID))
						totalPossibleConnections+=1
						
						# ^^^ COULD BE SLOW IF HAS TO ALWAYS SCAN THROUGH A BUNCH OF EDGES TO FIND IF THE CURRENT OTHER EDGE IN THE PAIR IS COMPATIBLE (I.E. IS IN THE LIST)
						# MAYBE DO A COMPATIBILITY DICT OR SOMETHING FOR O(1) COMPATIBILITY CHECKS
						
					else:
						potentialPieceRequirements.append(None)
					
				
				# .. (if this were multiple potentials loop I'd add to list but different for single loop) check all possible combos for 1 and 2 additions. As soon as >1 encountered pass to next empty side of this piece or next piece if out of sides etc
				
				if totalPossibleConnections >= 2: # this space has enough surrounding pieces to reliably test for 1 piece potential entries
					
					# efficiently find a piece that fits, e.g. maybe start with the edge it must connect to in potentialPieceRequirements that has the smallest number of potential/compatible pairings, then go through the rest of potentialPieceRequirements
					# to see if there even exists a piece that's compatible with all connections that itll form when placed there.
					# lastly if a piece exists, maybe test each edge at higher detail or whatever the plan was, then carry on looping through pieces to see if a 2nd potential piece fits all requirements
					# and if a 2nd piece does exist, immediately stop and let it get handles in next loop
					# if it doesnt exist, update everything, add it to layout etc, then go to next big loop? (the base loop)
					
					# terrible code below but tired
					efficientOrder = []
					for tmpI, req in enumerate(potentialPieceRequirements):
						if req is not None:
							efficientOrder.append(	( len(prelimCompatPairsInniesAndOutiesInds[req[0]][req[1]]), tmpI )	 )
					
					efficientOrder.sort() # we now have order of edges defined in potentialPieceRequirements ordered from lowest compatible pairings to it
					
					fullyCompatibleAdditions = [] # compatibility is tested much faster than similarity so check if there even exists a piece that is fully compatible with the place it is being put
					
					for firstCompatibleEdgePairing in prelimCompatPairsInniesAndOutiesInds[potentialPieceRequirements[efficientOrder[0][1]][0]][potentialPieceRequirements[efficientOrder[0][1]][1]]:
						
						
						# NOTE: firstCompatibleEdgePairing variable actually just holds a single edge, specifically an edge on a potential piece that is compatible with the first edge (first as chosen to be most efficient) in the group of required edges that the ghost/potential piece must be compatible with
						
						# did for loop for first edge since it locks the orientation of the potential piece
						# now do while loop for the rest of items in efficientOrder to iterate in a tree-like fashion to append fully compatible pieces to fullyCompatibleAdditions.
						# note: multiple edges from the same piece can be compatible with a given req edge, thats why can just stop if I find an edge with the same pieceID as current potentialPiece at each level
						
						# ACTUALLY A LOT SIMPLER THAN I THOUGHT, since orientation of potentialPiece is locked, can just iterate compatible edge lists searching for the specific (pieceID, edgeID) that corrosponds to the edge
						# of potentialPiece that would form a connection to the req edge given the first pairing being assumed to be locked in
						
						# going to start sacraficing junk variables for readability because this is getting ridiculous
						firstPieceID = potentialPieceRequirements[efficientOrder[0][1]][0]
						firstPieceEdgeID = potentialPieceRequirements[efficientOrder[0][1]][1]
						firstPieceGlobalOrientation = currentLayoutData[firstPieceID][0][1]
						firstPieceEdgeKey = largePieceDatabase[firstPieceID][1][0][firstPieceEdgeID][0]
						
						
						firstPieceEdgeGlobalOrientation = (firstPieceGlobalOrientation + localEdgeOrientationRepresentations[firstPieceEdgeKey])%4
						ghostPieceEdgeGlobalOrientation = (firstPieceEdgeGlobalOrientation+2)%4 # +2 is opposite
						ghostPieceID = firstCompatibleEdgePairing[3]
						ghostPieceFirstEdgeID = firstCompatibleEdgePairing[4]
						ghostPieceFirstEdgeKey = largePieceDatabase[ghostPieceID][1][0][ghostPieceFirstEdgeID][0]
						ghostPieceGlobalOrientation = (ghostPieceEdgeGlobalOrientation - localEdgeOrientationRepresentations[ghostPieceFirstEdgeKey])%4
						currEdgeConfiguration = [(ghostPieceID, ghostPieceFirstEdgeID)] # construct list in SAME ORDER as efficientOrder that pairs edges from potentialPiece to edges in efficientOrder (by assuming the firstCompatibleEdgePairing)
						# Then I can just also use tmpDepthEfficientOrder for currEdgeConfiguration to get exact (pieceID, edgeID) that I'm looking for, partly for readability since edgeID will be same for each edge and wasting space etc..
						passedReqs = True
						for remainingEdgeReq in efficientOrder[1:]:
							# currEdgeConfiguration...
							
							# have standardised order of potentialPieceRequirements for both 1 and 2 piece additions
							# already have for 1 piece additions i.e. i think anticlockwise? double check
							# for 2 piece additions maybe do clockwise/anticlockwise as if the 2 pieces were connected, ignoring the inner pairing (this works well because remember potentialPieceRequirements is constructed using
							# the edges currently around the empty space that the pieces will fit into, so dont have the inner pair anyway yet)
							# then for this part simply find the orientation N (0 is topEdge or up or whatever) after the first edge is fixed, then use this to automatically offset a variable that can be used as index to a global dict:
							# {0: topEdge, 1: leftEdge, ...}
							
							# then for readability add e.g. (pieceID, "topEdge") to currEdgeConfiguration then can use currEdgeConfiguration below to check if edges exist
							# NOTE this is just slightly different cause I was previously going to check if (pieceID, edgeID) exists
							
							#===
							
							# we have orientation of the already fixed pieces w.r.t. global orientation
							# we have the orientation representation of the edge that the ghost edge is connecting to
							# we (can) have the orientation of the ghost piece w.r.t. global orientation based on the first pairing
							# from this we can get the global orientation representation of the edge in the ghost piece
							# from this we can get the edge key that's being connected
							
							tmpPieceID = potentialPieceRequirements[remainingEdgeReq[1]][0]
							tmpPieceEdgeID = potentialPieceRequirements[remainingEdgeReq[1]][1]
							tmpPieceGlobalEdgeOrientation = currentLayoutData[tmpPieceID][0][1]
							tmpGhostPieceGlobalEdgeOrientation = (tmpPieceGlobalEdgeOrientation+2)%4
							tmpGhostPieceEdgeOrientation = (tmpGhostPieceGlobalEdgeOrientation - ghostPieceGlobalOrientation)%4
							tmpGhostPieceEdgeKey = localEdgeOrientationRepresentationsReversed[tmpGhostPieceEdgeOrientation]
							
							passedThisReq = False
							for tmpCompatEdge in prelimCompatPairsInniesAndOutiesInds[tmpPieceID][tmpPieceEdgeID]:
								# tmpGhostPieceEdgeID = 
								if tmpCompatEdge[3]==ghostPieceID:
									if largePieceDatabase[tmpCompatEdge[3]][1][0][tmpCompatEdge[4]][0] == tmpGhostPieceEdgeKey: # need to take both the pieceID and edgeID at this entry and use it to get the edgeKey that the edgeID corrosponds to since it may be different for any given piece
										currEdgeConfiguration.append((ghostPieceID, tmpCompatEdge[4]))
										passedThisReq=True
										break
							if not(passedThisReq):
								passedReqs=False
								break
						
						if passedReqs:
							
							fullyCompatibleAdditions.append((ghostPieceCoord, ghostPieceGlobalOrientation, currEdgeConfiguration))
						
						
					# test similarity score of each edge by iterating using same index for efficientOrder and fullyCompatibleAdditions \/\/\/
					
					# as soon as MORE THAN 1 ghost piece passes matching+compatibility requirements, skip because it should be handled in the multiple potentials section
					# I'll probably do a HIGHLY inefficient method and not save the already-obtained 2 fully matching/compatible ghost pieces OR even store the fact that this empty space has 2+ fully matching/compat pieces
					# if needed I can add later but I assume itll save relatively no time compared to the similarity score calculations
					# (I will obviously be storing any updated similarity score calculations that are done)
					
					# method to handle 2 piece additions in 1 step will be very similar to above just need to handle traversing anticlockwise on border of 2 connected pieces + handle middle connection between them, probably defined by efficientOrder
					fullyMatchingAdditions = [] # keeping this as a list just so it's easier to see similarity when doing method for multiple possibilities
					for fullyCompatiblePiece in fullyCompatibleAdditions:
						tmpGhostPieceCoord = fullyCompatiblePiece[0]
						tmpGhostPieceGlobalOrientation = fullyCompatiblePiece[1]
						tmpFullyCompatiblePieceEdgeDat = fullyCompatiblePiece[2]
						fullyMatching = True
						for tmpI in range(len(efficientOrder)):
							tmpPiece1ID = potentialPieceRequirements[efficientOrder[tmpI][1]][0]
							tmpPiece1EdgeID = potentialPieceRequirements[efficientOrder[tmpI][1]][1]
							tmpPiece2ID = tmpFullyCompatiblePieceEdgeDat[tmpI][0]
							tmpPiece2EdgeID = tmpFullyCompatiblePieceEdgeDat[tmpI][1]
							newSimScore = updateSimilarityScore(tmpPiece1ID, tmpPiece1EdgeID, tmpPiece2ID, tmpPiece2EdgeID, detailLevel?, data structures..., ...)
							if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
								... maybe just remove the compatibility entries altogether?
								fullyMatching = False
								break
							# similarityScore = prelimCompatPairsInniesAndOutiesInds[]
						if fullyMatching:
							# if lenfullyMatchingAddition is not None:
								# break
							# else:
							fullyMatchingAdditions.append(fullyCompatiblePiece)
							if len(fullyMatchingAdditions) > 1: # dumb and wasteful code but I care more about readability for now, don't lose any time/space compared to other functions so doesn't matter
								break
					if len(fullyMatchingAdditions) == 1:
						# ...
						# add/update stuff, make sure automatically skips rest of big loop and goes back to start, with updated vars/indices/trackers if required
						tmpNewAdditionPieceID = fullyMatchingAdditions[0][2][0][0] # fullyMatchingAdditions[0][2][X][0] are all ghostPieceID
						tmpNewAdditionPieceCoord = fullyMatchingAdditions[0][0]
						tmpNewAdditionPieceGlobalOrientation = fullyMatchingAdditions[0][1]
						newNode = [ [ [(tmpNewAdditionPieceID)] ], [] ] # [[[(pieceID1), (pieceID2)], nodedata...], []]
						deepestNode[1].append(newNode)
						layoutCoordDict[tmpNewAdditionPieceCoord] = tmpNewAdditionPieceID
						currentPath.append(0)
						deepestNode = deepestNode[1][0]
						currentLayoutData[tmpNewAdditionPieceID][0] = (tmpNewAdditionPieceCoord, tmpNewAdditionPieceGlobalOrientation)
						for tmpI in range(len(efficientOrder)):
							tmpPiece1ID = potentialPieceRequirements[efficientOrder[tmpI][1]][0]
							tmpPiece1EdgeID = potentialPieceRequirements[efficientOrder[tmpI][1]][1]
							tmpPiece2ID = fullyMatchingAdditions[0][2][tmpI][0]
							tmpPiece2EdgeID = fullyMatchingAdditions[0][2][tmpI][1]
							
							# DEBUG
							if True:
								if currentLayoutData[tmpPiece1ID][1][tmpPiece1EdgeID] is not None:
									print("3dj442d3i3??")
								if currentLayoutData[tmpPiece2ID][1][tmpPiece2EdgeID] is not None:
									print("3dj442d3i3??")
							###
							
							currentLayoutData[tmpPiece1ID][1][tmpPiece1EdgeID] = (tmpPiece2ID, tmpPiece2EdgeID)
							currentLayoutData[tmpPiece2ID][1][tmpPiece2EdgeID] = (tmpPiece1ID, tmpPiece1EdgeID)
						
						# update all previous/higher-priority loop-types since they now have new edges to test
						
						if tpspEdgeInd==-1:
							tpspPathDepth+=1
							tpspCurrentNode=tpspCurrentNode[1][currentPath[tpspPathDepth]]
							tpspPieceInd = len(tpspCurrentNode[0][0])-1
							tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
						if opmpEdgeInd==-1:
							opmpPathDepth+=1
							opmpCurrentNode=opmpCurrentNode[1][currentPath[opmpPathDepth]]
							opmpPieceInd = len(opmpCurrentNode[0][0])-1
							opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
						if tpmpEdgeInd==-1:
							tpmpPathDepth+=1
							tpmpCurrentNode=tpmpCurrentNode[1][currentPath[tpmpPathDepth]]
							tpmpPieceInd = len(tpmpCurrentNode[0][0])-1
							tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
						
						
						didAnythingHappen=True
					# DONT PUT ANTHING AFTER HERE AND ON THE LINES WITH #, any else scenarios should naturally flow to multiple possibilities case
					# .. if 1 possibility found, update tree and stuff and edge/piece tracker then re-loop this inner loop, also update currentNode and stuff etc and didAnythingHappen
				#
			# ...
			opspEdgeInd-=1
			if opspEdgeInd==-1:
				if opspPieceInd>0:
					opspPieceInd-=1
					opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
				elif opspPathDepth<len(currentPath)-1:
					opspPathDepth+=1
					opspCurrentNode=opspCurrentNode[1][currentPath[opspPathDepth]]
					opspPieceInd = len(opspCurrentNode[0][0])-1
					opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
				else: # tested every edge of every piece in current puzzle layout
					break
					
			# ...
			# if opspEdgeInd==-1:
				# break
		#
		
		# second passthrough no conflicting 2 piece addition (effectively 1 possibility)
		# if didAnythingHappen==False:
		if opspEdgeInd==-1 and tpspEdgeInd!=-1:
			
			while opspEdgeInd==-1 and tpspEdgeInd!=-1:
				# if tmpPathTraversalInd>len(currentPath)-1:
					# break
				
				currentPieceID = tpspCurrentNode[0][0][tpspPieceInd][0]
				currentEdgeID = tpspEdgeInd
				
				# need to check if first empty space would only form connection with 1 edge i.e. current edge
				# then for loop each empty space connected to each edge of the main space to find spaces that would only form 1 other connection (not including the one that would be formed with the current main space)
				# then for loop each compatible edgepair from current real peice to main blank space, and within this do another for loop each piece with compatible edgepair with the connection between the 2 ghost pieces and finally if the 2nd ghost piece has compatible connection with other real piece in layout, add to compatible list
				# lastly, iterate all compatible 2 piece additions to find fully matching additions, as soon as 2 conflicting, stop
				if currentLayoutData[currentPieceID][1][currentEdgeID] is None: # if edge has no piece connecting to it, there must be an empty space for a piece next to this edge
					
					actuallyFullyCompatibleAdditions = [] # previous fullyCompatibleAdditions might have just been used for fully matching+compatible additions but this time just for fully compatible
					
					globalOrientationFirstRealPiece = currentLayoutData[currentPieceID][0][1]
					mainConnectionPieceCoord = currentLayoutData[currentPieceID][0][0]
					firstRealPieceEdgeKey = largePieceDatabase[currentPieceID][1][0][currentEdgeID][0]
					localOrientationFirstRealPieceEdge = localEdgeOrientationRepresentationsReversed[firstRealPieceEdgeKey]
					globalOrientationFirstRealPieceEdge = (localOrientationFirstRealPieceEdge + globalOrientationFirstRealPiece)%4
					
					xOrientationModifier = abs((globalOrientationFirstRealPieceEdge+1)%4-2)-1
					yOrientationModifier = abs((globalOrientationFirstRealPieceEdge)%4-2)-1
					ghostPieceCoord1 = (mainConnectionPieceCoord[0]+xOrientationModifier, mainConnectionPieceCoord[1]+yOrientationModifier)
					
					# Just going to iterate all 4 sides of potential piece/ghost piece even though I already know 1 (the mainConnectionPiece)
					totalPossibleConnections = 0
					for tmpN in range(0, 4):
						xOrientationModifier = abs((tmpN+1)%4-2)-1
						yOrientationModifier = abs((tmpN)%4-2)-1
						coordAtCurrentSideOfGhostPiece = (ghostPieceCoord1[0]+xOrientationModifier, ghostPieceCoord1[1]+yOrientationModifier) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
						if coordAtCurrentSideOfGhostPiece in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
							
							totalPossibleConnections+=1
							
						
					if totalPossibleConnections == 1:
						
						# iterate the 4 sides of the empty space, if the side has another empty space there, check for connections, if 1, test stuff further, else pass
						
						otherRealPieceID=None
						for tmpN in range(0, 4):# for each 2nd empty space connecting to the first empty space, there should be exactly 3 since one is to the edge in the actual piece we started from
							xOrientationModifier = abs((tmpN+1)%4-2)-1
							yOrientationModifier = abs((tmpN)%4-2)-1
							coordAtCurrentSideOfGhostPiece = (ghostPieceCoord1[0]+xOrientationModifier, ghostPieceCoord1[1]+yOrientationModifier)
							if coordAtCurrentSideOfGhostPiece not in layoutCoordDict: # if first empty space has another empty space on one of it's sides, check if that empty space also only has 1 connection
								potentialPieceRequirements2 = []
								totalPossibleConnections2 = 0
								globalOrientationNextSideOfGhostPiece2 = None
								for tmpM in range(0, 4):
									xOrientationModifier2 = abs((tmpM+1)%4-2)-1
									yOrientationModifier2 = abs((tmpM)%4-2)-1
									coordNextToSecondEmptySpace = (coordAtCurrentSideOfGhostPiece[0]+xOrientationModifier2, coordAtCurrentSideOfGhostPiece[1]+yOrientationModifier2) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
									if coordNextToSecondEmptySpace in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
										
										totalPossibleConnections2+=1
										
										# assigning variables in case there is only 1 possible connection, then I don't need to loop through each side again to find the data about the 1 connection
										globalOrientationNextSideOfGhostPiece2=tmpM
										otherRealPieceID = layoutCoordDict[coordNextToSecondEmptySpace]
									
									# else:
										# potentialPieceRequirements2.append(None)
									
								if totalPossibleConnections2==1: # now we have a second empty space on one of the sides of the first empty space where both empty spaces only have 1 connection to a current real layout piece
									
									
									globalOrientationCurrentSideOfGhostPiece1 = (globalOrientationFirstRealPieceEdge+2)%4
									globalOrientationNextSideOfGhostPiece1 = tmpN
									
									globalOrientationCurrentSideOfGhostPiece2 = (globalOrientationNextSideOfGhostPiece1+2)%4
									# globalOrientationNextSideOfGhostPiece2
									
									globalOrientationRecievingSideOfOtherRealPiece = (globalOrientationNextSideOfGhostPiece2+2)%4
									globalOrientationOtherRealPiece = currentLayoutData[otherRealPieceID][0][1]
									localOrientationRecievingSideOfOtherRealPiece = (globalOrientationRecievingSideOfOtherRealPiece-globalOrientationOtherRealPiece)%4
									recievingSideOfOtherRealPieceKey = localEdgeOrientationRepresentations[localOrientationRecievingSideOfOtherRealPiece]
									
									otherRealPieceEdgeID = None
									for tmpI, tmpEdge in enumerate(largePieceDatabase[otherRealPieceID][1][0]):
										if tmpEdge[0] == recievingSideOfOtherRealPieceKey:
											otherRealPieceEdgeID=tmpI
											break
									if otherRealPieceEdgeID is None:
										print("wat?dr23332r3y77d")
										exit()
									
									for realToGhostEdgePair1 in prelimCompatPairsInniesAndOutiesInds[currentPieceID][currentEdgeID]:
										
										edgeKeyCurrentSideGhostPiece1 = largePieceDatabase[realToGhostEdgePair1[3]][1][0][realToGhostEdgePair1[4]][0]
										
										# globalOrientationCurrentSideOfGhostPiece1
										# globalOrientationNextSideOfGhostPiece1
										needAmountAntiClockwise = globalOrientationNextSideOfGhostPiece1 - globalOrientationCurrentSideOfGhostPiece1
										
										localOrientationCurrentSideGhostPiece1 = localEdgeOrientationRepresentationsReversed[edgeKeyCurrentSideGhostPiece1]
										localOrientationNextSideGhostPiece1 = (localOrientationCurrentSideGhostPiece1 + needAmountAntiClockwise)%4
										edgeKeyNextSideGhostPiece1 = localEdgeOrientationRepresentations[localOrientationNextSideGhostPiece1]
										
										tmpNextSideGhostPiece1ID = None
										for tmpI, tmpEdge in enumerate(largePieceDatabase[realToGhostEdgePair1[3]][1][0]):
											if tmpEdge[0] == edgeKeyNextSideGhostPiece1:
												tmpNextSideGhostPiece1ID=tmpI
												break
										if tmpNextSideGhostPiece1ID is None:
											print("wat?dr232r3y77d3k3k3")
											exit()
										
										for ghost1ToGhost2EdgePair in prelimCompatPairsInniesAndOutiesInds[realToGhostEdgePair1[3]][tmpNextSideGhostPiece1ID]:
											
											edgeKeyCurrentSideGhostPiece2 = largePieceDatabase[ghost1ToGhost2EdgePair[3]][1][0][ghost1ToGhost2EdgePair[4]][0]
											
											# globalOrientationCurrentSideOfGhostPiece2
											# globalOrientationNextSideOfGhostPiece2
											needAmountAntiClockwise2 = globalOrientationNextSideOfGhostPiece2 - globalOrientationCurrentSideOfGhostPiece2
											
											localOrientationCurrentSideGhostPiece2 = localEdgeOrientationRepresentationsReversed[edgeKeyCurrentSideGhostPiece2]
											localOrientationNextSideGhostPiece2 = (localOrientationCurrentSideGhostPiece2 + needAmountAntiClockwise2)%4
											edgeKeyNextSideGhostPiece2 = localEdgeOrientationRepresentations[localOrientationNextSideGhostPiece2]
											
											tmpNextSideGhostPiece2ID = None
											for tmpI, tmpEdge in enumerate(largePieceDatabase[ghost1ToGhost2EdgePair[3]][1][0]):
												if tmpEdge[0] == edgeKeyNextSideGhostPiece2:
													tmpNextSideGhostPiece2ID=tmpI
													break
											if tmpNextSideGhostPiece2ID is None:
												print("wat?dr2312r3y77d3k3k3")
												exit()
											
											# for loop to check if the 2nd ghost piece has connection to final real edge
											
											for otherRealEdgePair in prelimCompatPairsInniesAndOutiesInds[otherRealPieceID][otherRealPieceEdgeID]:
												if otherRealEdgePair[3] == ghost1ToGhost2EdgePair[3] and otherRealEdgePair[4] == tmpNextSideGhostPiece2ID:
													ghostPiece1Orientation = (globalOrientationCurrentSideOfGhostPiece1-localOrientationCurrentSideGhostPiece1)%4
													ghostPiece2Orientation = (globalOrientationCurrentSideOfGhostPiece2-localOrientationCurrentSideGhostPiece2)%4
													# actuallyFullyCompatibleAdditions.append((realToGhostEdgePair1[3], realToGhostEdgePair1[4], ghostPiece1Orientation, ghost1ToGhost2EdgePair[3], ghost1ToGhost2EdgePair[4], ghostPiece2Orientation)) # currently (ghostPiece1ID, ID of edge of ghost piece 1 that connects to first real piece, ghostPiece1Orientation, and same for ghostPiece2 with edgeID connecting to ghostPiece1)
													# don't think I particularly need those specific edgeIDs but they are one of the multiple ways to uniquely distinguish the arrangement of the 2 pieces here, just pieceIDs and orientations aren't sufficient
													
													
													firstRealPieceID = currentPieceID
													ghostPiece1ID = realToGhostEdgePair1[3]
													ghostPiece2ID = ghost1ToGhost2EdgePair[3]
													# otherRealPieceID = 
													
													firstPairEdgeIDs = (currentEdgeID, realToGhostEdgePair1[4])
													secondPairEdgeIDs = (tmpNextSideGhostPiece1ID, ghost1ToGhost2EdgePair[4])
													thirdPairEdgeIDs = (tmpNextSideGhostPiece2ID, otherRealPieceEdgeID)
													
													ghostPieceCoord2 = coordAtCurrentSideOfGhostPiece
													
													actuallyFullyCompatibleAdditions.append( (firstRealPieceID, ghostPiece1ID, ghostPiece2ID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs, ghostPiece1Orientation, ghostPiece2Orientation, globalOrientationNextSideOfGhostPiece1, ghostPieceCoord1, ghostPieceCoord2) )
													# edgePair IDs are in expected/obvious order, first real to ghost 1 to ghost 2 to second real
						
						####### up to here <<<<<<<<<<<<<<< next is fully matching test? then conflict/multiple possibility check
					
					# gonna do a second loop to go through and test full matchability rather than just testing before adding to a list in above loop
					# this way in the future if I want to check for there being way too many options before wasting time updating scores, I can do so
					
					fullyMatchingAdditions = []
					conflictExists = False
					for fullyCompatibleAddition in actuallyFullyCompatibleAdditions:
						firstRealPieceID, ghostPiece1ID, ghostPiece2ID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs, ghostPiece1Orientation, ghostPiece2Orientation, globalOrientationNextSideOfGhostPiece1, ghostPieceCoord1, ghostPieceCoord2 = fullyCompatibleAddition
						
						avgScore = 0
						
						newSimScore = updateSimilarityScore(firstRealPieceID, firstPairEdgeIDs[0], ghostPiece1ID, firstPairEdgeIDs[1], detailLevel?, data structures..., ...)
						if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
							... maybe just remove the compatibility entries altogether?
						else:
							avgScore+=newSimScore
							newSimScore = updateSimilarityScore(ghostPiece1ID, secondPairEdgeIDs[0], ghostPiece2ID, secondPairEdgeIDs[1], detailLevel?, data structures..., ...)
							if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
								... maybe just remove the compatibility entries altogether?
							else:
								avgScore+=newSimScore
								newSimScore = updateSimilarityScore(ghostPiece2ID, thirdPairEdgeIDs[0], otherRealPieceID, thirdPairEdgeIDs[1], detailLevel?, data structures..., ...)
								if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
									... maybe just remove the compatibility entries altogether?
								else:
									avgScore+=newSimScore
									avgScore=avgScore/3
									tmpDataToAdd = (ghostPiece1ID, ghostPiece1Orientation, globalOrientationNextSideOfGhostPiece1, ghostPiece2ID, ghostPiece2Orientation, avgScore, ghostPieceCoord1, ghostPieceCoord2, firstRealPieceID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs)
									for tmpMatchingAddition in fullyMatchingAdditions:
										# compare to tmpDataToAdd
										# if ghostPiece1 is different
										# or ghostPiece1 is the same but ghostPiece2 is taking up the same place but different piece or orientation
										# or ghostPiece2 is in different place but it's using the same ghostPiece2 that has been used in another fullyMatchingAddition
										
										# if ghostPiece1 orientation or ID is different, conflict exists
										# else if ghostPiece1 next edge orientation is the same (i.e. ghostPiece2 coord is the same) but ghostPiece2 ID is different or the same but with different orientation, conflict exists
										# else if ghostPiece2 ID is the same but ghostPiece1 next edge orientation is different
										tmpghostPiece1ID, tmpghostPiece1Orientation, tmpglobalOrientationNextSideOfGhostPiece1, tmpghostPiece2ID, tmpghostPiece2Orientation = tmpMatchingAddition[:5]
										if tmpghostPiece1ID != ghostPiece1ID or tmpghostPiece1Orientation != ghostPiece1Orientation:
											conflictExists=True
											break
										elif tmpglobalOrientationNextSideOfGhostPiece1 == globalOrientationNextSideOfGhostPiece1 and (tmpghostPiece2ID != ghostPiece2ID or tmpghostPiece2Orientation != ghostPiece2Orientation):
											conflictExists=True
											break
										elif tmpghostPiece2ID == ghostPiece2ID and tmpglobalOrientationNextSideOfGhostPiece1 != globalOrientationNextSideOfGhostPiece1:
											conflictExists=True
											break
										
									if conflictExists:
										break
									fullyMatchingAdditions.append(tmpDataToAdd) # any data to be added to layout, schema, etc...
									
					if not(conflictExists) and len(fullyMatchingAdditions)>0:
						...
						# add/update stuff, make sure automatically skips rest of big loop and goes back to start, with updated vars/indices/trackers if required
						bestAvgScore = float('inf')
						bestAddition = None
						for tmpMatchingAddition in fullyMatchingAdditions:
							if tmpMatchingAddition[5]<bestAvgScore:
								bestAvgScore=tmpMatchingAddition[5]
								bestAddition=tmpMatchingAddition
						
						# (ghostPiece1ID, ghostPiece1Orientation, globalOrientationNextSideOfGhostPiece1, ghostPiece2ID, ghostPiece2Orientation, avgScore, ghostPieceCoord1, ghostPieceCoord2, firstRealPieceID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs)
						
						tmpNewAdditionPieceID1 = bestAddition[0]
						tmpNewAdditionPieceID2 = bestAddition[3]
						tmpNewAdditionPieceCoord1 = bestAddition[6]
						tmpNewAdditionPieceCoord2 = bestAddition[7]
						tmpNewAdditionPieceGlobalOrientation1 = bestAddition[1]
						tmpNewAdditionPieceGlobalOrientation2 = bestAddition[4]
						newNode = [ [ [(tmpNewAdditionPieceID1), (tmpNewAdditionPieceID2)] ], [] ] # [[[(pieceID1), (pieceID2)], nodedata...], []]
						deepestNode[1].append(newNode)
						layoutCoordDict[tmpNewAdditionPieceCoord1] = tmpNewAdditionPieceID1
						layoutCoordDict[tmpNewAdditionPieceCoord2] = tmpNewAdditionPieceID2
						currentPath.append(0)
						deepestNode = deepestNode[1][0]
						currentLayoutData[tmpNewAdditionPieceID1][0] = (tmpNewAdditionPieceCoord1, tmpNewAdditionPieceGlobalOrientation1)
						currentLayoutData[tmpNewAdditionPieceID2][0] = (tmpNewAdditionPieceCoord2, tmpNewAdditionPieceGlobalOrientation2)
						
						tmpPair1Piece1ID = bestAddition[8]
						tmpPair1Piece2ID = bestAddition[0]
						tmpPair1Piece1EdgeID = bestAddition[10][0]
						tmpPair1Piece2EdgeID = bestAddition[10][1]
						currentLayoutData[tmpPair1Piece1ID][1][tmpPair1Piece1EdgeID] = (tmpPair1Piece2ID, tmpPair1Piece2EdgeID)
						currentLayoutData[tmpPair1Piece2ID][1][tmpPair1Piece2EdgeID] = (tmpPair1Piece1ID, tmpPair1Piece1EdgeID)
						
						tmpPair2Piece1ID = bestAddition[0]
						tmpPair2Piece2ID = bestAddition[3]
						tmpPair2Piece1EdgeID = bestAddition[11][0]
						tmpPair2Piece2EdgeID = bestAddition[11][1]
						currentLayoutData[tmpPair2Piece1ID][1][tmpPair2Piece1EdgeID] = (tmpPair2Piece2ID, tmpPair2Piece2EdgeID)
						currentLayoutData[tmpPair2Piece2ID][1][tmpPair2Piece2EdgeID] = (tmpPair2Piece1ID, tmpPair2Piece1EdgeID)
						
						tmpPair3Piece1ID = bestAddition[3]
						tmpPair3Piece2ID = bestAddition[9]
						tmpPair3Piece1EdgeID = bestAddition[12][0]
						tmpPair3Piece2EdgeID = bestAddition[12][1]
						currentLayoutData[tmpPair3Piece1ID][1][tmpPair3Piece1EdgeID] = (tmpPair3Piece2ID, tmpPair3Piece2EdgeID)
						currentLayoutData[tmpPair3Piece2ID][1][tmpPair3Piece2EdgeID] = (tmpPair3Piece1ID, tmpPair3Piece1EdgeID)
						
						# update all previous/higher-priority loop-types since they now have new edges to test
						opspPathDepth+=1
						opspCurrentNode=opspCurrentNode[1][currentPath[opspPathDepth]]
						opspPieceInd = len(opspCurrentNode[0][0])-1
						opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
						
						if opmpEdgeInd==-1:
							opmpPathDepth+=1
							opmpCurrentNode=opmpCurrentNode[1][currentPath[opmpPathDepth]]
							opmpPieceInd = len(opmpCurrentNode[0][0])-1
							opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
						if tpmpEdgeInd==-1:
							tpmpPathDepth+=1
							tpmpCurrentNode=tpmpCurrentNode[1][currentPath[tpmpPathDepth]]
							tpmpPieceInd = len(tpmpCurrentNode[0][0])-1
							tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
						
						didAnythingHappen=True
					
					
				tpspEdgeInd-=1
				if tpspEdgeInd==-1:
					if tpspPieceInd>0:
						tpspPieceInd-=1
						tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
					elif tpspPathDepth<len(currentPath)-1:
						tpspPathDepth+=1
						tpspCurrentNode=tpspCurrentNode[1][currentPath[tpspPathDepth]]
						tpspPieceInd = len(tpspCurrentNode[0][0])-1
						tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
					else: # tested every edge of every piece in current puzzle layout
						break
		
		
		if opspEdgeInd==-1 and tpspEdgeInd==-1 and opmpEdgeInd!=-1:
			
			while opspEdgeInd==-1 and tpspEdgeInd==-1 and opmpEdgeInd!=-1:
		
				currentPieceID = opmpCurrentNode[0][0][opmpPieceInd][0]
				currentEdgeID = opmpEdgeInd
				
				if currentLayoutData[currentPieceID][1][currentEdgeID] is None: # if edge has no piece connecting to it, there must be an empty space for a piece next to this edge
					
					potentialPieceRequirements = [] # list of requirements for each edge of a perspective piece in clockwise order, if an edge has no requirements then append empty list
					mainConnectionPieceCoord = currentLayoutData[currentPieceID][0][0]
					
					globalOrientationFirstRealPiece = currentLayoutData[currentPieceID][0][1]
					
					firstRealPieceEdgeKey = largePieceDatabase[currentPieceID][1][0][currentEdgeID][0]
					localOrientationFirstRealPieceEdge = localEdgeOrientationRepresentationsReversed[firstRealPieceEdgeKey]
					globalOrientationFirstRealPieceEdge = (localOrientationFirstRealPieceEdge + globalOrientationFirstRealPiece)%4
					
					xOrientationModifier = abs((globalOrientationFirstRealPieceEdge+1)%4-2)-1
					yOrientationModifier = abs((globalOrientationFirstRealPieceEdge)%4-2)-1
					ghostPieceCoord = (mainConnectionPieceCoord[0]+xOrientationModifier, mainConnectionPieceCoord[1]+yOrientationModifier)
					
					totalPossibleConnections = 0
					for tmpN in range(0, 4):
						xOrientationModifier = abs((tmpN+1)%4-2)-1
						yOrientationModifier = abs((tmpN)%4-2)-1
						coordAtCurrentSideOfGhostPiece = (ghostPieceCoord[0]+xOrientationModifier, ghostPieceCoord[1]+yOrientationModifier) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
						if coordAtCurrentSideOfGhostPiece in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
							tmpPieceAtCoordID = layoutCoordDict[coordAtCurrentSideOfGhostPiece]
							tmpPieceAtCoordOrientationN = currentLayoutData[tmpPieceAtCoordID][0][1]
							tmpPieceAtCoordRelevantSide = None
							# pieceAtCoordRelevantSideID = None
							needSideAtOrientation = (tmpN+2)%4 # if the piece at current side of ghost piece is orientated n=0 or topEdge pointing up, this is the n of the side we need to connect to ghost piece
							actualSideAtOrientation = (needSideAtOrientation-tmpPieceAtCoordOrientationN)%4 # orientation of the required side of the piece RELATIVE to the orientation of the piece that the side belongs to
							# e.g. ghost piece which has orientation 0 and we are looking at its left side, if the other piece has topEdge facing downwards then its orientation is 2 and if it were facing up with orientation 0 then we would need right side to match ghost i.e. side 3, then w.r.t. other piece we need side 1
							if actualSideAtOrientation==0:
								tmpPieceAtCoordRelevantSide="topEdge"
							elif actualSideAtOrientation==1:
								tmpPieceAtCoordRelevantSide="leftEdge"
							elif actualSideAtOrientation==2:
								tmpPieceAtCoordRelevantSide="bottomEdge"
							elif actualSideAtOrientation==3:
								tmpPieceAtCoordRelevantSide="rightEdge"
							
							 
							tmpRelevantSideAtCoordID = None
							for tmpI, tmpEdge in enumerate(largePieceDatabase[tmpPieceAtCoordID][1][0]):
								if tmpEdge[0] == tmpPieceAtCoordRelevantSide:
									tmpRelevantSideAtCoordID=tmpI
									break
							if tmpRelevantSideAtCoordID is None:
								print("wat?d2r3y77d3k3k3")
								exit()
							
							potentialPieceRequirements.append((tmpPieceAtCoordID, tmpRelevantSideAtCoordID))
							totalPossibleConnections+=1
							
						else:
							potentialPieceRequirements.append(None)
						
					if totalPossibleConnections >= 2: # this space has enough surrounding pieces to reliably test for 1 piece potential entries
						
						efficientOrder = []
						for tmpI, req in enumerate(potentialPieceRequirements):
							# totalCompatibleAndSimilarEdges = 0 # I only want to count edges that |||	NEVERMIND I want ALL compatible edges, then I'll update the tests to current detail level or whatever and evaluate the similarity score at the relevant detail level
							if req is not None:
								efficientOrder.append(	( len(prelimCompatPairsInniesAndOutiesInds[req[0]][req[1]]), tmpI )	 )
						
						efficientOrder.sort() # we now have order of edges defined in potentialPieceRequirements ordered from lowest compatible pairings to it
						
						fullyCompatibleAdditions = [] # compatibility is tested much faster than similarity so check if there even exists a piece that is fully compatible with the place it is being put
						
						for firstCompatibleEdgePairing in prelimCompatPairsInniesAndOutiesInds[potentialPieceRequirements[efficientOrder[0][1]][0]][potentialPieceRequirements[efficientOrder[0][1]][1]]:
							
							
							firstPieceID = potentialPieceRequirements[efficientOrder[0][1]][0]
							firstPieceEdgeID = potentialPieceRequirements[efficientOrder[0][1]][1]
							firstPieceGlobalOrientation = currentLayoutData[firstPieceID][0][1]
							firstPieceEdgeKey = largePieceDatabase[firstPieceID][1][0][firstPieceEdgeID][0]
							
							
							firstPieceEdgeGlobalOrientation = (firstPieceGlobalOrientation + localEdgeOrientationRepresentations[firstPieceEdgeKey])%4
							ghostPieceEdgeGlobalOrientation = (firstPieceEdgeGlobalOrientation+2)%4 # +2 is opposite
							ghostPieceID = firstCompatibleEdgePairing[3]
							ghostPieceFirstEdgeID = firstCompatibleEdgePairing[4]
							ghostPieceFirstEdgeKey = largePieceDatabase[ghostPieceID][1][0][ghostPieceFirstEdgeID][0]
							ghostPieceGlobalOrientation = (ghostPieceEdgeGlobalOrientation - localEdgeOrientationRepresentations[ghostPieceFirstEdgeKey])%4
							currEdgeConfiguration = [(ghostPieceID, ghostPieceFirstEdgeID)] # construct list in SAME ORDER as efficientOrder that pairs edges from potentialPiece to edges in efficientOrder (by assuming the firstCompatibleEdgePairing)
							# Then I can just also use tmpDepthEfficientOrder for currEdgeConfiguration to get exact (pieceID, edgeID) that I'm looking for, partly for readability since edgeID will be same for each edge and wasting space etc..
							passedReqs = True
							for remainingEdgeReq in efficientOrder[1:]:
								
								
								tmpPieceID = potentialPieceRequirements[remainingEdgeReq[1]][0]
								tmpPieceEdgeID = potentialPieceRequirements[remainingEdgeReq[1]][1]
								tmpPieceGlobalEdgeOrientation = currentLayoutData[tmpPieceID][0][1]
								tmpGhostPieceGlobalEdgeOrientation = (tmpPieceGlobalEdgeOrientation+2)%4
								tmpGhostPieceEdgeOrientation = (tmpGhostPieceGlobalEdgeOrientation - ghostPieceGlobalOrientation)%4
								tmpGhostPieceEdgeKey = localEdgeOrientationRepresentationsReversed[tmpGhostPieceEdgeOrientation]
								
								passedThisReq = False
								for tmpCompatEdge in prelimCompatPairsInniesAndOutiesInds[tmpPieceID][tmpPieceEdgeID]:
									# tmpGhostPieceEdgeID = 
									if tmpCompatEdge[3]==ghostPieceID:
										if largePieceDatabase[tmpCompatEdge[3]][1][0][tmpCompatEdge[4]][0] == tmpGhostPieceEdgeKey: # need to take both the pieceID and edgeID at this entry and use it to get the edgeKey that the edgeID corrosponds to since it may be different for any given piece
											currEdgeConfiguration.append((ghostPieceID, tmpCompatEdge[4]))
											passedThisReq=True
											break
								if not(passedThisReq):
									passedReqs=False
									break
							
							if passedReqs:
								
								fullyCompatibleAdditions.append((ghostPieceCoord, ghostPieceGlobalOrientation, currEdgeConfiguration))
							
						# method to handle 2 piece additions in 1 step will be very similar to above just need to handle traversing anticlockwise on border of 2 connected pieces + handle middle connection between them, probably defined by efficientOrder
						fullyMatchingAdditions = [] # keeping this as a list just so it's easier to see similarity when doing method for multiple possibilities
						for fullyCompatiblePiece in fullyCompatibleAdditions:
							tmpGhostPieceCoord = fullyCompatiblePiece[0]
							tmpGhostPieceGlobalOrientation = fullyCompatiblePiece[1]
							tmpFullyCompatiblePieceEdgeDat = fullyCompatiblePiece[2]
							fullyMatching = True
							for tmpI in range(len(efficientOrder)):
								tmpPiece1ID = potentialPieceRequirements[efficientOrder[tmpI][1]][0]
								tmpPiece1EdgeID = potentialPieceRequirements[efficientOrder[tmpI][1]][1]
								tmpPiece2ID = tmpFullyCompatiblePieceEdgeDat[tmpI][0]
								tmpPiece2EdgeID = tmpFullyCompatiblePieceEdgeDat[tmpI][1]
								newSimScore = updateSimilarityScore(tmpPiece1ID, tmpPiece1EdgeID, tmpPiece2ID, tmpPiece2EdgeID, detailLevel?, data structures..., ...)
								if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
									... maybe just remove the compatibility entries altogether?
									fullyMatching = False
									break
								# similarityScore = prelimCompatPairsInniesAndOutiesInds[]
							if fullyMatching:
								
								fullyMatchingAdditions.append(fullyCompatiblePiece)
								
						# if len(fullyMatchingAdditions) == 1:
						if len(fullyMatchingAdditions) > 0:
							for fullyMatchingAddition in fullyMatchingAdditions:
								# ...
								# add/update stuff, make sure automatically skips rest of big loop and goes back to start, with updated vars/indices/trackers if required
								tmpNewAdditionPieceID = fullyMatchingAddition[2][0][0] # fullyMatchingAdditions[0][2][X][0] are all ghostPieceID
								# tmpNewAdditionPieceCoord = fullyMatchingAddition[0]
								# tmpNewAdditionPieceGlobalOrientation = fullyMatchingAddition[1]
								newNode = [ [ [(tmpNewAdditionPieceID)], fullyMatchingAddition, efficientOrder, potentialPieceRequirements ], [] ] # [[[(pieceID1), (pieceID2)], nodedata...], []]
								deepestNode[1].append(newNode)
							
							fullyMatchingAddition = deepestNode[1][-1][0][1]
							efficientOrder = deepestNode[1][-1][0][2] # pointless but for readability and will actually have to do this in future when backtracking
							potentialPieceRequirements = deepestNode[1][-1][0][3] # pointless but for readability and will actually have to do this in future when backtracking
							
							tmpNewAdditionPieceID = fullyMatchingAddition[2][0][0]
							tmpNewAdditionPieceCoord = fullyMatchingAddition[0]
							tmpNewAdditionPieceGlobalOrientation = fullyMatchingAddition[1]
							
							layoutCoordDict[tmpNewAdditionPieceCoord] = tmpNewAdditionPieceID
							currentPath.append(len(deepestNode[1])-1)
							deepestNode = deepestNode[1][currentPath[-1]]
							currentLayoutData[tmpNewAdditionPieceID][0] = (tmpNewAdditionPieceCoord, tmpNewAdditionPieceGlobalOrientation)
							for tmpI in range(len(efficientOrder)):
								tmpPiece1ID = potentialPieceRequirements[efficientOrder[tmpI][1]][0]
								tmpPiece1EdgeID = potentialPieceRequirements[efficientOrder[tmpI][1]][1]
								tmpPiece2ID = fullyMatchingAddition[2][tmpI][0]
								tmpPiece2EdgeID = fullyMatchingAddition[2][tmpI][1]
								
								# DEBUG
								if True:
									if currentLayoutData[tmpPiece1ID][1][tmpPiece1EdgeID] is not None:
										print("3dj448yh2d3i3??")
									if currentLayoutData[tmpPiece2ID][1][tmpPiece2EdgeID] is not None:
										print("3dj442d38ji3??")
								##
								
								currentLayoutData[tmpPiece1ID][1][tmpPiece1EdgeID] = (tmpPiece2ID, tmpPiece2EdgeID)
								currentLayoutData[tmpPiece2ID][1][tmpPiece2EdgeID] = (tmpPiece1ID, tmpPiece1EdgeID)
								
							# update all previous/higher-priority loop-types since they now have new edges to test
							
							opspPathDepth+=1
							opspCurrentNode=opspCurrentNode[1][currentPath[opspPathDepth]]
							opspPieceInd = len(opspCurrentNode[0][0])-1
							opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
							
							
							
							tpspPathDepth+=1
							tpspCurrentNode=tpspCurrentNode[1][currentPath[tpspPathDepth]]
							tpspPieceInd = len(tpspCurrentNode[0][0])-1
							tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
							
							
							if tpmpEdgeInd==-1:
								tpmpPathDepth+=1
								tpmpCurrentNode=tpmpCurrentNode[1][currentPath[tpmpPathDepth]]
								tpmpPieceInd = len(tpmpCurrentNode[0][0])-1
								tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
							
							didAnythingHappen=True
						# DONT PUT ANTHING AFTER HERE AND ON THE LINES WITH #, any else scenarios should naturally flow to multiple possibilities case
						# .. if 1 possibility found, update tree and stuff and edge/piece tracker then re-loop this inner loop, also update currentNode and stuff etc and didAnythingHappen
					#
				# ...
				opmpEdgeInd-=1
				if opmpEdgeInd==-1:
					if opmpPieceInd>0:
						opmpPieceInd-=1
						opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
					elif opmpPathDepth<len(currentPath)-1:
						opmpPathDepth+=1
						opmpCurrentNode=opmpCurrentNode[1][currentPath[opmpPathDepth]]
						opmpPieceInd = len(opmpCurrentNode[0][0])-1
						opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
					else: # tested every edge of every piece in current puzzle layout
						break
		
		# second passthrough no conflicting 2 piece addition (effectively 1 possibility)
		# if didAnythingHappen==False:
		if opspEdgeInd==-1 and tpspEdgeInd==-1 and opmpEdgeInd==-1 and tpmpEdgeInd!=-1:
			
			while opspEdgeInd==-1 and tpspEdgeInd==-1 and opmpEdgeInd==-1 and tpmpEdgeInd!=-1:
				
				currentPieceID = tpmpCurrentNode[0][0][tpmpPieceInd][0]
				currentEdgeID = tpmpEdgeInd
				
				# need to check if first empty space would only form connection with 1 edge i.e. current edge
				# then for loop each empty space connected to each edge of the main space to find spaces that would only form 1 other connection (not including the one that would be formed with the current main space)
				# then for loop each compatible edgepair from current real peice to main blank space, and within this do another for loop each piece with compatible edgepair with the connection between the 2 ghost pieces and finally if the 2nd ghost piece has compatible connection with other real piece in layout, add to compatible list
				# lastly, iterate all compatible 2 piece additions to find fully matching additions, as soon as 2 conflicting, stop
				if currentLayoutData[currentPieceID][1][currentEdgeID] is None: # if edge has no piece connecting to it, there must be an empty space for a piece next to this edge
					
					actuallyFullyCompatibleAdditions = [] # previous fullyCompatibleAdditions might have just been used for fully matching+compatible additions but this time just for fully compatible
					
					# potentialPieceRequirements1 = []
					
					globalOrientationFirstRealPiece = currentLayoutData[currentPieceID][0][1]
					mainConnectionPieceCoord = currentLayoutData[currentPieceID][0][0]
					firstRealPieceEdgeKey = largePieceDatabase[currentPieceID][1][0][currentEdgeID][0]
					localOrientationFirstRealPieceEdge = localEdgeOrientationRepresentationsReversed[firstRealPieceEdgeKey]
					globalOrientationFirstRealPieceEdge = (localOrientationFirstRealPieceEdge + globalOrientationFirstRealPiece)%4
					
					xOrientationModifier = abs((globalOrientationFirstRealPieceEdge+1)%4-2)-1
					yOrientationModifier = abs((globalOrientationFirstRealPieceEdge)%4-2)-1
					ghostPieceCoord1 = (mainConnectionPieceCoord[0]+xOrientationModifier, mainConnectionPieceCoord[1]+yOrientationModifier)
					
					# Just going to iterate all 4 sides of potential piece/ghost piece even though I already know 1 (the mainConnectionPiece)
					totalPossibleConnections = 0
					for tmpN in range(0, 4):
						xOrientationModifier = abs((tmpN+1)%4-2)-1
						yOrientationModifier = abs((tmpN)%4-2)-1
						coordAtCurrentSideOfGhostPiece = (ghostPieceCoord1[0]+xOrientationModifier, ghostPieceCoord1[1]+yOrientationModifier) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
						if coordAtCurrentSideOfGhostPiece in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
							
							totalPossibleConnections+=1
							
						
					if totalPossibleConnections == 1:
						
						# iterate the 4 sides of the empty space, if the side has another empty space there, check for connections, if 1, test stuff further, else pass
						
						otherRealPieceID=None
						for tmpN in range(0, 4):# for each 2nd empty space connecting to the first empty space, there should be exactly 3 since one is to the edge in the actual piece we started from
							xOrientationModifier = abs((tmpN+1)%4-2)-1
							yOrientationModifier = abs((tmpN)%4-2)-1
							coordAtCurrentSideOfGhostPiece = (ghostPieceCoord1[0]+xOrientationModifier, ghostPieceCoord1[1]+yOrientationModifier)
							if coordAtCurrentSideOfGhostPiece not in layoutCoordDict: # if first empty space has another empty space on one of it's sides, check if that empty space also only has 1 connection
								potentialPieceRequirements2 = []
								totalPossibleConnections2 = 0
								globalOrientationNextSideOfGhostPiece2 = None
								for tmpM in range(0, 4):
									xOrientationModifier2 = abs((tmpM+1)%4-2)-1
									yOrientationModifier2 = abs((tmpM)%4-2)-1
									coordNextToSecondEmptySpace = (coordAtCurrentSideOfGhostPiece[0]+xOrientationModifier2, coordAtCurrentSideOfGhostPiece[1]+yOrientationModifier2) # if a piece exists here, itll have an edge that connects to an edge in the ghost piece
									if coordNextToSecondEmptySpace in layoutCoordDict: # find the side that connects to a side of the ghost piece i.e. the side that points towards ghostPieceCoord
										
										totalPossibleConnections2+=1
										
										# assigning variables in case there is only 1 possible connection, then I don't need to loop through each side again to find the data about the 1 connection
										globalOrientationNextSideOfGhostPiece2=tmpM
										otherRealPieceID = layoutCoordDict[coordNextToSecondEmptySpace]
									
								if totalPossibleConnections2==1: # now we have a second empty space on one of the sides of the first empty space where both empty spaces only have 1 connection to a current real layout piece
									
									
									globalOrientationCurrentSideOfGhostPiece1 = (globalOrientationFirstRealPieceEdge+2)%4
									globalOrientationNextSideOfGhostPiece1 = tmpN
									
									globalOrientationCurrentSideOfGhostPiece2 = (globalOrientationNextSideOfGhostPiece1+2)%4
									# globalOrientationNextSideOfGhostPiece2
									
									globalOrientationRecievingSideOfOtherRealPiece = (globalOrientationNextSideOfGhostPiece2+2)%4
									globalOrientationOtherRealPiece = currentLayoutData[otherRealPieceID][0][1]
									localOrientationRecievingSideOfOtherRealPiece = (globalOrientationRecievingSideOfOtherRealPiece-globalOrientationOtherRealPiece)%4
									recievingSideOfOtherRealPieceKey = localEdgeOrientationRepresentations[localOrientationRecievingSideOfOtherRealPiece]
									
									otherRealPieceEdgeID = None
									for tmpI, tmpEdge in enumerate(largePieceDatabase[otherRealPieceID][1][0]):
										if tmpEdge[0] == recievingSideOfOtherRealPieceKey:
											otherRealPieceEdgeID=tmpI
											break
									if otherRealPieceEdgeID is None:
										print("wat?dr23332r3y77d")
										exit()
									
									for realToGhostEdgePair1 in prelimCompatPairsInniesAndOutiesInds[currentPieceID][currentEdgeID]:
										
										edgeKeyCurrentSideGhostPiece1 = largePieceDatabase[realToGhostEdgePair1[3]][1][0][realToGhostEdgePair1[4]][0]
										
										
										needAmountAntiClockwise = globalOrientationNextSideOfGhostPiece1 - globalOrientationCurrentSideOfGhostPiece1
										
										localOrientationCurrentSideGhostPiece1 = localEdgeOrientationRepresentationsReversed[edgeKeyCurrentSideGhostPiece1]
										localOrientationNextSideGhostPiece1 = (localOrientationCurrentSideGhostPiece1 + needAmountAntiClockwise)%4
										edgeKeyNextSideGhostPiece1 = localEdgeOrientationRepresentations[localOrientationNextSideGhostPiece1]
										
										tmpNextSideGhostPiece1ID = None
										for tmpI, tmpEdge in enumerate(largePieceDatabase[realToGhostEdgePair1[3]][1][0]):
											if tmpEdge[0] == edgeKeyNextSideGhostPiece1:
												tmpNextSideGhostPiece1ID=tmpI
												break
										if tmpNextSideGhostPiece1ID is None:
											print("wat?dr232r3y77d3k3k3")
											exit()
										
										for ghost1ToGhost2EdgePair in prelimCompatPairsInniesAndOutiesInds[realToGhostEdgePair1[3]][tmpNextSideGhostPiece1ID]:
											
											edgeKeyCurrentSideGhostPiece2 = largePieceDatabase[ghost1ToGhost2EdgePair[3]][1][0][ghost1ToGhost2EdgePair[4]][0]
											
											
											needAmountAntiClockwise2 = globalOrientationNextSideOfGhostPiece2 - globalOrientationCurrentSideOfGhostPiece2
											
											localOrientationCurrentSideGhostPiece2 = localEdgeOrientationRepresentationsReversed[edgeKeyCurrentSideGhostPiece2]
											localOrientationNextSideGhostPiece2 = (localOrientationCurrentSideGhostPiece2 + needAmountAntiClockwise2)%4
											edgeKeyNextSideGhostPiece2 = localEdgeOrientationRepresentations[localOrientationNextSideGhostPiece2]
											
											tmpNextSideGhostPiece2ID = None
											for tmpI, tmpEdge in enumerate(largePieceDatabase[ghost1ToGhost2EdgePair[3]][1][0]):
												if tmpEdge[0] == edgeKeyNextSideGhostPiece2:
													tmpNextSideGhostPiece2ID=tmpI
													break
											if tmpNextSideGhostPiece2ID is None:
												print("wat?dr2312r3y77d3k3k3")
												exit()
											
											
											# for loop to check if the 2nd ghost piece has connection to final real edge
											
											for otherRealEdgePair in prelimCompatPairsInniesAndOutiesInds[otherRealPieceID][otherRealPieceEdgeID]:
												if otherRealEdgePair[3] == ghost1ToGhost2EdgePair[3] and otherRealEdgePair[4] == tmpNextSideGhostPiece2ID:
													ghostPiece1Orientation = (globalOrientationCurrentSideOfGhostPiece1-localOrientationCurrentSideGhostPiece1)%4
													ghostPiece2Orientation = (globalOrientationCurrentSideOfGhostPiece2-localOrientationCurrentSideGhostPiece2)%4
													
													firstRealPieceID = currentPieceID
													ghostPiece1ID = realToGhostEdgePair1[3]
													ghostPiece2ID = ghost1ToGhost2EdgePair[3]
													# otherRealPieceID = 
													
													firstPairEdgeIDs = (currentEdgeID, realToGhostEdgePair1[4])
													secondPairEdgeIDs = (tmpNextSideGhostPiece1ID, ghost1ToGhost2EdgePair[4])
													thirdPairEdgeIDs = (tmpNextSideGhostPiece2ID, otherRealPieceEdgeID)
													
													ghostPieceCoord2 = coordAtCurrentSideOfGhostPiece
													
													actuallyFullyCompatibleAdditions.append( (firstRealPieceID, ghostPiece1ID, ghostPiece2ID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs, ghostPiece1Orientation, ghostPiece2Orientation, globalOrientationNextSideOfGhostPiece1, ghostPieceCoord1, ghostPieceCoord2) )
													# edgePair IDs are in expected/obvious order, first real to ghost 1 to ghost 2 to second real
													
						
					
					fullyMatchingAdditions = []
					# conflictExists = False
					for fullyCompatibleAddition in actuallyFullyCompatibleAdditions:
						firstRealPieceID, ghostPiece1ID, ghostPiece2ID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs, ghostPiece1Orientation, ghostPiece2Orientation, globalOrientationNextSideOfGhostPiece1, ghostPieceCoord1, ghostPieceCoord2 = fullyCompatibleAddition
						
						avgScore = 0
						
						newSimScore = updateSimilarityScore(firstRealPieceID, firstPairEdgeIDs[0], ghostPiece1ID, firstPairEdgeIDs[1], detailLevel?, data structures..., ...)
						if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
							... maybe just remove the compatibility entries altogether?
						else:
							avgScore+=newSimScore
							newSimScore = updateSimilarityScore(ghostPiece1ID, secondPairEdgeIDs[0], ghostPiece2ID, secondPairEdgeIDs[1], detailLevel?, data structures..., ...)
							if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
								... maybe just remove the compatibility entries altogether?
							else:
								avgScore+=newSimScore
								newSimScore = updateSimilarityScore(ghostPiece2ID, thirdPairEdgeIDs[0], otherRealPieceID, thirdPairEdgeIDs[1], detailLevel?, data structures..., ...)
								if newSimScore is None or newSimScore>similarityThreshold: # remember lower score is better so above threshold is bad
									... maybe just remove the compatibility entries altogether?
								else:
									avgScore+=newSimScore
									avgScore=avgScore/3
									tmpDataToAdd = (ghostPiece1ID, ghostPiece1Orientation, globalOrientationNextSideOfGhostPiece1, ghostPiece2ID, ghostPiece2Orientation, avgScore, ghostPieceCoord1, ghostPieceCoord2, firstRealPieceID, otherRealPieceID, firstPairEdgeIDs, secondPairEdgeIDs, thirdPairEdgeIDs)
									
									fullyMatchingAdditions.append(tmpDataToAdd) # any data to be added to layout, schema, etc...
					groupedFullyMatchingAdditions=[]
					if len(fullyMatchingAdditions)==1:
						groupedFullyMatchingAdditions = [[fullyMatchingAdditions[0]]]
					if len(fullyMatchingAdditions)>1:
						groupedFullyMatchingAdditions = [[fullyMatchingAdditions[0]]]
						for fullyMatchingAddition in fullyMatchingAdditions[1:]:
							ghostPiece1ID, ghostPiece1Orientation, globalOrientationNextSideOfGhostPiece1, ghostPiece2ID, ghostPiece2Orientation = fullyMatchingAddition[:5]
							addedSomewhere=False
							for existingGroup in groupedFullyMatchingAdditions:
								conflictExists=False
								for existingAddition in existingGroup:
									tmpghostPiece1ID, tmpghostPiece1Orientation, tmpglobalOrientationNextSideOfGhostPiece1, tmpghostPiece2ID, tmpghostPiece2Orientation = existingAddition[:5]
									if tmpghostPiece1ID != ghostPiece1ID or tmpghostPiece1Orientation != ghostPiece1Orientation:
										conflictExists=True
										break
									elif tmpglobalOrientationNextSideOfGhostPiece1 == globalOrientationNextSideOfGhostPiece1 and (tmpghostPiece2ID != ghostPiece2ID or tmpghostPiece2Orientation != ghostPiece2Orientation):
										conflictExists=True
										break
									elif tmpghostPiece2ID == ghostPiece2ID and tmpglobalOrientationNextSideOfGhostPiece1 != globalOrientationNextSideOfGhostPiece1:
										conflictExists=True
										break
								if not(conflictExists):
									existingGroup.append(fullyMatchingAddition)
									addedSomewhere=True
									break
							if not(addedSomewhere):
								groupedFullyMatchingAdditions.append([fullyMatchingAddition])
					
					if len(groupedFullyMatchingAdditions)>0:
						for groupedAdditions in groupedFullyMatchingAdditions:
							bestAvgScore = float('inf')
							bestAddition = None
							for tmpMatchingAddition in groupedAdditions:
								if tmpMatchingAddition[5]<bestAvgScore:
									bestAvgScore=tmpMatchingAddition[5]
									bestAddition=tmpMatchingAddition
							tmpNewAdditionPieceID1 = bestAddition[0]
							tmpNewAdditionPieceID2 = bestAddition[3]
							newNode = [ [ [(tmpNewAdditionPieceID1), (tmpNewAdditionPieceID2)], bestAddition ], [] ] # [[[(pieceID1), (pieceID2)], nodedata...], []]
							deepestNode[1].append(newNode)
						
						currentPath.append(len(deepestNode[1])-1)
						
						bestAddition = deepestNode[1][currentPath[-1]][0][1]
						
						tmpNewAdditionPieceID1 = bestAddition[0]
						tmpNewAdditionPieceID2 = bestAddition[3]
						tmpNewAdditionPieceCoord1 = bestAddition[6]
						tmpNewAdditionPieceCoord2 = bestAddition[7]
						tmpNewAdditionPieceGlobalOrientation1 = bestAddition[1]
						tmpNewAdditionPieceGlobalOrientation2 = bestAddition[4]
						
						layoutCoordDict[tmpNewAdditionPieceCoord1] = tmpNewAdditionPieceID1
						layoutCoordDict[tmpNewAdditionPieceCoord2] = tmpNewAdditionPieceID2
						
						currentLayoutData[tmpNewAdditionPieceID1][0] = (tmpNewAdditionPieceCoord1, tmpNewAdditionPieceGlobalOrientation1)
						currentLayoutData[tmpNewAdditionPieceID2][0] = (tmpNewAdditionPieceCoord2, tmpNewAdditionPieceGlobalOrientation2)
						
						tmpPair1Piece1ID = bestAddition[8]
						tmpPair1Piece2ID = bestAddition[0]
						tmpPair1Piece1EdgeID = bestAddition[10][0]
						tmpPair1Piece2EdgeID = bestAddition[10][1]
						currentLayoutData[tmpPair1Piece1ID][1][tmpPair1Piece1EdgeID] = (tmpPair1Piece2ID, tmpPair1Piece2EdgeID)
						currentLayoutData[tmpPair1Piece2ID][1][tmpPair1Piece2EdgeID] = (tmpPair1Piece1ID, tmpPair1Piece1EdgeID)
						
						tmpPair2Piece1ID = bestAddition[0]
						tmpPair2Piece2ID = bestAddition[3]
						tmpPair2Piece1EdgeID = bestAddition[11][0]
						tmpPair2Piece2EdgeID = bestAddition[11][1]
						currentLayoutData[tmpPair2Piece1ID][1][tmpPair2Piece1EdgeID] = (tmpPair2Piece2ID, tmpPair2Piece2EdgeID)
						currentLayoutData[tmpPair2Piece2ID][1][tmpPair2Piece2EdgeID] = (tmpPair2Piece1ID, tmpPair2Piece1EdgeID)
						
						tmpPair3Piece1ID = bestAddition[3]
						tmpPair3Piece2ID = bestAddition[9]
						tmpPair3Piece1EdgeID = bestAddition[12][0]
						tmpPair3Piece2EdgeID = bestAddition[12][1]
						currentLayoutData[tmpPair3Piece1ID][1][tmpPair3Piece1EdgeID] = (tmpPair3Piece2ID, tmpPair3Piece2EdgeID)
						currentLayoutData[tmpPair3Piece2ID][1][tmpPair3Piece2EdgeID] = (tmpPair3Piece1ID, tmpPair3Piece1EdgeID)
						
						deepestNode = deepestNode[1][currentPath[-1]]
						
						# update all previous/higher-priority loop-types since they now have new edges to test
						opspPathDepth+=1
						opspCurrentNode=opspCurrentNode[1][currentPath[opspPathDepth]]
						opspPieceInd = len(opspCurrentNode[0][0])-1
						opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
						
						tpspPathDepth+=1
						tpspCurrentNode=tpspCurrentNode[1][currentPath[tpspPathDepth]]
						tpspPieceInd = len(tpspCurrentNode[0][0])-1
						tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
						
						opmpPathDepth+=1
						opmpCurrentNode=opmpCurrentNode[1][currentPath[opmpPathDepth]]
						opmpPieceInd = len(opmpCurrentNode[0][0])-1
						opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
						
						didAnythingHappen=True
					
				tpmpEdgeInd-=1
				if tpmpEdgeInd==-1:
					if tpmpPieceInd>0:
						tpmpPieceInd-=1
						tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
					elif tpmpPathDepth<len(currentPath)-1:
						tpmpPathDepth+=1
						tpmpCurrentNode=tpmpCurrentNode[1][currentPath[tpmpPathDepth]]
						tpmpPieceInd = len(tpmpCurrentNode[0][0])-1
						tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
					else: # tested every edge of every piece in current puzzle layout
						break
		
		
		if opspEdgeInd==-1 and tpspEdgeInd==-1 and opmpEdgeInd==-1 and tpmpEdgeInd==-1:
			# ...save this piece layout if it's good enough or the best current, whatever the plan is, only save required data and maybe reformat but maybe not needed, and dont need to save any tree structures here, would be dumb/wasteful...
			
			if len(layoutCoordDict)>len(bestLayoutCoordDict):
				bestLayoutCoordDict = deepcopy(layoutCoordDict)
				bestCurrentLayoutData = deepcopy(currentLayoutData)
			
			# first get the first multiple potential node on the path starting from the deepest node, then update stuff from there to the deepest node on path, then remove the indices from currentPath
			# need to do it forwards rather than intuitive backtracking direction because backwards would require walking down full path up to the next node every time since cant just step backwards up a tree in 1 step like forwards
			
			nextMultiplePotential = None
			tmpI = len(currentPath)-1
			if tmpI>=0:
				while True:
					if currentPath[tmpI]>0:
						nextMultiplePotential=tmpI
						break
					tmpI-=1
					if tmpI<0:
						break
			
			if nextMultiplePotential is not None:
				# startI = nextMultiplePotential
				
				newSecondLastNode = expansionTree
				for tmpI in range(nextMultiplePotential):
					newSecondLastNode=newSecondLastNode[1][currentPath[tmpI]]
				# when done, delete the already-used potential from newSecondLastNode[1]
				currNode = newSecondLastNode[1][currentPath[nextMultiplePotential]]
				tmpTracker = nextMultiplePotential
				while True:
					for tmpPiece in currNode[0][0]:
						tmpPieceID = tmpPiece[0]
						tmpPieceCoord = currentLayoutData[tmpNewAdditionPieceID1][0][0]
						layoutCoordDict.pop(tmpPieceCoord)
						for tmpEdgePairInd in range(len(currentLayoutData[tmpPieceID][1])):
							tmpOtherPieceID = currentLayoutData[tmpPieceID][1][tmpEdgePairInd][0]
							tmpOtherEdgeID = currentLayoutData[tmpPieceID][1][tmpEdgePairInd][1]
							currentLayoutData[tmpOtherPieceID][1][tmpOtherEdgeID]=None
							currentLayoutData[tmpPieceID][1][tmpEdgePairInd]=None
						currentLayoutData[tmpNewAdditionPieceID1][0]=None
					
					tmpTracker+=1
					if tmpTracker>len(currentPath)-1:
						break
					currNode=currNode[1][currentPath[tmpTracker]]
				
				newSecondLastNode[1].pop(currentPath[nextMultiplePotential])
				currentPath = currentPath[:nextMultiplePotential]
				
				currentPath.append(len(newSecondLastNode[1])-1)
				
				opspPathDepth=len(currentPath)-1
				tpspPathDepth=len(currentPath)-1
				opmpPathDepth=len(currentPath)-1
				tpmpPathDepth=len(currentPath)-1
				
				opspCurrentNode=expansionTree
				tpspCurrentNode=expansionTree
				opmpCurrentNode=expansionTree
				tpmpCurrentNode=expansionTree
				for tmpI in currentPath:
					opspCurrentNode=opspCurrentNode[1][tmpI]
					tpspCurrentNode=tpspCurrentNode[1][tmpI]
					opmpCurrentNode=opmpCurrentNode[1][tmpI]
					tpmpCurrentNode=tpmpCurrentNode[1][tmpI]
				opspPieceInd=len(opspCurrentNode[0][0])-1
				tpspPieceInd=len(tpspCurrentNode[0][0])-1
				opmpPieceInd=len(opmpCurrentNode[0][0])-1
				tpmpPieceInd=len(tpmpCurrentNode[0][0])-1
				opspEdgeInd=len(currentLayoutData[opspCurrentNode[0][0][opspPieceInd][0]][1])-1
				tpspEdgeInd=len(currentLayoutData[tpspCurrentNode[0][0][tpspPieceInd][0]][1])-1
				opmpEdgeInd=len(currentLayoutData[opmpCurrentNode[0][0][opmpPieceInd][0]][1])-1
				tpmpEdgeInd=len(currentLayoutData[tpmpCurrentNode[0][0][tpmpPieceInd][0]][1])-1
				
			... what if it is None? then we're done
		
	return



exitlater=False
debuggingAnnulusIntersection=True
def miniCacheSkip(currWindowInd, windowAmount, leftWindowRawDatInd, leftPotentialRawDatInd, window, trackerList, compatibleLists, wiggleConstraints, seedCoord1, seedCoord2, stepCoords1, stepCoords2, rawDat1, rawDat2, stepLength1, stepLength2, edge1SeedIsAfterStepCoordIndN, edge2SeedIsAfterStepCoordIndN, params, edge1, edge2, potentialCache, currentBranchOfChainDatTree, limitWiggleRoomCalcCaches, windowSegWildCardTreeCaches, currBranchOfChainDatTreeIndexList, windowMatches,estimatedScale, edge1PixelationError, edge2PixelationError, windowTempClockwiseCheckCache, angleSideWindowCache):
	global debuggingAnnulusIntersection
	# onlyLWRskip: if we already have a window->potential pair and cant use wild card just want quick limitWiggleRoom skip
	# if onlyLWRskip: #currWindowInd == windowAmount-1: # actually this should prob be if currWindowInd == windowAmount-1 AND we already have a potential pair, if we havent queried for compatibleLists yet then prob pass to below
		# if ((leftWindowRawDat, leftPotentialRawDat), (rightWindowRawDat, rightPotentialRawDat)) in limitWiggleRoomCalcCaches[currWindowInd-1][1]:
			# limWigRoomBigSkipDat = limitWiggleRoomCalcCaches[currWindowInd-1][1][((leftWindowRawDat, leftPotentialRawDat), (rightWindowRawDat, rightPotentialRawDat))]
			# currOverlapWithPotentialWiggCon = limitWiggleRoom(..., currOverlapWithPotentialWiggCon, ...)
		# else:
			# specificWindowSegLimitWiggleRoomCalcCache = limitWiggleRoomCalcCaches[currWindowInd-1][1]
			# ... inputs
			# currOverlapWithPotentialWiggCon = limitWiggleRoom(..., currOverlapWithPotentialWiggCon, ...)
		# don't need to return True, this will always succeed because if no cache data exists it'll just call limitWiggleRoom default way
		
	# elif current pair wiggle room is a subset of cached pair e.g. if current pair is constrained and cached pair was fully unconstrained due to being the 2nd window in a previous sliding window
	# then simply copy any branches that made it to either windowAmount or windowAmount-1 and out of these, remove any that have 0 intersection at windowAmount-1 when intersected with current constraint (never care about lineseg at cached windowAmount because thats too far)
	# NOTE!!!! since this can still happen like halway through the window, make sure its capped at windowAmount-1 in absolute terms not relative with the assumption that this only happens at the second window e.g. make sure to only go as deep as windowAmount - currWindowInd - 1 or whatever
	#else: # need to do limitWiggleRoom first regardless cause can only decide if we can skip whole branches based on intersection of wiggleConstraint AFTER being constrained by minimum of 1 point every X length
	global yesPrint
	global exitlater
	
	global allWhileLoopChains
	global allChainsAtLeastSize2
	global allChainsAtLeastSize3
	global allChainsAtLeastSize4
	global allChainsAtLeastSize5
	global allChainsAtLeastSize6
	global windowMatchesAmount

	global allChainsAtLeastSize1
	
	global tempTimeKeep
	global tempTimeKeepAmount
	
	global totalTimeSimilarityInstanceCall
	global amountSimilarityInstanceCall
	global totalTimeLastSectionOfSimilarityInstance
	global amountLastSectionOfSimilarityInstance
	
	if True:
		depthReq = windowAmount-currWindowInd
		
		if True: # sanity check
			if windowSegWildCardTreeCaches[currWindowInd-1][0]!=window[currWindowInd][0]:
				print("sanity check failed 219j")
				exit()
			
			if wiggleConstraints[currWindowInd] is not None:
				print("sanity check failed 938h")
				exit()
		
		if len(windowSegWildCardTreeCaches[currWindowInd-1][1])>0:
			# check if subset
			wildCardDat = windowSegWildCardTreeCaches[currWindowInd-1][1] # -1 because caches lag behind by 1
			
			currentWiggleConstraintGivenByPreviousPair = wiggleConstraints[currWindowInd-1] # -1 because we want constraint given by previous window seg i.e. window seg on the left
			
			wildCardWiggleCoverage = wildCardDat[0] # for now assume 1 full interval, will need to iterate intervals if ever allowed more than 1 and data for each interval will also have to be separate
			wildCardDatTree = wildCardDat[1]
			
			# print(currentWiggleConstraintGivenByPreviousPair)
			# print(wildCardWiggleCoverage)
			
			currWiggleRoomSubsetOfCached, dontCareIntersection = angleIntervalIntersection(currentWiggleConstraintGivenByPreviousPair, wildCardWiggleCoverage)
			# print(dontCareIntersection)
			
			# print(currWiggleRoomSubsetOfCached)
			# print("-----------------------")
			# print()
			if currWiggleRoomSubsetOfCached:
				#skip stuff and update loop stuff
				#...
				# for chainDatWithLength in wildCardDat[1]:
					# add pointers to current data because even if we dont finish a chain we want the data stored in the fully wild card data for the current window[0] seg
					#...
					# for chainDat in chainDatWithLength[1]:
						#...
				# Tree iteration
				
				# tree iterator vars and stuff
				#...
				
				# tree while loop
				# ...
				tempCompatibleChainTree = []
				tempDepthIndexTrackerList = [] # 
				
				# initialise, first depth needs to check for overlap wiggle room AND min pts per X arclength
				for tmpI in range(0, len(wildCardDatTree)):
					if leftPotentialRawDatInd <= wildCardDatTree[tmpI][0][1]: # same as minimumIndex stuff, if window indices are increasing then the query/potential edge indices must also increase, I don't think I currently check if potential pts on the same line occur increasingly on the line but maybe do that if it doesnt add too much computation
						potentialChainWiggleConstraint = wildCardDatTree[tmpI][1]
						dontCare, currOverlapWithPotentialWiggCon = angleIntervalIntersection(currentWiggleConstraintGivenByPreviousPair, potentialChainWiggleConstraint)
						if len(currOverlapWithPotentialWiggCon)>0:
							##################################################################
							withinOrientationBracket=False
							
							# FOR NOW JUST MAKING THIS EXACT SAME AS WITHOUT CACHE METHOD, BUT CAN MAKE THIS MUCH FASTER BY SIMPLY CHECKING IF IN RANGE OR SOMETHING
							# window bracket:currOverlapWithPotentialWiggCon
							tempOrientation = window[currWindowInd][1]
							if tempOrientation < 0:
								tempOrientation+=math.pi*2
							orientationRange = [tempOrientation-params['orientationError'], tempOrientation+params['orientationError']]
							orientationRange = [orientationRange[0]+currOverlapWithPotentialWiggCon[0], orientationRange[1]+currOverlapWithPotentialWiggCon[1]]
							if orientationRange[1]-orientationRange[0] >= 2*math.pi:
								orientationRange = [0, 2*math.pi]
							else:
								while orientationRange[0] < 0:
									orientationRange[0]+=math.pi*2
								while orientationRange[0] >= math.pi*2:
									orientationRange[0]-=math.pi*2
								while orientationRange[1] <= 0:
									orientationRange[1]+=math.pi*2
								while orientationRange[1] > math.pi*2:
									orientationRange[1]-=math.pi*2
								if abs(orientationRange[0]-math.pi)<0.0001:
									orientationRange[0]=math.pi
								elif abs(orientationRange[0]--math.pi)<0.0001:
									orientationRange[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
								if abs(orientationRange[1]-math.pi)<0.0001:
									orientationRange[1]=math.pi
								elif abs(orientationRange[1]--math.pi)<0.0001:
									orientationRange[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							partitionId1 = int(math.floor(orientationRange[0]/params['segOrientationPartitionSize']))
							partitionId2 = int(math.floor(orientationRange[1]/params['segOrientationPartitionSize']))
							
							tempOrientation = rawDat2[wildCardDatTree[tmpI][0][1]][1] # potentialOrientation
							if tempOrientation < 0:
								tempOrientation+=math.pi*2
							partitionIdPotential = int(math.floor(tempOrientation/params['segOrientationPartitionSize']))
							
							if partitionId1 <= partitionId2:
								if partitionId1 <= partitionIdPotential and partitionIdPotential <= partitionId2:
									withinOrientationBracket=True
							else:
								if partitionId1 <= partitionIdPotential or partitionIdPotential <= partitionId2:
									withinOrientationBracket=True
							####################################################################
							
							if withinOrientationBracket:
								
								tempWindowP1 = None
								tempWindowP2 = None
								angleSide1 = None
								angleSide2 = None
								### subAreaTracker+1 here because we're using current wiggle constraints to constrain search parameters for the next window subarea, the reason [0] is used at the beginning of this function is because we kind of do subAreaTracker and wiggleConstraints[subAreaTracker-1] rather than subAreaTracker+1 and wiggleConstraints[subAreaTracker] since angleWiggleRoom is the 'previous' wiggle constraint for subAreaTracker==0
								if window[currWindowInd][4]:
									tempWindowP1 = stepCoords1[rawDat1[window[currWindowInd][0]][0][0]][0]
									tempWindowP2 = stepCoords1[rawDat1[window[currWindowInd][0]][0][1]][0]
									angleSide1 = window[currWindowInd][2][0]
									angleSide2 = window[currWindowInd][2][1]
								else:
									tempWindowP1 = stepCoords1[rawDat1[window[currWindowInd][0]][0][1]][0]
									tempWindowP2 = stepCoords1[rawDat1[window[currWindowInd][0]][0][0]][0]
									angleSide1 = window[currWindowInd][2][1]
									angleSide2 = window[currWindowInd][2][0]
								
								
								tempLinearTransformedAnnulusSectorDat = constructLinearTransformedAnnulusSectorDat(estimatedScale, params, tempWindowP1, tempWindowP2, seedCoord1, edge1PixelationError, edge2PixelationError, angleSide1, angleSide2, currOverlapWithPotentialWiggCon, seedCoord2)
								
								potentialSegIntersectsAnnulusSector=None
								if debuggingAnnulusIntersection:
									currOverlapWithPotentialWiggCon = searchOBBTree(None, rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, None, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=wildCardDatTree[tmpI][0][1], debugReturnConstrainedWiggleRoom=currOverlapWithPotentialWiggCon, window=window, currWindowInd=currWindowInd)
									if currOverlapWithPotentialWiggCon is not None and len(currOverlapWithPotentialWiggCon)>0:
										potentialSegIntersectsAnnulusSector=True
									else:
										potentialSegIntersectsAnnulusSector=False
								else:
									potentialSegIntersectsAnnulusSector = searchOBBTree(None, rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, None, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=wildCardDatTree[tmpI][0][1])
								
								if potentialSegIntersectsAnnulusSector:
									allWhileLoopChains+=1
									
									if True: # sanity check
										if limitWiggleRoomCalcCaches[currWindowInd][0]!=window[currWindowInd][0]:
											print("sanity check failed 213t49j")
											exit()
										if limitWiggleRoomCalcCaches[currWindowInd-1][0] != leftWindowRawDatInd:
											print("sanity check failed 2552r")
											exit()
									
									if False:#((leftWindowRawDatInd, leftPotentialRawDatInd), wildCardDatTree[tmpI][0]) in limitWiggleRoomCalcCaches[currWindowInd-1][1]:
										limWigRoomBigSkipDat = limitWiggleRoomCalcCaches[currWindowInd-1][1][((leftWindowRawDatInd, leftPotentialRawDatInd), wildCardDatTree[tmpI][0])]
										if yesPrint:#==False:
											print("1111111111111111111111111111111111111111111111111111")
										currOverlapWithPotentialWiggCon = limitWiggleRoom(None, currWindowInd, potentialCache, None, None, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=False, specificWindowSegLimitWiggleRoomCalcCache=None, limWigRoomBigSkipDat=limWigRoomBigSkipDat, limWigRoomFastConstraint=currOverlapWithPotentialWiggCon, limWigRoomFastDat=None) #wildCardDatTree[tmpI][0]
										# currOverlapWithPotentialWiggCon = limitWiggleRoom(..., currOverlapWithPotentialWiggCon, ...)
									else:
										specificWindowSegLimitWiggleRoomCalcCache = limitWiggleRoomCalcCaches[currWindowInd-1][1]
										# limWigRoomFastDat = [(potentialRawDatIndLeft, potentialRawDatIndRight), ]
										limWigRoomFastDat = [(leftPotentialRawDatInd, wildCardDatTree[tmpI][0][1])] # thought i was gonna need more data than just the left/right potential rawDatInds so I put it in a list
										# wildCardDatTree[tmpI][0]
										
										# ... inputs
										if yesPrint:#==False:
											print("2222222222222222222222222222222222222222222222222222222")
											print(((leftWindowRawDatInd, leftPotentialRawDatInd), wildCardDatTree[tmpI][0]))
											print(currWindowInd)
											# if ((leftWindowRawDatInd, leftPotentialRawDatInd), wildCardDatTree[tmpI][0]) == ((5, 10), (6, 10)):
												# exit()
												# exitlater=True
										currOverlapWithPotentialWiggCon = limitWiggleRoom(None, currWindowInd, potentialCache, None, None, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=False, specificWindowSegLimitWiggleRoomCalcCache=specificWindowSegLimitWiggleRoomCalcCache, limWigRoomBigSkipDat=None, limWigRoomFastConstraint=currOverlapWithPotentialWiggCon, limWigRoomFastDat=limWigRoomFastDat)
										# currOverlapWithPotentialWiggCon = limitWiggleRoom(..., currOverlapWithPotentialWiggCon, ...)
										
									if len(currOverlapWithPotentialWiggCon)>0:
										tempCompatibleChainTree.append([tmpI, currOverlapWithPotentialWiggCon, []])
										if currWindowInd==1:
											allChainsAtLeastSize2+=1
										if currWindowInd==2:
											allChainsAtLeastSize3+=1
										if currWindowInd==3:
											allChainsAtLeastSize4+=1
										if currWindowInd==4:
											allChainsAtLeastSize5+=1
										if currWindowInd==5:
											allChainsAtLeastSize6+=1
										# if currWindowInd==6:
											# allChainsAtLeastSize2+=1
				
				
				tempDepthIndexTrackerList.append(len(tempCompatibleChainTree)-1)
				depthTrackerIndFromInitialisation=0 # This is tracking depth in tempDepthIndexTrackerList and w.r.t. root being tempCompatibleChainTree NOT currentBranchOfChainDatTree or currentBranchOfChainDatTree[3] or whatever ... this used to be depthTrackerInd which was confusing because since compatible tree kinda starts 1 ahead or the lists below are set 1 ahead or something its confusing and isnt in sync with window indices
				depthFromCurrWindowInd = 1 # this is used for telling where i am in relation to currWindowInd and to be in sync with window indices
				if depthReq==1:
					print("SOMEHOW DEPTHREQ CAN ACTUALLY BE 1..?")
					exit()
				if depthReq > 1 and len(tempCompatibleChainTree)>0: # and somthing cant remember: # (this function wasnt called just for the last link in the chain) and something cant remember
					while tempDepthIndexTrackerList[0] >= 0:
						#...
						if tempDepthIndexTrackerList[depthTrackerIndFromInitialisation] < 0:
							tempDepthIndexTrackerList.pop(-1)
							depthTrackerIndFromInitialisation-=1
							depthFromCurrWindowInd-=1
							tempDepthIndexTrackerList[depthTrackerIndFromInitialisation]-=1
						else:
							# get the current branch in compatible tree and associated branch in cache tree (need to re-route from root/trunk every time)
							currBranch = wildCardDatTree
							currCompatTreeBranch = tempCompatibleChainTree
							for tmpI in range(0, depthTrackerIndFromInitialisation+1):
								if tmpI == depthTrackerIndFromInitialisation: # just the way iterating this tree works, I want to end up with the full branch but to get there need other condition to route through the branch lists at each depth i.e. [2] in compat tree and [3] in cache tree
									currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]]
									currBranch = currBranch[currCompatTreeBranch[0]]
								else:
									# currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]][2]
									# currBranch = currBranch[currCompatTreeBranch[0]][3]
									
									currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]]
									currBranch = currBranch[currCompatTreeBranch[0]][3]
									currCompatTreeBranch=currCompatTreeBranch[2]
							
							# iterate all branches from current branch in cache tree and test for compatible ones, store compatible ones in branches list for/from current branch in compatible tree
							for tmpI in range(0, len(currBranch[3])):
								# if leftPotentialRawDatInd <= wildCardDatTree[tmpI][0][1]: # dont think I need to assert index order here because these should already be ordered since they were processed through either stitching (like in loop above for initialisation) or through non-cache method which already utilises minimumIndex
								potentialChainWiggleConstraint = currBranch[3][tmpI][1]
								wiggleConstraintGivenByPreviousLinkInChain = currCompatTreeBranch[1] # currentWiggleRoom effectively
								dontCare, currOverlapWithPotentialWiggCon = angleIntervalIntersection(wiggleConstraintGivenByPreviousLinkInChain, potentialChainWiggleConstraint)
								if len(currOverlapWithPotentialWiggCon)>0:
									####### DOES THIS WORK???????????????????????
									tempWindowP1 = None
									tempWindowP2 = None
									angleSide1 = None
									angleSide2 = None
									
									
									if window[currWindowInd+depthFromCurrWindowInd][4]:
										tempWindowP1 = stepCoords1[rawDat1[window[currWindowInd+depthFromCurrWindowInd][0]][0][0]][0]
										tempWindowP2 = stepCoords1[rawDat1[window[currWindowInd+depthFromCurrWindowInd][0]][0][1]][0]
										angleSide1 = window[currWindowInd+depthFromCurrWindowInd][2][0]
										angleSide2 = window[currWindowInd+depthFromCurrWindowInd][2][1]
									else:
										tempWindowP1 = stepCoords1[rawDat1[window[currWindowInd+depthFromCurrWindowInd][0]][0][1]][0]
										tempWindowP2 = stepCoords1[rawDat1[window[currWindowInd+depthFromCurrWindowInd][0]][0][0]][0]
										angleSide1 = window[currWindowInd+depthFromCurrWindowInd][2][1]
										angleSide2 = window[currWindowInd+depthFromCurrWindowInd][2][0]
									
									tempLinearTransformedAnnulusSectorDat = constructLinearTransformedAnnulusSectorDat(estimatedScale, params, tempWindowP1, tempWindowP2, seedCoord1, edge1PixelationError, edge2PixelationError, angleSide1, angleSide2, currOverlapWithPotentialWiggCon, seedCoord2)
									
									potentialSegIntersectsAnnulusSector=None
									if debuggingAnnulusIntersection:
										currOverlapWithPotentialWiggCon = searchOBBTree(None, rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, None, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=currBranch[3][tmpI][0][1], debugReturnConstrainedWiggleRoom=currOverlapWithPotentialWiggCon, window=window, currWindowInd=currWindowInd+depthFromCurrWindowInd)
										if currOverlapWithPotentialWiggCon is not None and len(currOverlapWithPotentialWiggCon)>0:
											potentialSegIntersectsAnnulusSector=True
										else:
											potentialSegIntersectsAnnulusSector=False
									else:
										potentialSegIntersectsAnnulusSector = searchOBBTree(None, rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, None, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=currBranch[3][tmpI][0][1])
									
									####
									
									if potentialSegIntersectsAnnulusSector: ###################### IF NOT, REMOVE AND UNINDENT BELOW
										currCompatTreeBranch[2].append([tmpI, currOverlapWithPotentialWiggCon, []])
										# if currWindowInd+depthFromCurrWindowInd==1:
											# allChainsAtLeastSize2+=1
										if currWindowInd+depthFromCurrWindowInd==2:
											allChainsAtLeastSize3+=1
										if currWindowInd+depthFromCurrWindowInd==3:
											allChainsAtLeastSize4+=1
										if currWindowInd+depthFromCurrWindowInd==4:
											allChainsAtLeastSize5+=1
										if currWindowInd+depthFromCurrWindowInd==5:
											allChainsAtLeastSize6+=1
							
							if len(currCompatTreeBranch[2]) == 0 or depthFromCurrWindowInd+1 == depthReq: # end of branch, go back until highest level branch found with new branches to test
								tempDepthIndexTrackerList[depthTrackerIndFromInitialisation]-=1
							else:
								tempDepthIndexTrackerList.append(len(currCompatTreeBranch[2])-1)
								depthTrackerIndFromInitialisation+=1
								depthFromCurrWindowInd+=1
						
				#### JUST ADDING ALL TO MAIN TREE ##################################
				finalChainList = []
				tempDepthIndexTrackerList = [len(tempCompatibleChainTree)-1]
				actualChainDatTreeIndexTrackerList = [-1]
				# depthTrackerInd=0
				depthTrackerIndFromInitialisation=0
				depthFromCurrWindowInd = 0
				# currChain = []
				# print(currentBranchOfChainDatTree)
				# print("^^^")
				while tempDepthIndexTrackerList[0]>=0:
					if tempDepthIndexTrackerList[depthTrackerIndFromInitialisation] < 0:
						tempDepthIndexTrackerList.pop(-1)
						actualChainDatTreeIndexTrackerList.pop(-1)
						depthTrackerIndFromInitialisation-=1
						depthFromCurrWindowInd-=1
						tempDepthIndexTrackerList[depthTrackerIndFromInitialisation]-=1
					else:
						currBranch = wildCardDatTree
						currCompatTreeBranch = tempCompatibleChainTree
						
						currActualChainDatTreeBranch = currentBranchOfChainDatTree[3] # currentBranchOfChainDatTree[3] is all window[currWindowInd][0], potentialRawDatInd pairs that are compatible given previous chains constraints
						for tmpI in range(0, depthTrackerIndFromInitialisation+1):
							if tmpI == depthTrackerIndFromInitialisation: # just the way iterating this tree works, I want to end up with the full branch but to get there need other condition to route through the branch lists at each depth i.e. [2] in compat tree and [3] in cache tree
								currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]]
								currBranch = currBranch[currCompatTreeBranch[0]]
							else:
								# currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]][2]
								# currBranch = currBranch[currCompatTreeBranch[0]][3]
								
								currCompatTreeBranch = currCompatTreeBranch[tempDepthIndexTrackerList[tmpI]]
								currBranch = currBranch[currCompatTreeBranch[0]][3]
								currCompatTreeBranch=currCompatTreeBranch[2]
						# print("HI")
						for tmpI in range(0, depthTrackerIndFromInitialisation):
							if False:#tmpI == depthTrackerInd-1:
								# print(actualChainDatTreeIndexTrackerList)
								# print(depthTrackerInd)
								# print(currActualChainDatTreeBranch)
								# print(actualChainDatTreeIndexTrackerList[tmpI])
								currActualChainDatTreeBranch = currActualChainDatTreeBranch[actualChainDatTreeIndexTrackerList[tmpI]]
							else:
								currActualChainDatTreeBranch = currActualChainDatTreeBranch[actualChainDatTreeIndexTrackerList[tmpI]][3]
						currActualChainDatTreeBranch.append([currBranch[0], currCompatTreeBranch[1], None, []]) # JUST POINTING TO SAME DATA, I ASSUME NOTHING IN THE TREE CHANGES EVER INCLUDING WHEN PASSED THROUGH LIMITWIGGLEROOM
						actualChainDatTreeIndexTrackerList[depthTrackerIndFromInitialisation]+=1
						
						
						
						artificialDeadEnd=False
						if depthFromCurrWindowInd+1 == depthReq: # no tree needs to be deeper than windowAmount
							veryTempChainTreeRouteFromCurrentBranchOfChainDatTree = []
							for tmpI in actualChainDatTreeIndexTrackerList:
								veryTempChainTreeRouteFromCurrentBranchOfChainDatTree.append(tmpI)
							finalChainList.append(veryTempChainTreeRouteFromCurrentBranchOfChainDatTree)
							artificialDeadEnd=True
						
						if len(currCompatTreeBranch[2])>0 and not(artificialDeadEnd):
							tempDepthIndexTrackerList.append(len(currCompatTreeBranch[2])-1)
							actualChainDatTreeIndexTrackerList.append(-1)
							depthTrackerIndFromInitialisation+=1
							depthFromCurrWindowInd+=1
						else:
							tempDepthIndexTrackerList[depthTrackerIndFromInitialisation]-=1
				
				for finalChain in finalChainList:
					tic = time.perf_counter()
					
					# sanity check
					if firstLoopCheck and len(compatibleLists[currWindowInd])>0: # this function should be called before potentials have been queried for in oobtree
						print(compatibleLists)
						print("sanity check 93e8h3 failed")
						exit()
					if firstLoopCheck and trackerList[currWindowInd]!=0 and trackerList[currWindowInd]!=-1: # this function should be called before potentials have been queried for in oobtree
						print("sanity check 93e234e238h3 failed") # THIS ONE MIGHT FAIL IF I DONT RESET IT AS MUCH AS I DO FOR COMPATIBLELISTS OR MAYBE IF ITS -1 for some reason, maybe its -1 after failed loop rather than default 0
						exit()
					
					firstLoopCheck=False
					
					reqDat = []
					
					# wiggle=None
					pseudoTreeRoot = currentBranchOfChainDatTree[3]
					tmpBranch = pseudoTreeRoot
					for listInd, tmpI in enumerate(finalChain):
						# if need any other data get it, for now just need last link in chain for wiggle
						
						tmpPotentialRawDatInd = tmpBranch[tmpI][0][1]
						reqDat.append([tmpPotentialRawDatInd]) # list in case I need to add more data
						if listInd != len(finalChain)-1:
							tmpBranch = tmpBranch[tmpI][3]
						else:
							tmpBranch = tmpBranch[tmpI]
					
					wiggle = tmpBranch[1]
					
					# scuffed stitching data onto the persistant lists from similarityInstance so I dont need to change a bunch of stuff below that was copied from there
					scuffedInd=0
					for tmpI in range(currWindowInd, len(window)): # len(window)==windowAmount
						
						compatibleLists[tmpI]=[ [reqDat[scuffedInd][0], None] ]
						trackerList[tmpI]=0
						scuffedInd+=1
					
					shiftWindowBy = None
					if wiggle[1] == wiggle[0]:
						shiftWindowBy = wiggle[0]
					elif wiggle[1] > wiggle[0]: # i assume wiggle is always wiggle[1] more anticlockwise than wiggle[0]?
						shiftWindowBy = (wiggle[1] + wiggle[0])/2
					else:
						tempEnd = wiggle[1]+math.pi*2
						shiftWindowBy = (tempEnd+wiggle[0])/2
						if shiftWindowBy>math.pi:
							shiftWindowBy-=math.pi*2
					
					pointPairs = [] # [(windowpt1, otherpt1), (windowpt2, otherpt2), ...]
					pointPairsPotential = []
					
					tempWindowAngleRanges = []
					tempPotentialAngleRanges = []
					
					for windowSeg in window:
						if windowSeg[4]:
							tempWindowAngleRanges.append([windowSeg[2][1], windowSeg[2][0]])
						else:
							tempWindowAngleRanges.append([windowSeg[2][0], windowSeg[2][1]])
					for trackerInd in range(len(trackerList)):
						# compatibleLists[-1][trackerList[-1]][0]
						cacheInd = compatibleLists[trackerInd][trackerList[trackerInd]][0]
						tempPotentialStartAngle = potentialCache[cacheInd][3]
						tempPotentialEndAngle = potentialCache[cacheInd][4]
						if potentialCache[cacheInd][5]:
							tempPotentialAngleRanges.append([tempPotentialEndAngle, tempPotentialStartAngle])
						else:
							tempPotentialAngleRanges.append([tempPotentialStartAngle, tempPotentialEndAngle])
					
					for tempWindowAngleRange in tempWindowAngleRanges:
						tempWindowAngleRange[0]+= shiftWindowBy
						tempWindowAngleRange[1]+= shiftWindowBy
						if tempWindowAngleRange[0] < -math.pi:
							tempWindowAngleRange[0]+= math.pi*2
						elif tempWindowAngleRange[0] > math.pi:
							tempWindowAngleRange[0]-= math.pi*2
						if tempWindowAngleRange[1] < -math.pi:
							tempWindowAngleRange[1]+= math.pi*2
						elif tempWindowAngleRange[1] > math.pi:
							tempWindowAngleRange[1]-= math.pi*2
						if abs(tempWindowAngleRange[0]-math.pi)<0.0001:
							tempWindowAngleRange[0]=math.pi
						elif abs(tempWindowAngleRange[0]--math.pi)<0.0001:
							tempWindowAngleRange[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
						if abs(tempWindowAngleRange[1]-math.pi)<0.0001:
							tempWindowAngleRange[1]=math.pi
						elif abs(tempWindowAngleRange[1]--math.pi)<0.0001:
							tempWindowAngleRange[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
					# for now just take start and end of each overlap interval for each pair of segs and if the end of one is very close to the start of the next one just remove one of them so its more spaced out, define close by like one in last 5% of angle interval and other in first 5% or something
					tempOverlapRanges = []
					for pairInd in range(len(tempWindowAngleRanges)):
						if abs(tempWindowAngleRanges[pairInd][0]-tempPotentialAngleRanges[pairInd][0])<0.00001:
							tempWindowAngleRanges[pairInd][0] = tempPotentialAngleRanges[pairInd][0]
						if abs(tempWindowAngleRanges[pairInd][1]-tempPotentialAngleRanges[pairInd][1])<0.00001:
							tempWindowAngleRanges[pairInd][1] = tempPotentialAngleRanges[pairInd][1]
						if abs(tempWindowAngleRanges[pairInd][0]-tempPotentialAngleRanges[pairInd][1])<0.00001:
							tempWindowAngleRanges[pairInd][0] = tempPotentialAngleRanges[pairInd][1]
						if abs(tempWindowAngleRanges[pairInd][1]-tempPotentialAngleRanges[pairInd][0])<0.00001:
							tempWindowAngleRanges[pairInd][1] = tempPotentialAngleRanges[pairInd][0]
						
						if tempWindowAngleRanges[pairInd][0] <= tempWindowAngleRanges[pairInd][1]:
							if tempPotentialAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
								overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
								overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
								tempOverlapRanges.append([overlapStart, overlapEnd])
							else:
								if tempWindowAngleRanges[pairInd][1] >= tempPotentialAngleRanges[pairInd][0]:
									overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
									overlapEnd = tempWindowAngleRanges[pairInd][1]
									tempOverlapRanges.append([overlapStart, overlapEnd])
								elif tempWindowAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
									overlapStart = tempWindowAngleRanges[pairInd][0]
									overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
									tempOverlapRanges.append([overlapStart, overlapEnd])
								else:
									print(tempWindowAngleRanges[pairInd])
									print(tempPotentialAngleRanges[pairInd])
									
									print("hu22h?3dij3ij")
									exit()
								
						else:
							if tempPotentialAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
								if tempPotentialAngleRanges[pairInd][1] >= tempWindowAngleRanges[pairInd][0]:
									overlapStart = max(tempPotentialAngleRanges[pairInd][0], tempWindowAngleRanges[pairInd][0])
									overlapEnd = tempPotentialAngleRanges[pairInd][1]
									tempOverlapRanges.append([overlapStart, overlapEnd])
								elif tempPotentialAngleRanges[pairInd][0] <= tempWindowAngleRanges[pairInd][1]:
									overlapStart = tempPotentialAngleRanges[pairInd][0]
									overlapEnd = min(tempPotentialAngleRanges[pairInd][1], tempWindowAngleRanges[pairInd][1])
									tempOverlapRanges.append([overlapStart, overlapEnd])
								else:
									print("hu22h?yt45")
									exit()
								
							else:
								overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
								overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
								tempOverlapRanges.append([overlapStart, overlapEnd])
						
					yetAnotherTempList = []
					for pairInd in range(len(tempWindowAngleRanges)):
						
						tmptest1 = 0
						tmptest2 = 0
						tmptest3 = 0
						
						# IF ANY ANGLES ARE ABOVE 180 THEY GET NEGATED E.G. IF ANGLE IS -200 OR 200 ITLL TURN INTO 160 OR -160, HOPE THAT DOESNT MATTER
						absWindowInterval = tempWindowAngleRanges[pairInd][1]-tempWindowAngleRanges[pairInd][0]
						if absWindowInterval != 0:
							
							# if trues because copied from main function and deleted if falses, THESE ARE NOT DEBUG "if true"s
							if True: # new ASSUMING tempWindowAngleRanges[pairInd][1] IS MORE ANTICLOCKWISE THAN tempWindowAngleRanges[pairInd][0]	 !!!! (like wiggle room and stuff)
								
								if absWindowInterval < 0:
									absWindowInterval+= math.pi*2
								tmptest1=absWindowInterval
							
							ratioOverlapPoint1 = tempOverlapRanges[pairInd][0]-tempWindowAngleRanges[pairInd][0]
							
							if True:
								if ratioOverlapPoint1 < 0:
									ratioOverlapPoint1+= math.pi*2
								tmptest2=ratioOverlapPoint1
								ratioOverlapPoint1 = ratioOverlapPoint1/absWindowInterval
							
							ratioOverlapPoint2 = tempOverlapRanges[pairInd][1]-tempWindowAngleRanges[pairInd][0]
							
							if True:
								if ratioOverlapPoint2 < 0:
									ratioOverlapPoint2+= math.pi*2
								tmptest3=ratioOverlapPoint2
								ratioOverlapPoint2 = ratioOverlapPoint2/absWindowInterval
							
							overflowCheck = tempOverlapRanges[pairInd][1] - tempOverlapRanges[pairInd][0]
							
							if abs(overflowCheck) >= 0.000001 and not(tmptest1 >= tmptest3 and tmptest3 >= tmptest2 and tmptest2>=0):
								print(tmptest1)
								print(tmptest2)
								print(tmptest3)
								print(tempWindowAngleRanges[pairInd])
								# print(tempPotentialAngleRanges[pairInd])
								print(tempOverlapRanges[pairInd])
								print("22wat?deod")
								exit()
							
							if abs(overflowCheck) >= 0.000001:
								
								if abs(ratioOverlapPoint2-ratioOverlapPoint1) > 0.08: # shouldnt need abs, 2 should be >= 1
									yetAnotherTempList.append([ratioOverlapPoint1, ratioOverlapPoint2])
								else:
									yetAnotherTempList.append([ratioOverlapPoint1])
							else:
								if ratioOverlapPoint1 >= 0 and ratioOverlapPoint1 <=1:
									yetAnotherTempList.append([ratioOverlapPoint1])
								elif ratioOverlapPoint2 >= 0 and ratioOverlapPoint2 <=1:
									yetAnotherTempList.append([ratioOverlapPoint2])
						else: # use dist along line ratio instead? 
							
							yetAnotherTempList.append([0, 1])
							
					for yetAnotherTempListInd in range(len(yetAnotherTempList)-1):
						firstRatio = None
						if len(yetAnotherTempList[yetAnotherTempListInd]) > 1:
							firstRatio=yetAnotherTempList[yetAnotherTempListInd][1]
						else:
							firstRatio=yetAnotherTempList[yetAnotherTempListInd][0]
						
						secondRatio = yetAnotherTempList[yetAnotherTempListInd+1][0]
						if 1-firstRatio+secondRatio < 0.08:
							if len(yetAnotherTempList[yetAnotherTempListInd]) > 1:
								yetAnotherTempList[yetAnotherTempListInd] = [yetAnotherTempList[yetAnotherTempListInd][0]]
							else:
								yetAnotherTempList[yetAnotherTempListInd] = []
					
					ticTemp = time.perf_counter()
					
					
					for pairInd in range(len(yetAnotherTempList)): #  pairInd HERE IS PAIR OF LINESEGS NOT PAIR OF ANGLE RAY SHOOT INTERSECTIONS 
						pointPairs.append([])
						pointPairsPotential.append([])
						for endingInd in range(len(yetAnotherTempList[pairInd])): # we can only do this because we only remove 2nd point or 2nd point and 1st point so we'd never have yetAnotherTempList[i] = [ratioOverlapPoint2]
							
							pointPairs[-1].append([])
							pointPairsPotential[-1].append([])
							angleInPotentialEdge = tempOverlapRanges[pairInd][endingInd]
							angleInWindowEdge = angleInPotentialEdge-shiftWindowBy
							if angleInWindowEdge <= -math.pi:
								angleInWindowEdge+= math.pi*2
							elif angleInWindowEdge > math.pi:
								angleInWindowEdge-= math.pi*2
							if abs(angleInWindowEdge-math.pi)<0.0001:
								angleInWindowEdge=math.pi
							elif abs(angleInWindowEdge--math.pi)<0.0001:
								angleInWindowEdge=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							windowSegStartIndInContour = stepCoords1[rawDat1[window[pairInd][0]][0][0]][1]
							windowSegEndIndInContour = stepCoords1[rawDat1[window[pairInd][0]][0][1]][1]
							
							windowSegStartRatioOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][0]][4]
							windowSegEndRatioOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][1]][4]
							
							potentialSegStartIndInContour = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][0]][1]
							potentialSegEndIndInContour = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][1]][1]
							potentialSegStartRatioOnLine = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][0]][4]
							potentialSegEndRatioOnLine = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][1]][4]
							
							
							windowLineC = None
							windowLineM = None
							if abs(angleInWindowEdge) != math.pi/2:
								windowLineM = math.tan(angleInWindowEdge)
								windowLineC = seedCoord1[1]-windowLineM*seedCoord1[0]
							else:
								windowLineC = seedCoord1[0]
							
							
							if windowSegStartIndInContour == windowSegEndIndInContour: # inds like 5.1, 5.7
								idktemp(edge1, windowSegStartIndInContour, windowSegStartRatioOnLine, windowSegEndIndInContour, windowSegEndRatioOnLine, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
								
							
							else: #windowSegStartIndInContour != windowSegEndIndInContour:
								# do first and last since they usually have non-integer boundaries
								# if windowSegStartIndInContour left/right and windowSegStartIndInContour+1 right/left
								# first do firstind to firstind+1 and if intersection consider firstind+windowSegStartRatioOnLine to firstind+1
								# same but lastind lastind+1 and consider lastind to lastind+windowSegEndRatioOnLine
								
								# then iterate rest
								
								idktemp(edge1, windowSegStartIndInContour, windowSegStartRatioOnLine, 'pointless', 1, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
								
								if windowSegEndRatioOnLine != 0:
									idktemp(edge1, windowSegEndIndInContour, 0, 'pointless', windowSegEndRatioOnLine, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
								
								for remainingInd in range(windowSegStartIndInContour+1, windowSegEndIndInContour):
									idktemp(edge1, remainingInd, 0, 'pointless', 1, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
							
							potentialLineC = None
							potentialLineM = None
							if abs(angleInPotentialEdge) != math.pi/2:
								potentialLineM = math.tan(angleInPotentialEdge)
								potentialLineC = seedCoord2[1]-potentialLineM*seedCoord2[0]
							else:
								potentialLineC = seedCoord2[0]
							
							
							if potentialSegStartIndInContour == potentialSegEndIndInContour: # inds like 5.1, 5.7
								idktemp(edge2, potentialSegStartIndInContour, potentialSegStartRatioOnLine, potentialSegEndIndInContour, potentialSegEndRatioOnLine, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
								
							
							else: #windowSegStartIndInContour != windowSegEndIndInContour:
								# do first and last since they usually have non-integer boundaries
								# if windowSegStartIndInContour left/right and windowSegStartIndInContour+1 right/left
								# first do firstind to firstind+1 and if intersection consider firstind+windowSegStartRatioOnLine to firstind+1
								# same but lastind lastind+1 and consider lastind to lastind+windowSegEndRatioOnLine
								
								# then iterate rest
								
								idktemp(edge2, potentialSegStartIndInContour, potentialSegStartRatioOnLine, 'pointless', 1, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
								
								if potentialSegEndRatioOnLine != 0:
									idktemp(edge2, potentialSegEndIndInContour, 0, 'pointless', potentialSegEndRatioOnLine, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
								
								for remainingInd in range(potentialSegStartIndInContour+1, potentialSegEndIndInContour):
									idktemp(edge2, remainingInd, 0, 'pointless', 1, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
					
					
					for lineSegPairInd in range(len(pointPairs)): # moved this back 1 indent idk why it was forward
						for n in range(len(pointPairs[lineSegPairInd])): # 1 or 2 i think
							windowPts = pointPairs[lineSegPairInd][n]
							
							if len(windowPts) > 3:
								lowest = windowPts[0]
								highest = windowPts[0]
								for k in range(1, len(windowPts)):
									if windowPts[k][0] < lowest[0]:
										lowest = windowPts[k]
									elif windowPts[k][0] > highest[0]:
										highest = windowPts[k]
								middle = (lowest[0]+highest[0])/2
								middest = windowPts[0]
								currMidDiff = abs(middest[0]-middle)
								for k in range(1, len(windowPts)):
									if abs(windowPts[k][0]-middle) < currMidDiff:
										middest = windowPts[k]
										currMidDiff = abs(windowPts[k][0]-middle)
								windowPts = [lowest, middest, highest]
								pointPairs[lineSegPairInd][n] = windowPts
						# for n in range(len(pointPairsPotential[pairInd])):
							potentialPts = pointPairsPotential[lineSegPairInd][n]
							if len(potentialPts) > 3:
								lowest = potentialPts[0]
								highest = potentialPts[0]
								for k in range(1, len(potentialPts)):
									if potentialPts[k][0] < lowest[0]:
										lowest = potentialPts[k]
									elif potentialPts[k][0] > highest[0]:
										highest = potentialPts[k]
								middle = (lowest[0]+highest[0])/2
								middest = potentialPts[0]
								currMidDiff = abs(middest[0]-middle)
								for k in range(1, len(potentialPts)):
									if abs(potentialPts[k][0]-middle) < currMidDiff:
										middest = potentialPts[k]
										currMidDiff = abs(potentialPts[k][0]-middle)
								potentialPts = [lowest, middest, highest]
								pointPairsPotential[lineSegPairInd][n] = potentialPts
					
					scaleList = []
					for lineSegPairInd in range(len(pointPairs)):
						for p in range(len(pointPairs[lineSegPairInd])):
							tempList = []
							for n in range(len(pointPairs[lineSegPairInd][p])):
								for m in range(len(pointPairsPotential[lineSegPairInd][p])):
									tempRatio = pointPairs[lineSegPairInd][p][n][0]/pointPairsPotential[lineSegPairInd][p][m][0]
									# tempRatio = pointPairsPotential[pairInd][m][0]/pointPairs[pairInd][n][0]
									tempList.append([tempRatio, p, n, m, lineSegPairInd])
							tempList.sort()
							scaleList.append(tempList)
					
					bestIndsForMean = bestPtsForMean(scaleList)
					
					tocTemp = time.perf_counter()
					
					tempTimeKeep+=tocTemp-ticTemp
					tempTimeKeepAmount+=1
					
					if bestIndsForMean is not None and len(bestIndsForMean)>0:
						# remove worst X amount of outliers
						totalPts = 0
						for ind in bestIndsForMean:
							if ind != -1:
								totalPts+=1
						
						removeWorstN = 1 + max(0, math.floor((totalPts-len(window))/3))
						for loops in range(removeWorstN):
							tempMean = 0
							for ind, val in enumerate(bestIndsForMean):
								if val != -1:
									tempMean+=scaleList[ind][val][0]
							tempMean = tempMean/totalPts
							
							mostOutlyingOutlier = 0
							amountOfOutlying = 0
							for ind, val in enumerate(bestIndsForMean):
								if val != -1:
									tempOutlying = abs(tempMean-scaleList[ind][val][0])
									if tempOutlying > amountOfOutlying:
										amountOfOutlying = tempOutlying
										mostOutlyingOutlier = ind
							bestIndsForMean[mostOutlyingOutlier] = -1
							totalPts-=1
						
						finalVariance = 0
						finalMean = 0
						for ind, val in enumerate(bestIndsForMean):
							if val != -1:
								finalMean+=scaleList[ind][val][0]
								
						finalMean = finalMean/totalPts
						for ind, val in enumerate(bestIndsForMean):
							if val != -1:
								finalVariance+=(finalMean-scaleList[ind][val][0])**2
						finalVariance = finalVariance/totalPts
						finalVariance = finalVariance/(finalMean)**2
						
						impliedScale = finalMean # just for readability
						
						### new, not sure why i used minScale and maxScale when that can give vastly different abs dists depending on the dist from seed, 50% scale error close to seed could be very accurate
						
						scaleQueryOverWindow = 1/impliedScale
						maxAbsDistToCountAsMatch=float('-inf')
						for ind, val in enumerate(bestIndsForMean):
							if val != -1:
								distFromSeedQueryPoint = pointPairsPotential[scaleList[ind][val][4]][scaleList[ind][val][1]][scaleList[ind][val][3]][0]
								distFromSeedWindowPointInQuerySpace = scaleQueryOverWindow*pointPairs[scaleList[ind][val][4]][scaleList[ind][val][1]][scaleList[ind][val][2]][0]
								absDistQuerySpace = abs(distFromSeedWindowPointInQuerySpace-distFromSeedQueryPoint)
								if absDistQuerySpace > maxAbsDistToCountAsMatch:
									maxAbsDistToCountAsMatch=absDistQuerySpace
								
						###
						maxAbsDistToCountAsMatch+=params["maxAbsDistToCountAsMatchPixelError"]
						
						meanAbsDistDiff = 0
						
						tempRatio = 1/impliedScale
						
						minimumStepsAroundSeedMatch = params['minimumStepsAroundSeedMatch']
						# tempRatio = 1/impliedScale
						
						checkArcLengthStepsAroundSeedRadius = params['checkArcLengthStepsAroundSeedRadius']
						
						# just check stepcoords and like 3-5 indices evenly spaced within stepcoord subareas for now			@@@@@@@@@@@@@
						
						checkPtsBetweenStepCoordsAmt = params['checkPtsBetweenStepCoordsAmt'] # 3 for now so 5 total each subarea (endings shared though)
						
						sinP1 = math.sin(shiftWindowBy)
						cosP1 = math.cos(shiftWindowBy)
						# rotatedPt1 = [windowP1[0]*cosP1 - windowP1[1]*sinP1, windowP1[0]*sinP1 + windowP1[1]*cosP1]
						
						totalSuccessfulPtsAroundSeed = 0
						
						lastClosestInd = 0 # the closest point inds should always be monotone increasing if stepCoords are increasing and vice versa so both edges should both increase/decrease closest point pairs inds
						stepCoordIndBeforeLastClosestInd = edge2SeedIsAfterStepCoordIndN
						amtWithoutFailuresAfter = 0
						failureAmtAfter = 0
						lastClosestPoint = None
						firstTest = True
						# after
						for ind in range(min(edge1SeedIsAfterStepCoordIndN+1, len(stepCoords1)-1), min(edge1SeedIsAfterStepCoordIndN+1+checkArcLengthStepsAroundSeedRadius, len(stepCoords1)-1)): # for each subarea defined by 2 consecutive seedcoords
							if yesPrint:
								print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2222222222")
							testCoord = copy.deepcopy(stepCoords1[ind][0]) # .copy not needed
							testCoord = [testCoord[0] - seedCoord1[0], testCoord[1] - seedCoord1[1]]
							testCoord = [testCoord[0]*cosP1 - testCoord[1]*sinP1, testCoord[0]*sinP1 + testCoord[1]*cosP1]
							testCoord = [testCoord[0]*tempRatio, testCoord[1]*tempRatio]
							testCoord[0]+=seedCoord2[0]
							testCoord[1]+=seedCoord2[1]
							
							
							# indsWithoutCloser = 0
							tempIndClosestDist = None
							tempClosestPoint = None
							tempClosestDist = float('inf')
							tempStepCoordIndBeforeClosestDist = None
							# tempLastClosestInd = lastClosestInd
							startStepCoordIndInEdge2 = stepCoordIndBeforeLastClosestInd+1 # -1 below because the iterations between start and end, define the start of the subarea, and the end of the subare will be startind+1
							endStepCoordIndInEdge2 = min(startStepCoordIndInEdge2 + 2*windowAmount, len(stepCoords2)-1) - 1 # will add 1 to each to get start and end, terrible arbitrary choice but its hopefully temp compromise between exhaustive checking and accidentally skipping over closest pts
							for stepInd in range(startStepCoordIndInEdge2, endStepCoordIndInEdge2+1): # +1 -1 for readability  ## preliminary scan checking dist to each stepcoord as well as ~3 pts evenly spaced within subareas defined by stepcoords
								startInd = stepCoords2[stepInd][1]+1
								endInd = stepCoords2[stepInd+1][1]
								if startInd < lastClosestInd:
									# if lastC
									startInd = math.floor(lastClosestInd) # since startInd is already the first integer index AFTER the beginning of the subarea, floor covers all remaining cases
								sampleStep = max(1, math.floor((endInd-startInd)/(checkPtsBetweenStepCoordsAmt+2))) # +2 to account for stepcoord endings
								for cntr in range(1, min(endInd-startInd, checkPtsBetweenStepCoordsAmt+1)):
									mostTempInd = startInd+cntr*sampleStep
									mostTempCoord = edge2[mostTempInd][0]
									mostTempDist = getDistance(mostTempCoord[0], testCoord[0], mostTempCoord[1], testCoord[1])
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd
										tempIndClosestDist = mostTempInd
										tempClosestPoint = mostTempCoord
								mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd][0][0], testCoord[1], stepCoords2[stepInd][0][1]) # stepcoord ending 1 aka the start of the subarea
								if mostTempDist < tempClosestDist:
									tempClosestDist = mostTempDist
									tempStepCoordIndBeforeClosestDist = stepInd
									tempIndClosestDist = stepCoords2[stepInd][1] + stepCoords2[stepInd][4] # 
									tempClosestPoint = stepCoords2[stepInd][0]
								mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd+1][0][0], testCoord[1], stepCoords2[stepInd+1][0][1]) # stepcoord ending 2 aka the end of the subarea
								if mostTempDist < tempClosestDist:
									tempClosestDist = mostTempDist
									tempStepCoordIndBeforeClosestDist = stepInd
									tempIndClosestDist = stepCoords2[stepInd+1][1] + stepCoords2[stepInd+1][4] # 
									tempClosestPoint = stepCoords2[stepInd+1][0]
							
							# now check every contour point within the subarea that contained the closest point in preliminary check
							if tempStepCoordIndBeforeClosestDist is not None: # should never be none anyway
								# for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1], min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1]+2, edge2.shape[0])): # guess im just checking the point before the first stepcoord at floor(stepcoordind) and ceil of the stepcoordind for the ending anyway so dont need to be particular about checking all whole integer indices strictly between stepcoords and the stepcoords themselves as float indices
								for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1]+1, min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1] + 1, edge2.shape[0])):
									mostTempDist = getDistance(edge2[tempInd][0][0], testCoord[0], edge2[tempInd][0][1], testCoord[1])
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempIndClosestDist = tempInd
										tempClosestPoint = edge2[tempInd][0]
										
							# finally do the check for if closest dist is actually at that coord or if its on line between that and prevcoord or nextcoord
							# then set lastClosestInd and stuff
							if tempIndClosestDist is not None:
								if tempIndClosestDist % 1 == 0:
									absoluteTempIndClosestDist = tempIndClosestDist
									if tempIndClosestDist>0:
										ratioOnLine, closePt = closestPt([edge2[tempIndClosestDist-1][0], edge2[tempIndClosestDist][0]], testCoord)
										mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = tempIndClosestDist-1 + ratioOnLine
											tempClosestPoint = closePt
									if absoluteTempIndClosestDist < edge2.shape[0]-1:
										ratioOnLine, closePt = closestPt([edge2[absoluteTempIndClosestDist][0], edge2[absoluteTempIndClosestDist+1][0]], testCoord)
										mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = absoluteTempIndClosestDist + ratioOnLine
											tempClosestPoint = closePt
							
							withinMatchRange = False
							
							if yesPrint:
								print('#######################e3ee3#####################################')
								print(tempClosestDist)
								print(maxAbsDistToCountAsMatch)
								print(lastClosestPoint)
								print(tempClosestPoint)
							# print(maxAbsDistToCountAsMatch)
							# print("di388")
							if tempClosestDist <= maxAbsDistToCountAsMatch:
								withinMatchRange = True
							
							
							if (lastClosestPoint is None and not(firstTest)) or tempClosestPoint is None or ((lastClosestPoint is not None and tempClosestPoint is not None) and tempClosestPoint[0] == lastClosestPoint[0] and tempClosestPoint[1] == lastClosestPoint[1]) or not(withinMatchRange):
								failureAmtAfter+=1
							else:
								amtWithoutFailuresAfter+=1
							if failureAmtAfter>=2 and failureAmtAfter/(failureAmtAfter+amtWithoutFailuresAfter) > 0.5: # if decent amount has been tested and the failure rate is over half (if half and half we err to side of assuming matching zone cause its around seed)
								break
							
							lastClosestPoint = tempClosestPoint
							lastClosestInd = tempIndClosestDist
							stepCoordIndBeforeLastClosestInd = tempStepCoordIndBeforeClosestDist
							firstTest=False
							# ... loop stuff that i never added the first time
							
						
						######### PASTING ABOVE LOOPS AND CHANGING TO CALC STUFF BEFORE RATHER THAN AFTER
						########
						
						lastClosestInd = float('inf') # the closest point inds should always be monotone increasing if stepCoords are increasing and vice versa so both edges should both increase/decrease closest point pairs inds
						stepCoordIndBeforeLastClosestInd = edge2SeedIsAfterStepCoordIndN
						amtWithoutFailuresBefore = 0
						failureAmtBefore = 0
						lastClosestPoint = None
						firstTest=True
						# before..
						
						for ind in range(edge1SeedIsAfterStepCoordIndN, max(edge1SeedIsAfterStepCoordIndN-checkArcLengthStepsAroundSeedRadius-1, 0), -1): # for each subarea defined by 2 consecutive seedcoords
							if yesPrint:
								print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@111111111")
							testCoord = copy.deepcopy(stepCoords1[ind][0]) # not needed (copy part)
							testCoord = [testCoord[0] - seedCoord1[0], testCoord[1] - seedCoord1[1]]
							testCoord = [testCoord[0]*cosP1 - testCoord[1]*sinP1, testCoord[0]*sinP1 + testCoord[1]*cosP1]
							testCoord = [testCoord[0]*tempRatio, testCoord[1]*tempRatio]
							testCoord[0]+=seedCoord2[0]
							testCoord[1]+=seedCoord2[1]
							
							# indsWithoutCloser = 0
							tempIndClosestDist = None
							tempClosestPoint = None
							tempClosestDist = float('inf')
							tempStepCoordIndBeforeClosestDist = None
							# tempLastClosestInd = lastClosestInd
							startStepCoordIndInEdge2 = stepCoordIndBeforeLastClosestInd # # start and end here (to be more intuitive) is goin backwards from the seed
							endStepCoordIndInEdge2 = max(startStepCoordIndInEdge2 - 2*windowAmount, 0) + 1 # will add 1 to each to get start and end, terrible arbitrary choice but its hopefully temp compromise between exhaustive checking and accidentally skipping over closest pts
							for stepInd in range(startStepCoordIndInEdge2, endStepCoordIndInEdge2-1, -1): # This part will also be step -1 whereas the actual test within each subarea will be forwards normal step					 ##### +1 -1 for readability  ## preliminary scan checking dist to each stepcoord as well as ~3 pts evenly spaced within subareas defined by stepcoords
								# startInd = stepCoords2[stepInd][1]+1
								# endInd = stepCoords2[stepInd+1][1]
								startInd = stepCoords2[stepInd-1][1]+1 # start and end here must be increasing, like the natural order of the contour
								endInd = stepCoords2[stepInd][1]
								if endInd > lastClosestInd:
									# if lastC
									endInd = math.ceil(lastClosestInd) # since endInd is already the first integer index BEFORE the ending of the subarea, ceil covers all remaining cases
								sampleStep = max(1, math.floor((endInd-startInd)/(checkPtsBetweenStepCoordsAmt+2))) # +2 to account for stepcoord endings
								for cntr in range(1, min(endInd-startInd, checkPtsBetweenStepCoordsAmt+1)):
									mostTempInd = startInd+cntr*sampleStep
									mostTempCoord = copy.deepcopy(edge2[mostTempInd][0])
									mostTempDist = getDistance(mostTempCoord[0], testCoord[0], mostTempCoord[1], testCoord[1])
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd-1 # -1 because due to reversal 
										tempIndClosestDist = mostTempInd
										tempClosestPoint = copy.deepcopy(mostTempCoord)
								mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd][0][0], testCoord[1], stepCoords2[stepInd][0][1]) # stepcoord ending 2 aka the end of the subarea
								if mostTempDist < tempClosestDist:
									tempClosestDist = mostTempDist
									tempStepCoordIndBeforeClosestDist = stepInd-1
									tempIndClosestDist = stepCoords2[stepInd][1] + stepCoords2[stepInd][4] # 
									tempClosestPoint = copy.deepcopy(stepCoords2[stepInd][0])
								mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd-1][0][0], testCoord[1], stepCoords2[stepInd-1][0][1]) # stepcoord ending 1 aka the start of the subarea
								if mostTempDist < tempClosestDist:
									tempClosestDist = mostTempDist
									tempStepCoordIndBeforeClosestDist = stepInd-1
									tempIndClosestDist = stepCoords2[stepInd-1][1] + stepCoords2[stepInd-1][4] # 
									tempClosestPoint = copy.deepcopy(stepCoords2[stepInd-1][0])
							
							
							# @@@@@@@@@@@@@@@@@ HERE @@@@@@@@@@@@@@
							
							# now check every contour point within the subarea that contained the closest point in preliminary check
							if tempStepCoordIndBeforeClosestDist is not None: # should never be none anyway
								# for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1], min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1]+2, edge2.shape[0])): # guess im just checking the point before the first stepcoord at floor(stepcoordind) and ceil of the stepcoordind for the ending anyway so dont need to be particular about checking all whole integer indices strictly between stepcoords and the stepcoords themselves as float indices
								for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1]+1, min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1] + 1, edge2.shape[0])): # dont see why i put min here but not removing for now even though its definitely pointless
									mostTempDist = getDistance(edge2[tempInd][0][0], testCoord[0], edge2[tempInd][0][1], testCoord[1])
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempIndClosestDist = tempInd
										tempClosestPoint = copy.deepcopy(edge2[tempInd][0])
										
							# finally do the check for if closest dist is actually at that coord or if its on line between that and prevcoord or nextcoord
							# then set lastClosestInd and stuff
							if tempIndClosestDist is not None:
								if tempIndClosestDist % 1 == 0:
									if tempIndClosestDist>0:
										ratioOnLine, closePt = closestPt([edge2[int(tempIndClosestDist)-1][0], edge2[int(tempIndClosestDist)][0]], testCoord)
										mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1]) # shouldnt i just check if ratioOnLine is not 0 or 1 or whatever????? @@@@@@@@@@@@@
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = tempIndClosestDist-1 + ratioOnLine
											tempClosestPoint = copy.deepcopy(closePt)
									if tempIndClosestDist < edge2.shape[0]-1:
										ratioOnLine, closePt = closestPt([edge2[int(tempIndClosestDist)][0], edge2[int(tempIndClosestDist)+1][0]], testCoord)
										mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = tempIndClosestDist + ratioOnLine
											tempClosestPoint = copy.deepcopy(closePt)
							
							withinMatchRange = False
							
							if tempClosestDist <= maxAbsDistToCountAsMatch:
								withinMatchRange = True
							
							if yesPrint:
								print('###################################################################################')
								print(tempClosestDist)
								print(maxAbsDistToCountAsMatch)
								print(lastClosestPoint)
								print(tempClosestPoint)
							
							
							
							
							if (lastClosestPoint is None and not(firstTest)) or tempClosestPoint is None or ((lastClosestPoint is not None and tempClosestPoint is not None) and tempClosestPoint[0] == lastClosestPoint[0] and tempClosestPoint[1] == lastClosestPoint[1]) or not(withinMatchRange):
								failureAmtBefore+=1
							else:
								amtWithoutFailuresBefore+=1
							if failureAmtBefore>=2 and failureAmtBefore/(failureAmtBefore+amtWithoutFailuresBefore) > 0.5: # if decent amount has been tested and the failure rate is over half (if half and half we err to side of assuming matching zone cause its around seed)
								break
							
							lastClosestPoint = copy.deepcopy(tempClosestPoint)
							lastClosestInd = tempIndClosestDist
							stepCoordIndBeforeLastClosestInd = tempStepCoordIndBeforeClosestDist
							firstTest=False
							# ... loop stuff that i never added the first time
							
						if yesPrint:
							print("amtwithoutfailafter, before, minstepsaround: ")
							print(amtWithoutFailuresAfter)
							print(amtWithoutFailuresBefore)
							print(minimumStepsAroundSeedMatch)
						if amtWithoutFailuresAfter + amtWithoutFailuresBefore < minimumStepsAroundSeedMatch:
							# return
							pass
						else:
						# windowMatches.append([finalVariance, shiftWindowBy, impliedScale]) # whatever other data i will need, maybe totalPts to give more weight to low variance high amount of pts? or just the data for point pairs? or is that even needed? maybe just need implied orientation, scale and seedcoord?
							if True:
								
								reqDatd = []
								
								# wiggle=None
								pseudoTreeRootd = currentBranchOfChainDatTree[3]
								tmpBranchd = pseudoTreeRootd
								for listIndd, tmpId in enumerate(finalChain):
									# if need any other data get it, for now just need last link in chain for wiggle
									
									tmpWiggle = tmpBranchd[tmpId][1]
									reqDatd.append(tmpWiggle) # list in case I need to add more data
									if listIndd != len(finalChain)-1:
										tmpBranchd = tmpBranchd[tmpId][3]
									else:
										tmpBranchd = tmpBranchd[tmpId]
								
								# wiggled = tmpBranchd[1]
								
								
								tmpbeugg = []
								for trackerInd in range(len(trackerList)):
									tmpbeugg.append((window[trackerInd][0], compatibleLists[trackerInd][trackerList[trackerInd]][0]))
								windowMatches.append([finalVariance, shiftWindowBy, 1/impliedScale, maxAbsDistToCountAsMatch, tmpbeugg, reqDatd]) # hopefully last part is right, assuming maxAbsDistToCountAsMatch is in window space
								windowMatchesAmount+=1
							else:
								windowMatches.append([finalVariance, shiftWindowBy, 1/impliedScale, maxAbsDistToCountAsMatch])
								windowMatchesAmount+=1
							
							# windowMatches.append([finalVariance, shiftWindowBy, 1/impliedScale, maxAbsDistToCountAsMatch]) # hopefully last part is right, assuming maxAbsDistToCountAsMatch is in window space
							# print("?????<<<<<?>>?>?")
					
					
					toc = time.perf_counter()
					
					totalTimeLastSectionOfSimilarityInstance += toc-tic # use these 2 to calc average
					amountLastSectionOfSimilarityInstance += 1
					
				for tmpI in range(currWindowInd, len(window)): # len(window)==windowAmount
					compatibleLists[tmpI]=[]
					trackerList[tmpI]=0
				
				#######################################################################################
				
				wiggleConstraints[currWindowInd-1]=None # should already be this
				###
				trackerList[currWindowInd-1] -= 1
				currBranchOfChainDatTreeIndexList.pop(-1) # dont need to be in branch for left pair anymore since we've exhausted all possible chains starting from the right window wild card given the left pair and constraints up to left pair
				
				return True
	
	return False


def angleIntervalIntersection(interval1, interval2):
	if interval1[0] <= -math.pi:
		interval1[0]+= math.pi*2
	elif interval1[0] > math.pi:
		interval1[0]-= math.pi*2
	if interval1[1] <= -math.pi:
		interval1[1]+= math.pi*2
	elif interval1[1] > math.pi:
		interval1[1]-= math.pi*2
	if interval2[0] <= -math.pi:
		interval2[0]+= math.pi*2
	elif interval2[0] > math.pi:
		interval2[0]-= math.pi*2
	if interval2[1] <= -math.pi:
		interval2[1]+= math.pi*2
	elif interval2[1] > math.pi:
		interval2[1]-= math.pi*2
	if abs(interval1[0]-math.pi)<0.0001:
		interval1[0]=math.pi
	elif abs(interval1[0]--math.pi)<0.0001:
		interval1[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	if abs(interval1[1]-math.pi)<0.0001:
		interval1[1]=math.pi
	elif abs(interval1[1]--math.pi)<0.0001:
		interval1[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	if abs(interval2[0]-math.pi)<0.0001:
		interval2[0]=math.pi
	elif abs(interval2[0]--math.pi)<0.0001:
		interval2[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	if abs(interval2[1]-math.pi)<0.0001:
		interval2[1]=math.pi
	elif abs(interval2[1]--math.pi)<0.0001:
		interval2[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	intersection = []
	
	skipThisSchema=False
	if interval1[0] <= interval1[1]: # intuitive
		if interval2[0] <= interval2[1]:
			# if tempWiggle[0] > wiggle[1] or tempWiggle[1] < wiggle[0]:
				# skipThisSchema=True
			# else:
			wiggleStart = max(interval2[0], interval1[0])
			wiggleEnd = min(interval2[1], interval1[1])
			if wiggleStart>wiggleEnd:
				skipThisSchema=True
			else:
				intersection = [wiggleStart, wiggleEnd]
		else:
			if interval1[1] >= interval2[0]:# or tempWiggle[1] <= wiggle[1]:
				wiggleStart = max(interval1[0], interval2[0])
				wiggleEnd = interval1[1]
				intersection = [wiggleStart, wiggleEnd] # tempWiggle.copy() # tempwiggle is a subset of wiggle
			elif interval1[0] <= interval2[1]: #tempWiggle[1] < wiggle[0] and tempWiggle[0] > wiggle[1]:
				# skipThisSchema = True
				wiggleStart = interval1[0]
				wiggleEnd = min(interval1[1], interval2[1])
				intersection = [wiggleStart, wiggleEnd]
			else:
				
				skipThisSchema = True
	else:
		if interval2[0] <= interval2[1]:
			if interval2[1]>=interval1[0]:
				wiggleStart = max(interval2[0], interval1[0])
				wiggleEnd = interval2[1]
				intersection = [wiggleStart, wiggleEnd]
			
			elif interval2[0] <= interval1[1]:
				wiggleStart = interval2[0]
				wiggleEnd = min(interval2[1], interval1[1])
				intersection = [wiggleStart, wiggleEnd]
			else:# tempWiggle[0] > wiggle[0] and tempWiggle[0] <= wiggle[1]:
				skipThisSchema = True
		else:
			# both cross 0 so will always have some overlap
			wiggleStart = max(interval2[0], interval1[0])
			wiggleEnd = min(interval2[1], interval1[1])
			# if :
				# skipThisSchema=True
			# else:
			intersection = [wiggleStart, wiggleEnd]
	
	if skipThisSchema:
		return False, []
	
	interval1SubsetOfInterval2 = False
	if interval1[0] == intersection[0] and interval1[1] == intersection[1]:
		interval1SubsetOfInterval2 = True
	
	return interval1SubsetOfInterval2, intersection
	


def similarityInstance(seedCoord1, seedCoord2, staticData1, staticData2, angleWiggleRoom, orientationWiggleRoom, windowAmount, stepCoords1, rawDat1, stepCoords2, rawDat2, stepLength1, stepLength2, estimatedScale, edge1PixelationError, edge2PixelationError, edge1SeedIsAfterStepCoordIndN, edge2SeedCntIndDat, edge2SeedIsAfterStepCoordIndN, edge1, edge2, params, non=None):
	# angleWiggleRoom: [a, b] angles from x axis where 'b' is more counter clockwise than 'a' so in most cases a<b and usually a = -b e.g. [-45 deg, +45 deg], so as with wiggleConstraints we can just add 'a' or 'b' to the angle of a point to get the angular range of the point
	# params['orientationError'] 5*math.pi/180 or so maybe 10 deg instead idk
	# estimatedScale edge1/edge2
	# stepLengthRatio = stepLength1/stepLength2 # for readability to be consistent with other ratios
	# stepLengthRatio = 1/stepLengthRatio # for readability to be consistent with other ratios
	
	global similarityInstanceCall
	global windowSlide
	global allWhileLoopChains
	global allChainsAtLeastSize2
	global allChainsAtLeastSize3
	global allChainsAtLeastSize4
	global allChainsAtLeastSize5
	global allChainsAtLeastSize6
	global totalTimeSimilarityInstanceCall
	global amountSimilarityInstanceCall
	global totalTimeLastSectionOfSimilarityInstance
	global amountLastSectionOfSimilarityInstance
	global allChainsAtLeastSize1
	
	global tempTimeKeep
	global tempTimeKeepAmount
	
	global tmpppp22
	global tmpdebug1
	global tmpdebug2
	global tmpdebug3
	global tmpdebug4
	global tmpdebug5
	global tmpdebuglist
	global yesPrint
	global debuggingAnnulusIntersection
	# global timesPastWiggleLen2
	global windowMatchesGlobalTracker
	global exitlater
	global windowMatchesAmount
	duplicateSchemaCache = {}
	
	tmpppp22+=1
	if yesPrint:
		for i in range(3):
			print(tmpppp22)
		print(tmpppp22)
	
	
	allDebugs = False
	# if tmpppp22>=7:
		# allDebugs = True
	
	windowTempClockwiseCheckCache={}
	angleSideWindowCache={}
	window = []
	# for i in range(windowAmount):
	for i in range(len(rawDat1)-windowAmount, len(rawDat1)):
		# debug sanity check
		# if rawDat1[i][0] != i:
			# print('dpokwd')
			# exit()
		tempList = [i, rawDat1[i][1]] # rawDatInd, orientation
		
		# since rawDat is ordered we can just do i, i+1 in stepCoords instead of rawDat[i][0][0], [i][0][1]
		tempAngleStart = math.atan2(stepCoords1[i][0][1]-seedCoord1[1], stepCoords1[i][0][0]-seedCoord1[0])
		tempAngleEnd = math.atan2(stepCoords1[i+1][0][1]-seedCoord1[1], stepCoords1[i+1][0][0]-seedCoord1[0]) # window will never be same size as whole edge so dont need % or anything
		tempList.append([tempAngleStart, tempAngleEnd])
		
		tempDistStart = getDistance(seedCoord1[0], stepCoords1[i][0][0], seedCoord1[1], stepCoords1[i][0][1])
		tempDistEnd = getDistance(seedCoord1[0], stepCoords1[i+1][0][0], seedCoord1[1], stepCoords1[i+1][0][1])
		tempList.append([tempDistStart, tempDistEnd])
		
		tempClockwiseCheck = tempList[1] - tempAngleStart
		while tempClockwiseCheck <= -math.pi:
			tempClockwiseCheck+= math.pi*2
		while tempClockwiseCheck > math.pi:
			tempClockwiseCheck-= math.pi*2
		if abs(tempClockwiseCheck-math.pi)<0.0001:
			tempClockwiseCheck=math.pi
		elif abs(tempClockwiseCheck--math.pi)<0.0001:
			tempClockwiseCheck=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
		
		if tempClockwiseCheck > 0:
			tempList.append(False)
			windowTempClockwiseCheckCache[i]=False
		# elif tempClockwiseCheck < 0:
		elif tempClockwiseCheck <= 0:
			tempList.append(True)
			windowTempClockwiseCheckCache[i]=True
		
		angleSideWindowCache[i]=(tempAngleStart, tempAngleEnd)
		
		window.append(tempList)
		# windowTempClockwiseCheckCache[i]=
	
	potentialCache = {} # keys: rawdatind2, items: [potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise]
	
	
	limitWiggleRoomCalcCaches = []
	for j in range(len(window)):
		# limitWiggleRoomCalcCaches.append([window[j][0], {}])
		limitWiggleRoomCalcCaches.append([window[j][0], {}])
	# limitWiggleRoomCalcCaches.append([None, {}]) # dummy entry, wont be used, could technically put window[-1][0]+1 but doesn't matter
	windowSegWildCardTreeCaches = []
	for j in range(1, len(window)):
		# windowSegWildCardTreeCaches.append([window[j][0], []])
		windowSegWildCardTreeCaches.append([window[j][0], []])
	windowSegWildCardTreeCaches.append([None, []]) # same as above
	# currentBranchOfChainDatTree
	
	minimumIndex = 0
	
	windowMatchesDebugLenList=[]
	
	allWindowDat = []
	# print(len(rawDat1))
	# print(len(stepCoords1))
	# exit()
	# for i in range(windowAmount, len(rawDat1) + 1): # +1 at end because theres a lag of 1 step due to window so last iteration will be too large, very scuffed and tired implementation
	for i in range(len(rawDat1)-windowAmount-1, -1, -1):
		# print(i)
		# print(i)
		# print(i)
		
		windowSlide+=1
		
		currentChainDatTree = []
		currentBranchOfChainDatTree = currentChainDatTree # idk if this should be here or at start of while loop, maybe here if I initialise currentChainDatTree to have 1 entry for first compatibleLists[0] item? idk
		currBranchOfChainDatTreeIndexList = []
		
		compatibleLists = []
		for j in range(len(window)):
			compatibleLists.append([])
		
		wiggleConstraints = []
		for j in range(len(window)):
			wiggleConstraints.append(None)
		# annulusDist1 = scaledDist1*(1-params['scaleEstimationError'])
		subAreaTracker = 0
		# midCoord = stepCoords1[rawDat1[window[-1][0]][0][0]][0]
						# lastCoord = stepCoords1[rawDat1[window[-1][0]][0][1]][0]
		
		tempWindowP1 = None
		tempWindowP2 = None
		angleSide1 = None
		angleSide2 = None
		if window[subAreaTracker][4]:
			tempWindowP1 = stepCoords1[rawDat1[window[subAreaTracker][0]][0][0]][0]
			tempWindowP2 = stepCoords1[rawDat1[window[subAreaTracker][0]][0][1]][0]
			angleSide1 = window[subAreaTracker][2][0]
			angleSide2 = window[subAreaTracker][2][1]
		else:
			tempWindowP1 = stepCoords1[rawDat1[window[subAreaTracker][0]][0][1]][0]
			tempWindowP2 = stepCoords1[rawDat1[window[subAreaTracker][0]][0][0]][0]
			angleSide1 = window[subAreaTracker][2][1]
			angleSide2 = window[subAreaTracker][2][0]
		# estimatedScale
		firstLinearTransformedAnnulusSectorDat = constructLinearTransformedAnnulusSectorDat(estimatedScale, params, tempWindowP1, tempWindowP2, seedCoord1, edge1PixelationError, edge2PixelationError, angleSide1, angleSide2, angleWiggleRoom, seedCoord2)
		minimumIndex = 0 # for first search the subareas can be placed anywhere but subsequent ones must come after the previous one
		tempOrientation = window[subAreaTracker][1]
		if tempOrientation < 0:
			tempOrientation+=math.pi*2
		orientationRange = [tempOrientation-params['orientationError'], tempOrientation+params['orientationError']]
		orientationRange = [orientationRange[0]+angleWiggleRoom[0], orientationRange[1]+angleWiggleRoom[1]]
		if orientationRange[1]-orientationRange[0] >= 2*math.pi:
			orientationRange = [0, 2*math.pi]
		else:
			while orientationRange[0] < 0:
				orientationRange[0]+=math.pi*2
			while orientationRange[0] >= math.pi*2:
				orientationRange[0]-=math.pi*2
			while orientationRange[1] <= 0:
				orientationRange[1]+=math.pi*2
			while orientationRange[1] > math.pi*2:
				orientationRange[1]-=math.pi*2
			if abs(orientationRange[0]-math.pi)<0.0001:
				orientationRange[0]=math.pi
			elif abs(orientationRange[0]--math.pi)<0.0001:
				orientationRange[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
			if abs(orientationRange[1]-math.pi)<0.0001:
				orientationRange[1]=math.pi
			elif abs(orientationRange[1]--math.pi)<0.0001:
				orientationRange[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

		partitionId1 = int(math.floor(orientationRange[0]/params['segOrientationPartitionSize']))
		partitionId2 = int(math.floor(orientationRange[1]/params['segOrientationPartitionSize']))
		tempCompatible = []
		if partitionId1 <= partitionId2:
			for ind in range(partitionId1, partitionId2+1):
				if debuggingAnnulusIntersection:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=angleWiggleRoom, window=window, currWindowInd=subAreaTracker)
				else:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
		else:
			for ind in range(partitionId1, params['segOrientationPartitionAmt']):
				if debuggingAnnulusIntersection:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=angleWiggleRoom, window=window, currWindowInd=subAreaTracker)
				else:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
			for ind in range(0, partitionId2+1):
				if debuggingAnnulusIntersection:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=angleWiggleRoom, window=window, currWindowInd=subAreaTracker)
				else:
					tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, firstLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
		compatibleLists[0] = tempCompatible
		
		allChainsAtLeastSize1+=len(compatibleLists[0])
		
		# print(firstLinearTransformedAnnulusSectorDat)
		# print(partitionId1)
		# print(partitionId2)
		# print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		# print(tempCompatible)
		# print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		# mainTracker = len(compatibleLists[0])-1
		
		# subAreaPotentialMatchTracker = 0
		upOrDown = True # True is up, swap to down if intersections/tree stuff comes back empty or subareaTracker == len(window)-1 and subareaPotentialMatchTracker < 0 or whatever signifies us exhausting compatibleLists[len(window)-1]
		# upOrDown needs to bounce a lot, it should cause subareaTracker to bounce something like 0 -> 1 -> .. -> 5 -> 4 - > 5 - > ... - > 5 - > 4 - > 3 - > 4 - > 5 - > ... - > 1 - > 0 done
		
		trackerList = []
		for j in range(len(window)):
			trackerList.append(0)
		trackerList[0] = len(compatibleLists[0])-1
		
		windowMatches = []
		
		bestWindowMatch = [] # [score, either full data amount paired pts found through ray stabbing OR just the implications of this e.g. implied scale and orientation and stuff probably the latter]
		
		currentWiggleRoom = [0, 0] # APPLIED TO WINDOW, NOT QUERY SUBAREAS
		
		while trackerList[0] >= 0: # and..? or is that enough?
			# miniCacheSkipHappened=False
			# print(trackerList[0])
			# print("===================================================================================")
			# print(wiggleConstraints)
			allWhileLoopChains+=1
			
			currentBranchOfChainDatTree = currentChainDatTree
			for listInd, tmpI in enumerate(currBranchOfChainDatTreeIndexList):
				if listInd == len(currBranchOfChainDatTreeIndexList)-1:
					currentBranchOfChainDatTree = currentBranchOfChainDatTree[tmpI]
				else:
					currentBranchOfChainDatTree = currentBranchOfChainDatTree[tmpI][3]
			
			if subAreaTracker < len(window)-1:
				tmpdebug1+=1
				if trackerList[subAreaTracker] < 0:
					###(new)
					wiggleConstraints[subAreaTracker]=None
					compatibleLists[subAreaTracker]=[]
					###
					subAreaTracker-=1
					trackerList[subAreaTracker]-=1
					
					currBranchOfChainDatTreeIndexList.pop(-1) # just putting this whenever subAreaTracker-=1, hopefully it's right 
					
				else:
					
					if subAreaTracker == 0:
						
						print(subAreaTracker)
						print(compatibleLists[subAreaTracker][trackerList[subAreaTracker]])
						if yesPrint:
							print("3333333333333333333333333333333333333333333333")
						if debuggingAnnulusIntersection:
							tempWiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=compatibleLists[subAreaTracker][trackerList[subAreaTracker]][2])
						else:
							tempWiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=angleWiggleRoom)
						if len(tempWiggle)>0 and (tempWiggle[0] < -math.pi or tempWiggle[0] > math.pi or tempWiggle[1] < -math.pi or tempWiggle[1] > math.pi):
							print("@@@@@@@@dddddrrrrrrrrr@@@@5435435@@@@@@@@")
							exit()
						
						if len(tempWiggle) ==2:
							wiggleConstraints[subAreaTracker] = [tempWiggle[0], tempWiggle[1]]
						else:
							wiggleConstraints[subAreaTracker] = None
						
					else: # above and this is when compatibleLists has already been queried for and we're checking pairs so just do limitWiggleRoom fast attempt
						if yesPrint:
							print("YES WE INDEED MADE IT HERE WHICH MEANS LIMITWIGGLEROOM IS FAILING")
						# currWindowInd = subAreaTracker
						# print(trackerList)
						# tempTEST = []
						# for tempTEST2 in compatibleLists:
							# tempTEST.append(len(tempTEST2))
						# print(tempTEST)
						# print("----------------------------222")
						
						
						#wiggle
						tempWiggle=[]
						# if (window[subAreaTracker][0], compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]) in duplicateSchemaCache:
						leftWindowRawDatInd = window[subAreaTracker-1][0]
						leftPotentialRawDatInd = compatibleLists[subAreaTracker-1][trackerList[subAreaTracker-1]][0]
						rightWindowRawDatInd = window[subAreaTracker][0]
						rightPotentialRawDatInd = compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]
						
						
						if limitWiggleRoomCalcCaches[subAreaTracker-1][0] != leftWindowRawDatInd:
							print(window)
							tmjpejeje = []
							for itemtem in limitWiggleRoomCalcCaches:
								tmjpejeje.append(itemtem[0])
							print(tmjpejeje)
							print(leftWindowRawDatInd)
							# print(limitWiggleRoomCalcCaches[subAreaTracker-2][0])
							print(limitWiggleRoomCalcCaches[subAreaTracker-1][0])
							print("woopsies it was meant to be -1 after all222")
							exit()
						if False:#((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd)) in limitWiggleRoomCalcCaches[subAreaTracker-1][1]:
							limWigRoomBigSkipDat = limitWiggleRoomCalcCaches[subAreaTracker-1][1][((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))]
							# tempWiggle = limitWiggleRoom(..., wiggleConstraints[subAreaTracker-1], ...)
							if yesPrint:
								print("444444444444444444444444444444444444444444444")
							if debuggingAnnulusIntersection:
								tempWiggle = limitWiggleRoom(None, subAreaTracker, potentialCache, None, None, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=cancerdebug, specificWindowSegLimitWiggleRoomCalcCache=None, limWigRoomBigSkipDat=limWigRoomBigSkipDat, limWigRoomFastConstraint=compatibleLists[subAreaTracker][trackerList[subAreaTracker]][2], limWigRoomFastDat=None, rawDatIndPairWhenWiggleNotPreConstrained=(leftWindowRawDatInd, leftPotentialRawDatInd, rightWindowRawDatInd, rightPotentialRawDatInd))
							else:
								tempWiggle = limitWiggleRoom(None, subAreaTracker, potentialCache, None, None, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=cancerdebug, specificWindowSegLimitWiggleRoomCalcCache=None, limWigRoomBigSkipDat=limWigRoomBigSkipDat, limWigRoomFastConstraint=wiggleConstraints[subAreaTracker-1], limWigRoomFastDat=None, rawDatIndPairWhenWiggleNotPreConstrained=(leftWindowRawDatInd, leftPotentialRawDatInd, rightWindowRawDatInd, rightPotentialRawDatInd))
							
						else:
							if yesPrint:
								print("555555555555555555555555555555555555555555555555")
							specificWindowSegLimitWiggleRoomCalcCache=limitWiggleRoomCalcCaches[subAreaTracker-1][1]
							# if limitWiggleRoomCalcCaches[currWindowInd-2][0] != leftWindowRawDatInd:
								# print("woopsies it was meant to be -1 after all")
								# exit()
							if debuggingAnnulusIntersection:
								# print(compatibleLists[subAreaTracker][trackerList[subAreaTracker]])
								# print(compatibleLists[subAreaTracker][trackerList[subAreaTracker]][2])
								# print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
								tempWiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=cancerdebug, specificWindowSegLimitWiggleRoomCalcCache=specificWindowSegLimitWiggleRoomCalcCache, limWigRoomBigSkipDat=None, limWigRoomFastConstraint=compatibleLists[subAreaTracker][trackerList[subAreaTracker]][2])
							else:
								tempWiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=cancerdebug, specificWindowSegLimitWiggleRoomCalcCache=specificWindowSegLimitWiggleRoomCalcCache)
						if len(tempWiggle)>0 and (tempWiggle[0] < -math.pi or tempWiggle[0] > math.pi or tempWiggle[1] < -math.pi or tempWiggle[1] > math.pi):
							print("@@@@@2364263246@@@@@@@")
							exit()
						
						
						if len(tempWiggle)==2:
							wiggleConstraints[subAreaTracker] = [tempWiggle[0], tempWiggle[1]]
						else:
							wiggleConstraints[subAreaTracker] = None
					if True:#not(miniCacheSkipHappened): ################# THIS IS just after the pair on the left (at currWindowInd) has been processed, check if we can do big wild card cache skip, if not then do normal compatibleLists prep for next loop
						if wiggleConstraints[subAreaTracker] is not None:# and potentialCache[compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]][0]:
							tmpdebug2+=1
							
							if subAreaTracker==1:
								allChainsAtLeastSize2+=1
							if subAreaTracker==2:
								allChainsAtLeastSize3+=1
							if subAreaTracker==3:
								allChainsAtLeastSize4+=1
							if subAreaTracker==4:
								allChainsAtLeastSize5+=1
							
							
							if len(currBranchOfChainDatTreeIndexList)==0:
								currentBranchOfChainDatTree.append([(window[subAreaTracker][0], compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]), wiggleConstraints[subAreaTracker], None, []]) # im 85% sure its not subAreaTracker-1 !~!~!~!
								currBranchOfChainDatTreeIndexList.append(len(currentBranchOfChainDatTree)-1)
								currentBranchOfChainDatTree=currentBranchOfChainDatTree[-1]
							else:
								if yesPrint:
									print(currBranchOfChainDatTreeIndexList)
									print(currentBranchOfChainDatTree)
								currentBranchOfChainDatTree[3].append([(window[subAreaTracker][0], compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]), wiggleConstraints[subAreaTracker], None, []]) # im 85% sure its not subAreaTracker-1 !~!~!~!
								currBranchOfChainDatTreeIndexList.append(len(currentBranchOfChainDatTree[3])-1)
								currentBranchOfChainDatTree=currentBranchOfChainDatTree[3][-1]
							leftWindowRawDatInd = window[subAreaTracker][0]
							leftPotentialRawDatInd = compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]
							
							cacheSkipHappened=False
							# cacheSkipHappened82ue
							if True:
								cacheSkipHappened = miniCacheSkip(subAreaTracker+1, windowAmount, leftWindowRawDatInd, leftPotentialRawDatInd, window, trackerList, compatibleLists, wiggleConstraints, seedCoord1, seedCoord2, stepCoords1, stepCoords2, rawDat1, rawDat2, stepLength1, stepLength2, edge1SeedIsAfterStepCoordIndN, edge2SeedIsAfterStepCoordIndN, params, edge1, edge2, potentialCache, currentBranchOfChainDatTree, limitWiggleRoomCalcCaches, windowSegWildCardTreeCaches, currBranchOfChainDatTreeIndexList, windowMatches, estimatedScale, edge1PixelationError, edge2PixelationError, windowTempClockwiseCheckCache, angleSideWindowCache) # I wrote miniCacheSkip under the assumption that currWindowInd was for window seg on the right but not the case so need to pass currWindowInd+1 to it instead
							
							if exitlater:
								# print(currentChainDatTree)
								for wasddd in windowSegWildCardTreeCaches:
									print(wasddd)
								# exit()
							
							if not(cacheSkipHappened):
								
								# tempLinearTransformedAnnulusSectorDat = ... wiggleConstraints[subAreaTracker] ...
								tempWindowP1 = None
								tempWindowP2 = None
								angleSide1 = None
								angleSide2 = None
								### subAreaTracker+1 here because we're using current wiggle constraints to constrain search parameters for the next window subarea, the reason [0] is used at the beginning of this function is because we kind of do subAreaTracker and wiggleConstraints[subAreaTracker-1] rather than subAreaTracker+1 and wiggleConstraints[subAreaTracker] since angleWiggleRoom is the 'previous' wiggle constraint for subAreaTracker==0
								if window[subAreaTracker+1][4]:
									tempWindowP1 = stepCoords1[rawDat1[window[subAreaTracker+1][0]][0][0]][0]
									tempWindowP2 = stepCoords1[rawDat1[window[subAreaTracker+1][0]][0][1]][0]
									angleSide1 = window[subAreaTracker+1][2][0]
									angleSide2 = window[subAreaTracker+1][2][1]
								else:
									tempWindowP1 = stepCoords1[rawDat1[window[subAreaTracker+1][0]][0][1]][0]
									tempWindowP2 = stepCoords1[rawDat1[window[subAreaTracker+1][0]][0][0]][0]
									angleSide1 = window[subAreaTracker+1][2][1]
									angleSide2 = window[subAreaTracker+1][2][0]
								# estimatedScale
								#hd33h73h3
								minimumIndex = compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]
								
								tempLinearTransformedAnnulusSectorDat = constructLinearTransformedAnnulusSectorDat(estimatedScale, params, tempWindowP1, tempWindowP2, seedCoord1, edge1PixelationError, edge2PixelationError, angleSide1, angleSide2, wiggleConstraints[subAreaTracker], seedCoord2)
								
								#####
								
								tempOrientation = window[subAreaTracker+1][1]
								if tempOrientation < 0:
									tempOrientation+=math.pi*2
								orientationRange = [tempOrientation-params['orientationError'], tempOrientation+params['orientationError']]
								orientationRange = [orientationRange[0]+wiggleConstraints[subAreaTracker][0], orientationRange[1]+wiggleConstraints[subAreaTracker][1]]
								if orientationRange[1]-orientationRange[0] >= 2*math.pi:
									orientationRange = [0, 2*math.pi]
								else:
									while orientationRange[0] < 0:
										orientationRange[0]+=math.pi*2
									while orientationRange[0] >= math.pi*2:
										orientationRange[0]-=math.pi*2
									while orientationRange[1] <= 0:
										orientationRange[1]+=math.pi*2
									while orientationRange[1] > math.pi*2:
										orientationRange[1]-=math.pi*2
									if abs(orientationRange[0]-math.pi)<0.0001:
										orientationRange[0]=math.pi
									elif abs(orientationRange[0]--math.pi)<0.0001:
										orientationRange[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
									if abs(orientationRange[1]-math.pi)<0.0001:
										orientationRange[1]=math.pi
									elif abs(orientationRange[1]--math.pi)<0.0001:
										orientationRange[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

								
								partitionId1 = int(math.floor(orientationRange[0]/params['segOrientationPartitionSize']))
								partitionId2 = int(math.floor(orientationRange[1]/params['segOrientationPartitionSize']))
								tempCompatible = []
								if partitionId1 <= partitionId2:
									for ind in range(partitionId1, partitionId2+1):
										if debuggingAnnulusIntersection:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=wiggleConstraints[subAreaTracker], window=window, currWindowInd=subAreaTracker+1)
										else:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
								else:
									for ind in range(partitionId1, params['segOrientationPartitionAmt']):
										if debuggingAnnulusIntersection:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=wiggleConstraints[subAreaTracker], window=window, currWindowInd=subAreaTracker+1)
										else:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
									for ind in range(0, partitionId2+1):
										if debuggingAnnulusIntersection:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex, intersectionDat=None, miniCacheSkipRawDatIndPotentialRight=None, debugReturnConstrainedWiggleRoom=wiggleConstraints[subAreaTracker], window=window, currWindowInd=subAreaTracker+1)
										else:
											tempCompatible = tempCompatible+searchOBBTree(staticData2[ind][1], rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
								
								###################
								
								if yesPrint:#False:
									# if subAreaTracker >= 3 and window[0][0]==1 and compatibleLists[0][trackerList[0]][0]==7 and compatibleLists[1][trackerList[1]][0]==7 and compatibleLists[2][trackerList[2]][0]==8 and compatibleLists[3][trackerList[3]][0]==8:
									print("DEBUGGING   @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
									print(wiggleConstraints)
									print(compatibleLists[subAreaTracker])
									print(subAreaTracker)
									print(tempCompatible)
									print("DEBUGGING   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
									# print(wiggleConstraints)
									exit()
								
								# tempOBBTreeSearchDat = searchOBBTree(tree2, rawDat2, stepCoords2, tempLinearTransformedAnnulusSectorDat, seedCoord2, minimumIndex)
								if len(tempCompatible) > 0:
									compatibleLists[subAreaTracker+1] = tempCompatible#.copy()
									trackerList[subAreaTracker+1] = len(compatibleLists[subAreaTracker+1])-1
									subAreaTracker+=1
								else:
									# subAreaTracker-=1
									###(new)
									wiggleConstraints[subAreaTracker]=None
									###
									trackerList[subAreaTracker]-=1
									currBranchOfChainDatTreeIndexList.pop(-1) # in this case there are no possible potentials to pair with right window wild card given the left pair so need to get out of current branch which currently signifies the starting point being the left pair
								
						else: # dont need to pop currBranchOfChainDatTreeIndexList because we didnt add to it with the assumption of starting a branch where the left window seg is paired with the current potential seg
							###(new)
							wiggleConstraints[subAreaTracker]=None # already true but for readability i guess
							###
							trackerList[subAreaTracker]-=1
			else: # just check if limitWiggleRoom inputs are in cache, if yes just speed the comparison, dont need skipDat or anything big here since its last one in schema
				if trackerList[subAreaTracker] < 0: # does this ever happen?
					# print("yes it does")
					# exit()
					###(new)
					wiggleConstraints[subAreaTracker]=None
					compatibleLists[subAreaTracker]=[]
					###
					subAreaTracker-=1
					trackerList[subAreaTracker]-=1
					
					currBranchOfChainDatTreeIndexList.pop(-1) # just putting this whenever subAreaTracker-=1, hopefully it's right 
					
				# if trackerList[-1] >= 0:
				else:
					tmpdebug3+=1
					
					leftWindowRawDatInd = window[subAreaTracker-1][0]
					leftPotentialRawDatInd = compatibleLists[subAreaTracker-1][trackerList[subAreaTracker-1]][0]
					rightWindowRawDatInd = window[subAreaTracker][0]
					rightPotentialRawDatInd = compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]
					
					wiggle=[]
					if limitWiggleRoomCalcCaches[subAreaTracker-1][0] != leftWindowRawDatInd:
						print(window)
						tmjpejeje = []
						for itemtem in limitWiggleRoomCalcCaches:
							tmjpejeje.append(itemtem[0])
						print(tmjpejeje)
						print(leftWindowRawDatInd)
						# print(limitWiggleRoomCalcCaches[subAreaTracker-2][0])
						print(limitWiggleRoomCalcCaches[subAreaTracker-1][0])
						print("woopsies it was meant to be -1 after all111")
						exit()
					
					else:
						if yesPrint:
							print("88888888888888888888888888888888888888888")
						specificWindowSegLimitWiggleRoomCalcCache=limitWiggleRoomCalcCaches[subAreaTracker-1][1]
						if debuggingAnnulusIntersection:
							wiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=False, specificWindowSegLimitWiggleRoomCalcCache=specificWindowSegLimitWiggleRoomCalcCache, limWigRoomBigSkipDat=None, limWigRoomFastConstraint=compatibleLists[subAreaTracker][trackerList[subAreaTracker]][2])
						else:
							wiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=False, specificWindowSegLimitWiggleRoomCalcCache=specificWindowSegLimitWiggleRoomCalcCache)
					
					# wiggle = limitWiggleRoom(wiggleConstraints, subAreaTracker, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, debug3=True)
					if len(wiggle)>0 and (wiggle[0] < -math.pi or wiggle[0] > math.pi or wiggle[1] < -math.pi or wiggle[1] > math.pi):
						print("@@@@@@@@ddddd@@@@5435435@@@@@@@@")
						exit()
					
					if yesPrint:
						print("tmpdebug3:::::::::::::::::::::::::")
						print(tmpdebug3)
					
					if len(wiggle)==2:
						
						allChainsAtLeastSize6+=1
						
						tic = time.perf_counter()
						
						currentBranchOfChainDatTree[3].append([(window[subAreaTracker][0], compatibleLists[subAreaTracker][trackerList[subAreaTracker]][0]), (wiggle[0], wiggle[1]), None, []])
						
						# timesPastWiggleLen2+=1
						tmpdebug4+=1
						if yesPrint:
							print("????????????????????????????????????????????????????????????????")
						# set it halfway for a rough middleground?
						shiftWindowBy = None
						if wiggle[1] == wiggle[0]:
							shiftWindowBy = wiggle[0]
						elif wiggle[1] >= wiggle[0]: # i assume wiggle is always wiggle[1] more anticlockwise than wiggle[0]?
							shiftWindowBy = (wiggle[1] + wiggle[0])/2
						else:
							tempEnd = wiggle[1]+math.pi*2
							shiftWindowBy = (tempEnd+wiggle[0])/2
							if shiftWindowBy>math.pi:
								shiftWindowBy-=math.pi*2
						
						# calc similarity/variance or whatever
						
						pointPairs = [] # [(windowpt1, otherpt1), (windowpt2, otherpt2), ...]
						pointPairsPotential = []
						
						tempWindowAngleRanges = []
						tempPotentialAngleRanges = []
						if yesPrint:
							print(window)
						# rightPotentialRawDatInd
						if True:
							tmpbeugg = []
							for trackerInd in range(len(trackerList)):
								tmpbeugg.append(compatibleLists[trackerInd][trackerList[trackerInd]][0])
							if yesPrint:
								print(tmpbeugg)
						
						for windowSeg in window:
							if windowSeg[4]:
								tempWindowAngleRanges.append([windowSeg[2][1], windowSeg[2][0]])
							else:
								tempWindowAngleRanges.append([windowSeg[2][0], windowSeg[2][1]])
						for trackerInd in range(len(trackerList)):
							# compatibleLists[-1][trackerList[-1]][0]
							cacheInd = compatibleLists[trackerInd][trackerList[trackerInd]][0]
							tempPotentialStartAngle = potentialCache[cacheInd][3]
							tempPotentialEndAngle = potentialCache[cacheInd][4]
							if potentialCache[cacheInd][5]:
								tempPotentialAngleRanges.append([tempPotentialEndAngle, tempPotentialStartAngle])
							else:
								tempPotentialAngleRanges.append([tempPotentialStartAngle, tempPotentialEndAngle])
						
						for tempWindowAngleRange in tempWindowAngleRanges:
							tempWindowAngleRange[0]+= shiftWindowBy
							tempWindowAngleRange[1]+= shiftWindowBy
							if tempWindowAngleRange[0] <= -math.pi:
								tempWindowAngleRange[0]+= math.pi*2
							elif tempWindowAngleRange[0] > math.pi:
								tempWindowAngleRange[0]-= math.pi*2
							if tempWindowAngleRange[1] <= -math.pi:
								tempWindowAngleRange[1]+= math.pi*2
							elif tempWindowAngleRange[1] > math.pi:
								tempWindowAngleRange[1]-= math.pi*2
							if abs(tempWindowAngleRange[0]-math.pi)<0.0001:
								tempWindowAngleRange[0]=math.pi
							elif abs(tempWindowAngleRange[0]--math.pi)<0.0001:
								tempWindowAngleRange[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
							if abs(tempWindowAngleRange[1]-math.pi)<0.0001:
								tempWindowAngleRange[1]=math.pi
							elif abs(tempWindowAngleRange[1]--math.pi)<0.0001:
								tempWindowAngleRange[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

						# for now just take start and end of each overlap interval for each pair of segs and if the end of one is very close to the start of the next one just remove one of them so its more spaced out, define close by like one in last 5% of angle interval and other in first 5% or something
						tempOverlapRanges = []
						for pairInd in range(len(tempWindowAngleRanges)):
							if abs(tempWindowAngleRanges[pairInd][0]-tempPotentialAngleRanges[pairInd][0])<0.00001:
								tempWindowAngleRanges[pairInd][0] = tempPotentialAngleRanges[pairInd][0]
							if abs(tempWindowAngleRanges[pairInd][1]-tempPotentialAngleRanges[pairInd][1])<0.00001:
								tempWindowAngleRanges[pairInd][1] = tempPotentialAngleRanges[pairInd][1]
							if abs(tempWindowAngleRanges[pairInd][0]-tempPotentialAngleRanges[pairInd][1])<0.00001:
								tempWindowAngleRanges[pairInd][0] = tempPotentialAngleRanges[pairInd][1]
							if abs(tempWindowAngleRanges[pairInd][1]-tempPotentialAngleRanges[pairInd][0])<0.00001:
								tempWindowAngleRanges[pairInd][1] = tempPotentialAngleRanges[pairInd][0]
							if tempWindowAngleRanges[pairInd][0] <= tempWindowAngleRanges[pairInd][1]:
								if tempPotentialAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
									overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
									overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
									tempOverlapRanges.append([overlapStart, overlapEnd])
								else:
									if tempWindowAngleRanges[pairInd][1] >= tempPotentialAngleRanges[pairInd][0]:
										overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
										overlapEnd = tempWindowAngleRanges[pairInd][1]
										tempOverlapRanges.append([overlapStart, overlapEnd])
									elif tempWindowAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
										overlapStart = tempWindowAngleRanges[pairInd][0]
										overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
										tempOverlapRanges.append([overlapStart, overlapEnd])
									else:
										print("huh?3dij3ij")
										exit()
									
							else:
								if tempPotentialAngleRanges[pairInd][0] <= tempPotentialAngleRanges[pairInd][1]:
									if tempPotentialAngleRanges[pairInd][1] >= tempWindowAngleRanges[pairInd][0]:
										overlapStart = max(tempPotentialAngleRanges[pairInd][0], tempWindowAngleRanges[pairInd][0])
										overlapEnd = tempPotentialAngleRanges[pairInd][1]
										tempOverlapRanges.append([overlapStart, overlapEnd])
									elif tempPotentialAngleRanges[pairInd][0] <= tempWindowAngleRanges[pairInd][1]:
										overlapStart = tempPotentialAngleRanges[pairInd][0]
										overlapEnd = min(tempPotentialAngleRanges[pairInd][1], tempWindowAngleRanges[pairInd][1])
										tempOverlapRanges.append([overlapStart, overlapEnd])
									else:
										print("huh?yt45")
										exit()
									# overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
									# overlapEnd = tempPotentialAngleRanges[pairInd][1]
									# tempOverlapRanges.append([overlapStart, overlapEnd])
								else:
									overlapStart = max(tempWindowAngleRanges[pairInd][0], tempPotentialAngleRanges[pairInd][0])
									overlapEnd = min(tempWindowAngleRanges[pairInd][1], tempPotentialAngleRanges[pairInd][1])
									tempOverlapRanges.append([overlapStart, overlapEnd])
							
						yetAnotherTempList = []
						for pairInd in range(len(tempWindowAngleRanges)):
							
							tmptest1 = 0
							tmptest2 = 0
							tmptest3 = 0
							
							# IF ANY ANGLES ARE ABOVE 180 THEY GET NEGATED E.G. IF ANGLE IS -200 OR 200 ITLL TURN INTO 160 OR -160, HOPE THAT DOESNT MATTER
							absWindowInterval = tempWindowAngleRanges[pairInd][1]-tempWindowAngleRanges[pairInd][0]
							if absWindowInterval != 0:
								
								if False:
									if absWindowInterval < -math.pi:
										absWindowInterval+= math.pi*2
									elif absWindowInterval > math.pi:
										absWindowInterval-= math.pi*2
									tmptest1=absWindowInterval
									absWindowInterval=abs(absWindowInterval)
								
								if True: # new ASSUMING tempWindowAngleRanges[pairInd][1] IS MORE ANTICLOCKWISE THAN tempWindowAngleRanges[pairInd][0]	 !!!! (like wiggle room and stuff)
									
									if absWindowInterval < 0:
										absWindowInterval+= math.pi*2
									tmptest1=absWindowInterval
								
								ratioOverlapPoint1 = tempOverlapRanges[pairInd][0]-tempWindowAngleRanges[pairInd][0]
								if False:
									if ratioOverlapPoint1 < -math.pi:
										ratioOverlapPoint1+= math.pi*2
									elif ratioOverlapPoint1 > math.pi:
										ratioOverlapPoint1-= math.pi*2
									
									tmptest2=ratioOverlapPoint1
									
									ratioOverlapPoint1=abs(ratioOverlapPoint1/absWindowInterval)
								if True:
									if ratioOverlapPoint1 < 0:
										ratioOverlapPoint1+= math.pi*2
									tmptest2=ratioOverlapPoint1
									ratioOverlapPoint1 = ratioOverlapPoint1/absWindowInterval
								
								ratioOverlapPoint2 = tempOverlapRanges[pairInd][1]-tempWindowAngleRanges[pairInd][0]
								if False:
									if ratioOverlapPoint2 < -math.pi:
										ratioOverlapPoint2+= math.pi*2
									elif ratioOverlapPoint2 > math.pi:
										ratioOverlapPoint2-= math.pi*2
									# ratioOverlapPoint2=ratioOverlapPoint2/absWindowInterval
									tmptest3=ratioOverlapPoint2
									ratioOverlapPoint2=abs(ratioOverlapPoint2/absWindowInterval) # shouldnt need this since both ratioOverlapPoint1 and ratioOverlapPoint2 should have same sign with abs(2)>abs(1) since its further along the interval/lineseg or whatever this is calcing
								if True:
									if ratioOverlapPoint2 < 0:
										ratioOverlapPoint2+= math.pi*2
									tmptest3=ratioOverlapPoint2
									ratioOverlapPoint2 = ratioOverlapPoint2/absWindowInterval
								
								overflowCheck = tempOverlapRanges[pairInd][1] - tempOverlapRanges[pairInd][0]
								
								if abs(overflowCheck) >= 0.000001 and not(tmptest1 >= tmptest3 and tmptest3 >= tmptest2 and tmptest2>=0):
									print(tmptest1)
									print(tmptest2)
									print(tmptest3)
									print(tempWindowAngleRanges[pairInd])
									print(tempPotentialAngleRanges[pairInd])
									print(tempOverlapRanges[pairInd])
									print(window)
									print(tempWindowAngleRanges)
									print(tempPotentialAngleRanges)
									print(shiftWindowBy)
									print(wiggle)
									print(wiggleConstraints)
									print("wat?deod")
									exit()
								
								if abs(overflowCheck) >= 0.000001:
									# so arbitrary its textbook insanity \/
									
									# if ratioOverlapPoint2-ratioOverlapPoint1 > 0.08:
									if abs(ratioOverlapPoint2-ratioOverlapPoint1) > 0.08: # shouldnt need abs, 2 should be >= 1
										yetAnotherTempList.append([ratioOverlapPoint1, ratioOverlapPoint2])
									else:
										yetAnotherTempList.append([ratioOverlapPoint1])
								else:
									if ratioOverlapPoint1 >= 0 and ratioOverlapPoint1 <=1:
										yetAnotherTempList.append([ratioOverlapPoint1])
									elif ratioOverlapPoint2 >= 0 and ratioOverlapPoint2 <=1:
										yetAnotherTempList.append([ratioOverlapPoint2])
							else: # use dist along line ratio instead? 
								
								yetAnotherTempList.append([0, 1])
								
						for yetAnotherTempListInd in range(len(yetAnotherTempList)-1):
							firstRatio = None
							if len(yetAnotherTempList[yetAnotherTempListInd]) > 1:
								firstRatio=yetAnotherTempList[yetAnotherTempListInd][1]
							else:
								firstRatio=yetAnotherTempList[yetAnotherTempListInd][0]
							
							secondRatio = yetAnotherTempList[yetAnotherTempListInd+1][0]
							if 1-firstRatio+secondRatio < 0.08:
								if len(yetAnotherTempList[yetAnotherTempListInd]) > 1:
									yetAnotherTempList[yetAnotherTempListInd] = [yetAnotherTempList[yetAnotherTempListInd][0]]
								else:
									yetAnotherTempList[yetAnotherTempListInd] = []
						
						ticTemp = time.perf_counter()
						
						for pairInd in range(len(yetAnotherTempList)): #  pairInd HERE IS PAIR OF LINESEGS NOT PAIR OF ANGLE RAY SHOOT INTERSECTIONS 
							pointPairs.append([])
							pointPairsPotential.append([])
							for endingInd in range(len(yetAnotherTempList[pairInd])): # we can only do this because we only remove 2nd point or 2nd point and 1st point so we'd never have yetAnotherTempList[i] = [ratioOverlapPoint2]
								pointPairs[-1].append([])
								pointPairsPotential[-1].append([])
								angleInPotentialEdge = tempOverlapRanges[pairInd][endingInd]
								angleInWindowEdge = angleInPotentialEdge-shiftWindowBy
								if angleInWindowEdge <= -math.pi:
									angleInWindowEdge+= math.pi*2
								elif angleInWindowEdge > math.pi:
									angleInWindowEdge-= math.pi*2
								if abs(angleInWindowEdge-math.pi)<0.0001:
									angleInWindowEdge=math.pi
								elif abs(angleInWindowEdge--math.pi)<0.0001:
									angleInWindowEdge=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
								
								windowSegStartIndInContour = stepCoords1[rawDat1[window[pairInd][0]][0][0]][1]
								windowSegEndIndInContour = stepCoords1[rawDat1[window[pairInd][0]][0][1]][1]
								
								
								windowSegStartRatioOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][0]][4]
								windowSegEndRatioOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][1]][4]
								# windowSegStartDistOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][0]][2]
								# windowSegEndDistOnLine = stepCoords1[rawDat1[window[pairInd][0]][0][1]][2]
								potentialSegStartIndInContour = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][0]][1]
								potentialSegEndIndInContour = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][1]][1]
								potentialSegStartRatioOnLine = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][0]][4]
								potentialSegEndRatioOnLine = stepCoords2[rawDat2[compatibleLists[pairInd][trackerList[pairInd]][0]][0][1]][4]
								# potentialSegStartDistOnLine = stepCoords2[rawDat2[compatibleLists[trackerInd][trackerList[trackerInd]][0]][0][0]][2]
								# potentialSegEndDistOnLine = stepCoords2[rawDat2[compatibleLists[trackerInd][trackerList[trackerInd]][0]][0][1]][2]
								
								# print(windowSegStartIndInContour+windowSegStartRatioOnLine)
								# print(windowSegEndIndInContour+windowSegEndRatioOnLine)
								# print("-")
								# print(potentialSegStartIndInContour+potentialSegStartRatioOnLine)
								# print(potentialSegEndIndInContour+potentialSegEndRatioOnLine)
								# print("-")
								
								windowLineC = None
								windowLineM = None
								if abs(angleInWindowEdge) != math.pi/2:
									windowLineM = math.tan(angleInWindowEdge)
									windowLineC = seedCoord1[1]-windowLineM*seedCoord1[0]
								else:
									windowLineC = seedCoord1[0]
								
								
								if windowSegStartIndInContour == windowSegEndIndInContour: # inds like 5.1, 5.7
									idktemp(edge1, windowSegStartIndInContour, windowSegStartRatioOnLine, windowSegEndIndInContour, windowSegEndRatioOnLine, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
									
								
								else: #windowSegStartIndInContour != windowSegEndIndInContour:
									# do first and last since they usually have non-integer boundaries
									# if windowSegStartIndInContour left/right and windowSegStartIndInContour+1 right/left
									# first do firstind to firstind+1 and if intersection consider firstind+windowSegStartRatioOnLine to firstind+1
									# same but lastind lastind+1 and consider lastind to lastind+windowSegEndRatioOnLine
									
									# then iterate rest
									
									idktemp(edge1, windowSegStartIndInContour, windowSegStartRatioOnLine, 'pointless', 1, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
									
									if windowSegEndRatioOnLine != 0:
										idktemp(edge1, windowSegEndIndInContour, 0, 'pointless', windowSegEndRatioOnLine, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
									
									for remainingInd in range(windowSegStartIndInContour+1, windowSegEndIndInContour):
										idktemp(edge1, remainingInd, 0, 'pointless', 1, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1)
								
								
								potentialLineC = None
								potentialLineM = None
								if abs(angleInPotentialEdge) != math.pi/2:
									potentialLineM = math.tan(angleInPotentialEdge)
									potentialLineC = seedCoord2[1]-potentialLineM*seedCoord2[0]
								else:
									potentialLineC = seedCoord2[0]
								
								
								if potentialSegStartIndInContour == potentialSegEndIndInContour: # inds like 5.1, 5.7
									idktemp(edge2, potentialSegStartIndInContour, potentialSegStartRatioOnLine, potentialSegEndIndInContour, potentialSegEndRatioOnLine, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
								
								else: #windowSegStartIndInContour != windowSegEndIndInContour:
									# do first and last since they usually have non-integer boundaries
									# if windowSegStartIndInContour left/right and windowSegStartIndInContour+1 right/left
									# first do firstind to firstind+1 and if intersection consider firstind+windowSegStartRatioOnLine to firstind+1
									# same but lastind lastind+1 and consider lastind to lastind+windowSegEndRatioOnLine
									
									# then iterate rest
									
									idktemp(edge2, potentialSegStartIndInContour, potentialSegStartRatioOnLine, 'pointless', 1, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
									
									if potentialSegEndRatioOnLine != 0:
										idktemp(edge2, potentialSegEndIndInContour, 0, 'pointless', potentialSegEndRatioOnLine, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
									
									for remainingInd in range(potentialSegStartIndInContour+1, potentialSegEndIndInContour):
										idktemp(edge2, remainingInd, 0, 'pointless', 1, potentialLineM, potentialLineC, seedCoord2, pointPairsPotential, stepLength2)
						
						
						for lineSegPairInd in range(len(pointPairs)): # moved this back 1 indent idk why it was forward
							for n in range(len(pointPairs[lineSegPairInd])): # 1 or 2 i think
								windowPts = pointPairs[lineSegPairInd][n]
								
								if len(windowPts) > 3:
									lowest = windowPts[0]
									highest = windowPts[0]
									for k in range(1, len(windowPts)):
										if windowPts[k][0] < lowest[0]:
											lowest = windowPts[k]
										elif windowPts[k][0] > highest[0]:
											highest = windowPts[k]
									middle = (lowest[0]+highest[0])/2
									middest = windowPts[0]
									currMidDiff = abs(middest[0]-middle)
									for k in range(1, len(windowPts)):
										if abs(windowPts[k][0]-middle) < currMidDiff:
											middest = windowPts[k]
											currMidDiff = abs(windowPts[k][0]-middle)
									windowPts = [lowest, middest, highest]
									pointPairs[lineSegPairInd][n] = windowPts
							# for n in range(len(pointPairsPotential[pairInd])):
								potentialPts = pointPairsPotential[lineSegPairInd][n]
								if len(potentialPts) > 3:
									lowest = potentialPts[0]
									highest = potentialPts[0]
									for k in range(1, len(potentialPts)):
										if potentialPts[k][0] < lowest[0]:
											lowest = potentialPts[k]
										elif potentialPts[k][0] > highest[0]:
											highest = potentialPts[k]
									middle = (lowest[0]+highest[0])/2
									middest = potentialPts[0]
									currMidDiff = abs(middest[0]-middle)
									for k in range(1, len(potentialPts)):
										if abs(potentialPts[k][0]-middle) < currMidDiff:
											middest = potentialPts[k]
											currMidDiff = abs(potentialPts[k][0]-middle)
									potentialPts = [lowest, middest, highest]
									pointPairsPotential[lineSegPairInd][n] = potentialPts
						
						scaleList = []
						for lineSegPairInd in range(len(pointPairs)):
							for p in range(len(pointPairs[lineSegPairInd])):
								tempList = []
								for n in range(len(pointPairs[lineSegPairInd][p])):
									for m in range(len(pointPairsPotential[lineSegPairInd][p])):
										tempRatio = pointPairs[lineSegPairInd][p][n][0]/pointPairsPotential[lineSegPairInd][p][m][0]
										# tempRatio = pointPairsPotential[pairInd][m][0]/pointPairs[pairInd][n][0]
										tempList.append([tempRatio, p, n, m, lineSegPairInd])
								tempList.sort()
								scaleList.append(tempList)
						
						bestIndsForMean = bestPtsForMean(scaleList)
						# either return bestVariance from bestPtsForMean or calc a different more computationally intensive but more useful variance e.g. square differences
						
						tocTemp = time.perf_counter()
						
						tempTimeKeep+=tocTemp-ticTemp
						tempTimeKeepAmount+=1
						# if len(bestIndsForMean) HERE HERE HERE HERE
						if bestIndsForMean is not None and len(bestIndsForMean)>0:
							# remove worst X amount of outliers
							totalPts = 0
							for ind in bestIndsForMean:
								if ind != -1:
									totalPts+=1
							
							removeWorstN = 1 + max(0, math.floor((totalPts-len(window))/3))
							for loops in range(removeWorstN):
								tempMean = 0
								for ind, val in enumerate(bestIndsForMean):
									if val != -1:
										tempMean+=scaleList[ind][val][0]
								tempMean = tempMean/totalPts
								
								mostOutlyingOutlier = 0
								amountOfOutlying = 0
								for ind, val in enumerate(bestIndsForMean):
									if val != -1:
										tempOutlying = abs(tempMean-scaleList[ind][val][0])
										if tempOutlying > amountOfOutlying:
											amountOfOutlying = tempOutlying
											mostOutlyingOutlier = ind
								bestIndsForMean[mostOutlyingOutlier] = -1
								totalPts-=1
							
							finalVariance = 0
							finalMean = 0
							for ind, val in enumerate(bestIndsForMean):
								if val != -1:
									finalMean+=scaleList[ind][val][0]
									
							finalMean = finalMean/totalPts
							for ind, val in enumerate(bestIndsForMean):
								if val != -1:
									finalVariance+=(finalMean-scaleList[ind][val][0])**2
							finalVariance = finalVariance/totalPts
							finalVariance = finalVariance/(finalMean)**2
							
							impliedScale = finalMean # just for readability
							
							### new, not sure why i used minScale and maxScale when that can give vastly different abs dists depending on the dist from seed, 50% scale error close to seed could be very accurate
							
							scaleQueryOverWindow = 1/impliedScale
							maxAbsDistToCountAsMatch=float('-inf')
							for ind, val in enumerate(bestIndsForMean):
								if val != -1:
									distFromSeedQueryPoint = pointPairsPotential[scaleList[ind][val][4]][scaleList[ind][val][1]][scaleList[ind][val][3]][0]
									distFromSeedWindowPointInQuerySpace = scaleQueryOverWindow*pointPairs[scaleList[ind][val][4]][scaleList[ind][val][1]][scaleList[ind][val][2]][0]
									absDistQuerySpace = abs(distFromSeedWindowPointInQuerySpace-distFromSeedQueryPoint)
									if absDistQuerySpace > maxAbsDistToCountAsMatch:
										maxAbsDistToCountAsMatch=absDistQuerySpace
									
							
							maxAbsDistToCountAsMatch+=params["maxAbsDistToCountAsMatchPixelError"]
							
							# either think about getting rid of more outliers by slicing off quartiles or whatever or carry on with using this range/maxdist as a threshold below to classify as matching around seedpoints
							
							meanAbsDistDiff = 0
							
							tempRatio = 1/impliedScale
							
							minimumStepsAroundSeedMatch = params['minimumStepsAroundSeedMatch']
							# tempRatio = 1/impliedScale
							
							checkArcLengthStepsAroundSeedRadius = params['checkArcLengthStepsAroundSeedRadius']
							
							checkPtsBetweenStepCoordsAmt = params['checkPtsBetweenStepCoordsAmt'] # 3 for now so 5 total each subarea (endings shared though)
							
							sinP1 = math.sin(shiftWindowBy)
							cosP1 = math.cos(shiftWindowBy)
							# rotatedPt1 = [windowP1[0]*cosP1 - windowP1[1]*sinP1, windowP1[0]*sinP1 + windowP1[1]*cosP1]
							
							totalSuccessfulPtsAroundSeed = 0
							
							lastClosestInd = 0 # the closest point inds should always be monotone increasing if stepCoords are increasing and vice versa so both edges should both increase/decrease closest point pairs inds
							stepCoordIndBeforeLastClosestInd = edge2SeedIsAfterStepCoordIndN
							amtWithoutFailuresAfter = 0
							failureAmtAfter = 0
							lastClosestPoint = None
							firstTest = True
							# print(min(edge1SeedIsAfterStepCoordIndN+1, len(stepCoords1)-1))
							# print(min(edge1SeedIsAfterStepCoordIndN+1+minimumStepsAroundSeedMatch, len(stepCoords1)-1))
							# after
							for ind in range(min(edge1SeedIsAfterStepCoordIndN+1, len(stepCoords1)-1), min(edge1SeedIsAfterStepCoordIndN+1+checkArcLengthStepsAroundSeedRadius, len(stepCoords1)-1)): # for each subarea defined by 2 consecutive seedcoords
								if yesPrint:
									print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2222222222")
								testCoord = copy.deepcopy(stepCoords1[ind][0]) # .copy not needed
								testCoord = [testCoord[0] - seedCoord1[0], testCoord[1] - seedCoord1[1]]
								testCoord = [testCoord[0]*cosP1 - testCoord[1]*sinP1, testCoord[0]*sinP1 + testCoord[1]*cosP1]
								testCoord = [testCoord[0]*tempRatio, testCoord[1]*tempRatio]
								testCoord[0]+=seedCoord2[0]
								testCoord[1]+=seedCoord2[1]
								
								# now testCoord has been transformed into edge2 space
								
								# secondClosest = ... ADD THIS IF NECESSARY if 5 pts sample isnt accurate enough
								
								# indsWithoutCloser = 0
								tempIndClosestDist = None
								tempClosestPoint = None
								tempClosestDist = float('inf')
								tempStepCoordIndBeforeClosestDist = None
								# tempLastClosestInd = lastClosestInd
								startStepCoordIndInEdge2 = stepCoordIndBeforeLastClosestInd+1 # -1 below because the iterations between start and end, define the start of the subarea, and the end of the subare will be startind+1
								endStepCoordIndInEdge2 = min(startStepCoordIndInEdge2 + 2*windowAmount, len(stepCoords2)-1) - 1 # will add 1 to each to get start and end, terrible arbitrary choice but its hopefully temp compromise between exhaustive checking and accidentally skipping over closest pts
								for stepInd in range(startStepCoordIndInEdge2, endStepCoordIndInEdge2+1): # +1 -1 for readability  ## preliminary scan checking dist to each stepcoord as well as ~3 pts evenly spaced within subareas defined by stepcoords
									startInd = stepCoords2[stepInd][1]+1
									endInd = stepCoords2[stepInd+1][1]
									if startInd < lastClosestInd:
										# if lastC
										startInd = math.floor(lastClosestInd) # since startInd is already the first integer index AFTER the beginning of the subarea, floor covers all remaining cases
									sampleStep = max(1, math.floor((endInd-startInd)/(checkPtsBetweenStepCoordsAmt+2))) # +2 to account for stepcoord endings
									for cntr in range(1, min(endInd-startInd, checkPtsBetweenStepCoordsAmt+1)):
										mostTempInd = startInd+cntr*sampleStep
										mostTempCoord = edge2[mostTempInd][0]
										mostTempDist = getDistance(mostTempCoord[0], testCoord[0], mostTempCoord[1], testCoord[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempStepCoordIndBeforeClosestDist = stepInd
											tempIndClosestDist = mostTempInd
											tempClosestPoint = mostTempCoord
									mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd][0][0], testCoord[1], stepCoords2[stepInd][0][1]) # stepcoord ending 1 aka the start of the subarea
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd
										tempIndClosestDist = stepCoords2[stepInd][1] + stepCoords2[stepInd][4] # 
										tempClosestPoint = stepCoords2[stepInd][0]
									mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd+1][0][0], testCoord[1], stepCoords2[stepInd+1][0][1]) # stepcoord ending 2 aka the end of the subarea
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd
										tempIndClosestDist = stepCoords2[stepInd+1][1] + stepCoords2[stepInd+1][4] # 
										tempClosestPoint = stepCoords2[stepInd+1][0]
								
								
								# now check every contour point within the subarea that contained the closest point in preliminary check
								if tempStepCoordIndBeforeClosestDist is not None: # should never be none anyway
									# for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1], min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1]+2, edge2.shape[0])): # guess im just checking the point before the first stepcoord at floor(stepcoordind) and ceil of the stepcoordind for the ending anyway so dont need to be particular about checking all whole integer indices strictly between stepcoords and the stepcoords themselves as float indices
									for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1]+1, min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1] + 1, edge2.shape[0])):
										mostTempDist = getDistance(edge2[tempInd][0][0], testCoord[0], edge2[tempInd][0][1], testCoord[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = tempInd
											tempClosestPoint = edge2[tempInd][0]
											
								# finally do the check for if closest dist is actually at that coord or if its on line between that and prevcoord or nextcoord
								# then set lastClosestInd and stuff
								if tempIndClosestDist is not None:
									if tempIndClosestDist % 1 == 0:
										absoluteTempIndClosestDist = tempIndClosestDist
										if tempIndClosestDist>0:
											ratioOnLine, closePt = closestPt([edge2[tempIndClosestDist-1][0], edge2[tempIndClosestDist][0]], testCoord)
											mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
											if mostTempDist < tempClosestDist:
												tempClosestDist = mostTempDist
												tempIndClosestDist = tempIndClosestDist-1 + ratioOnLine
												tempClosestPoint = closePt
										if absoluteTempIndClosestDist < edge2.shape[0]-1:
											ratioOnLine, closePt = closestPt([edge2[absoluteTempIndClosestDist][0], edge2[absoluteTempIndClosestDist+1][0]], testCoord)
											mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
											if mostTempDist < tempClosestDist:
												tempClosestDist = mostTempDist
												tempIndClosestDist = absoluteTempIndClosestDist + ratioOnLine
												tempClosestPoint = closePt
								
								withinMatchRange = False
								
								if yesPrint:
									print('#######################e3ee3#####################################')
									print(tempClosestDist)
									print(maxAbsDistToCountAsMatch)
									print(lastClosestPoint)
									print(tempClosestPoint)
									# print(maxAbsDistToCountAsMatch)
									# print("di388")
								if tempClosestDist <= maxAbsDistToCountAsMatch:
									withinMatchRange = True
								
								
								if (lastClosestPoint is None and not(firstTest)) or tempClosestPoint is None or ((lastClosestPoint is not None and tempClosestPoint is not None) and tempClosestPoint[0] == lastClosestPoint[0] and tempClosestPoint[1] == lastClosestPoint[1]) or not(withinMatchRange):
									failureAmtAfter+=1
								else:
									amtWithoutFailuresAfter+=1
								if failureAmtAfter>=2 and failureAmtAfter/(failureAmtAfter+amtWithoutFailuresAfter) > 0.5: # if decent amount has been tested and the failure rate is over half (if half and half we err to side of assuming matching zone cause its around seed)
									break
								
								lastClosestPoint = tempClosestPoint
								lastClosestInd = tempIndClosestDist
								stepCoordIndBeforeLastClosestInd = tempStepCoordIndBeforeClosestDist
								firstTest=False
								# ... loop stuff that i never added the first time
								
								
							# before
							# for ind in range(max(edge1SeedIsAfterStepCoordIndN, 0), max(edge1SeedIsAfterStepCoordIndN-minimumStepsAroundSeedMatch, 0)):
								
							
							######### PASTING ABOVE LOOPS AND CHANGING TO CALC STUFF BEFORE RATHER THAN AFTER
							########
							
							lastClosestInd = float('inf') # the closest point inds should always be monotone increasing if stepCoords are increasing and vice versa so both edges should both increase/decrease closest point pairs inds
							stepCoordIndBeforeLastClosestInd = edge2SeedIsAfterStepCoordIndN
							amtWithoutFailuresBefore = 0
							failureAmtBefore = 0
							lastClosestPoint = None
							firstTest=True
							
							for ind in range(edge1SeedIsAfterStepCoordIndN, max(edge1SeedIsAfterStepCoordIndN-checkArcLengthStepsAroundSeedRadius-1, 0), -1): # for each subarea defined by 2 consecutive seedcoords
								if yesPrint:
									print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@111111111")
								testCoord = copy.deepcopy(stepCoords1[ind][0]) # not needed (copy part)
								testCoord = [testCoord[0] - seedCoord1[0], testCoord[1] - seedCoord1[1]]
								testCoord = [testCoord[0]*cosP1 - testCoord[1]*sinP1, testCoord[0]*sinP1 + testCoord[1]*cosP1]
								testCoord = [testCoord[0]*tempRatio, testCoord[1]*tempRatio]
								testCoord[0]+=seedCoord2[0]
								testCoord[1]+=seedCoord2[1]
								
								# now testCoord has been transformed into edge2 space
								
								# secondClosest = ... ADD THIS IF NECESSARY if 5 pts sample isnt accurate enough
								
								# indsWithoutCloser = 0
								tempIndClosestDist = None
								tempClosestPoint = None
								tempClosestDist = float('inf')
								tempStepCoordIndBeforeClosestDist = None
								# tempLastClosestInd = lastClosestInd
								startStepCoordIndInEdge2 = stepCoordIndBeforeLastClosestInd # # start and end here (to be more intuitive) is goin backwards from the seed
								endStepCoordIndInEdge2 = max(startStepCoordIndInEdge2 - 2*windowAmount, 0) + 1 # will add 1 to each to get start and end, terrible arbitrary choice but its hopefully temp compromise between exhaustive checking and accidentally skipping over closest pts
								for stepInd in range(startStepCoordIndInEdge2, endStepCoordIndInEdge2-1, -1): # This part will also be step -1 whereas the actual test within each subarea will be forwards normal step					 ##### +1 -1 for readability  ## preliminary scan checking dist to each stepcoord as well as ~3 pts evenly spaced within subareas defined by stepcoords
									# startInd = stepCoords2[stepInd][1]+1
									# endInd = stepCoords2[stepInd+1][1]
									startInd = stepCoords2[stepInd-1][1]+1 # start and end here must be increasing, like the natural order of the contour
									endInd = stepCoords2[stepInd][1]
									if endInd > lastClosestInd:
										# if lastC
										endInd = math.ceil(lastClosestInd) # since endInd is already the first integer index BEFORE the ending of the subarea, ceil covers all remaining cases
									sampleStep = max(1, math.floor((endInd-startInd)/(checkPtsBetweenStepCoordsAmt+2))) # +2 to account for stepcoord endings
									for cntr in range(1, min(endInd-startInd, checkPtsBetweenStepCoordsAmt+1)):
										mostTempInd = startInd+cntr*sampleStep
										mostTempCoord = copy.deepcopy(edge2[mostTempInd][0])
										mostTempDist = getDistance(mostTempCoord[0], testCoord[0], mostTempCoord[1], testCoord[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempStepCoordIndBeforeClosestDist = stepInd-1 # -1 because due to reversal 
											tempIndClosestDist = mostTempInd
											tempClosestPoint = copy.deepcopy(mostTempCoord)
									mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd][0][0], testCoord[1], stepCoords2[stepInd][0][1]) # stepcoord ending 2 aka the end of the subarea
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd-1
										tempIndClosestDist = stepCoords2[stepInd][1] + stepCoords2[stepInd][4] # 
										tempClosestPoint = copy.deepcopy(stepCoords2[stepInd][0])
									mostTempDist = getDistance(testCoord[0], stepCoords2[stepInd-1][0][0], testCoord[1], stepCoords2[stepInd-1][0][1]) # stepcoord ending 1 aka the start of the subarea
									if mostTempDist < tempClosestDist:
										tempClosestDist = mostTempDist
										tempStepCoordIndBeforeClosestDist = stepInd-1
										tempIndClosestDist = stepCoords2[stepInd-1][1] + stepCoords2[stepInd-1][4] # 
										tempClosestPoint = copy.deepcopy(stepCoords2[stepInd-1][0])
								
								
								# now check every contour point within the subarea that contained the closest point in preliminary check
								if tempStepCoordIndBeforeClosestDist is not None: # should never be none anyway
									# for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1], min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1]+2, edge2.shape[0])): # guess im just checking the point before the first stepcoord at floor(stepcoordind) and ceil of the stepcoordind for the ending anyway so dont need to be particular about checking all whole integer indices strictly between stepcoords and the stepcoords themselves as float indices
									for tempInd in range(stepCoords2[tempStepCoordIndBeforeClosestDist][1]+1, min(stepCoords2[tempStepCoordIndBeforeClosestDist+1][1] + 1, edge2.shape[0])): # dont see why i put min here but not removing for now even though its definitely pointless
										mostTempDist = getDistance(edge2[tempInd][0][0], testCoord[0], edge2[tempInd][0][1], testCoord[1])
										if mostTempDist < tempClosestDist:
											tempClosestDist = mostTempDist
											tempIndClosestDist = tempInd
											tempClosestPoint = copy.deepcopy(edge2[tempInd][0])
											
								# finally do the check for if closest dist is actually at that coord or if its on line between that and prevcoord or nextcoord
								# then set lastClosestInd and stuff
								if tempIndClosestDist is not None:
									if tempIndClosestDist % 1 == 0:
										if tempIndClosestDist>0:
											ratioOnLine, closePt = closestPt([edge2[int(tempIndClosestDist)-1][0], edge2[int(tempIndClosestDist)][0]], testCoord)
											mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1]) # shouldnt i just check if ratioOnLine is not 0 or 1 or whatever????? @@@@@@@@@@@@@
											if mostTempDist < tempClosestDist:
												tempClosestDist = mostTempDist
												tempIndClosestDist = tempIndClosestDist-1 + ratioOnLine
												tempClosestPoint = copy.deepcopy(closePt)
										if tempIndClosestDist < edge2.shape[0]-1:
											ratioOnLine, closePt = closestPt([edge2[int(tempIndClosestDist)][0], edge2[int(tempIndClosestDist)+1][0]], testCoord)
											mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1])
											if mostTempDist < tempClosestDist:
												tempClosestDist = mostTempDist
												tempIndClosestDist = tempIndClosestDist + ratioOnLine
												tempClosestPoint = copy.deepcopy(closePt)
								
								withinMatchRange = False
								
								if tempClosestDist <= maxAbsDistToCountAsMatch:
									withinMatchRange = True
								if yesPrint:
									print('###################################################################################')
									print(tempClosestDist)
									print(maxAbsDistToCountAsMatch)
									print(lastClosestPoint)
									print(tempClosestPoint)
								
								if (lastClosestPoint is None and not(firstTest)) or tempClosestPoint is None or ((lastClosestPoint is not None and tempClosestPoint is not None) and tempClosestPoint[0] == lastClosestPoint[0] and tempClosestPoint[1] == lastClosestPoint[1]) or not(withinMatchRange):
									failureAmtBefore+=1
								else:
									amtWithoutFailuresBefore+=1
								if failureAmtBefore>=2 and failureAmtBefore/(failureAmtBefore+amtWithoutFailuresBefore) > 0.5: # if decent amount has been tested and the failure rate is over half (if half and half we err to side of assuming matching zone cause its around seed)
									break
								
								lastClosestPoint = copy.deepcopy(tempClosestPoint)
								lastClosestInd = tempIndClosestDist
								stepCoordIndBeforeLastClosestInd = tempStepCoordIndBeforeClosestDist
								firstTest=False
								# ... loop stuff that i never added the first time
							
							if yesPrint:
								print("amtwithoutfailafter, before, minstepsaround: ")
								print(amtWithoutFailuresAfter)
								print(amtWithoutFailuresBefore)
								print(minimumStepsAroundSeedMatch)
								input("press anything...............")
							if amtWithoutFailuresAfter + amtWithoutFailuresBefore < minimumStepsAroundSeedMatch:
								# return
								pass
							else:
							# windowMatches.append([finalVariance, shiftWindowBy, impliedScale]) # whatever other data i will need, maybe totalPts to give more weight to low variance high amount of pts? or just the data for point pairs? or is that even needed? maybe just need implied orientation, scale and seedcoord?
								if True:
									tmpbeugg = []
									tmphhgy = []
									for trackerInd in range(len(trackerList)):
										tmpbeugg.append((window[trackerInd][0], compatibleLists[trackerInd][trackerList[trackerInd]][0]))
										tmphhgy.append((wiggleConstraints[trackerInd]))
									windowMatches.append([finalVariance, shiftWindowBy, 1/impliedScale, maxAbsDistToCountAsMatch, tmpbeugg, tmphhgy]) # hopefully last part is right, assuming maxAbsDistToCountAsMatch is in window space
									windowMatchesAmount+=1
								else:
									windowMatches.append([finalVariance, shiftWindowBy, 1/impliedScale, maxAbsDistToCountAsMatch])
									windowMatchesAmount+=1
								
						toc = time.perf_counter()
						
						totalTimeLastSectionOfSimilarityInstance += toc-tic # use these 2 to calc average
						amountLastSectionOfSimilarityInstance += 1
						
				
					###(new)
					wiggleConstraints[subAreaTracker]=None
					###
					trackerList[subAreaTracker] -= 1
					
					
		
		if len(currentChainDatTree)==0:
			windowSegWildCardTreeCaches.insert(0, [window[0][0], []])
		else:
			# tempCoverage = [currentChainDatTree[0][1]]
			# for tmpI in range(1, len(currentChainDatTree)):
			
			windowSegWildCardTreeCaches.insert(0, [window[0][0], [angleWiggleRoom, currentChainDatTree]]) # this is the wiggle room that every window[0] is queried on (gets all compatible potential segs that have any overlap in this range) and since limitWiggleRoom uses this for firstPair, every wiggle room will be a subset of this so will always be able to apply fast cache skip function
		windowSegWildCardTreeCaches.pop(-1)
		
		windowMatchesDebugLenList.append(len(windowMatches))
		
		if len(windowMatches) <= params['topNWindowMatches']:
			allWindowDat+=windowMatches
		else:
			# tempTopN = []
			tempTopN = windowMatches[:params['topNWindowMatches']]
			# tempTopN.sort()
			highestVal = float('-inf')
			highestInd = None
			for ind in range(len(tempTopN)):
				if tempTopN[ind][0] > highestVal:
					highestInd = ind
					highestVal = tempTopN[ind][0]
			for ind in range(params['topNWindowMatches'], len(windowMatches)):
				if windowMatches[ind][0] < highestVal:
					tempTopN[highestInd] = windowMatches[ind]
					highestVal = windowMatches[ind][0]
					# tempTopN.sort()
					for ind2 in range(len(tempTopN)): # can be more efficient with linked list
						if tempTopN[ind2][0] > highestVal:
							highestInd = ind2
							highestVal = tempTopN[ind2][0]
					
			allWindowDat+=tempTopN
		
		if True:#i < len(rawDat1): # very scuffed
			# debug sanity check
			if rawDat1[i][0][0] != i:
				print('dpokwd')
				exit()
			tempList = [i, rawDat1[i][1]] # rawDatInd, orientation
			
			# since rawDat is ordered we can just do i, i+1 in stepCoords instead of rawDat[i][0][0], [i][0][1]
			tempAngleStart = math.atan2(stepCoords1[i][0][1]-seedCoord1[1], stepCoords1[i][0][0]-seedCoord1[0])
			tempAngleEnd = math.atan2(stepCoords1[i+1][0][1]-seedCoord1[1], stepCoords1[i+1][0][0]-seedCoord1[0]) # window will never be same size as whole edge so dont need % or anything
			tempList.append([tempAngleStart, tempAngleEnd])
			
			tempDistStart = getDistance(seedCoord1[0], stepCoords1[i][0][0], seedCoord1[1], stepCoords1[i][0][1])
			tempDistEnd = getDistance(seedCoord1[0], stepCoords1[i+1][0][0], seedCoord1[1], stepCoords1[i+1][0][1])
			tempList.append([tempDistStart, tempDistEnd])
			
			tempClockwiseCheck = tempList[1] - tempAngleStart
			while tempClockwiseCheck <= -math.pi:
				tempClockwiseCheck+= math.pi*2
			while tempClockwiseCheck > math.pi:
				tempClockwiseCheck-= math.pi*2
			if abs(tempClockwiseCheck-math.pi)<0.0001:
				tempClockwiseCheck=math.pi
			elif abs(tempClockwiseCheck--math.pi)<0.0001:
				tempClockwiseCheck=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
			if tempClockwiseCheck > 0:
				tempList.append(False)
				windowTempClockwiseCheckCache[i]=False
			# elif tempClockwiseCheck < 0:
			elif tempClockwiseCheck <= 0:
				tempList.append(True)
				windowTempClockwiseCheckCache[i]=True
			
			angleSideWindowCache[i]=(tempAngleStart, tempAngleEnd)
			
			window.pop(windowAmount-1)
			window.insert(0, tempList)
			
		
		limitWiggleRoomCalcCaches.insert(0, [window[0][0], {}])
		limitWiggleRoomCalcCaches.pop(-1)
		
	
	# allWindowDat now contains items of the form [finalVariance, shiftWindowBy, impliedScale]
	print("windowMatchesDebugLenList")
	print(windowMatchesDebugLenList)
	
	seedInstanceTopN = params['seedInstanceTopN'] # 3?
	
	seedInstanceTopNSchemata = allWindowDat[:seedInstanceTopN]
	
	
	if len(allWindowDat) > seedInstanceTopN:
		
		highestVal = float('-inf')
		highestInd = None
		for ind in range(len(seedInstanceTopNSchemata)):
			if seedInstanceTopNSchemata[ind][0] > highestVal:
				highestInd = ind
				highestVal = seedInstanceTopNSchemata[ind][0]
		for ind in range(params['seedInstanceTopN'], len(allWindowDat)):
			if allWindowDat[ind][0] < highestVal:
				seedInstanceTopNSchemata[highestInd] = allWindowDat[ind]
				highestVal = allWindowDat[ind][0]
			
				for ind2 in range(len(seedInstanceTopNSchemata)): # can be more efficient with linked list
					if seedInstanceTopNSchemata[ind2][0] > highestVal:
						highestInd = ind2
						highestVal = seedInstanceTopNSchemata[ind2][0]
	
	return seedInstanceTopNSchemata # dont bother returning seeds here i think, just add it to this data wherever this function is called from



def firstSweepCompatibility(testDat, compatCache, params, queryStepCoords, windowStepCoords, queryEdge, windowEdge):
	global debugging2323
	# testDat = [	  (_uniqueSeed1Top5UpToShift)[ [seedPairSchema1Dat...], [seedPairSchema2Dat...], ...   ],			 (_uniqueSeed2Top5UpToShift)[  [seedPairSchema1Dat...], [seedPairSchema2Dat...], ...   ],		   ...		 ]
	global yesPrint
	# sort cache stuff later when i actually know what its gonna look like
	
	# seedInstance/[seedPairSchema1Dat...] = [angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace, ]
	
	
	groupedSeedsIntervals = []
	for ind1, uniqueSeedUpToShift in enumerate(testDat):
		tmpUniqueSeedUpToShiftIntervals = []
		for ind2, seedInstance in enumerate(uniqueSeedUpToShift[1]): # changed from uniqueSeedUpToShift to uniqueSeedUpToShift[1] because i made [0] be unique identifier
			
			windowEdgeID, queryEdgeID, windowPieceID, queryPieceID, windowSeedCoord, querySeedCoord, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace = seedInstance#[:N]
			
			secondaryListInd, seedInstanceInd = roughClosestPoints(queryStepCoords, windowStepCoords, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace, querySeedCoord, windowSeedCoord, compatCache, len(queryStepCoords), params, queryPieceID, windowPieceID, queryEdgeID, windowEdgeID, queryEdge, windowEdge)#, .......)
			# iterate current detail level and != -1 to calc average euclid dist or whatever <<<<<<<< HERE HERE HERE
			# what am i on about average dist? need to get intervals for match/no-match zones
			
			
			# multiple params for the same thing, clean up at the end, window and stepcoord arclength and stuff below should be 1 thing or at least derived from 1 value
			
			# assuming detail level is the amount of evenly spread points taken from stepcoords:
			# ratioOfEdgeBetweenDistVals = compatCache[1][secondaryListInd][seedInstanceInd][-2]/params['']
			
			# treat -1 as not match
			# for closestDist in compatCache[1][secondaryListInd][seedInstanceInd][-1]:
				# think a bit, roughly consecutive matching/non-matching dists(or -1s), minimum size of a matching/non-matching zone, are these 2 different sizes? how to check rough compatibility after? (zones wont fit perfectly most of the time)
			
			# ASSUMING all calced pts are spaced like this
			# which may not be true if the list was built using more than 1 stage and where the desiredDetailLevels dont fit/extend perfectly like a ruler
			step = round(len(compatCache[1][secondaryListInd][seedInstanceInd][-1])/compatCache[1][secondaryListInd][seedInstanceInd][-2]) # if max detail level is ever allowed to be greater than number of stepcoords ill need to handle fairly differently by getting points inbetween stepcoords in windowedge 
			
			stepCoordsPerDistVal = step
			ratioOfEdgePerDistVal = stepCoordsPerDistVal*params['ratioOfEdgeBetweenStepCoords'] # aleady a param but cant remember name clean up at end
			minDistValsForZone = params['minimumRatioOfEdgeForRealMatchingZone']/ratioOfEdgePerDistVal # same as above, looks dumb
			minDistValsForZone = round(minDistValsForZone)
			if minDistValsForZone % 2 == 0: # IF EVEN, make it odd, need the point of interest to be at the center of the window
				minDistValsForZone+=1 # i chose to add one rather than subtract
			
			
			windowZone = 0
			for i in range(minDistValsForZone):
				tmpVal = compatCache[1][secondaryListInd][seedInstanceInd][-1][i*step]
				if tmpVal > maxDiffForMatchInQuerySpace or tmpVal < 0:
					# distValWindow.append(0)
					pass
				else:
					# distValWindow.append(1)
					windowZone+=1
			
			distValIntervals = []
			
			if windowZone >= minDistValsForZone/2: # 50%
				distValIntervals.append([0, None, 1]) # [start, end, matchOrNonMatch]
			else:
				distValIntervals.append([0, None, 0])
			
			aboutToGoToBed = 0
			
			# for i in range(minDistValsForZone, len(compatCache[1][secondaryListInd][seedInstanceInd][-1]), step): # using same iterator as is used in creation/calculation in roughClosestPoints
			for i in range(minDistValsForZone*step, len(compatCache[1][secondaryListInd][seedInstanceInd][-1]), step): # using same iterator as is used in creation/calculation in roughClosestPoints
				# distVal = compatCache[1][secondaryListInd][seedInstanceInd][-1][i]
				
				# discussed in doc
				
				# if sliding window 5%, and distVal is every 2 stepcoords i.e. like 50 or 51 distval then min amount of distVals for zone is 3
				# this would be much easier if values in zones were distinct, but: most values in matching zones will match, but an arbitrary amount of values in non-matching zones may match
				# I wouldnt do less than 3 distVals for zone.
				# do 66% to decide zone for 3, and 50% otherwise
				
				# slide window, then go over again to see if any zones are close enough to merge, e.g. if 66% of window non-matching for 1 step then back to matching, prob worth just merging and
				# assuming it was anomaly
				
				tmpVal = compatCache[1][secondaryListInd][seedInstanceInd][-1][i-minDistValsForZone]
				if not(tmpVal > maxDiffForMatchInQuerySpace or tmpVal < 0):
					windowZone-=1
				
				tmpVal = compatCache[1][secondaryListInd][seedInstanceInd][-1][i]
				if not(tmpVal > maxDiffForMatchInQuerySpace or tmpVal < 0):
					windowZone+=1
				
				tmpBool = 0
				if windowZone >= minDistValsForZone/2:
					tmpBool = 1
				if tmpBool != distValIntervals[-1][2]:
					# distValIntervals[-1][1] = round(i-minDistValsForZone + (minDistValsForZone+1)/2)	# if sliding window is 5 and the majority is now a non-matching zone, assume the flipping point was about currentInd - half the window roughly
					distValIntervals[-1][1] = i-math.floor(step*(minDistValsForZone/2))	 # nvm this is actually used as index so needs to be integer	 # if sliding window is 5 and the majority is now a non-matching zone, assume the flipping point was about currentInd - half the window roughly
					distValIntervals.append([distValIntervals[-1][1]+step, None, 1-distValIntervals[-1][2]]) # ^^ also minDistValsForZone is even so can just divide by 2
					
				aboutToGoToBed = i
				
			distValIntervals[-1][1] = aboutToGoToBed
			
			# min
			deleteIntervalInds = set() # holy cow this is inefficient
			maxDeleteIntervalInd = -1
			intervalInd = 0
			while intervalInd < len(distValIntervals):
				
				if distValIntervals[intervalInd][1] - distValIntervals[intervalInd][0] >= minDistValsForZone*step: # there should be at least 1 or 2 zones the size of the window that can be extended, this is to avoid extending single value windows especially in the case of single point intervals with zone type 0 1 0 1 0 1 0 1 ...
					
					tmpInd = intervalInd-1
					# extendToBackwards = intervalInd
					while tmpInd > maxDeleteIntervalInd: # dont want to check deleted areas
						if distValIntervals[intervalInd][0] - distValIntervals[tmpInd][1] < minDistValsForZone*step: # interval endings close enough to merge
							if distValIntervals[tmpInd][2] == distValIntervals[intervalInd][2]:
								deleteIntervalInds.add(tmpInd)
								
								# extendToBackwards = distValIntervals[tmpInd][0]
								distValIntervals[intervalInd][0] = distValIntervals[tmpInd][0]
						else:
							break
						tmpInd-=1
					
					
					tmpInd = intervalInd+1
					while tmpInd < len(distValIntervals):
						if distValIntervals[tmpInd][0] - distValIntervals[intervalInd][1] < minDistValsForZone*step: # interval endings close enough to merge
							if distValIntervals[tmpInd][2] == distValIntervals[intervalInd][2]:
								deleteIntervalInds.add(tmpInd)
								if tmpInd > maxDeleteIntervalInd: # prob always true
									maxDeleteIntervalInd = tmpInd
								# extendToBackwards = distValIntervals[tmpInd][0]
								distValIntervals[intervalInd][1] = distValIntervals[tmpInd][1]
						else:
							break
						tmpInd+=1
					# if len(deleteIntervalInds) > 0:
						# maxDeleteIntervalInd = deleteIntervalInds[-1] # might look weird since this may be set far back in cases where there were no forward deletions for a while but the large areas naturally also act as stoppages so dont need to handle/account for other cases
					
					# if extended forward then set intervalInd accordingly
					
					# intervalInd
				intervalInd+=1
				if maxDeleteIntervalInd >= intervalInd:
					intervalInd = maxDeleteIntervalInd + 1
				# intervalInd+=1 <<< only do this if isnt set forward by extending an interval @@@
			
			for intervalInd in range(len(distValIntervals)):
				if distValIntervals[intervalInd][1] - distValIntervals[intervalInd][0] < minDistValsForZone*step: # just remove any remaining small zones
					deleteIntervalInds.add(intervalInd)
			
			tempIntervals = []
			for tmpInd in range(len(distValIntervals)): # so bad
				if tmpInd not in deleteIntervalInds:
					tempIntervals.append(distValIntervals[tmpInd])
			distValIntervals = tempIntervals
			
			# now think about how to do final check to get the gist of it, the big zones, to be compared to other schemas, also convert intervals to arclength intervals in case other schemas have different detail level or something?
			
			# the intervals can all be compared to eachother because they are all w.r.t. the same edge <<<<
			if yesPrint:
				print("distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals distValIntervals ")
				print(distValIntervals)
				print("")
				print("")
				print("")
			# exit()
			#for now just storing matching areas and treating rest as non-matching
			# AND intervals now (if werent already) stored in terms of stepCoord index/number
			
			DEBUGGYDEBUG = True
			print("DEBUGGYDEBUG DEBUGGYDEBUG == true @@@@@@@@!!!!!!!!!")
			
			if DEBUGGYDEBUG:
				tempytemptempDEBUG = [] # DELETE DELETE DELETE 
				for interval in distValIntervals:
					if interval[2] == 1:
						tempytemptempDEBUG.append([interval[0], interval[1], interval[2]])
			
			tempIntervals = []
			for interval in distValIntervals:
				if interval[2] == 1:
					tempIntervals.append([interval[0], interval[1]])
			distValIntervals = tempIntervals
			
			matchZoneRatioToTotalEdge = 0
			for tempInterval in distValIntervals:
				matchZoneRatioToTotalEdge+= tempInterval[1] - tempInterval[0]
			matchZoneRatioToTotalEdge = matchZoneRatioToTotalEdge*params['ratioOfEdgeBetweenStepCoords']
			
			
			if DEBUGGYDEBUG:
				tmpUniqueSeedUpToShiftIntervals.append([ind1, ind2, [], distValIntervals, matchZoneRatioToTotalEdge, (secondaryListInd, seedInstanceInd), tempytemptempDEBUG]) 
			else:
				tmpUniqueSeedUpToShiftIntervals.append([ind1, ind2, [], distValIntervals, matchZoneRatioToTotalEdge, (secondaryListInd, seedInstanceInd)]) # testDat inds, compatibleWithInds, intervals
		
		groupedSeedsIntervals.append(tmpUniqueSeedUpToShiftIntervals)#
	
	# check permutations of groupedSeedsIntervals according to doc
	
	# efficient way to do this or just check all? also think of ways to maybe speed up like a flat total % matched to see if they add up to a number that makes sense before going through and checking intervals align roughly
	
	for i in range(len(groupedSeedsIntervals)):
		for j in range(len(groupedSeedsIntervals[i])):
			for k in range(i+1, len(groupedSeedsIntervals)):
				for l in range(groupedSeedsIntervals[k]):
					# check if compatible (not *fully* compatible/complete) i.e. not too much overlap, maybe seeds in the right place? idk
					
					matchZoneRatioToTotalEdge1 = groupedSeedsIntervals[i][j][4]
					matchZoneRatioToTotalEdge2 = groupedSeedsIntervals[k][l][4]
					smallerMatchZoneRatioToTotalEdge = min(matchZoneRatioToTotalEdge1, matchZoneRatioToTotalEdge2)
					maxOverlap = min(params['maxOverlapFor2CompatibleSchemaAsRatioOfSmallerSchema']*smallerMatchZoneRatioToTotalEdge, params['maxOverlapFor2CompatibleSchema'])
					
					amountOfStepCoordsOverlap = checkOverlapIntervalsDistValIntervals(groupedSeedsIntervals[i][j][3], groupedSeedsIntervals[k][l][3])
					ratioOverlapToTotal = amountOfStepCoordsOverlap*params['ratioOfEdgeBetweenStepCoords'] # this can also be changed to just be <= however many stepcoords are 10% then its just comparison not multiplication+comparison
					if ratioOverlapToTotal <= maxOverlap: # 10%/0.1 for now? ANY OTHER CONDITIONS?????
						groupedSeedsIntervals[i][j][2].append((k, l))
						# groupedSeedsIntervals[k][l][2].append((i, j))
	
	# for now just find all fully compatible/complete meta-schemas then take best (lowest total variance/euclid dist diff), in future if this is slow, easily just change order of iteration to roughly efficient i.e. generally start from permutations involving top of each list of schemas, then stop when 1 compatible/complete
	if yesPrint:
		print(groupedSeedsIntervals)
		
		print("]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]")
	
	results = []
	
	for i in range(len(groupedSeedsIntervals)): # PRETTY SURE ABOVE I CAN JUST STORE 1 DIRECTION RATHER THAN STORING COMPATIBLENESS IN BOTH LISTS AND ALSO JUST ITERATE AND COMPARE 1 DIRECTION TO AVOID DUPLICATES AND FASTER, but prob tiny efficiency save compared to rest so do if needed
		for j in range(len(groupedSeedsIntervals[i])): # HERE HERE HERE HERE @@@@@@@@@@@@@@@@@
			# any way to only store data about compatibleness rather than the way its stored above cause can be sparse and only want to iterate schemas with at least 1 compatible
			#and is there any hyper efficient way to store like matrix stuff 0s/1s or nah, also store total % coverage for each schema cause im gonna want to check if compatibles add to 90%+ or whatever
			
			# for now just iterate
			
			if len(groupedSeedsIntervals[i][j][2]) > 0:
				# results = []
				# inefficientTrackerList = []
				# completeOrNah, otherDatIfNeeded = checkCompletenessMetaSchema(groupedSeedsIntervals[i][j][2])
				# completeOrNah, otherDatIfNeeded = checkCompletenessMetaSchema(groupedSeedsIntervals, [(i, j)], results)
				checkCompletenessMetaSchema(groupedSeedsIntervals, [(i, j)], results)
				
			elif len(groupedSeedsIntervals[i][j][2]) == 0: # new
				if groupedSeedsIntervals[i][j][4] >= params["minimumRoughTotalCoverageRatioDebugDeleteLater"]: # dont need to check upper limit for coverage, should be impossible to be > 1
					results.append([[i, j]])
			
	
	for result in results: # metaschema, result is [indpair1, indpair2, ...] of compatible/complete indices for groupedSeedsIntervals[indpair[0]][indpair[1]]
		# compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1][overlapIter]
		# varList item: [intervalStart, intervalEnd, groupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2]
		varList, intervalStep = chooseBestUnion(result, groupedSeedsIntervals, compatCache) # intervalStep here because spaghetti code
		meanCntr = 0
		meanTotal = 0
		for tempInterval in varList:
			for tempInd in range(tempInterval[0], tempInterval[1]+1, intervalStep):
				meanTotal+=compatCache[1][tempInterval[3]][tempInterval[4]][-1][tempInd]
				meanCntr+=1
		meanTotal = meanTotal/meanCntr
		result.append(meanTotal)
	
	results.sort(key=lambda x: x[-1])
	if len(results)>0:
		# print('hiiiiiii')
		# exit()
		return groupedSeedsIntervals, results[0] #?
	else:
		return groupedSeedsIntervals, None

def checkCompletenessMetaSchema(groupedSeedsIntervals, trackerDat, results):
	# print("anything?@")
	# exit()
	# whenchecking if new is compatible with all prev, need to go through whatever trackerDat is and somehow check that all currently included schemas in groupedSeedsIntervals contain (in their [2]) (x,y)
	
	# e.g. for (x,y) in compatList, for (z,w) in groupedSeedsIntervals[x][y], if (z,w) in compatList, for (p,q) in groupedSeedsIntervals[z][w], if (p,q) in compatList and in groupedSeedsIntervals[x][y], i think
	
	
	if len(trackerDat) == 0:
		print("LLLLLLLLKKKKKKKKKKKKK")
		return
	noCompat3 = True
	for index2D in groupedSeedsIntervals[trackerDat[len(trackerDat)-1][0]][trackerDat[len(trackerDat)-1][1]][2]:
		noCompat = False
		for i in range(0, len(trackerDat)-2):
			noCompat2 = True
			for tempIndex2D in groupedSeedsIntervals[trackerDat[i][0]][trackerDat[i][1]][2]:
				if tempIndex2D[0] == index2D[0] and tempIndex2D[1] == index2D[1]:
					noCompat2 = False
					break
			if noCompat2:
				noCompat = True
				break
		if noCompat == False:
			trackerDat.append(index2D)
			completeOrNah, otherDatIfNeeded = checkCompletenessMetaSchema(groupedSeedsIntervals, trackerDat, results)
			# ...?
		# ...?
	
	inefficientTotal = 0
	for indPair in trackerDat:
		inefficientTotal+=groupedSeedsIntervals[indPair[0]][indPair[1]][4]
	
	# if ... complete/compatible, 85-90%+ coverage etc: # @@@@@@@@@@@@@ <<<<<<<<<<<<<<<<<<<<
	if yesPrint:
		print(inefficientTotal-1)
		print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
		# exit()
		print("debudbe delete 298ye")
	
	veryRoughTotalCoverageRatioDebugDeleteLater = params["veryRoughTotalCoverageRatioDebugDeleteLater"] # DELETE LATER, TERRIBLE WAY OF DOING COVERAGE JUST TAKING UNION OF ALL SCHEMAS MATCHING ZONES
	
	if inefficientTotal <= veryRoughTotalCoverageRatioDebugDeleteLater and inefficientTotal >= params["minimumRoughTotalCoverageRatioDebugDeleteLater"]:#0.15: now actually 0.85 and 1.15
		tempListDecouple = []
		for indPair in trackerDat:
			tempListDecouple.append(indPair)
		results.append(tempListDecouple) # MAYBE/PROBABLY ADD data here like actual value of coverage and stuff or maybe the rest stuff can be calced after somewhere else
	
	
	trackerDat.pop()
	
	# where/how am i storing/returning fully compatible schemata??? at each dead end it should be evaluated (to make sure fully compatible e.g. 90%+ coverage etc) and stored if compatible
	# need to pop off list at some point when dead end or whatever and need to make it back to trackerDat=[] at end
	
	return


def chooseBestUnion(metaSchemaIndPairs, groupedSeedsIntervals, compatCache):
	
	varList = []
	intervalStep = 1
	for indpair in metaSchemaIndPairs:
		list2 = groupedSeedsIntervals[indpair[0]][indpair[1]][3]
		
		secondaryListIndInterval2, seedInstanceIndInterval2 = groupedSeedsIntervals[indpair[0]][indpair[1]][5]
		intervalStep = int(round(len(compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1])/compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-2]))
		
		
		varList = chooseBestUnionIter(varList, list2, (indpair[0], indpair[1]), groupedSeedsIntervals, intervalStep, secondaryListIndInterval2, seedInstanceIndInterval2, compatCache)
	
	return varList, intervalStep # passing intervalStep here because spaghetti code



def chooseBestUnionIter(list1, list2, list2GroupedSeedsIntevalsIndPair, groupedSeedsIntervals, intervalStep, secondaryListIndInterval2, seedInstanceIndInterval2, compatCache): # assume any schemas being compared with this have same step amount and total amount so intervals and steps and everything are coherent/in-phase
	# groupedSeedsIntervals[i][j][3]
	
	#list1 is best out of union/overlap, items [interval[0], interval[1], indPair, ..]
	if len(list1) == 0:
		for interval in list2:
			list1.append([interval[0], interval[1], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
		return list1
	# newList = []
	tempIntervals = []
	totalOverlapAmt = 0
	
	i = 0
	j = 0
	
	while i < len(list1) and j < len(list2):
		interval1 = list1[i]
		interval2 = list2[j]
		
		if interval1[1] < interval2[1]:
			i+=1
		else:
			j+=1
		
		# if overlap, dont just iterate each step within intervals and take best cause that could fragment, instead find best single point/index to slice and merge, or if one is subinterval of other just delete if its worse etc
		# ^^ nvm, for now just split as needed as long as more than a single point interval size results
		if interval1[1] >= interval2[0] and interval2[1] >= interval1[0]:########## \\/\/\/\/\//
			end_pts = sorted([interval1[0], interval1[1], interval2[0], interval2[1]])
			
			if end_pts[0] == interval1[0]:
				
				# if interval2[1] <= interval1[1]: # interval2 subinterval of interval1
				consecutiveOppositeIntervalAmt = 0
				currIntervalNum = 1 # 1 or 2, suchbad code
				
				# add secondaryind and other ind to items in tempIntervals or newlist, also add tempIntervals to newList @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
				tempIntervals.append([interval1[0], interval2[0]-intervalStep, interval1[2], interval1[3], interval1[4]]) # using interval1[0] as placeholder instead of -1 incase its actually possible or messes up and doesnt get updated from -1
				
				if interval1[0] == interval2[0]:
					# if EUCLID DIST FOR INTERVAL2[0] POINT IS SMALLER THAN THE METASCHEMA THAT INTERVAL1[0] IS FROM: @@@@@@@@
					if compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1][interval2[0]] < compatCache[1][secondaryListIndInterval1][seedInstanceIndInterval1][-1][interval1[0]]:
						currIntervalNum = 2
						tempIntervals[0] = [interval2[0], interval2[0], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2]
					else:
						tempIntervals[0][1]+=intervalStep
				
				overlapIter = tempIntervals[0][1]+intervalStep
				
				while overlapIter <= min(interval1[1], interval2[1]):
					# if EUCLID DIST FOR INTERVAL2[0] POINT IS SMALLER THAN THE METASCHEMA THAT INTERVAL1[0] IS FROM: @@@@@@@@
					if compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1][overlapIter] < compatCache[1][secondaryListIndInterval1][seedInstanceIndInterval1][-1][overlapIter]:
						if currIntervalNum == 1:
							consecutiveOppositeIntervalAmt+=1
							if consecutiveOppositeIntervalAmt==2:
								tempIntervals[-1][1]-=intervalStep
								tempIntervals.append([overlapIter-intervalStep, overlapIter, list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
								currIntervalNum = 2
								consecutiveOppositeIntervalAmt=0
						else:
							consecutiveOppositeIntervalAmt=0
							tempIntervals[-1][1]=overlapIter
					else:
						if currIntervalNum == 2:
							consecutiveOppositeIntervalAmt+=1
							if consecutiveOppositeIntervalAmt==2:
								tempIntervals[-1][1]-=intervalStep
								tempIntervals.append([overlapIter-intervalStep, overlapIter, interval1[2], interval1[3], interval1[4]])
								currIntervalNum = 1
								consecutiveOppositeIntervalAmt=0
						else:
							consecutiveOppositeIntervalAmt=0
							tempIntervals[-1][1]=overlapIter
					overlapIter+=intervalStep
				if interval2[1] <= interval1[1]:
					if currIntervalNum == 1:
						tempIntervals[-1][1] = interval1[1]
					else:
						if interval1[1] - interval2[1] > intervalStep:
							tempIntervals.append([interval2[1]+intervalStep, interval1[1], interval1[2], interval1[3], interval1[4]])
				else:
					if currIntervalNum == 2:
						tempIntervals[-1][1] = interval2[1]
					else:
						if interval2[1] - interval1[1] > intervalStep:
							tempIntervals.append([interval1[1]+intervalStep, interval2[1], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
				
			elif end_pts[0] == interval2[0]:
				
				consecutiveOppositeIntervalAmt = 0
				currIntervalNum = 2 # 1 or 2, suchbad code
				
				tempIntervals.append([interval2[0], interval1[0]-intervalStep, list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2]) # using interval1[0] as placeholder instead of -1 incase its actually possible or messes up and doesnt get updated from -1
				
				if interval2[0] == interval1[0]:
					# if EUCLID DIST FOR INTERVAL1[0] POINT IS SMALLER THAN THE METASCHEMA THAT INTERVAL2[0] IS FROM: @@@@@@@@
					if compatCache[1][secondaryListIndInterval1][seedInstanceIndInterval1][-1][interval1[0]] < compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1][interval2[0]]:
						currIntervalNum = 1
						tempIntervals[0] = [interval1[0], interval1[0], interval1[2], interval1[3], interval1[4]]
					else:
						tempIntervals[0][1]+=intervalStep
				
				overlapIter = tempIntervals[0][1]+intervalStep
				
				while overlapIter <= min(interval1[1], interval2[1]):
					# if EUCLID DIST FOR INTERVAL1[0] POINT IS SMALLER THAN THE METASCHEMA THAT INTERVAL2[0] IS FROM: @@@@@@@@
					if compatCache[1][secondaryListIndInterval1][seedInstanceIndInterval1][-1][overlapIter] < compatCache[1][secondaryListIndInterval2][seedInstanceIndInterval2][-1][overlapIter]:
						if currIntervalNum == 2:
							consecutiveOppositeIntervalAmt+=1
							if consecutiveOppositeIntervalAmt==2:
								tempIntervals[-1][1]-=intervalStep
								tempIntervals.append([overlapIter-intervalStep, overlapIter, interval1[2], interval1[3], interval1[4]])
								currIntervalNum = 1
								consecutiveOppositeIntervalAmt=0
						else:
							consecutiveOppositeIntervalAmt=0
							tempIntervals[-1][1]=overlapIter
					else:
						if currIntervalNum == 1:
							consecutiveOppositeIntervalAmt+=1
							if consecutiveOppositeIntervalAmt==2:
								tempIntervals[-1][1]-=intervalStep
								tempIntervals.append([overlapIter-intervalStep, overlapIter, list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
								currIntervalNum = 2
								consecutiveOppositeIntervalAmt=0
						else:
							consecutiveOppositeIntervalAmt=0
							tempIntervals[-1][1]=overlapIter
					overlapIter+=intervalStep
				if interval1[1] <= interval2[1]:
					if currIntervalNum == 2:
						tempIntervals[-1][1] = interval2[1]
					else:
						if interval2[1] - interval1[1] > intervalStep:
							tempIntervals.append([interval1[1]+intervalStep, interval2[1], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
				else:
					if currIntervalNum == 1:
						tempIntervals[-1][1] = interval1[1]
					else:
						if interval1[1] - interval2[1] > intervalStep:
							tempIntervals.append([interval2[1]+intervalStep, interval1[1], interval1[2], interval1[3], interval1[4]])
			
		else:
			if interval1[0] > interval2[1]: # interval1 already formatted
				tempIntervals.append([interval2[0], interval2[1], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
				tempIntervals.append(interval1)
				
			elif interval2[0] > interval1[1]:
				tempIntervals.append(interval1)
				tempIntervals.append([interval2[0], interval2[1], list2GroupedSeedsIntevalsIndPair, secondaryListIndInterval2, seedInstanceIndInterval2])
			
	
	return tempIntervals

def checkOverlapIntervalsDistValIntervals(list1, list2):
	
	totalOverlapAmt = 0
	
	i = 0
	j = 0
	
	while i < len(list1) and j < len(list2):
		interval1 = list1[i]
		interval2 = list2[j]
		if interval1[1] < interval2[1]:
			i+=1
		else:
			j+=1
		
		if interval1[1] >= interval2[0] and interval2[1] >= interval1[0]:
			end_pts = sorted([interval1[0], interval1[1], interval2[0], interval2[1]])
			overlap = [end_pts[1], end_pts[2]]
			overlapAmt = overlap[1] - overlap[0] # 0 if they just share an ending because that shouldn't count as overlap
			totalOverlapAmt+=overlapAmt
	
	return totalOverlapAmt

def roughClosestPoints(queryStepCoords, windowStepCoords, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace, querySeedCoord, windowSeedCoord, compatCache, desiredDetailLevel, params, queryPieceID, windowPieceID, queryEdgeID, windowEdgeID, queryEdge, windowEdge):#, .......):
	# params['maxDetailLevel'] == len(stepCoords) for now
	
	# COMPATCACHE [-1] NEEDS TO BE THE DIST LIST, [-2] NEEDS TO BE DETAIL LEVEL @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
	
	# not sure if this is already somewhere or if it should be somewhere else but for now:
	if len(compatCache[0])-1 < max(windowPieceID, queryPieceID):
		for i in range(len(compatCache[0]), max(windowPieceID, queryPieceID)+1):
			compatCache[0].append([[], [], [], []])
	
	
	# exists = False
	secondaryListInd = None
	for item in compatCache[0][windowPieceID][windowEdgeID]:
		if len(item) >= 2 and item[0] == queryPieceID and item[1] == queryEdgeID:
			# exists=True
			secondaryListInd = item[2]
			break
	
	# if not(exists):
	if secondaryListInd is None:
		compatCache[1].append([])
		secondaryListInd = len(compatCache[1])-1
		compatCache[0][windowPieceID][windowEdgeID].append([queryPieceID, queryEdgeID, secondaryListInd])
		compatCache[0][queryPieceID][queryEdgeID].append([windowPieceID, windowEdgeID, secondaryListInd])
	seedInstanceInd = None
	queryWindowFlipped = False
	for ind, item in enumerate(compatCache[1][secondaryListInd]): #[pieceID_query, pieceID_window, querySeedCoord, windowSeedCoord, orientationQueryMinusWindow, estimatedScaleQueryOverWindow, …, otherseedinstanceDat…, …, detailLevel, euclidDistDat]
		if item[4] == angleDiffQueryMinusWindow and item[5] == estimatedScaleQueryOverWindow:
			if item[0] == queryPieceID and item[1] == windowPieceID:
				if item[2][0] == querySeedCoord[0] and item[2][1] == querySeedCoord[1] and item[3][0] == windowSeedCoord[0] and item[3][1] == windowSeedCoord[1]:
					seedInstanceInd=ind
			elif item[1] == queryPieceID and item[0] == windowPieceID:
				if item[3][0] == querySeedCoord[0] and item[3][1] == querySeedCoord[1] and item[2][0] == windowSeedCoord[0] and item[2][1] == windowSeedCoord[1]:
					seedInstanceInd=ind
					queryWindowFlipped = True # DONT THINK THIS WOULD ACTUALLY HAPPEN BECAUSE angleDiffQueryMinusWindow WOULD BE NEGATIVE AND estimatedScaleQueryOverWindow WOULD BE 1/estimatedScaleQueryOverWindow ??
	
	if seedInstanceInd is None: # this seed instance (unique schema and seedpair) hasnt been tested yet
		compatCache[1][secondaryListInd].append([queryPieceID, windowPieceID, querySeedCoord, windowSeedCoord, angleDiffQueryMinusWindow, estimatedScaleQueryOverWindow, maxDiffForMatchInQuerySpace, queryEdgeID, windowEdgeID, 0, []]) # detailLevel for now is amount of entries so here itll be len(stepCoords) since im doing all for prelim sweep
		seedInstanceInd = len(compatCache[1][secondaryListInd])-1
		for i in range(params['maxDetailLevel']):
			compatCache[1][secondaryListInd][-1][-1].append(-1)
	elif compatCache[1][secondaryListInd][seedInstanceInd][-2] >= desiredDetailLevel:
		return secondaryListInd, seedInstanceInd
	
	# if compatCache[1][secondaryListInd]
	
	step = round(len(queryStepCoords)/desiredDetailLevel) # if max detail level is ever allowed to be greater than number of stepcoords ill need to handle fairly differently by getting points inbetween stepcoords in windowedge 
	
	sinP1 = math.sin(angleDiffQueryMinusWindow)
	cosP1 = math.cos(angleDiffQueryMinusWindow)
	
	roughNeighbourhoodLimit = math.floor(len(queryStepCoords)/8)
	
	# print(windowEdge)
	# print(windowStepCoords)
	# exit()
	
	for i in range(0, len(windowStepCoords), step):
		
		testCoord = windowStepCoords[i][0]
		testCoord = [testCoord[0] - windowSeedCoord[0], testCoord[1] - windowSeedCoord[1]]
		testCoord = [testCoord[0]*cosP1 - testCoord[1]*sinP1, testCoord[0]*sinP1 + testCoord[1]*cosP1]
		testCoord = [testCoord[0]*estimatedScaleQueryOverWindow, testCoord[1]*estimatedScaleQueryOverWindow]
		#
		testCoordLineM = None
		if testCoord[0] != 0:
			testCoordLineM = testCoord[1]/testCoord[0] # here cause currently testcoord is centered around origin so dont need to minus seed coord again
		
		
		testCoord[0]+=querySeedCoord[0]
		# print(testCoord[1])
		# print(queryStepCoords[1])
		testCoord[1]+=querySeedCoord[1]
		
		tempSign1 = None
		tempSign2 = None
		tempSign1Perpen = None
		tempSign2Perpen = None
		
		testCoordLineC = None
		
		if testCoordLineM is None:
			testCoordLineC = testCoord[0]
		else:
			testCoordLineC = testCoord[1]-testCoordLineM*testCoord[0]
		
		testCoordLinePerpenM = None
		testCoordLinePerpenC = None
		
		if testCoordLineM is None:
			testCoordLinePerpenM = 0
			testCoordLinePerpenC = testCoord[1]
		else:
			if testCoordLineM == 0:
				# testCoordLinePerpenM=None
				testCoordLinePerpenC = testCoord[0]
			else:
				testCoordLinePerpenM = -1/testCoordLineM
				testCoordLinePerpenC = testCoord[1]-testCoordLinePerpenM*testCoord[0]
		
		crossesList = []
		crossesPerpenList = []
		
		# for j in range(len(queryStepCoords)-1):
		for j in range(max(0, i-roughNeighbourhoodLimit), min(len(queryStepCoords)-1, i+roughNeighbourhoodLimit)):
			startPt = queryStepCoords[j][0]
			endPt = queryStepCoords[j+1][0]
			if testCoordLineM is None:
				tempSign1 = startPt[0] - testCoordLineC
				tempSign2 = endPt[0] - testCoordLineC
			else:
				tempSign1 = startPt[1] - testCoordLineM*startPt[0] - testCoordLineC
				tempSign2 = endPt[1] - testCoordLineM*endPt[0] - testCoordLineC
			
			if testCoordLinePerpenM is None:
				tempSign1Perpen = startPt[0] - testCoordLinePerpenC
				tempSign2Perpen = endPt[0] - testCoordLinePerpenC
			else:
				tempSign1Perpen = startPt[1] - testCoordLinePerpenM*startPt[0] - testCoordLinePerpenC
				tempSign2Perpen = endPt[1] - testCoordLinePerpenM*endPt[0] - testCoordLinePerpenC
			
			if ((tempSign1>=0) or (tempSign2>=0)) and ((tempSign1<=0) or (tempSign2<=0)):
				crossesList.append(j)
			if ((tempSign1Perpen>=0) or (tempSign2Perpen>=0)) and ((tempSign1Perpen<=0) or (tempSign2Perpen<=0)):
				crossesPerpenList.append(j)
			
		if len(crossesList) > 1: # get the subarea where one of the endpoints is the closest out of all subareas that cross the line
			closestDist = float('inf')
			closestInd = None
			for ind in crossesList:
				# tempDist = getDistance(querySeedCoord[0], queryStepCoords[ind][0][0], querySeedCoord[1], queryStepCoords[ind][0][1]) what was I thinking putting querySeedCoord here..?
				tempDist = getDistance(testCoord[0], queryStepCoords[ind][0][0], testCoord[1], queryStepCoords[ind][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind
				# tempDist = getDistance(querySeedCoord[0], queryStepCoords[ind+1][0][0], querySeedCoord[1], queryStepCoords[ind+1][0][1])
				tempDist = getDistance(testCoord[0], queryStepCoords[ind+1][0][0], testCoord[1], queryStepCoords[ind+1][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind # doesnt rly matter i think if ind or ind+1 we just care which subarea not which ending of subarea
			crossesList = [closestInd]
		if len(crossesPerpenList) > 1:
			closestDist = float('inf')
			closestInd = None
			for ind in crossesPerpenList:
				# tempDist = getDistance(querySeedCoord[0], queryStepCoords[ind][0][0], querySeedCoord[1], queryStepCoords[ind][0][1])
				tempDist = getDistance(testCoord[0], queryStepCoords[ind][0][0], testCoord[1], queryStepCoords[ind][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind
				# tempDist = getDistance(querySeedCoord[0], queryStepCoords[ind+1][0][0], querySeedCoord[1], queryStepCoords[ind+1][0][1])
				tempDist = getDistance(testCoord[0], queryStepCoords[ind+1][0][0], testCoord[1], queryStepCoords[ind+1][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind # doesnt rly matter i think if ind or ind+1 we just care which subarea not which ending of subarea
			crossesPerpenList = [closestInd]
		
		
		# check around these ind subarea for closest point, FOR NOW 1 FULL SUBAREA BEFORE AND AFTER, prob too much maybe or too little if stepArcLength is small
		#terrible code for next like 40 lines
		startInd1 = None
		endInd1 = None
		startInd2 = None
		endInd2 = None
		if len(crossesList) == 1: # can be 0 if never crosses
			# startInd = None
			# endInd = None
			if crossesList[0] > 0:
				startInd1 = queryStepCoords[crossesList[0]-1][1]
			else:
				startInd1 = queryStepCoords[crossesList[0]][1]
			if crossesList[0] < len(queryStepCoords)-2:
				endInd1 = queryStepCoords[crossesList[0]+2][1]
			else:
				endInd1 = queryStepCoords[crossesList[0]+1][1]
			# for ind in range(startInd, endInd+1):
				
		if len(crossesPerpenList) == 1:
			# startInd = None
			# endInd = None
			if crossesPerpenList[0] > 0:
				startInd2 = queryStepCoords[crossesPerpenList[0]-1][1]
			else:
				startInd2 = queryStepCoords[crossesPerpenList[0]][1]
			if crossesPerpenList[0] < len(queryStepCoords)-2:
				endInd2 = queryStepCoords[crossesPerpenList[0]+2][1]
			else:
				endInd2 = queryStepCoords[crossesPerpenList[0]+1][1]
		
		if startInd1 is not None and startInd2 is not None:
			if startInd1 < endInd2 and endInd1 >= startInd2:
				endInd1 = endInd2
				startInd2=None
				endInd2=None
			elif startInd2 < endInd1 and endInd2 >= startInd1:
				startInd1 = startInd2
				# endInd1 = 
				startInd2=None
				endInd2=None
		elif startInd1 is None and startInd2 is not None:
			startInd1 = startInd2
			endInd1 = endInd2
			startInd2=None
			endInd2=None
		
		closestDist = float('inf')
		closestInd = None
		if startInd1 is not None:
			
			
			for ind in range(startInd1, endInd1+1):
				tempDist = getDistance(testCoord[0], queryEdge[ind][0][0], testCoord[1], queryEdge[ind][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind
			
		
		if startInd2 is not None:
			# closestDist = float('inf')
			# closestInd = None
			
			for ind in range(startInd2, endInd2+1):
				tempDist = getDistance(testCoord[0], queryEdge[ind][0][0], testCoord[1], queryEdge[ind][0][1])
				if tempDist < closestDist:
					closestDist = tempDist
					closestInd = ind
			
		if closestInd is not None:
			if closestInd < queryEdge.shape[0]-1:# and getDistance(queryEdge[closestInd][0], queryEdge[closestInd+1][0], queryEdge[closestInd][1], queryEdge[closestInd+1][1]) > 
				ratioOnLine, closePt = closestPt([queryEdge[closestInd][0], queryEdge[closestInd+1][0]], querySeedCoord)
				mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1]) # shouldnt i just check if ratioOnLine is not 0 or 1 or whatever????? @@@@@@@@@@@@@
				if mostTempDist < closestDist:
					closestDist = mostTempDist
					# tempClosestPoint = closePt # unneeded for now
			if closestInd > 0:
				ratioOnLine, closePt = closestPt([queryEdge[closestInd-1][0], queryEdge[closestInd][0]], querySeedCoord)
				mostTempDist = getDistance(testCoord[0], closePt[0], testCoord[1], closePt[1]) # shouldnt i just check if ratioOnLine is not 0 or 1 or whatever????? @@@@@@@@@@@@@
				if mostTempDist < closestDist:
					closestDist = mostTempDist
					# tempClosestPoint = closePt # unneeded for now
			# put in a list or store somehow
			compatCache[1][secondaryListInd][seedInstanceInd][-1][i] = closestDist
			# compatCache[0][windowPieceID][windowEdgeID].append([queryPieceID, queryEdgeID, len(compatCache[1])-1])
			# compatCache[0][queryPieceID][queryEdgeID].append([windowPieceID, windowEdgeID, len(compatCache[1])-1])
		else:
			# instead of closest dist store None, this may be normal/expected e.g. if theres excess tail at the start/end of an edge but also potentially bad if there definitely should be closest dist e.g. at some point in the middle, might need to count these, can prob ignore a few anomolies but if too many i should skip the comparison
			
			pass # leave as -1 for now? or set to something else to signify it failing the test? @@@@@@@@@@@@@@@@@@
		
	compatCache[1][secondaryListInd][seedInstanceInd][-2] = desiredDetailLevel
	return secondaryListInd, seedInstanceInd



limwigroomFast=0
limwigroomSlow=0
limwigroomSlowBeforeFirstPair=0
def limitWiggleRoom(wiggleConstraints, currWindowInd, potentialCache, trackerList, compatibleLists, stepCoords2, rawDat2, seedCoord2, window, stepCoords1, rawDat1, seedCoord1, firstPair=None, debug3=False, specificWindowSegLimitWiggleRoomCalcCache=None, limWigRoomBigSkipDat=None, limWigRoomFastConstraint=None, limWigRoomFastDat=None, rawDatIndPairWhenWiggleNotPreConstrained=None):
	global limwigroomFast
	global limwigroomSlow
	global limwigroomSlowBeforeFirstPair
	global yesPrint
	
	if limWigRoomBigSkipDat is not None:
		wiggle = [limWigRoomFastConstraint[0], limWigRoomFastConstraint[1]]
		if wiggle[0] < -math.pi or wiggle[0] > math.pi or wiggle[1] < -math.pi or wiggle[1] > math.pi:
			print("you forgot to do if limWigRoomFastConstraint[0] < -math.pi, limWigRoomFastConstraint[0]+=2*math.pi etc idiot")
			exit()
		
		limwigroomFast+=1
		
		
		##################
		if rawDatIndPairWhenWiggleNotPreConstrained is not None:
			leftWindowRawDatInd, leftPotentialRawDatInd, rightWindowRawDatInd, rightPotentialRawDatInd = rawDatIndPairWhenWiggleNotPreConstrained
			
			
			potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise = None, None, None, None, None, None
			if rightPotentialRawDatInd in potentialCache:
				potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise = potentialCache[rightPotentialRawDatInd]
			else:
				if True:
					print("this should never happen")
					exit()
				# mid to previous window lineseg ending
				tempPotentialClockwise = None
				potentialOrientation = rawDat2[rightPotentialRawDatInd][1]
				# potentialOrientationSeedToP1 = compatibleLists[-1][trackerList[-1]][2]
				
				
				tempCoordPotentialStart = stepCoords2[rawDat2[rightPotentialRawDatInd][0][0]][0]
				tempCoordPotentialEnd = stepCoords2[rawDat2[rightPotentialRawDatInd][0][1]][0]
				
				potentialOrientationSeedToP1 = math.atan2(tempCoordPotentialStart[1] - seedCoord2[1], tempCoordPotentialStart[0] - seedCoord2[0])
				potentialOrientationSeedToP2 = math.atan2(tempCoordPotentialEnd[1] - seedCoord2[1], tempCoordPotentialEnd[0] - seedCoord2[0])
				####### # THIS AND OTHER CLOCKWISE TESTS CAN BE CHANGED TO SIMPLE LINE +/- CHECK OR WHATEVER, SIMILAR TO DEFECT STUFF
				
				tempLeftOrRight = potentialOrientation - potentialOrientationSeedToP1
				while tempLeftOrRight <= -math.pi:
					tempLeftOrRight+= math.pi*2
				while tempLeftOrRight > math.pi:
					tempLeftOrRight-= math.pi*2
				if tempLeftOrRight < 0:
					tempPotentialClockwise = True
				elif tempLeftOrRight > 0:
					tempPotentialClockwise = False
				
				potentialCache[rightPotentialRawDatInd] = [potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise]
			
			skipThisSchema = False
			tempWiggle=[]
			if window[currWindowInd][4] == False:
				if tempPotentialClockwise == False:
					# both anticlockwise
					# first limit wiggle room based on max wiggle of potential and window seg with no constraints from previous window/potential segs
					
					# (since both anticlockwise, get wiggle boundaries by setting window[0] to potential[1] and window[1] to potential[0])
					#window[1] first since [0] pairing is more anticlockwise shifted
					tempWiggle0 = potentialOrientationSeedToP1 - window[currWindowInd][2][1]
					tempWiggle1 = potentialOrientationSeedToP2 - window[currWindowInd][2][0]
					tempWiggle = [tempWiggle0, tempWiggle1]
				else:
					# window anticlockwise, tempseg clockwise
					# window[1] and temppotential[1] -> window[0] and temppotential[0]
					tempWiggle0 = potentialOrientationSeedToP2 - window[currWindowInd][2][1]
					tempWiggle1 = potentialOrientationSeedToP1 - window[currWindowInd][2][0]
					tempWiggle = [tempWiggle0, tempWiggle1]
			else:
				if tempPotentialClockwise == False:
					# window clockwise tempseg anticlockwise
					# window[0] and temppotential[0] -> window[1] and temppotential[1]
					tempWiggle0 = potentialOrientationSeedToP1 - window[currWindowInd][2][0]
					tempWiggle1 = potentialOrientationSeedToP2 - window[currWindowInd][2][1]
					tempWiggle = [tempWiggle0, tempWiggle1]
				else:
					# both clockwise
					# window[0] and temppotential[1] -> window[1] and temppotential[0]
					tempWiggle0 = potentialOrientationSeedToP2 - window[currWindowInd][2][0]
					tempWiggle1 = potentialOrientationSeedToP1 - window[currWindowInd][2][1]
					tempWiggle = [tempWiggle0, tempWiggle1]
			
			
			if tempWiggle[0] <= -math.pi:
				tempWiggle[0]+= math.pi*2
			elif tempWiggle[0] > math.pi:
				tempWiggle[0]-= math.pi*2
			if tempWiggle[1] <= -math.pi:
				tempWiggle[1]+= math.pi*2
			elif tempWiggle[1] > math.pi:
				tempWiggle[1]-= math.pi*2
			if abs(tempWiggle[0]-math.pi)<0.0001:
				tempWiggle[0]=math.pi
			elif abs(tempWiggle[0]--math.pi)<0.0001:
				tempWiggle[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
			if abs(tempWiggle[1]-math.pi)<0.0001:
				tempWiggle[1]=math.pi
			elif abs(tempWiggle[1]--math.pi)<0.0001:
				tempWiggle[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

			if tempWiggle[0] <= tempWiggle[1]: # intuitive
				if wiggle[0] <= wiggle[1]:
					# if tempWiggle[0] > wiggle[1] or tempWiggle[1] < wiggle[0]:
						# skipThisSchema=True
					# else:
					wiggleStart = max(wiggle[0], tempWiggle[0])
					wiggleEnd = min(wiggle[1], tempWiggle[1])
					if wiggleStart>wiggleEnd:
						skipThisSchema=True
					else:
						wiggle = [wiggleStart, wiggleEnd]
					# wiggle = [wiggleStart, wiggleEnd]
				else:
					if tempWiggle[1] >= wiggle[0]:# or tempWiggle[1] <= wiggle[1]:
						wiggleStart = max(tempWiggle[0], wiggle[0])
						wiggleEnd = tempWiggle[1]
						wiggle = [wiggleStart, wiggleEnd] # tempWiggle.copy() # tempwiggle is a subset of wiggle
					elif tempWiggle[0] <= wiggle[1]: #tempWiggle[1] < wiggle[0] and tempWiggle[0] > wiggle[1]:
						# skipThisSchema = True
						wiggleStart = tempWiggle[0]
						wiggleEnd = min(tempWiggle[1], wiggle[1])
						wiggle = [wiggleStart, wiggleEnd]
					else:
						# if tempWiggle[1] < wiggle[0]:
						# if tempWiggle[0] < wiggle[1]: # equivalent to above but more readable
							# wiggle[0] = tempWiggle[0]
						# elif tempWiggle[1] > wiggle[0]: # we assume we cant have both cases because we will never have wiggle span > 180 or anything
							# wiggle[1] = tempWiggle[1]
						skipThisSchema = True
			else:
				if wiggle[0] <= wiggle[1]:
					if wiggle[1]>=tempWiggle[0]:
						wiggleStart = max(wiggle[0], tempWiggle[0])
						wiggleEnd = wiggle[1]
						wiggle = [wiggleStart, wiggleEnd]
					
					elif wiggle[0] <= tempWiggle[1]:
						wiggleStart = wiggle[0]
						wiggleEnd = min(wiggle[1], tempWiggle[1])
						wiggle = [wiggleStart, wiggleEnd]
					else:# tempWiggle[0] > wiggle[0] and tempWiggle[0] <= wiggle[1]:
						skipThisSchema = True
				else:
					# both cross 0 so will always have some overlap
					wiggleStart = max(wiggle[0], tempWiggle[0])
					wiggleEnd = min(wiggle[1], tempWiggle[1])
					wiggle = [wiggleStart, wiggleEnd]
			
			if skipThisSchema:
				wiggle=[]
				return wiggle
			
			if rightPotentialRawDatInd == leftPotentialRawDatInd: # constrained by shifting the 1 potential segment around the middle point between the 2 window segments, same as the intersection of shifting potential seg around left window seg, and shifting potential seg around right window seg
				return wiggle
			
		
		eq_lambda, eq_lambda_ambiguous, required_wiggle, required_wiggle_ambiguous, realityLambda, eq_g, eq_h, eq_h2, eq_p, eq_alpha, eq_gamma = limWigRoomBigSkipDat
		
		if eq_h is None:
			print("hânggg????")
			wiggle=[]
			return wiggle
		
		
		if eq_lambda is None: # sqrt was <0 so no roots so either all or none
			angleInWiggleRange = None
			if wiggle[1] == wiggle[0]:
				angleInWiggleRange = wiggle[0]
			elif wiggle[1] > wiggle[0]:
				angleInWiggleRange = (wiggle[1] + wiggle[0])/2
			else:
				tempEnd = wiggle[1]+math.pi*2
				angleInWiggleRange = (tempEnd+wiggle[0])/2
				if angleInWiggleRange>math.pi:
					angleInWiggleRange-=math.pi*2
			newLambda =	 angleInWiggleRange + realityLambda
			if newLambda <= -math.pi:
				newLambda+= math.pi*2
			elif newLambda > math.pi:
				newLambda-= math.pi*2
			if abs(newLambda-math.pi)<0.0001:
				newLambda=math.pi
			elif abs(newLambda--math.pi)<0.0001:
				newLambda=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
			if (newLambda + eq_alpha)%(math.pi)!=0 and (eq_p - newLambda + eq_gamma)%(math.pi)!=0:
				# tempDiv1 = math.sin(newLambda + eq_alpha)
			# divZeroFlag = False
			# if tempDiv1!=0:
				# tempDiv2 = math.sin(newLambda-eq_p + eq_gamma)
				# if tempDiv2 != 0:
				# testRatio = (eq_g*math.sin(newLambda-eq_p))/(tempDiv2*eq_h2) + (eq_g*math.sin(newLambda))/(tempDiv1*eq_h)
				tempDiv1 = math.sin(newLambda + eq_alpha)
				
				tempDiv2 = math.sin(eq_p-newLambda + eq_gamma)
				
				testRat1 = (eq_g*math.sin(eq_p-newLambda))/(tempDiv2*eq_h2)
				testRat2 = (eq_g*math.sin(newLambda))/(tempDiv1*eq_h)
				testRatio = testRat1 + testRat2
				# if testRatio <= 1:
				if testRatio < 1 or testRat1 > 1 or testRat2 > 1: # NEW, same as other notes
					wiggle=wiggle
				else:
					wiggle=[]
					if yesPrint:
						print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
			else:
				wiggle=[]
				print("HOW IS THIS PRINTING???30928444")
		else:
			
			rareSkipFlag = False
			splitDat = [] # [angle to test,	 [newWiggle if <1],	 [newWiggle if >1]	]  # newWiggle so lazy/bad coding but would rather do that than have 50 levels of conditionals for each case/duplicate code, its for readability
			if wiggle[1] > wiggle[0]:
				if required_wiggle >= wiggle[0] and required_wiggle <= wiggle[1] and required_wiggle_ambiguous >= wiggle[0] and required_wiggle_ambiguous <= wiggle[1]: # new, large and closeup line segs can be more than 180 deg wiggle constraint in rare cases
					# I don't think it's valid/possible in reality for it to split into 2 intervals so only check if it's shrinked to a single inverval from required_wiggle -> required_wiggle_ambiguous
					lowerWig = min(required_wiggle, required_wiggle_ambiguous)
					upperWig = max(required_wiggle, required_wiggle_ambiguous)
					newLambda = (lowerWig+upperWig)/2 + realityLambda
					
					splitDat = [newLambda, [lowerWig, upperWig], []]
				
				elif required_wiggle >= wiggle[0] and required_wiggle <= wiggle[1]:
					# check random wiggle(lambda) (casting) then choose which section of wiggle sliced at required_wiggle we should keep based on which side <=1
					if required_wiggle != wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle)/2
						newLambda = (wiggle[0]+required_wiggle)/2 + realityLambda
						
						splitDat = [newLambda, [wiggle[0], required_wiggle], [required_wiggle, wiggle[1]]]
					else:
						# newLambda = realityLambda - (required_wiggle+wiggle[1])/2
						newLambda = (required_wiggle+wiggle[1])/2 + realityLambda
						
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
				elif required_wiggle_ambiguous >= wiggle[0] and required_wiggle_ambiguous <= wiggle[1]:
					if required_wiggle_ambiguous != wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle_ambiguous)/2
						newLambda = (wiggle[0]+required_wiggle_ambiguous)/2 + realityLambda
						
						splitDat = [newLambda, [wiggle[0], required_wiggle_ambiguous], [required_wiggle_ambiguous, wiggle[1]]]
					else:
						# newLambda = realityLambda - (required_wiggle_ambiguous+wiggle[1])/2
						newLambda = (required_wiggle_ambiguous+wiggle[1])/2 + realityLambda
						
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
				else: # new, whole interval is either not valid or all valid
					newLambda = (wiggle[0]+wiggle[1])/2 + realityLambda
					splitDat = [newLambda, wiggle, []]
			elif wiggle[1] < wiggle[0]:
				if (required_wiggle >= wiggle[0] or required_wiggle <= wiggle[1]) and (required_wiggle_ambiguous >= wiggle[0] or required_wiggle_ambiguous <= wiggle[1]):
					if (required_wiggle >= wiggle[0] and required_wiggle_ambiguous >= wiggle[0]) or (required_wiggle <= wiggle[1] and required_wiggle_ambiguous <= wiggle[1]):
						lowerWig = min(required_wiggle, required_wiggle_ambiguous)
						upperWig = max(required_wiggle, required_wiggle_ambiguous)
						# newLambda = realityLambda - (lowerWig+upperWig)/2
						newLambda = (lowerWig+upperWig)/2 + realityLambda
						
						splitDat = [newLambda, [lowerWig, upperWig], []]
					elif required_wiggle >= wiggle[0]:
						newLambda = None
						if required_wiggle!=wiggle[0]:
							# newLambda = realityLambda - (required_wiggle+math.pi)/2
							newLambda = (required_wiggle+math.pi)/2 + realityLambda
						else:
							# newLambda = realityLambda - (0+required_wiggle_ambiguous)/2
							newLambda = (0+required_wiggle_ambiguous)/2 + realityLambda
						splitDat = [newLambda, [required_wiggle, required_wiggle_ambiguous], []]
					elif required_wiggle <= wiggle[1]:
						newLambda = None
						if required_wiggle!=wiggle[1]:
							# newLambda = realityLambda - (0+required_wiggle)/2
							newLambda = (0+required_wiggle)/2 + realityLambda
						else:
							# newLambda = realityLambda - (required_wiggle_ambiguous+math.pi)/2
							newLambda = (required_wiggle_ambiguous+math.pi)/2 + realityLambda
						splitDat = [newLambda, [required_wiggle_ambiguous, required_wiggle], []]
					# else prob 2 intervals so wiggle stays default to []
				elif required_wiggle >= wiggle[0] or required_wiggle <= wiggle[1]:
					if required_wiggle > wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle)/2
						newLambda = (wiggle[0]+required_wiggle)/2 + realityLambda
						splitDat = [newLambda, [wiggle[0], required_wiggle], [required_wiggle, wiggle[1]]]
					elif required_wiggle < wiggle[1]:
						# newLambda = realityLambda - (required_wiggle+wiggle[1])/2
						newLambda = (required_wiggle+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, [required_wiggle, wiggle[1]], [wiggle[0], required_wiggle]]
					elif required_wiggle == wiggle[0]:
						# newLambda = realityLambda - (-math.pi+wiggle[1])/2
						newLambda = (-math.pi+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
					elif required_wiggle == wiggle[1]:
						# newLambda = realityLambda - (math.pi+wiggle[0])/2
						newLambda = (math.pi+wiggle[0])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[1], wiggle[1]]]
					
				elif required_wiggle_ambiguous >= wiggle[0] or required_wiggle_ambiguous <= wiggle[1]:
					if required_wiggle_ambiguous > wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle_ambiguous)/2
						newLambda = (wiggle[0]+required_wiggle_ambiguous)/2 + realityLambda
						splitDat = [newLambda, [wiggle[0], required_wiggle_ambiguous], [required_wiggle_ambiguous, wiggle[1]]]
					elif required_wiggle_ambiguous < wiggle[1]:
						# newLambda = realityLambda - (required_wiggle_ambiguous+wiggle[1])/2
						newLambda = (required_wiggle_ambiguous+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, [required_wiggle_ambiguous, wiggle[1]], [wiggle[0], required_wiggle_ambiguous]]
					elif required_wiggle_ambiguous == wiggle[0]:
						# newLambda = realityLambda - (-math.pi+wiggle[1])/2
						newLambda = (-math.pi+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
					elif required_wiggle_ambiguous == wiggle[1]:
						# newLambda = realityLambda - (math.pi+wiggle[0])/2
						newLambda = (math.pi+wiggle[0])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[1], wiggle[1]]]
				else: # new, whole interval is either not valid or all valid
					# print("HERE 22222222222222222222222")
					newLambda = None #realityLambda - (wiggle[0]+wiggle[1])/2
					if wiggle[1] != 0:
						# newLambda = realityLambda - (0+wiggle[1])/2
						newLambda = (0+wiggle[1])/2 + realityLambda
					else:
						# newLambda = realityLambda - (wiggle[0]+math.pi)/2
						newLambda = (wiggle[0]+math.pi)/2 + realityLambda
					splitDat = [newLambda, wiggle, []]
			else:
				if required_wiggle == wiggle[0] or required_wiggle_ambiguous == wiggle[0]:
					rareSkipFlag=True # leave wiggle = wiggle
				# elif required_wiggle_ambiguous == wiggle[0]:
					# rareSkipFlag=True
			
			if rareSkipFlag:
				pass
			elif len(splitDat) > 0:
				
				if splitDat[0] <= -math.pi:
					splitDat[0]+= math.pi*2
				elif splitDat[0] > math.pi:
					splitDat[0]-= math.pi*2
				if abs(splitDat[0]-math.pi)<0.0001:
					splitDat[0]=math.pi
				elif abs(splitDat[0]--math.pi)<0.0001:
					splitDat[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
				
				if (splitDat[0] + eq_alpha)%(math.pi)!=0 and (splitDat[0]-eq_p + eq_gamma)%(math.pi)!=0:
					
					tempDiv1 = math.sin(splitDat[0] + eq_alpha)
					tempDiv2 = math.sin(eq_p-splitDat[0] + eq_gamma)
					
					if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
						testRat1 = (eq_g*math.sin(eq_p-splitDat[0]))/(tempDiv2*eq_h2)
						testRat2 = (eq_g*math.sin(splitDat[0]))/(tempDiv1*eq_h)
						testRatio = testRat1 + testRat2
					
						# if testRatio < 1:
						if testRatio < 1 or testRat1 > 1 or testRat2 > 1: # NEW, same as other notes
							wiggle=splitDat[1]
						else:
							wiggle=splitDat[2]
					else:
						print("div by 0, hopefully rare not handling case properly444")
						wiggle=[]
				else:
					print("hopefully this is rare/impossible and doesn't really matter")
					# havent thought about this for more than 5 seconds, could be wiggle=wiggle, could be wiggle=[], could be anything
			else:
				wiggle = []
			
		
		return wiggle
		
	
	
	limwigroomSlowBeforeFirstPair+=1
	
	rightWindowRawDatInd = window[currWindowInd][0]
	rightPotentialRawDatInd = None
	if limWigRoomFastDat is not None:
		# leftPotentialRawDatInd = limWigRoomFastDat[0][0]
		rightPotentialRawDatInd = limWigRoomFastDat[0][1]
	else:
		rightPotentialRawDatInd = compatibleLists[currWindowInd][trackerList[currWindowInd]][0]
	
	
	if yesPrint:
		print("--- LIMITWIGGLEROOM ----------------------------------")
		print(wiggleConstraints)
		print(currWindowInd-1)
		# print()
		# print()
		# print()
		# print()
		# print()
		# print()
		# print()
		print("--- LIMITWIGGLEROOM ----------------------------------")
	
	
	global tmpppp22
	# if debug3:
		# for i in range(3):
			# print(tmpppp22)
			# print("^^^^^^^^^^^^^")
	
	if limWigRoomFastConstraint is not None:
		wiggle = [limWigRoomFastConstraint[0], limWigRoomFastConstraint[1]]
	elif firstPair is None:
		wiggle = [wiggleConstraints[currWindowInd-1][0], wiggleConstraints[currWindowInd-1][1]]
	else:
		wiggle = [firstPair[0], firstPair[1]]
	# calculate t for current and previous window linesegs outward from their shared point
	# wiggle room is amount angle is shifted, anticlockwise
	# print("@@@@@@@@ddddd@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
	# print(wiggle)
	if wiggle[0] < -math.pi or wiggle[0] > math.pi or wiggle[1] < -math.pi or wiggle[1] > math.pi:
		print(firstPair)
		print("@@@@@@@@ddddd@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		exit()
	# WIGGLE ROOM[1] IS ALWAYS MORE ANTICLOCKWISE THAN WIGGLE ROOM[0], so if its weird like [20, -10] instead of intuitive [-10, 20] that means its wiggle of 170 (I MEAN 330***) degrees all the way from 20 to -10 anticlockwise
	potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise = None, None, None, None, None, None
	if rightPotentialRawDatInd in potentialCache:
		potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise = potentialCache[rightPotentialRawDatInd]
	else:
		# mid to previous window lineseg ending
		tempPotentialClockwise = None
		potentialOrientation = rawDat2[rightPotentialRawDatInd][1]
		# potentialOrientationSeedToP1 = compatibleLists[-1][trackerList[-1]][2]
		
		#### not changing tree search and dependant functions to return this angle atm so just calc it again
		tempCoordPotentialStart = stepCoords2[rawDat2[rightPotentialRawDatInd][0][0]][0]
		tempCoordPotentialEnd = stepCoords2[rawDat2[rightPotentialRawDatInd][0][1]][0]
		
		potentialOrientationSeedToP1 = math.atan2(tempCoordPotentialStart[1] - seedCoord2[1], tempCoordPotentialStart[0] - seedCoord2[0])
		potentialOrientationSeedToP2 = math.atan2(tempCoordPotentialEnd[1] - seedCoord2[1], tempCoordPotentialEnd[0] - seedCoord2[0])
		####### # THIS AND OTHER CLOCKWISE TESTS CAN BE CHANGED TO SIMPLE LINE +/- CHECK OR WHATEVER, SIMILAR TO DEFECT STUFF
		
		tempLeftOrRight = potentialOrientation - potentialOrientationSeedToP1
		while tempLeftOrRight <= -math.pi:
			tempLeftOrRight+= math.pi*2
		while tempLeftOrRight > math.pi:
			tempLeftOrRight-= math.pi*2
		if tempLeftOrRight < 0:
			tempPotentialClockwise = True
		elif tempLeftOrRight > 0:
			tempPotentialClockwise = False
		
		potentialCache[rightPotentialRawDatInd] = [potentialOrientation, tempCoordPotentialStart, tempCoordPotentialEnd, potentialOrientationSeedToP1, potentialOrientationSeedToP2, tempPotentialClockwise]
	
	
	
	
	skipThisSchema = False
	tempWiggle=[]
	if window[currWindowInd][4] == False:
		if tempPotentialClockwise == False:
			# both anticlockwise
			# first limit wiggle room based on max wiggle of potential and window seg with no constraints from previous window/potential segs
			
			# (since both anticlockwise, get wiggle boundaries by setting window[0] to potential[1] and window[1] to potential[0])
			#window[1] first since [0] pairing is more anticlockwise shifted
			tempWiggle0 = potentialOrientationSeedToP1 - window[currWindowInd][2][1]
			tempWiggle1 = potentialOrientationSeedToP2 - window[currWindowInd][2][0]
			tempWiggle = [tempWiggle0, tempWiggle1]
		else:
			# window anticlockwise, tempseg clockwise
			# window[1] and temppotential[1] -> window[0] and temppotential[0]
			tempWiggle0 = potentialOrientationSeedToP2 - window[currWindowInd][2][1]
			tempWiggle1 = potentialOrientationSeedToP1 - window[currWindowInd][2][0]
			tempWiggle = [tempWiggle0, tempWiggle1]
	else:
		if tempPotentialClockwise == False:
			# window clockwise tempseg anticlockwise
			# window[0] and temppotential[0] -> window[1] and temppotential[1]
			tempWiggle0 = potentialOrientationSeedToP1 - window[currWindowInd][2][0]
			tempWiggle1 = potentialOrientationSeedToP2 - window[currWindowInd][2][1]
			tempWiggle = [tempWiggle0, tempWiggle1]
		else:
			# both clockwise
			# window[0] and temppotential[1] -> window[1] and temppotential[0]
			tempWiggle0 = potentialOrientationSeedToP2 - window[currWindowInd][2][0]
			tempWiggle1 = potentialOrientationSeedToP1 - window[currWindowInd][2][1]
			tempWiggle = [tempWiggle0, tempWiggle1]
	
	
	if tempWiggle[0] <= -math.pi:
		tempWiggle[0]+= math.pi*2
	elif tempWiggle[0] > math.pi:
		tempWiggle[0]-= math.pi*2
	if tempWiggle[1] <= -math.pi:
		tempWiggle[1]+= math.pi*2
	elif tempWiggle[1] > math.pi:
		tempWiggle[1]-= math.pi*2
	if abs(tempWiggle[0]-math.pi)<0.0001:
		tempWiggle[0]=math.pi
	elif abs(tempWiggle[0]--math.pi)<0.0001:
		tempWiggle[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	if abs(tempWiggle[1]-math.pi)<0.0001:
		tempWiggle[1]=math.pi
	elif abs(tempWiggle[1]--math.pi)<0.0001:
		tempWiggle[1]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	if tempWiggle[0] <= tempWiggle[1]: # intuitive
		if wiggle[0] <= wiggle[1]:
			# if tempWiggle[0] > wiggle[1] or tempWiggle[1] < wiggle[0]:
				# skipThisSchema=True
			# else:
			wiggleStart = max(wiggle[0], tempWiggle[0])
			wiggleEnd = min(wiggle[1], tempWiggle[1])
			if wiggleStart>wiggleEnd:
				skipThisSchema=True
			else:
				wiggle = [wiggleStart, wiggleEnd]
			# wiggle = [wiggleStart, wiggleEnd]
		else:
			if tempWiggle[1] >= wiggle[0]:# or tempWiggle[1] <= wiggle[1]:
				wiggleStart = max(tempWiggle[0], wiggle[0])
				wiggleEnd = tempWiggle[1]
				wiggle = [wiggleStart, wiggleEnd] # tempWiggle.copy() # tempwiggle is a subset of wiggle
			elif tempWiggle[0] <= wiggle[1]: #tempWiggle[1] < wiggle[0] and tempWiggle[0] > wiggle[1]:
				# skipThisSchema = True
				wiggleStart = tempWiggle[0]
				wiggleEnd = min(tempWiggle[1], wiggle[1])
				wiggle = [wiggleStart, wiggleEnd]
			else:
				# if tempWiggle[1] < wiggle[0]:
				# if tempWiggle[0] < wiggle[1]: # equivalent to above but more readable
					# wiggle[0] = tempWiggle[0]
				# elif tempWiggle[1] > wiggle[0]: # we assume we cant have both cases because we will never have wiggle span > 180 or anything
					# wiggle[1] = tempWiggle[1]
				skipThisSchema = True
	else:
		if wiggle[0] <= wiggle[1]:
			if wiggle[1]>=tempWiggle[0]:
				wiggleStart = max(wiggle[0], tempWiggle[0])
				wiggleEnd = wiggle[1]
				wiggle = [wiggleStart, wiggleEnd]
			
			elif wiggle[0] <= tempWiggle[1]:
				wiggleStart = wiggle[0]
				wiggleEnd = min(wiggle[1], tempWiggle[1])
				wiggle = [wiggleStart, wiggleEnd]
			else:# tempWiggle[0] > wiggle[0] and tempWiggle[0] <= wiggle[1]:
				skipThisSchema = True
		else:
			# both cross 0 so will always have some overlap
			wiggleStart = max(wiggle[0], tempWiggle[0])
			wiggleEnd = min(wiggle[1], tempWiggle[1])
			wiggle = [wiggleStart, wiggleEnd]
	
	if skipThisSchema:
		return []
	if firstPair is not None:
		return wiggle
	
	#h8u23h7
	
	leftWindowRawDatInd = window[currWindowInd-1][0]
	leftPotentialRawDatInd = None
	if limWigRoomFastDat is not None:
		leftPotentialRawDatInd = limWigRoomFastDat[0][0]
	else:
		leftPotentialRawDatInd = compatibleLists[currWindowInd-1][trackerList[currWindowInd-1]][0]
	
	if leftPotentialRawDatInd==rightPotentialRawDatInd: # explained earlier in this function at cache skip bit
		return wiggle
	
	
	limwigroomSlow+=1
	
	if skipThisSchema==False: # NO EARLY RETURNS WITHOUT SETTING limitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))]	 @@@@@@@@@@@@@@@@@@
		
		# now we have limited wiggle based on new [-1] window and we needed the potential to seed angles so theyre already stored in potentialOrientationSeedToP1 etc but need to recalculate below for getting t function for window[-2]
		# get function for t(angle), i think by getting function for angle(t) then rearranging or something itll be obvious
		# 
		
		eq_p = None # p = lambda + psi OR angle from seed->potentialPointPairingForFIRSTwindowSeg  TO  seed->potentialPointPairingForLASTwindowSeg
		eq_lambda = None # signed/normally calculated angle from seed->midpoint TO seed->potentialPointPairingForFIRSTwindowSeg
		# eq_psi = None # signed/normally calculated angle from seed->midpoint TO seed->potentialPointPairingForLASTwindowSeg
		eq_gamma = None # angle from midpoint->seed TO midpoint->lastpoint
		eq_alpha = None # angle from midpoint->seed TO midpoint->firstpoint
		eq_a = None # -cos(gamma) # abcd might be wrong not sure if pi-angle is right in this case since i actually care about signed angles but i didnt when calcing i just thought about absolute angles
		eq_b = None # sin(gamma)
		eq_c = None # -cos(alpha)
		eq_d = None # sin(alpha)
		eq_k = None # tan(p)
		eq_x = None # tan(lambda)
		eq_g = None # original A, seed->mid length
		eq_h = None # original C, window seg length i.e. 1% of edge that window is taken from
		
		firstCoord = stepCoords1[rawDat1[leftWindowRawDatInd][0][0]][0]
		midCoord = stepCoords1[rawDat1[rightWindowRawDatInd][0][0]][0]
		lastCoord = stepCoords1[rawDat1[rightWindowRawDatInd][0][1]][0]
		angleMidToSeed = math.atan2(seedCoord1[1] - midCoord[1], seedCoord1[0] - midCoord[0])
		# eq_gamma = math.atan2(seedCoord1[1] - lastCoord[1], seedCoord1[0] - lastCoord[0]) - angleMidToSeed
		# eq_alpha = math.atan2(seedCoord1[1] - firstCoord[1], seedCoord1[0] - firstCoord[0]) - angleMidToSeed
		# eq_p = 
		eq_alpha = math.atan2(firstCoord[1] - midCoord[1], firstCoord[0] - midCoord[0]) - angleMidToSeed
		eq_gamma = angleMidToSeed - math.atan2(lastCoord[1] - midCoord[1], lastCoord[0] - midCoord[0])
		
		# eq_p_firstCoord = None
		# eq_p_secondCoord = None
		
		# eq_p_firstOrient = None
		# eq_p_secondOrient = None
		
		
		if eq_gamma <= -math.pi:
			eq_gamma+= math.pi*2
		elif eq_gamma > math.pi:
			eq_gamma-= math.pi*2
		if eq_alpha <= -math.pi:
			eq_alpha+= math.pi*2
		elif eq_alpha > math.pi:
			eq_alpha-= math.pi*2
		if abs(eq_gamma-math.pi)<0.0001:
			eq_gamma=math.pi
		elif abs(eq_gamma--math.pi)<0.0001:
			eq_gamma=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
		if abs(eq_alpha-math.pi)<0.0001:
			eq_alpha=math.pi
		elif abs(eq_alpha--math.pi)<0.0001:
			eq_alpha=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

		### experimental, after added m and changed rho, hopefully works
		# eq_gamma = abs(eq_gamma)
		# eq_alpha = abs(eq_alpha)
		###
		if False:
			if window[currWindowInd][4] == False and eq_gamma < 0:
				eq_gamma = abs(eq_gamma)
			elif window[currWindowInd][4] == True and eq_gamma > 0:
				eq_gamma = -eq_gamma
			if window[currWindowInd-1][4] == False and eq_alpha < 0:
				eq_alpha = abs(eq_alpha)
			elif window[currWindowInd-1][4] == True and eq_alpha > 0:
				eq_alpha = -eq_alpha
		
		
		angleSeedToMid = angleMidToSeed-math.pi
		if angleSeedToMid <= -math.pi:
			angleSeedToMid+= math.pi*2
		elif angleSeedToMid > math.pi:
			angleSeedToMid-= math.pi*2
		if abs(angleSeedToMid-math.pi)<0.0001:
			angleSeedToMid=math.pi
		elif abs(angleSeedToMid--math.pi)<0.0001:
			angleSeedToMid=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
		
		eq_h = getDistance(firstCoord[0], midCoord[0], firstCoord[1], midCoord[1]) # c1
		eq_g = getDistance(seedCoord1[0], midCoord[0], seedCoord1[1], midCoord[1])
		
		eq_h2 = getDistance(lastCoord[0], midCoord[0], lastCoord[1], midCoord[1]) # c2, just h in wolframalpha
		# eq_m=1 # once again changing, lambda and psi signed, then all related angles signed same as lambda/psi and all sides(A,C) positive always
		eq_m=eq_h/eq_h2 # once again changing, lambda and psi signed, then all related angles signed same as lambda/psi and all sides(A,C) positive always
		
		# if window[-1][4] == True:
			# eq_h2 = -eq_h2
		# if window[-2][4] == True:
			# eq_h = -eq_h
		# eq_m = eq_h/eq_h2
		
		relevantPointLambda = None
		relevantPointPhi = None
		
		# print(":::::::::::")
		# print(rawDat1[window[currWindowInd-1][0]][0][0])
		# print(rawDat1[window[currWindowInd][0]][0][0])
		# print(firstCoord)
		# print(midCoord)
		# print(window[currWindowInd-1][0])
		# print(window[currWindowInd][0])
		# print("-")
		# print(window)
		
		
		if window[currWindowInd][4] == False:
			if tempPotentialClockwise == False:
				# eq_psi = potentialOrientationSeedToP1 - angleSeedToMid
				# eq_p_secondCoord = tempCoordPotentialStart
				# eq_p_secondOrient = potentialOrientationSeedToP1
				relevantPointPhi = [tempCoordPotentialStart[0], tempCoordPotentialStart[1]]
			else:
				# eq_psi = potentialOrientationSeedToP2 - angleSeedToMid
				# eq_p_secondCoord = tempCoordPotentialEnd
				# eq_p_secondOrient = potentialOrientationSeedToP2
				relevantPointPhi = [tempCoordPotentialEnd[0], tempCoordPotentialEnd[1]]
		else:
			if tempPotentialClockwise == False:
				# eq_psi = potentialOrientationSeedToP2 - angleSeedToMid
				# eq_p_secondCoord = tempCoordPotentialEnd
				# eq_p_secondOrient = potentialOrientationSeedToP2
				relevantPointPhi = [tempCoordPotentialEnd[0], tempCoordPotentialEnd[1]]
			else:
				# eq_psi = potentialOrientationSeedToP1 - angleSeedToMid
				# eq_p_secondCoord = tempCoordPotentialStart
				# eq_p_secondOrient = potentialOrientationSeedToP1
				relevantPointPhi = [tempCoordPotentialStart[0], tempCoordPotentialStart[1]]
		
		
		# if eq_psi < -math.pi:
			# eq_psi+= math.pi*2
		# elif eq_psi > math.pi:
			# eq_psi-= math.pi*2
		
		
		# mid to current window lineseg ending
		# tempPotentialClockwise = None
		tempPotentialClockwise_2 = None
		# print(compatibleLists[currWindowInd-1])
		# print(trackerList[currWindowInd-1])
		
		# print(trackerList)
		# tempTEST = []
		# for tempTEST2 in compatibleLists:
			# tempTEST.append(len(tempTEST2))
		# print(tempTEST)
		# print(compatibleLists[currWindowInd-1][trackerList[currWindowInd-1]])
		# print(rawDat2[compatibleLists[currWindowInd-1][trackerList[currWindowInd-1]][0]])
		# print()
		
		potentialOrientation_2 = rawDat2[leftPotentialRawDatInd][1]
		# potentialOrientationSeedToP1 = compatibleLists[-1][trackerList[-1]][2]
		
		#### not changing tree search and dependant functions to return this angle atm so just calc it again
		tempCoordPotentialStart_2 = stepCoords2[rawDat2[leftPotentialRawDatInd][0][0]][0]
		tempCoordPotentialEnd_2 = stepCoords2[rawDat2[leftPotentialRawDatInd][0][1]][0]
		
		potentialOrientationSeedToP1_2 = math.atan2(tempCoordPotentialStart_2[1] - seedCoord2[1], tempCoordPotentialStart_2[0] - seedCoord2[0])
		potentialOrientationSeedToP2_2 = math.atan2(tempCoordPotentialEnd_2[1] - seedCoord2[1], tempCoordPotentialEnd_2[0] - seedCoord2[0])
		#######
		
		tempLeftOrRight_2 = potentialOrientation_2 - potentialOrientationSeedToP1_2
		while tempLeftOrRight_2 < -math.pi:
			tempLeftOrRight_2+= math.pi*2
		while tempLeftOrRight_2 > math.pi:
			tempLeftOrRight_2-= math.pi*2
		if tempLeftOrRight_2 < 0:
			tempPotentialClockwise_2 = True
		elif tempLeftOrRight_2 > 0:
			tempPotentialClockwise_2 = False
		
		
		# if window[-2][4] == False:
			# if tempPotentialClockwise == False:
				
			
		if window[currWindowInd-1][4] == False:
			if tempPotentialClockwise_2 == False:
				# eq_lambda = potentialOrientationSeedToP1 - angleSeedToMid
				# eq_p_firstCoord = tempCoordPotentialStart
				# eq_p_firstOrient = potentialOrientationSeedToP1
				relevantPointLambda = [tempCoordPotentialEnd_2[0], tempCoordPotentialEnd_2[1]]
			else:
				# eq_lambda = potentialOrientationSeedToP2 - angleSeedToMid
				# eq_p_firstCoord = tempCoordPotentialEnd
				# eq_p_firstOrient = potentialOrientationSeedToP2
				relevantPointLambda = [tempCoordPotentialStart_2[0], tempCoordPotentialStart_2[1]]
		else:
			if tempPotentialClockwise_2 == False:
				# eq_lambda = potentialOrientationSeedToP2 - angleSeedToMid
				# eq_p_firstCoord = tempCoordPotentialEnd
				# eq_p_firstOrient = potentialOrientationSeedToP2
				relevantPointLambda = [tempCoordPotentialStart_2[0], tempCoordPotentialStart_2[1]]
			else:
				# eq_lambda = potentialOrientationSeedToP1 - angleSeedToMid
				# eq_p_firstCoord = tempCoordPotentialStart
				# eq_p_firstOrient = potentialOrientationSeedToP1
				relevantPointLambda = [tempCoordPotentialEnd_2[0], tempCoordPotentialEnd_2[1]]
		
		
		# realityLambda = eq_p_firstOrient - angleSeedToMid
		# if realityLambda < -math.pi:
			# realityLambda+= math.pi*2
		# elif realityLambda > math.pi:
			# realityLambda-= math.pi*2
		# if eq_lambda < -math.pi:
			# eq_lambda+= math.pi*2
		# elif eq_lambda > math.pi:
			# eq_lambda-= math.pi*2
		# if window[-1][4] == False:
			# if tempPotentialClockwise == False:
		
		# eq_p = eq_p_secondOrient - eq_p_firstOrient
		# eq_p = eq_p_firstOrient - eq_p_secondOrient
		
		# eq_p = eq_lambda+eq_psi
		# if eq_p < -math.pi:
			# eq_p+= math.pi*2
		# elif eq_p > math.pi:
			# eq_p-= math.pi*2
		realityLambda = angleSeedToMid - math.atan2(relevantPointLambda[1] - seedCoord2[1], relevantPointLambda[0] - seedCoord2[0])
		realityPhi = math.atan2(relevantPointPhi[1] - seedCoord2[1], relevantPointPhi[0] - seedCoord2[0]) - angleSeedToMid
		
		if realityLambda <= -math.pi:
			realityLambda+= math.pi*2
		elif realityLambda > math.pi:
			realityLambda-= math.pi*2
		if realityPhi <= -math.pi:
			realityPhi+= math.pi*2
		elif realityPhi > math.pi:
			realityPhi-= math.pi*2
		if abs(realityLambda-math.pi)<0.0001:
			realityLambda=math.pi
		elif abs(realityLambda--math.pi)<0.0001:
			realityLambda=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
		if abs(realityPhi-math.pi)<0.0001:
			realityPhi=math.pi
		elif abs(realityPhi--math.pi)<0.0001:
			realityPhi=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
		eq_p = realityLambda + realityPhi
		
		
		
		eq_a = -math.cos(eq_gamma) # -cos(gamma) # abcd might be wrong not sure if pi-angle is right in this case since i actually care about signed angles but i didnt when calcing i just thought about absolute angles
		eq_b = math.sin(eq_gamma) # sin(gamma)
		eq_c = -math.cos(eq_alpha) # -cos(alpha)
		eq_d = math.sin(eq_alpha) # sin(alpha)
		eq_k = None # tan(p)
		eq_x = None # tan(lambda)
		
		eq_lambda = None
		eq_lambda_ambiguous = None
		
		alreadyDone=False
		
		tempNegTest = None
		tempNegTest_ambiguous = None
		
		required_wiggle = None
		required_wiggle_ambiguous = None
		if (eq_p - math.pi/2)%math.pi != 0: # just putting this all the way down here becuase its rare so doesnt matter if some computation is wasted very rarely
			eq_k = math.tan(eq_p)
			# eq_achkLong = -(eq_a*eq_c*eq_h2*eq_k*eq_m + eq_a*eq_d*eq_h2*eq_m + eq_a*eq_g*eq_k + eq_b*eq_c*eq_h2*eq_m - eq_b*eq_d*eq_h2*eq_k*eq_m + eq_b*eq_g + eq_c*eq_g*eq_k*eq_m - eq_d*eq_g*eq_m)
			# eq_achShorter = -eq_a*eq_c*eq_h2*eq_m - eq_a*eq_g + eq_b*eq_c*eq_h2*eq_k*eq_m + eq_b*eq_g*eq_k - eq_c*eq_g*eq_m
			
			# eq_sqrt = eq_achkLong*eq_achkLong - 4*eq_achShorter * (-eq_a*eq_d*eq_h2*eq_k*eq_m - eq_b*eq_d*eq_h2*eq_m + eq_d*eq_g*eq_k*eq_m)
			
			
			# HERE @!@!@!!@!!@@ FIRST, INTERPERATE EQ_LAMBDA
			
			# eq_denominator = 2*eq_achShorter
			
			eq_long = eq_a*eq_c*eq_h*eq_k + eq_a*eq_d*eq_h + eq_a*eq_g*eq_k - eq_b*eq_c*eq_h + eq_b*eq_d*eq_h*eq_k - eq_b*eq_g + eq_c*eq_g*eq_k*eq_m + eq_d*eq_g*eq_m
			eq_achShorter = -eq_a*eq_c*eq_h - eq_a*eq_g - eq_b*eq_c*eq_h*eq_k - eq_b*eq_g*eq_k - eq_c*eq_g*eq_m

			eq_sqrt = eq_long*eq_long - 4*eq_achShorter * (-eq_a*eq_d*eq_h*eq_k + eq_b*eq_d*eq_h - eq_d*eq_g*eq_k*eq_m)
			eq_denominator = -2*eq_achShorter
			
			
			
			if eq_denominator != 0: # real angle when the ratios == 1
				if eq_sqrt>=0: # if it ==1 (denom !=0) then it does so at real angle
					
					eq_x_positive = math.sqrt(eq_sqrt)
					eq_x_negative = -eq_x_positive
					eq_x_positive += eq_long
					eq_x_negative += eq_long
					eq_x_positive = eq_x_positive/eq_denominator
					eq_x_negative = eq_x_negative/eq_denominator
					
					if False:
						print("SWAPPING X NEGATIVE AND POSITIVE!!!!!!")
						eq_x_positive, eq_x_negative = eq_x_negative, eq_x_positive
					
					
					eq_lambda = math.atan(eq_x_positive)
					# eq_lambda_ambiguous = 0
					if eq_lambda > 0:
						eq_lambda_ambiguous = eq_lambda - math.pi
					else:
						eq_lambda_ambiguous = eq_lambda + math.pi
					
					tempNegTest = math.atan(eq_x_negative)
					
					if tempNegTest > 0:
						tempNegTest_ambiguous = tempNegTest - math.pi
					else:
						tempNegTest_ambiguous = tempNegTest + math.pi
						
					if False:
						print("SWAPPING AMBIGUOUS AND NORMAL LAMBDA!!!!!!")
						eq_lambda, eq_lambda_ambiguous = eq_lambda_ambiguous, eq_lambda
					
					
					# tempDiv1 = math.sin(splitDat[0] + eq_alpha)
					# tempDiv2 = math.sin(eq_p-splitDat[0] + eq_gamma)
					
					# testRatio = (eq_g*math.sin(eq_p-splitDat[0]))/(tempDiv2*eq_h2) + (eq_g*math.sin(splitDat[0]))/(tempDiv1*eq_h)
					# eq_lambda = 0.19
					
					# eq_lambda = eq_lambda_ambiguous
					if True:#False:
						tempDiv1 = math.sin(eq_lambda_ambiguous + eq_alpha)
						tempDiv2 = math.sin(eq_p-eq_lambda_ambiguous + eq_gamma)
						
						if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
						
							testRat1 = (eq_g*math.sin(eq_p-eq_lambda_ambiguous))/(tempDiv2*eq_h2)
							testRat2 = (eq_g*math.sin(eq_lambda_ambiguous))/(tempDiv1*eq_h)
							testRatio = testRat1 + testRat2
							
					# print(eq_p)
					# print(eq_lambda)
					# print(eq_g)
					# print()
					# print()
					
					# exit()
					
					# tempNegTest = tempNegTest_ambiguous
					if True:#False:
						tempDiv1 = math.sin(tempNegTest_ambiguous + eq_alpha)
						tempDiv2 = math.sin(eq_p - tempNegTest_ambiguous + eq_gamma)
						
						if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
							testRat1 = (eq_g*math.sin(eq_p-tempNegTest_ambiguous))/(tempDiv2*eq_h2)
							testRat2 = (eq_g*math.sin(tempNegTest_ambiguous))/(tempDiv1*eq_h)
							testRatio = testRat1 + testRat2
					
					
				else:
					# else:
				# maybe check a random value in range then if its <1 assume all <1 and if its >1 assume all >1?
					
				# CASE 2 above
					alreadyDone=True
					angleInWiggleRange = None
					if wiggle[1] >= wiggle[0]:
						angleInWiggleRange = (wiggle[1] + wiggle[0])/2
					else:
						tempEnd = wiggle[1]+math.pi*2
						angleInWiggleRange = (tempEnd+wiggle[0])/2
						if angleInWiggleRange>math.pi:
							angleInWiggleRange-=math.pi*2
					
					
					
					# newLambda = realityLambda - angleInWiggleRange
					newLambda = angleInWiggleRange + realityLambda
					if newLambda <= -math.pi:
						newLambda+= math.pi*2
					elif newLambda > math.pi:
						newLambda-= math.pi*2
					if abs(newLambda-math.pi)<0.0001:
						newLambda=math.pi
					elif abs(newLambda--math.pi)<0.0001:
						newLambda=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
					if (newLambda + eq_alpha)%(math.pi)!=0 and (eq_p - newLambda + eq_gamma)%(math.pi)!=0:
						# tempDiv1 = math.sin(eq_lambda + eq_alpha)
						# tempDiv2 = math.sin(eq_p-eq_lambda + eq_gamma)
						
						
						# testRatio = testRat1 + testRat2
						tempDiv1 = math.sin(newLambda + eq_alpha)
					# divZeroFlag = False
					# if tempDiv1!=0:
						tempDiv2 = math.sin(eq_p-newLambda + eq_gamma)
						# if tempDiv2 != 0:
						if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
							testRat1 = (eq_g*math.sin(eq_p-newLambda))/(tempDiv2*eq_h2)
							testRat2 = (eq_g*math.sin(newLambda))/(tempDiv1*eq_h)
							testRatio = testRat1 + testRat2
							
							# print("lambda when wiggled by center of wiggle room: "+str((wiggleConstraints[0][1]+wiggleConstraints[0][0])/2) + realityLambda)
							# if testRatio <= 1:
							if testRatio <= 1 or testRat1>1 or testRat2>1: # NEW, if a sin equation is >1 in wiggle room then that's effectively -infinity, this assumes all eqs/calcs accurately describe the situation according to docs which I think they do after all the tweaks I did
								wiggle=wiggle #..? i hope this was for "readability"
							else:
								wiggle=[]
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
						else:
							print("div by 0, hopefully rare not handling case properly111")
							wiggle=[]
						
					else:
						wiggle=[]
						print("HOW IS THIS PRINTING???30928")
					
					# limitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (eq_lambda, eq_lambda_ambiguous, required_wiggle, required_wiggle_ambiguous, realityLambda, eq_g, eq_h, eq_h2, eq_p, eq_alpha, eq_gamma)
					
					
			else:
				specificWindowSegLimitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (None, None, None, None, None, None, None, None, None, None, None)
				print("hânggg????")
				wiggle=[]
				return wiggle
		else:# in notebook, tan(p-lambda) = 1/lambda if p is this condition
			eq_denominator = (2*eq_b*(eq_c*eq_h+eq_g))
			eq_3rdbit = (eq_a*eq_c*eq_h+eq_a*eq_g+eq_b*eq_d*eq_h+eq_c*eq_g*eq_m)
			eq_sqrt = eq_3rdbit**2-4*(eq_b*eq_c*eq_h+eq_b*eq_g)*(eq_a*eq_d*eq_h+eq_d*eq_g*eq_m)
			if eq_denominator !=0:
				if eq_sqrt >=0:
					eq_frac = 1/eq_denominator
					eq_sqrt = math.sqrt(eq_sqrt)
					eq_x_positive = eq_frac*(eq_sqrt+eq_3rdbit)
					eq_x_negative = eq_frac*(-eq_sqrt+eq_3rdbit)
					
					eq_lambda = math.atan(eq_x_positive)
					# eq_lambda_ambiguous = 0
					if eq_lambda > 0:
						eq_lambda_ambiguous = eq_lambda - math.pi
					else:
						eq_lambda_ambiguous = eq_lambda + math.pi
					
					tempNegTest = math.atan(eq_x_negative)
					
					if tempNegTest > 0:
						tempNegTest_ambiguous = tempNegTest - math.pi
					else:
						tempNegTest_ambiguous = tempNegTest + math.pi
					# limitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (eq_lambda, eq_lambda_ambiguous, required_wiggle, required_wiggle_ambiguous, realityLambda, eq_g, eq_h, eq_h2, eq_p, eq_alpha, eq_gamma)
					
				else:
				# CASE 2 above
					alreadyDone=True
					angleInWiggleRange = None
					if wiggle[1] >= wiggle[0]:
						angleInWiggleRange = (wiggle[1] + wiggle[0])/2
					else:
						tempEnd = wiggle[1]+math.pi*2
						angleInWiggleRange = (tempEnd+wiggle[0])/2
						if angleInWiggleRange>math.pi:
							angleInWiggleRange-=math.pi*2
					# newLambda = realityLambda - angleInWiggleRange
					newLambda =	 angleInWiggleRange + realityLambda
					if newLambda <= -math.pi:
						newLambda+= math.pi*2
					elif newLambda > math.pi:
						newLambda-= math.pi*2
					if abs(newLambda-math.pi)<0.0001:
						newLambda=math.pi
					elif abs(newLambda--math.pi)<0.0001:
						newLambda=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
					if (newLambda + eq_alpha)%(math.pi)!=0 and (eq_p - newLambda + eq_gamma)%(math.pi)!=0:
						# tempDiv1 = math.sin(newLambda + eq_alpha)
					# divZeroFlag = False
					# if tempDiv1!=0:
						# tempDiv2 = math.sin(newLambda-eq_p + eq_gamma)
						# if tempDiv2 != 0:
						# testRatio = (eq_g*math.sin(newLambda-eq_p))/(tempDiv2*eq_h2) + (eq_g*math.sin(newLambda))/(tempDiv1*eq_h)
						tempDiv1 = math.sin(newLambda + eq_alpha)
						
						tempDiv2 = math.sin(eq_p-newLambda + eq_gamma)
						if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
							testRat1 = (eq_g*math.sin(eq_p-newLambda))/(tempDiv2*eq_h2)
							testRat2 = (eq_g*math.sin(newLambda))/(tempDiv1*eq_h)
							testRatio = testRat1 + testRat2
							# if testRatio <= 1:
							if testRatio <= 1 or testRat1>1 or testRat2>1: # NEW, if a sin equation is >1 in wiggle room then that's effectively -infinity, this assumes all eqs/calcs accurately describe the situation according to docs which I think they do after all the tweaks I did
								wiggle=wiggle
							else:
								wiggle=[]
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
								# print("MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? MAYBE BIG EQUATION FAIL??????????? ")
						else:
							print("div by 0, hopefully rare not handling case properly333")
							wiggle=[]
					else:
						wiggle=[]
						print("HOW IS THIS PRINTING???30928444")
					
					# limitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (eq_lambda, eq_lambda_ambiguous, required_wiggle, required_wiggle_ambiguous, realityLambda, eq_g, eq_h, eq_h2, eq_p, eq_alpha, eq_gamma)
					
					
			else:
				specificWindowSegLimitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (None, None, None, None, None, None, None, None, None, None, None)
				print("hânggg????")
				wiggle=[]
				return wiggle
			
		if alreadyDone==False:
			
			# tempLambda_t = ... epsilon or delta simple equation NVM
			
			required_wiggle = eq_lambda + realityLambda # these are right, not below, not explaining why
			# required_wiggle_ambiguous = realityLambda - eq_lambda_ambiguous
			required_wiggle_ambiguous = eq_lambda_ambiguous + realityLambda
			
			if False:
				for debugI in range(2):
					print("DEBUG DEBUG THIS IS A TEST SET THIS TO FALSE")
				required_wiggle, required_wiggle_ambiguous = required_wiggle_ambiguous, required_wiggle
				# eq_lambda, 
			if required_wiggle <= -math.pi:
				required_wiggle+= math.pi*2
			elif required_wiggle > math.pi:
				required_wiggle-= math.pi*2
			if required_wiggle_ambiguous <= -math.pi:
				required_wiggle_ambiguous+= math.pi*2
			elif required_wiggle_ambiguous > math.pi:
				required_wiggle_ambiguous-= math.pi*2
			if abs(required_wiggle-math.pi)<0.0001:
				required_wiggle=math.pi
			elif abs(required_wiggle--math.pi)<0.0001:
				required_wiggle=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
			if abs(required_wiggle_ambiguous-math.pi)<0.0001:
				required_wiggle_ambiguous=math.pi
			elif abs(required_wiggle_ambiguous--math.pi)<0.0001:
				required_wiggle_ambiguous=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi

			# if debug3 and tmpppp22==146:
				# print("req wiggle:")
			# print("wiggle:::::::::::::::")
			# print(required_wiggle)
			# print(required_wiggle_ambiguous)
			# print(wiggle)
			rareSkipFlag = False
			splitDat = [] # [angle to test,	 [newWiggle if <1],	 [newWiggle if >1]	]  # newWiggle so lazy/bad coding but would rather do that than have 50 levels of conditionals for each case/duplicate code, its for readability
			if wiggle[1] > wiggle[0]:
				if required_wiggle >= wiggle[0] and required_wiggle <= wiggle[1] and required_wiggle_ambiguous >= wiggle[0] and required_wiggle_ambiguous <= wiggle[1]: # new, large and closeup line segs can be more than 180 deg wiggle constraint in rare cases
					# I don't think it's valid/possible in reality for it to split into 2 intervals so only check if it's shrinked to a single inverval from required_wiggle -> required_wiggle_ambiguous
					lowerWig = min(required_wiggle, required_wiggle_ambiguous)
					upperWig = max(required_wiggle, required_wiggle_ambiguous)
					# newLambda = realityLambda - (lowerWig+upperWig)/2
					newLambda = (lowerWig+upperWig)/2 + realityLambda
					
					# newWiggle = required_wiggle-()
					# newLambda = 
					
					splitDat = [newLambda, [lowerWig, upperWig], []]
				
				elif required_wiggle >= wiggle[0] and required_wiggle <= wiggle[1]:
					# check random wiggle(lambda) (casting) then choose which section of wiggle sliced at required_wiggle we should keep based on which side <=1
					if required_wiggle != wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle)/2
						newLambda = (wiggle[0]+required_wiggle)/2 + realityLambda
						
						# newWiggle = required_wiggle - (required_wiggle-wiggle[0])/2
						
						# newLambda = eq_lambda + (required_wiggle-wiggle[0])/2
						
						# => newLambda = realityLambda - required_wiggle + (required_wiggle-wiggle[0])/2
						
						# => newLambda = realityLambda	- (required_wiggle+wiggle[0])/2
						# newLambda = realityLambda - (wiggle[0]+required_wiggle)/2
						# if (newLambda + eq_alpha)%(math.pi)==0 or (newLambda-eq_p + eq_gamma)%(math.pi)==0:
							# newLambda = realityLambda - (wiggle[0] + (wiggle[0]+required_wiggle)/2)/2
						
						# if newLambda < -math.pi:
							# newLambda+= math.pi*2
						# elif newLambda > math.pi:
							# newLambda-= math.pi*2
						splitDat = [newLambda, [wiggle[0], required_wiggle], [required_wiggle, wiggle[1]]]
					else:
						# newLambda = realityLambda - (required_wiggle+wiggle[1])/2
						newLambda = (required_wiggle+wiggle[1])/2 + realityLambda
						
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
				elif required_wiggle_ambiguous >= wiggle[0] and required_wiggle_ambiguous <= wiggle[1]:
					if required_wiggle_ambiguous != wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle_ambiguous)/2
						newLambda = (wiggle[0]+required_wiggle_ambiguous)/2 + realityLambda
						
						splitDat = [newLambda, [wiggle[0], required_wiggle_ambiguous], [required_wiggle_ambiguous, wiggle[1]]]
					else:
						# newLambda = realityLambda - (required_wiggle_ambiguous+wiggle[1])/2
						newLambda = (required_wiggle_ambiguous+wiggle[1])/2 + realityLambda
						
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
				else: # new, whole interval is either not valid or all valid
					# newWiggle = required_wiggle + ((wiggle[0]+wiggle[1])/2 - required_wiggle)
					# newLambda = eq_lambda - (wiggle[0]+wiggle[1])/2 + required_wiggle
					# => == realityLambda - (wiggle[0]+wiggle[1])/2
					
					# print("HERE 1111111111111111111")
					# newLambda = realityLambda - (wiggle[0]+wiggle[1])/2
					newLambda = (wiggle[0]+wiggle[1])/2 + realityLambda
					# print("hiiiiiiiiiii")
					# print(wiggle)
					# print(newLambda)
					splitDat = [newLambda, wiggle, []]
			elif wiggle[1] < wiggle[0]:
				if (required_wiggle >= wiggle[0] or required_wiggle <= wiggle[1]) and (required_wiggle_ambiguous >= wiggle[0] or required_wiggle_ambiguous <= wiggle[1]):
					if (required_wiggle >= wiggle[0] and required_wiggle_ambiguous >= wiggle[0]) or (required_wiggle <= wiggle[1] and required_wiggle_ambiguous <= wiggle[1]):
						lowerWig = min(required_wiggle, required_wiggle_ambiguous)
						upperWig = max(required_wiggle, required_wiggle_ambiguous)
						# newLambda = realityLambda - (lowerWig+upperWig)/2
						newLambda = (lowerWig+upperWig)/2 + realityLambda
						
						splitDat = [newLambda, [lowerWig, upperWig], []]
					elif required_wiggle >= wiggle[0]:
						newLambda = None
						if required_wiggle!=wiggle[0]:
							# newLambda = realityLambda - (required_wiggle+math.pi)/2
							newLambda = (required_wiggle+math.pi)/2 + realityLambda
						else:
							# newLambda = realityLambda - (0+required_wiggle_ambiguous)/2
							newLambda = (0+required_wiggle_ambiguous)/2 + realityLambda
						splitDat = [newLambda, [required_wiggle, required_wiggle_ambiguous], []]
					elif required_wiggle <= wiggle[1]:
						newLambda = None
						if required_wiggle!=wiggle[1]:
							# newLambda = realityLambda - (0+required_wiggle)/2
							newLambda = (0+required_wiggle)/2 + realityLambda
						else:
							# newLambda = realityLambda - (required_wiggle_ambiguous+math.pi)/2
							newLambda = (required_wiggle_ambiguous+math.pi)/2 + realityLambda
						splitDat = [newLambda, [required_wiggle_ambiguous, required_wiggle], []]
					# else prob 2 intervals so wiggle stays default to []
				elif required_wiggle >= wiggle[0] or required_wiggle <= wiggle[1]:
					if required_wiggle > wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle)/2
						newLambda = (wiggle[0]+required_wiggle)/2 + realityLambda
						splitDat = [newLambda, [wiggle[0], required_wiggle], [required_wiggle, wiggle[1]]]
					elif required_wiggle < wiggle[1]:
						# newLambda = realityLambda - (required_wiggle+wiggle[1])/2
						newLambda = (required_wiggle+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, [required_wiggle, wiggle[1]], [wiggle[0], required_wiggle]]
					elif required_wiggle == wiggle[0]:
						# newLambda = realityLambda - (-math.pi+wiggle[1])/2
						newLambda = (-math.pi+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
					elif required_wiggle == wiggle[1]:
						# newLambda = realityLambda - (math.pi+wiggle[0])/2
						newLambda = (math.pi+wiggle[0])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[1], wiggle[1]]]
					
				elif required_wiggle_ambiguous >= wiggle[0] or required_wiggle_ambiguous <= wiggle[1]:
					if required_wiggle_ambiguous > wiggle[0]:
						# newLambda = realityLambda - (wiggle[0]+required_wiggle_ambiguous)/2
						newLambda = (wiggle[0]+required_wiggle_ambiguous)/2 + realityLambda
						splitDat = [newLambda, [wiggle[0], required_wiggle_ambiguous], [required_wiggle_ambiguous, wiggle[1]]]
					elif required_wiggle_ambiguous < wiggle[1]:
						# newLambda = realityLambda - (required_wiggle_ambiguous+wiggle[1])/2
						newLambda = (required_wiggle_ambiguous+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, [required_wiggle_ambiguous, wiggle[1]], [wiggle[0], required_wiggle_ambiguous]]
					elif required_wiggle_ambiguous == wiggle[0]:
						# newLambda = realityLambda - (-math.pi+wiggle[1])/2
						newLambda = (-math.pi+wiggle[1])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[0], wiggle[0]]]
					elif required_wiggle_ambiguous == wiggle[1]:
						# newLambda = realityLambda - (math.pi+wiggle[0])/2
						newLambda = (math.pi+wiggle[0])/2 + realityLambda
						splitDat = [newLambda, wiggle, [wiggle[1], wiggle[1]]]
				else: # new, whole interval is either not valid or all valid
					# print("HERE 22222222222222222222222")
					newLambda = None #realityLambda - (wiggle[0]+wiggle[1])/2
					if wiggle[1] != 0:
						# newLambda = realityLambda - (0+wiggle[1])/2
						newLambda = (0+wiggle[1])/2 + realityLambda
					else:
						# newLambda = realityLambda - (wiggle[0]+math.pi)/2
						newLambda = (wiggle[0]+math.pi)/2 + realityLambda
					splitDat = [newLambda, wiggle, []]
			else:
				if required_wiggle == wiggle[0] or required_wiggle_ambiguous == wiggle[0]:
					rareSkipFlag=True # leave wiggle = wiggle
				# elif required_wiggle_ambiguous == wiggle[0]:
					# rareSkipFlag=True
			
			if rareSkipFlag:
				pass
			elif len(splitDat) > 0:
				
				if splitDat[0] <= -math.pi:
					splitDat[0]+= math.pi*2
				elif splitDat[0] > math.pi:
					splitDat[0]-= math.pi*2
				if abs(splitDat[0]-math.pi)<0.0001:
					splitDat[0]=math.pi
				elif abs(splitDat[0]--math.pi)<0.0001:
					splitDat[0]=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
				# update stuff that is based on lambda, nvm none i think
				
				
				# eq_p = None # p = lambda + psi OR angle from seed->potentialPointPairingForFIRSTwindowSeg	 TO	 seed->potentialPointPairingForLASTwindowSeg
				# eq_lambda = None # signed/normally calculated angle from seed->midpoint TO seed->potentialPointPairingForFIRSTwindowSeg
				# eq_gamma = None # angle from midpoint->seed TO midpoint->lastpoint
				# eq_alpha = None # angle from midpoint->seed TO midpoint->firstpoint
				# eq_a = None # -cos(gamma) # abcd might be wrong not sure if pi-angle is right in this case since i actually care about signed angles but i didnt when calcing i just thought about absolute angles
				# eq_b = None # sin(gamma)
				# eq_c = None # -cos(alpha)
				# eq_d = None # sin(alpha)
				# eq_k = None # tan(p)
				# eq_x = None # tan(lambda)
				# eq_g = None # original A, seed->mid length
				# eq_h = None # original C, window seg length i.e. 1% of edge that window is taken from
				
				if (splitDat[0] + eq_alpha)%(math.pi)!=0 and (splitDat[0]-eq_p + eq_gamma)%(math.pi)!=0:
					# splitDat[0] = eq_lambda # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
					
					tempDiv1 = math.sin(splitDat[0] + eq_alpha)
					tempDiv2 = math.sin(eq_p-splitDat[0] + eq_gamma)
					
					if tempDiv1 != 0 and tempDiv2 != 0 and eq_h!=0 and eq_h2 !=0:
						
						testRat1 = (eq_g*math.sin(eq_p-splitDat[0]))/(tempDiv2*eq_h2)
						testRat2 = (eq_g*math.sin(splitDat[0]))/(tempDiv1*eq_h)
						testRatio = testRat1 + testRat2
						
						if testRatio < 1 or testRat1 > 1 or testRat2 > 1: # NEW, same as other notes
							wiggle=splitDat[1]
						else:
							wiggle=splitDat[2]
					else:
						print("div by 0, hopefully rare not handling case properly222")
						wiggle=[]
			else:
				wiggle = []
		# print(specificWindowSegLimitWiggleRoomCalcCache)
		# print(specificWindowSegLimitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))])
		specificWindowSegLimitWiggleRoomCalcCache[((leftWindowRawDatInd, leftPotentialRawDatInd), (rightWindowRawDatInd, rightPotentialRawDatInd))] = (eq_lambda, eq_lambda_ambiguous, required_wiggle, required_wiggle_ambiguous, realityLambda, eq_g, eq_h, eq_h2, eq_p, eq_alpha, eq_gamma)
		
	# if debug3 and tmpppp22==146:
		# print('debgging stuff')
		# print(wiggle)
		# print(splitDat)
		# print(required_wiggle)
		# print(required_wiggle_ambiguous)
		# print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW")
	# if debug3 and tmpppp22>146:
		# print('debgging stuff')
		# exit()
	
	return wiggle

def bestPtsForMean(scaleList):
	# tempList.append([tempRatio, p, n, m])
	# tempList.sort()
	# scaleList.append(tempList)
	
	constantInds = []
	notConstantInds = []
	# bestMean = 0
	bestVarianceChoices=[]
	currMean = 0
	currVariance = 0 # not actual variance, just sum of absolute differences from mean
	bestVariance = 0
	varianceTracker = []
	# currMeanChoices = []
	n=0
	
	for i, meanColumn in enumerate(scaleList):
		varianceTracker.append(-1)
		# bestVarianceChoices.append([])
		bestVarianceChoices.append(-1)
		if len(meanColumn)!=0:
			varianceTracker[-1]=0
			# bestVarianceChoices[-1].append(0)
			bestVarianceChoices[-1] = 0
			currMean+=meanColumn[0][0]
			n+=1
			if len(meanColumn)==1:
				constantInds.append(i)
			else:
				notConstantInds.append(i)
	if n>1:
		currMean = currMean/n
	# elif n == 1:
	else:
		return # expand on this later if needed
	# bestMean=currMean
	
	for i, val in enumerate(varianceTracker):
		if val != -1:
			currVariance+=abs(currMean-scaleList[i][val][0])
	bestVariance = currVariance
	
	# bestMeanChoices = 
	
	while len(notConstantInds)!=0: # NEED AN OUT FOR WHEN NONE LEFT BELOW MEAN OR WHATEVER
		# tempCurrMeanInds = []
		didAnythingHappenQuestionMark = False
		lowestBelowMean = float('inf')
		lowestBelowMeanInd = None
		for i in notConstantInds:
			if scaleList[i][varianceTracker[i]+1][0] < currMean and scaleList[i][varianceTracker[i]+1][0] < lowestBelowMean:
				lowestBelowMeanInd = i
				lowestBelowMean = scaleList[i][varianceTracker[i]+1][0]
		if lowestBelowMeanInd is not None:
			didAnythingHappenQuestionMark = True
			varianceTracker[lowestBelowMeanInd] +=1
			if varianceTracker[lowestBelowMeanInd] == len(scaleList[lowestBelowMeanInd])-1:
				notConstantInds.remove(lowestBelowMeanInd)
				# maybe add to constant inds? prob not useful though but take note
			newVariance = 0
			newMean = 0
			for i, val in enumerate(varianceTracker):
				if val != -1:
					newMean+=scaleList[i][val][0]
			newMean = newMean/n
			for i, val in enumerate(varianceTracker):
				if val != -1:
					newVariance+=abs(newMean-scaleList[i][val][0])
			if newVariance < bestVariance:
				bestVariance = newVariance
				for i in range(len(bestVarianceChoices)):
					if varianceTracker[i] != -1:
						# bestVarianceChoices[i][0] = varianceTracker[i]
						bestVarianceChoices[i] = varianceTracker[i]
		else:
			lowestVal = float('inf')
			lowestValInd = None
			bestChangeInd = -1
			bestChangeAmount = 0
			for i in notConstantInds:
				# backup case to force something to change, not even sure if its possible for this to actually be required but rather safe than sorry
				
				if scaleList[i][varianceTracker[i]][0] < currMean:
					tempMean = 0
					for j, val in enumerate(varianceTracker):
						if j!=i and val != -1:
							tempMean+=scaleList[j][val][0]
					tempMean = tempMean/(n-1)
					prevDiff = abs(tempMean-scaleList[i][varianceTracker[i]][0])
					newDiff = abs(tempMean-scaleList[i][varianceTracker[i]+1][0])
					improvement = newDiff-prevDiff
					if improvement < bestChangeAmount:
						bestChangeInd = i
						bestChangeAmount = improvement
			if bestChangeInd != -1:
				didAnythingHappenQuestionMark = True
				varianceTracker[bestChangeInd] +=1
				if varianceTracker[bestChangeInd] == len(scaleList[bestChangeInd])-1:
					notConstantInds.remove(bestChangeInd)
					# maybe add to constant inds? prob not useful though but take note
				newVariance = 0
				newMean = 0
				for i, val in enumerate(varianceTracker):
					if val != -1:
						newMean+=scaleList[i][val][0]
				newMean = newMean/n
				for i, val in enumerate(varianceTracker):
					if val != -1:
						newVariance+=abs(newMean-scaleList[i][val][0])
				if newVariance < bestVariance:
					bestVariance = newVariance
					for i in range(len(bestVarianceChoices)):
						if varianceTracker[i] != -1:
							# bestVarianceChoices[i][0] = varianceTracker[i]
							bestVarianceChoices[i] = varianceTracker[i]
			else:
				for i in notConstantInds:
					if scaleList[i][varianceTracker[i]+1][0] < lowestVal:
						lowestValInd = i
						lowestVal = scaleList[i][varianceTracker[i]+1][0]
				if lowestValInd is not None: # should always be true
					didAnythingHappenQuestionMark = True
					varianceTracker[lowestValInd] +=1
					if varianceTracker[lowestValInd] == len(scaleList[lowestValInd])-1:
						notConstantInds.remove(lowestValInd)
						# maybe add to constant inds? prob not useful though but take note
					newVariance = 0
					newMean = 0
					for i, val in enumerate(varianceTracker):
						if val != -1:
							newMean+=scaleList[i][val][0]
					newMean = newMean/n
					for i, val in enumerate(varianceTracker):
						if val != -1:
							newVariance+=abs(newMean-scaleList[i][val][0])
					if newVariance < bestVariance:
						bestVariance = newVariance
						for i in range(len(bestVarianceChoices)):
							if varianceTracker[i] != -1:
								# bestVarianceChoices[i][0] = varianceTracker[i]
								bestVarianceChoices[i] = varianceTracker[i]
		if didAnythingHappenQuestionMark == False:
			print("how did nothing happen?? eh293dq1")
			exit() # remove when ready
			break
	return bestVarianceChoices



def constructLinearTransformedAnnulusSectorDat(estimatedScale, params, windowP1, windowP2, windowSeedCoord, windowEdgePixelationError, queryEdgePixelationError, angleSide1, angleSide2, currWiggle, querySeedCoord):
	# estimatedScale is estimated size of edge1/edge2 where edge1 is where window comes from and edge2 is what we query
	
	tempLinearTransformedAnnulusSectorDat = {}
	
	tempDist1 = getDistance(windowSeedCoord[0], windowP1[0], windowSeedCoord[1], windowP1[1])
	tempDist2 = getDistance(windowSeedCoord[0], windowP2[0], windowSeedCoord[1], windowP2[1])
	
	dist1 = None
	dist2 = None
	
	if tempDist1 <= tempDist2:
		dist1 = tempDist1
		dist2 = tempDist2
	else:
		dist1 = tempDist2
		dist2 = tempDist1
	
	# pixelation error for window piece
	
	dist1 -= windowEdgePixelationError
	dist2 += windowEdgePixelationError
	
	scaledDist1 = dist1/estimatedScale
	scaledDist2 = dist2/estimatedScale
	
	# errorFromScale = params['scaleEstimationError']/estimatedScale # we actually want edge2/edge1 so instead of estimatedScale*params['scaleEstimationError'] we have this, params['scaleEstimationError'] is global 5% or whatever to denote max error when calcing scale between 2 edges
	
	annulusDist1 = scaledDist1*(1-params['scaleEstimationError'])
	annulusDist2 = scaledDist2*(1+params['scaleEstimationError']) # params['scaleEstimationError'] a float like 0.05
	
	annulusDist1 -= queryEdgePixelationError
	annulusDist2 += queryEdgePixelationError
	
	# if annulusDist1 <= 0:
		# annulusDist1 = 0.001*annulusDist2 # or something, not sure if letting it == 0 below will be okay cant remember exact calculations that happen with these
	
	if annulusDist1 < 0:
		annulusDist1 = 0
	
	tempLinearTransformedAnnulusSectorDat['distRing1'] = annulusDist1
	tempLinearTransformedAnnulusSectorDat['distRing2'] = annulusDist2
	
	annulusSide1Angle = angleSide1 + currWiggle[1] # cause wiggle intervals are always right then left but side1 is left of side2
	annulusSide2Angle = angleSide2 + currWiggle[0]
	# print(annulusSide1Angle)
	# print(annulusSide2Angle)
	# input("oress jioije..............")
	
	annulusSide1M = None
	annulusSide2M = None
	
	annulusSide1C = None
	annulusSide2C = None
	
	
	if annulusSide1Angle <= -math.pi:
		annulusSide1Angle+= math.pi*2
	elif annulusSide1Angle > math.pi:
		annulusSide1Angle-= math.pi*2
	if annulusSide2Angle <= -math.pi:
		annulusSide2Angle+= math.pi*2
	elif annulusSide2Angle > math.pi:
		annulusSide2Angle-= math.pi*2
	
	if abs(annulusSide1Angle-math.pi)<0.0001:
		annulusSide1Angle=math.pi
	elif abs(annulusSide1Angle--math.pi)<0.0001:
		annulusSide1Angle=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	
	if abs(annulusSide2Angle-math.pi)<0.0001:
		annulusSide2Angle=math.pi
	elif abs(annulusSide2Angle--math.pi)<0.0001:
		annulusSide2Angle=math.pi # if an angle is basically -math.pi I always +=2pi which just gives pi
	
	# if abs(annulusSide1Angle) != math.pi/2:
		# annulusSide1M = math.tan(annulusSide1Angle) # INSTEAD OF DOING TAN I CAN JUST DO ROTATEDPTS FIRST THEN DO NORMAL LINE EQUATION USING ROTATED PT AND SEED
		# annulusSide1C = windowSeedCoord[1]-annulusSide1M*windowSeedCoord[0]
	# else:
		# annulusSide1C = windowSeedCoord[0]
	
	# if abs(annulusSide1Angle) != math.pi/2:
		# annulusSide2M = math.tan(annulusSide1Angle)
		# annulusSide2C = windowSeedCoord[1]-annulusSide2M*windowSeedCoord[0]
	# else:
		# annulusSide2C = windowSeedCoord[0]
	
	if abs(annulusSide1Angle) != math.pi/2:
		annulusSide1M = math.tan(annulusSide1Angle) # INSTEAD OF DOING TAN I CAN JUST DO ROTATEDPTS FIRST THEN DO NORMAL LINE EQUATION USING ROTATED PT AND SEED
		annulusSide1C = querySeedCoord[1]-annulusSide1M*querySeedCoord[0]
	else:
		annulusSide1C = querySeedCoord[0]
	
	if abs(annulusSide2Angle) != math.pi/2:
		annulusSide2M = math.tan(annulusSide2Angle)
		annulusSide2C = querySeedCoord[1]-annulusSide2M*querySeedCoord[0]
	else:
		annulusSide2C = querySeedCoord[0]
	
	tempLinearTransformedAnnulusSectorDat['lineEqSide1'] = [annulusSide1M, annulusSide1C]
	tempLinearTransformedAnnulusSectorDat['lineEqSide2'] = [annulusSide2M, annulusSide2C]
	
	if False:
		sinP1 = math.sin(currWiggle[1])
		cosP1 = math.cos(currWiggle[1])
		sinP2 = math.sin(currWiggle[0])
		cosP2 = math.cos(currWiggle[0])
		
		tempPt1MinusOrigin = [windowP1[0] - windowSeedCoord[0], windowP1[1] - windowSeedCoord[1]]
		tempPt2MinusOrigin = [windowP2[0] - windowSeedCoord[0], windowP2[1] - windowSeedCoord[1]]
		
		rotatedPt1 = [tempPt1MinusOrigin[0]*cosP1 - tempPt1MinusOrigin[1]*sinP1, tempPt1MinusOrigin[0]*sinP1 + tempPt1MinusOrigin[1]*cosP1]
		rotatedPt2 = [tempPt2MinusOrigin[0]*cosP2 - tempPt2MinusOrigin[1]*sinP2, tempPt2MinusOrigin[0]*sinP2 + tempPt2MinusOrigin[1]*cosP2]
		
		rotatedPt1 = [rotatedPt1[0] + windowSeedCoord[0], rotatedPt1[1] + windowSeedCoord[1]]
		rotatedPt2 = [rotatedPt2[0] + windowSeedCoord[0], rotatedPt2[1] + windowSeedCoord[1]]
		
		tempLinearTransformedAnnulusSectorDat['arbSide1Point'] = rotatedPt1
		tempLinearTransformedAnnulusSectorDat['arbSide2Point'] = rotatedPt2
		
		tempLinearTransformedAnnulusSectorDat['arbSide1PointMinusSeed'] = [rotatedPt1[0] - windowSeedCoord[0], rotatedPt1[1] - windowSeedCoord[1]]
		tempLinearTransformedAnnulusSectorDat['arbSide2PointMinusSeed'] = [rotatedPt2[0] - windowSeedCoord[0], rotatedPt2[1] - windowSeedCoord[1]]
	else:
		
		arbSide1Point = None
		arbSide2Point = None
		# arbSide1PointMinusSeed = None
		# arbSide2PointMinusSeed = None
		corner1 = None
		corner2 = None
		corner3 = None
		corner4 = None
		
		tmpDist = (annulusDist2-annulusDist1)/2 # get this dist along tempLinearTransformedAnnulusSectorDat['lineEqSide1'] and tempLinearTransformedAnnulusSectorDat['lineEqSide2']
		# in right direction since the circle of these dists intersects twice with a line
		
		# is this right? why did I think the part above in if False: would work?? check what arbSide1Point is used for after this function is called, if its related to being on lineEqSide1 then think its wrong
		
		if annulusSide1M is None:
			if annulusSide1Angle < 0: # it should be -math.pi/2 but just doing this in case of small float difference errors
				arbSide1Point = [querySeedCoord[0], querySeedCoord[1]-tmpDist]
				corner1 = [querySeedCoord[0], querySeedCoord[1]-annulusDist1]
				corner4 = [querySeedCoord[0], querySeedCoord[1]-annulusDist2]
			else:
				arbSide1Point = [querySeedCoord[0], querySeedCoord[1]+tmpDist]
				corner1 = [querySeedCoord[0], querySeedCoord[1]+annulusDist1]
				corner4 = [querySeedCoord[0], querySeedCoord[1]+annulusDist2]
		else:
			# use angle and dists and vector stuff
			tmpCos = math.cos(annulusSide1Angle)
			tmpSin = math.sin(annulusSide1Angle)
			xComponentRing1 = annulusDist1*tmpCos
			yComponentRing1 = annulusDist1*tmpSin
			corner1 = [querySeedCoord[0]+xComponentRing1, querySeedCoord[1]+yComponentRing1]
			
			# tmpCos = math.cos(annulusSide1Angle)
			# tmpSin = math.sin(annulusSide1Angle)
			xComponentRing2 = annulusDist2*tmpCos
			yComponentRing2 = annulusDist2*tmpSin
			corner4 = [querySeedCoord[0]+xComponentRing2, querySeedCoord[1]+yComponentRing2]
			
			arbSide1Point = [(corner1[0]+corner4[0])/2, (corner1[1]+corner4[1])/2]
			
		if annulusSide2M is None:
			if annulusSide2Angle < 0: # it should be -math.pi/2 but just doing this in case of small float difference errors
				arbSide2Point = [querySeedCoord[0], querySeedCoord[1]-tmpDist]
				corner2 = [querySeedCoord[0], querySeedCoord[1]-annulusDist1]
				corner3 = [querySeedCoord[0], querySeedCoord[1]-annulusDist2]
			else:
				arbSide2Point = [querySeedCoord[0], querySeedCoord[1]+tmpDist]
				corner2 = [querySeedCoord[0], querySeedCoord[1]+annulusDist1]
				corner3 = [querySeedCoord[0], querySeedCoord[1]+annulusDist2]
		else:
			tmpCos = math.cos(annulusSide2Angle)
			tmpSin = math.sin(annulusSide2Angle)
			xComponentRing1 = annulusDist1*tmpCos
			yComponentRing1 = annulusDist1*tmpSin
			corner2 = [querySeedCoord[0]+xComponentRing1, querySeedCoord[1]+yComponentRing1]
			
			# tmpCos = math.cos(annulusSide1Angle)
			# tmpSin = math.sin(annulusSide1Angle)
			xComponentRing2 = annulusDist2*tmpCos
			yComponentRing2 = annulusDist2*tmpSin
			corner3 = [querySeedCoord[0]+xComponentRing2, querySeedCoord[1]+yComponentRing2]
			
			arbSide2Point = [(corner2[0]+corner3[0])/2, (corner2[1]+corner3[1])/2]
			
		tempLinearTransformedAnnulusSectorDat['corners'] = [corner1, corner2, corner3, corner4]
		
		# minus seeds !@@@@@@@@@@@!!!!!!!!!!!!!!!!!!!!@@@@@@@@@@@
		
		tempLinearTransformedAnnulusSectorDat['arbSide1Point'] = arbSide1Point
		tempLinearTransformedAnnulusSectorDat['arbSide2Point'] = arbSide2Point
		
		tempLinearTransformedAnnulusSectorDat['arbSide1PointMinusSeed'] = [arbSide1Point[0] - querySeedCoord[0], arbSide1Point[1] - querySeedCoord[1]]
		tempLinearTransformedAnnulusSectorDat['arbSide2PointMinusSeed'] = [arbSide2Point[0] - querySeedCoord[0], arbSide2Point[1] - querySeedCoord[1]]
		
		
		if True:
			tempLinearTransformedAnnulusSectorDat['annulusSide1Angle'] = annulusSide1Angle
			tempLinearTransformedAnnulusSectorDat['annulusSide2Angle'] = annulusSide2Angle
		
		
	# 'angleSize' left i think
	
	# CONTINUE CONSTRUCTING DICT
	
	angleSize = math.atan2(tempLinearTransformedAnnulusSectorDat['arbSide1PointMinusSeed'][1], tempLinearTransformedAnnulusSectorDat['arbSide1PointMinusSeed'][0]) - math.atan2(tempLinearTransformedAnnulusSectorDat['arbSide2PointMinusSeed'][1], tempLinearTransformedAnnulusSectorDat['arbSide2PointMinusSeed'][0])
	if angleSize < 0:
		angleSize+=math.pi*2
	
	tempLinearTransformedAnnulusSectorDat['angleSize'] = angleSize
	
	
	if tempLinearTransformedAnnulusSectorDat['lineEqSide1'][1] is None:
		print("?????????535??????????????")
		exit()
	if tempLinearTransformedAnnulusSectorDat['lineEqSide2'][1] is None:
		print("??????352?????????????????")
		exit()
	
	return tempLinearTransformedAnnulusSectorDat

# get point of intersection between line and line seg, or if line seg is on the line, get 3 evenly spaced points along the line seg
idktempCalls = 0
idktempConditional = 0
idktempTimeKeep=0
def idktemp(edge1, windowSegStartIndInContour, windowSegStartRatioOnLine, windowSegEndIndInContour, windowSegEndRatioOnLine, windowLineM, windowLineC, seedCoord1, pointPairs, stepLength1):
	global idktempCalls
	global idktempConditional
	global idktempTimeKeep
	idkticTemp = time.perf_counter()
	idktempCalls+=1
	
	startPt = copy.deepcopy(edge1[windowSegStartIndInContour][0])
	endPt = copy.deepcopy(edge1[windowSegStartIndInContour+1][0]) # windowSegStartIndInContour will never == edge1.shape[0]-1
	tempSign1=None
	tempSign2=None
	if windowLineM is None:
		tempSign1 = startPt[0] - windowLineC
		tempSign2 = endPt[0] - windowLineC
	else:
		tempSign1 = startPt[1] - windowLineM*startPt[0] - windowLineC
		tempSign2 = endPt[1] - windowLineM*endPt[0] - windowLineC
	# if (tempSign1<0) and (tempSign2<0) or (tempSign1>0) and (tempSign2>0)

	if ((tempSign1>=0) or (tempSign2>=0)) and ((tempSign1<=0) or (tempSign2<=0)):
		idktempConditional+=1
		if tempSign1 == 0 and tempSign2 == 0:
			currSegLength = getDistance(startPt[0], endPt[0], startPt[1], endPt[1])
			currSegLength = currSegLength*(windowSegEndRatioOnLine-windowSegStartRatioOnLine)
			ratioCurrSegToStepLength = currSegLength/stepLength1
			if ratioCurrSegToStepLength > 0.3:
				tempPt1 = [startPt[0] + (endPt[0] - startPt[0])*windowSegStartRatioOnLine, startPt[1] + (endPt[1] - startPt[1])*windowSegStartRatioOnLine]
				tempPt2 = [startPt[0] + (endPt[0] - startPt[0])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2, startPt[1] + (endPt[1] - startPt[1])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2]
				tempPt3 = [startPt[0] + (endPt[0] - startPt[0])*windowSegEndRatioOnLine, startPt[1] + (endPt[1] - startPt[1])*windowSegEndRatioOnLine]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1]), tempPt1]) # add more dat here if needed
				if tempPt2[0] != seedCoord1[0] and tempPt2[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt2[0], seedCoord1[1], tempPt2[1]), tempPt2]) # add more dat here if needed
				if tempPt3[0] != seedCoord1[0] and tempPt3[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt3[0], seedCoord1[1], tempPt3[1]), tempPt3]) # add more dat here if needed
			else:
				tempPt2 = [startPt[0] + (endPt[0] - startPt[0])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2, startPt[1] + (endPt[1] - startPt[1])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt2[0] != seedCoord1[0] and tempPt2[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt2[0], seedCoord1[1], tempPt2[1]), tempPt2]) # add more dat here if needed
		else:
			# find intersection point
			if windowLineM is None:
				tempY = startPt[1] + ((endPt[1]-startPt[1])*(windowLineC-startPt[0]))/(endPt[0]-startPt[0])
				tempPt1 = [windowLineC, tempY]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1]), tempPt1]) # add more dat here if needed
			elif windowLineM == 0:
				tempX = startPt[0] + ((endPt[0]-startPt[0])*(windowLineC-startPt[1]))/(endPt[1]-startPt[1])
				tempPt1 = [tempX, windowLineC]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1]), tempPt1]) # add more dat here if needed
			else:
				tempT = (windowLineM*startPt[0]+windowLineC-startPt[1])/(endPt[1]-startPt[1]-windowLineM*(endPt[0]-startPt[0]))
				tempX = startPt[0]+(endPt[0]-startPt[0])*tempT
				tempY = startPt[1]+(endPt[1]-startPt[1])*tempT
				tempPt1 = [tempX, tempY]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1]), tempPt1]) # add more dat here if needed
	idktocTemp = time.perf_counter()
	idktempTimeKeep+=idktocTemp-idkticTemp
	return


def miniIdktemp(startPt, endPt, windowLineM, windowLineC, seedCoord1, stepLength1, intersections, estDist, currStepCoordsInd, prevSign):
	
	# intersections=[]
	
	tempSign1=None
	tempSign2=None
	if windowLineM is None:
		if prevSign is None:
			tempSign1 = startPt[0] - windowLineC
		else:
			tempSign1 = prevSign
		tempSign2 = endPt[0] - windowLineC
	else:
		if prevSign is None:
			tempSign1 = startPt[1] - windowLineM*startPt[0] - windowLineC
		else:
			tempSign1 = prevSign
		tempSign2 = endPt[1] - windowLineM*endPt[0] - windowLineC
	if ((tempSign1>=0) or (tempSign2>=0)) and ((tempSign1<=0) or (tempSign2<=0)):
		if tempSign1 == 0 and tempSign2 == 0:
			# currSegLength = getDistance(startPt[0], endPt[0], startPt[1], endPt[1])
			# currSegLength = currSegLength*(windowSegEndRatioOnLine-windowSegStartRatioOnLine)
			# ratioCurrSegToStepLength = currSegLength/stepLength1
			if True:#ratioCurrSegToStepLength > 0.3:
				tempPt1 = [startPt[0], startPt[1]]
				tempPt2 = [startPt[0] + (endPt[0] - startPt[0])/2, startPt[1] + (endPt[1] - startPt[1])/2]
				tempPt3 = [endPt[0], endPt[1]]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt1, currStepCoordsInd]) # add more dat here if needed
				if tempPt2[0] != seedCoord1[0] and tempPt2[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt2[0], seedCoord1[1], tempPt2[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt2, currStepCoordsInd]) # add more dat here if needed
				if tempPt3[0] != seedCoord1[0] and tempPt3[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt3[0], seedCoord1[1], tempPt3[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt3, currStepCoordsInd]) # add more dat here if needed
			# else:
				# tempPt2 = [startPt[0] + (endPt[0] - startPt[0])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2, startPt[1] + (endPt[1] - startPt[1])*(windowSegStartRatioOnLine+windowSegEndRatioOnLine)/2]
				
				# if tempPt2[0] != seedCoord1[0] and tempPt2[1] != seedCoord1[1]:
					# pointPairs[-1][-1].append([getDistance(seedCoord1[0], tempPt2[0], seedCoord1[1], tempPt2[1]), tempPt2]) # add more dat here if needed
		else:
			# find intersection point
			if windowLineM is None:
				tempY = startPt[1] + ((endPt[1]-startPt[1])*(windowLineC-startPt[0]))/(endPt[0]-startPt[0])
				tempPt1 = [windowLineC, tempY]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt1, currStepCoordsInd]) # add more dat here if needed
			elif windowLineM == 0:
				tempX = startPt[0] + ((endPt[0]-startPt[0])*(windowLineC-startPt[1]))/(endPt[1]-startPt[1])
				tempPt1 = [tempX, windowLineC]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt1, currStepCoordsInd]) # add more dat here if needed
			else:
				tempT = (windowLineM*startPt[0]+windowLineC-startPt[1])/(endPt[1]-startPt[1]-windowLineM*(endPt[0]-startPt[0]))
				tempX = startPt[0]+(endPt[0]-startPt[0])*tempT
				tempY = startPt[1]+(endPt[1]-startPt[1])*tempT
				tempPt1 = [tempX, tempY]
				# pointPairs[pairInd].append([angleInWindowEdge])
				if tempPt1[0] != seedCoord1[0] and tempPt1[1] != seedCoord1[1]:
					tmpDist=getDistance(seedCoord1[0], tempPt1[0], seedCoord1[1], tempPt1[1])
					intersections.append([abs(tmpDist-estDist), tmpDist, tempPt1, currStepCoordsInd]) # add more dat here if needed
	return tempSign2


def closestPt(lineSeg, point): # ASSUME LINESEG HAS NON-ZERO LENGTH
	
	
	dx = lineSeg[1][0] - lineSeg[0][0]
	dy = lineSeg[1][1] - lineSeg[0][1]
	d2 = dx*dx + dy*dy
	nx = ((point[0]-lineSeg[0][0])*dx + (point[1]-lineSeg[0][1])*dy) / d2
	nx = min(1, max(0, nx))
	return nx, (dx*nx + lineSeg[0][0], dy*nx + lineSeg[0][1])



#					!!!!!!!!!!!!!!!!!				!!!!!!!!!!!!!! \/\/\/\/\/\/\/
# CURRENTLY GIVES 1D AXIS COORDS IN DIRECTION FROM LEFT SIDE TO RIGHT SIDE, e.g. if intersects sides at [20, 45] and [30, 48] and intersection with left side x is <= 20, then itll give [20, 30] x dimensions of intersection coords (I say <= cause if the inf line for the segment intersects with left side but segment doesnt go all the way to meet the left side then this function gives the left most point of the segment)
def lineSegLineIntersect(coord1, coord2, lineSegSlope, lineSegC, linearTransformedAnnulusSectorDat, querySeedCoord): # this gives intervals using x or y coords since a line is uniquely defined on x axis unless line is x=c in which case need to define interval using y
	seedCoord = querySeedCoord
	m1, c1 = linearTransformedAnnulusSectorDat['lineEqSide1']
	m2, c2 = linearTransformedAnnulusSectorDat['lineEqSide2']
	
	arbSide1PointMinusSeed = linearTransformedAnnulusSectorDat['arbSide1PointMinusSeed']
	arbSide2PointMinusSeed = linearTransformedAnnulusSectorDat['arbSide2PointMinusSeed']
	
	arbSide1Point = linearTransformedAnnulusSectorDat['arbSide1Point']
	arbSide2Point = linearTransformedAnnulusSectorDat['arbSide2Point']
	
	# print("lineSegLineIntersect:------")
	# print(linearTransformedAnnulusSectorDat)
	# print(coord1)
	# print(coord2)
	# print(lineSegSlope)
	# print(lineSegC)
	# print(querySeedCoord)
	# print("-.-.-.-.-.-.-")
	
	
	# lineSegSlope = None
	# lineSegC = None
	
	# tempDiv = coord2[0] - coord1[0]
	# if tempDiv != 0:
		# lineSegSlope = (coord2[1] - coord1[1]/tempDiv)
	
	# if lineSegSlope is not None:
		# lineSegC = coord1[1] - lineSegSlope*coord1[0]
	
	# print(linearTransformedAnnulusSectorDat)
	# print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
	
	intersectionSide1 = None
	intersectionSide2 = None
	if lineSegSlope != m1: # \/ if intersection is outside line-segment part of inf line
		if lineSegSlope is not None and m1 is not None:
			intersectionSide1X = (c1-lineSegC)/(lineSegSlope-m1)
			intersectionSide1 = [intersectionSide1X, m1*intersectionSide1X + c1]
		elif lineSegSlope is not None: # and m1 is
			# print("HERE")
			# x = c1 is the line so if this intersects with anything itll be at x=c1
			intersectionSide1 = [c1, lineSegSlope*c1+lineSegC]
		elif m1 is not None: # and lineSegSlope is
			# print("HERE")
			intersectionSide1 = [lineSegC, m1*lineSegC+c1]
		if abs(coord1[0]-intersectionSide1[0])<0.0000001:
			intersectionSide1[0]=coord1[0]
		if abs(coord1[1]-intersectionSide1[1])<0.0000001:
			intersectionSide1[1]=coord1[1]
		if abs(coord2[0]-intersectionSide1[0])<0.0000001:
			intersectionSide1[0]=coord2[0]
		if abs(coord2[1]-intersectionSide1[1])<0.0000001:
			intersectionSide1[1]=coord2[1]
		
		if coord1[0] != coord2[0]:
			if coord1[0] < coord2[0]:
				if intersectionSide1[0] < coord1[0] or intersectionSide1[0] > coord2[0]:
					intersectionSide1 = None
			else:
				if intersectionSide1[0] > coord1[0] or intersectionSide1[0] < coord2[0]:
					intersectionSide1 = None
		else:
			if coord1[1] < coord2[1]:
				if intersectionSide1[1] < coord1[1] or intersectionSide1[1] > coord2[1]:
					intersectionSide1 = None
			else:
				if intersectionSide1[1] > coord1[1] or intersectionSide1[1] < coord2[1]:
					intersectionSide1 = None
					#--
		if intersectionSide1 is not None: # intersection on wrong half of inf line through seedcoord and side1/side2
			if seedCoord[0] != arbSide1Point[0]:
				if arbSide1Point[0] - seedCoord[0] > 0:
					if intersectionSide1[0] < seedCoord[0]:
						intersectionSide1 = None # intersection doesnt happen on the side1 line on the correct side of the seedCoord point, we only care about a specific part of side1 line from seedCoord in direction of arbSide1Point
				else:
					if intersectionSide1[0] > seedCoord[0]:
						intersectionSide1 = None
			elif seedCoord[1] != arbSide1Point[1]:
				if arbSide1Point[1] - seedCoord[1] > 0:
					if intersectionSide1[1] < seedCoord[1]:
						intersectionSide1 = None # intersection doesnt happen on the side1 line on the correct side of the seedCoord point, we only care about a specific part of side1 line from seedCoord in direction of arbSide1Point
				else:
					if intersectionSide1[1] > seedCoord[1]:
						intersectionSide1 = None
	if lineSegSlope != m2:
		if lineSegSlope is not None and m2 is not None:
			intersectionSide2X = (c2-lineSegC)/(lineSegSlope-m2)
			intersectionSide2 = [intersectionSide2X, m2*intersectionSide2X + c2]
		elif lineSegSlope is not None: # and m2 is
			# x = c2 is the line so if this intersects with anything itll be at x=c2
			intersectionSide2 = [c2, lineSegSlope*c2+lineSegC]
		elif m2 is not None: # and lineSegSlope is
			intersectionSide2 = [lineSegC, m2*lineSegC+c2]
		# intersectionSide2X = (c2-lineSegC)/(lineSegSlope-m2)
		# intersectionSide2 = [intersectionSide2X, m2*intersectionSide2X + c2]
		if abs(coord1[0]-intersectionSide2[0])<0.0000001:
			intersectionSide2[0]=coord1[0]
		if abs(coord1[1]-intersectionSide2[1])<0.0000001:
			intersectionSide2[1]=coord1[1]
		if abs(coord2[0]-intersectionSide2[0])<0.0000001:
			intersectionSide2[0]=coord2[0]
		if abs(coord2[1]-intersectionSide2[1])<0.0000001:
			intersectionSide2[1]=coord2[1]
		if coord1[0] != coord2[0]:
			if coord1[0] < coord2[0]:
				if intersectionSide2[0] < coord1[0] or intersectionSide2[0] > coord2[0]:
					intersectionSide2 = None
			else:
				if intersectionSide2[0] > coord1[0] or intersectionSide2[0] < coord2[0]:
					intersectionSide2 = None
		else:
			if coord1[1] < coord2[1]:
				if intersectionSide2[1] < coord1[1] or intersectionSide2[1] > coord2[1]:
					intersectionSide2 = None
			else:
				if intersectionSide2[1] > coord1[1] or intersectionSide2[1] < coord2[1]:
					intersectionSide2 = None
					#--
		if intersectionSide2 is not None:
			if seedCoord[0] != arbSide2Point[0]:
				if arbSide2Point[0] - seedCoord[0] > 0:
					if intersectionSide2[0] < seedCoord[0]:
						intersectionSide2 = None # intersection doesnt happen on the side2 line on the correct side of the seedCoord point, we only care about a specific part of side2 line from seedCoord in direction of arbSide2Point
				else:
					if intersectionSide2[0] > seedCoord[0]:
						intersectionSide2 = None
			elif seedCoord[1] != arbSide2Point[1]:
				if arbSide2Point[1] - seedCoord[1] > 0:
					if intersectionSide2[1] < seedCoord[1]:
						intersectionSide2 = None # intersection doesnt happen on the side2 line on the correct side of the seedCoord point, we only care about a specific part of side2 line from seedCoord in direction of arbSide2Point
				else:
					if intersectionSide2[1] > seedCoord[1]:
						intersectionSide2 = None
	# print(intersectionSide1)
	# print(intersectionSide2)
	# print("ooooooooooooooooooooo")
	if intersectionSide1 is None and intersectionSide2 is None:
		midPt = [(coord1[0]+coord2[0])/2, (coord1[1]+coord2[1])/2]# in case collinear stuff that i chose not to handle/consider
		angleSide1ToMidPt = math.atan2(arbSide1PointMinusSeed[1], arbSide1PointMinusSeed[0]) - math.atan2(midPt[1]-seedCoord[1], midPt[0]-seedCoord[0])
		if angleSide1ToMidPt < 0:
			angleSide1ToMidPt += math.pi*2
		if angleSide1ToMidPt >= linearTransformedAnnulusSectorDat['angleSize']:
			return None, None
		else:
			# print(1)
			# if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
				# return [coord1[0], coord2[0]], 'X'
			# else:
				# return [coord1[1], coord2[1]], 'Y'
			lineSegPointBefore = coord1
			sign = (coord1[1] - seedCoord[1])*(coord2[0] - seedCoord[0]) - (coord1[0] - seedCoord[0])*(coord2[1] - seedCoord[1])
			# print(sign)
			# print(seedCoord)
			# print(coord2)
			# print(coord1)
			if sign < 0:
				# coord1 is to the right/clockwise of line from seed to coord2
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord2[0], coord1[0]], 'X'
				else:
					return [coord2[1], coord1[1]], 'Y'
			else:
				# coord1 is to the left/anticlockwise of line from seed to coord2
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord1[0], coord2[0]], 'X'
				else:
					return [coord1[1], coord2[1]], 'Y'
	
	elif intersectionSide1 is None: # only intersects 1 side so need to split lineseg at intersection and take whichever side is anticlockwise of intersectionSide2 i.e. inside (because asserted side2 is clockwise of side1)
		if intersectionSide2[0] != coord1[0] or intersectionSide2[1] != coord1[1]:
			# lineSegPointBefore = [(coord1[0]+intersectionSide2[0])/2, (coord1[1]+intersectionSide2[1])/2] # not sure why i originally wanted a pt between start and intersection
			lineSegPointBefore = coord1
			sign = (lineSegPointBefore[1] - seedCoord[1])*(arbSide2Point[0] - seedCoord[0]) - (lineSegPointBefore[0] - seedCoord[0])*(arbSide2Point[1] - seedCoord[1])
			if sign < 0:
				# print(2)
				# lineSegPointBefore is to the right/clockwise of line from seed to side2, i want to the left!
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord2[0], intersectionSide2[0]], 'X'
				else:
					return [coord2[1], intersectionSide2[1]], 'Y'
			else:
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord1[0], intersectionSide2[0]], 'X'
				else:
					return [coord1[1], intersectionSide2[1]], 'Y'
		else:
			lineSegPointAfter = coord2
			sign = (lineSegPointAfter[1] - seedCoord[1])*(arbSide2Point[0] - seedCoord[0]) - (lineSegPointAfter[0] - seedCoord[0])*(arbSide2Point[1] - seedCoord[1])
			if sign < 0:
				# print(3)
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord1[0], intersectionSide2[0]], 'X' # intersectionSide2 == coord1 so this is single point interval
				else:
					return [coord1[1], intersectionSide2[1]], 'Y'
			else:
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [coord2[0], intersectionSide2[0]], 'X'
				else:
					return [coord2[1], intersectionSide2[1]], 'Y'
			
			
	elif intersectionSide2 is None:
		# if intersectionSide2[0]-
		if intersectionSide1[0] != coord1[0] or intersectionSide1[1] != coord1[1]:
			# lineSegPointBefore = [(coord1[0]+intersectionSide1[0])/2, (coord1[1]+intersectionSide1[1])/2] # not sure why i originally wanted a pt between start and intersection
			lineSegPointBefore = coord1
			sign = (lineSegPointBefore[1] - seedCoord[1])*(arbSide1Point[0] - seedCoord[0]) - (lineSegPointBefore[0] - seedCoord[0])*(arbSide1Point[1] - seedCoord[1])
			if sign > 0: # >0 this time because we want stuff to the right i.e. clockwise of side1 so in this case >0 is what we dont want
				# print(4)
				# print(intersectionSide1)
				# print(coord1)
				# print(sign)
				# print("	this 0?? ^^444^^^^^")
				# lineSegPointBefore is to the left/anticlockwise of line from seed to side1, i want to the right!
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [intersectionSide1[0], coord2[0]], 'X'
				else:
					return [intersectionSide1[1], coord2[1]], 'Y'
			else:
				# print(5)
				# print(sign)
				# print(seedCoord)
				# print(coord2)
				# print(coord1)
				# print(sign)
				# print("	this 0?? ^^222^^^^^")
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [intersectionSide1[0], coord1[0]], 'X'
				else:
					return [intersectionSide1[1], coord1[1]], 'Y'
		else:
			lineSegPointAfter = coord2
			sign = (lineSegPointAfter[1] - seedCoord[1])*(arbSide1Point[0] - seedCoord[0]) - (lineSegPointAfter[0] - seedCoord[0])*(arbSide1Point[1] - seedCoord[1])
			if sign > 0:
				# print(6)
				# print(sign)
				# print("	this 0?? ^^333^^^^^")
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [intersectionSide1[0], coord1[0]], 'X'
				else:
					return [intersectionSide1[1], coord1[1]], 'Y'
			else:
				# print(7)
				# print(sign)
				# print("	this 0?? ^^^^111^^^")
				if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
					return [intersectionSide1[0], coord2[0]], 'X'
				else:
					return [intersectionSide1[1], coord2[1]], 'Y'
	# else: # intersects both, check if 1 interval between or 2 intervals on ends of segment (happens if linearTransformedAnnulusSectorDat['angleSize'] > math.pi)
		# @@@ ??? what was meant to go here
		
		# WRITTEN WAY AFTER ALL THE OTHER STUFF HERE AFTER IVE FORGOTTEN EVERYTHING IN THIS FUNCTION @@@
		
	
	if linearTransformedAnnulusSectorDat['angleSize'] < math.pi: # NEW, WANT IT ORDERED SIDE1 TO SIDE2 I.E. CLOCKWISE
		if intersectionSide1[0] != intersectionSide2[0] or intersectionSide1[1] == intersectionSide2[1]: # need to handle 0 or undefined slopes seperately
			return [intersectionSide1[0], intersectionSide2[0]], 'X'
		else:
			return [intersectionSide1[1], intersectionSide2[1]], 'Y'
	
	
	else: # NEW, WANT IT ORDERED SIDE1 TO SIDE2 I.E. CLOCKWISE
		return None, None
		#
		# not handling this rare case where annulus sector angle is > 180 deg and line seg intersects partially on each ending because then the returned list isnt monotone e.g. if interval returned is [a, b, c, d] it can be e.g. a>b and c<d which id have to handle seperately in intersectIntervals and just after intersectIntervals calls
		#
		print("MAYBE JUST DELETE IF CAUSING ISSUES @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
		distCoord1ToSide1Intersect = getDistance(intersectionSide1[0], coord1[0], intersectionSide1[1], coord1[1])
		distCoord1ToSide2Intersect = getDistance(intersectionSide2[0], coord1[0], intersectionSide2[1], coord1[1])
		if distCoord1ToSide1Intersect < distCoord1ToSide2Intersect:
			if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
				return [intersectionSide1[0], coord1[0], coord2[0], intersectionSide2[0]], 'X'
			else:
				return [intersectionSide1[1], coord1[1], coord2[1], intersectionSide2[1]], 'Y'
		else:
			if coord1[0] != coord2[0] or coord1[1] == coord2[1]:
				return [intersectionSide1[0], coord2[0], coord1[0], intersectionSide2[0]], 'X'
			else:
				return [intersectionSide1[1], coord2[1], coord1[1], intersectionSide2[1]], 'Y'
		# if intersectionSide1 is not None:
			# if intersectionSide1[0] != coord1[0]:
				# lineSegPointBefore = [(coord1[0]+intersectionSide1[0])/2, (coord1[1]+intersectionSide1[1])/2]
				
			# else:
				# lineSegPointAfter = [(coord1[0]+intersectionSide1[0])/2, (coord1[1]+intersectionSide1[1])/2]
		
		
	# elif linearTransformedAnnulusSectorDat['angleSize'] > math.pi: # need to treat differently
		
	# else: # same 180 line
		
	
	return None, None


def lineSegAnnulusIntersect(coord1, coord2, lineSegSlope, lineSegC, linearTransformedAnnulusSectorDat, seedCoord, distRing1, distRing2):
	
	# ring1R = linearTransformedAnnulusSectorDat['distRing1']
	# ring
	
	# ring1Discriminant = ring1R*ring1R*
	# print(linearTransformedAnnulusSectorDat['corners'])
	# print(coord1)
	# print(coord2)
	# print(lineSegSlope)
	# print(lineSegC)
	# print(seedCoord)
	
	if lineSegSlope is not None:
		B = 2*(lineSegSlope*(lineSegC-seedCoord[1]) - seedCoord[0])
		A = lineSegSlope*lineSegSlope + 1
		C = seedCoord[1]*seedCoord[1] - distRing1*distRing1 + seedCoord[0]*seedCoord[0] - 2*lineSegC*seedCoord[1] + lineSegC*lineSegC
		ring1Discriminant = B*B-4*A*C
		
		
		# 1 interval defined by 2 intersections with outer ring2
		# get ring2 X coords of the 2 intersections then use logic with x coords of coord1/coord2 and if they go up/down to choose if interval is [ring2Intersection1[0], ring2Intersection2[0]] or [ring2Intersection2[0], ring2Intersection1[0]]
		ring2B = B
		ring2A = A
		ring2C = seedCoord[1]*seedCoord[1] - distRing2*distRing2 + seedCoord[0]*seedCoord[0] - 2*lineSegC*seedCoord[1] + lineSegC*lineSegC
		ring2Discriminant = ring2B*ring2B - 4*ring2A*ring2C
		intersection1XRing2 = (-ring2B + math.sqrt(ring2Discriminant))/(2*ring2A)
		intersection2XRing2 = (-ring2B - math.sqrt(ring2Discriminant))/(2*ring2A)
		if ring1Discriminant <= 0:
			if coord1[0] < coord2[0]:
				if intersection1XRing2 < intersection2XRing2:
					return [intersection1XRing2, intersection2XRing2], 'X'
				else:
					return [intersection2XRing2, intersection1XRing2], 'X'
			else:
				if intersection1XRing2 > intersection2XRing2:
					return [intersection1XRing2, intersection2XRing2], 'X'
				else:
					return [intersection2XRing2, intersection1XRing2], 'X'
		# else:
		# get all 4 intersections then get 2 intervals
		# ring1Intersection1 = 
		# ring1Intersection2 = 
		# ring1Intersections = []
		
		# ... make sure ordered like with other stuff according to coord1 => coord2
		# also since lineSegSlope is not None, we know coord1[0] != coord2[0] so use x coordinates
		
		intersection1XRing1 = (-B + math.sqrt(ring1Discriminant))/(2*A)
		intersection2XRing1 = (-B - math.sqrt(ring1Discriminant))/(2*A)
		intersections = [intersection1XRing2, intersection1XRing1, intersection2XRing1, intersection2XRing2]
		if coord1[0] < coord2[0]:
			intersections.sort()
		else:
			intersections.sort(reverse=True)
		return intersections, 'X'
	else:
		# same as above but with constant x or whatever, graph is x=c
		A = 1
		B = -2*seedCoord[1]
		C = seedCoord[1]*seedCoord[1] - distRing1*distRing1 + seedCoord[0]*seedCoord[0] - 2*coord1[0]*seedCoord[0] + coord1[0]*coord1[0]
		ring1Discriminant = B*B-4*A*C
		
		# ---- copied and pasted below
		ring2B = B
		ring2A = A
		ring2C = seedCoord[1]*seedCoord[1] - distRing2*distRing2 + seedCoord[0]*seedCoord[0] - 2*coord1[0]*seedCoord[0] + coord1[0]*coord1[0]
		ring2Discriminant = ring2B*ring2B - 4*ring2A*ring2C
		intersection1YRing2 = (-ring2B + math.sqrt(ring2Discriminant))/(2*ring2A)
		intersection2YRing2 = (-ring2B - math.sqrt(ring2Discriminant))/(2*ring2A)
		if ring1Discriminant <= 0:
			if coord1[1] < coord2[1]:
				if intersection1YRing2 < intersection2YRing2:
					return [intersection1YRing2, intersection2YRing2], 'Y'
				else:
					return [intersection2YRing2, intersection1YRing2], 'Y'
			else:
				if intersection1YRing2 > intersection2YRing2:
					return [intersection1YRing2, intersection2YRing2], 'Y'
				else:
					return [intersection2YRing2, intersection1YRing2], 'Y'
		
		intersection1YRing1 = (-B + math.sqrt(ring1Discriminant))/(2*A)
		intersection2YRing1 = (-B - math.sqrt(ring1Discriminant))/(2*A)
		intersections = [intersection1YRing2, intersection1YRing1, intersection2YRing1, intersection2YRing2]
		if coord1[1] < coord2[1]:
			intersections.sort()
		else:
			intersections.sort(reverse=True)
		return intersections, 'Y'
	
	return


def newClosestPt(coord1, coord2, lineSegSlope, lineSegC, seedCoord):
	
	if lineSegSlope is None:
		minY = None
		maxY = None
		if coord1[1] <= coord2[1]:
			minY = coord1[1]
			maxY = coord2[1]
		else:
			minY = coord2[1]
			maxY = coord1[1]
		if seedCoord[1] >= minY and seedCoord[1] <= maxY:
			return [coord1[0], seedCoord[1]]
		else:
			if abs(seedCoord[1]-coord1[1]) <= abs(seedCoord[1]-coord2[1]):
				return coord1
			else:
				return coord2
			
		
	elif lineSegSlope == 0:
		# return [seedCoord[0], coord1[1]]
		minX = None
		maxX = None
		if coord1[0] <= coord2[0]:
			minX = coord1[0]
			maxX = coord2[0]
		else:
			minX = coord2[0]
			maxX = coord1[0]
		if seedCoord[0] >= minX and seedCoord[0] <= maxX:
			return [seedCoord[0], coord1[1]]
		else:
			if abs(seedCoord[0]-coord1[0]) <= abs(seedCoord[0]-coord2[0]):
				return coord1
			else:
				return coord2
	else:
		perpendicularSlope = -1/lineSegSlope
		perpendicularC = seedCoord[1] - perpendicularSlope*seedCoord[0]
		# tempDiv = lineSegSlope - perpendicularSlope # cant be equal lol
		intersectX = (perpendicularC - lineSegC)/(lineSegSlope - perpendicularSlope)
		intersectY = perpendicularSlope*intersectX + perpendicularC
		
		minX = None
		maxX = None
		if coord1[0] <= coord2[0]:
			minX = coord1[0]
			maxX = coord2[0]
		else:
			minX = coord2[0]
			maxX = coord1[0]
		# if seedCoord[0] >= minX and seedCoord[0] <= maxX:
		if intersectX >= minX and intersectX <= maxX:
			return [intersectX, intersectY]
		else:
			if abs(intersectX-coord1[0]) <= abs(intersectX-coord2[0]):
				return coord1
			else:
				return coord2
		# return [intersectX, intersectY]
	
	# return


def intersectIntervals(arr1, arr2):
	
	# print("££££££££££££££££££££££")
	# print(arr1)
	if arr1 is None or arr2 is None:
		return []
	
	n = len(arr1)
	m = len(arr2)
	
	if n==0 or m==0: # can be <2 test instead of ==0 test if intervals are ever allowed to be length 1 i.e. [a] instead of [a, a]
		return []
	reverse1=False
	reverse2=False
	# if arr1[0] > arr1[-1] or arr2[0] > arr2[-1]: # terrible code but not tweaking the loop for now
		# arr1 = arr1[::-1]
		# arr2 = arr2[::-1]
		# reverse=True
	# print("===============")
	# print(arr2)
	# print(arr1)
	if arr1[0] > arr1[-1]:
		arr1 = arr1[::-1]
		reverse1=True
	if arr2[0] > arr2[-1]:
		arr2 = arr2[::-1]
		reverse2=True
	# print(arr1)
	# print(reverse1)
	intersectionIntervals = []
	# i and j pointers for arr1
	# and arr2 respectively
	i = j = 0
	# print(arr2)
	# n=0
	# m=0
	# if arr1 is not None:
		# n = len(arr1)
	# if arr2 is not None:
		# m = len(arr2)
	# Loop through all intervals unless one 
	# of the interval gets exhausted
	while i < n and j < m:
		
		# Left bound for intersecting segment
		l = max(arr1[i], arr2[j])
		
		# Right bound for intersecting segment
		r = min(arr1[i+1], arr2[j+1])
		
		# If segment is valid print it
		if l <= r:
			intersectionIntervals.append([l, r])
		# If i-th interval's right bound is
		# smaller increment i else increment j
		if arr1[i+1] < arr2[j+1]:
			i += 2
		else:
			j += 2
	# if reverse:
		# arr1 = arr1[::-1]
		# arr2 = arr2[::-1]
		# intersectionIntervals = intersectionIntervals[::-1]
		# for tmpinterval in intersectionIntervals:
			# tmpinterval = tmpinterval[::-1]
	# print(intersectionIntervals)
	if reverse2:
		arr2 = arr2[::-1]
	if reverse1: # arr1 is sides intersections and those are actually ordered, from side1 to side2 i.e. clockwise order, so keeping the output in sync with that in case I need to know their order, BUT REMEMBER CLOCKWISE/ANTICLOCKWISE DOESNT == INCREASING/DECREASING COORDS
		arr1 = arr1[::-1]
		intersectionIntervals = intersectionIntervals[::-1]
		for tmpinterval in intersectionIntervals:
			tmpinterval.reverse()
	# print(intersectionIntervals)
	# print("^^^^^^^^^^^^")
	return intersectionIntervals

# intersectionDat = searchOBBTree(branch, rawDat, stepCoords, linearTransformedAnnulusSectorDat, seedCoord, minimumIndex, intersectionDat)

def staticEdgeStepData(stepCoords, estimatedSize, edgeOrientation, params): # ASSUME COORDS HAVE BEEN SHIFTED SO ORIENTATION == X AXIS!@!!@!@!@!@
	
	# params['stepDataOrderDict'] = {'orientation': 0, 'flownvm': 1, ...}
	# params['stepDataOrder'] = [1,0,2,...]
	
	rawDat = []
	# tempUniqueInds = []
	tempStepData = {} # plan roughly stepData split into partitionable feature1 e.g. subarea orientation or flow direction from edge-x-axis etc. then within each partition, further partition and on until all fully partitionable features done, then bvh tree or something for last feature if needed or uniform grid
	
	for i in range(len(stepCoords)-2):
		
		subAreaOrient = math.atan2(stepCoords[i+1][0][1] - stepCoords[i][0][1], stepCoords[i+1][0][0] - stepCoords[i][0][0]) # edge orientation is already x axis so no point subtracting is cause itd be 0
		# ...
		
		
		
		rawDat.append([[i, i+1], subAreaOrient])# ...]) # rawDat[j][0] are inds for stepCoords items
	
	
	# MAYBE ANALYSE DISTRIBUTION TO DECIDE HOW TO PARTITION, FOR NOW ITLL BE UNIFORM AND EDUCATED GUESS AT DECENT VALUES (+/- 22.5 deg, partitions of 10 deg)
	
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
	
	# ... above again but within each partition, do until done or until i need to do a tree <<<<<<<<<<<<< record depth???
	
	# IF I WANT TO PARTITION FURTHER BEFORE SPACE PARTITIONING/TREE, just iterate the data within each partition then split further, then make the tree stage iterate the leaf partitions which will be +1 depth to currently (if added 1 more partition level)
	
	# iterate tempStepData
		# construct finalStepData @@@@@@@@@@@@@
	
	for key, val in tempStepData.items(): # add extra for loop for each partition depth added
		tempInds = val[1]
		
		tempTree = unoptimisedOOBTree(stepCoords, rawDat, tempInds, True)
		tempStepData[key][1] = tempTree
		
	
	
	return tempStepData, rawDat



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
















































