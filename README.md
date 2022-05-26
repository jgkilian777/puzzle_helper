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

After running mainfile.py, press enter when prompted and when the first image is displayed click 2 diagonal corners of any piece then press a key e.g. spacebar
![An example of a piece with 2 diagonal corners circled](/images/clickcorners.png)
Then when prompted, click anywhere inside the reference piece that appears in every image for this batch and press a key
![An example of the reference piece with a circle inside](/images/clickrefpiece.png)
Lastly, when prompted, click inside the flipped piece that exposes the piece material that only appears in the first image and press a key
![An example of the flipped piece with a circle inside](/images/clickpiecematerial.png)

Then for each image after the first, repeat the steps above except for the flipped piece since that should only appear in the first image.

When given results at the end, press a button e.g. spacebar to go through results, once true positive results start to be too sparse it's probably time to take new images of a different/remaining set of pieces and rerunning for more matches.

If possible, shuffle orientation/position of remaining pieces rather than leaving them in the same place and adding a new batch of pieces.

The main matching parameters can be found here: https://github.com/jgkilian777/puzzle_helper/blob/922b672c6b67b7cca52936257270583fe87c1876/edgeMatchingUtils.py#L3697
(start of mainEdgeSimilarity function)
The specific parameters that should be tweaked to control compatibility constraints to allow for more matches with more false positives or less matches with faster runtime can be seen being referenced here: https://github.com/jgkilian777/puzzle_helper/blob/922b672c6b67b7cca52936257270583fe87c1876/edgeMatchingUtils.py#L3804
(near the end of the parameters block of code under looseConstraints and/or tightColourConstraints conditional statements)

args.use_cuda = False
	# args.use_cuda = True
  
  disp=False
	# disp=True
  
  # loadSavedMats=False
		loadSavedMats=True
    
    

