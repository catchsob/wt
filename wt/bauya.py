class Bauya:
	
	MODEL = ['model_resnet50_100ep-Copy1.h5',]
	MODEL_DES = ['ResNet50',]
	MODEL_COLOR = [3,] # 1: mono, 3: BGR, 4: RGB
	MODEL_PUB = [0.95,]
	MODEL_PRI = [0.86,]
	MODEL_PATH = './model' 

	#MODEL_HDF5 = './model_resnet50_100ep-Copy1.h5'
	CAT = [['羊蹄甲 bv', '洋紫荊 bp', '艷紫荊 bb']]
	RES = 224

	model = [None,]
	#graph = None
	graph = [None,]

	def __init__(self):
		import tensorflow as tf
		#from tensorflow.keras.models import load_model
		from keras.models import load_model
		#self.graph = tf.get_default_graph()
		#self.model = load_model(self.MODEL_HDF5)
		for i in range(len(self.MODEL)):
			self.model[i] = load_model(self.MODEL_PATH + '/' + self.MODEL[i])
			self.graph[i] = tf.get_default_graph()
	
	# input f may be filename of str or bytearray
	def _prepareImg(self, f, color=3):
		import cv2
		import numpy as np
		if color in [3, 4]:
			img = cv2.imread(f, 1) if type(f) is str else cv2.imdecode(f, 1)
			if color == 4:
				img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
			img = cv2.resize(img, (self.RES, self.RES))
			img = np.reshape(img, (-1, self.RES, self.RES, 3)) /255.
		else:
			img = cv2.imread(f, 0) if type(f) is str else cv2.imdecode(f, 0)
			img = cv2.resize(img, (self.RES, self.RES))
			img = np.reshape(img, (-1, self.RES, self.RES, 1)) /255.
		return img

	#def judge(self, filename):
	#	import numpy as np
	#	img = self._prepareImg(filename)
	#	pred = None
	#	with self.graph.as_default():
	#		pred = np.argmax(self.model.predict(img))
	#	return pred, self.CAT[pred]
		
	# input may be filename of str or bytearray
	def judge(self, fnimg, model_i=1):
		import numpy as np
		img = self._prepareImg(fnimg, self.MODEL_COLOR[model_i - 1])
		pred = None
		with self.graph[model_i - 1].as_default():
			pred = np.argmax(self.model[model_i - 1].predict(img))
		return pred, self.CAT[model_i - 1][pred], self.MODEL_DES[model_i - 1]

if __name__ == "__main__":
	import sys

	if (len(sys.argv) == 2):
		from time import time
		start = time()
		filename = sys.argv[1]
		judge = Bauya()
		for i in range(1, 5):
			cat, cat_str, mod_str = judge.judge(filename, i)
			print(cat, cat_str, mod_str)
		print(time() - start, 'secs')
	else:
		print('usage: python ' + sys.argv[0] + ' image_filename')
