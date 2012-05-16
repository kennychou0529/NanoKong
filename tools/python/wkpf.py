#!/usr/bin/python

import sys
import pynvc

DATATYPE_INT16 = 0
DATATYPE_BOOLEAN = 1
DATATYPE_REFRESH_RATE = 2

global __sequenceNumber
__sequenceNumber = 0

def getNextSequenceNumberAsList():
  global __sequenceNumber
  __sequenceNumber = (__sequenceNumber + 1) % (2**16)
  return [__sequenceNumber/256, __sequenceNumber%256]

class WuObject:
  def __init__(self, nodeId, portNumber, wuclassId):
    self.nodeId = nodeId
    self.portNumber = portNumber
    self.wuclassId = wuclassId
  def __repr__(self):
    return 'wuobject(node %d port %d wuclass %d)' % (self.nodeId, self.portNumber, self.wuclassId)

def verifyWKPFmsg(messageStart, minAdditionalBytes):
  # minPayloadLength should not include the command or the 2 byte sequence number
  return lambda command, payload: (command == pynvc.WKPF_ERROR_R) or (payload != None and payload[0:len(messageStart)]==messageStart and len(payload) >= len(messageStart)+minAdditionalBytes)

def getWuClassList(destination):
  sn = getNextSequenceNumberAsList()
  reply = pynvc.sendWithRetryAndCheckedReceive(destination=destination,
                                                command=pynvc.WKPF_GET_WUCLASS_LIST,
                                                payload=sn,
                                                allowedReplies=[pynvc.WKPF_GET_WUCLASS_LIST_R, pynvc.WKPF_ERROR_R],
                                                verify=verifyWKPFmsg(messageStart=sn, minAdditionalBytes=1)) # number of wuclasses
  if reply == None:
    return None
  if reply[0] == pynvc.WKPF_ERROR_R:
    print "WKPF RETURNED ERROR ", reply[3]
    return None
  wuclasses = []
  reply = reply[4:]
  while len(reply) > 1:
    wuclasses.append((reply[0] <<8) + reply[1])
    reply = reply[2:]
  return wuclasses

def getWuObjectList(destination):
  sn = getNextSequenceNumberAsList()
  reply = pynvc.sendWithRetryAndCheckedReceive(destination=destination,
                                                command=pynvc.WKPF_GET_WUOBJECT_LIST,
                                                payload=sn,
                                                allowedReplies=[pynvc.WKPF_GET_WUOBJECT_LIST_R, pynvc.WKPF_ERROR_R],
                                                verify=verifyWKPFmsg(messageStart=sn, minAdditionalBytes=1)) # number of wuobjects
  if reply == None:
    return None
  if reply[0] == pynvc.WKPF_ERROR_R:
    print "WKPF RETURNED ERROR ", reply[3]
    return None
  wuobjects = []
  reply = reply[4:]
  while len(reply) > 1:
    wuobjects.append(WuObject(destination, reply[0], (reply[1] <<8) + reply[2]))
    reply = reply[3:]
  return wuobjects

def getProperty(wuobject, propertyNumber):
  sn = getNextSequenceNumberAsList()
  payload=sn+[wuobject.portNumber, wuobject.wuclassId/256, wuobject.wuclassId%256, propertyNumber]
  reply = pynvc.sendWithRetryAndCheckedReceive(destination=wuobject.nodeId,
                                                command=pynvc.WKPF_READ_PROPERTY,
                                                payload=payload,
                                                allowedReplies=[pynvc.WKPF_READ_PROPERTY_R, pynvc.WKPF_ERROR_R],
                                                verify=verifyWKPFmsg(messageStart=payload, minAdditionalBytes=2)) # datatype + value
  if reply == None:
    return None
  if reply[0] == pynvc.WKPF_ERROR_R:
    print "WKPF RETURNED ERROR ", reply[3]
    return None
  datatype = reply[7]
  if datatype == DATATYPE_BOOLEAN:
    return reply[8] != 0
  elif datatype == DATATYPE_INT16 or datatype == DATATYPE_REFRESH_RATE:
    return (reply[8] <<8) + reply[9]
  else:
    return None

def setProperty(wuobject, propertyNumber, datatype, value):
  sn = getNextSequenceNumberAsList()
  if datatype == DATATYPE_BOOLEAN:
    payload=sn+[wuobject.portNumber, wuobject.wuclassId/256, wuobject.wuclassId%256, propertyNumber, datatype, 1 if value else 0]
  elif datatype == DATATYPE_INT16 or datatype == DATATYPE_REFRESH_RATE:
    payload=sn+[wuobject.portNumber, wuobject.wuclassId/256, wuobject.wuclassId%256, propertyNumber, datatype, value/256, value%256]
  reply = pynvc.sendWithRetryAndCheckedReceive(destination=wuobject.nodeId,
                                                command=pynvc.WKPF_WRITE_PROPERTY,
                                                payload=payload,
                                                allowedReplies=[pynvc.WKPF_WRITE_PROPERTY_R, pynvc.WKPF_ERROR_R],
                                                verify=verifyWKPFmsg(messageStart=payload[0:6], minAdditionalBytes=0))
  if reply == None:
    return None
  if reply[0] == pynvc.WKPF_ERROR_R:
    print "WKPF RETURNED ERROR ", reply[3]
    return None
  return value


pynvc.init(0)
#print getWuClassList(3)
#print getWuObjectList(3)
#print getProperty(WuObject(nodeId=3, portNumber=4, wuclassId=4), 0)
#print setProperty(WuObject(nodeId=3, portNumber=1, wuclassId=3), 0, DATATYPE_INT16, 255)