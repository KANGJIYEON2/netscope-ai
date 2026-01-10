export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg border border-gray-100">
        {/* 로고 / 서비스명 */}
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold tracking-tight">NetScope AI</h1>
          <p className="mt-1 text-sm text-gray-500">
            Intelligent Log Analysis Platform
          </p>
        </div>

        {children}
      </div>
    </div>
  );
}
