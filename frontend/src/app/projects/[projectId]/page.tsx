"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

export default function ProjectPage() {
  const { projectId } = useParams();
  const router = useRouter();

  useEffect(() => {
    if (projectId) {
      router.replace(`/projects/${projectId}/reports`);
    }
  }, [projectId, router]);

  return null;
}
