# -*- coding: utf-8 -*-
"""pytorch_vision_deeplabv3_resnet101.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Y6QX3lj5VPccx7F-vHZm7MRuuVE5q6Ul

### This notebook is optionally accelerated with a GPU runtime.
### If you would like to use this acceleration, please select the menu option "Runtime" -> "Change runtime type", select "Hardware Accelerator" -> "GPU" and click "SAVE"

----------------------------------------------------------------------

# Deeplabv3-ResNet101

*Author: Pytorch Team*

**DeepLabV3 model with a ResNet-101 backbone**

_ | _
- | -
![alt](https://pytorch.org/assets/images/deeplab1.png) | ![alt](https://pytorch.org/assets/images/deeplab2.png)
"""
import pdb
import torch
import numpy as np
from PIL import Image
from matplotlib import cm
import matplotlib.pyplot as plt
import pylab
import imageio
from PIL import Image
from torchvision import transforms
import cv2
from skimage import measure                        # (pip install scikit-image)
from shapely.geometry import Polygon, MultiPolygon # (pip install Shapely)
import json
from scipy.io import loadmat
model = torch.hub.load('pytorch/vision', 'deeplabv3_resnet101', pretrained=True)
model.eval()


"""All pre-trained models expect input images normalized in the same way,
i.e. mini-batches of 3-channel RGB images of shape `(N, 3, H, W)`, where `N` is the number of images, `H` and `W` are expected to be at least `224` pixels.
The images have to be loaded in to a range of `[0, 1]` and then normalized using `mean = [0.485, 0.456, 0.406]`
and `std = [0.229, 0.224, 0.225]`.

The model returns an `OrderedDict` with two Tensors that are of the same height and width as the input Tensor, but with 21 classes.
`output['out']` contains the semantic masks, and `output['aux']` contains the auxillary loss values per-pixel. In inference mode, `output['aux']` is not useful.
So, `output['out']` is of shape `(N, 21, H, W)`. More documentation can be found [here](https://pytorch.org/docs/stable/torchvision/models.html#object-detection-instance-segmentation-and-person-keypoint-detection).
"""

