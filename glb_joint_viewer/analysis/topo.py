import json, math
exec(open("/tmp/recon2.py").read().split("for tag,fn")[0])  # reuse functions

def subtree(hub, start, adj):
    # nodes reachable from `start` without going back through hub
    seen={hub}; st=[start]; out=[]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); out.append(x)
        for y in adj[x]:
            if y not in seen: st.append(y)
    return out

def depth_from(hub,start,adj):
    # longest path length (in hops) from start away from hub
    best=[0]
    def dfs(x,parent,d):
        best[0]=max(best[0],d)
        for y in adj[x]:
            if y!=parent and y!=hub: dfs(y,x,d+1)
    dfs(start,hub,1)
    return best[0]

for tag,fn in [("gripA","/tmp/grip2.json"),("gripB","/tmp/grip3.json")]:
    joints,bones=load(fn)
    canon,pos,groups,edges,adj=reconstruct(joints,bones)
    deg={g:len(adj[g]) for g in canon}
    print(f"\n========== {tag} ==========")
    for hub in [108,135]:
        print(f"\n-- wrist hub {hub} pos={[round(x,3) for x in pos[hub]]} deg={deg[hub]} --")
        branches=[]
        for nb in adj[hub]:
            st=subtree(hub,nb,adj)
            dp=depth_from(hub,nb,adj)
            branches.append((len(st),dp,nb,st))
        branches.sort(reverse=True)
        for sz,dp,nb,st in branches:
            kind="ARM/body" if sz>10 else "finger"
            print(f"   branch via {nb}: size={sz} depth={dp} [{kind}]  nodes={sorted(st) if sz<=8 else '...'+str(len(st))+' nodes'}")
