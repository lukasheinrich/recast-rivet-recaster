import time
from celery import Celery,task

BROKERURL = 'lheinric-recast-hype'

CELERY_RESULT_BACKEND = 'redis://{}:6379/0'.format(BROKERURL)

app = Celery('tasks', backend='redis://{}'.format(BROKERURL), broker='redis://{}'.format(BROKERURL))


import subprocess
import glob
import jinja2
import yoda
import os
import shutil

import redis
import emitter
import zipfile

red = redis.StrictRedis(host = BROKERURL, db = 0)
io  = emitter.Emitter({'client': red})

import requests
def download_file(url,download_dir):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    download_path = '{}/{}'.format(download_dir,local_filename)
    with open(download_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return download_path    

@task
def postresults(jobguid,requestId,parameter_point):
  workdir = 'workdirs/{}'.format(jobguid)
  yodafile = '{}/Rivet.yoda'.format(workdir)
  resultdir = 'rivet_results/{}/{}'.format(requestId,parameter_point)
  
  if(os.path.exists(resultdir)):
    shutil.rmtree(resultdir)
    
  os.makedirs(resultdir)  
  shutil.copytree('{}/plots'.format(workdir),'{}/plots'.format(resultdir))
  shutil.copyfile('{}/Rivet.yoda'.format(workdir),'{}/Rivet.yoda'.format(resultdir))
  
  # also copy to server
  # subprocess.call('''ssh localhost "mkdir -p /Users/lukas/Code/atlas/recast/recast-frontend-prototype/rivet_results/{}"'''.format(requestId),shell = True)
  subprocess.call('''mkdir -p /Users/lukas/Code/atlas/recast/recast-frontend-prototype/rivet_results/{}'''.format(requestId),shell = True)

  subprocess.call(['cp', '-r', resultdir,'/Users/lukas/Code/atlas/recast/recast-frontend-prototype/rivet_results/{}/{}'.format(requestId,parameter_point)])
  
  io.Of('/monitor').In(str(jobguid)).Emit('results_done')
  return requestId

@task
def rivet(jobguid,rivetanalysis):
  workdir = 'workdirs/{}'.format(jobguid)
  hepmcfiles = glob.glob('{}/*.hepmc'.format(workdir))


  print "running rivet analysis: {}".format(rivetanalysis) 
  # raise NotImplementedError
  if not hepmcfiles: raise IOError

  yodafile = '{}/Rivet.yoda'.format(workdir)
  plotdir = '{}/plots'.format(workdir)
  analysisdir = os.path.abspath('../implementation/rivet')
  subprocess.call(['rivet','-a',rivetanalysis,'-H',yodafile]+hepmcfiles)
  subprocess.call(['rivet-mkhtml','-c','../implementation/rivet/DMHiggsFiducial.plot','-o',plotdir,yodafile])
  io.Of('/monitor').In(str(jobguid)).Emit('rivet_done')
  
  return jobguid
  
@task
def pythia(jobguid):
  workdir = 'workdirs/{}'.format(jobguid)

  fileglob = "{}/inputs/*.events".format(workdir)
  print "looking for files: {}".format(fileglob)
  eventfiles = glob.glob("{}/inputs/*.events".format(workdir))
  
  print 'found {} event files'.format(len(eventfiles))
  
  env = jinja2.Environment(undefined=jinja2.StrictUndefined)


  if not eventfiles:
    print 'no event files found'
    raise IOError

  for file in eventfiles:
    absinputfname = os.path.abspath(file)
    basefname = os.path.basename(absinputfname)

    steeringfname = '{}/{}.steering'.format(workdir,basefname)
    outfname = workdir+'/'+'.'.join(basefname.split('.')[0:-1]+['hepmc'])

    with open('../implementation/pythiasteering.tplt') as steeringfile:
      template = env.from_string(steeringfile.read())
      with open(steeringfname,'w+') as output:
        output.write(template.render({'INPUTLHEF':absinputfname}))

    subprocess.call(['../implementation/pythia/pythiarun',steeringfname,outfname])

  io.Of('/monitor').In(str(jobguid)).Emit('pythia_done')
  
  return jobguid

import time

@task
def prepare_job(jobguid,jobinfo):
  print "job info is {}".format(jobinfo)
  print "job uuid is {}".format(jobguid)
  workdir = 'workdirs/{}'.format(jobguid)
  
  input_url = 'http://localhost:5000/rivet/inputfile/{}/{}/{}'.format(jobinfo['requestId'],jobinfo['pointcount'],jobinfo['file'])
  print "downloading file : {}".format(input_url) 
  filepath = download_file(input_url,workdir)

  print "downloaded file to: {}".format(filepath)

  with zipfile.ZipFile(filepath)as f:
    f.extractall('{}/inputs'.format(workdir))

  return jobguid

@task
def prepare_workdir(fileguid,jobguid):
  uploaddir = 'uploads/{}'.format(fileguid)
  workdir = 'workdirs/{}'.format(jobguid)
  
  os.makedirs(workdir)
  # os.symlink(os.path.abspath(uploaddir),workdir+'/inputs')
  io.Of('/monitor').Emit('pubsubmsg','prepared workdirectory...')

  print "emitting to room"
  io.Of('/monitor').In(str(jobguid)).Emit('workdir_done','prepared workdirectory...')

  return jobguid
  

import recastapi.request
import json
import uuid

def get_chain(jobinfo):

  jobguid = uuid.uuid1()

  analysis_queue = 'rivet_queue'  

  request_uuid = jobinfo['requestId']
  point = jobinfo['pointcount']
  rivetanalysis = jobinfo['rivetanalysis']

  chain = (
            prepare_workdir.subtask((request_uuid,jobguid),queue=analysis_queue) |
            prepare_job.subtask((jobinfo,),queue=analysis_queue)                 |
            pythia.subtask(queue=analysis_queue)                                 |
            rivet.subtask((rivetanalysis,),queue=analysis_queue)                                  |
            postresults.subtask((request_uuid,point),queue=analysis_queue) 
          )
  return (jobguid,chain)  
