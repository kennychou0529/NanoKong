//
// config.h
//
// NanoVM configuration file for the avr atmega8 test board
//

#ifndef CONFIG_H
#define CONFIG_H

// cpu related setup
#define ATMEGA2560
#define CLOCK 16000000

#define CODESIZE 0x7E00
#define HEAPSIZE 768

// avr specific native init routines
#define NATIVE_INIT  native_init()

// enable debug info
#define DEBUG
//#define DEBUG_WIRELESS_TRACE
#define DEBUG_WIRELESS_TRACE_TARGET_NODE_ID 2
// enable logging info
//#define LOGGING

// enable simple unittests for wuclass framework (choose 1)
//#define TEST_WKPF_WUCLASSES
//#define TEST_WKPF_WUOBJECTS
//#define TEST_WKPF_PROPERTIES
//#define TEST_WKPF_NATIVE_WUCLASSES
//#define TEST_WKPF_UPDATE_FOR_NATIVE_WUCLASSES
//#define TEST_WKPF_LOGICAL_WUCLASSES
//#define TEST_WKPF_CONFIGURATION
#if defined(TEST_WKPF_WUCLASSES) || defined(TEST_WKPF_WUOBJECTS) || defined(TEST_WKPF_PROPERTIES) || defined(TEST_WKPF_NATIVE_WUCLASSES) || defined(TEST_WKPF_UPDATE_FOR_NATIVE_WUCLASSES) || defined(TEST_WKPF_LOGICAL_WUCLASSES) || defined(TEST_WKPF_CONFIGURATION)
//#define TEST_WKPF // General WKPF test support
#endif

//#define TEST_GROUP // Virtual Synchrony test support

// vm setup
#undef NVM_USE_STACK_CHECK      // enable check if method returns empty stack
#define NVM_USE_ARRAY           // enable arrays
#define NVM_USE_OBJ_ARRAY       // enable object arrays
#define NVM_USE_SWITCH          // support switch instruction
#define NVM_USE_INHERITANCE     // support for inheritance
#define NVM_USE_UTILS           // enable inline utils
#define NVM_USE_MEMCPY_UP       // enable custom memcpy for heap compacting
#define NVM_USE_COMM
#define NVM_USE_COMMZWAVE       // enable Z-wave support
#define NVM_USE_GROUP           // enable virtually synchronous process group
//#define NVM_USE_COMMXBEE        // enable XBee support
// bytecode location (choose one)
#define NVM_USE_FLASH_PROGRAM	// execute directly from FLASH
#define NVM_USE_FLASH_PROGRAM_INLINE	// execute directly from FLASH
//#define NVM_USE_RAM_PROGRAM		// copy to RAM at startup

// native setup
#define NVM_USE_STDIO           // enable native stdio support

// marker used to indicate, that this item is stored in flash
#define NVMFILE_FLAG     0x8000

// uart setup
#define UART_BAUDRATE 115200      // default UART bitrate
#define UART_BUFFER_BITS 5       // 32 bytes buffer (min. req for loader)
#ifdef NVM_USE_COMMZWAVE
#define ZWAVE_UART_BAUDRATE 115200 // bitrate for Z-Wave board
#endif

#endif // CONFIG_H
