import Link from "next/link";

export default function TopNav() {
  return (
    <nav className="border-b border-zinc-800 mb-6">
      <div className="max-w-5xl mx-auto p-4 flex gap-6">
        <Link href="/" className="font-bold">
          NETSCOPE AI
        </Link>
        <Link href="/projects" className="text-zinc-400 hover:text-white">
          Projects
        </Link>
      </div>
    </nav>
  );
}
