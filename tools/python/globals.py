active_ind = 0
applications = []
location_tree = None
wukong_status = ""

MASTER_BUSY = True

def is_master_busy():
    global MASTER_BUSY
    return MASTER_BUSY

def master_busy():
    global MASTER_BUSY
    MASTER_BUSY = True

def master_available():
    global MASTER_BUSY
    MASTER_BUSY = False

def active_application():
  global applications
  global active_ind
  return applications[active_ind]

def set_active_application_index(new_index):
  global active_ind
  active_ind = new_index

def get_wukong_status():
  global wukong_status
  return wukong_status

def set_wukong_status(status):
  global wukong_status
  print '-----set_wukong_status %s' % (status)
  wukong_status = status
