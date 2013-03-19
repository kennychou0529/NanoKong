#!/usr/bin/python
# vim: ts=4 sw=4

# Wukong middleware framework
# Codegen component frontend for component.xml
# plus backend for parsing and generating code for
# java component implementation
# and plugin for NiagaraAX tool
#
#
# Author: Penn Su
# Date: May 13, 2012

import sys, os, re
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import distutils.dir_util
import logging
from jinja2 import Template, Environment, FileSystemLoader
from optparse import OptionParser
from xml.dom.minidom import parse, parseString

from util import *
from configuration import *

# Those classes are temporaily moved here for compatibility reasons
class WuType:
    def __init__(self, name, dataType, values=()):
        self._name = name  # WuType's name
        self._dataType = dataType # a string describing data type
        self._allowed_values = values # a tuple of sequential unicode values of the specified type

    def __repr__(self):
        return "WuType %s (type=%s) val:%s" % (self._name, self._dataType, str(self._allowed_values))

    def __contains__(self, value):
        return value in self._allowed_values

    def getName(self):
        return self._name

    def getDataType(self):
        return self._dataType

    def hasAllowedValues(self):
        return self._allowed_values != ()

    def getAllowedValues(self):
        return self._allowed_values

    def getValueInCConstant(self, value):
        return 'WKPF_' + '_'.join([Convert.to_constant(self._dataType), Convert.to_constant(self._name), Convert.to_constant(value)])

    def getValueInJavaConstant(self, value):
        return '_'.join([Convert.to_constant(self._dataType), Convert.to_constant(self._name), Convert.to_constant(value)])

    def getValueInJavaConstByValue(self, value):
        if self.hasAllowedValues():
            return 'GENERATEDWKPF.' + Convert.to_constant(self._dataType) + "_" + Convert.to_constant(self._name) + "_" + Convert.to_constant(value)
        else:
            return value

class WuProperty:
    def __init__(self, class_name, name, id, wutype, access, default=None, value=None, status=None):
        self._class_name = class_name
        self._name = name  # an unicode for property's name
        self._id = id      # an integer for property's id
        self._wutype = wutype # a WuType object
        self._access = access
        self._default = default
        self._current_value = value
        self._property_status = status

    def __repr__(self):
        return "WuProperty %s (id=%s, wutype=%s access=%s current_value=%s)" % (self._name, self._id, self._wutype, self._access, str(self._current_value))

    def getName(self):
        return self._name 

    def getWuClassName(self):
        return self._class_name

    def getJavaName(self):
        return Convert.to_constant(self._name)

    def getCConstName(self):
        return "WKPF_" + self.getJavaConstName()

    def getJavaConstName(self):
        return "PROPERTY_" + Convert.to_constant(self._class_name) + "_" + Convert.to_constant(self._name)

    def getPropertyStatus(self):
        return self._property_status

    def setPropertyStatus(self, status):
        self._property_status = status

    def hasDefault(self):
        return self._default != None

    def getDefault(self):
        return self._default

    def setDefault(self, default):
        if self._wutype.hasAllowedValues():
            if default in self._wutype.getAllowedValues():
                self._default = default
        else:
            self._default = default

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getWuType(self):
        return self._wutype

    def getDataType(self):
        return self._wutype.getName()

    # deprecated
    def setDataType(self, typeName):
        print 'set datatype of name %s of property %s' % (typeName, self.getName())
        if typeName != self._wutype.getName():
            for wutype in WuType.all():
                if wutype.getName() == typeName:
                    self._wutype = copy.deepcopy(wutype)


    def getAccess(self):
        return self._access

    def getCurrentValue(self):
        if self._current_value == None:
            return self._default
        return self._current_value

    def setCurrentValue(self, value):
        if self._wutype.hasAllowedValues():
            if value in self._wutype:
                self._current_value = value
        else:
            self._current_value = value

