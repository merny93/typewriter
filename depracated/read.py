import typewriter as tw
import time
print(tw._init())
try:
    while True:
            res = tw._read(20)
            try:
                ress = list(map(lambda x: x >0, res))
                ans = ress.index(True)
                print(ans)
                print(res)
                
                
            except:
                pass
except:
     tw._cleanup()