import math, collections, json
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

for tag,fn in [("gripA","/tmp/grip2.json"),("gripB","/tmp/grip3.json")]:
    canon,pos,adj,edges=build(fn)
    deg={g:len(adj[g]) for g in canon}
    hand108=hand_nodes(108,adj); hand135=hand_nodes(135,adj)
    # legs: branch from chest 104 via spine 103 -> the 4 leg leaves; hips by x sign
    legnodes=set(subtree(104,103,adj))
    legleaves=[g for g in legnodes if deg[g]==1]
    xpos=[(pos[g][0],g) for g in legleaves]
    # body left-right axis from leg leaves spread (PCA on leg leaves)
    LP=np.array([pos[g] for g in legnodes])
    legcen=LP.mean(0)
    # hip line: vector separating the two leg clusters
    plusx=[g for g in legleaves if pos[g][0]>legcen[0]]
    minusx=[g for g in legleaves if pos[g][0]<=legcen[0]]
    cpx=np.mean([pos[g] for g in plusx],0); cmx=np.mean([pos[g] for g in minusx],0)
    hipaxis=cpx-cmx; hipaxis/=np.linalg.norm(hipaxis)  # points toward +x leg cluster
    # shoulders (upper-arm node adjacent to chest)
    sh108=[n for n in adj[108] if n==arm_neighbor(108,adj)][0]  # 107... no, that's toward wrist
    # better: shoulder = node on arm path adjacent to chest 104
    def shoulder(hub):
        # walk arm from hub until neighbor of 104
        arm=arm_neighbor(hub,adj); prev=hub;cur=arm
        while 104 not in adj[cur]:
            nxt=[y for y in adj[cur] if y!=prev]; 
            if not nxt: break
            prev,cur=cur,nxt[0]
        return cur
    s108=shoulder(108); s135=shoulder(135)
    # project shoulder positions onto hipaxis (which points to +x leg)
    p108=np.dot(np.array(pos[s108])-legcen,hipaxis)
    p135=np.dot(np.array(pos[s135])-legcen,hipaxis)
    out=dict(
        nodes={str(g):pos[g] for g in canon},
        edges=[[int(a),int(b)] for (a,b,c) in edges],
        wrists=dict(hand108=108,hand135=135),
        hand108=sorted(int(x) for x in hand108),
        hand135=sorted(int(x) for x in hand135),
        chest=104, head_branch=159, spine_branch=103,
        shoulders=dict(hand108=int(s108),hand135=int(s135)),
        shoulder_proj_on_hipaxis=dict(hand108=float(p108),hand135=float(p135)),
        legleaves_x=xpos,
    )
    with open(f"/tmp/labeled_{tag}.json","w") as f: json.dump(out,f)
    print(f"{tag}: shoulder108={s108} proj={p108:+.3f} | shoulder135={s135} proj={p135:+.3f} | legleaves {sorted(legleaves)}")
    print(f"   +x leg cluster {plusx}, -x leg cluster {minusx}")
