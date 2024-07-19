from core import atmos

def rsr_hyper(waves, widths, step = 0.25, nm = True):

    nbands = len(waves)
    rsr = {}
    for b in range(nbands):
        wave, resp = atmos.shared.gauss_response(waves[b], widths[b], step=step)
        rsr[b] = {'wave':wave, 'response': resp}
        if nm: rsr[b]['wave']/=1000
    return(rsr)
