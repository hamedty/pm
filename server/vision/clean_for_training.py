import glob
import cv2
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import pickle

VISION_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(VISION_PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
DATASET_PATH = os.path.join(BASE_PATH, 'dataset')
MODELS_PATH = os.path.join(BASE_PATH, 'models')

SRC_DATA = os.path.join(VISION_PATH, 'annotaion.json')
DST_DATA = os.path.join(MODELS_PATH, 'annotaion.json')

DOSING_Y_MARGIN = 30


def load_data():
    with open(SRC_DATA) as f:
        data = json.loads(f.read())
    return data


data = load_data()

nodes = list(data.keys())
nodes.sort()
componenets = ['holder', 'dosing']


def npz_valid(npz_filename, roi_in, zero_in):
    if not os.path.isfile(npz_filename):
        return False
    npz = np.load(npz_filename, allow_pickle=True)
    return (npz.get('roi') == roi_in) and (npz.get('zero') == zero_in)


def passive_roi(frame, roi, component):
    x0 = roi['x0']
    dx = roi['dx']
    y0 = roi['y0']
    dy = roi['dy']

    if component == 'dosing':
        x_downsample = 8
        y_downsample = 1

        # active ROI
        y0 -= DOSING_Y_MARGIN
        dy += 2 * DOSING_Y_MARGIN

    elif component == 'holder':
        x_downsample = 1
        y_downsample = 8

    x_size = round(dx / x_downsample)
    y_size = round(dy / y_downsample)
    frame = frame[y0:y0 + dy, x0:x0 + dx, :]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (x_size, y_size), interpolation=cv2.INTER_AREA)

    return frame


def active_roi(frame, back_cross_section):
    cross_section = frame.mean(axis=1)
    argmax = np.argmax(np.convolve(
        back_cross_section[0], cross_section, mode='same'))
    offset = argmax - back_cross_section[1]
    assert abs(offset) < DOSING_Y_MARGIN
    # print(offset)
    return offset


def prepare_cross_section(datasets, roi, node):
    dataset_name = list(datasets.keys())[0]
    dataset_dict = datasets[dataset_name]
    zero = dataset_dict['zero']
    back = (zero + (400 / 2)) % 400
    filename = DATASET_PATH + f'/dosing_{node}_{dataset_name}_192.168.44.{node}/{int(back):03d}_00.png'
    image = cv2.imread(filename)
    frame = passive_roi(image, roi, 'dosing')
    cross_section = frame.mean(axis=1)
    default_argmax = np.argmax(np.convolve(
        cross_section, cross_section, mode='same'))
    data = (cross_section, default_argmax)

    with open(MODELS_PATH + f'/cross_section_{node}.pickle', 'wb') as f:
        pickle.dump(data, f)

    return (cross_section, default_argmax)


def prepare_frame(frame, roi, component, back_cross_section):
    frame = passive_roi(frame, roi, component)

    if component == 'dosing':
        offset = active_roi(frame, back_cross_section)
        frame = frame[DOSING_Y_MARGIN + offset:offset - DOSING_Y_MARGIN, :]

        # plt.imshow(frame)
        # plt.show()
        # raise
    # if component == 'dosing':
    #     mid_point = int(frame.shape[0] / 2)
    #     a = frame[0:mid_point - 55, :].flatten()
    #     b = frame[mid_point + 55:, :].flatten()
    #     frame = np.concatenate([a, b])
    # else:
    frame = frame.flatten()
    return frame


def main():
    for node in nodes:
        for component in componenets:
            datasets = data[node][component]
            roi = data[node][component + '_roi']

            back_cross_section = None
            if component == 'dosing':
                back_cross_section = prepare_cross_section(datasets, roi, node)

            for dataset_name in datasets:
                IMAGES = []
                INDICES = []

                dataset_dict = datasets[dataset_name]
                path = DATASET_PATH + '/%s_%s_%s_192.168.44.%s' % (
                    component, node, dataset_name, node)
                npz_filename = path + '/data.npz'
                files = glob.glob(path + '/*.png')
                files.sort()
                fpr = int(files[-1].split('/')[-1].split('_')[0]) + 1
                zero = dataset_dict['zero']
                print(path, fpr)

                if npz_valid(npz_filename, roi, zero):
                    print('npz is valid')
                    continue

                for filename in files:
                    image = cv2.imread(filename)
                    image = prepare_frame(
                        image, roi, component, back_cross_section)
                    IMAGES.append(image)

                    index = int(filename.split('/')[-1].split('_')[0]) - zero
                    index = float(index % fpr) / fpr
                    INDICES.append(index)

                IMAGES = np.array(IMAGES)
                INDICES = np.array(INDICES)
                np.savez_compressed(path + '/data.npz',
                                    images=IMAGES, indices=INDICES, roi=roi, zero=zero)


if __name__ == '__main__':
    main()
