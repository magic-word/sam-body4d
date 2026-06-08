import json, math, collections
import numpy as np
exec(open("/tmp/recon2.py").read().split("for tag,fn")[0])
def build(fn):
    j,b=load(fn); canon,pos,groups,edges,adj=reconstruct(j,b); return canon,pos,adj,edges
def subtree(hub,start,adj):
    seen={hub}; st=[start]; out=[]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); out.append(x)
        for y in adj[x]:
            if y not in seen: st.append(y)
    return out
def arm_neighbor(hub,adj):
    best=None;bsz=-1
    for nb in adj[hub]:
        sz=len(subtree(hub,nb,adj))
        if sz>bsz: bsz=sz;best=nb
    return best
def hand_nodes(hub,adj):
    arm=arm_neighbor(hub,adj); out={hub}
    for nb in adj[hub]:
        if nb!=arm: out|=set(subtree(hub,nb,adj))
    return out

# ---- derive finger assignment ONCE from grip A ----
cA,posA,adjA,edgesA=build("/tmp/grip2.json")
degA={g:len(adjA[g]) for g in cA}

FCOL={"thumb":(0.90,0.15,0.12),"index":(0.95,0.55,0.10),"middle":(0.95,0.90,0.15),
      "ring":(0.20,0.55,0.95),"pinky":(0.70,0.25,0.85)}

label_map={}   # node_id -> dict(side,finger,level)
hand_struct={} # side -> dict(wrist, palm[], fingers[{name,nodes[]}])
for side,hub in [("Right",108),("Left",135)]:
    hn=hand_nodes(hub,adjA)
    par={hub:None}; dq=collections.deque([hub])
    while dq:
        x=dq.popleft()
        for y in adjA[x]:
            if y in hn and y not in par: par[y]=x; dq.append(y)
    tips=[g for g in hn if degA[g]==1]
    palm=set(g for g in hn if g!=hub and degA[g]>=3)
    # finger = tip back until wrist or palm node (stop before it)
    fingers=[]
    for t in tips:
        ch=[t]
        while True:
            p=par[ch[-1]]
            if p==hub or p in palm or p is None: break
            ch.append(p)
        ch=ch[::-1]  # MCP..tip
        fingers.append(ch)
    # name fingers from geometry
    W=np.array(posA[hub])
    mcps=[np.array(posA[c[0]]) for c in fingers]
    dirs=[(m-W)/(np.linalg.norm(m-W)+1e-9) for m in mcps]
    mean=sum(dirs)/len(dirs); mean/=np.linalg.norm(mean)
    angs=[math.degrees(math.acos(max(-1,min(1,float(np.dot(d,mean)))))) for d in dirs]
    lens=[sum(np.linalg.norm(np.array(posA[c[k+1]])-np.array(posA[c[k]])) for k in range(len(c)-1)) for c in fingers]
    thumb=int(np.argmax([a*0.4-l*30 for a,l in zip(angs,lens)]))
    M=np.array(mcps); _,_,Vt=np.linalg.svd(M-M.mean(0)); across=Vt[1]
    proj={i:float(np.dot(mcps[i]-W,across)) for i in range(len(fingers))}
    others=sorted([i for i in range(len(fingers)) if i!=thumb],key=lambda i:proj[i])
    names=[None]*len(fingers); names[thumb]="thumb"
    for k,i in enumerate(others): names[i]=["index","middle","ring","pinky"][k]
    flist=[]
    for ci,ch in enumerate(fingers):
        L=len(ch); nm=names[ci]
        for k,node in enumerate(ch):
            lvl="MCP" if k==0 else ("tip" if k==L-1 else ["PIP","DIP","J4","J5"][min(k-1,3)])
            label_map[node]=dict(side=side,finger=nm,level=lvl)
        flist.append(dict(name=nm,nodes=[int(x) for x in ch]))
    for pnode in palm: label_map[pnode]=dict(side=side,finger="palm",level="metacarpal")
    label_map[hub]=dict(side=side,finger="wrist",level="wrist")
    hand_struct[side]=dict(wrist=int(hub),palm=[int(p) for p in palm],fingers=flist)

# ---- emit geometry for both grips using the SAME label_map ----
for tag,fn in [("A","/tmp/grip2.json"),("B","/tmp/grip3.json")]:
    c,pos,adj,edges=build(fn)
    out={"side":{}}
    for side,hub in [("Right",108),("Left",135)]:
        hn=hand_nodes(hub,adj)
        nodes=[]
        for g in sorted(hn):
            lm=label_map.get(g,dict(side=side,finger="?",level="?"))
            nodes.append(dict(id=int(g),pos=pos[g],finger=lm["finger"],level=lm["level"]))
        hedges=[[int(a),int(b)] for (a,b,_) in edges if a in hn and b in hn]
        out["side"][side]=dict(wrist=int(hub),nodes=nodes,edges=hedges)
    out["colors"]=FCOL
    json.dump(out, open(f"/tmp/handgeo_{tag}.json","w"))

json.dump(dict(label_map={str(k):v for k,v in label_map.items()},struct=hand_struct,colors=FCOL),
          open("/tmp/hand_labels.json","w"))
print("FINGER ASSIGNMENT (from grip A, applied to both):")
for side in ("Right","Left"):
    print(f"\n{side} hand  (wrist {hand_struct[side]['wrist']}, palm nodes {hand_struct[side]['palm']}):")
    for f in hand_struct[side]["fingers"]:
        print(f"  {f['name']:7s}: {f['nodes']}")
