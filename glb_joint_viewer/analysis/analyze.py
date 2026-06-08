import json, math

def load(fn):
    with open(fn) as f: return json.load(f)

def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))

def build(data):
    joints = {int(k):v for k,v in data["joints"].items()}
    ids = sorted(joints)
    # snap bone endpoints to nearest joint
    edges=set()
    bonelens={}
    for bk,(p1,p2) in data["bones"].items():
        def nearest(p):
            best=None;bd=1e9
            for j in ids:
                d=dist(p,joints[j])
                if d<bd: bd=d;best=j
            return best,bd
        j1,d1=nearest(p1); j2,d2=nearest(p2)
        if j1!=j2:
            edges.add((min(j1,j2),max(j1,j2)))
    adj={j:set() for j in ids}
    for a,b in edges:
        adj[a].add(b); adj[b].add(a)
    return joints,ids,edges,adj

def components(ids,adj):
    seen=set();comps=[]
    for s in ids:
        if s in seen: continue
        stack=[s];comp=[]
        while stack:
            x=stack.pop()
            if x in seen: continue
            seen.add(x);comp.append(x)
            for y in adj[x]:
                if y not in seen: stack.append(y)
        comps.append(sorted(comp))
    return comps

for tag,fn in [("grip2","/tmp/grip2.json"),("grip3","/tmp/grip3.json")]:
    data=load(fn)
    joints,ids,edges,adj=build(data)
    comps=components(ids,adj)
    degs={j:len(adj[j]) for j in ids}
    leaves=[j for j in ids if degs[j]==1]
    branch=[j for j in ids if degs[j]>=3]
    print(f"=== {tag} ===")
    print("n_joints",len(ids),"n_edges",len(edges),"n_components",len(comps))
    print("component sizes:",[len(c) for c in comps])
    print("leaves(deg1):",len(leaves),"branch(deg>=3):",len(branch))
    print("degree histogram:",{d:sum(1 for j in ids if degs[j]==d) for d in sorted(set(degs.values()))})
