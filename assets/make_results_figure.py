import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"Inter","font.size":11,"svg.fonttype":"path"})
models=["Gemma 4 31B","TahrirchiBERT","Goldfish Latin (full)"]
data={"Current Latin":[97.3,98.7,96.7],"Cyrillic":[98.1,76.8,91.7],"Reformed Latin":[90.5,87.3,None]}
colors=["#3d3d3d","#8c8c8c","#cfcfcf"]
fig,ax=plt.subplots(figsize=(8,3.1))
h=0.24
for i,(k,v) in enumerate(data.items()):
    for j,x in enumerate(v):
        y=j+(i-1)*h
        if x is None:
            ax.text(50.6,y,"not scored",va="center",fontsize=9,color="#8c959f"); continue
        ax.barh(y,x-50,left=50,height=h*0.9,color=colors[i],label=k if j==0 else None)
        ax.text(x+0.4,y,f"{x:.1f}",va="center",fontsize=9,color="#24292f")
ax.set_yticks(range(3)); ax.set_yticklabels(models); ax.set_ylim(2.45,-0.45)
ax.set_xlim(50,102); ax.set_xticks([50,60,70,80,90,100])
ax.set_xlabel("Accuracy (%) on 2,400 pairs  ·  chance = 50",color="#57606a",fontsize=10)
for s in ["top","right","left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#d0d7de"); ax.tick_params(axis="y",length=0); ax.tick_params(axis="x",colors="#57606a")
ax.xaxis.grid(True,color="#eaeef2"); ax.set_axisbelow(True)
ax.legend(loc="lower center",bbox_to_anchor=(0.4,1.0),ncol=3,frameon=False,fontsize=10,handlelength=1,columnspacing=1.5)
fig.tight_layout()
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),"results.svg"),facecolor="white")
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),"results.png"),dpi=200,facecolor="white")
