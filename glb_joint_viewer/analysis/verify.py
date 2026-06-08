import json, math, collections
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
def kabsch(P,Q):
    Pc=P-P.mean(0); Qc=Q-Q.mean(0); H=Pc.T@Qc
    U,S,Vt=np.linalg.svd(H); d=np.sign(np.linalg.det(Vt.T@U.T))
    R=Vt.T@np.diag([1,1,d])@U.T; return R
def ang(R): return math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))

A,posA,adjA=build("/tmp/grip2.json")
B,posB,adjB=build("/tmp/grip3.json")

# ---- 1. GLOBAL-ROTATION INVARIANCE TEST ----
def rel_angle(posA,posB):
    Qs={}
    for hub in (108,135):
        common=sorted(hand_nodes(hub,adjA)&hand_nodes(hub,adjB))
        P=np.array([posA[i] for i in common]); Q=np.array([posB[i] for i in common])
        Qs[hub]=kabsch(P,Q)
    return ang(Qs[135].T@Qs[108])
base=rel_angle(posA,posB)
# apply random rotation G to ALL of grip B
rng=np.random.default_rng(7)
Gv,_=np.linalg.qr(rng.standard_normal((3,3)))
if np.linalg.det(Gv)<0: Gv[:,0]*=-1
posB_rot={k:(Gv@np.array(v)).tolist() for k,v in posB.items()}
rot=rel_angle(posA,posB_rot)
print(f"1. GLOBAL-INVARIANCE: relative angle baseline={base:.2f}deg, after random G on grip B={rot:.2f}deg, diff={abs(base-rot):.4f}deg")

# ---- 2. LEFT/RIGHT via arm trace to shoulders ----
def trace_arm(hub,adj):
    # walk from hub via arm neighbor along the chain; record nodes until a branch (deg>=3)
    arm=arm_neighbor(hub,adj); path=[hub,arm]; prev=hub; cur=arm
    while True:
        nxt=[y for y in adj[cur] if y!=prev]
        if len(adj[cur])>=3 or len(nxt)!=1:  # reached branch (shoulder/torso) 
            break
        prev,cur=cur,nxt[0]; path.append(cur)
    return path
for hub in (108,135):
    p=trace_arm(hub,adjA)
    print(f"2. arm trace from wrist {hub}: {p}  (endpoint pos {[round(x,3) for x in posA[p[-1]]]})")

# find root/pelvis = node maximizing min-eccentricity (graph center) on full tree
def graph_center(canon,adj):
    import collections
    best=None;bestecc=1e9
    for s in canon:
        d={s:0}; dq=collections.deque([s])
        while dq:
            x=dq.popleft()
            for y in adj[x]:
                if y not in d: d[y]=d[x]+1; dq.append(y)
        ecc=max(d.values())
        if ecc<bestecc: bestecc=ecc;best=s
    return best,bestecc
ctr,ecc=graph_center(A,adjA)
print(f"   graph center (≈pelvis/torso) node={ctr} pos={[round(x,3) for x in posA[ctr]]} ecc={ecc}")

# shoulders = endpoints of arm traces
sh108=trace_arm(108,adjA)[-1]; sh135=trace_arm(135,adjA)[-1]
print(f"   shoulder for wrist108 = node {sh108} pos={[round(x,3) for x in posA[sh108]]}")
print(f"   shoulder for wrist135 = node {sh135} pos={[round(x,3) for x in posA[sh135]]}")

# body frame: up = center->head-ish? Use spine: center to highest-eccentricity head cluster.
# Determine L/R by chirality: define up (torso) and forward, then sign of (shoulder . sideaxis)
ctrp=np.array(posA[ctr])
# crude up vector: from pelvis center toward mean of the two shoulders' parent (chest)
sA=np.array(posA[sh108]); sB=np.array(posA[sh135])
chest=(sA+sB)/2
up=chest-ctrp; up/=np.linalg.norm(up)
shoulder_line=sB-sA  # from 108-shoulder to 135-shoulder
# forward = up x shoulder_line
fwd=np.cross(up,shoulder_line); fwd/=np.linalg.norm(fwd)
# side(right-hand-rule): for a person, left shoulder is on +(up x fwd)?
side=np.cross(up,fwd); side/=np.linalg.norm(side)
proj108=np.dot(sA-chest,side); proj135=np.dot(sB-chest,side)
print(f"2. L/R: proj of shoulder108 on side-axis={proj108:+.3f}, shoulder135={proj135:+.3f}")
print(f"   (anatomical left side = +side if forward computed as up x shoulderline(108->135))")
