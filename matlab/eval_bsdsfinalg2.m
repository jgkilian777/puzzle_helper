function Q = eval_bsds()
% function [Q, L, M] = eval_bsds()
% clear all;

fn = cd;
disp(fn)
disp('0000000000')
% fn = fullfile(fn, '..');
% fnMAT = [fn, '\pidiOUTPUT\eval_results\mats_epoch_013']
% fnNMS = [fn, '\pidiOUTPUT\eval_results\nms']
% data_dir = 'map_folder/table5_pidinet';
% ablation = false;
% suffix = '_epoch_019';

% addpath(fnMAT)
% addpath(fnNMS)
% Data directory data_dir should be defined outside.
% fprintf('Data dir: %s\n', data_dir);
% addpath(genpath([fn, '\edge_eval_matlab\edges']));
% addpath(genpath([fn, '\edge_eval_matlab\toolbox.badacost.public']));
% addpath(genpath([fn, '\edge_eval_matlab\toolbox.badacost.public\channels']));
% addpath(genpath([fn, '\edge_eval_matlab\toolbox.badacost.public\channels\private']));
% addpath([fn, '\edge_eval_matlab\toolbox.badacost.public\channels']);
% addpath([fn, '\edge_eval_matlab\toolbox.badacost.public\channels\private']);
% addpath([fn, '\edge_eval_matlab\toolbox.badacost.public\channels\private\convConst.mex']);
% disp(path)
% rehash

% tic;
% Section 1: NMS process (formerly nms_process.m from HED repo).
% disp('NMS process...')
% mat_dir = fullfile(data_dir, ['mats', suffix]);
% mat_dir = fnMAT;
% nms_dir = fullfile(data_dir, ['nms', suffix]);
% nms_dir = fnNMS;
% mkdir(nms_dir)

% files = dir(mat_dir);
% files = files(3:end,:);  % It means all files except ./.. are considered.
% mat_names = cell(1,size(files, 1));
% nms_names = cell(1,size(files, 1));
% for i = 1:size(files, 1),
    % mat_names{i} = files(i).name;
    % nms_names{i} = [files(i).name(1:end-4), '.png']; % Output PNG files.
% end
disp('111111')

% data1 = cell(size(mat_names,2))
% data2 = cell(size(mat_names,2))
% matObj = matinput; % Read MAT files.
% matObj = load(matinput); % Read MAT files.
% varlist = who(matObj);

matObj = load(fullfile([fn, '\pidiOUTPUT\g2.mat'])); % Read MAT files.
varlist = who('-file', fullfile([fn, '\pidiOUTPUT\g2.mat']));

x = matObj.(char(varlist));
% E=convTri(single(x),1);
E=convTri(single(x),1, 1, 1);
% [Ox,Oy]=gradient2(convTri(E,4));
[Ox,Oy]=gradient2(convTri(E,4, 1, 1));
[Oxx,~]=gradient2(Ox); [Oxy,Oyy]=gradient2(Oy);
O=mod(atan(Oyy.*sign(-Oxy)./(Oxx+1e-5)),pi);
% E=edgesNmsMex(E,O,1,5,1.01,4);
E=edgesNmsMex(E,O,1,5,1.06,4); % not bad<<
% E=edgesNmsMex(E,O,2,5,1.01,4);
% E=edgesNmsMex(E,O,1,2,1.01,4);
Q=uint8(E*255);
% imwrite(uint8(E*255),fullfile(nms_dir, nms_names{i}))
% for i = 1:size(mat_names,2),
% disp('aaaaa')
% disp(fullfile(mat_dir, mat_names{i}))
% disp([mat_dir, '\', mat_names{i}])
% matObj = matfile(fullfile(mat_dir, mat_names{i})); % Read MAT files.
% matObj = matfile([mat_dir, mat_names{i}]); % Read MAT files.
% matObj = load([mat_dir, '\', mat_names{i}]); % Read MAT files.
% matObj = load(fullfile(mat_dir, mat_names{i})); % Read MAT files.
% matObj = matinput; % Read MAT files.
% disp('222222')
% varlist = who(matObj);
% varlist = who('-file', fullfile(mat_dir, mat_names{i}));
% varlist = who(matObj);
% disp('3333333')
% x = matObj.(char(varlist));
% disp('123123123')
% disp(x)
% dist(single(x))
% y1 = single(x)
% disp('hi')
% Q=single(x);
% data1{i}=single(x);
% data2{i}=single(x);
% M='hii'
% M=single(x);
% =Q
% disp(class(Q))
% end
% E=feval('convTri',single(x),1);
% E=convTri(single(x),1);
% disp('444444')
% [Ox,Oy]=gradient2(convTri(E,4));
% [Oxx,~]=gradient2(Ox); [Oxy,Oyy]=gradient2(Oy);
% disp('555555')
% O=mod(atan(Oyy.*sign(-Oxy)./(Oxx+1e-5)),pi);
% E=edgesNmsMex(E,O,1,5,1.01,4);
%E=edgesNmsMex(E,O,2,5,1.01,4);
% imwrite(uint8(E*255),fullfile(nms_dir, nms_names{i}))
% end
% Q=data1;
% L=data2;
% Q='yoyo'
% Section 2: Evaluate the edges (formerly EvalEdge.m from HED repo).
% disp('Evaluate the edges...');
% if ablation
    % gtDir  = 'data/groundTruth/val';
% else
    % gtDir  = 'data/groundTruth/test';
% end
%resDir = fullfile(data_dir, 'nms');
% resDir = nms_dir;
% edgesEvalDir('resDir',resDir,'gtDir',gtDir, 'thin', 1, 'pDistr',{{'type','parfor'}},'maxDist',0.0075);

% figure; 
% edgesEvalnoPlot(resDir,'PiDiNet');

% rmdir(mat_dir, 's');
% rmdir(nms_dir, 's');
% toc;

