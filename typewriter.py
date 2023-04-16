import ctypes
import time
import os
import threading
import json
import warnings
import sysv_ipc
from queue import Queue, Full, Empty
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
_lib.init_tw.argtypes = tuple()
_lib.init_tw.restype = ctypes.c_int
def _init():
    global _lib
    return int(_lib.init_tw())

## now cleanup
_lib.cleanup_tw.argtypes = tuple()
_lib.cleanup_tw.restype = ctypes.c_int
def _cleanup():
    global _lib
    return int(_lib.cleanup_tw())


## streaming read
_lib.read_stream_tw.argtypes = (ctypes.POINTER(ctypes.c_int),)
def _read_stream(alive_array):
    global _lib
    _lib.read_stream_tw(alive_array)
    return 

#multiple write
_lib.write_multiple_tw.argtypes = (ctypes.POINTER(ctypes.c_int),ctypes.c_int, ctypes.c_int)
_lib.write_multiple_tw.restype = ctypes.c_int
def _write_many(key_list, ms_per_key):
    global _lib
    key_type =  ctypes.c_int*len(key_list)
    keys = key_type(*key_list)
    return int(_lib.write_multiple_tw( keys,ctypes.c_int(len(key_list)), ctypes.c_int(ms_per_key)))


class ReadStream(object):
    def __init__(self):

        self.mq = sysv_ipc.MessageQueue(1234, sysv_ipc.IPC_CREAT) 
        self._empty()
        
        self.alive = ctypes.POINTER(ctypes.c_int)(ctypes.c_int(1))
        self.c_thread = threading.Thread(target=_read_stream, daemon=True, args=(self.alive,))
           
          
        self.queue = Queue(1000)
        self.read_thread = threading.Thread(target=self._get, daemon=True)
        
    def get(self, max_size = 100):
        res = []
        while True:
            try:
                res.append(self.queue.get(block=False))
                if len(res ) >= max_size:
                    break
            except Empty:
                break
        return res
    def __enter__(self):
        self.c_thread.start() 
        self.read_thread.start()
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
    def _get_next(self):
        try:
            message, mtype = self.mq.receive(block=False)
            res = int.from_bytes(message, byteorder='little')
            try:
                self.queue.put((res, time.time()), block=False,)
            except Full:
                pass
            # print(f"Interpret as numpy: {numpy_message}")
        except sysv_ipc.BusyError:
            return
        except sysv_ipc.ExistentialError:
            return
    def _empty(self):
        while True:
            try:
                _ = self.mq.receive(block=False)
            except sysv_ipc.BusyError:
                return        
    def _get(self):
        while self.alive.contents.value:
            self._get_next()
    def cleanup(self):
        print("quitting")
        self.alive.contents.value = 0
        # time.sleep(0.5)
        self.c_thread.join()
        self.read_thread.join()
        
        
        
        try:
            self.mq.remove()
        except sysv_ipc.ExistentialError:
            print("message queue already removed")
            pass




with open("mapping.json") as f:
    mapping_full = json.load(f)
mapping_full_inv = {
    "None": {v: k for k, v in mapping_full["None"].items()},
    "Shift": {v: k for k, v in mapping_full["Shift"].items()}
}

