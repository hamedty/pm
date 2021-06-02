import glob
import cv2
import numpy as np
import json


def load_data():
    with open('annotaion.json') as f:
        data = json.loads(f.read())
    return data


data = load_data()

nodes = list(data.keys())
nodes.sort()
componenets = ['holder']  # ,['holder', 'dosing']

for node in nodes[1:]:
    for component in componenets:
        roi = data[node][component + '_roi']
        x0 = roi['x0']
        x1 = roi['x0'] + roi['dx']
        y0 = roi['y0']
        y1 = roi['y0'] + roi['dy']

        for dataset_name in data[node][component]:
            IMAGES = []
            INDICES = []

            dataset_dict = data[node][component][dataset_name]
            path = '../../dataset/%s_%s_%s_192.168.44.%s' % (
                component, node, dataset_name, node)
            files = glob.glob(path + '/*.png')
            files.sort()
            fpr = int(files[-1].split('/')[-1].split('_')[0]) + 1
            zero = dataset_dict['zero']
            print(path, fpr)

            for filename in files:
                image = cv2.imread(filename)[y0:y1, x0:x1, :]
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                IMAGES.append(image.flatten())

                index = int(filename.split('/')[-1].split('_')[0]) - zero
                index = float(index % fpr) / fpr
                INDICES.append(index)

            IMAGES = np.array(IMAGES)
            INDICES = np.array(INDICES)
            np.savez_compressed(path + '/data.npz',
                                images=IMAGES, indices=INDICES)
