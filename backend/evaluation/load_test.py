"""Load test ringan tanpa dependensi tambahan; jalankan terhadap backend khusus uji."""
import argparse,json,statistics,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen

def hit(url:str)->tuple[bool,float]:
    started=time.perf_counter();payload=json.dumps({"text":"Pesan uji performa tanpa data pribadi","source":"load_test"}).encode()
    try:
        with urlopen(Request(url,data=payload,headers={"Content-Type":"application/json"}),timeout=30) as response:response.read();ok=response.status==200
    except Exception:ok=False
    return ok,(time.perf_counter()-started)*1000

def percentile(values:list[float],p:float)->float:
    ordered=sorted(values);return ordered[min(len(ordered)-1,int((len(ordered)-1)*p))]

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--url",default="http://127.0.0.1:8000/api/analyze");parser.add_argument("--requests",type=int,default=30);parser.add_argument("--concurrency",type=int,default=5);parser.add_argument("--max-p95-ms",type=float,default=3000);args=parser.parse_args()
    started=time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:results=[future.result() for future in as_completed([pool.submit(hit,args.url) for _ in range(args.requests)])]
    duration=time.perf_counter()-started;latencies=[item[1] for item in results];passed=sum(item[0] for item in results)
    report={"requests":args.requests,"concurrency":args.concurrency,"successful":passed,"failed":args.requests-passed,"requests_per_second":round(args.requests/duration,2),"latency_ms":{"mean":round(statistics.mean(latencies),2),"p50":round(percentile(latencies,.5),2),"p95":round(percentile(latencies,.95),2),"max":round(max(latencies),2)}}
    print(json.dumps(report,indent=2));raise SystemExit(0 if passed==args.requests and report["latency_ms"]["p95"]<=args.max_p95_ms else 1)
if __name__=="__main__":main()
