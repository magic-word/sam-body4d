import math, collections
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
A,posA,adjA=build("/tmp/grip2.json")
deg={g:len(adjA[g]) for g in A}

# characterize neighbors of chest hub 104
print("Node 104 pos",[round(x,3) for x in posA[104]],"deg",deg[104])
for nb in adjA[104]:
    st=subtree(104,nb,adjA)
    leaves=[n for n in st if deg[n]==1]
    print(f"  branch via {nb}: size={len(st)} leaves={len(leaves)} pos_nb={[round(x,3) for x in posA[nb]]}")

# Identify all leaves and their positions to find head(face)/feet/finger tips
leaves=[g for g in A if deg[g]==1]
print("\nAll leaves:")
for g in sorted(leaves):
    print(f"  leaf {g} pos={[round(x,3) for x in posA[g]]}")

# bounding box of whole skeleton
P=np.array([posA[g] for g in A])
print("\nBBox min",[round(x,3) for x in P.min(0)],"max",[round(x,3) for x in P.max(0)])
print("Centroid",[round(x,3) for x in P.mean(0)])
