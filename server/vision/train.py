import os
import glob
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn import svm, calibration
import pickle
import multiprocessing


VISION_PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(VISION_PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
DATASET_PATH = os.path.join(BASE_PATH, 'dataset')
MODELS_PATH = os.path.join(BASE_PATH, 'models')

SRC_DATA = os.path.join(VISION_PATH, 'annotaion.json')
DST_DATA = os.path.join(MODELS_PATH, 'annotaion.json')
MAX_ITER = 100


def train_generic(node, component, write_lock):
    if component == 'dosing':
        train_dosing(int(node))
    elif component == 'holder':
        train_holder(int(node))

    update_data(node, component, write_lock)


def train_dosing(node, CPR=100.0, max_iter=MAX_ITER):
    component = 'dosing'
    files = glob.glob(DATASET_PATH + '/%s_%03d_*/data.npz' % (component, node))
    print(files)
    y = []
    X = []
    for file in files:
        file = np.load(file)
        print(len(file['indices']))
        y.append(file['indices'])
        X.append(file['images'])
    y = np.concatenate(y)
    X = np.concatenate(X)
    print(y.shape)
    print(X.shape)

    y = y * CPR
    y = np.mod(y.round().astype(int) + int(CPR / 2), CPR) - int(CPR / 2)

    start_back = (115.0 / 400 * CPR + CPR / 2) % CPR - CPR / 2
    end_back = (285.0 / 400 * CPR + CPR / 2) % CPR - CPR / 2

    selected = ((end_back - 5) < y) * (y < (start_back + 5))
    X = X[selected].copy()
    y = y[selected].copy()

    y[y > start_back] = int(CPR / 2) - 1
    y[y < end_back] = int(CPR / 2) - 1

    # plt.plot(y)
    # plt.show()

    train(CPR, X, y, max_iter, '%s_%03d' % (component, node))


def train_holder(node, CPR=100.0, max_iter=MAX_ITER):
    component = 'holder'
    files = glob.glob(DATASET_PATH + '/%s_%03d_*/data.npz' % (component, node))
    y = []
    X = []
    for file in files:
        file = np.load(file)
        y.append(file['indices'])
        X.append(file['images'])
    y = np.concatenate(y)
    X = np.concatenate(X)
    print(y.shape)
    print(X.shape)

    y = y * CPR
    y = np.mod(y.round().astype(int) + int(CPR / 2), CPR) - int(CPR / 2)
    train(CPR, X, y, max_iter, '%s_%03d' % (component, node))


def train(C, X, y, max_iter, name):
    test_portion = 0.1
    istest = np.random.random_sample(y.shape) < test_portion

    X_train = X[~istest, :].copy()
    X_test = X[istest, :].copy()
    y_train = y[~istest].copy()
    y_test = y[istest].copy()

    IX = np.argsort(y_test)
    X_test = X_test[IX, :]
    y_test = y_test[IX]

    clf = svm.LinearSVC(C=1, max_iter=max_iter, verbose=True)
    clf = calibration.CalibratedClassifierCV(clf)
    clf = clf.fit(X_train, y_train)

    with open(MODELS_PATH + '/%s.clf' % name, 'wb') as f:
        pickle.dump(clf, f)

    full_range = C / 2
    predict = clf.predict(X_test)
    print('STD:', np.std(np.minimum(np.abs(predict - y_test),
                                    np.abs(full_range - np.abs(predict - y_test)))))

    test = abs(y_test) < 20
    print('STD under 40:', np.std(np.minimum(np.abs(
        predict[test] - y_test[test]), np.abs(full_range - np.abs(predict[test] - y_test[test])))))

    plt.clf()
    plt.figure(figsize=(20, 12))
    plt.scatter(y_test, predict, alpha=0.1, s=10)
    plt.savefig(MODELS_PATH + '/predict_%s.png' % name, dpi=150)
    # plt.show()


def load_data(filename):
    with open(filename) as f:
        data = json.loads(f.read())
    return data


def compare_dict(a, b):
    a_str = json.dumps(a, sort_keys=True)
    b_str = json.dumps(b, sort_keys=True)
    return a_str == b_str


def update_data(node, component, write_lock):
    write_lock.acquire()
    try:
        src_data = load_data(SRC_DATA)
        dst_data = load_data(DST_DATA)
        dst_data[node][component] = src_data[node][component]
        dst_data[node][component + '_roi'] = src_data[node][component + '_roi']
        dst_data_json = json.dumps(dst_data, sort_keys=True, indent=4)
        with open(DST_DATA, 'w') as f:
            f.write(dst_data_json)
    finally:
        write_lock.release()


def main():
    src_data = load_data(SRC_DATA)
    dst_data = load_data(DST_DATA)

    nodes = list(src_data.keys())
    nodes.sort()
    componenets = ['holder', 'dosing']
    res = []
    with multiprocessing.get_context('spawn').Pool(5) as pool:
        process_manager = multiprocessing.Manager()
        write_lock = process_manager.Lock()

        for node in nodes:
            for component in componenets:
                c1 = compare_dict(src_data[node][component],
                                  dst_data[node][component])
                c2 = compare_dict(
                    src_data[node][component + '_roi'], dst_data[node][component + '_roi'])
                if c1 and c2:
                    print(node, component, 'mode is up to-date')
                    continue
                print(node, component, 'training model')
                res.append(pool.apply_async(
                    train_generic, (node, component, write_lock)))
        for r in res:
            r.get()


if __name__ == '__main__':
    main()
