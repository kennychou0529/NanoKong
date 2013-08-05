#!/usr/bin/python
# vim: ts=2 sw=2
# author: Penn Su
from gevent import monkey; monkey.patch_all()
import gevent
import tornado.ioloop
import tornado.web
import tornado.template as template
import os, sys, zipfile
import simplejson as json
import logging
import hashlib
from xml.dom.minidom import parse, parseString
from threading import Thread
import traceback
import time
import re
import StringIO
import shutil, errno
import datetime
from subprocess import Popen, PIPE, STDOUT

import wkpf.fakedata
import wkpf.wusignal
from wkpf.wkapplication import WuApplication
from wkpf.wkpf import *
from wkpf.wkpfcomm import *

from wkpf.globals import *
from configuration import *

import tornado.options
tornado.options.parse_command_line()
tornado.options.enable_pretty_logging()

IP = sys.argv[1] if len(sys.argv) >= 2 else '127.0.0.1'

#locationTree= None
landId = 100
node_infos = []

from make_js import make_main
from make_fbp import fbp_main
def import_wuXML():
	test = make_main()
	test.make()
	
def make_FBP():
	test_1 = fbp_main()
	test_1.make()	


# Helper functions
def setup_signal_handler_greenlet():
  logging.info('setting up signal handler')
  gevent.spawn(wusignal.signal_handler)
def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def copyAnything(src, dst):
  try:
    shutil.copytree(src, dst)
  except OSError as exc: # python >2.5
    if exc.errno == errno.ENOTDIR:
      shutil.copy(src, dst)
    else: raise

def getAppIndex(app_id):
  global applications
  # make sure it is not unicode
  app_id = app_id.encode('ascii','ignore')
  for index, app in enumerate(applications):
    if app.id == app_id:
      return index
  return None

def delete_application(i):
  global applications
  try:
    shutil.rmtree(applications[i].dir)
    #os.system('rm -rf ' + applications[i].dir)
    applications.pop(i)
    return True
  except Exception as e:
    logging.error(e)
    return False

def load_app_from_dir(dir):
  app = WuApplication(dir=dir)
  app.loadConfig()
  return app

def update_applications():
  global applications
  logging.info('updating applications:')

  application_basenames = [os.path.basename(app.dir) for app in applications]

  for dirname in os.listdir(APP_DIR):
    app_dir = os.path.join(APP_DIR, dirname)
    if dirname.lower() == 'base': continue
    if not os.path.isdir(app_dir): continue

    if dirname not in application_basenames:
      logging.info('%s' % (dirname))
      applications.append(load_app_from_dir(app_dir))
      application_basenames = [os.path.basename(app.dir) for app in applications]

def getPropertyValuesOfApp(mapping_results, property_names):
  properties_json = []

  comm = getComm()
  for wuobject in mapping_results.values():
    for name in property_names:
      if name in wuobject:
        wuproperty = wuobject.getPropertyByName(name)
        (value, datatype, status) = comm.getProperty(wuobject, int(wuproperty.getId()))
        properties_json.append({'name': name, 'value': value, 'wuclassname': wuproperty.getWuClassName()})

  return properties_json

# List all uploaded applications
class main(tornado.web.RequestHandler):
  def get(self):
    self.render('templates/application.html')

class list_applications(tornado.web.RequestHandler):
  def get(self):
    self.render('templates/index.html', applications=applications)

  def post(self):
    global applications
    update_applications()
    apps = sorted([application.config() for application in applications], key=lambda k: k['name'])
    self.content_type = 'application/json'
    self.write(json.dumps(apps))

# Returns a form to upload new application
class new_application(tornado.web.RequestHandler):
  def post(self):
    global applications
    #self.redirect('/applications/'+str(applications[-1].id), permanent=True)
    #self.render('templates/upload.html')
    try:
      app_name = 'application' + str(len(applications))
      app_id = hashlib.md5(app_name).hexdigest()

      # copy base for the new application
      logging.info('creating application...')
      copyAnything(BASE_DIR, os.path.join(APP_DIR, app_id))

      app = WuApplication(id=app_id, name=app_name, dir=os.path.join(APP_DIR, app_id))
      applications.append(app)

      # dump config file to app
      logging.info('saving application configuration...')
      app.saveConfig()

      self.content_type = 'application/json'
      self.write({'status':0, 'app': app.config()})
    except Exception as e:
      print e
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg':'Cannot create application'})

