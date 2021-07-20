import uproot
from coffea.nanoevents import NanoEventsFactory, BaseSchema, NanoAODSchema
#uproot.open.defaults["xrootd_handler"] = uproot.source.xrootd.MultithreadedXRootDSource
### https://uproot.readthedocs.io/en/latest/uproot.source.xrootd.html
uproot.open.defaults["xrootd_handler"] = uproot.source.xrootd.XRootDSource

import coffea.processor as processor
from processors import VBFHHggtautauProcessor
import job_utils

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

file_handler = logging.FileHandler('logs/example.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

samplelist = ["HH_ggTauTau", "VBF_HH_ggTauTau", "Data"]
#samplelist = ["Data"]
fileset = job_utils.make_fileset(samplelist, ["2016","2017","2018"], use_xrootd=True) 
#outdfname = "test_VBFyields_withdata.parquet" 
outpath = "/work/gallim/devel/HiggsDNA_studies/out"
jobtag = "test"

from dask_jobqueue import SLURMCluster
from dask.distributed import Client
#client = Client(memory_limit='2GB', n_workers=5, threads_per_worker=1)
#client = Client("tcp://169.228.130.37:12318")

localfiles = ["./processors.py", "./utils.py", "./data/samples_and_scale1fb_HHggTauTau.json"]
#for localfile in localfiles:
    #client.upload_file(localfile)

logger.debug(f"fileset: {fileset}")

def run(useNanoEvents):

    if useNanoEvents == True:

        file = uproot.open(fnames[1])
        events = NanoEventsFactory.from_root(
            file,
            entry_stop=10000,
            metadata={"dataset": "VBFHHggtautau"},
            schemaclass=NanoAODSchema,
        ).events()
        p = MyProcessor()
        out = p.process(events)
        return out, events

    else:


        with SLURMCluster(cores=2, memory="4G") as cluster:
            with Client(cluster) as client:
                cluster.scale(200)
                out = processor.run_uproot_job(
                    fileset,
                    treename = 'Events',
                    processor_instance = VBFHHggtautauProcessor(outpath, jobtag),
                    #executor=processor.futures_executor,
                    #executor_args={"schema": None, "workers": 3, "use_dataframes": True}, # our skim only works with None if we want to use selectedPhoton..
                    executor=processor.dask_executor,
                    executor_args={"schema": None, "client": client, "use_dataframes": True},
                    )

        #logger.debug(f"columns: {out.columns}")
        #logger.debug(f"head of df: {out.head()}")

        #import dask.dataframe as dd
        #dd.to_parquet(out, path="./outputs/test2_useNumbaForDr.parquet")
        #dd.to_parquet(out, path="./outputs/test2.parquet")
        #dd.to_parquet(out, path="./outputs/" + outdfname)

        #client.shutdown()

if __name__ == '__main__':
    run(False)
