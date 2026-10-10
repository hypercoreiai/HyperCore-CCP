import json
d=json.load(open('_index.json'))
for e in d:
    print(f"{e['slug'][:32]:32} | pub={str(e['publisher'])[:11]:11} | size={str(e['params'])[:14]:14} | ctx={str(e['ctx'])[:18]:18} | arch={str(e['arch'])[:28]:28} | rel={str(e['release'])[:18]:18}")
