import ctypes
import time
import os
import threading
import json
import warnings
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
    def __init__(self, n_repeat = 8, char_wait = 0.04, cr_wait_p_char = 0.02, read_blocks = 20, double_wait = 0.2 ):
        self.n_repeat = n_repeat
        self.char_wait = char_wait
        self.cr_wait_p_char = cr_wait_p_char
        self.shift_state = False
        self.c_advance = 0
        self.read_blocks = read_blocks
        self.double_wait = double_wait
        self.commanding_queue = []
        if _lock:
            raise ValueError("can not have two instances")
        pass
    def __enter__(self):
        init_re = _init()
        if init_re == 0:
            raise ValueError("Failed to init the bcm interface")
        elif init_re == -1:
            raise ValueError("Did not have permision to change priority settings, run ulimit -Sr 1")
        global _lock
        _lock = True
        return self
    def __exit__(self, *errors):
        _cleanup()
        global _lock
        _lock = False
    def gen_command(self, char, default= "*", shift_char_call =False):
        def write_func(char):
            return lambda self = self, char=char: _write(char, self.n_repeat)

        if char == "\n":
            #if carriage return wait longer
            wait = self.c_advance*self.cr_wait_p_char
            self.c_advance = 0
        else:
            #regular wait
            self.c_advance += 1
            wait = self.char_wait

        wait_func = lambda wait=wait: time.sleep(wait)

        #check if char is in the mapping
        if char in mapping:
            #check if it's reccursive
            if type(mapping[char]) == int:
                #it is not
                self.commanding_queue.append(write_func(mapping[char]))
                shift = False
            else:
                #it is do the recursive thing
                self.gen_command(mapping[char], shift_char_call=True)
                shift = True  
        elif char.lower() in mapping:
            #is the lowercase version in it?
            #do recursive thing
            self.gen_command(char.lower(), shift_char_call=True)
            shift = True
        else:
            #unknown
            warning_string = f"Unknown charachter: {char}, replaced with default: {default}"
            warnings.warn(warning_string)
            self.gen_command(default)
            return
        
        #if its a space ignore shift state
        if char in [" ", "\n"]:
            shift = self.shift_state
        
        #only do the prepending shift if its a shift call
        if not shift_char_call:
            if shift and not self.shift_state:
                #need to press caps but backup 2 squares cause of the sleep
                self.commanding_queue.insert(-2, write_func(CAPS))
                self.commanding_queue.insert(-2, wait_func)
                self.shift_state = True
            elif not shift and self.shift_state:
                #this is a lowercase char so there was no second call so no sleep got appended
                #backup only 1 square
                self.commanding_queue.insert(-1, write_func(SHIFT))
                self.commanding_queue.insert(-1, wait_func)
                self.shift_state = False
        #add the sleep
        self.commanding_queue.append(wait_func)

    def type_queue_blocking(self):
        for command in self.commanding_queue:
            command()
        self.commanding_queue = []
    def gen_commands(self, string):
        """
        Generate commands for string into the commanding queue. Will press shift at the start just in case
        """
        prev = " "
        self.shift_state = False
        self.commanding_queue.append(lambda self=self: _write(SHIFT, self.n_repeat))
        self.commanding_queue.append(lambda self = self: time.sleep(self.char_wait))
        for s in string:
            if s == prev:
                self.commanding_queue.append(lambda self=self: time.sleep(self.double_wait))
            prev = s  
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
            if len(keys) == 0:
                #Nothing pressed
                continue
            elif len(keys) >1:
                warning_string = "multiple keys pressed at once. ignoring"
                warnings.warn(warning_string)
                continue
            #only one so get it
            key = int(next(iter(keys)))
            if not key in mapping_inv:
                warning_string = f"Recieved unknown input key: {key}"
                warnings.warn(warning_string)
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
        tw.gen_commands("Hello my friend!")
        tw.type_queue_blocking()
        # print(tw.read_blocking(5))
