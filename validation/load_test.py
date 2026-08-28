import concurrent.futures, json, time, urllib.request
URL="http://127.0.0.1:8000/api/analyze"; BODY=json.dumps({"text":"Jangan pernah kirim OTP kepada siapa pun","source":"load_test"}).encode()
def hit(_):
    start=time.perf_counter(); request=urllib.request.Request(URL,data=BODY,headers={"Content-Type":"application/json"});
    with urllib.request.urlopen(request,timeout=30) as response: response.read(); return response.status,time.perf_counter()-start
if __name__=="__main__":
    started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool: results=list(pool.map(hit,range(50)))
    durations=[x[1] for x in results]; print(json.dumps({"requests":len(results),"success":sum(x[0]==200 for x in results),"elapsed_seconds":round(time.perf_counter()-started,3),"average_ms":round(sum(durations)/len(durations)*1000,2),"max_ms":round(max(durations)*1000,2)},indent=2))
