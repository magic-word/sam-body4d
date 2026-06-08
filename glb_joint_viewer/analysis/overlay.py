import json
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
def kabsch(P,Q):
    Pc=P-P.mean(0); Qc=Q-Q.mean(0); H=Pc.T@Qc
    U,S,Vt=np.linalg.svd(H); d=np.sign(np.linalg.det(Vt.T@U.T))
    return Vt.T@np.diag([1,1,d])@U.T

A,posA,adjA,edgesA=build("/tmp/grip2.json"); B,posB,adjB,edgesB=build("/tmp/grip3.json")
RIGHT,LEFT=108,135
Lc=sorted(hand_nodes(LEFT,adjA)&hand_nodes(LEFT,adjB))
Rset=sorted(hand_nodes(RIGHT,adjA)&hand_nodes(RIGHT,adjB))
# align grip B -> grip A by LEFT hand
PL_A=np.array([posA[i] for i in Lc]); PL_B=np.array([posB[i] for i in Lc])
L=kabsch(PL_B,PL_A); cB=PL_B.mean(0); cA=PL_A.mean(0)
posB_al={i:(L@(np.array(p)-cB)+cA).tolist() for i,p in posB.items()}
# right-hand edges (within Rset)
Redges=[[a,b] for (a,b,c) in edgesA if a in Rset and b in Rset]
out=dict(
  rightA={str(i):posA[i] for i in Rset},
  rightB_aligned={str(i):posB_al[i] for i in Rset},
  edges=Redges, wrist=RIGHT)
json.dump(out, open("/tmp/overlay.json","w"))
print("right-hand nodes:",len(Rset),"edges:",len(Redges))
