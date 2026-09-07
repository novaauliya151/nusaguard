import Image from "next/image";

export default function LogoNusaGuard({ className = "" }: { className?: string }) {
  return (
    <Image
      className={className}
      src="/images/logo_nusaguard.png"
      width={530}
      height={558}
      alt="Logo NusaGuard"
    />
  );
}