class application(tornado.web.RequestHandler):
  # topbar info
  def get(self, app_id):
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      title = ""
      if self.get_argument('title'):
        title = self.get_argument('title')
      app = applications[app_ind].config()
      topbar = template.Loader(os.getcwd()).load('templates/topbar.html').generate(application=applications[app_ind], title=title, default_location=LOCATION_ROOT)
      self.content_type = 'application/json'
      self.write({'status':0, 'app': app, 'topbar': topbar})

  # Display a specific application
  def post(self, app_id):
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      # active application
      set_active_application_index(app_ind)
      app = applications[app_ind].config()
      #app = {'name': applications[app_ind].name, 'desc': applications[app_ind].desc, 'id': applications[app_ind].id}
      topbar = template.Loader(os.getcwd()).load('templates/topbar.html').generate(application=applications[app_ind], title="Flow Based Programming")
      self.content_type = 'application/json'
      self.write({'status':0, 'app': app, 'topbar': topbar})

  # Update a specific application
  def put(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      try:
        applications[app_ind].name = self.get_argument('name', 'application name')
        applications[app_ind].desc = self.get_argument('desc', '')
        applications[app_ind].saveConfig()
        self.content_type = 'application/json'
        self.write({'status':0})
      except Exception as e:
        print e
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot save application'})

  # Destroy a specific application
  def delete(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      if delete_application(app_ind):
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot delete application'})

class reset_application(tornado.web.RequestHandler):
  def post(self, app_id):
    app_ind = getAppIndex(app_id)

    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      set_wukong_status("")
      applications[app_ind].status = ""
      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version})

class deploy_application(tornado.web.RequestHandler):
  def get(self, app_id):
    global applications
    global location_tree
    global node_infos
    try:
      # Discovery results
      #comm = getComm()
      node_infos = location_tree.getAllNodeInfos()
      #node_infos = []
      app_ind = getAppIndex(app_id)
      if app_ind == None:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot find the application'})
      else:
        deployment = template.Loader(os.getcwd()).load('templates/deployment.html').generate(app=applications[app_ind], app_id=app_id, node_infos=node_infos, logs=applications[app_ind].logs(), mapping_results=applications[app_ind].mapping_results, set_location=False, default_location=LOCATION_ROOT)
        self.content_type = 'application/json'
        self.write({'status':0, 'page': deployment})
      
    except Exception as e:
      print e
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot initiate connection with the baseStation'})

  def post(self, app_id):
    global location_tree
    app_ind = getAppIndex(app_id)

    set_wukong_status("Start deploying")
    applications[app_ind].status = "    "
    if SIMULATION==1:
      from translator import generateJava
      generateJava(applications[app_ind])

    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      platforms = ['avr_mega2560']
      # TODO: need platforms from fbp

      # old stuff
      '''
      if applications[app_ind].deploy(node_ids, platforms):
        self.content_type = 'application/json'
        self.write({'status':0, 'version': applications[app_ind].version})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Deploy has failed'})
      '''

      # signal deploy in other greenlet task
      wusignal.signal_deploy(platforms)
      set_active_application_index(app_ind)
           
      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version})

