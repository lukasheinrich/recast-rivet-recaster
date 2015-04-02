import time
from celery import shared_task

import subprocess
import glob
import jinja2
import yoda
import os
import shutil

import redis
import emitter
import zipfile

from recastbackend.backendtasks import socketlog

@shared_task
def rivet(jobguid,rivetanalysis):
  workdir = 'workdirs/{}'.format(jobguid)
  hepmcfiles = glob.glob('{}/*.hepmc'.format(workdir))


  print "running rivet analysis: {}".format(rivetanalysis) 
  # raise NotImplementedError
  if not hepmcfiles: raise IOError

  yodafile = '{}/Rivet.yoda'.format(workdir)
  logfile = '{}/Rivet.log'.format(workdir)

  plotdir = '{}/plots'.format(workdir)

  with open(logfile,'w') as log:
    subprocess.call(['rivet','-a',rivetanalysis,'-H',yodafile]+hepmcfiles,stdout = log)

  subprocess.call(['rivet-mkhtml','-o',plotdir,yodafile])

  socketlog(jobguid,'ran rivet')
  
  return jobguid
  
@shared_task
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

    with open('pythiasteering.tplt') as steeringfile:
      template = env.from_string(steeringfile.read())
      with open(steeringfname,'w+') as output:
        output.write(template.render({'INPUTLHEF':absinputfname}))

    subprocess.call(['pythia/pythiarun',steeringfname,outfname])
    
    #sanity check that file is non-empty
    assert os.stat(outfname).st_size > 0 

  socketlog(jobguid,'ran pythia')
  return jobguid

def resultlist():
  return ['plots','Rivet.yoda','Rivet.log']

def get_chain(queuename,rivetanalysis):
  chain = (
            pythia.subtask(queue=queuename)                                 |
            rivet.subtask((rivetanalysis,),queue=queuename)
          )
  return chain  
