from flask import Blueprint, render_template, jsonify, request, send_from_directory
blueprint = Blueprint('general_rivet', __name__, template_folder='general_rivet_templates')

RECAST_ANALYSIS_ID = 'general_rivet'
RECASTSTORAGEPATH = '/home/analysis/recast/recaststorage'

import json
import requests
import requests
import os
from zipfile import ZipFile
import glob

@blueprint.route('/t/<requestId>/<parameter_pt>')
def result_view(requestId,parameter_pt):
  analysis = '*'

  analyses = filter(os.path.isdir,glob.glob('{}/results/{}/{}/plots/*'.format(RECASTSTORAGEPATH,requestId,parameter_pt)))

  print analyses
  print ['{}/results/{}/{}/plots/{}/*.dat'.format(RECASTSTORAGEPATH,requestId,parameter_pt,a) for a in analyses]

  plotdict = {os.path.basename(a):[os.path.basename(p).rsplit('.',1)[0] for p in glob.glob('{}/*.dat'.format(a))] for a in analyses}

  print plotdict
  
  return render_template('general_rivet_result.html',analysisId = RECAST_ANALYSIS_ID,requestId=requestId,parameter_pt=parameter_pt,plotdict = plotdict)

@blueprint.route('/plot/<requestId>/<parameter_pt>/<path:file>')
def plot_server(requestId,parameter_pt,file):
  filepath = '{}/results/{}/{}/plots/{}'.format(RECASTSTORAGEPATH,requestId,parameter_pt,file)
  print filepath
  return send_from_directory(os.path.dirname(filepath),os.path.basename(filepath))
  


