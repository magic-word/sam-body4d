import json, math
from PIL import Image, ImageDraw, ImageFont

def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf","/System/Library/Fonts/Helvetica.ttc"]:
        try: return ImageFont.truetype(p,sz)
        except: pass
    return ImageFont.load_default()

F=font(26); FB=font(30); FT=font(40); FL=font(24)

def col255(c): return tuple(int(round(x*255)) for x in c)

def draw_hand(proj, side, grip, outpath):
    W,H=proj["W"],proj["H"]
    img=Image.open(proj["path"]).convert("RGB")
    d=ImageDraw.Draw(img)
    colors=proj["colors"]
    nd={n["id"]:n for n in proj["nodes"]}
    def fcol(fid): return col255(colors.get(nd[fid]["finger"],colors["?"]))
    # bones
    for a,b in proj["edges"]:
        if a in nd and b in nd:
            ca=nd[a]; cb=nd[b]
            # color = child's finger (the one further from wrist => deeper level)
            child = b if nd[b]["level"]!="wrist" else a
            d.line([(ca["px"],ca["py"]),(cb["px"],cb["py"])], fill=(210,210,215), width=4)
    # node markers
    for n in proj["nodes"]:
        c=fcol(n["id"]); x,y=n["px"],n["py"]
        r=11 if n["finger"]=="wrist" else 8
        d.ellipse([x-r,y-r,x+r,y+r], fill=c, outline=(0,0,0), width=2)
    # labels stacked on margins
    nodes=sorted(proj["nodes"], key=lambda n:n["py"])
    left=[n for n in nodes if n["px"]<W/2]
    right=[n for n in nodes if n["px"]>=W/2]
    def place(group, xanchor, align):
        if not group: return
        n=len(group); top=120; bot=H-60; step=(bot-top)/max(1,n-1) if n>1 else 0
        for i,node in enumerate(group):
            ly=top+i*step
            c=fcol(node["id"])
            fn=node["finger"]; lv=node["level"]
            if fn=="wrist": txt=f'{node["id"]}  WRIST'
            elif fn=="palm": txt=f'{node["id"]}  palm/metacarpal'
            else: txt=f'{node["id"]}  {fn}? · {lv}'
            tb=d.textbbox((0,0),txt,font=F); tw=tb[2]-tb[0]; th=tb[3]-tb[1]
            if align=="right": lx=xanchor-tw
            else: lx=xanchor
            # leader line
            d.line([(node["px"],node["py"]),(lx+(tw if align=='right' else 0), ly+th/2)],
                   fill=c, width=2)
            d.rectangle([lx-6,ly-4,lx+tw+6,ly+th+8], fill=(18,18,20), outline=c, width=2)
            d.text((lx,ly),txt,font=F,fill=(255,255,255))
    place(left, 24, "left")
    place(right, W-24, "right")
    # title
    d.rectangle([0,0,W,70], fill=(18,18,20))
    d.text((24,14), f"{side.upper()} HAND  —  grip {grip}   (finger names are BEST-GUESS — please validate)", font=FB, fill=(255,255,255))
    # legend
    lx=W//2-260; ly=H-46
    d.rectangle([lx-10,ly-8,lx+560,ly+34], fill=(18,18,20))
    order=["thumb","index","middle","ring","pinky"]
    xx=lx
    for fn in order:
        c=col255(colors[fn]); d.ellipse([xx,ly+4,xx+18,ly+22],fill=c,outline=(0,0,0))
        d.text((xx+24,ly), fn, font=FL, fill=(230,230,230)); xx+=110
    img.save(outpath)
    return outpath

P=json.load(open("/tmp/hand_proj_A.json"))
draw_hand(P["Right"],"Right","A","/tmp/annot_right_A.png")
draw_hand(P["Left"],"Left","A","/tmp/annot_left_A.png")
print("saved /tmp/annot_right_A.png /tmp/annot_left_A.png")