# Now both WuClass and WuObject have node id attribute, because each could represent at different stages of mapping process
class WuClass:
    def __init__(self, name, id, properties, virtual, soft, node_id=None):
        self._name = name  # WuClass's name
        self._id = id      # an integer for class' id
        self._properties = properties  # a dict of WuProperty objects accessed thru the prop's name
        self._virtual = virtual    # a boolean for virtual or native
        self._soft = soft  # a boolean for soft or hard
        self_node_id = node_id

    def __iter__(self):
        for property in self._properties.values():
            yield property

    def __contains__(self, propertyName):
        return propertyName in self._properties

    def __repr__(self):
        return "WuClass %s (id=%d, virt=%s, soft=%s) prop:%s" % (self._name, self._id,str(self._virtual),str(self._soft),str(self._properties))

    def getPropertyByName(self, name):
        if name in self._properties:
            return self._properties[name]
        return None

    def setPropertyByName(self, name, property):
        if name in self._properties:
            self._properties[name] = property
            return True
        return False
    
    def getPropertyValueByName(self, name):
        if name in self._properties:
            return prop.getCurrentValue()
        return None
            
    def setPropertyValueByName(self, name, value):
        if name in self._properties:
            prop =  self._properties[name]
            prop.setCurrentValue(value)
            
    def getJavaGenClassName(self):
        return "GENERATEDVirtual" + Convert.to_java(self._name) + "WuObject"

    def getJavaClassName(self):
        return "Virtual" + Convert.to_java(self._name) + "WuObject"

    def getCDefineName(self):
        return Convert.to_constant(self.getCName())

    def getCName(self):
        return 'wuclass_' + Convert.to_c(self._name)

    def getCFileName(self):
        return 'GENERATED' + self.getCName()

    def getCUpdateName(self):
        return self.getCName() + "_update"

    def getCPropertyName(self):
        return self.getCName() + "_properties"

    def getCConstName(self):
        return "WKPF_" + self.getJavaConstName()

    def getJavaConstName(self):
        return "WUCLASS_" + Convert.to_constant(self._name)

    def getName(self):
        return self._name

    def getProperties(self):
        return self._properties

    def getId(self):
        return self._id

    def isVirtual(self):
        return self._virtual

    def isSoft(self):
        return self._soft

    def getNodeId(self):
        return self._node_id

    def setNodeId(self, id):
        self._node_id = id

# Now both WuClass and WuObject have node id attribute, because each could represent at different stages of mapping process
# The wuClass in WuObject is just for reference only, the node_id shouldn't be used
class WuObject:
    def __init__(self, wuClass, instanceId, instanceIndex, nodeId=None, portNumber=None, occupied = False, queries=[]):
        self._wuClass = wuClass
        self._instanceId = instanceId
        self._instanceIndex = instanceIndex
        self._nodeId = nodeId
        self._portNumber = portNumber
        self._hasWuClass = False
        self._occupied = occupied
         #queries are [locationQuery, group_sizeQuery], should be replaced by a query class when we have more policy requirements in the future.
        self._queries = queries

    def __repr__(self):
        return 'wuobject(node:'+ str(self._nodeId)+' port:'+ str(self._portNumber)+ ' wuclass id: '+ str(self.getWuClassId())+' queries:'+ str(self._queries) +')'

    def __contains__(self, propertyName):
        return propertyName in self._wuClass.getProperties()

    def __iter__(self):
        for property in self.getProperties().values():
            yield property

    def isOccupied(self):
        return self._occupied

    def setOccupied(self, va = False):
        self._occupied = va

    def hasWuClass(self):
        return self._hasWuClass

    def setHasWuClass(self, value):
        self._hasWuClass = value

    def addQueries(self, queries):
        for query in queries:
            self.addQuery(query)

    def removeQuery(self, query):
        self._queries.remove(query)

    def addQuery(self, query):
        self._queries.append(query)

    def getQueries(self):
        return self._queries

    def setQueries(self, queries):
        self._queries = queries

    def toJava(self):
        print 'wuobject toJava'
        return ', '.join([str(self.getNodeId()), str(self.getPortNumber())])

    def getWuClass(self):
        return self._wuClass

    def getWuClassName(self):
        return self._wuClass.getName()

    def getWuClassId(self):
        return self._wuClass.getId()

    def getInstanceId(self):
        return self._instanceId

    def getInstanceIndex(self):
        return self._instanceIndex

    def getNodeId(self):
        return self._nodeId

    def setNodeId(self, nodeId):
        self._nodeId = nodeId

    def getPortNumber(self):
        return self._portNumber
    
    def setPortNumber(self, portNumber):
        self._portNumber = portNumber

    def getPropertyByName(self, prop_name):
        return self._wuClass.getPropertyByName(prop_name)

    def getProperties(self):
        return self._wuClass.getProperties()

    def setProperties(self, properties):
        for property in properties:
            self._wuClass.setPropertyByName(property.getName(), property)


