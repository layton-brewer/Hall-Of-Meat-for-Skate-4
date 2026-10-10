#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint64_t u64;
#define MIX(a,b,c) \
 a-=b;a-=c;a^=(c>>43); b-=c;b-=a;b^=(a<<9); c-=a;c-=b;c^=(b>>8); \
 a-=b;a-=c;a^=(c>>38); b-=c;b-=a;b^=(a<<23); c-=a;c-=b;c^=(b>>5); \
 a-=b;a-=c;a^=(c>>35); b-=c;b-=a;b^=(a<<49); c-=a;c-=b;c^=(b>>11); \
 a-=b;a-=c;a^=(c>>12); b-=c;b-=a;b^=(a<<18); c-=a;c-=b;c^=(b>>22);
static u64 h64(const unsigned char*k,int n){u64 a=0xABCDEF0011223344ULL,b=a,c=0x9E3779B97F4A7C13ULL;int i=0;
 while(n-i>=24){u64 x,y,z;memcpy(&x,k+i,8);memcpy(&y,k+i+8,8);memcpy(&z,k+i+16,8);a+=x;b+=y;c+=z;MIX(a,b,c);i+=24;}
 c+=n;int r=n-i;for(int j=0;j<r;j++){u64 ch=k[i+j];if(j>=16)c+=ch<<(8*(j-16+1));else if(j>=8)b+=ch<<(8*(j-8));else a+=ch<<(8*j);}
 MIX(a,b,c);return c;}
u64 tg[4096];int nt;char *w[4096];int nw;
static int cmp(const void*x,const void*y){u64 a=*(u64*)x,b=*(u64*)y;return a<b?-1:a>b;}
static int has(u64 h){int lo=0,hi=nt-1;while(lo<=hi){int m=(lo+hi)/2;if(tg[m]==h)return 1;if(tg[m]<h)lo=m+1;else hi=m-1;}return 0;}
char buf[512];
static void test(int n){u64 h=h64((unsigned char*)buf,n);if(has(h))printf("%016llx %.*s\n",(unsigned long long)h,n,buf);}
int main(int argc,char**argv){FILE*f=fopen(argv[1],"r");char line[256];while(fgets(line,256,f)){tg[nt++]=strtoull(line,0,16);}qsort(tg,nt,8,cmp);
 f=fopen(argv[2],"r");while(fgets(line,256,f)){line[strcspn(line,"\r\n")]=0;if(*line)w[nw++]=strdup(line);}
 int depth=atoi(argv[3]); const char*seps[]={"_","","::"," "}; int nsep=argc>4?atoi(argv[4]):2;
 /* words provided in desired case; caller supplies lower and Capitalized variants */
 for(int s=0;s<nsep;s++){const char*sp=seps[s];int sl=strlen(sp);
  for(int i=0;i<nw;i++){int l1=strlen(w[i]);memcpy(buf,w[i],l1);if(s==0)test(l1);
   if(depth<2)continue;
   for(int j=0;j<nw;j++){int p=l1;memcpy(buf+p,sp,sl);p+=sl;int l2=strlen(w[j]);memcpy(buf+p,w[j],l2);p+=l2;test(p);
    if(depth<3)continue;
    for(int k=0;k<nw;k++){int q=p;memcpy(buf+q,sp,sl);q+=sl;int l3=strlen(w[k]);memcpy(buf+q,w[k],l3);q+=l3;test(q);
     if(depth<4)continue;
     for(int m=0;m<nw;m++){int r=q;memcpy(buf+r,sp,sl);r+=sl;int l4=strlen(w[m]);memcpy(buf+r,w[m],l4);r+=l4;test(r);}
    }}}}
 return 0;}
