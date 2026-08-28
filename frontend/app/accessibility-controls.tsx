"use client";
import {useEffect,useSyncExternalStore} from "react";

const KEY="nusaguard_accessibility";
const EVENT="nusaguard-accessibility-change";
type Preference="large"|"contrast";

function read(name:Preference){try{return Boolean(JSON.parse(localStorage.getItem(KEY)??"{}")[name])}catch{return false}}
function subscribe(callback:()=>void){window.addEventListener("storage",callback);window.addEventListener(EVENT,callback);return()=>{window.removeEventListener("storage",callback);window.removeEventListener(EVENT,callback)}}
function usePreference(name:Preference){return useSyncExternalStore(subscribe,()=>read(name),()=>false)}

export default function AccessibilityControls(){
 const large=usePreference("large"),contrast=usePreference("contrast");
 useEffect(()=>{document.documentElement.classList.toggle("large",large);document.documentElement.classList.toggle("contrast",contrast)},[large,contrast]);
 function apply(nextLarge:boolean,nextContrast:boolean){localStorage.setItem(KEY,JSON.stringify({large:nextLarge,contrast:nextContrast}));window.dispatchEvent(new Event(EVENT))}
 return <div className="global-access" aria-label="Pengaturan aksesibilitas"><button onClick={()=>apply(!large,contrast)} aria-pressed={large} title="Ubah ukuran teks">A+</button><button onClick={()=>apply(large,!contrast)} aria-pressed={contrast} title="Ubah kontras">◐</button></div>
}
