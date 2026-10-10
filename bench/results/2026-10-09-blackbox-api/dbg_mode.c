#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <unistd.h>
static void cb(const hypercore_output_chunk_t* c, void* u){ (void)c;(void)u; }
int main(void){
  hypercore_engine_t* e=NULL;
  const char* cfg="{\"engine_mode\":\"worker\",\"worker_binary\":\"/home/ai-user0/HyperCore/build-shared/hypercore-worker\",\"ipc_socket\":\"/tmp/hc_dbg.sock\",\"batch\":2}";
  int st = hypercore_engine_init(&e, cfg);
  printf("init=%d\n", st);
  if(st) return 1;
  hypercore_request_config_t c={0}; c.struct_size=sizeof c; c.max_new_tokens=8; c.top_k=1;
  int32_t p[6]={1,2,3,1,2,3};
  int s = hypercore_engine_submit(e, 1, &c, p, 6, cb, NULL);
  printf("submit=%d\n", s);
  hypercore_engine_destroy(e);
  return 0;
}