class CodeGen:
    @staticmethod
    def generate(logger, component_string, project_dir):
        global_vm_dir = os.path.join('vm', 'src')
        vm_dir = os.path.join('vm', 'src', 'native_wuclasses')
        java_dir = os.path.join('java', 'nanovm', 'wkpf')

        plugin_dir = os.path.join(project_dir, 'plugins')
        template_dir = os.path.join(plugin_dir, 'templates')

        # Filenames
        global_vm_header_filename = 'GENERATEDwkpf_wuclass_library.h'
        global_virtual_constants_filename = 'GENERATEDWKPF.java'

        # Paths
        global_vm_header_path = os.path.join(project_dir, global_vm_dir, global_vm_header_filename)
        global_virtual_constants_path = os.path.join(project_dir, java_dir, global_virtual_constants_filename)

        # IOs
        global_vm = open(global_vm_header_path, 'w')
        global_virtual_constants = open(global_virtual_constants_path, 'w')

        # Lines
        global_vm_header_lines = []
        global_virtual_constants_lines = []

        # Parse ComponentLibrary XML
        dom = parseString(component_string)

        wuclasses = dom.getElementsByTagName("WuClass")
        wutypedefs = dom.getElementsByTagName("WuTypedef")
        wutypedefs_hash = []

        logger.info("==================Begin TypeDefs=====================")
        # Boilerplate for Java global constants file
        global_virtual_constants_lines.append('''
            package nanovm.wkpf;

            public class GENERATEDWKPF {
        ''')

        # Parsing to WuKong Profile Framework Component Library header
        wuTypes = {'short': WuType('short', 'short'), 'boolean': WuType('boolean', 'boolean'), 'refresh_rate': WuType('refresh_rate', 'refresh_rate')}

        for wutypedef in wutypedefs:
          logger.info("Parsing wutype %s" % (wutypedef.getAttribute('name')))
          if wutypedef.getAttribute('type').lower() == 'enum':
            wuTypes[wutypedef.getAttribute('name')] = WuType(wutypedef.getAttribute('name'), wutypedef.getAttribute('type'), tuple([element.getAttribute('value') for element in wutypedef.getElementsByTagName('enum')]))
          else:
            wuTypes[wutypedef.getAttribute('name')] = WuType(wutypedef.getAttribute('name'), wutypedef.getAttribute('type'))

          wutype = wuTypes[wutypedef.getAttribute('name')]

          wutypedefs_hash.append(wutypedef.getAttribute("name"))

          # Generate global header typedef definition for VM
          for enumvalue, value in enumerate(wutype.getAllowedValues()):
            cline = "#define " + wutype.getValueInCConstant(value) + " %d\n" % (enumvalue)
            jline = "public static final short " + wutype.getValueInJavaConstant(value) + " = %d;\n" % (enumvalue)

            global_vm_header_lines.append(cline)
            global_virtual_constants_lines.append(jline)
        logger.info("==================End of TypeDefs=====================")

        logger.info("==================Begin WuClasses=====================")
        for wuclass in wuclasses:
          logger.info("Parsing WuClass %s" % (wuclass.getAttribute('name')))
          wuclassName = wuclass.getAttribute('name')
          wuclassId = int(wuclass.getAttribute('id'),0)
          wuclassProperties = {}
          for i, prop in enumerate(wuclass.getElementsByTagName('property')):
              propType = prop.getAttribute('datatype')
              propName = prop.getAttribute('name')

              wuclassProperties[propName] = WuProperty(wuclassName, propName, i, wuTypes[propType], prop.getAttribute('access')) 

          wuClass = WuClass(wuclassName, wuclassId, wuclassProperties, True if wuclass.getAttribute('virtual').lower() == 'true' else False, True if wuclass.getAttribute('type').lower() == 'soft' else False)


          # Native header
          wuclass_native_header_path = os.path.join(project_dir, vm_dir, wuClass.getCFileName() + '.h')
          wuclass_native_header = open(wuclass_native_header_path, 'w')

          # Native impl
          wuclass_native_impl_path = os.path.join(project_dir, vm_dir, wuClass.getCFileName() + '.c')
          wuclass_native_impl = open(wuclass_native_impl_path, 'w')

          # Virtual (Java)
          if wuclass.getAttribute('virtual') == 'true':
            wuclass_virtual_super_path = os.path.join(project_dir, java_dir, wuClass.getJavaGenClassName() + '.java')
            wuclass_virtual_super = open(wuclass_virtual_super_path, 'w') 

          # Lines
          wuclass_native_header_lines = []
          wuclass_native_impl_lines = []
          wuclass_virtual_super_lines = []

          # Generate global header definition for VM
          global_vm_header_lines.append("#define " + wuClass.getCConstName() + " %s\n" % (wuClass.getId()))

          # Generate global constants definition for Java
          global_virtual_constants_lines.append("public static final short " + wuClass.getJavaConstName() + " = %s;\n" % (wuClass.getId()))

          for indprop, property in enumerate(wuClass.getProperties().values()):
            global_vm_header_lines.append("#define " + property.getCConstName() + " " + str(indprop) + "\n")

            global_virtual_constants_lines.append("public static final byte " + property.getJavaConstName() + " = " + str(indprop) + ";\n")

          global_vm_header_lines.append("\n")

          global_virtual_constants_lines.append("\n")


          # Parsing to WuKong Profile Framework Component Library header in Java
          if wuclass.getAttribute('virtual') == 'true':
            wuclass_virtual_super_lines.append('''
            package nanovm.wkpf;

            public abstract class %s extends VirtualWuObject {
              public static byte[] properties = new byte[] {
            ''' % (wuClass.getJavaGenClassName()))

            for ind, property in enumerate(wuClass.getProperties().values()):
              datatype = property.getDataType()
              access = property.getAccess()

              print 'datatype', datatype
              print 'wutypedef_hash', wutypedefs_hash
              if datatype in wutypedefs_hash:
                datatype = "SHORT"

              line = "WKPF.PROPERTY_TYPE_" + datatype.upper() + "|WKPF.PROPERTY_ACCESS_" + access.upper()
              if ind < len(wuClass.getProperties())-1:
                line += ","

              line += "\n"
              wuclass_virtual_super_lines.append(line)

            wuclass_virtual_super_lines.append('''
              };
            ''')

            for propind, property in enumerate(wuClass.getProperties().values()):
              wuclass_virtual_super_lines.append("protected static final byte %s = %d;\n" % (property.getJavaName(), propind))

            wuclass_virtual_super_lines.append('''
            }
            ''')

          # Generate C header for each native component implementation
          wuclass_native_header_lines.append('''
          #include <wkpf.h>
          #include "native_wuclasses.h"

          #ifndef %sH
          #define %sH

          extern wkpf_wuclass_definition %s;

          #endif
          ''' % (
                  wuClass.getCDefineName(),
                  wuClass.getCDefineName(),
                  wuClass.getCName()
                ))

          # Generate C implementation for each native component implementation
          wuclass_native_impl_lines.append('''
          #include <wkpf.h>
          #include "native_wuclasses.h"

          #ifdef ENABLE_%s

          extern void %s(wkpf_local_wuobject *wuobject);

          uint8_t %s[] = {
          ''' % (
                  wuClass.getCDefineName(),
                  wuClass.getCUpdateName(),
                  wuClass.getCPropertyName(),
                ))

          for ind, property in enumerate(wuClass.getProperties().values()):
            datatype = property.getDataType()
            access = property.getAccess()

            if datatype in wutypedefs_hash:
              datatype = "SHORT"

            line = "WKPF_PROPERTY_TYPE_" + datatype.upper() + "+WKPF_PROPERTY_ACCESS_" + access.upper()
            if ind < len(wuClass.getProperties())-1:
              line += ","

            line += "\n"
            wuclass_native_impl_lines.append(line)

          wuclass_native_impl_lines.append('''
          };
          ''')

          wuclass_native_impl_lines.append('''
          wkpf_wuclass_definition %s = {
            %s,
            %s,
            %d,
            %s
          };
          ''' % (wuClass.getCName(), 
                wuClass.getCConstName(),
                wuClass.getCUpdateName(),
                len(wuClass.getProperties()), 
                wuClass.getCPropertyName()))

          wuclass_native_impl_lines.append('''
          #endif
          ''')

          wuclass_native_header.writelines(wuclass_native_header_lines)
          wuclass_native_header.close()

          wuclass_native_impl.writelines(wuclass_native_impl_lines)
          wuclass_native_impl.close()

          if wuclass.getAttribute('virtual') == 'true':
            wuclass_virtual_super.writelines(wuclass_virtual_super_lines)
            wuclass_virtual_super.close()

          print "==================End of WuClasses====================="

        global_virtual_constants_lines.append('''
        }
        ''')

        global_vm.writelines(global_vm_header_lines)
        global_vm.close()

        global_virtual_constants.writelines(global_virtual_constants_lines)
        global_virtual_constants.close()



