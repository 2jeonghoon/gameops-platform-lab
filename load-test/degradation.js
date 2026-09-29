import http from "k6/http";
import { check } from "k6";

const baseUrl = (__ENV.BASE_URL || "").replace(/\/$/, "");
if (!baseUrl) {
  throw new Error(
    "BASE_URL is required; use: k6 run -e BASE_URL=http://HOST load-test/degradation.js",
  );
}

export const options = {
  scenarios: {
    degradation: {
      executor: "constant-arrival-rate",
      rate: 80,
      timeUnit: "1s",
      duration: "7m",
      preAllocatedVUs: 40,
      maxVUs: 150,
      gracefulStop: "15s",
    },
  },
  thresholds: {
    // A non-zero k6 exit caused by these limits is expected threshold failure evidence.
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<250"],
  },
};

export function setup() {
  console.warn(
    "DEGRADATION EXPERIMENT: an expected threshold failure must be recorded, not reported as a pass.",
  );
}

export default function () {
  const response = http.post(
    `${baseUrl}/sessions`,
    JSON.stringify({ region: "ap-northeast-2", player_count: 64 }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(response, {
    "degradation request returned a defined response": (result) =>
      result.status === 201 || result.status === 500 || result.status === 503,
  });

  if (response.status === 201) {
    const sessionId = response.json("id");
    http.get(`${baseUrl}/sessions/${sessionId}`);
    http.del(`${baseUrl}/sessions/${sessionId}`);
  }
}