#utside the loop through the entire set of images
annotations = []
images=[]
for f in range(1000):
    
    
    
    # sample execution (requires torchvision)
    
    # input_image = Image.open(filename)
    image = Image.open('/home/nasha/workspace/Colab Notebooks/images/{0:06d}.png'.format(f))
    label = (loadmat("/home/nasha/workspace/Colab Notebooks/labels/{0:06d}.mat".format(f))['vidMark'])
    
    input_image = Image.fromarray(np.uint8(image))
    preprocess = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model
    
    # move the input and model to GPU for speed if available
    if torch.cuda.is_available():
        input_batch = input_batch.to('cuda')
        model.to('cuda')
    
    with torch.no_grad():
        output = model(input_batch)['out'][0]
    output_predictions = output.argmax(0)
    
    
    """The output here is of shape `(21, H, W)`, and at each location, there are unnormalized proababilities corresponding to the prediction of each class.
    To get the maximum prediction of each class, and then use it for a downstream task, you can do `output_predictions = output.argmax(0)`.
    
    Here's a small snippet that plots the predictions, with each color being assigned to each class (see the visualized image on the left).
    """
    
    #@title Segmentation Result
    # create a color pallette, selecting a color for each class
    palette = torch.tensor([2 ** 25 - 1, 2 ** 15 - 1, 2 ** 21 - 1])
    
    colors = torch.as_tensor([i for i in range(21)])[:, None] * palette
    colors = (colors % 255).numpy().astype("uint8")
    
    #classes = ['__background__', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
    #  'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike',
    #  'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
    
    # plot the semantic segmentation predictions of 21 classes in each color
    r = Image.fromarray(output_predictions.byte().cpu().numpy()).resize(input_image.size)
    
    

    
    #@title Blur the input image according to the segmentation results
    
    out_img = output_predictions.cpu().numpy()
    in_img = image
    
    
    
    blurred = cv2.medianBlur(np.asarray(in_img),11)

    
    # get the horse part of the segmentation
    
    #get an image with only the horse blurred
    out_ = output_predictions.byte().cpu().numpy()
    out_3 =(np.stack([out_,out_,out_], axis=2))
    
    bit_mask = np.where(out_3 == 13,blurred,image)
    
    horse_mask = np.where(out_3 == 13,[ 13, 121, 148],[0,0,0])
    
    

    
    
    
    ## convert output segmentation mask to coco format
    
    
    
    def create_sub_masks(mask_image):
        width, height = mask_image.size
    
        # Initialize a dictionary of sub-masks indexed by RGB colors
        sub_masks = {}
        for x in range(width):
            for y in range(height):
                # Get the RGB values of the pixel
                pixel = mask_image.getpixel((x,y))[:3]
    
                # If the pixel is not black...
                if pixel != (0, 0, 0):
                    # Check to see if we've created a sub-mask...
                    pixel_str = str(pixel)
                    sub_mask = sub_masks.get(pixel_str)
                    if sub_mask is None:
                       # Create a sub-mask (one bit per pixel) and add to the dictionary
                        # Note: we add 1 pixel of padding in each direction
                        # because the contours module doesn't handle cases
                        # where pixels bleed to the edge of the image
                        sub_masks[pixel_str] = Image.new('1', (width+2, height+2))
    
                    # Set the pixel value to 1 (default is 0), accounting for padding
                    sub_masks[pixel_str].putpixel((x+1, y+1), 1)
    
        return sub_masks
    # Create sub-mask annotation
    # Here's a python function that will take a sub-mask, create polygons out of the shapes inside, and then return an annotation dictionary. This is where we remove the padding mentioned above.
    
    
    def create_sub_mask_annotation(sub_mask, image_id, category_id, annotation_id, is_crowd):
        # Find contours (boundary lines) around each sub-mask
        # Note: there could be multiple contours if the object
        # is partially occluded. (E.g. an elephant behind a tree)
        contours = measure.find_contours(sub_mask, 0.5, positive_orientation='low')
    
        segmentations = []
        polygons = []
        for contour in contours:
            # Flip from (row, col) representation to (x, y)
            # and subtract the padding pixel
            for i in range(len(contour)):
                row, col = contour[i]
                contour[i] = (col - 1, row - 1)
    
            # Make a polygon and simplify it
            poly = Polygon(contour)
            try:
                poly0 = poly.simplify(1, preserve_topology=False)
                          
                segmentation = np.array(poly0.exterior.coords).ravel().tolist()
                poly = poly0
            except:
                segmentation = np.array(poly.exterior.coords).ravel().tolist()
                
            polygons.append(poly)
            segmentations.append(segmentation)
    
        # Combine the polygons to calculate the bounding box and area
        multi_poly = MultiPolygon(polygons)
        x, y, max_x, max_y = multi_poly.bounds
        width = max_x - x
        height = max_y - y
        
        
        bbox = (x, y, width, height)
        area = multi_poly.area
    
        annotation = {
            'segmentation': segmentations,
            "num_keypoints": 27,
            'iscrowd': is_crowd,
            'image_id': image_id,
            'category_id': category_id,
            'id': annotation_id,
            'bbox': bbox,
            'area': area
        }
    
        return annotation
    # Putting it all together
    # Finally, we'll use these two functions on our images
    
    
    
    # plant_book_mask_image = Image.open('/path/to/images/plant_book_mask.png')
    # bottle_book_mask_image = Image.open('/path/to/images/bottle_book_mask.png')
    
    horse_mask_image = Image.fromarray(horse_mask.astype("uint8"))
    
    # mask_images = [plant_book_mask_image, bottle_book_mask_image]
    
    mask_images = [horse_mask_image]
    
    # Define which colors match which categories in the images
    horse =0
    # houseplant_id, book_id, bottle_id, lamp_id = [1, 2, 3, 4]
    # __background__, aeroplane, bicycle, bird, boat, bottle, bus, car, cat, chair, cow, diningtable, dog, horse, motorbike, person, pottedplant, sheep, sofa, train, tvmonitor = np.arange(21)
    category_ids = {
        0: {
            str(tuple(colors[13])): horse,
                }
    
    }
    
    is_crowd = 0
    
    # These ids will be automatically increased as we go
    annotation_id = 1
    image_id = f
    
    # Create the annotations
    
    for mask_image in mask_images:
      #read image
      #generate mask
      #Read annotation corresponding
      #generate keypoints and count them (this will be the same for every video of a particular kind)
        sub_masks = create_sub_masks(mask_image)
        for color, sub_mask in sub_masks.items():
            category_id = category_ids[0][color]
            annotation = create_sub_mask_annotation(sub_mask, image_id, category_id, annotation_id, is_crowd)
            annotations.append(annotation)
            annotation_id = f
        image_id = f
    info = {
        "description": "UTH Horse Dataset",
        "version": "1.0",
        "year": 2013,
        
        "date_created": "2013"
    }
    
    categories= [
        {
            "supercategory": "animal",
            "id": f,
            "name": "horse",
            "keypoints": [
                "Poll 1","CristaFac_R 2","Shoulder_R 3","Elbow_R 4","Carpus_R 5","Fetl_RF 6","Hoof_RF 7","Hoof_RH 8",
                "Fetl_RH 9","Tarsus_R 10","Knee_R 11","Hip_R 12","TubSac 13","TubCox_R 14","T8 15","CristaFac_L 16","Shoulder_L 17",
                "Elbow_L 18","Carpus_L 19","Fetl_LF 20","Hoof_LF 21","Hoof_LH 22","Fetl_LH 23","Tarsus_L 24","Knee_L 25","Hip_L 26",
                "TubCox_L 27"
            ],
            "skeleton": [
                [1,2],[1,16],[1,15],[15,13],[13,14],[13,27],[14,12],[27,26],[12,11],[26,25],
                [11,10],[25,24],[10,9],[24,23],[9,8],[23,22],[15,3],[15,17],[3,4],
                [17,18],[4,5],[18,19],[5,6],[19,20],[6,7],[20,21]
            ]
        }
    ]
    image_ = {"filename": "{0:06d}.png".format(f), "id":f}
    images.append(image_)
    # #do augmentation in the open pose section
    # {
    #     "info": {...},
    #     "licenses": [...],
    #     "images": [...],
    #     "annotations": [...],
    #     "categories": [...], <-- Not in Captions annotations
    #     "segment_info": [...] <-- Only in Panoptic annotations
    # }
    
    # "annotations": [
    #     {
    #         "segmentation": [[204.01,306.23,...206.53,307.95]],
    #         "num_keypoints": 15,
    #         "area": 5463.6864,
    #         "iscrowd": 0,
    #         "keypoints": [229,256,2,...,223,369,2],
    #         "image_id": 289343,
    #         "bbox": [204.01,235.08,60.84,177.36],
    #         "category_id": 1,
    #         "id": 201376
    #     }
    # ]
    
    #view a couple of sample images with the above alone
    
    xmax,xmin = np.nanmax(label[:,0]),np.nanmin(label[:,0])
    ymax,ymin = np.nanmax(label[:,1]),np.nanmin(label[:,1])
    
    xmin-= 200
    xmax+=170
    ymax+=90
    ymin-=120
    width = xmax-xmin
    height = ymax-ymin
    
    w_b, h_b = annotation['bbox'][2:]
    
    x_scale = (width)/w_b
    y_scale = (height)/h_b
    
    image = Image.open('/home/nasha/workspace/Colab Notebooks/images/{0:06d}.png'.format(f))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    
    implot = plt.imshow(image,origin='lower')
    
    x_shift = (annotation['bbox'][0])-xmin/x_scale
    y_shift = (horse_mask.shape[0]-annotation['bbox'][1]) - ymax/y_scale
    
    # save the rescaled kepoints
    
    label_xy = np.stack(((((label[:,0])/x_scale)+x_shift).astype(int),(((label[:,1])/y_scale)+y_shift).astype(int)), axis =1)
    label_resc = np.concatenate((label_xy,np.expand_dims(label[:,2],axis=1)),axis=1)
    label_list = [item for sublist in label_resc.tolist() for item in sublist]
    
     	
    # Add keypoint to the annotations
