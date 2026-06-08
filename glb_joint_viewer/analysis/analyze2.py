import json, math

def load(fn):
    with open(fn) as f: return json.load(f)
def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))

def build(data, eps=0.004):
    raw = {int(k):v for k,v in data["joints"].items()}
    ids = sorted(raw)
    # union-find dedup
    parent={j:j for j in ids}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b): parent[find(a)]=find(b)
    for i in range(len(ids)):
        for k in range(i+1,len(ids)):
            if dist(raw[ids[i]],raw[ids[k]])<eps:
                union(ids[i],ids[k])
    # canonical groups
    groups={}
    for j in ids: groups.setdefault(find(j),[]).append(j)
    canon=sorted(groups)  # representative ids
    pos={g: raw[g] for g in canon}
    def jof(p):
        best=None;bd=1e9
        for g in canon:
            d=dist(p,pos[g])
            if d<bd:bd=d;best=g
        return best
    edges=set()
    for bk,(p1,p2) in data["bones"].items():
        a=jof(p1);b=jof(p2)
        if a!=b: edges.add((min(a,b),max(a,b)))
    adj={g:set() for g in canon}
    for a,b in edges: adj[a].add(b);adj[b].add(a)
    return pos,canon,edges,adj,groups

def comps(canon,adj):
    seen=set();out=[]
    for s in canon:
        if s in seen:continue
        st=[s];c=[]
        while st:
            x=st.pop()
            if x in seen:continue
            seen.add(x);c.append(x)
            for y in adj[x]:
                if y not in seen:st.append(y)
        out.append(sorted(c))
    return out

for tag,fn in [("grip2","/tmp/grip2.json"),("grip3","/tmp/grip3.json")]:
    pos,canon,edges,adj,groups=build(load(fn))
    cc=comps(canon,adj)
    degs={g:len(adj[g]) for g in canon}
    print(f"=== {tag} ===")
    print("unique joints",len(canon),"edges",len(edges),"components",len(cc))
    print("comp sizes",sorted([len(c) for c in cc],reverse=True))
    print("merged groups (dups):",{k:v for k,v in groups.items() if len(v)>1})
    print("deg hist",{d:sum(1 for g in canon if degs[g]==d) for d in sorted(set(degs.values()))})
