import { useEffect } from "react";
import { useRouter } from "next/router";

export default function AnalysisIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/analysis/BBCA");
  }, [router]);

  return null;
}
