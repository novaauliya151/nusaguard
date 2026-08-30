import {ReactNode,Suspense} from "react";
import AdminShell from "./admin-shell";
export default function AdminLayout({children}:{children:ReactNode}){return <Suspense fallback={null}><AdminShell>{children}</AdminShell></Suspense>}
