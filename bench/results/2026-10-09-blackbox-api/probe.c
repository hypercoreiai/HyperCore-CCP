#define _POSIX_C_SOURCE 200809L
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>
#include <time.h>
static int toks=0, term=0;
static void cb(const hypercore_output_chunk_t* c, void* u){
  (void)u;
  if(c->token_id>=0){toks++;return;}
  term=1; printf("terminal: struct_size=%u decode_ms=%llu produced=%u offered=%u accepted=%u stop=%d\n",
    c->summary?c->summary->struct_size:0,
    c->summary?(unsigned long long)c->summary->decode_ms:0,
    c->summary?c->summary->produced_tokens:0,
    c->summary?c->summary->drafts_offered:0,
    c->summary?c->summary->drafts_accepted:0,
    c->summary?(int)c->summary->stop_reason:-1);
}
int main(){
  hypercore_engine_t* e=NULL;
  printf("init=%d\n", (int)hypercore_engine_init(&e,"{\"pcie_frac\":0.25,\"spec_min_p\":0.5}"));
  hypercore_request_config_t cfg; memset(&cfg,0,sizeof cfg);
  cfg.struct_size=sizeof cfg; cfg.temperature=1.0f; cfg.top_p=1.0f; cfg.top_k=8; cfg.max_new_tokens=20;
  cfg.pcie_frac=-1.0f; cfg.spec_min_p=-1.0f;
  int32_t p[6]={1,2,3,4,5,6};
  printf("submit=%d\n",(int)hypercore_engine_submit(e,1,&cfg,p,6,cb,NULL));
  while(!term){ struct timespec ts={0,1000000}; nanosleep(&ts,NULL); }
  printf("tokens=%d\n",toks);
  hypercore_engine_destroy(e);
  printf("destroyed\n");
  return 0;
}
