import java.io.*;
import nanovm.avr.*;
import nanovm.wkpf.*;
import nanovm.lang.Math;

public class HAScenario2 {
  // =========== Begin: Constant part, not affected by the application.
  private static int myNodeId;

  // TODONR: these could be changed to native methods for performance reasons (but they're only used in initialisation, so it's not too important)
  private static byte getPortNumberForComponent(short componentId) {
    return componentInstanceToEndpointMap[componentId*2 + 1];
  }
  private static boolean isLocalComponent(short componentId) {    
    int nodeId=componentInstanceToEndpointMap[componentId*2];
    return nodeId == myNodeId;
  }
  // =========== End: Constant part, not affected by the application.
  
  // =========== Begin: Generated by the compiler from application WuML
  private static final short COMPONENT_INSTANCE_ID_INPUTCONTROLLER1 = 0;
  private static final short COMPONENT_INSTANCE_ID_LIGHTSENSOR1 = 1;
  private static final short COMPONENT_INSTANCE_ID_THRESHOLD1 = 2;
  private static final short COMPONENT_INSTANCE_ID_LIGHT1 = 3;
  private static final short COMPONENT_INSTANCE_ID_OCCUPANCY1 = 4;
  private static final short COMPONENT_INSTANCE_ID_ANDGATE1 = 5;

  private final static byte[] componentInstanceToEndpointMap = { // Indexed by component instance id.
    (byte)1, (byte)0x1, // Component 0: input controller    @ node 1, port 1
    (byte)1, (byte)0x2, // Component 1: light sensor        @ node 1, port 2
    (byte)3, (byte)0x3, // Component 2: threshold           @ node 3, port 3
    (byte)3, (byte)0x4, // Component 3: light               @ node 3, port 4
    (byte)1, (byte)0x5, // Component 4: occupancy           @ node 1, port 5
    (byte)3, (byte)0x6  // Component 5: and gate            @ node 3, port 6
  };


  private final static byte[] linkDefinitions = { // Note: Component instance id and profile id are little endian
    // Note: using WKPF constants now, but this should be generated as literal bytes by the WuML->Java compiler.
    // Connect input controller to threshold
    (byte)COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, (byte)0, (byte)WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT,
    (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)0, (byte)WKPF.PROPERTY_THRESHOLD_THRESHOLD,
    (byte)WKPF.PROFILE_THRESHOLD, (byte)0,

    // Connect light sensor to threshold
    (byte)COMPONENT_INSTANCE_ID_LIGHTSENSOR1, (byte)0, (byte)WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE,
    (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)0, (byte)WKPF.PROPERTY_THRESHOLD_VALUE,
    (byte)WKPF.PROFILE_THRESHOLD, (byte)0,

    // Connect threshold to and gate
    (byte)COMPONENT_INSTANCE_ID_THRESHOLD1, (byte)0, (byte)WKPF.PROPERTY_THRESHOLD_OUTPUT,
    (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)0, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_IN1,
    (byte)VirtualANDGateProfile.PROFILE_AND_GATE, (byte)0,

    // Connect occupancy to and gate
    (byte)COMPONENT_INSTANCE_ID_OCCUPANCY1, (byte)0, (byte)VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED,
    (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)0, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_IN2,
    (byte)VirtualANDGateProfile.PROFILE_AND_GATE, (byte)0,

    // Connect and gate to light
    (byte)COMPONENT_INSTANCE_ID_ANDGATE1, (byte)0, (byte)VirtualANDGateProfile.PROPERTY_AND_GATE_OUTPUT,
    (byte)COMPONENT_INSTANCE_ID_LIGHT1, (byte)0, (byte)WKPF.PROPERTY_LIGHT_ONOFF,
    (byte)WKPF.PROFILE_LIGHT, (byte)0
  };