class map_application(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    global location_tree

    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      platforms = ['avr_mega2560']
      # TODO: need platforms from fbp

      # comm.addActiveNodesToLocTree(fakedata.locTree)

      # Map with location tree info (discovery), this will produce mapping_results
      applications[app_ind].map(location_tree)

    #  print applications[app_ind].mapping_results

      ret = []
      for key, value in applications[app_ind].mapping_results.items():
        for ind, wuobj in enumerate(value):
          if ind == 0:
            ret.append({'leader': True, 'instanceId': wuobj.getInstanceId(), 'name': wuobj.getWuClassName(), 'nodeId': wuobj.getNodeId(), 'portNumber': wuobj.getPortNumber()})
          else:
            ret.append({'leader': False, 'instanceId': wuobj.getInstanceId(), 'name': wuobj.getWuClassName(), 'nodeId': wuobj.getNodeId(), 'portNumber': wuobj.getPortNumber()})

      self.content_type = 'application/json'
      self.write({'status':0, 'mapping_results': ret, 'version': applications[app_ind].version})

class monitor_application(tornado.web.RequestHandler):
  def get(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    #elif not applications[app_ind].mapping_results or not applications[app_ind].deployed:
      #self.content_type = 'application/json'
      #self.wrtie({'status':1, 'mesg': 'No mapping results or application out of sync, please deploy the application first.'})
    else:

      #properties_json = {}
      properties_json = getPropertyValuesOfApp(applications[app_ind].mapping_results, [property.getName() for wuobject in applications[app_ind].mapping_results.values() for property in wuobject])

      monitor = template.Loader(os.getcwd()).load('templates/monitor.html').generate(app=applications[app_ind], mapping_results={}, logs=applications[app_ind].logs(), properties_json=properties_json)
      self.content_type = 'application/json'
      self.write({'status':0, 'page': monitor})

class properties_application(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      properties_json = getPropertyValuesOfApp(applications[app_ind].mapping_results, [property.getName() for wuobject in applications[app_ind].mapping_results.values() for property in wuobject])

      self.content_type = 'application/json'
      self.write({'status':0, 'properties': properties_json})

# Never let go
class poll(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      #if int(applications[app_ind].version) <= int(self.get_argument('version')):
        #self.content_type = 'application/json'
        #self.write({'status':0, 'version': applications[app_ind].version, 'returnCode': applications[app_ind].returnCode, 'logs': applications[app_ind].retrieve()})
      #else:

      logging.info(get_wukong_status())
      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version, 'wukong_status': get_wukong_status(), 'application_status': applications[app_ind].status, 'returnCode': applications[app_ind].returnCode, 'logs': applications[app_ind].retrieve()})

class save_fbp(tornado.web.RequestHandler):
  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      xml = self.get_argument('xml')
      applications[app_ind].updateXML(xml)
      #applications[app_ind] = load_app_from_dir(applications[app_ind].dir)
      #applications[app_ind].xml = xml
      # TODO: need platforms from fbp
      #platforms = self.get_argument('platforms')
      platforms = ['avr_mega2560']

      self.content_type = 'application/json'
      self.write({'status':0, 'version': applications[app_ind].version})

class load_fbp(tornado.web.RequestHandler):
  def get(self, app_id):
    self.render('templates/fbp.html')

  def post(self, app_id):
    global applications
    app_ind = getAppIndex(app_id)
    if app_ind == None:
      self.content_type = 'application/json'
      self.write({'status':1, 'mesg': 'Cannot find the application'})
    else:
      self.content_type = 'application/json'
      self.write({'status':0, 'xml': applications[app_ind].xml})

class poll_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      status = comm.currentStatus()
      if status != None:
        self.content_type = 'application/json'
        self.write({'status':0, 'logs': status.split('\n')})
      else:
        self.content_type = 'application/json'
        self.write({'status':0, 'logs': []})
    else:
      self.content_type = 'application/json'
      self.write({'status':0, 'logs': []})

class stop_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      if comm.onStopMode():
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1})
    else:
      self.content_type = 'application/json'
      self.write({'status':2})

class exclude_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      if comm.onDeleteMode():
        self.content_type = 'application/json'
        self.write({'status':0, 'log': 'Going into exclude mode'})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'log': 'There is an error going into exclude mode'})
    else:    
      self.content_type = 'application/json'
      self.write({'status':2, 'log': 'Not available in simulation'})

class include_testrtt(tornado.web.RequestHandler):
  def post(self):
    global applications
    if SIMULATION == 0:
      comm = getComm()
      if comm.onAddMode():
        self.content_type = 'application/json'
        self.write({'status':0, 'log': 'Going into include mode'})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'log': 'There is an error going into include mode'})
    else:
      self.content_type = 'application/json'
      self.write({'status':2, 'log': 'Not available in simulation'})

class testrtt(tornado.web.RequestHandler):
  def get(self):
    global node_infos

    if SIMULATION == 0:
        comm = getComm()
        node_infos = comm.getAllNodeInfos()
    elif SIMULATION == 1:
        node_infos = fakedata.simNodeInfos
    else:
        logging.error("SIMULATION %d is not invalid" % (SIMULATION))
        exit()

    # debug purpose
    #node_infos = fakedata.node_infos

    testrtt = template.Loader(os.getcwd()).load('templates/testrtt.html').generate(log=['Please press the buttons to add/remove nodes.'], node_infos=node_infos, set_location=True, default_location = LOCATION_ROOT)
    self.content_type = 'application/json'
    self.write({'status':0, 'testrtt':testrtt})

class refresh_nodes(tornado.web.RequestHandler):
  def post(self):
    global location_tree
    global node_infos

    if SIMULATION == 0:
      comm = getComm()
      node_infos = comm.getActiveNodeInfos(force=True)
    elif SIMULATION ==1:
      node_infos = fakedata.simNodeInfos
      
    else:
      logging.error("SIMULATION %d is not invalid" % (SIMULATION))
      exit()
    location_tree.buildTree(node_infos)
    #furniture data loaded from fake data for purpose of 
    location_tree.addLandmark(fakedata.landmark1)
    location_tree.addLandmark(fakedata.landmark2)
    location_tree.printTree()
    # default is false
    set_location = self.get_argument('set_location', False)

    nodes = template.Loader(os.getcwd()).load('templates/monitor-nodes.html').generate(node_infos=node_infos, set_location=set_location, default_location=LOCATION_ROOT)

    self.content_type = 'application/json'
    self.write({'status':0, 'nodes': nodes})

