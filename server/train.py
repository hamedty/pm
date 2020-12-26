import numpy as np
import cv2
import matplotlib.pyplot as plt
from sklearn import svm, calibration
import pickle

C = 100

X = np.load('holder.npy')
y = np.arange(X.shape[0]) / (400.0 / C)
y = np.mod(y.round().astype(int) + int(C / 2), C) - int(C / 2)

print(X.shape)
print(y.shape)


test_portion = 0.25
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

with open('model.clf', 'wb') as f:
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
# plt.savefig(filename + '.png', dpi = 150)
plt.show()
