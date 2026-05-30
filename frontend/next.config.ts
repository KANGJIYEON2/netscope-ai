import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // dev 전용 인디케이터를 좌하단 사이드바 Logout 버튼과 겹치지 않게 우하단으로 이동
  devIndicators: {
    position: "bottom-right",
  },
};

export default nextConfig;
