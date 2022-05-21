opts={'--mex', '-DMATLAB_MEX_FILE', '-o'};

% list of files (missing /private/ part of directory)
fs={'channels/convConst.cpp', 'channels/gradientMex.cpp',...
 'edges/edgesNmsMex.cpp'
};
n=length(fs); 

useSpecialPath=zeros(1,n);
useSpecialPath(3)=1;

rd=fileparts(mfilename('fullpath')); rd=[rd, '/edge_eval_matlab/toolbox.badacost.public']; tic;
errmsg=' -> COMPILE FAILURE: ''%s'' %s\n';
for i=1:n
  try
    if(useSpecialPath(i)), [d,f1,e]=fileparts(fs{i}); f=[rd '/' d '/private2/' f1]; else [d,f1,e]=fileparts(fs{i}); f=[rd '/' d '/private/' f1]; end
   
    fprintf(' -> %s\n',[f e]); mex(opts{:}, [f '.' mexext], [f e]);
  catch err, fprintf(errmsg,[f1 e],err.message); end
end

disp('..................................Done Compiling'); toc;
