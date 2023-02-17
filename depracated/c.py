import json

st = '''input letter: 0 or ctrl+c to skip
got mapping 0 : 17
input letter: 1 or ctrl+c to skip
got mapping 1 : 48
input letter: 2 or ctrl+c to skip
got mapping 2 : 49
input letter: 3 or ctrl+c to skip
got mapping 3 : 40
input letter: 4 or ctrl+c to skip
got mapping 4 : 41
input letter: 5 or ctrl+c to skip
got mapping 5 : 32
input letter: 6 or ctrl+c to skip
got mapping 6 : 33
input letter: 7 or ctrl+c to skip
got mapping 7 : 24
input letter: 8 or ctrl+c to skip
got mapping 8 : 25
input letter: 9 or ctrl+c to skip
got mapping 9 : 16
input letter: a or ctrl+c to skip
got mapping a : 60
input letter: b or ctrl+c to skip
got mapping b : 46
input letter: c or ctrl+c to skip
got mapping c : 54
input letter: d or ctrl+c to skip
got mapping d : 52
input letter: e or ctrl+c to skip
got mapping e : 50
input letter: f or ctrl+c to skip
got mapping f : 53
input letter: g or ctrl+c to skip
got mapping g : 44
input letter: h or ctrl+c to skip
got mapping h : 45
input letter: i or ctrl+c to skip
got mapping i : 27
input letter: j or ctrl+c to skip
got mapping j : 36
input letter: k or ctrl+c to skip
got mapping k : 37
input letter: l or ctrl+c to skip
got mapping l : 28
input letter: m or ctrl+c to skip
got mapping m : 38
input letter: n or ctrl+c to skip
got mapping n : 47
input letter: o or ctrl+c to skip
got mapping o : 26
input letter: p or ctrl+c to skip
got mapping p : 19
input letter: q or ctrl+c to skip
got mapping q : 58
input letter: r or ctrl+c to skip
got mapping r : 43
input letter: s or ctrl+c to skip
got mapping s : 61
input letter: t or ctrl+c to skip
got mapping t : 42
input letter: u or ctrl+c to skip
got mapping u : 34
input letter: v or ctrl+c to skip
got mapping v : 55
input letter: w or ctrl+c to skip
got mapping w : 51
input letter: x or ctrl+c to skip
got mapping x : 63
input letter: y or ctrl+c to skip
got mapping y : 35
input letter: z or ctrl+c to skip
got mapping z : 62
input letter: A or ctrl+c to skip'''
mapping = {}

for line in st.splitlines():
    print(line)
    if line.startswith("got mapping"):
        parts = line.split(" : ")
        mapping[parts[0][-1]] = int(parts[1])

with open("mapping.json", "x") as f:
    f.writelines(json.dumps(mapping))