class nodes(tornado.web.RequestHandler):
  def get(self):
    pass

  def post(self, nodeId):
    info = None
    if SIMULATION == 0:
      comm = getComm()
      info = comm.getNodeInfo(nodeId)
    elif SIMULATION == 1:
      for i in range(fakedata.simNodeInfos):
          if fakedata.simNodeInfos[i].nodeId == nodeId:
              info = fakedata.simNodeInfos[i]
    else:
        logging.error("SIMULATION %d is not invalid" % (SIMULATION))
        exit()
    
    self.content_type = 'application/json'
    self.write({'status':0, 'node_info': info})

  def put(self, nodeId):
    global location_tree
    global node_infos
    location = self.get_argument('location')
    if SIMULATION !=0:
      for info in node_infos:
        if info.nodeId == int(nodeId):
          info.location = location
          senNd = SensorNode(info)
#          senNd = SensorNode(info, 0, 0, 0)
          location_tree.addSensor(senNd)
      location_tree.printTree()
      self.content_type = 'application/json'
      self.write({'status':0})
      return
    if location:
      comm = getComm()
      if comm.setLocation(int(nodeId), location):
        # update our knowledge too
        for info in comm.getActiveNodeInfos():
          if info.nodeId == int(nodeId):
            info.location = location
            senNd = SensorNode(info)
            print (info.location)
#            senNd = SensorNode(info, 0, 0, 0)
            location_tree.addSensor(senNd)
        location_tree.printTree()
        self.content_type = 'application/json'
        self.write({'status':0})
      else:
        self.content_type = 'application/json'
        self.write({'status':1, 'mesg': 'Cannot set location, please try again.'})

class loc_tree(tornado.web.RequestHandler):	
  def post(self):
    global location_tree
    global node_infos
    
    load_xml = ""
    flag = os.path.exists("../ComponentDefinitions/landmark.xml")
#    if(flag):
    if(False):
      f = open("../ComponentDefinitions/landmark.xml","r")
      for row in f:
        load_xml += row	
    else:
      pass
  #  print node_infos      
    addloc = template.Loader(os.getcwd()).load('templates/display_locationTree.html').generate(node_infos=node_infos)
    print "addloc"+str(addloc)
    disploc = location_tree.getJson()   #a list of all the nodes to be drawn
    print "displaying disploc" 
    print disploc

    self.content_type = 'application/json'
    self.write({'loc':json.dumps(disploc),'node':addloc,'xml':load_xml})	
  
  def get(self, node_id):
    global location_tree
    global node_infos
    node_id = int(node_id)
    curNode = location_tree.findLocationById(node_id)
    if curNode == None:
        self.write({'status':1,'message':'cannot find node id '+str(node_id)})
        return
    else:
        self.write({'status':0, 'message':'succeed in finding node id'+str(node_id), 
                    'distanceModifier':str(curNode.distanceModifier), 'centerPnt':curNode.centerPnt, 
                    'size':curNode.size, 'location':curNode.getLocationStr(), 'local_coord':curNode.getOriginalPnt(),
                    'global_coord':curNode.getGlobalOrigPnt()})	

class sensor_info(tornado.web.RequestHandler):	
    def get(self, node_id, sensor_id):
        global location_tree
        global node_infos
        node_id = int(node_id)
        curNode = location_tree.findLocationById(node_id)
        if curNode == None:
            self.write({'status':1,'message':'cannot find node id '+str(node_id)})
            return
        if sensor_id[0:2] =='se':   #sensor case
            se_id = int(sensor_id[2:])
            sensr = curNode.getSensorById(se_id)
            self.write({'status':0,'message':'find sensor id '+str(se_id), 'location':sensr.location})
        elif sensor_id[0:2] =='lm': #landmark case
            lm_id = int(sensor_id[2:])
            landmk = curNode.findLandmarkById(lm_id)
            self.write({'status':0,'message':'find landmark id '+str(lm_id), 'location':landmk.location,'size':landmk.size, 'direction':landmk.direction})
        else:
            self.write({'status':1, 'message':'failed in finding '+sensor_id+" in node"+ str(node_id)})
    
    
