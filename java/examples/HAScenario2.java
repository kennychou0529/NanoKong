import java.io.*;
import nanovm.avr.*;
import nanovm.wkpf.*;
import nanovm.lang.Math;

public class HAScenario2 {
  // =========== Constant part, not affected by the application.
  private static int myNodeId;

  private static boolean matchDirtyProperty(int componentInstanceId, byte propertyNumber) {
    Endpoint endpoint = ComponentInstancetoEndpoint(componentInstanceId);
    return endpoint.nodeId == myNodeId
        && endpoint.portNumber == WKPF.getDirtyPropertyPortNumber()
        && propertyNumber == WKPF.getDirtyPropertyNumber();
  }
  private static void setPropertyShort(int componentInstanceId, byte propertyNumber, short value) {      
      Endpoint endpoint = ComponentInstancetoEndpoint(componentInstanceId);
      WKPF.setPropertyShort(endpoint.nodeId, endpoint.portNumber, propertyNumber, endpoint.profileId, value);
  }
  private static void setPropertyBoolean(int componentInstanceId, byte propertyNumber, boolean value) {
      Endpoint endpoint = ComponentInstancetoEndpoint(componentInstanceId);
      WKPF.setPropertyBoolean(endpoint.nodeId, endpoint.portNumber, propertyNumber, endpoint.profileId, value);
  }

  public static Endpoint ComponentInstancetoEndpoint(int componentInstanceId) {
    // INITIAL STATIC VERSION: This could later be replaced by something more dynamic, for now the table is a hardcoded constant
    Endpoint endpoint = new Endpoint();
    endpoint.nodeId=componentInstanceToEndpointMapping_nodeId[componentInstanceId];
    endpoint.portNumber=componentInstanceToEndpointMapping_portNumber[componentInstanceId];
    endpoint.profileId=(short)componentInstanceToEndpointMapping_profileId[componentInstanceId];
    return endpoint;
  }

  // =========== Generated by the compiler
  private static final int COMPONENT_INSTANCE_ID_INPUTCONTROLLER1 = 0;
  private static final int COMPONENT_INSTANCE_ID_LIGHTSENSOR1 = 1;
  private static final int COMPONENT_INSTANCE_ID_THRESHOLD1 = 2;
  private static final int COMPONENT_INSTANCE_ID_LIGHT1 = 3;
  private static final int COMPONENT_INSTANCE_ID_OCCUPANCY1 = 4;
  private static final int COMPONENT_INSTANCE_ID_ANDGATE1 = 5;
  
  private static int lastPropagatedValue;
  private static short tmpDummy = 0;
  
  private static final byte[] componentInstanceToEndpointMapping_nodeId = { // Indexed by component instance id.
    (byte)1, // Input
    (byte)1, // Light sensor
    (byte)3, // Threshold
    (byte)3, // Light    
    (byte)1, // Occupancy    
    (byte)3, // And gate    
  };
  private static final byte[] componentInstanceToEndpointMapping_portNumber = { // Indexed by component instance id.
    (byte)1, // Input
    (byte)2, // Light sensor
    (byte)3, // Threshold
    (byte)4, // Light    
    (byte)5, // Occupancy    
    (byte)6, // And gate    
  };
  private static final int[] componentInstanceToEndpointMapping_profileId = { // Indexed by component instance id.
    WKPF.PROFILE_NUMERIC_CONTROLLER, // Input
    WKPF.PROFILE_LIGHT_SENSOR, // Temperature sensor
    WKPF.PROFILE_THRESHOLD, // Threshold
    WKPF.PROFILE_LIGHT, // Light
    VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, // Occupancy
    VirtualANDGateProfile.PROFILE_AND_GATE // And gate
  };
  
