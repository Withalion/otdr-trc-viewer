import sys,struct,os,math
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tree import load
C=299792458.0
def v(o,k):
    t,d=o[k]
    if t==1 and len(d)==4: return struct.unpack('<i',d)[0]
    if t==3 and len(d)==8: return struct.unpack('<d',d)[0]
    if t==4: return d.decode('utf-16le').rstrip('\0')
    return d
def traces(fn):
    o=load(fn); base='/OtdrData/Fibers/Fiber0/Traces/'
    n=v(o,base+'Count'); res=[]
    for i in range(n):
        p=f'{base}Trace{i}/'
        T=dict(wl=v(o,p+'Wavelength')*1e9,pulse=v(o,p+'Pulse')*1e9,range=v(o,p+'Range'),
               dur=v(o,p+'Duration'),date=v(o,p+'Date'),dt=v(o,p+'SamplingPeriod'),
               ior=v(o,p+'FiberSectionCharacteristics/Section0/Ior'),
               rbs=v(o,p+'FiberSectionCharacteristics/Section0/Rbs'),
               avg=v(o,p+'AcquisitionDatas/AcquisitionData0/NumberOfAverages'),
               model=v(o,p+'ModuleInformation/ModelName'))
        T['y']=np.frombuffer(o[p+'RawSamples'][1],dtype='<u2')/1000.0
        T['dz']=C*T['dt']/(2*T['ior'])
        ev=[];ne=v(o,p+'EventTable/Count')
        for j in range(ne):
            q=f'{p}EventTable/Event{j}/'
            if q+'Type' in o:
                ev.append(dict(kind='event',pos=v(o,q+'Position'),type=v(o,q+'Type'),
                    loss=v(o,q+'Loss') if q+'Loss' in o else float('nan'),
                    refl=v(o,q+'Reflectance'),level=v(o,q+'CurveLevel')))
            else:
                L=v(o,q+'Length');Ls=v(o,q+'Loss')
                ev.append(dict(kind='section',pos=v(o,q+'Position'),length=L,loss=Ls,
                    att=Ls/L*1000 if L>0 else float('nan')))
        T['ev']=ev; res.append(T)
    return res
def f(x,fmt='{:.3f}'): return '—' if x is None or (isinstance(x,float) and math.isnan(x)) else fmt.format(x)
TYPES={2:'neodrazová',3:'odrazová'}
if __name__=="__main__":
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    md=[]
    for fn in sys.argv[2:]:
        name=os.path.basename(fn)
        ts=traces(fn)
        fig,ax=plt.subplots(figsize=(12,5.5))
        for T in ts:
            x=np.arange(len(T['y']))*T['dz']
            ax.plot(x,T['y'],lw=0.7,label=f"{T['wl']:.0f} nm")
            md.append(f"\n## {name} — {T['wl']:.0f} nm\n")
            md.append(f"Prístroj {T['model']}, dátum {T['date']}, impulz {T['pulse']:.0f} ns, rozsah {T['range']:.0f} m, "
                      f"IOR {T['ior']}, priemerovaní {T['avg']}, čas merania {T['dur']} s, krok vzorky {T['dz']:.3f} m\n")
            md.append("| # | Typ | Poloha [m] | Dĺžka úseku [m] | Strata [dB] | Merné tlmenie [dB/km] | Odrazivosť [dB] |")
            md.append("|---|---|---|---|---|---|---|")
            k=0
            for e in T['ev']:
                if e['kind']=='event':
                    k+=1
                    md.append(f"| {k} | {TYPES.get(e['type'],e['type'])} | {e['pos']:.2f} | | {f(e['loss'])} | | {f(e['refl'],'{:.1f}')} |")
                else:
                    md.append(f"| | úsek vlákna | {e['pos']:.2f} | {e['length']:.2f} | {f(e['loss'])} | {f(e['att'])} | |")
            evs=[e for e in T['ev'] if e['kind']=='event']
            secs=[e for e in T['ev'] if e['kind']=='section']
            tot=sum(e['loss'] for e in T['ev'] if not math.isnan(e['loss']) and not (e['kind']=='event' and e is evs[-1]))
            md.append(f"\nKoniec vlákna: {evs[-1]['pos']:.2f} m; súčet strát udalostí a úsekov (bez koncovej): {tot:.3f} dB\n")
            for e in evs:
                ax.axvline(e['pos'],color='grey',lw=0.4,ls=':')
        ax.set_xlabel('Vzdialenosť [m]');ax.set_ylabel('Úroveň [dB]')
        endpos=max(e['pos'] for T in ts for e in T['ev'])
        ax.set_xlim(-10,endpos*1.08+20);ax.grid(alpha=.3);ax.legend()
        ax.set_title(name)
        fig.tight_layout();png=os.path.join(out,name.replace('.trc','.png'));fig.savefig(png,dpi=130);plt.close(fig)
        md.append(f"Graf: {png}\n")
    open(os.path.join(out,'udalosti.md'),'w').write('\n'.join(md))
    print('\n'.join(md))
