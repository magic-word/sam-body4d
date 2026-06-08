import json, math
import numpy as np
exec(open("/tmp/recon2.py").read().split("for tag,fn")[0])  # reuse funcs

def build(fn):
    joints,bones=load(fn)
    canon,pos,groups,edges,adj=reconstruct(joints,bones)
    return canon,pos,adj

def subtree(hub,start,adj):
    seen={hub}; st=[start]; out=[]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); out.append(x)
        for y in adj[x]:
            if y not in seen: st.append(y)
    return out

def hand_nodes(hub,adj,arm_nb):
    # all nodes in hub subtree except arm branch; include hub
    out={hub}
    for nb in adj[hub]:
        if nb==arm_nb: continue
        out|=set(subtree(hub,nb,adj))
    return out

def hops_from(hub,adj,maxhop):
    # BFS hop distance from hub, not crossing into arm (we just BFS whole then filter by membership)
    dist={hub:0}; from collections import deque
A,posA,adjA=build("/tmp/grip2.json")
B,posB,adjB=build("/tmp/grip3.json")

# arm neighbor = the large branch (size>10)
def arm_neighbor(hub,adj):
    best=None;bsz=-1
    for nb in adj[hub]:
        sz=len(subtree(hub,nb,adj))
        if sz>bsz: bsz=sz;best=nb
    return best

def proximal_set(hub,adj,armnb,maxhop):
    # BFS from hub within hand only
    hand=hand_nodes(hub,adj,armnb)
    import collections
    dq=collections.deque([(hub,0)]); seen={hub}; out=set()
    while dq:
        x,d=dq.popleft()
        if d<=maxhop: out.add(x)
        if d>=maxhop: continue
        for y in adj[x]:
            if y in hand and y not in seen:
                seen.add(y); dq.append((y,d+1))
    return out

results={}
for label,(hubA,hubB) in [("hand1(108)",(108,108)),("hand2(135)",(135,135))]:
    armA=arm_neighbor(hubA,adjA); armB=arm_neighbor(hubB,adjB)
    handA=hand_nodes(hubA,adjA,armA); handB=hand_nodes(hubB,adjB,armB)
    results[label]=dict(armA=armA,armB=armB,handA=sorted(handA),handB=sorted(handB),
                        common=sorted(handA&handB))
    print(label,"armA",armA,"armB",armB,"|handA|",len(handA),"|handB|",len(handB),"common",len(handA&handB))

def kabsch(P,Q):
    # rotation mapping P->Q (both Nx3), centered
    Pc=P-P.mean(0); Qc=Q-Q.mean(0)
    H=Pc.T@Qc
    U,S,Vt=np.linalg.svd(H)
    d=np.sign(np.linalg.det(Vt.T@U.T))
    D=np.diag([1,1,d])
    R=Vt.T@D@U.T
    return R, np.sqrt(((Qc-(Pc@R.T))**2).sum()/len(P))  # R maps Pc -> Qc: Qc ~ R@Pc

def ang(R):
    return math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))
def axis(R):
    w=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]])
    n=np.linalg.norm(w)
    return (w/n).tolist() if n>1e-9 else [0,0,0]

print("\n--- Kabsch per hand (grip A -> grip B), several node subsets ---")
for subset_name, maxhop in [("wrist+full hand",99),("wrist+hop<=2 (palm/MCP)",2),("wrist+hop<=3",3)]:
    Qs={}
    rmsds={}
    for label,(hub,_) in [("hand1",(108,108)),("hand2",(135,135))]:
        armA=arm_neighbor(hub,adjA); armB=arm_neighbor(hub,adjB)
        if maxhop>=99:
            common=sorted(hand_nodes(hub,adjA,armA) & hand_nodes(hub,adjB,armB))
        else:
            common=sorted(proximal_set(hub,adjA,armA,maxhop) & proximal_set(hub,adjB,armB,maxhop))
        P=np.array([posA[i] for i in common]); Q=np.array([posB[i] for i in common])
        R,rmsd=kabsch(P,Q)
        Qs[label]=R; rmsds[label]=(len(common),rmsd)
    rel = Qs["hand2"].T @ Qs["hand1"]   # Q_left^{-1} Q_right (angle invariant to which is which)
    print(f"\n[{subset_name}]")
    for label in ("hand1","hand2"):
        n,rm=rmsds[label]; print(f"   {label}: npts={n} kabsch_rmsd={rm*1000:.1f}mm self_rot={ang(Qs[label]):.1f}deg")
    print(f"   >>> RELATIVE right-vs-left change between grips = {ang(rel):.1f} deg  axis={[round(x,2) for x in axis(rel)]}")
