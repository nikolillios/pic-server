import images.models as image_models
import numpy as np
from PIL import Image

def getImagesByUserID(user_id):
    images = image_models.ImageModel.objects.filter(
        owner=user_id)
    print(images)
    return [image._id for image in images]

def saveImageModel(user_id, image_url):
    image = image_models.ImageModel(
        owner = user_id,
        url = image_url,
    )
    image.save()
    print(image_models.ImageModel.objects.all())

def userImagesDirPath(instance, filename):
    return 'user_{0}/{1}'.format(instance.owner.id, filename)

# def getImageById(image_id):
#     # TODO: download from cloud and return]
#     img = Image.open('../test_images/MD_fam.jpeg')
#     print(img)
#     return img

def findClosestE6PaletteColor(pixel):
    colors = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 0], [1, 0, 0], [0, 0, 1], [0, 0, 1]])
    minDist = float('inf')
    closestColor = (-1, -1, -1)
    for color in colors:
        dist = sum([(color[i]-pixel[i])**2 for i in range(3)])
        if dist < minDist:
            minDist = dist
            closestColor = color
    return closestColor

def ditherFloydSteinberg(image):
    shape = image.shape
    image = np.divide(image, 255)
    for i in range(shape[0]):
        for j in range(shape[1]):
            # newPixel = colors[np.argmin(
            #     [(colors[i]-image[i, j, :])**2
            #     for i in range(len(colors))]
            # )]
            newPixel = findClosestE6PaletteColor(image[i, j, :])
            quantErr = image[i, j, :] - newPixel
            image[i, j] = newPixel
            if j < shape[1] - 1:
                image[i, j+1] = image[i, j+1] + quantErr*7/16
                if i < shape[0] - 1:
                    image[i+1, j+1] = image[i+1, j+1] + quantErr * 1/16
            if i < shape[0] - 1:
                image[i+1, j] = image[i+1, j] + quantErr * 5/16
                if j > 0:
                    image[i+1, j-1] = image[i+1, j-1] + quantErr * 3/16
    return image

def ditherAtkinson(image):
    shape = image.shape
    image = np.divide(image, 255)
    for i in range(shape[0]):
        for j in range(shape[1]):
            newPixel = findClosestE6PaletteColor(image[i, j, :])
            quantErr = image[i, j, :] - newPixel
            image[i, j] = newPixel
            if j < shape[1] - 1:
                image[i, j+1] = image[i, j+1] + quantErr * 1/8
                if i < shape[0] - 1:
                    image[i+1, j+1] = image[i+1, j+1] + quantErr * 1/8
                if j < shape[0] - 2:
                    image[i, j+2] = image[i, j+2] + quantErr * 1/8
            if i < shape[0] - 1:
                image[i+1, j] = image[i+1, j] + quantErr * 1/8
                if j > 0:
                    image[i+1, j-1] = image[i+1, j-1] + quantErr * 1/8
                if i < shape[0] - 2:
                    image[i+2, j] = image[i+2, j] + quantErr * 1/8
    return image


def testDitherFloydSteinberg():
    image = Image.open("test_images/MD_fam.jpeg").resize((800, 480))
    image.show()
    imArr = np.array(image)
    # print(imArr.shape)
    # print(imArr)
    dithered = ditherFloydSteinberg(imArr)
    print(dithered.shape)
    ditheredImage = Image.fromarray(np.array(dithered*255, dtype=np.uint8))
    ditheredImage.show()
    atkinsDithered = ditherAtkinson(np.array(image))
    atkinsIm = Image.fromarray(np.array(atkinsDithered*255, dtype=np.uint8))
    atkinsIm.show()
    ditheredImage.save('/Users/nikolillios/picturesque/repos/server/test_images/floydSteinbergRheeFam.bmp')
    atkinsIm.save('/Users/nikolillios/picturesque/repos/server/test_images/atkinsonRheeFam.bmp')
