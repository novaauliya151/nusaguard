import UserShell from "./user-shell";
import {Suspense} from "react";
export default function DashboardPage(){return <Suspense fallback={<main>Memuat dashboard…</main>}><UserShell/></Suspense>}
