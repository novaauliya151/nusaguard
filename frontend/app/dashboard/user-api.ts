/* eslint-disable @next/next/no-location-assign-relative-destination */
export const API=process.env.NEXT_PUBLIC_API_URL??"http://localhost:8000";
export function sessionToken(){return localStorage.getItem("nusaguard_token")??sessionStorage.getItem("nusaguard_token")}
export function clearSession(){localStorage.removeItem("nusaguard_token");sessionStorage.removeItem("nusaguard_token")}
export async function userFetch<T>(path:string,init:RequestInit={}):Promise<T>{const response=await fetch(`${API}${path}`,{...init,headers:{"Content-Type":"application/json",Authorization:`Bearer ${sessionToken()}`,...init.headers}});if(response.status===401){clearSession();location.href=`/masuk?next=${encodeURIComponent(location.pathname+location.search)}`;throw new Error("Sesi berakhir.")}if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(body.detail??"Permintaan gagal.")}return response.status===204?({} as T):response.json()}
