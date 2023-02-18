from typewriter import Typewriter
import sys
data = sys.stdin.read()

with Typewriter() as tw:
    tw.gen_commands(data)
    tw.type_queue_blocking()