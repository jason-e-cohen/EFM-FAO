import json, voi2, evpi
rows=[]
for cb in [0.03,0.10]:
    for N in [600,1000,2000,4000]:
        E=evpi.evpi(N,class_band=cb)['EVPI_U']
        best=None
        for D in [4,8]:
            for K in [1,2]:
                r=voi2.voi(N,D=D,K=K,class_band=cb)
                net=r['EVSI']-r['cost_at_zero']-r['ops']
                r['net0']=net
                if best is None or net>best['net0']: best=r
        old_mde3=round(54/ (0.4*N*3)**0.5,2)
        rows.append(dict(band=cb,N=N,class_sq=best['class_sq'],EVPI=E,bestD=best['D'],bestK=best['K'],se=best['se'],EVSI=best['EVSI'],cost=best['cost_at_zero'],ops=best['ops'],net=best['net0'],ratio=round(best['EVSI']/(best['cost_at_zero']+best['ops']),2),old_mde_3cyc=old_mde3,old_verdict='Recommend' if old_mde3<=2.3 else 'Optional/Not'))
for r in rows: print(json.dumps(r))
