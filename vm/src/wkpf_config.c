#include <string.h>
#include <eeprom.h>
#include "debug.h"
#include "wkpf.h"
#include "wkpf_config.h"

#define WKPF_FEATURE_ARRAY_SIZE           (WKPF_MAX_FEATURE_NUMBER/8 + 1)

static char EEPROM eeprom_location[LOCATION_MAX_LENGTH] = ""; // Currently can only handle locations that fit into a single message
static uint8_t EEPROM eeprom_wkpf_features[WKPF_FEATURE_ARRAY_SIZE];
static uint8_t EEPROM eeprom_master_address;

#define load_location_length() eeprom_read_byte((u08_t*)&eeprom_location_length)
#define save_location_length(x) eeprom_update_byte((u08_t*)&eeprom_location_length, (u08_t)x)
#define load_location(dest, offset, length) eeprom_read_block((void*)dest, (const void*)(eeprom_location+offset), length)
#define save_location(src, offset, length) eeprom_update_block((const void*)src, (void*)(eeprom_location+offset), length)
#define feat_addr(feature) &eeprom_wkpf_features[feature / 8]
#define enable_feature(feature) eeprom_update_byte(feat_addr(feature), eeprom_read_byte(feat_addr(feature)) | (1<<(feature % 8)))
#define disable_feature(feature) eeprom_update_byte(feat_addr(feature), eeprom_read_byte(feat_addr(feature)) & ~(1<<(feature % 8)))
#define get_feature_enabled(feature) (eeprom_read_byte(feat_addr(feature)) & (1<<(feature % 8)))
#define load_master_node_id() eeprom_read_byte((u08_t*)&eeprom_master_address)
#define save_master_node_id(x) eeprom_update_byte((u08_t*)&eeprom_master_address, (u08_t)x)


// Stores a part of the location in EEPROM, or returns WKPF_ERR_LOCATION_TOO_LONG if the string is too long.
uint8_t wkpf_config_set_part_of_location_string(char* src, uint8_t offset, uint8_t length) {
  if (offset + length > LOCATION_MAX_LENGTH)
    return WKPF_ERR_LOCATION_TOO_LONG;

  save_location(src, offset, length);
  return WKPF_OK;
}

// Retrieves a part the location from EEPROM and stores it in dest.
uint8_t wkpf_config_get_part_of_location_string(char* dest, uint8_t offset, uint8_t length) {
  // If we're trying to read too many bytes, return the number of bytes that could be read.
  if (offset + length > LOCATION_MAX_LENGTH) {
    if (offset >= LOCATION_MAX_LENGTH)
      length = 0;
    else
      length = LOCATION_MAX_LENGTH - offset;
  }

  load_location(dest, offset, length);
  return length;
}

uint8_t wkpf_config_set_feature_enabled(uint8_t feature, bool enabled) {
  if (feature > WKPF_MAX_FEATURE_NUMBER)
    return WKPF_ERR_UNKNOWN_FEATURE;
  if (enabled)
    enable_feature(feature);
  else
    disable_feature(feature);
  return WKPF_OK;
}

bool wkpf_config_get_feature_enabled(uint8_t feature) {
  return feature <= WKPF_MAX_FEATURE_NUMBER
          && get_feature_enabled(feature) > 0;
}

address_t wkpf_config_get_master_node_id() {
  return (address_t)load_master_node_id();
}

void wkpf_config_set_master_node_id(address_t node_id) {
  if (sizeof(address_t) != 1) {
    // Bit crude: just enter an endless loop when address_t is changed to a bigger datatype because that means we need to change this function as well.
    // This way uploading new code won't work (as long as we call this when receiving NVMCOMM_CMD_REPRG_OPEN) until this function is fixed.
    // The alternative would be hard to find bugs when one byte of the node_id is lost.
    while(1);
  }
  save_master_node_id(node_id);
}
