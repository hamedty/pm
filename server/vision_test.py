import vision
import glob
import pickle
import cv2

clf_dosing = pickle.load(open('model_dosing.clf', 'rb'))
ls = glob.glob('data/dosing*.png')
ls.sort()
for filename in ls:
    image = cv2.imread(filename)
    print(vision.detect(clf_dosing, image))
