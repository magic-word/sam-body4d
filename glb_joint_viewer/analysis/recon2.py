import json, math

def load(fn):
    with open(fn) as f: d=json.load(f)
    return {int(k):v for k,v in d["joints"].items()},{int(k):v for k,v in d["bones"].items()}
def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
def sub(a,b): return [a[i]-b[i] for i in range(3)]
def norm(a):
    l=math.sqrt(sum(x*x for x in a)); return [x/l for x in a] if l>1e-12 else [0,0,0]
def dot(a,b): return sum(a[i]*b[i] for i in range(3))

def dedupe(joints, eps=0.005):
    ids=sorted(joints); parent={j:j for j in ids}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for i in range(len(ids)):
        for k in range(i+1,len(ids)):
            if dist(joints[ids[i]],joints[ids[k]])<eps: parent[find(ids[k])]=find(ids[i])
    groups={}
    for j in ids: groups.setdefault(find(j),[]).append(j)
    canon=sorted(groups); return canon,{g:joints[g] for g in canon},groups

def nearest_k(p,canon,pos,k=6): return sorted(canon,key=lambda g:dist(p,pos[g]))[:k]

def reconstruct(joints,bones):
    canon,pos,groups=dedupe(joints)
    edge_cost={}  # edge -> min cost  (bone evidence)
    for bid,(p1,p2) in bones.items():
        blen=dist(p1,p2); bmid=[(p1[i]+p2[i])/2 for i in range(3)]; bdir=norm(sub(p2,p1))
        for a in nearest_k(p1,canon,pos):
            for b in nearest_k(p2,canon,pos):
                if a==b: continue
                key=(min(a,b),max(a,b)); pa,pb=pos[a],pos[b]
                elen=dist(pa,pb); emid=[(pa[i]+pb[i])/2 for i in range(3)]; edir=norm(sub(pb,pa))
                cost=dist(bmid,emid)+abs(blen-elen)+0.05*(1-abs(dot(bdir,edir)))
                if key not in edge_cost or cost<edge_cost[key]: edge_cost[key]=cost
    # Kruskal MST over candidate edges
    parent={g:g for g in canon}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra==rb: return False
        parent[ra]=rb; return True
    cand=sorted(edge_cost.items(), key=lambda kv: kv[1])
    edges=[]; deg={g:0 for g in canon}
    for (a,b),c in cand:
        if find(a)!=find(b):
            union(a,b); edges.append((a,b,c)); deg[a]+=1; deg[b]+=1
    # if not fully connected, add nearest-neighbor bridges
    def ncomp():
        roots=set(find(g) for g in canon); return len(roots)
    if ncomp()>1:
        bridges=[]
        for i,a in enumerate(canon):
            for b in canon[i+1:]:
                bridges.append((dist(pos[a],pos[b]),a,b))
        bridges.sort()
        for d,a,b in bridges:
            if find(a)!=find(b):
                union(a,b); edges.append((a,b,d)); deg[a]+=1; deg[b]+=1
    adj={g:set() for g in canon}
    for a,b,c in edges: adj[a].add(b); adj[b].add(a)
    return canon,pos,groups,edges,adj

for tag,fn in [("gripA","/tmp/grip2.json"),("gripB","/tmp/grip3.json")]:
    joints,bones=load(fn)
    canon,pos,groups,edges,adj=reconstruct(joints,bones)
    deg={g:len(adj[g]) for g in canon}
    dh={}
    for g in canon: dh[deg[g]]=dh.get(deg[g],0)+1
    # connectivity check
    seen=set(); st=[canon[0]]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x)
        for y in adj[x]:
            if y not in seen: st.append(y)
    print(f"=== {tag} ===")
    print("nodes:",len(canon),"edges:",len(edges),"connected:",len(seen)==len(canon),"is_tree:",len(edges)==len(canon)-1)
    print("degree histogram:",dict(sorted(dh.items())))
    hubs=sorted([g for g in canon if deg[g]>=5])
    print("deg>=5 hubs:",[(g,deg[g],[round(x,3) for x in pos[g]]) for g in hubs])
