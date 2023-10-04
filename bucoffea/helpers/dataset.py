import re

from bucoffea.execute.dataset_definitions import short_name

def is_lo_znunu(dataset):
    return bool(re.match(r'Z(\d*)Jet.*(mg|MLM|madgraph).*', dataset))

def is_lo_z(dataset):
    return bool(re.match(r'(DY|Z)(\d*)Jet.*(mg|MLM|madgraph).*', dataset))

def is_lo_z_ewk(dataset):
    return bool(re.match(r'EWKZ2Jets_ZTo.', dataset))

def is_lo_w(dataset):
    return bool(re.match(r'W(\d*)Jet.*(mg|MLM).*', dataset))

def is_lo_w_ewk(dataset):
    return bool(re.match(r'EWKW(Minus|Plus)2Jets_WToLNu.', dataset))

def is_lo_g(dataset):
    return bool(re.match(r'GJets.*HT.*', dataset))

def is_lo_g_ewk(dataset):
    return bool(re.match(r'GJets.*EWK.*', dataset))

def is_nlo_g(dataset):
    return bool(re.match(r'G(\d)*Jet.*(amc|NLO).*', dataset))

def is_nlo_g_ewk(dataset):
    return bool(re.match(r'AJJ.*amc.*', dataset))

def is_nlo_z(dataset):
    return bool(re.match(r'(DY|Z)(\d*)Jet.*FXFX.*', dataset))

def is_nlo_w(dataset):
    return bool(re.match(r'W(\d*)Jet.*FXFX.*', dataset))

def has_v_jet(dataset):
    return bool(re.match(r'(WW|WZ|ZZ|TTJets|TTToHadronic|.*WToQQ|.*ZToQQ).*', dataset))

def is_data(dataset):
    tags = ['EGamma','MET','SingleElectron','SingleMuon','SinglePhoton','JetHT']
    if any([dataset.startswith(itag) for itag in tags ]):
        return True
    if re.match('QCD_data_(\d)+',dataset):
        return True
    return False


def extract_year(dataset):
    for x in [6,7,8]:
        if f"201{x}" in dataset:
            return 2010+x
    raise RuntimeError("Could not determine dataset year")

def extract_year_run3(dataset):
    for x in [2,3]:
        #if (x==2): # implement the EE
        #    for y in ["preEE","postEE"]:
        if f"202{x}" in dataset:
            return 2020+x
    raise RuntimeError("Could not determine dataset year for Run3")


def rand_dataset_dict(keys, year):
    '''
    Creates a map of dataset names -> short dataset names for randomized parameter samples
    '''
    if year==2016:
        conditions = 'RunIISummer16'
    elif year==2017:
        conditions = 'RunIIFall17'
    elif year==2018:
        conditions = 'RunIIAutumn18'
    else:
        raise RuntimeError("Cannot recognize year: {year}")

    datasets = [x.replace("GenModel_","") for x in keys if "GenModel" in x]

    return {x : short_name(f"/{x}/{conditions}/NANOAODSIM") for x in datasets}