#    annotations[f].update( {'keypoints' : label_list} )

# Add the image info in a similar manner to how I am doing the annotations
# put a red dot, size 40, at 2 locations:
    plt.scatter(x=((label[:,0])/x_scale)+x_shift, y=((label[:,1])/y_scale)+y_shift, c='r', s=10)
    plt.title('{}'.format(f))
    plt.show()
    
print(json.dumps(annotations))


everything = {"info":info,"images":images,"annotations":annotations,"categories":categories}
print(json.dumps(everything))

#put them in the required format

with open('annotations.txt','w') as outfile:
    json.dump(everything,outfile)

#create the "images" as I read multiple files ,“info”, “licenses”, “images”, “annotations”, “categories”

#do this for my complete dataset and save everything



"""### Model Description

Deeplabv3-ResNet101 is contructed by a Deeplabv3 model with a ResNet-101 backbone.
The pre-trained model has been trained on a subset of COCO train2017, on the 20 categories that are present in the Pascal VOC dataset.

Their accuracies of the pre-trained models evaluated on COCO val2017 dataset are listed below.

|    Model structure  |   Mean IOU  | Global Pixelwise Accuracy |
| ------------------- | ----------- | --------------------------|
| deeplabv3_resnet101 |   67.4      |   92.4                    |

### Resources

 - [Rethinking Atrous Convolution for Semantic Image Segmentation](https://arxiv.org/abs/1706.05587)
"""