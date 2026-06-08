import math
import numpy as np
exec(open("/tmp/recon2.py").read().split("for tag,fn")[0])
def build(fn):
    j,b=load(fn); canon,pos,groups,edges,adj=reconstruct(j,b); return canon,pos,adj
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
def ang(R): return math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))
def axis(R):
    w=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]]); n=np.linalg.norm(w)
    return (w/n).tolist() if n>1e-9 else [0,0,0]

A,posA,adjA=build("/tmp/grip2.json"); B,posB,adjB=build("/tmp/grip3.json")

def pca_frame(pts, wrist):
    C=pts.mean(0); X=pts-C
    U,S,Vt=np.linalg.svd(X,full_matrices=False)
    R=Vt.T  # columns = principal axes (e1,e2,e3)
    # sign e1 toward fingertips (away from wrist)
    if np.dot(R[:,0], C-wrist)<0: R[:,0]*=-1
    # make right-handed
    if np.linalg.det(R)<0: R[:,2]*=-1
    return R,S

def frames_for(posd,adjd):
    out={}
    for hub in (108,135):
        nodes=sorted(hand_nodes(hub,adjd))
        pts=np.array([posd[i] for i in nodes]); wrist=np.array(posd[hub])
        out[hub]=pca_frame(pts,wrist)[0]
    return out

# sign-consistency: align grip B frames to grip A per hand (fix spurious flips only)
def align(Rb,Ra):
    best=Rb; bestsc=-9
    import itertools
    for s in itertools.product([1,-1],repeat=3):
        Rs=Rb*np.array(s)
        if np.linalg.det(Rs)<0: continue
        sc=np.trace(Ra.T@Rs)
        if sc>bestsc: bestsc=sc; best=Rs
    return best

FA=frames_for(posA,adjA); FB=frames_for(posB,adjB)
FB={h:align(FB[h],FA[h]) for h in FB}

# R_rel = R_left^T R_right ; treat 135=left,108=right (label-independent for angle)
relA=FA[135].T@FA[108]
relB=FB[135].T@FB[108]
dR=relB@relA.T
print("PCA-FRAME cross-check (full-hand point clouds):")
print(f"  per-hand frame rotation A->B: hand108={ang(align(FB[108],FA[108])@FA[108].T if False else FB[108]@FA[108].T):.1f}  hand135={ang(FB[135]@FA[135].T):.1f}")
print(f"  >>> relative right-vs-left change between grips = {ang(dR):.1f} deg  axis={[round(x,2) for x in axis(dR)]}")

# also report per-grip right-relative-to-left frame angle (context)
print(f"  R_rel angle gripA (right wrt left) = {ang(relA):.1f} deg ; gripB = {ang(relB):.1f} deg")