class Typewriter(object):
    def __init__(self, n_repeat = 8, char_wait = 0.04, cr_wait_p_char = 0.02, read_blocks = 10, double_wait = 0.1 ):
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
        self.stream_ptr=0
        self.stream = []

        self.two_read_gap = 0.07
        self.shift_short_gap = 0.07
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
    def gen_command(self, char, prev_key_n = None):
        '''
        State should contain char_pos
        '''
        def write_func(char_n_seq):
            return lambda self = self, char_n_seq=char_n_seq: _write_many(char_n_seq, self.n_repeat)

        #check if char is in the mapping
        if char in mapping_full["None"]:
            key_n = mapping_full["None"][char]
            self.commanding_queue.append(write_func([key_n]))
        elif char in mapping_full["Shift"]:
            key_n = mapping_full["Shift"][char]
            self.commanding_queue.append(write_func([SHIFT, key_n]))
        else:
            #unknown
            warning_string = f"Unknown charachter: {char}, replaced with default: {self.default}"
            warnings.warn(warning_string)
            
            return self.gen_command(self.default, prev_key_n=prev_key_n)
        if char == "\n":
            #if carriage return wait longer
            wait = self.c_advance*self.cr_wait_p_char
            self.c_advance = 0
        if key_n == prev_key_n:
            wait = self.double_wait
        else:
            #regular wait
            self.c_advance += 1
            wait = self.char_wait

        wait_func = lambda wait=wait: time.sleep(wait)
        #add the sleep
        self.commanding_queue.insert(-1,wait_func)
        return key_n
    def write(self, message, block=True):
        self.gen_commands(message)
        write_thread = threading.Thread(target= self.type_queue_blocking, daemon=True)
        write_thread.start()
        if block:
            write_thread.join()
    def type_queue_blocking(self):
        for command in self.commanding_queue:
            command()
        self.commanding_queue = []
    def gen_commands(self, string):
        """
        Generate commands for string into the commanding queue. Will press shift at the start just in case
        """
        MAX_LINE_LENGTH_SOFT = 60 # characters
        MAX_LINE_WIDTH_HARD = 70 # characters
        self.commanding_queue.append(lambda self=self: _write_many([SHIFT], self.n_repeat))
        prev = 0
        for s in string:
            prev = self.gen_command(s,prev_key_n=prev)
            if self.c_advance > MAX_LINE_LENGTH_SOFT and s == " ":
                self.gen_command("\n")
            elif self.c_advance > MAX_LINE_WIDTH_HARD:
                self.gen_command("-")
                self.gen_command("\n")
        self.commanding_queue.append(lambda self=self: _write_many([SHIFT], self.n_repeat))
    
    def read_stream_worker(self,rs: ReadStream):
        self.stream.extend(rs.get())
        processed_stream = []

        key_seen_dict = {}
        try:
            last_interaction_t = self.stream[0][1]
        except:
            last_interaction_t = 0

        new_stream = self.stream
        for i, (key, key_t) in enumerate(self.stream):
            if key in key_seen_dict:
                last_key_time  = key_seen_dict[key]
            else:
                last_key_time = 0 #zero c time, infinitly far behind

            if key_t - last_key_time > self.two_read_gap:
                #this is a new key
                if key in [SHIFT,]:
                    pass
                    #nothing to do
                elif i < self.stream_ptr:
                    pass
                    #nothing to do, just rebuild the dict
                elif SHIFT in key_seen_dict and key_t - key_seen_dict[SHIFT] < self.shift_short_gap:
                    #its a shift key
                    try:
                        processed_stream.append(mapping_full_inv["Shift"][key])
                    except KeyError:
                        warn_string = f"Unrecognized key {key}"
                        warnings.warn(warn_string)
                else:
                    #not a shift key
                    try:
                        processed_stream.append(mapping_full_inv["None"][key])
                    except KeyError:
                        warn_string = f"Unrecognized key {key}"
                        warnings.warn(warn_string)
            #update the dict of last seen keys
            key_seen_dict[key] = key_t
            if key_t - last_interaction_t > self.two_read_gap:
                #this means that history is irelevant
                new_stream = self.stream[i:]
            last_interaction_t = key_t
        self.stream = new_stream
        self.stream_ptr = len(self.stream)
        return "".join(processed_stream)
    def read_stream(self, rs, timeout, block=True):
        start = time.time()
        res = ""
        while time.time() - start < timeout:
            line= self.read_stream_worker(rs)
            # print("hi")
            res += line
            print(line, end='', flush=True)
            time.sleep(0.25)
        print()
        return res



if __name__ == "__main__":
    with Typewriter() as tw:

        with ReadStream() as rs:
            res = tw.read_stream(rs, 30)
            print("full message:", res)

        # tw.write("heLlo")
