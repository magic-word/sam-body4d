import json, math, itertools

def load(fn):
    with open(fn) as f: d=json.load(f)
    joints={int(k):v for k,v in d["joints"].items()}
    bones={int(k):v for k,v in d["bones"].items()}
    return joints,bones

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
            if dist(joints[ids[i]],joints[ids[k]])<eps:
                parent[find(ids[k])]=find(ids[i])
    groups={}
    for j in ids: groups.setdefault(find(j),[]).append(j)
    canon=sorted(groups)
    pos={g:joints[g] for g in canon}
    return canon,pos,groups

def nearest_k(p,canon,pos,k=6):
    return sorted(canon,key=lambda g:dist(p,pos[g]))[:k]

def reconstruct(joints,bones):
    canon,pos,groups=dedupe(joints)
    # global one-to-one bone<->edge assignment
    cands=[]  # (cost, bone_id, edge(a,b))
    for bid,(p1,p2) in bones.items():
        blen=dist(p1,p2); bmid=[(p1[i]+p2[i])/2 for i in range(3)]
        bdir=norm(sub(p2,p1))
        n1=nearest_k(p1,canon,pos); n2=nearest_k(p2,canon,pos)
        seen=set()
        for a in n1:
            for b in n2:
                if a==b: continue
                key=(min(a,b),max(a,b))
                if key in seen: continue
                seen.add(key)
                pa,pb=pos[a],pos[b]
                elen=dist(pa,pb); emid=[(pa[i]+pb[i])/2 for i in range(3)]
                edir=norm(sub(pb,pa))
                cost=dist(bmid,emid)+abs(blen-elen)+0.05*(1-abs(dot(bdir,edir)))
                cands.append((cost,bid,key))
    cands.sort()
    used_bone=set(); used_edge=set(); edges=[]
    for cost,bid,key in cands:
        if bid in used_bone or key in used_edge: continue
        used_bone.add(bid); used_edge.add(key); edges.append((key,cost,bid))
    # build adjacency
    adj={g:set() for g in canon}
    for (a,b),c,bid in edges: adj[a].add(b); adj[b].add(a)
    return canon,pos,groups,edges,adj

def components(canon,adj):
    seen=set(); out=[]
    for s in canon:
        if s in seen: continue
        st=[s]; c=[]
        while st:
            x=st.pop()
            if x in seen: continue
            seen.add(x); c.append(x)
            for y in adj[x]:
                if y not in seen: st.append(y)
        out.append(sorted(c))
    return out

for tag,fn in [("gripA","/tmp/grip2.json"),("gripB","/tmp/grip3.json")]:
    joints,bones=load(fn)
    canon,pos,groups,edges,adj=reconstruct(joints,bones)
    cc=components(canon,adj)
    degs={g:len(adj[g]) for g in canon}
    dh={}
    for g in canon: dh[degs[g]]=dh.get(degs[g],0)+1
    print(f"=== {tag} ===")
    print("unique nodes:",len(canon),"edges assigned:",len(edges),"components:",len(cc))
    print("comp sizes:",sorted([len(c) for c in cc],reverse=True))
    print("merged pairs:",{k:v for k,v in groups.items() if len(v)>1})
    print("degree histogram:",dict(sorted(dh.items())))
    hubs=[g for g in canon if degs[g]>=5]
    print("degree>=5 hubs:",[(g,degs[g],[round(x,3) for x in pos[g]]) for g in hubs])
