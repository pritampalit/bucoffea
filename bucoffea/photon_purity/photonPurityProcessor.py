import os
import re

import coffea.processor as processor
import numpy as np
from awkward import JaggedArray
from coffea import hist
from coffea.analysis_objects import JaggedCandidateArray

from bucoffea.helpers.dataset import (extract_year, is_lo_w, is_lo_z, is_nlo_w,
                                      is_nlo_z, is_data)
from bucoffea.helpers.gen import find_gen_dilepton, setup_gen_candidates, setup_dressed_gen_candidates, isnu, islep, fill_gen_v_info
from bucoffea.helpers import (
                              weight_shape,
                              object_overlap
                             )
from bucoffea.helpers import min_dphi_jet_met

Hist = hist.Hist
Bin = hist.Bin
Cat = hist.Cat


# VID map definition
# 
# 0  1  MinPtCut
# 2  3  PhoSCEtaMultiRangeCut
# 4  5  PhoSingleTowerHadOverEmCut
# 6  7  PhoFull5x5SigmaIEtaIEtaCut
# 8  9  PhoAnyPFIsoWithEACut
# 10 11 PhoAnyPFIsoWithEAAndQuadScalingCut
# 12 13 PhoAnyPFIsoWithEACut

def medium_id_no_sieie(photons):
    # VID bitmask encodes 7 cuts with each two bits.
    # for each cut, the more significant bit indicates
    # whether the medium WP of the cut is passed.
    #
    # To get medium or tighter, require every second bit:
    #   --> 1X-1X-1X-1X-1X-1X-1X
    #   where X = 0 or 1 (we dont care)
    #
    # To ignore the sieie requirement, also ignore bit 7
    #   --> 1X-1X-1X-XX-1X-1X-1X
    # 
    # We are going to check the logical AND of the mask
    # and the bitmap, so set all X to 0
    mask = int('10101000101010',2)
    return (photons.vid & mask) == mask

def medium_id_no_sieie_inv_iso(photons):
    # Same as medium_id_no_sieie, but in first step,
    # ignore isolation bits
    # --> XX-XX-XX-XX-1X-1X-1X
    mask1 = int('00000000101010',2)
    medium_id_no_iso = (photons.vid & mask1) == mask1

    # In second step, actually *veto* the isolation bits
    # only want to veto medium iso WP, though, so only
    # the more significant bit of the iso is set to 0
    # --> 0X-0X-0X-XX-1X-1X-1X
    #
    # NB: We are going to OR the mask with the bitmap
    # so set all X to 1
    mask2 = int('01010111111111',2)
    inv_iso = (photons.vid | mask2) == mask2

    return medium_id_no_iso & inv_iso


def setup_photons(df):
    # Setup photons
    photons = JaggedCandidateArray.candidatesfromcounts(
        df['nPhoton'],
        pt=df['Photon_pt'],
        eta=df['Photon_eta'],
        abseta=np.abs(df['Photon_eta']),
        phi=df['Photon_phi'],
        mass=0*df['Photon_pt'],
        mediumId=(df['Photon_cutBasedBitmap']>=2) & df['Photon_electronVeto'],
        r9=df['Photon_r9'],
        barrel=np.abs(df['Photon_eta']) < 1.479,
        vid=df['Photon_vidNestedWPBitmap'],
        eleveto= df['Photon_electronVeto'],
        sieie= df['Photon_sieie'],
    )

    photons = photons[ (photons.pt > 200) & photons.barrel]
    return photons

def setup_jets(df):
    ak4 = JaggedCandidateArray.candidatesfromcounts(
        df['nJet'],
        pt=df[f'Jet_pt'],
        eta=df['Jet_eta'],
        abseta=np.abs(df['Jet_eta']),
        phi=df['Jet_phi'],
        mass=np.zeros_like(df['Jet_pt']),
        looseId=(df['Jet_jetId']&4) == 4, # bitmask: 1 = loose, 2 = tight, 3 = tight + lep veto
        tightId=(df['Jet_jetId']&4) == 4, # bitmask: 1 = loose, 2 = tight, 3 = tight + lep veto
        nhf=df['Jet_neHEF'],
        chf=df['Jet_chHEF'],
        ptraw=df['Jet_pt']*(1-df['Jet_rawFactor']),
        nconst=df['Jet_nConstituents']
    )
    return ak4

class photonPurityProcessor(processor.ProcessorABC):
    def __init__(self):

        # Histogram setup
        dataset_ax = Cat("dataset", "Primary dataset")

        sieie_ax = Bin("sieie", r"sieie", 100,0,0.02)
        pt_ax = Bin("sieie", r"sieie", 50, 200, 1200)
        cat_ax = Cat("cat", r"cat")

        items = {}
        items[f"sieie"] = Hist(
                               "Counts",
                               dataset_ax,
                               sieie_ax,
                               pt_ax,
                               cat_ax
                               )

        items['sumw'] = processor.defaultdict_accumulator(float)
        items['sumw2'] = processor.defaultdict_accumulator(float)

        self._accumulator = processor.dict_accumulator(items)

    @property
    def accumulator(self):
        return self._accumulator


    def process(self, df):
        output = self.accumulator.identity()
        dataset = df['dataset']
        photons = setup_photons(df)

        ak4 = setup_jets(df)
        ak4 = ak4[
                  object_overlap(ak4, photons) \
                  & (ak4.pt > 100) \
                  & (ak4.abseta < 2.4)
                  ]

        event_mask = (ak4.counts > 0) & df['HLT_Photon200']

        # Generator weight
        weights = processor.Weights(size=df.size, storeIndividual=True)

        if is_data(dataset):
            weights.add('gen', np.ones(df.size))
        else:
            weights.add('gen', df['Generator_weight'])

        photon_kinematics = (photons.pt > 200) & (photons.barrel)

        # Medium
        vals = photons[photon_kinematics & photons.mediumId].sieie[event_mask]
        pt = photons[photon_kinematics & photons.mediumId].pt[event_mask]
        output['sieie'].fill(
                             dataset=dataset,
                             cat='medium',
                             sieie=vals.flatten(),
                             pt=pt.flatten(),
                             weights=weight_shape(
                                                  vals,
                                                  weights.weight()[event_mask]
                                                  )
                            )

        # No Sieie
        vals = photons[photon_kinematics & medium_id_no_sieie(photons)].sieie[event_mask]
        pt = photons[photon_kinematics & medium_id_no_sieie(photons)].pt[event_mask]
        output['sieie'].fill(
                             dataset=dataset,
                             cat='medium_nosieie',
                             sieie=vals.flatten(),
                             pt=pt.flatten(),
                             weights=weight_shape(
                                                  vals,
                                                  weights.weight()[event_mask]
                                                  )
                            )

        # No Sieie, inverted isolation
        vals = photons[photon_kinematics & medium_id_no_sieie_inv_iso(photons)].sieie[event_mask]
        pt = photons[photon_kinematics & medium_id_no_sieie_inv_iso(photons)].pt[event_mask]
        output['sieie'].fill(
                             dataset=dataset,
                             cat='medium_nosieie_invertiso',
                             sieie=vals.flatten(),
                             pt=pt.flatten(),
                             weights=weight_shape(
                                                  vals,
                                                  weights.weight()[event_mask]
                                                  )
                            )

        # Keep track of weight sum
        if not is_data(dataset):
            output['sumw'][dataset] +=  df['genEventSumw']
            output['sumw2'][dataset] +=  df['genEventSumw2']
        return output

    def postprocess(self, accumulator):
        return accumulator
