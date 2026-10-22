import numpy as np
def brier_score_loss(y,p): y=np.asarray(y,float); p=np.asarray(p,float); return float(np.mean((y-p)**2))
def roc_auc_score(y,p):
    y=np.asarray(y); p=np.asarray(p); from scipy.stats import rankdata
    r=rankdata(p); n1=(y==1).sum(); n0=len(y)-n1
    return float((r[y==1].sum()-n1*(n1+1)/2)/(n1*n0))