  public static void main(String[] args) {
    System.out.println("HAScenario 2");
    
    myNodeId = WKPF.getMyNodeId();
    
    System.out.println("MY NODE ID:" + myNodeId);

    // ----- REGISTER VIRTUAL PROFILES -----
    // Won't work now since we already have a native profile
    // WKPF.registerProfile((short)WKPF.PROFILE_THRESHOLD, VirtualThresholdProfile.properties, (byte)VirtualThresholdProfile.properties.length);


    // ----- INIT -----
    // INITIAL STATIC VERSION: This should later be replaced by return value from WKPF.wait so the framework can dynamically allocate a new profile
    // Register Occupancy sensor and AND gate profiles.
    WKPF.registerProfile(VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, VirtualOccupancySensorProfile.properties, (byte)VirtualOccupancySensorProfile.properties.length); // TODONR: numberOfProperties shouldn't be necessary, but I can't figure out how to get the array size in native code (need heap ID)
    WKPF.registerProfile(VirtualANDGateProfile.PROFILE_AND_GATE, VirtualANDGateProfile.properties, (byte)VirtualANDGateProfile.properties.length); // TODONR: numberOfProperties shouldn't be necessary, but I can't figure out how to get the array size in native code (need heap ID)
    
    // Setup the temperature sensor
    if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_LIGHTSENSOR1).nodeId == myNodeId) { 
      setPropertyShort(COMPONENT_INSTANCE_ID_LIGHTSENSOR1, WKPF.PROPERTY_COMMON_REFRESHRATE, (short)5000); // Sample the temperature every 5 seconds
    }
    // Setup the numeric input
    if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1).nodeId == myNodeId) { 
      setPropertyShort(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT, (short)127); // Sample the temperature every 5 seconds
    }
    // Create and setup the threshold
    if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_THRESHOLD1).nodeId == myNodeId) {
      WKPF.createEndpoint((short)WKPF.PROFILE_THRESHOLD, ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_THRESHOLD1).portNumber, null);
      setPropertyShort(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_OPERATOR, VirtualThresholdProfile.OPERATOR_LTE); // Sample the temperature every 5 seconds
    }
    // Create and setup the occupancy sensor
    if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_OCCUPANCY1).nodeId == myNodeId) {
      VirtualProfile profileInstanceOccupancy = new VirtualOccupancySensorProfile();
      WKPF.createEndpoint((short)VirtualOccupancySensorProfile.PROFILE_OCCUPANCY_SENSOR, ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_OCCUPANCY1).portNumber, profileInstanceOccupancy);
      // Default occupied
      setPropertyBoolean(COMPONENT_INSTANCE_ID_OCCUPANCY1, VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED, true);
    }
    // Create and setup the AND gate
    if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_ANDGATE1).nodeId == myNodeId) {
      VirtualProfile profileInstanceANDGate = new VirtualANDGateProfile();
      WKPF.createEndpoint((short)VirtualANDGateProfile.PROFILE_AND_GATE, ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_ANDGATE1).portNumber, profileInstanceANDGate);
    }

    // ----- MAIN LOOP -----
    System.out.println("HAScenario - Entering main loop");
    while(true) {
      VirtualProfile profile = WKPF.select();
      if (profile != null) {
        profile.update();
      }
      propagateDirtyProperties();
      
      // TODONR: Temporarily write to a dummy property to trigger updates while don't have a scheduling mechanism yet.
      if (ComponentInstancetoEndpoint(COMPONENT_INSTANCE_ID_LIGHTSENSOR1).nodeId == myNodeId) { 
        tmpDummy += 1;
        System.out.println("HAScenario - updating dummy variable to trigger lightsensor update ");
        setPropertyShort(COMPONENT_INSTANCE_ID_LIGHTSENSOR1, (byte)(WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE+1), tmpDummy);
        if (WKPF.getErrorCode() != WKPF.OK)
          System.out.println("Error: " + WKPF.getErrorCode());
      }
      Timer.wait(1000);
    }
  }

  public static void propagateDirtyProperties() {
    System.out.println("HAScenario - start propagateDirtyProperties");
    while(WKPF.loadNextDirtyProperty()) {
      
      if (matchDirtyProperty(COMPONENT_INSTANCE_ID_LIGHTSENSOR1, WKPF.PROPERTY_LIGHT_SENSOR_CURRENT_VALUE)) {
        System.out.println("HAScenario - propagating lightsensor.currentvalue -> threshold.input");

/*  TODONR: Math.abs doesn't work
      short value = WKPF.getDirtyPropertyShortValue();
        if (Math.abs(lastPropagatedValue - value) > 2) {
          lastPropagatedValue = value;
          setPropertyShort(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_VALUE, value);
        } */
      setPropertyShort(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_VALUE, WKPF.getDirtyPropertyShortValue());
      
      } else if (matchDirtyProperty(COMPONENT_INSTANCE_ID_INPUTCONTROLLER1, WKPF.PROPERTY_NUMERIC_CONTROLLER_OUTPUT)) {
        System.out.println("HAScenario - propagating numericcontroller.output -> threshold.threshold");
        setPropertyShort(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_THRESHOLD, WKPF.getDirtyPropertyShortValue());

      } else if (matchDirtyProperty(COMPONENT_INSTANCE_ID_THRESHOLD1, WKPF.PROPERTY_THRESHOLD_OUTPUT)) {
        System.out.println("HAScenario - propagating threshold.output -> andgate.in1");
        setPropertyBoolean(COMPONENT_INSTANCE_ID_ANDGATE1, VirtualANDGateProfile.PROPERTY_AND_GATE_IN1, WKPF.getDirtyPropertyBooleanValue());

      } else if (matchDirtyProperty(COMPONENT_INSTANCE_ID_OCCUPANCY1, VirtualOccupancySensorProfile.PROPERTY_OCCUPANCY_SENSOR_OCCUPIED)) {
        System.out.println("HAScenario - propagating occupancysensor.occupied -> andgate.in2");
        setPropertyBoolean(COMPONENT_INSTANCE_ID_ANDGATE1, VirtualANDGateProfile.PROPERTY_AND_GATE_IN2, WKPF.getDirtyPropertyBooleanValue());

      } else if (matchDirtyProperty(COMPONENT_INSTANCE_ID_ANDGATE1, VirtualANDGateProfile.PROPERTY_AND_GATE_OUTPUT)) {
        System.out.println("HAScenario - propagating andgate.output -> light.onoff");
        setPropertyBoolean(COMPONENT_INSTANCE_ID_LIGHT1, WKPF.PROPERTY_LIGHT_ONOFF, WKPF.getDirtyPropertyBooleanValue());
      }
    }
    System.out.println("HAScenario - end propagateDirtyProperties");
  }
}
