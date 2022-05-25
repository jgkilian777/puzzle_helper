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

args.use_cuda = False
	# args.use_cuda = True
  
  disp=False
	# disp=True
  
  # loadSavedMats=False
		loadSavedMats=True
    
    

