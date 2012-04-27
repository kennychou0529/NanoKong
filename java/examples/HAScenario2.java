import java.io.*;
import nanovm.avr.*;
import nanovm.wkpf.*;
import nanovm.lang.Math;

public class HAScenario2 {
  // =========== Constant part, not affected by the application.
  private static int myNodeId;

  private static byte getPortNumberForComponent(int componentId) {
    return componentInstanceToEndpointMap[componentId*3 + 2];
  }
  private static boolean isLocalComponent(int componentId) {
    int nodeId=componentInstanceToEndpointMap[componentId*3]*256
               +componentInstanceToEndpointMap[componentId*3 + 1];
    return nodeId == myNodeId;
  }

  // =========== Generated by the compiler
  private static final int COMPONENT_INSTANCE_ID_INPUTCONTROLLER1 = 0;
  private static final int COMPONENT_INSTANCE_ID_LIGHTSENSOR1 = 1;
  private static final int COMPONENT_INSTANCE_ID_THRESHOLD1 = 2;
  private static final int COMPONENT_INSTANCE_ID_LIGHT1 = 3;
  private static final int COMPONENT_INSTANCE_ID_OCCUPANCY1 = 4;
  private static final int COMPONENT_INSTANCE_ID_ANDGATE1 = 5;

  private static short tmpDummy = 0;
  
  /*
  typedef struct remote_endpoint_struct {
    address_t node_id;
    uint8_t port_number;  
  } remote_endpoint;
  */
  private static final byte[] componentInstanceToEndpointMap = { // Indexed by component instance id.
    (byte)0, (byte)1, (byte)1, // Input        @ node 1, port 1
    (byte)0, (byte)1, (byte)2, // Light sensor @ node 1, port 2
    (byte)0, (byte)3, (byte)3, // Threshold    @ node 3, port 3
    (byte)0, (byte)3, (byte)4, // Light        @ node 3, port 4
    (byte)0, (byte)1, (byte)5, // Occupancy    @ node 1, port 5
    (byte)0, (byte)3, (byte)6, // And gate     @ node 3, port 6  
  };

  /*
  typedef struct link_entry_struct {
    uint16_t src_component_id;
    uint8_t src_property_number;
    uint16_t dest_component_id;  
    uint8_t dest_property_number;
    uint16_t dest_profile_id;
  } link_entry;
  */
  private static final byte[] linkDefinitions = {
    (byte)0, (byte)COMPONENT_INSTANCE_ID_LIGHTSENSOR1, (byte)WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE,
    (byte)0, (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)WKPF.PROPERTY_THRESHOLD_VALUE,
    (byte)0, (byte)WKPF.PROFILE_THRESHOLD,

    (byte)0, (byte)COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, (byte)WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT,
    (byte)0, (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)WKPF.PROPERTY_THRESHOLD_THRESHOLD,
    (byte)0, (byte)WKPF.PROFILE_THRESHOLD,
    
    (byte)0, (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)WKPF.PROPERTY_THRESHOLD_OUTPUT,
    (byte)0, (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_IN1,
    (byte)0, (byte)VirtualANDGateProfile.PROFILE_AND_GATE,

    (byte)0, (byte)COMPONENT_INSTANCE_ID_OCCUPANCY1, (byte)VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED,
    (byte)0, (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_IN2,
    (byte)0, (byte)VirtualANDGateProfile.PROFILE_AND_GATE,

    (byte)0, (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_OUTPUT,
    (byte)0, (byte)COMPONENT_INSTANCE_ID_LIGHT1, (byte)WKPF.PROPERTY_LIGHT_ONOFF,
    (byte)0, (byte)WKPF.PROFILE_LIGHT
  };
  
  public static void main(String[] args) {
    System.out.println("HAScenario 2");
    
    myNodeId = WKPF.getMyNodeId();    
    System.out.println("MY NODE ID: " + myNodeId);

    WKPF.loadComponentToEndpointMap(componentInstanceToEndpointMap);
    System.out.println("Registering component to endpoint map: " + WKPF.getErrorCode());
    
    WKPF.loadLinkDefinitions(linkDefinitions);
    System.out.println("Registering link definitions: " + WKPF.getErrorCode());

    // ----- REGISTER VIRTUAL PROFILES -----
    // Won't work now since we already have a native profile
    // WKPF.registerProfile((short)WKPF.PROFILE_THRESHOLD, VirtualThresholdProfile.properties);

    // ----- INIT -----
    // INITIAL STATIC VERSION: This should later be replaced by return value from WKPF.wait so the framework can dynamically allocate a new profile
    // Register Occupancy sensor and AND gate profiles.
    if (isLocalComponent(COMPONENT_INSTANCE_ID_LIGHTSENSOR1)) {
      WKPF.setPropertyShort((short)COMPONENT_INSTANCE_ID_LIGHTSENSOR1, WKPF.PROPERTY_COMMON_REFRESHRATE, (short)5000); // Sample the light every 5 seconds  (doesn't work yet)
    }

    if (isLocalComponent(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1)) {
      WKPF.setPropertyShort((short)COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT, (short)127); // Default threshold 127
    }

    if (isLocalComponent(COMPONENT_INSTANCE_ID_OCCUPANCY1)) {
      WKPF.registerProfile(VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, VirtualOccupancySensorProfile.properties);
      VirtualProfile profileInstanceOccupancy = new VirtualOccupancySensorProfile();
      WKPF.createEndpoint((short)VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, getPortNumberForComponent(COMPONENT_INSTANCE_ID_OCCUPANCY1), profileInstanceOccupancy);
      WKPF.setPropertyBoolean((short)COMPONENT_INSTANCE_ID_OCCUPANCY1, VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED, true); // Default occupied
    }
    
    if (isLocalComponent(COMPONENT_INSTANCE_ID_THRESHOLD1)) {
      WKPF.createEndpoint((short)WKPF.PROFILE_THRESHOLD, getPortNumberForComponent(COMPONENT_INSTANCE_ID_THRESHOLD1), null);
      WKPF.setPropertyShort((short)COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_OPERATOR, VirtualThresholdProfile.OPERATOR_LTE); // Threshold operator: <=      
    }
    
    if (isLocalComponent(COMPONENT_INSTANCE_ID_ANDGATE1)) {
      WKPF.registerProfile(VirtualANDGateProfile.PROFILE_AND_GATE, VirtualANDGateProfile.properties);
      VirtualProfile profileInstanceANDGate = new VirtualANDGateProfile();
      WKPF.createEndpoint((short)VirtualANDGateProfile.PROFILE_AND_GATE, getPortNumberForComponent(COMPONENT_INSTANCE_ID_ANDGATE1), profileInstanceANDGate);
    }

    // ----- MAIN LOOP -----
    System.out.println("HAScenario - Entering main loop");
    while(true) {
      VirtualProfile profile = WKPF.select();
      if (profile != null) {
        profile.update();
      }
      
      // TODONR: Temporarily write to a dummy property to trigger updates while don't have a scheduling mechanism yet.
      if (isLocalComponent(COMPONENT_INSTANCE_ID_LIGHTSENSOR1)) { 
        tmpDummy += 1;
        System.out.println("HAScenario - updating dummy variable to trigger lightsensor update ");
        WKPF.setPropertyShort((short)COMPONENT_INSTANCE_ID_LIGHTSENSOR1, (byte)(WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE+1), tmpDummy);
        if (WKPF.getErrorCode() != WKPF.OK)
          System.out.println("Error: " + WKPF.getErrorCode());
      }
      Timer.wait(1000);
    }
  }
}
