import os
import glob
import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn import svm, calibration
import pickle

PATH = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(os.path.dirname(PATH), 'data')


def train_dosing():
    name = 'dosing'
    FPR = 400.0
    CPR = 100.0
    X = np.load('/home/it/Desktop/data_dosing/frames_%s.npy' % name)
    y = np.arange(X.shape[0]) / (FPR / CPR)
    y = np.mod(y.round().astype(int) + int(CPR / 2), CPR) - int(CPR / 2)

    start_back = (135.0 / 400 * CPR + CPR / 2) % CPR - CPR / 2
    end_back = (295.0 / 400 * CPR + CPR / 2) % CPR - CPR / 2

    selected = ((end_back - 5) < y) * (y < (start_back + 5))
    X = X[selected].copy()
    y = y[selected].copy()

    y[y > start_back] = 40
    y[y < end_back] = 40

    plt.plot(y)
    plt.show()
    # raise
    train(CPR, X, y, name)


def train_holder():
    name = 'holder'
    FPR = 400.0
    CPR = 100.0
    files = glob.glob(DATA_PATH + '/frames_%s_*.npy' % name)
    X = [np.load(file) for file in files]
    for x in X:
        print(x.shape)
        assert len(x.shape[0]) == len(X[0].shape[0])
        assert len(x.shape[0]) % FPR == 0
    X = np.concatenate(X)
    print(X.shape)

    y = np.arange(X.shape[0]) / (FPR / CPR) - 0.5
    y = np.mod(y.round().astype(int) + int(CPR / 2), CPR) - int(CPR / 2)
    train(CPR, X, y, name)


def train(C, X, y, name):
    test_portion = 0.1
    istest = np.random.random_sample(y.shape) < test_portion

    X_train = X[~istest, :].copy()
    X_test = X[istest, :].copy()
    y_train = y[~istest].copy()
    y_test = y[istest].copy()

    IX = np.argsort(y_test)
    X_test = X_test[IX, :]
    y_test = y_test[IX]

    clf = svm.LinearSVC(C=1, max_iter=20, verbose=True)
    clf = calibration.CalibratedClassifierCV(clf)
    clf = clf.fit(X_train, y_train)

    with open('model_%s.clf' % name, 'wb') as f:
        pickle.dump(clf, f)

    # full_range = C / 2
    predict = clf.predict(X)
    # print('STD:', np.std(np.minimum(np.abs(predict - y_test),
    #                                 np.abs(full_range - np.abs(predict - y_test)))))
    #
    # test = abs(y_test) < 20
    # print('STD under 40:', np.std(np.minimum(np.abs(
    #     predict[test] - y_test[test]), np.abs(full_range - np.abs(predict[test] - y_test[test])))))

    plt.clf()
    plt.figure(figsize=(20, 12))
    plt.scatter(y, predict, alpha=0.1, s=10)
    plt.savefig('predict_%s.png' % name, dpi=150)
    # plt.show()


train_holder()
# train_dosing()
