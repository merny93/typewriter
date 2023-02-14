import ctypes
import time
import os
#### to run adjust rtprio in
## > sudo nano /etc/security/limits.conf
# then
# su pi
# ulimit -Sr 1
#then it will work

_lib = ctypes.CDLL("./libtypewriter.so", mode=1)


##start with init
_lib.init.argtypes = tuple()
_lib.init.restype = ctypes.c_int
def _init():
    global _lib
    return int(_lib.init())

## now cleanup
_lib.cleanup.argtypes = tuple()
_lib.cleanup.restype = ctypes.c_int
def _cleanup():
    global _lib
    return int(_lib.cleanup())

## now write
_lib.write.argtypes = (ctypes.c_int,ctypes.c_int,ctypes.c_int)
_lib.write.restype = ctypes.c_int
def _write(row_n,col_n, repeat_n):
    global _lib
    return int(_lib.write(ctypes.c_int(row_n), ctypes.c_int(col_n),ctypes.c_int(repeat_n)))

_lib.read.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.c_int)
_lib.read.restype = ctypes.POINTER(ctypes.c_int*(8*9))
def _read(timeout_ms):
    global _lib
    res_type = ctypes.c_int*(8*9)
    res_mem = res_type(*[0 for _ in range(8*9)])
    t = time.perf_counter()
    result = _lib.read(res_mem, ctypes.c_int(timeout_ms))
    tt = time.perf_counter()
    
    print(tt-t)
    return [i for i in result.contents]
print("init")
print(_init())
print("done init")
print(_write(3,3,1))
print("done write")
for _ in range(100):
    res = _read(100)
    try:
        
        ans = res.index(True)
        print(f"{int(ans/8)} row and {ans%8} col")
        print(res.index(True))
    except:
        pass
# print(_write(7,5,4))
# time.sleep(0.1)
# print(_write(3,3,4))
# time.sleep(0.1)
# print(_write(4,6,4))
# time.sleep(0.1)
# print(_write(3,2,4))
# time.sleep(0.1)
# print(_write(5,7,4))
# time.sleep(1)

print("done read")
print(_cleanup())
print("done cleanup")
# lib.our_function.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
# lib.our_function.restype = ctypes.POINTER(ctypes.c_int*2)
# def our_function(numbers):
#     global lib
#     num_numbers = len(numbers)
#     array_type = ctypes.c_int * num_numbers
#     res_type = ctypes.c_int * 2
#     result = lib.our_function(ctypes.c_int(num_numbers), array_type(*numbers), res_type(0,0))
#     return [i for i in result.contents]

# print(our_function([2,2,2]))