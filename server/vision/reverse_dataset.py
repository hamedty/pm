import glob
import os

path = '/home/it/Desktop/PAM2060/dataset/holder_102_dag1aqju_192.168.44.102'

files = glob.glob(path + '/*.png')
for f in files:
    os.rename(f, f + 'o')

files = glob.glob(path + '/*.pngo')
for f in files:
    i, j = f.split('/')[-1].split('.')[0].split('_')
    i = '%03d' % (399 - int(i))
    new_f = path + '/%s_%s.png' % (i, j)
    os.rename(f, new_f)
