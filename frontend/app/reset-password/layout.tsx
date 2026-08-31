import {Suspense} from "react";
export default function ResetLayout({children}:{children:React.ReactNode}){return <Suspense fallback={<main>Memuat formulir…</main>}>{children}</Suspense>}
