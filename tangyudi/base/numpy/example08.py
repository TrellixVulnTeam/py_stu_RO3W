import numpy as np
B=np.arange(3)
print(B)
print(np.exp(B))
print(np.sqrt(B))
print(np.random.random((3, 4)))
a=np.floor(10*np.random.random((3,4)))
print(a)
print(a.ravel())
print(a.shape)
print('2' * 100)
print(a.T)


a=np.floor(10*np.random.random((2,2)))
b=np.floor(10*np.random.random((2,2)))
print(a)
print('-'*100)
print(b)
print(np.vstack((a,b)))
print('3' * 100)
print(np.hstack((a, b)))
a=np.arange(24).reshape((2,12))
print(a)
print(np.hsplit(a, 3))
print(np.hsplit(a, (3, 4)))

a=np.random.random((12,2))
print('------------')
print(a)
np.vsplit(a,3)
