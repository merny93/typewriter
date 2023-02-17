import typewriter as tw
import time
import json
with open("mapping.json") as f:

    mapping = json.load(f)
tw._init()

CAPS = 69
SHIFT = 6
print_string = '''           ;               ,           
         ,;                 '.         
        ;:                   :;        
       ::                     ::       
       ::                     ::       
       ':                     :        
        :.                    :        
     ;' ::                   ::  '     
    .'  ';                   ;'  '.    
   ::    :;                 ;:    ::   
   ;      :;.             ,;:     ::   
   :;      :;:           ,;"      ::   
   ::.      ':;  ..,.;  ;:'     ,.;:   
    "'"...   '::,::::: ;:   .;.;""'    
        '"""....;:::::;,;.;"""         
    .:::.....'"':::::::'",...;::::;.   
   ;:' '""'"";.,;:::::;.'""""""  ':;   
  ::'         ;::;:::;::..         :;  
 ::         ,;:::::::::::;:..       :: 
 ;'     ,;;:;::::::::::::::;";..    ':.
::     ;:"  ::::::"""'::::::  ":     ::
 :.    ::   ::::::;  :::::::   :     ; 
  ;    ::   :::::::  :::::::   :    ;  
   '   ::   ::::::....:::::'  ,:   '   
    '  ::    :::::::::::::"   ::       
       ::     ':::::::::"'    ::       
       ':       """""""'      ::       
        ::                   ;:        
        ':;                 ;:"        
-hrr-     ';              ,;'          
            "'           '"            
              ' '''
commands = []

def get_key_seq(char, default = "?"):
    if char in mapping:
        #great
        key = [mapping[char],]
        #is it a shift thing
        if type(key[0]) == str:
            key = [CAPS,mapping[key[0]], SHIFT]
    elif char.lower() in mapping:
        key = [CAPS,mapping[char.lower()], SHIFT]
    else:
        key = get_key_seq(default)
    return key

for s in print_string:
    for key in get_key_seq(s, default=" "):
        tw._write(key,4)
        time.sleep(0.1)

tw._cleanup()