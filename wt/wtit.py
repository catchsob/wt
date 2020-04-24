class Wtit:
	
	MODEL_DICT = {'classify_14tree':0, 'classify_8leaf':1, 'objdetect_14tree':2, 'objdetect_8leaf':3}
	MODEL = ['MobileNetV2_tree_acc797.h5', 'InceptionV3_leaf_acc94.h5.h5', '1120_tree.h5', '1124_leaf-2.h5']
	MODEL_DES = ['MobileNetV2', 'InceptionV3', 'YoloV3', 'YoloV3']
	MODEL_ANCHORS = [[], [],
					 [73,171, 98,314, 132,200, 149,357, 199,241, 216,364, 289,389, 331,283, 387,397],
					 [25,33, 52,94, 56,71, 67,83, 68,98, 73,65, 81,96, 116,134, 147,182]]
	MODEL_COLOR = [4, 4, 3, 3] # 1: mono, 3: BGR, 4: RGB
	PREPROCESS = ['common', 'common', 'none', 'none']
	MODEL_PUB = [0.80, 0.94, 0.50, 0.55]
	MODEL_PRI = [0.80, 0.94, 0.50, 0.55]
	MODEL_PATH = './model'

	#MODEL_HDF5 = './model_resnet50_100ep-Copy1.h5'
	CAT = [['黑板樹', '茄冬', '樟樹', '鳳凰木', '榕樹', '台灣欒樹', '楓香', '苦楝', '白千層', '水黃皮','阿勃勒','大王椰子','大葉欖仁', '小葉欖仁'],
		   ['青楓', '鳳凰木', '水同木', '稜果榕', '楓香', '大葉山欖', '盾柱木', '大葉欖仁'],
		   ["AS","BJ","CC","DR","FM","KE","LF","MA","MI","MP","PC","RR","TC","TM"],
		   #['黑板樹', '茄冬', '樟樹', '鳳凰木', '榕樹', '台灣欒樹', '楓香', '苦楝', '白千層', '水黃皮','阿勃勒','大王椰子','大葉欖仁', '小葉欖仁'],
		   #['青楓', '鳳凰木', '水同木', '稜果榕', '楓香', '大葉山欖', '盾柱木', '大葉欖仁'],
		   ["AE","DR","FF","FP","LF","PF","PP","TC"]]
	RES = [400, 299, 416, 416]

	model = [None, None, None, None]
	graph = [None, None, None, None]

	def __init__(self):
		import tensorflow as tf
		from keras.models import load_model
		
		for i, v in enumerate(self.MODEL):
			self.model[i] = load_model(self.MODEL_PATH + '/' + v)
			self.graph[i] = tf.get_default_graph()
	
	def _yolo3expe_load_model(self, model_fn):
		import json
		import cv2
		from keras.models import load_model
		import numpy as np
		from yolov3_expe.utils.utils import get_yolo_boxes, makedirs
		from yolov3_expe.utils.bbox import draw_boxes
		import tensorflow as tf

		infer_model = load_model(model_fn)
		
		return infer_model
	
	def judgeYolo(self, fnimg, fid, model_kw='objdetect_14tree'):
		import json
		import cv2
		import numpy as np
		from yolov3_expe.utils.utils import get_yolo_boxes
		from yolov3_expe.utils.bbox import draw_boxes
		
		m = self.MODEL_DICT[model_kw]
		
		obj_thresh, nms_thresh = 0.5, 0.45
		
		img = self._prepareImg(fnimg, self.MODEL_COLOR[m], self.RES[m], mode=self.PREPROCESS[m])
		# predict the bounding boxes
		boxes = get_yolo_boxes(self.model[m], [img], self.RES[m], self.RES[m], self.MODEL_ANCHORS[m], obj_thresh, nms_thresh, self.graph[m])[0]
		# draw bounding boxes on the image using labels
		draw_boxes(img, boxes, self.CAT[m], obj_thresh) 
		# write the image with bounding boxes to file
		cv2.imwrite(fid, np.uint8(img))
	
	# input f may be filename of str or bytearray
	def _prepareImg(self, f, color=3, res=224, mode='common'):
		import cv2
		import numpy as np
		
		img = None
		
		if mode == 'none': # for yolo
			img = cv2.imread(f, 1) if type(f) is str else cv2.imdecode(f, 1)
			return img
			
		if color in [3, 4]:
			img = cv2.imread(f, 1) if type(f) is str else cv2.imdecode(f, 1)
			if color == 4:
				img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
			img = cv2.resize(img, (res, res))
			img = np.reshape(img, (-1, res, res, 3))
		else:
			img = cv2.imread(f, 0) if type(f) is str else cv2.imdecode(f, 0)
			img = cv2.resize(img, (res, res))
			img = np.reshape(img, (-1, res, res, 1))
		
		img = img.astype('float32')
		if mode == 'common':
			img /= 255.
		elif mode == 'tf':
			img /= 127.5
			img -= 1.
				
		return img
		
	# input may be filename of str or bytearray
	def judge(self, fnimg, model_kw='classify_14tree'):
		import numpy as np
		
		m = self.MODEL_DICT[model_kw]
		
		img = self._prepareImg(fnimg, self.MODEL_COLOR[m], self.RES[m], mode=self.PREPROCESS[m])
		pred = None
		with self.graph[m].as_default():
			pred = np.argmax(self.model[m].predict(img))
		return pred, self.CAT[m][pred], self.MODEL_DES[m]

if __name__ == "__main__":
	import sys

	if (len(sys.argv) == 2):
		from time import time
		start = time()
		filename = sys.argv[1]
		judge = Wtit()
		for i in range(1, 5):
			cat, cat_str, mod_str = judge.judge(filename, i)
			print(cat, cat_str, mod_str)
		print(time() - start, 'secs')
	else:
		print('usage: python ' + sys.argv[0] + ' image_filename')