  private static short tmpDummy = 0;  
  public static void main(String[] args) {
    System.out.println("HAScenario 2");

    myNodeId = WKPF.getMyNodeId();
    System.out.println("MY NODE ID:" + myNodeId);

    WKPF.loadComponentToEndpointMap(componentInstanceToEndpointMap);
    if (WKPF.getErrorCode() == WKPF.OK)
      System.out.println("Registered component to endpoint map.");
    else
      System.out.println("Error while registering component to endpoint map: " + WKPF.getErrorCode());
    
    WKPF.loadLinkDefinitions(linkDefinitions);
    if (WKPF.getErrorCode() == WKPF.OK)
      System.out.println("Registered link definitions.");
    else
      System.out.println("Error while Registering link definitions: " + WKPF.getErrorCode());
      
    // ----- INIT -----
    // INITIAL STATIC VERSION: This should later be replaced by return value from WKPF.wait so the framework can dynamically allocate a new profile
    // Setup the temperature sensor
    if (isLocalComponent(COMPONENT_INSTANCE_ID_LIGHTSENSOR1)) { 
      WKPF.setPropertyShort(COMPONENT_INSTANCE_ID_LIGHTSENSOR1, WKPF.PROPERTY_COMMON_REFRESHRATE, (short)5000); // Sample the temperature every 5 seconds
    }
    // Setup the numeric input
    if (isLocalComponent(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1)) { 
      WKPF.setPropertyShort(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT, (short)127); // Default threshold: 127
    }
    // Create and setup the threshold endpoint
    if (isLocalComponent(COMPONENT_INSTANCE_ID_THRESHOLD1)) {
      WKPF.createEndpoint((short)WKPF.PROFILE_THRESHOLD, getPortNumberForComponent(COMPONENT_INSTANCE_ID_THRESHOLD1), null);
      WKPF.setPropertyShort(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_OPERATOR, WKPF.PROPERTY_THRESHOLD_OPERATOR_LTE); // Threshold operator: <=
    }
    // Setup the light
    if (isLocalComponent(COMPONENT_INSTANCE_ID_LIGHT1)) {
      // Native, builtin endpoint, no need to create.
    }
    // Register virtual and gate profile and create an endpoint
    if (isLocalComponent(COMPONENT_INSTANCE_ID_ANDGATE1)) {
      WKPF.registerProfile(VirtualANDGateProfile.PROFILE_AND_GATE, VirtualANDGateProfile.properties);
      VirtualProfile profileInstanceANDGate = new VirtualANDGateProfile();
      WKPF.createEndpoint((short)VirtualANDGateProfile.PROFILE_AND_GATE, getPortNumberForComponent(COMPONENT_INSTANCE_ID_ANDGATE1), profileInstanceANDGate);
    }
    // Register virtual occupancy sensor profile and create an endpoint
    if (isLocalComponent(COMPONENT_INSTANCE_ID_OCCUPANCY1)) {
      WKPF.registerProfile(VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, VirtualOccupancySensorProfile.properties);
      VirtualProfile profileInstanceOccupancy = new VirtualOccupancySensorProfile();
      WKPF.createEndpoint((short)VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, getPortNumberForComponent(COMPONENT_INSTANCE_ID_OCCUPANCY1), profileInstanceOccupancy);
      WKPF.setPropertyBoolean(COMPONENT_INSTANCE_ID_OCCUPANCY1, VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED, true); // Default: occupied
    }
    // =========== End: Generated by the compiler from application WuML

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
        System.out.println("HAScenario - updating dummy variable to trigger lightsensor update: " + tmpDummy);
        WKPF.setPropertyShort(COMPONENT_INSTANCE_ID_LIGHTSENSOR1, (byte)(WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE+1), tmpDummy);
        System.out.println("HAScenario - updating dummy variable to trigger lightsensor update, result: " + WKPF.getErrorCode());
        if (WKPF.getErrorCode() != WKPF.OK)
          System.out.println("Error: " + WKPF.getErrorCode());
      }
      Timer.wait(1000);
      // END: Temporarily write to a dummy property to trigger updates while don't have a scheduling mechanism yet.
    }
  }
}
