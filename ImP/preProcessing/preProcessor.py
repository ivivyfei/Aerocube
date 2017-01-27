import cv2 
import numpy as np
from skimage import data
from skimage import exposure 
from PIL import Image, ImageFilter

class PreProcessor:

	threshold_value = 2.2

	def __init__(self, pathToNewImage):
		self.image = cv2.imread(pathToNewImage) #for OpenCV
		self.scikitImage = data.imread(pathToNewImage) # for scikit 
		self.pilImage = Image.open(pathToNewImage) # for PIL 
		#only using this var underneath to play with new images at the moment
		

	def is_similar(self, pathToOtherImage):
		existingImage = cv2.imread(pathToOtherImage)
		difference = cv2.subtract(self.image, existingImage)
		return np.mean(difference) <= self.threshold_value
		

	def calculate_average_exposure(self):
		pass

	def increase_contrast(self):
		pass


	def darken_image(self):
		"""
		Aruco knows no bounds when it comes to dark images. At the moment we do not have a
		set value for how dark we can make an image. It works under x =0.2, but that may
		not be the case under our algorithm (pycuda version).
		
		TODO: Find threshold value for both pycuda and regular algorithm
			  Also, modify so we can set darkness levels via arg		
		"""
		#image = Image.open(self.path)
		#image.point(lambda x: x*0.4).save('darkest.jpg')
		self.pilImage.point(lambda x: x*0.4).save('darkest.jpg')
		self.pilImage.close()

	def brighten_image(self):
		"""
		Works the same way as darken_image() but x>1.0 to brighten the image as ooposed to 
		being x<1.0 to darken it.

		TODO: Develop way to find out how much we need to brighten the image
			  Feed in x value via arg

		"""
		
		self.pilImage.point(lambda x: x*3.0).save('brighter.jpg')
		self.pilImage.close()


	def is_low_contrast(self):
		"""
		By default the threshold value is set to 0.05, however under darker_image set to 
		0.4 we achieve a low contrast==True under the threshold of 0.24
		"""
		return exposure.is_low_contrast(self.scikitImage, fraction_threshold=0.24)
		
	def sharper_image(self):
		pass


