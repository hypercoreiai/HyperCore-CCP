#include "hypercore/hypercore_api.h"
#include <stdio.h>
int main(){ printf("caps=%zu request_config=%zu summary=%zu chunk=%zu\n", sizeof(hypercore_caps_t), sizeof(hypercore_request_config_t), sizeof(hypercore_request_summary_t), sizeof(hypercore_output_chunk_t)); return 0; }
