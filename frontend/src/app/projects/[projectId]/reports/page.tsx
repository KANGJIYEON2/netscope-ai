"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

/** Legacy route — superseded by the project "Analyses" tab. */
export default function LegacyReportsRedirect() {
  const { projectId } = useParams() as { projectId: string };
  const router = useRouter();
  useEffect(() => {
    if (projectId) router.replace(`/projects/${projectId}/analyses`);
  }, [projectId, router]);
  return null;
}
