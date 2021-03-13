import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn import svm, calibration
import pickle


def train_dosing():
    name = 'dosing'
    C = 100
    X = np.load('frames_%s.npy' % name)
    y = np.arange(X.shape[0]) / (400.0 / C)
    y = np.mod(y.round().astype(int) + int(C / 2), C) - int(C / 2)

    start_back = (85.0 / 400 * C + C / 2) % C - C / 2
    end_back = (295.0 / 400 * C + C / 2) % C - C / 2

    selected = ((end_back - 5) < y) * (y < (start_back + 5))
    X = X[selected].copy()
    y = y[selected].copy()

    y[y > start_back] = 25
    y[y < end_back] = 25

    plt.plot(y)
    plt.show()
    raise
    train(C, X, y, name)


def train_holder():
    name = 'holder'
    C = 100
    X = np.load('frames_%s.npy' % name)
    y = np.arange(X.shape[0]) / (400.0 / C) - 0.5
    y = np.mod(y.round().astype(int) + int(C / 2), C) - int(C / 2)
    train(C, X, y, name)


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

    clf = svm.LinearSVC(C=1, max_iter=10, verbose=True)
    clf = calibration.CalibratedClassifierCV(clf)
    clf = clf.fit(X_train, y_train)

    with open('model_%s.clf' % name, 'wb') as f:
        pickle.dump(clf, f)

    full_range = C / 2
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


# train_holder()
train_dosing()
