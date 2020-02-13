
#### Written by: Nasha Meoli

#### Date: 09/30/2019

#### Aim: Train a Pose Estimation Network to determine the pose in horses. 

#### Dataset: A description of the dataset can be found in the file , change the name of the data direcotry in the matlab to code to the location of your download.


## OVERVIEW OF THE METHOD

The complete pipeline can be seen in the figure below:


![preprocessing.png](attachment:preprocessing.png)


The OpenPose paper can be found at: https://arxiv.org/abs/1812.08008

The data available for this project consisted of MoCap data captured from horses running on a treadmill. The marker data was recorded at 256 fps and the video data at 25 fps; the timestamps for this data were synchronised. The extraction of video frames and corresponding MoCap frame was done by use of the code found in MarkerData/videoProcessing.m.

The spatial data from these two modalities was unaligned such that they were captured on different axis without a straightforward mapping between the two. It was therefore necessary to align these keypoints. The code used can be found in toCoco.py. The method consisted of using the bounding box from the DeepLabv3 segmentation network to find the scaling factor between the two sets of axis, the keypoints were then scaled and shifted to coincide with the region of the image in which the horse was. 

The horse images had the markers visible on the horses and it was necessary to blur these markers so that they did not interfere with the feature learning in subsequent steps. Using the segementation from a pre-trained DeepLabv3 network a median filter was applied to the image in the region containing the horse. Experimentation with different filters is recommended to investigate the effects on the learnt features. The code for this can be found in toCoco.py. Run this code to store the new images and create a train, val and test split in directories as required by the OpenPose network found at: https://github.com/tensorboy/pytorch_Realtime_Multi-Person_Pose_Estimation


## PROGRESS

The entire pre-processing pipeline was completed; synchronised and aligned data samples can be found in the following directories.

Attempts were made at editing the OpenPose repository found at https://github.com/tensorboy/pytorch_Realtime_Multi-Person_Pose_Estimation for the number of keypoints specific to this dataset and for the loading of a custom datatset.

Greater debugging of this repository would be needed to repair all the errors. 


## PRE-REQUISITES

Pytorch Version 1.2.0

CUDA Version 9.2.148

MATLAB


```python

```
