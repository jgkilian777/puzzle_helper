from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
import copy
import numpy as np
import cv2
import math
from oct2py import octave
from PIL import Image, ExifTags
from matplotlib.path import Path

import argparse
import os
import time
import pidistuff.models
from pidistuff.models.convert_pidinet import convert_pidinet
from pidistuff.utils import *
from pidistuff.edge_dataloader import BSDS_VOCLoader, BSDS_Loader, Multicue_Loader, NYUD_Loader, Custom_Loader
from torch.utils.data import DataLoader

import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
import torch.backends.cudnn as cudnn


def getPidiContours(imagesList, maxXDimensionJustForMachingLearningContours, imgMaximumXDimension, inputImgsPath):
	
	parser = argparse.ArgumentParser(description='PyTorch Pixel Difference Convolutional Networks')

	parser.add_argument('--savedir', type=str, default='results/savedir', 
			help='path to save result and checkpoint')
	parser.add_argument('--datadir', type=str, default='../data', 
			help='dir to the dataset')
	parser.add_argument('--only-bsds', action='store_true', 
			help='only use bsds for training')
	parser.add_argument('--ablation', action='store_true', 
			help='not use bsds val set for training')
	parser.add_argument('--dataset', type=str, default='BSDS',
			help='data settings for BSDS, Multicue and NYUD datasets')

	parser.add_argument('--model', type=str, default='baseline', 
			help='model to train the dataset')
	parser.add_argument('--sa', action='store_true', 
			help='use CSAM in pidinet')
	parser.add_argument('--dil', action='store_true', 
			help='use CDCM in pidinet')
	parser.add_argument('--config', type=str, default='carv4', 
			help='model configurations, please refer to models/config.py for possible configurations')
	parser.add_argument('--seed', type=int, default=None, 
			help='random seed (default: None)')
	parser.add_argument('--gpu', type=str, default='', 
			help='gpus available')
	parser.add_argument('--checkinfo', action='store_true', 
			help='only check the informations about the model: model size, flops')

	parser.add_argument('--epochs', type=int, default=20, 
			help='number of total epochs to run')
	parser.add_argument('--iter-size', type=int, default=24, 
			help='number of samples in each iteration')
	parser.add_argument('--lr', type=float, default=0.005, 
			help='initial learning rate for all weights')
	parser.add_argument('--lr-type', type=str, default='multistep', 
			help='learning rate strategy [cosine, multistep]')
	parser.add_argument('--lr-steps', type=str, default=None, 
			help='steps for multistep learning rate')
	parser.add_argument('--opt', type=str, default='adam', 
			help='optimizer')
	parser.add_argument('--wd', type=float, default=1e-4, 
			help='weight decay for all weights')
	parser.add_argument('-j', '--workers', type=int, default=4, 
			help='number of data loading workers')
	parser.add_argument('--eta', type=float, default=0.3, 
			help='threshold to determine the ground truth (the eta parameter in the paper)')
	parser.add_argument('--lmbda', type=float, default=1.1, 
			help='weight on negative pixels (the beta parameter in the paper)')

	parser.add_argument('--resume', action='store_true', 
			help='use latest checkpoint if have any')
	parser.add_argument('--print-freq', type=int, default=10, 
			help='print frequency')
	parser.add_argument('--save-freq', type=int, default=1, 
			help='save frequency')
	parser.add_argument('--evaluate', type=str, default=None, 
			help='full path to checkpoint to be evaluated')
	parser.add_argument('--evaluate_converted', action='store_true', 
			help='convert the checkpoint to vanilla cnn, then evaluate')

	args = parser.parse_args()

	args.model="pidinet_converted"
	# args.model="pidinet"
	# args.model="pidinet_small_converted"
	args.config="carv4"
	# args.config="baseline"
	args.sa=True
	args.dil=True
	args.gpu="0"
	args.savedir="pidiOUTPUT"
	args.datadir="pidiIMGS"
	args.dataset="Custom"
	args.evaluate="pidistuff/models/table7_pidinet.pth"
	# args.evaluate="pidistuff/models/table5_pidinet-small.pth"
	# args.evaluate="pidistuff/models/table5_baseline.pth"
	
	# args.evaluate="pidistuff/models/table5_pidinet.pth"
	args.evaluate_converted=True
	args.use_cuda = False
	# args.use_cuda = True
	args.workers=0
	
	os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu
	
	print("MAKE SURE pidiIMGS DIR IS EMPTY!!! (or same names as last run)")
	print('     !!!    REFERENCE CONTOUR MUST BE ORIENTED THE SAME WAY IN EVERY IMAGE      !!!')
	input('press enter... ^^^')
	
	for i, imagePath in enumerate(imagesList):
		im = cv2.imread(imagePath)
		
		if im.shape[1] > maxXDimensionJustForMachingLearningContours:
			im = cv2.resize(im, (maxXDimensionJustForMachingLearningContours, round((maxXDimensionJustForMachingLearningContours/im.shape[1]) * im.shape[0])), interpolation=cv2.INTER_AREA)
		newImgName = imagePath.split("/")[-1]
		cv2.imwrite(args.datadir+'/'+newImgName, im)
	
	### Refine args
	if args.seed is None:
		args.seed = int(time.time())
	torch.manual_seed(args.seed)
	torch.cuda.manual_seed_all(args.seed)
	
	if args.lr_steps is not None and not isinstance(args.lr_steps, list): 
		args.lr_steps = list(map(int, args.lr_steps.split('-'))) 

	dataset_setting_choices = ['BSDS', 'NYUD-image', 'NYUD-hha', 'Multicue-boundary-1', 
				'Multicue-boundary-2', 'Multicue-boundary-3', 'Multicue-edge-1', 'Multicue-edge-2', 'Multicue-edge-3', 'Custom']
	if not isinstance(args.dataset, list): 
		assert args.dataset in dataset_setting_choices, 'unrecognized data setting %s, please choose from %s' % (str(args.dataset), str(dataset_setting_choices))
		args.dataset = list(args.dataset.strip().split('-')) 

	### Create model
	model = getattr(pidistuff.models, args.model)(args)

	### Output its model size, flops and bops
	if args.checkinfo:
		count_paramsM = get_model_parm_nums(model)
		print('Model size: %f MB' % count_paramsM)
		print('##########Time##########', time.strftime('%Y-%m-%d %H:%M:%S'))
		return

	### Define optimizer
	conv_weights, bn_weights, relu_weights = model.get_weights()
	param_groups = [{
			'params': conv_weights,
			'weight_decay': args.wd,
			'lr': args.lr}, {
			'params': bn_weights,
			'weight_decay': 0.1 * args.wd,
			'lr': args.lr}, {
			'params': relu_weights, 
			'weight_decay': 0.0,
			'lr': args.lr
	}]
	info = ('conv weights: lr %.6f, wd %.6f' + \
			'\tbn weights: lr %.6f, wd %.6f' + \
			'\trelu weights: lr %.6f, wd %.6f') % \
			(args.lr, args.wd, args.lr, args.wd * 0.1, args.lr, 0.0)

	print(info)
	

	if args.opt == 'adam':
		optimizer = torch.optim.Adam(param_groups, betas=(0.9, 0.99))
	elif args.opt == 'sgd':
		optimizer = torch.optim.SGD(param_groups, momentum=0.9)
	else:
		raise TypeError("Please use a correct optimizer in [adam, sgd]")

	### Transfer to cuda devices
	if args.use_cuda:
		model = torch.nn.DataParallel(model).cuda()
		print('cuda is used, with %d gpu devices' % torch.cuda.device_count())
	else:
		print('cuda is not used, the running might be slow')

	#cudnn.benchmark = True

	### Load Data
	if 'BSDS' == args.dataset[0]:
		if args.only_bsds:
			train_dataset = BSDS_Loader(root=args.datadir, split="train", threshold=args.eta, ablation=args.ablation)
			test_dataset = BSDS_Loader(root=args.datadir, split="test", threshold=args.eta)
		else:
			train_dataset = BSDS_VOCLoader(root=args.datadir, split="train", threshold=args.eta, ablation=args.ablation)
			test_dataset = BSDS_VOCLoader(root=args.datadir, split="test", threshold=args.eta)
	elif 'Multicue' == args.dataset[0]:
		train_dataset = Multicue_Loader(root=args.datadir, split="train", threshold=args.eta, setting=args.dataset[1:])
		test_dataset = Multicue_Loader(root=args.datadir, split="test", threshold=args.eta, setting=args.dataset[1:])
	elif 'NYUD' == args.dataset[0]:
		train_dataset = NYUD_Loader(root=args.datadir, split="train", setting=args.dataset[1:])
		test_dataset = NYUD_Loader(root=args.datadir, split="test", setting=args.dataset[1:])
	elif 'Custom' == args.dataset[0]:
		train_dataset = Custom_Loader(root=args.datadir)
		test_dataset = pidistuff.edge_dataloader.Custom_Loader(root=args.datadir)
	else:
		raise ValueError("unrecognized dataset setting")

	train_loader = DataLoader(
		train_dataset, batch_size=1, num_workers=args.workers, shuffle=True)
	test_loader = DataLoader(
		test_dataset, batch_size=1, num_workers=args.workers, shuffle=False)

	args.start_epoch = 0
	### Evaluate directly if required
	if args.evaluate is not None:
		checkpoint = load_checkpoint(args)
		if checkpoint is not None:
			args.start_epoch = checkpoint['epoch'] + 1
			if args.evaluate_converted:
				model.load_state_dict(convert_pidinet(checkpoint['state_dict'], args.config, args.use_cuda))
			else:
				model.load_state_dict(checkpoint['state_dict'])
		else:
			raise ValueError('no checkpoint loaded')
		allImageContours = test(test_loader, model, args.start_epoch, args, imgMaximumXDimension, maxXDimensionJustForMachingLearningContours, inputImgsPath)
		print('##########Time########## %s' % (time.strftime('%Y-%m-%d %H:%M:%S')))
		return allImageContours

   
	return []



