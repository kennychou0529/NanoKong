import nanovm.avr.*;
import nanovm.io.*;

class IntelDemoLampController {
  private static final byte COMMAND_SET_LAMP = 1;
  private static final short COMMAND_SET_LAMP_ACK = 11;

  public static void main(String[] args) {
    AVR.portB.setOutput(0);
    AVR.portB.clrBit(0);
    while(true) {
      System.out.println("Waiting for data.....");
      byte[] data = NvmComm.receive(1000);
      if (data != null && data.length == 2 && data[0] == COMMAND_SET_LAMP) {
        if (data[1] == 0) {
          AVR.portB.clrBit(0);
          System.out.println("Turning lamp off");
        }
        else {
          AVR.portB.setBit(0);
          System.out.println("Turning lamp on");
        }
        byte[] reply = new byte[] {COMMAND_SET_LAMP_ACK};
        NvmComm.send((byte)1, reply, (byte)1);
      }
    }
  }
}