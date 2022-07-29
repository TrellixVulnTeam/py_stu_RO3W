'''

'''
import os
import numpy as np
import torch
from PIL import Image
import matplotlib.pyplot as plt

from torchvision import models
from torchvision.models.mobilenet import mobilenet_v2

from torchvision import transforms
from utils import GradCAM, show_cam_on_image, center_crop_img


def main():
    # models = models.mobilenet_v2(pretrained=True)
    model = mobilenet_v2(pretrained=True)
    target_layers = [model.features[-1]]
    data_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    # load image
    img_path="./both.png"
    assert os.path.exists(img_path),"file:'{}' does not exist.".format(img_path)
    img=Image.open(img_path).convert('RGB')
    img=np.array(img,dtype=np.uint8)
    img_tensor=data_transform(img)
    input_tensor=torch.unsqueeze(img_tensor,dim=0)
    cam=GradCAM(model=model,target_layers=target_layers,use_cuda=False)
    target_category=281
    grayscale_cam=cam(input_tensor,target_category=target_category)
    grayscale_cam=grayscale_cam[0,:]
    visualization=show_cam_on_image(img.astype(dtype=np.float32)/255.,
                                    grayscale_cam,
                                    use_rgb=True)
    plt.imshow(visualization)
    plt.show()







if __name__ == '__main__':
    main()