def click_event(event, x, y, flags, param):
	global mouseClicks
	if event == cv2.EVENT_LBUTTONDOWN:
		print(x,",",y)
		mouseClicks.append([x,y])
		

mouseClicks=[]


def test(test_loader, model, epoch, args, imgMaximumXDimension, maxXDimensionJustForMachingLearningContours, inputImgsPath):
	
	global mouseClicks
	
	edgeThresh=0.5
	# edgeThresh=0
	minLengthContour = 250
	# minAreaContour = 2500
	# erosionKernel=(4,4)
	erosionKernel=(3,3)
	# erosionKernel=(7,7)
	
	goalArcLengthRatioBetweenPts = 1/400 # rough average of 1% edge arclength between edge coords, but if 2 short edges and 2 long edges this will obv be disproportional (possibly in a big way)
	
	octave.addpath(octave.genpath(r'matlab'))
	octave.eval('pkg load image')
	
	
	disp=False
	# disp=True
	
	
	from PIL import Image
	import scipy.io as sio
	model.eval()

	# if args.ablation:
		# img_dir = os.path.join(args.savedir, 'eval_results_val', 'imgs_epoch_%03d' % (epoch - 1))
		# mat_dir = os.path.join(args.savedir, 'eval_results_val', 'mats_epoch_%03d' % (epoch - 1))
	# else:
		# img_dir = os.path.join(args.savedir, 'eval_results', 'imgs_epoch_%03d' % (epoch - 1))
		# mat_dir = os.path.join(args.savedir, 'eval_results', 'mats_epoch_%03d' % (epoch - 1))
	# eval_info = '\nBegin to eval...\nImg generated in %s\n' % img_dir
	# print(eval_info)
	# if not os.path.exists(img_dir):
		# os.makedirs(img_dir)
	# else:
		# print('%s already exits' % img_dir)
	# if not os.path.exists(mat_dir):
		# os.makedirs(mat_dir)
	print(test_loader)
	allImageContours=[]
	avgPieceMaterialColour=None
	baseImageReferenceContourArea=None
	baseImageReferenceContourIndPair=None
	
	
	choosePtsBeforeMainLoop=True
	# choosePtsBeforeMainLoop=False
	
	
	estPieceAreaDict={}
	estRectDict={}
	pieceMaterialPt=None
	referencePtDict={}
	if choosePtsBeforeMainLoop:
		for idx, (image, img_name) in enumerate(test_loader):
			img_name = img_name[0]
			
			estPieceArea=None
			estRect=None
			if True:
				
				tempImg = cv2.imread(inputImgsPath+img_name+str('.jpg'))
				
				mouseClicks=[]
				print("CLICK TWICE TO MAKE 2 DIAGONAL CORNERS OF A RECT ABOUT SIZE OF AVG PIECE")
				cv2.imshow('Contours', tempImg)
				cv2.setMouseCallback('Contours', click_event)
				cv2.waitKey(0)
				cv2.destroyAllWindows()
				pt1=mouseClicks[-2]
				pt3=mouseClicks[-1]
				pt2=[pt1[0], pt3[1]]
				pt4=[pt3[0], pt1[1]]
				tmpRectList = [pt1, pt2, pt3, pt4]
				tmpRect = np.zeros([4, 1, 2])
				for tmpI in range(4):
					tmpRect[tmpI][0][0]=tmpRectList[tmpI][0]
					tmpRect[tmpI][0][1]=tmpRectList[tmpI][1]
				tmpRectArea = cv2.contourArea(tmpRect.astype(int))
				estPieceArea=abs(tmpRectArea)
				# print(estPieceArea)
				# print(tmpRect)
				# input("estPieceArea")
				estRect=tmpRect.astype(int)
			
			estPieceAreaDict[img_name]=estPieceArea
			estRectDict[img_name]=estRect
			
			
			im = cv2.imread(inputImgsPath+img_name+str('.jpg'))
			
			if im.shape[1] > imgMaximumXDimension:
				
				scale = imgMaximumXDimension/im.shape[1]
				
				im = cv2.resize(im, (imgMaximumXDimension, round((imgMaximumXDimension/im.shape[1]) * im.shape[0])))
			
			if True:
				tmpIm = im.copy()
				mouseClicks=[]
				print("PICK REFERENCE PIECE")
				cv2.imshow('Contours', tmpIm)
				cv2.setMouseCallback('Contours', click_event)
				cv2.waitKey(0)
				cv2.destroyAllWindows()
				referencePt = mouseClicks[-1]
				referencePtDict[img_name]=referencePt
				
				if idx==0:
					mouseClicks=[]
					print('PICK PIECE MATERIAL CONTOUR')
					cv2.imshow('Contours', tmpIm)
					cv2.setMouseCallback('Contours', click_event)
					cv2.waitKey(0)
					cv2.destroyAllWindows()
					pieceMaterialPt=mouseClicks[-1]
		
	
	for idx, (image, img_name) in enumerate(test_loader):
		img_name = img_name[0]
		print(img_name)
		result=None
		
		saveMats=False
		
		loadSavedMats=False
		# loadSavedMats=True
		print('------------   loadSavedMats IS '+str(loadSavedMats))
		if not(loadSavedMats):
			
			with torch.no_grad():
				image = image.cuda() if args.use_cuda else image
				_, _, H, W = image.shape
				results = model(image)
				result = torch.squeeze(results[-1]).cpu().numpy()
			results_all = torch.zeros((len(results), 1, H, W))
			for i in range(len(results)):
			  results_all[i, 0, :, :] = results[i]

			# torchvision.utils.save_image(1-results_all, 
					# os.path.join(img_dir, "%s.jpg" % img_name))
			sio.savemat('pidiOUTPUT/tempmat.mat', {'img': result})
			
			if saveMats:
				tmpMatNames=['pidiOUTPUT/g1.mat', 'pidiOUTPUT/g2.mat', 'pidiOUTPUT/g3.mat']
				sio.savemat(tmpMatNames[idx], {'img': result})
		
		fusedarr=None
		im = cv2.imread(inputImgsPath+img_name+str('.jpg'))
		centreImgPt = (int(round(im.shape[1]/2)), int(round(im.shape[0]/2)))
		if True:
			
			result=None
			if not(loadSavedMats):
				result = octave.feval('eval_bsdsfinal')
			else:
				matlabFilenames=['eval_bsdsfinalg1', 'eval_bsdsfinalg2', 'eval_bsdsfinalg3']
				result = octave.feval(matlabFilenames[idx])
			
			fusedarr = cv2.resize(result, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_CUBIC)
		else:
			result1 = Image.fromarray((result * 255).astype(np.uint8))
			result1.save(os.path.join(img_dir, "%s.png" % img_name))
			runinfo = "Running test [%d/%d]" % (idx + 1, len(test_loader))
			print(runinfo)
			
			fusedarr = cv2.resize(result, (im.shape[1], im.shape[0]))
			
			for j in range(fusedarr.shape[0]):
				print(j)
				for k in range(fusedarr.shape[1]):
					if fusedarr[j][k] <= edgeThresh:
						fusedarr[j][k] = 0
			
			fusedarr = np.uint8(fusedarr * 255)
		
		img_grey = fusedarr
		if disp:
			cv2.imshow('Contours', img_grey)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
		
		estPieceArea=None
		estRect=None
		if choosePtsBeforeMainLoop:
			estPieceArea=estPieceAreaDict[img_name]
			estRect=estRectDict[img_name]
		else:
			if True:
				
				tempImg = cv2.imread(inputImgsPath+img_name+str('.jpg'))
				
				referencePt=None
				pieceMaterialPt=None
				
				mouseClicks=[]
				print("CLICK TWICE TO MAKE 2 DIAGONAL CORNERS OF A RECT ABOUT SIZE OF AVG PIECE")
				cv2.imshow('Contours', tempImg)
				cv2.setMouseCallback('Contours', click_event)
				cv2.waitKey(0)
				cv2.destroyAllWindows()
				pt1=mouseClicks[-2]
				pt3=mouseClicks[-1]
				pt2=[pt1[0], pt3[1]]
				pt4=[pt3[0], pt1[1]]
				tmpRectList = [pt1, pt2, pt3, pt4]
				tmpRect = np.zeros([4, 1, 2])
				for tmpI in range(4):
					tmpRect[tmpI][0][0]=tmpRectList[tmpI][0]
					tmpRect[tmpI][0][1]=tmpRectList[tmpI][1]
				tmpRectArea = cv2.contourArea(tmpRect.astype(int))
				estPieceArea=abs(tmpRectArea)
				# print(estPieceArea)
				# print(tmpRect)
				# input("estPieceArea")
				estRect=tmpRect.astype(int)
		if estPieceArea is None:
			print("estPieceArea is None pidicontours")
			exit()
		contours, hierarchy = cv2.findContours(img_grey, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		tempContours = []
		for cntr in contours:
			if abs(cv2.contourArea(cntr))<estPieceArea*2.5: # get rid of too big contours, but not too small cause a lot will be broken contours i.e. 0 area
				tempContours.append(cntr)
		contours=tempContours
		
		erosionimg = np.zeros(im.shape)
		for cntr in contours:
			cv2.drawContours(erosionimg, [cntr.astype(int)], -1, (255,255,255), -1)
			
		if disp:
			print('before erosion')
			cv2.imshow('Contours', erosionimg)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
		
		kernel = np.ones(erosionKernel,np.uint8)
		erosion = np.uint8(cv2.erode(erosionimg,kernel,iterations = 2))
		# erosion = np.uint8(cv2.erode(erosionimg,kernel,iterations = 1))
		
		if disp:
			print('after erosion')
			cv2.imshow('Contours', erosion)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
		
		
		erosion = cv2.cvtColor(erosion,cv2.COLOR_BGR2GRAY)
		# ret,thresh_img = cv2.threshold(erosion, thresh, 255, cv2.THRESH_BINARY)
		# contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		# contours, hierarchy = cv2.findContours(erosion, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		contours, hierarchy = cv2.findContours(erosion, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		
		ydim = im.shape[0]+1
		
		filteredContours = []
		for cntr in contours:
			
			if cv2.arcLength(cntr,False) > minLengthContour and abs(cv2.contourArea(cntr)) > estPieceArea*0.2:
				filteredContours.append(copy.deepcopy(cntr))
		
		im = cv2.imread(inputImgsPath+img_name+str('.jpg'))
		
		if im.shape[1] > imgMaximumXDimension:
			
			scale = imgMaximumXDimension/im.shape[1]
			for cntr in filteredContours:
				for coordI in range(cntr.shape[0]):
					cntr[coordI][0][0]=cntr[coordI][0][0]*scale
					cntr[coordI][0][1]=cntr[coordI][0][1]*scale
			centreImgPt=(centreImgPt[0]*scale, centreImgPt[1]*scale)
			for coordI in range(estRect.shape[0]):
				estRect[coordI][0][0]=estRect[coordI][0][0]*scale
				estRect[coordI][0][1]=estRect[coordI][0][1]*scale
			estPieceArea=abs(cv2.contourArea(estRect))
			
			im = cv2.resize(im, (imgMaximumXDimension, round((imgMaximumXDimension/im.shape[1]) * im.shape[0])))
		
		referencePt=None
		
		if choosePtsBeforeMainLoop:
			referencePt=referencePtDict[img_name]
		else:
			if True:
				tmpIm = im.copy()
				cv2.drawContours(tmpIm, filteredContours, -1, (255,255,255), 1)
				mouseClicks=[]
				print("PICK REFERENCE PIECE")
				cv2.imshow('Contours', tmpIm)
				cv2.setMouseCallback('Contours', click_event)
				cv2.waitKey(0)
				cv2.destroyAllWindows()
				referencePt = mouseClicks[-1]
				
				if idx==0:
					mouseClicks=[]
					print('PICK PIECE MATERIAL CONTOUR')
					cv2.imshow('Contours', tmpIm)
					cv2.setMouseCallback('Contours', click_event)
					cv2.waitKey(0)
					cv2.destroyAllWindows()
					pieceMaterialPt=mouseClicks[-1]
			
		
		if idx==0:
			
			pieceMaterialCntr=None
			smallestMaterialCntrArea=None # if on white paper, the point would be considered to be inside piece as well as large white paper contour, smallest one will be the piece contour
			for cntr in filteredContours:
				if pieceMaterialCntr is None and cv2.pointPolygonTest(cntr, pieceMaterialPt, False)>0:
					pieceMaterialCntr=cntr
					smallestMaterialCntrArea=abs(cv2.contourArea(cntr))
				elif cv2.pointPolygonTest(cntr, pieceMaterialPt, False)>0 and abs(cv2.contourArea(cntr))<smallestMaterialCntrArea:
					pieceMaterialCntr=cntr
					smallestMaterialCntrArea=abs(cv2.contourArea(cntr))
			
			if pieceMaterialCntr is None:
				print('yoyopidicontours1')
				exit()
			
			
			minX = float('inf')
			minY = float('inf')
			for coord in pieceMaterialCntr:
				if coord[0][0]<minX:
					minX = coord[0][0]
				if coord[0][1]<minY:
					minY = coord[0][1]
			minX-=2 # so theres buffer just incase weird stuff, i dont want points to be at (0, y) or (x, 0)
			minY-=2
			for i in range(pieceMaterialCntr.shape[0]):
				pieceMaterialCntr[i][0][0] = pieceMaterialCntr[i][0][0]-minX
				pieceMaterialCntr[i][0][1] = pieceMaterialCntr[i][0][1]-minY
			
			maxX = float('-inf')
			maxY = float('-inf')
			for coord in pieceMaterialCntr:
				if coord[0][0]>maxX:
					maxX = coord[0][0]
				if coord[0][1]>maxY:
					maxY = coord[0][1]
			maxX+=2
			maxY+=2
			
			maxX=int(math.ceil(maxX))
			maxY=int(math.ceil(maxY))
			
			x, y = np.meshgrid(np.arange(maxX), np.arange(maxY)) # make a canvas with coordinates
			x, y = x.flatten(), y.flatten()
			points = np.vstack((x,y)).T 
			
			wholePoly = []
			for coord in pieceMaterialCntr:
				wholePoly.append((coord[0][0], coord[0][1]))
			p = Path(wholePoly) # make a polygon
			grid = p.contains_points(points)
			
			actualPtsInside=[]
			for i in range(len(grid)): # grid.shape[0]
				if grid[i]:
					actualPtsInside.append(points[i])
			
			ptsInside=actualPtsInside
			
			avgPieceMaterialColour=None
			img_contours=im.copy()
			avgR=0
			avgColourCtr=0
			avgG=0
			avgB=0
			for tmpPtInside in ptsInside:
				actualPtInside = (int(round(tmpPtInside[0]+minX)), int(round(tmpPtInside[1]+minY)))
				tmpColour = img_contours[actualPtInside[1]][actualPtInside[0]] # x, y flipped when working directly with image in opencv
				# print(tmpColour)
				avgB+=tmpColour[0]
				avgG+=tmpColour[1]
				avgR+=tmpColour[2]
				avgColourCtr+=1
			if avgColourCtr!=0:
				avgR=avgR/avgColourCtr
				avgG=avgG/avgColourCtr
				avgB=avgB/avgColourCtr
				
				pix1 = np.zeros([1,1,3]).astype(np.uint8)
				pix1[0][0][0] = min(int(round(avgB)), 255)
				pix1[0][0][1] = min(int(round(avgG)), 255)
				pix1[0][0][2] = min(int(round(avgR)), 255)
				
				# pix1 = cv2.cvtColor(pix1 , cv2.COLOR_HSV2BGR_FULL)
				# print(pix1)
				pix1 = cv2.cvtColor(pix1 , cv2.COLOR_BGR2Lab)
				avgPieceMaterialColour=pix1
			
		referenceCntr=None
		referenceCntrInd=None
		for cntrI, cntr in enumerate(filteredContours):
			if cv2.pointPolygonTest(cntr, referencePt, False)>0:
				referenceCntr=cntr
				referenceCntrInd=cntrI
		if referenceCntr is None:
			print('yoyopidicontours2')
			exit()
		referenceCntrArea = cv2.contourArea(referenceCntr)
		print("referenceCntrArea")
		print(referenceCntrArea)
		
		
		if idx==0:
			baseImageReferenceContourArea=referenceCntrArea
			baseImageReferenceContourIndPair=(idx, referenceCntrInd)
		
		im = cv2.imread(inputImgsPath+img_name+str('.jpg'))
		
		
		if disp:
			img_contours = im.copy()
			img_contours2 = im.copy()
			approxcontours = np.zeros(im.shape)
			justContours = np.zeros(im.shape)
			if im.shape[1] > imgMaximumXDimension:
				img_contours2 = cv2.resize(img_contours2, (imgMaximumXDimension, round((imgMaximumXDimension/img_contours2.shape[1]) * img_contours2.shape[0])))
				justContours = cv2.resize(justContours, (imgMaximumXDimension, round((imgMaximumXDimension/justContours.shape[1]) * justContours.shape[0])))
				approxcontours = cv2.resize(approxcontours, (imgMaximumXDimension, round((imgMaximumXDimension/approxcontours.shape[1]) * approxcontours.shape[0])))
			
			
			cv2.drawContours(justContours, filteredContours, -1, (255,255,255), 1)
			
			cv2.drawContours(img_contours, contours, -1, (0,0,255), 2)
			cv2.drawContours(img_contours2, filteredContours, -1, (120,120,255), 1)
			
			cv2.imshow('Contours', img_contours)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
			
			cv2.imshow('Contours', img_contours2)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
			
			cv2.imshow('Contours', justContours)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
			
			for k in range(len(filteredContours)):
				print(filteredContours[k].shape[0])
				print()
			
			cv2.imshow('Contours', approxcontours)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
			
			
			# exit()
		
		
		if True:
			newFilteredContours = []
			for cntr in filteredContours:
				totalArcLength=0
				for cntrI in range(cntr.shape[0]-1):
					tmpC1=cntr[cntrI][0]
					tmpC2=cntr[cntrI+1][0]
					totalArcLength+=getDistance(tmpC1[0], tmpC2[0], tmpC1[1], tmpC2[1])
				goalArcLength = goalArcLengthRatioBetweenPts*totalArcLength
				
				newCntr=[]
				
				distBetweenPtsGoal = goalArcLength
				for cntrI in range(cntr.shape[0]-1):
					
					startContourIndRatio = cntrI
					endContourIndRatio = cntrI+1
					
					tmpC1=cntr[cntrI][0]
					tmpC2=cntr[cntrI+1][0]
					planeSegArcLength=getDistance(tmpC1[0], tmpC2[0], tmpC1[1], tmpC2[1])
					
					if planeSegArcLength >= distBetweenPtsGoal:
						floatSpreadAmtUsingExactGoal = planeSegArcLength/distBetweenPtsGoal
						spreadOption1Amt = math.floor(floatSpreadAmtUsingExactGoal)
						spreadOption2Amt = math.ceil(floatSpreadAmtUsingExactGoal)
						spreadOption1Dist = planeSegArcLength/spreadOption1Amt
						spreadOption2Dist = planeSegArcLength/spreadOption2Amt
						
						distBetweenPtsForThisPlaneSeg = None
						goalPtsAmt = None
						if abs(spreadOption1Dist-distBetweenPtsGoal)<abs(spreadOption2Dist-distBetweenPtsGoal):
							distBetweenPtsForThisPlaneSeg=spreadOption1Dist
							goalPtsAmt = spreadOption1Amt
						else:
							distBetweenPtsForThisPlaneSeg=spreadOption2Dist
							goalPtsAmt = spreadOption2Amt
						
						finalPlaneSeg = []
						
						coveredDist = 0
						
						i=startContourIndRatio
						veryTmpDist = planeSegArcLength
						
						amtOnLine = (veryTmpDist)/distBetweenPtsForThisPlaneSeg + 1
						# print(amtOnLine)
						amtOnLine = math.floor(amtOnLine)
						if amtOnLine>=1:
							
							ratioBetweenPtsForThisSeg = distBetweenPtsForThisPlaneSeg/veryTmpDist
							distToFirstPtOnLine = 0
							ratioOfFirstPt = 0
							
							for j in range(amtOnLine):
								tmpRatio = ratioOfFirstPt+j*ratioBetweenPtsForThisSeg
								tmpReqCoordX = cntr[i][0][0] + (cntr[i+1][0][0]-cntr[i][0][0])*tmpRatio
								tmpReqCoordY = cntr[i][0][1] + (cntr[i+1][0][1]-cntr[i][0][1])*tmpRatio
								tmpCoord = [tmpReqCoordX, tmpReqCoordY]
								finalPlaneSeg.append(tmpCoord)
								
						else:
							print("huh? how does the first if condition imply at least 1 pt here but then second if condition says none111?")
							exit()
							# pass
						
						
						if endContourIndRatio-math.floor(endContourIndRatio)==0:
							if len(finalPlaneSeg)-1 < goalPtsAmt:
								finalPlaneSeg.append([cntr[endContourIndRatio][0][0], cntr[endContourIndRatio][0][1]])
						
						if len(finalPlaneSeg)-1 < goalPtsAmt:
							print("prob not the end of the world but still very weird")
							exit()
						
						
						finalPlaneSeg.pop(-1)
						
						for tmpCoord in finalPlaneSeg:
							newCntr.append([[tmpCoord[0], tmpCoord[1]]])
						
					else:
						newCntr.append([[cntr[cntrI][0][0], cntr[cntrI][0][1]]])
				newCntr.append([[cntr[cntr.shape[0]-1][0][0], cntr[cntr.shape[0]-1][0][1]]])
				
				newFilteredContours.append(np.asarray(newCntr))
				
			filteredContours=newFilteredContours
		
		allImageContours.append({"image_path": inputImgsPath+img_name+str('.jpg'), "contours": filteredContours, "imgref": inputImgsPath+img_name+str('.jpg'), "ydim": ydim, "horizontalFov": None, "verticalFov": None, "imageSizeX": im.shape[1], "imageSizeY": im.shape[0], "focalLength": None, "centreImgPt": centreImgPt, "referenceCntrArea": referenceCntrArea, "referenceCntrInd": referenceCntrInd}) #placeholder image reference/identifier is the path to the image
	if True:
		baseImageReferenceContourArea=5
	return allImageContours, avgPieceMaterialColour, baseImageReferenceContourArea, baseImageReferenceContourIndPair#, maxydim

def getDistance(x1, x2, y1, y2):
	diffX = abs(x2 - x1)
	diffY = abs(y2 - y1)
	return math.hypot(diffX, diffY) # sqrt a^2 + b^2


