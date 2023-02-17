import ctypes
import time
import os
import json
#### to run adjust rtprio in
## > sudo nano /etc/security/limits.conf
# then
# su pi
# ulimit -Sr 1
#then it will work

CAPS = 69
SHIFT = 6

_lib = ctypes.CDLL("./libtypewriter.so", mode=1)

_lock = False
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
_lib.write.argtypes = (ctypes.c_int,ctypes.c_int)
_lib.write.restype = ctypes.c_int
def _write(key, repeat_n):
    global _lib
    return int(_lib.write( ctypes.c_int(key),ctypes.c_int(repeat_n)))

_lib.read.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.c_int)
_lib.read.restype = ctypes.POINTER(ctypes.c_int*(8*9))
def _read(timeout_ms):
    global _lib
    res_type = ctypes.c_int*(8*9)
    res_mem = res_type(*[0 for _ in range(8*9)])
    result = _lib.read(res_mem, ctypes.c_int(timeout_ms))
    return [i for i in result.contents]


with open("mapping.json") as f:
    mapping = json.load(f)

mapping_inv = {v: k for k, v in mapping.items()}

class Typewriter(object):
    def __init__(self, n_repeat = 10, char_wait = 0.05, cr_wait_p_char = 0.3, read_blocks = 20 ):
        self.n_repeat = n_repeat
        self.char_wait = char_wait
        self.cr_wait_p_char = cr_wait_p_char
        self.shift_state = False
        self.c_advance = 0
        self.read_blocks = read_blocks
        self.commanding_queue = []
        if _lock:
            raise ValueError("can not have two instances")
        pass
    def __enter__(self):
        init_re = _init()
        if init_re == 0:
            raise ValueError("Failed to init the bcm interface")
        elif init_re == -1:
            raise ValueError("Did not have permision to change priority settings")
        global _lock
        _lock = True
        return self
    def __exit__(self, *errors):
        _cleanup()
        global _lock
        _lock = False
    def gen_command(self, char, default= "?"):
        if char == "\n":
            wait = self.c_advance*self.cr_wait_p_char
        else:
            wait = self.char_wait
        wait_func = [lambda wait=wait: time.sleep(wait)]
        if char in mapping:
            if type(mapping[char]) == int:
                keys = [lambda self= self, char = char: _write(mapping[char], self.n_repeat),]   
                shift = False
            else:
                keys = [lambda self= self, char = char: _write(mapping[mapping[char]], self.n_repeat),]    
                shift = True  
        elif char.lower() in mapping:
            keys = [lambda self= self, char = char: _write(mapping[char.lower()], self.n_repeat),]
            shift = True
        else:
            self.gen_command(default)
            return
        if shift and not self.shift_state:
            keys = [lambda self = self: _write(CAPS, self.n_repeat)] + wait_func + keys
            self.shift_state = True
        elif not shift and self.shift_state:
            keys = [lambda self = self: _write(SHIFT, self.n_repeat)] + wait_func + keys
            self.shift_state = False
        
        keys =  keys + wait_func

        self.commanding_queue.extend(keys)
    def type_queue_blocking(self):
        for command in self.commanding_queue:
            command()
        self.commanding_queue = []
    def gen_commands(self, string):
        for s in string:
            self.gen_command(s)
    
    def read_blocking(self, time_to_read):
        starting_time = time.time()
        prev_keys = set()
        string_queue = []
        while (time.time()- starting_time < time_to_read):
            res = _read(self.read_blocks)
            keys = set()
            for char_key, repepat in enumerate(res):
                if repepat > 0:
                    keys.add(char_key)
            if SHIFT in keys:
                shift = True
                keys.discard(SHIFT)
            else:
                shift = False
            if prev_keys == keys:
                continue #nothing changed
            prev_keys= keys
            if len(keys) != 1:
                #zero or many keys
                #dunno ignore
                continue
            #only one so get it
            key = int(next(iter(keys)))
            if not key in mapping_inv:
                #unknown key
                continue
            key_map = mapping_inv[key]
            if shift:
                if key_map in mapping_inv:
                    key_map = mapping_inv[key_map]
                else:
                    key_map = key_map.upper()
            
            string_queue.append(key_map)
            

        return "".join(string_queue)




if __name__ == "__main__":
    with Typewriter() as tw:
        tw.gen_commands("Hi\nI am!")
        tw.type_queue_blocking()
        # print(tw.read_blocking(10))