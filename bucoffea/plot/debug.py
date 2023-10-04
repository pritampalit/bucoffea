#!/usr/bin/env python

from matplotlib import pyplot as plt
import os
from coffea import hist
import numpy as np

def debug_plot_output(output, region='inclusive', outdir='out', logscaley=True):
    """Dump all histograms as PDF."""
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    for name in output.keys():
        if name.startswith("_"):
            continue
        # if any([x in name for x in ['sumw','cutflow','selected_events','kinematics','weights']]):
        #     continue
        try:
            if np.sum(output[name].values().values()) == 0:
                continue
        except:
            continue

        if ((region == "sr_prompt") & (name == "tau_pt")) :
            print(f'region', region)
            print(f'name', name)
        try:
            h = output[name].integrate("region",region)
            #print("h : ", h)
            #assert(h)
            #print("h is asserted")
        except:
            continue
        ##print(name)
        try:
            #print("anything")
            #print("h type : ",type(h))
            ##x, y = h.to_numpy
            #print("x : ", x)
            #h = h.compute()
            #print(h)
            #hmean = h.accumulators.Sum()
            #print("anything2")
            #print("mean : ", hmean)
            #print("anything 3")
            
            fig, ax = plt.subplots(1, 1, figsize=(7,5))
            '''
            fig, ax, _ = hist.plot1d(
                h,
                overlay='dataset',
                overflow='all',
                clear = False
                )
            '''
            hist.plot1d(
                h,
                overlay='dataset',
                overflow='all',
                clear = False
            )

            #assert(fig)
            print("h is plotted")
        except:
            continue
        fig.suptitle(f'{region}, {name}')
        # ax.set_xscale('log')
        if logscaley:
            ax.set_yscale('log')
            ax.set_ylim(0.1, 1e8)
        else:
            ax.set_ylim(0.1, 1e3)
        fig.savefig(os.path.join(outdir, f"{region}_{name}.pdf"))
        print("figure saved successfully")
        plt.close(fig)
