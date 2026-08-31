"use client";
import {createContext,useContext} from "react";
import type {AdminUser} from "./admin-api";
const AdminContext=createContext<AdminUser|null>(null);
export const AdminProvider=AdminContext.Provider;
export function useAdmin(){const user=useContext(AdminContext);if(!user)throw new Error("Admin context belum tersedia.");return user}
export function usePermission(permission:string){return useAdmin().permissions.includes(permission)}
