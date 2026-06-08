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

A,pos,adj,edges=build("/tmp/grip2.json")
deg={g:len(adj[g]) for g in A}
RIGHT,LEFT=108,135
hands={RIGHT:"R",LEFT:"L"}

def descendants(r,via):
    seen={r}; st=[via]; out=set()
    while st:
        z=st.pop()
        if z in seen: continue
        seen.add(z); out.add(z)
        for w in adj[z]:
            if w not in seen: st.append(w)
    return out
headset=descendants(104,159); legset=descendants(104,103)

ann={}  # id -> dict
def put(i,name,conf,note=""):
    ann[i]=dict(id=i,name=name,confidence=conf,note=note,pos=pos[i])

# ---- chest / spine / arms ----
put(104,"Chest / upper-spine (arms+neck+spine junction)","certain","Graph hub where both arms, head and spine meet.")
# arm chains chest->wrist
def label_arm(hub,side):
    # path chest(104)->...->wrist
    parent={104:None}; dq=collections.deque([104])
    while dq:
        x=dq.popleft()
        for y in adj[x]:
            if y not in parent: parent[y]=x; dq.append(y)
    path=[hub]; 
    while parent[path[-1]] is not None: path.append(parent[path[-1]])
    path=path[::-1]  # 104 ... hub
    # path like [104, s, e, f, wrist]
    names=["chest","shoulder","elbow","forearm","wrist"]
    n=len(path)
    for k,node in enumerate(path):
        if node==104: continue
        # position from end: wrist is last
        from_end=n-1-k
        if from_end==0: nm,conf=f"{side} wrist",("certain","likely")  # role certain, side likely
        elif from_end==1: nm,conf=f"{side} forearm/low-arm",("likely",)
        elif from_end==2: nm,conf=f"{side} elbow",("likely",)
        elif from_end==3: nm,conf=f"{side} shoulder/upper-arm",("likely",)
        else: nm,conf=f"{side} arm joint",("likely",)
        if node in (RIGHT,LEFT):
            put(node, f"{side} WRIST", "certain", "Degree-5 hub with 5 finger chains — wrist is certain; L/R side is inferred (likely).")
        else:
            put(node, nm, "likely", "Along arm chain by hop-distance from chest.")
label_arm(RIGHT,"Right"); label_arm(LEFT,"Left")

# ---- hands: fingers ----
def label_hand(hub,side):
    hn=hand_nodes(hub,adj)
    # hop distance from wrist within hand
    hop={hub:0}; dq=collections.deque([hub])
    par={hub:None}
    while dq:
        x=dq.popleft()
        for y in adj[x]:
            if y in hn and y not in hop: hop[y]=hop[x]+1; par[y]=x; dq.append(y)
    tips=[g for g in hn if deg[g]==1]
    # build finger chains: from each tip back to wrist
    fingers=[]
    for t in tips:
        chain=[t]; 
        while par[chain[-1]] not in (hub,None): chain.append(par[chain[-1]])
        chain=chain[::-1]  # mcp..tip (excludes wrist)
        fingers.append(chain)
    # order fingers by knuckle position; identify thumb = most abducted (largest angle of wrist->mcp vs mean)
    W=np.array(pos[hub])
    mcps=[np.array(pos[f[0]]) for f in fingers]
    dirs=[(m-W)/ (np.linalg.norm(m-W)+1e-9) for m in mcps]
    mean=sum(dirs)/len(dirs); mean/=np.linalg.norm(mean)
    angs=[math.degrees(math.acos(max(-1,min(1,np.dot(d,mean))))) for d in dirs]
    thumb_i=int(np.argmax(angs))
    # order the remaining 4 across knuckle line (project on axis perpendicular)
    order=sorted(range(len(fingers)), key=lambda i: pos[fingers[i][0]][2])  # by z
    fingnames=["thumb?","index?","middle?","ring?","pinky?"]
    # assign: thumb is thumb_i; others in order
    others=[i for i in order if i!=thumb_i]
    name_map={thumb_i:"thumb?"}
    for k,i in enumerate(others): name_map[i]=["index?","middle?","ring?","pinky?"][k]
    jointlevel=["knuckle (MCP)","mid (PIP)","upper (DIP)","tip"]
    for fi,chain in enumerate(fingers):
        fn=name_map[fi]
        L=len(chain)
        for k,node in enumerate(chain):
            # level from tip
            from_tip=L-1-k
            if from_tip==0: lvl="fingertip"
            elif k==0: lvl="knuckle (MCP)"
            else: lvl=f"finger joint {k+1}"
            role_conf="certain"  # joint position within finger is certain
            put(node, f"{side} {fn} {lvl}", "uncertain",
                f"Finger STRUCTURE certain (this is a {('fingertip' if from_tip==0 else 'knuckle' if k==0 else 'mid-finger joint')}); WHICH finger ({fn}) is a best guess.")
    # palm/metacarpal junctions (hop1 nodes with degree>=3 inside hand that are shared)
    for g in hn:
        if g==hub: continue
        if deg[g]>=3 and g not in ann:
            put(g,f"{side} palm/metacarpal","likely","Internal palm branch node.")
label_hand(RIGHT,"Right"); label_hand(LEFT,"Left")

# ---- head / face ----
put(159,"Neck / head base","certain","Branch from chest toward the head cluster.")
hc=[g for g in headset if g!=159]
# face leaves
faceleaves=[g for g in hc if deg[g]==1]
for g in hc:
    if g in ann: continue
    if deg[g]==1:
        put(g,"Face feature (eye/ear/nose/jaw?)","uncertain","One of the facial landmarks; specific identity not resolved.")
    else:
        put(g,"Head/skull joint","likely","Interior head node.")

# ---- spine / pelvis / legs ----
legleaves=[g for g in legset if deg[g]==1]
for g in legset:
    if g in ann: continue
    if deg[g]==1:
        put(g,"Foot/toe/heel? (leg extremity)","uncertain","Leg extremity; specific identity not resolved.")
    elif deg[g]>=3:
        put(g,"Pelvis / hip junction","likely","Branch point toward the two legs.")
    else:
        put(g,"Spine / leg joint","likely","Along spine or leg chain.")

# any leftover
for g in A:
    if g not in ann:
        put(g,"Unlabeled joint","uncertain","Not classified by topology pass.")

# summary counts
from collections import Counter
cc=Counter(a["confidence"] for a in ann.values())
print("nodes annotated:",len(ann),"of",len(A))
print("confidence breakdown:",dict(cc))

# save annotation keyed by joint id with positions for BOTH grips
B_j,B_b=load("/tmp/grip3.json")
Bc,Bpos,Bgroups,Bedges=reconstruct(B_j,B_b)
out=dict(
  annotations={str(k):dict(name=v["name"],confidence=v["confidence"],note=v["note"]) for k,v in ann.items()},
  gripA_pos={str(k):pos[k] for k in A},
  gripB_pos={str(k):Bpos[k] for k in Bc},
)
json.dump(out, open("/tmp/joint_annotations.json","w"), indent=0)
print("wrote /tmp/joint_annotations.json")
