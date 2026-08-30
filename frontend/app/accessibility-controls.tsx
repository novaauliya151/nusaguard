"use client";
/* eslint-disable react-hooks/set-state-in-effect -- persisted theme is restored only after hydration */
import {useEffect,useState} from "react";
const KEY="nusaguard_theme";
export default function AccessibilityControls(){
  const[dark,setDark]=useState(false),[mounted,setMounted]=useState(false);
  useEffect(()=>{const saved=localStorage.getItem(KEY)==="dark";setDark(saved);document.documentElement.classList.toggle("dark",saved);document.documentElement.style.colorScheme=saved?"dark":"light";setMounted(true)},[]);
  function toggle(){const next=!dark;setDark(next);localStorage.setItem(KEY,next?"dark":"light");document.documentElement.classList.toggle("dark",next);document.documentElement.style.colorScheme=next?"dark":"light"}
  return <button className="theme-toggle" onClick={toggle} aria-pressed={mounted&&dark} aria-label={dark?"Gunakan tema terang":"Gunakan tema gelap"} title={dark?"Tema terang":"Tema gelap"}><span aria-hidden>{dark?"☀":"☾"}</span>{dark?"Terang":"Gelap"}</button>
}
