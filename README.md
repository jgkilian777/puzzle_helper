# puzzle_helper


refs:

https://github.com/zhuoinoulu/pidinet

https://github.com/xwjabc/hed





Installation:

( https://github.com/zhuoinoulu/pidinet )

Download this repo

Install the dependencies in an anaconda environment using puzzlehelper.yml
(There may be issues with gpu/cuda versions and pytorch, refer to pytorch documentation if there are issues)

Pidinet and others like HED use Piotr's Structured Forest matlab toolbox for post processing edge data.
Download the contents of this folder https://github.com/xwjabc/hed/tree/master/eval

Place the "edges" folder and the "toolbox.badacost.public" folder inside the "matlab" folder in this project.

Open a seperate anaconda prompt and within the project environment navigate to the matlab folder, enter "octave" in the anaconda prompt to run the octave cli
Enter "run toolboxCompile.m" to run the compiler file to compile the matlab files necessary for this project.
If successful, close the anaconda prompt window that was used with octave.

In the main anaconda prompt run "python mainfile.py"

Usage:

Parameters are currently tuned to work with images that have 1:1 aspect ratio, around 3024x3024 resolution and with images taken at a distance from the pieces such that the long side of an A4 piece of paper roughly takes up the length of the image.

Require at least one image as input. All images must have the same piece roughly in the center, oriented in the same direction in each image for consistency.
One image must have a piece flipped over to expose the colour of the material that the pieces are made out of and this image must have the lowest alphanumeric file name (e.g. 0.jpg).

The images should be taken with the camera (specifically image plane) being as parallel as possible to the table/piece plane.

Flash should be on when the images are taken.

Any time mainfile.py is run with a different set of images, make sure the pidiIMGS folder is empty and inputimgs folder only contains the new set of images.

After running mainfile.py, press enter when prompted and when the first image is displayed click ... corners...

args.use_cuda = False
	# args.use_cuda = True
  
  disp=False
	# disp=True
  
  # loadSavedMats=False
		loadSavedMats=True
    
    

