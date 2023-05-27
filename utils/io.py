import cv2
import numpy as np
from typing import List, Tuple
import matplotlib.pyplot as plt



def show_images(
    imgs: List[np.array], titles: List[str], figsize: Tuple[int]=(15, 10)
) -> None:
    """
    Show images with tites
    :param imgs: List of images
    :param titles: List of titles
    :param figsize: Figure size 
    """
    idx = 1
    fig = plt.figure(figsize=figsize)

    for img, title in zip(imgs, titles):
        ax = fig.add_subplot(1, len(imgs), idx)
        ax.imshow(img)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel(title)
        idx += 1
    plt.show()


def read_image(image_path: str) -> np.ndarray:
    '''
    Reads image from image path, and return floating point RGB image
    :param image_path: path to image
    '''
    bgr_image = cv2.imread(image_path)
    rgb_image = bgr_image[:, :, [2, 1, 0]]
    
    return rgb_image.astype(np.float32) / 255
