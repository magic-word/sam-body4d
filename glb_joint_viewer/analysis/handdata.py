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

for tag,fn in [("A","/tmp/grip2.json"),("B","/tmp/grip3.json")]:
    canon,pos,adj,edges=build(fn)
    deg={g:len(adj[g]) for g in canon}
    out={}
    for side,hub in [("Right",108),("Left",135)]:
        hn=hand_nodes(hub,adj)
        # BFS parent within hand from wrist
        par={hub:None}; hop={hub:0}; dq=collections.deque([hub])
        while dq:
            x=dq.popleft()
            for y in adj[x]:
                if y in hn and y not in par: par[y]=x; hop[y]=hop[x]+1; dq.append(y)
        tips=[g for g in hn if deg[g]==1]
        # finger chain: tip back to (but not incl) wrist
        chains=[]
        for t in tips:
            ch=[t]
            while par[ch[-1]] not in (hub,None): ch.append(par[ch[-1]])
            ch=ch[::-1]
            chains.append(ch)
        # name fingers
        W=np.array(pos[hub])
        mcps=[np.array(pos[c[0]]) for c in chains]
        dirs=[ (m-W)/(np.linalg.norm(m-W)+1e-9) for m in mcps]
        mean=sum(dirs)/len(dirs); mean/=np.linalg.norm(mean)
        # thumb = max angle from mean dir AND shortest-ish
        angs=[math.degrees(math.acos(max(-1,min(1,float(np.dot(d,mean)))))) for d in dirs]
        lens=[sum(np.linalg.norm(np.array(pos[c[k+1]])-np.array(pos[c[k]])) for k in range(len(c)-1)) for c in chains]
        thumb=int(np.argmax([a*0.5 - l for a,l in zip(angs,lens)]))  # abducted & short
        # order remaining by position along across-axis (PCA e2 of MCPs)
        M=np.array(mcps); Mc=M-M.mean(0)
        _,_,Vt=np.linalg.svd(Mc); across=Vt[1]
        proj={i:float(np.dot(mcps[i]-W,across)) for i in range(len(chains))}
        others=sorted([i for i in range(len(chains)) if i!=thumb], key=lambda i:proj[i])
        names=["?"]*len(chains); names[thumb]="thumb"
        for k,i in enumerate(others): names[i]=["index","middle","ring","pinky"][k] if k<4 else f"f{k}"
        fingers=[]
        for ci,ch in enumerate(chains):
            L=len(ch)
            joints=[]
            for k,node in enumerate(ch):
                if k==0: lvl="MCP (knuckle)"
                elif k==L-1: lvl="tip"
                else: lvl=["PIP","DIP","joint4","joint5"][k-1] if k-1<4 else f"j{k}"
                joints.append(dict(id=int(node), level=lvl, pos=pos[node]))
            fingers.append(dict(name=names[ci], joints=joints))
        # palm/metacarpal extra nodes (in hand, not wrist, not in any chain)
        chainset=set(n for c in chains for n in c)
        palm=[int(g) for g in hn if g!=hub and g not in chainset]
        out[side]=dict(wrist=dict(id=int(hub),pos=pos[hub]),
                       fingers=fingers, palm=[dict(id=g,pos=pos[g]) for g in palm])
    json.dump(out, open(f"/tmp/hands_{tag}.json","w"))
    # print summary
    print(f"=== grip {tag} ===")
    for side in out:
        fs=out[side]["fingers"]
        print(f" {side} wrist={out[side]['wrist']['id']} palm={[p['id'] for p in out[side]['palm']]}")
        for f in fs:
            print(f"   {f['name']:7s}: "+" -> ".join(f"{j['id']}({j['level']})" for j in f['joints']))