# deprecated
class PluginGen:
  def __init__(self, *args, **kwargs):
    # Plugin Name
    if 'plugin_name' in kwargs:

      self.plugin_name = kwargs['plugin_name']
      self.plugin_template_dir = os.path.join(template_dir, kwargs['plugin_name'], 'wukongObject')
      self.plugin_root_dir = os.path.join(plugin_dir, kwargs['plugin_name'], 'wukongObject')

      self.jinja2_env = Environment(loader=FileSystemLoader(get_all_subdirectories(plugin_template_dir) + [plugin_template_dir]))
      self.jinja2_env.filters["convert_filename_to_java"] = convert_filename_to_java

  # deprecated
  def generate_plugin(self):
    dom = parseString(self.component_string)

    wuclasses = dom.getElementsByTagName("WuClass")
    wutypedefs = dom.getElementsByTagName("WuTypedef")
    wucomponents = component_root.xpath("WuClass | WuTypedef")

    # Create plugin folder structure
    if self.plugin_name:
      distutils.dir_util.copy_tree(self.plugin_template_dir, self.plugin_root_dir)

      if self.plugin_name == "niagara":
        module_include_path = os.path.join(self.plugin_root_dir, 'module-include.xml')
        module_include = open(module_include_path, 'w')
        module_include_template = self.jinja2_env.get_template('module-include.xml')
        module_include.write(module_include_template.render(components=wucomponents))
        module_include.close()

        module_palette_path = os.path.join(self.plugin_root_dir, 'module.palette')
        module_palette = open(module_palette_path, 'w')
        module_palette_template = self.jinja2_env.get_template('module.palette')
        module_palette.write(module_palette_template.render(
          virtuals=component_root.xpath("//*[@virtual='true']"), 
          sensors=component_root.xpath("//*[contains(@name, 'Sensor')]"), 
          controllers=component_root.xpath("//*[contains(@name, 'Controller')]"),
          actuators=component_root.xpath("//*[contains(@name, 'Actuator')]")))
        module_palette.close()


        class_implementation_dir = os.path.join(self.plugin_root_dir, 'src', 'com', 'wukong', 'wukongObject')
        distutils.dir_util.mkpath(class_implementation_dir)
        #class_implementation_template = Template(open(os.path.join(class_implementation_dir, 'BTemplate.java')).read())
        class_implementation_template = self.jinja2_env.get_template('BTemplate.java')
        enum_implementation_template = self.jinja2_env.get_template('BTemplateEnum.java')

        for wuclass in wuclasses:
          wuclass_implementation_path = os.path.join(class_implementation_dir, 'B%s.java' % (convert_filename_to_java(wuclass.get("name"))))
          wuclass_implementation = open(wuclass_implementation_path, 'w')
          wuclass_implementation.write(class_implementation_template.render(component=wuclass))

        for wutypedef in wutypedefs:
          if wutypedef.get("type").lower() == 'enum':
            wutypedef_implementation_path = os.path.join(class_implementation_dir, 'B%s.java' % (convert_filename_to_java(wutypedef.get("name"))))
            wutypedef_implementation = open(wutypedef_implementation_path, 'w')
            wutypedef_implementation.write(enum_implementation_template.render(component=wutypedef))

      # delete template files
      try:
        os.remove(findInSubdirectory('BTemplate.java', self.plugin_root_dir))
      except IOError:
        print "Attempting to remove non-existing file %s" % ('BTemplate.java')

      try:
        os.remove(findInSubdirectory('BTemplateEnum.java', self.plugin_root_dir))
      except IOError:
        print "Attempting to remove non-existing file %s" % ('BTemplateEnum.java')


      print "==================End of Plugin====================="



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-i', '--input_xml', dest='component_file')
    parser.add_option('-p', '--projectdir', dest='project_dir')
    parser.add_option('-u', '--plugin', dest='plugin_name')
    (options, args) = parser.parse_args()

    print options, args

    if os.path.exists(options.component_file) and options.project_dir:
        CodeGen.generate(logging.getLogger(), open(options.component_file).read(), options.project_dir)
    else:
        print "path don't exist", options.component_file, options.project_dir
