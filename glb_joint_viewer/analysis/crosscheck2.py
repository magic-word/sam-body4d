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
def kabsch(P,Q):  # R: Pc->Qc
    Pc=P-P.mean(0); Qc=Q-Q.mean(0); H=Pc.T@Qc
    U,S,Vt=np.linalg.svd(H); d=np.sign(np.linalg.det(Vt.T@U.T))
    return Vt.T@np.diag([1,1,d])@U.T
def ang(R): return math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))
def axis(R):
    w=np.array([R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1]]); n=np.linalg.norm(w)
    return (w/n).tolist() if n>1e-9 else [0,0,0]

A,posA,adjA=build("/tmp/grip2.json"); B,posB,adjB=build("/tmp/grip3.json")
RIGHT,LEFT=108,135   # right=mover, left=anchor

def common(hub): return sorted(hand_nodes(hub,adjA)&hand_nodes(hub,adjB))
Lc=common(LEFT); Rc=common(RIGHT)

# Method X: align grip B to grip A by LEFT hand, then measure RIGHT hand residual rotation
PL_A=np.array([posA[i] for i in Lc]); PL_B=np.array([posB[i] for i in Lc])
L=kabsch(PL_B,PL_A)               # rotation mapping gripB-left -> gripA-left (about centroids)
cB_L=PL_B.mean(0); cA_L=PL_A.mean(0)
# transform ALL grip B points into grip-A left-hand-aligned frame
posB_aligned={i:(L@(np.array(p)-cB_L)+cA_L).tolist() for i,p in posB.items()}
PR_A=np.array([posA[i] for i in Rc]); PR_Bal=np.array([posB_aligned[i] for i in Rc])
Rres=kabsch(PR_A,PR_Bal)          # right hand rotation A->B after left-alignment
print(f"Method X (align by LEFT hand, measure RIGHT residual):")
print(f"  >>> relative rotation = {ang(Rres):.1f} deg  axis={[round(x,2) for x in axis(Rres)]}")

# symmetric: align by RIGHT, measure LEFT residual (should match magnitude)
PR_A2=np.array([posA[i] for i in Rc]); PR_B2=np.array([posB[i] for i in Rc])
Rr=kabsch(PR_B2,PR_A2); cB_R=PR_B2.mean(0); cA_R=PR_A2.mean(0)
posB_al2={i:(Rr@(np.array(p)-cB_R)+cA_R).tolist() for i,p in posB.items()}
PL_A2=np.array([posA[i] for i in Lc]); PL_B2=np.array([posB_al2[i] for i in Lc])
Lres=kabsch(PL_A2,PL_B2)
print(f"Method X' (align by RIGHT hand, measure LEFT residual) = {ang(Lres):.1f} deg")

# Method Y (already-known Kabsch composition) for reference
QR=kabsch(PR_A,PR_B2); QL=kabsch(PL_A,PL_B)
print(f"Method Y (Q_left^-1 Q_right composition) = {ang(QL.T@QR):.1f} deg")
