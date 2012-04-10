#include "config.h"
#include "types.h"
#include "debug.h"
#include "wkpf.h"
#include "wkpf_endpoints.h"

#define MAX_NUMBER_OF_ENDPOINTS 10
uint8_t number_of_endpoints;
wkpf_local_endpoint endpoints[MAX_NUMBER_OF_ENDPOINTS];

uint8_t wkpf_create_endpoint(wkpf_profile_definition *profile, uint8_t port_number) {
  if (number_of_endpoints == MAX_NUMBER_OF_ENDPOINTS) {
    DEBUGF_WKPF("WKPF: out of memory while creating endpoint for profile %x at port: FAILED\n", profile->profile_id, port_number);
    return WKPF_ERR_OUT_OF_MEMORY;
  }
  for (int8_t i=0; i<number_of_endpoints; i++) {
    if (endpoints[i].port_number == port_number) {
      DEBUGF_WKPF("WKPF: port %x in use while creating endpoint for profile id %x: FAILED\n", port_number, profile->profile_id);
      return WKPF_ERR_PORT_IN_USE;
    }
  }
  DEBUGF_WKPF("WKPF: creating endpoint for profile id %x at port %x\n", profile->profile_id, port_number);
  endpoints[number_of_endpoints].profile = profile;
  endpoints[number_of_endpoints].port_number = port_number;
  number_of_endpoints++;
  return WKPF_OK;  
}

uint8_t wkpf_remove_endpoint(uint8_t port_number) {
  for (int8_t i=0; i<number_of_endpoints; i++) {
    if (endpoints[i].port_number == port_number) {
      // Endpoint at index i will be removed:
      // Move endpoints at higher indexes on index down
      for (int8_t j=i+1; j<number_of_endpoints; j++) {
        endpoints[j-1] = endpoints[j];
      }
      number_of_endpoints--;
      return WKPF_OK;
    }
  }
  DEBUGF_WKPF("WKPF: no endpoint at port %x found: FAILED\n", port_number);
  return WKPF_ERR_ENDPOINT_NOT_FOUND;  
}

uint8_t wkpf_get_endpoint_by_port(uint8_t port_number, wkpf_local_endpoint **endpoint) {
  for (int8_t i=0; i<number_of_endpoints; i++) {
    if (endpoints[i].port_number == port_number) {
      *endpoint = &endpoints[i];
      return WKPF_OK;
    }
  }
  DEBUGF_WKPF("WKPF: no endpoint at port %x found: FAILED\n", port_number);
  return WKPF_ERR_ENDPOINT_NOT_FOUND;
}

uint8_t wkpf_get_endpoint_by_index(uint8_t index, wkpf_local_endpoint **endpoint) {
  if (index >= number_of_endpoints) {
    DEBUGF_WKPF("WKPF: no endpoint at index %x found: FAILED\n", index);
    return WKPF_ERR_ENDPOINT_NOT_FOUND;
  }
  *endpoint = &endpoints[index];
  return WKPF_OK;  
}

uint8_t wkpf_get_number_of_endpoints() {
  return number_of_endpoints;
}