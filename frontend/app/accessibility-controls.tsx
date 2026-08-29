"use client";
import {useEffect,useSyncExternalStore} from "react";
const KEY="nusaguard_theme",EVENT="nusaguard-theme-change";
function read(){return localStorage.getItem(KEY)==="dark"}
function subscribe(callback:()=>void){window.addEventListener("storage",callback);window.addEventListener(EVENT,callback);return()=>{window.removeEventListener("storage",callback);window.removeEventListener(EVENT,callback)}}
export default function AccessibilityControls(){const dark=useSyncExternalStore(subscribe,read,()=>false);useEffect(()=>{document.documentElement.classList.toggle("dark",dark);document.documentElement.style.colorScheme=dark?"dark":"light"},[dark]);function toggle(){localStorage.setItem(KEY,dark?"light":"dark");window.dispatchEvent(new Event(EVENT))}return <button className="theme-toggle" onClick={toggle} aria-pressed={dark} aria-label={dark?"Gunakan tema terang":"Gunakan tema gelap"} title={dark?"Tema terang":"Tema gelap"}><span aria-hidden>{dark?"☀":"☾"}</span>{dark?"Terang":"Gelap"}</button>}
