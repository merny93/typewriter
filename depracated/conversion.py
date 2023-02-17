import string
import json
import typewriter as tw
import time

chars_list = list(string.printable)

mapping = {}

tw._init()

for letter in chars_list:
    print("input letter:", letter, "or ctrl+c to skip")
    try:
        while True:
            res = tw._read(500)
            try:
                ans = res.index(True)
                print("got mapping", letter,":", ans)
                mapping[letter] = ans
                time.sleep(0.2)
                break
            except:
                pass
    except:
        print("\nSkipping:", letter)
        pass
    
tw._cleanup()
