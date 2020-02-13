%% Start by subsampling the video to the frame rate of the annotations -256 frames per second
%Selext some of the videos and subsample accordingly
% read the side videos from each horse
% Artiste is from the left
%Horatio is from the left
%Lacantus is from the left
%Larry is from the left (leave this one out, it's a different colour)
%Laz is from the left
%Leando is from the left
%Lord is from the left
%get a list of video and mat file names per horse
addpath('/home/natasha/workspace/mexopencv');
addpath('/home/natasha/workspace/mexopencv/opencv_contrib/');

root = '/home/natasha/workspace/OpenHorseData/';
horses = dir(root);
horses = horses(3:end);
horseLabels = {};
horseVids ={};
%loop through it all

for h = 1:length(horses)
    horse_path = strcat(root,horses(h).name,'/');
    %read all the video4
    horse_ = dir(strcat(horse_path,'*video4.mp4'));
    %read corresponding mat files
    horseVidpath = strcat(horse_path,extractfield(horse_,'name'));
    %find the corresponding mat files
    horseLabelpath = {};
    for vid = 1:length(horseVidpath)
        horseLabelpath{vid} = strcat(extractBetween(horseVidpath{vid},'','_vid'),'.mat');
        %check whether there's a corresponding mat file
        if isfile(horseLabelpath{vid})
        else
            disp('error!');
        end
    end
    horseLabels{h} = horseLabelpath;
    horseVids{h} =horseVidpath;
end

%loop through and store the image and the corresponding annotations -add
%the visibility information from view angle diescribed above and the
%special mat file

tot = 0;
%loop through all the horses
for h = 1:length(horses)
    vidsPath = horseVids{h};
    labelsPath = horseLabels{h}; 
    for v = 1:length(vidsPath)
%loop through each horse video
%draw out a couple of these just so that we're sure we're doing the right
%thing
USE_MEXOPENCV = 0;

%read these from the server
if USE_MEXOPENCV
    vid = cv.VideoCapture(fullfile(vidsPath{v}));
    pause(1)
else
    vid = VideoReader(fullfile(vidsPath{v}));
end

% 
% currAxes = subplot(1,2,1);
% 
% 
% currAxes0 = subplot(1,2,2);




%subsample the video and annotations at the same rate
labelFrame = load(fullfile(labelsPath{v}{1}));
marks = (load('/home/natasha/workspace/Colab Notebooks/markersLeft.mat'));
marker = cell2mat(marks.markers);
markUse = marker~=3;
mark_len = (size(labelFrame.(string(fieldnames(labelFrame))).Trajectories.Labeled.Data((markUse==1),[1,3],:)));

count_=vid.Duration-floor(vid.Duration);
m = (mark_len(3)-1)/((vid.Duration));
c = 1;
vid.CurrentTime = count_+1;
while hasFrame(vid)
    
    %figure out how to synchronise the annotations and the videos perfectly
    %filter out the unnnecessary, and add a column for the visibility (need
    %to Email Elin for these)
    
    
    vidFrame = readFrame(vid);

%     image(vidFrame, 'Parent', currAxes);
%     currAxes.Visible = 'off';
%     pause(1/vid.FrameRate);
    


    %display all this together
    label = labelFrame.(string(fieldnames(labelFrame))).Trajectories.Labeled.Data((markUse==1),[1,3],ceil(count_*m+c));
    visMark = transpose(marker(markUse==1));
    vidMark = horzcat(label,visMark);
    if sum(isnan(vidMark(:))) >0
        count_ = count_+0.5;
        vid.CurrentTime = count_+0.5;
        continue
    end


    count_ = count_+0.5;
    save(sprintf('/home/natasha/workspace/Colab Notebooks/labels/%06d.mat',tot),'vidMark');
    imwrite(vidFrame,sprintf('/home/natasha/workspace/Colab Notebooks/images/%06d.png',tot));
    tot = tot+1;
    vid.CurrentTime = count_+0.5;
    
%     %select a subset of the markers, select only the visible markers

%     lab = label(vidMark(:,3)==2,:);
%     subplot(1,2,2);
%     image(plot(lab(:,1),lab(:,2),'*'),'Parent',currAxes0);
   
    
end
    end
end