class tree_modifier(tornado.web.RequestHandler):
  def put(self, mode):
    start_id = self.get_argument("start")
    end_id = self.get_argument("end")
    distance = self.get_argument("distance")
    paNode = location_tree.findLocationById(int(start_id)//100)      #find parent node
    if paNode !=None:
        if int(mode) == 0:        #adding modifier between siblings
            if paNode.addDistanceModifier(int(start_id), int(end_id), int(distance)):
                self.write({'status':0,'message':'adding distance modifier between '+str(start_id) +'and'+str(end_id)+'to node'+str(int(start_id)//100)})
                return
            else:
                self.write({'status':1,'message':'adding faild due to not able to find common direct father of the two nodes'})
                return
        elif int(mode) == 1:        #deleting modifier between siblings
            if paNode.delDistanceModifier(int(start_id), int(end_id), int(distance)):
                self.write({'status':0,'message':'deletinging distance modifier between '+str(start_id) +'and'+str(end_id)+'to node'+str(int(start_id)//100)})
                return
            else:
                self.write({'status':1,'message':'deleting faild due to not able to find common direct father of the two nodes'})
                return
    self.write({'status':1,'message':'operation faild due to not able to find common direct father of the two nodes'})
    
 
class save_landmark(tornado.web.RequestHandler):
	def put(self):
		global location_tree
		
		self.write({'tree':location_tree})

	def post(self):
		landmark_info = self.get_argument('xml')
		f = open("../ComponentDefinitions/landmark.xml","w")
		f.write(landmark_info)
		f.close()
		
class add_landmark(tornado.web.RequestHandler):
  def put(self):
    global location_tree
    global landId
    name = self.get_argument("name")
    id = 0;
    location = self.get_argument("location")
    operation = self.get_argument("ope")
    size  = self.get_argument("size")
    direct = self.get_argument("direction")
    landmark = None
    rt_val = 0
    msg = ''
    if(operation=="1"):
      landmark = LandmarkNode(name, location, size, direct) 
      rt_val = location_tree.addLandmark(landmark)
      msg = 'add fails'
      location_tree.printTree()
    elif(operation=="0"):
      rt_val = location_tree.delLandmark(id)
      msg = 'deletion fails'
    
    self.content_type = 'application/json'
    if rt_val ==0:
        self.write({'status':0, 'id':landmark.getId()})
    if rt_val ==1:
        self.write({'status':1, 'id':landmark.getId(), 'msg':msg})
		       
settings = dict(
  static_path=os.path.join(os.path.dirname(__file__), "static"),
  debug=True
)

app = tornado.web.Application([
  (r"/", main),
  (r"/main", main),
  (r"/testrtt/exclude", exclude_testrtt),
  (r"/testrtt/include", include_testrtt),
  (r"/testrtt/stop", stop_testrtt),
  (r"/testrtt/poll", poll_testrtt),
  (r"/testrtt", testrtt),
  (r"/nodes/([0-9]*)", nodes),
  (r"/nodes/refresh", refresh_nodes),
  (r"/applications", list_applications),
  (r"/applications/new", new_application),
  (r"/applications/([a-fA-F\d]{32})", application),
  (r"/applications/([a-fA-F\d]{32})/reset", reset_application),
  (r"/applications/([a-fA-F\d]{32})/properties", properties_application),
  (r"/applications/([a-fA-F\d]{32})/poll", poll),
  (r"/applications/([a-fA-F\d]{32})/deploy", deploy_application),
  (r"/applications/([a-fA-F\d]{32})/deploy/map", map_application),
  (r"/applications/([a-fA-F\d]{32})/monitor", monitor_application),
  (r"/applications/([a-fA-F\d]{32})/fbp/save", save_fbp),
  (r"/applications/([a-fA-F\d]{32})/fbp/load", load_fbp),
  (r"/loc_tree/nodes/([0-9]*)", loc_tree),
  (r"/loc_tree/nodes/([0-9]*)/(\w+)", sensor_info),
  (r"/loc_tree", loc_tree),
  (r"/loc_tree/modifier/([0-9]*)", tree_modifier),
  (r"/loc_tree/save", save_landmark),
  (r"/loc_tree/land_mark", add_landmark)
], IP, **settings)

ioloop = tornado.ioloop.IOLoop.instance()
if __name__ == "__main__":
  logging.info("WuKong starting up...")
  setup_signal_handler_greenlet()
  update_applications()
  app.listen(MASTER_PORT)
  location_tree = LocationTree(LOCATION_ROOT)
  import_wuXML()
  make_FBP()
  ioloop.start()

