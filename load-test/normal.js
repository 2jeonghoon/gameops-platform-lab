import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = (__ENV.BASE_URL || "").replace(/\/$/, "");
if (!baseUrl) {
  throw new Error("BASE_URL is required; use: k6 run -e BASE_URL=http://HOST load-test/normal.js");
}

export const options = {
  scenarios: {
    normal: {
      executor: "constant-vus",
      vus: 5,
      duration: "5m",
      gracefulStop: "15s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<250"],
  },
};

const requestParams = {
  headers: { "Content-Type": "application/json" },
};

export default function () {
  const created = http.post(
    `${baseUrl}/sessions`,
    JSON.stringify({ region: "ap-northeast-2", player_count: 16 }),
    requestParams,
  );
  const createdOk = check(created, { "session created": (response) => response.status === 201 });
  if (!createdOk) {
    sleep(0.2);
    return;
  }

  const sessionId = created.json("id");
  const fetched = http.get(`${baseUrl}/sessions/${sessionId}`);
  check(fetched, { "session fetched": (response) => response.status === 200 });

  const deleted = http.del(`${baseUrl}/sessions/${sessionId}`);
  check(deleted, { "session deleted": (response) => response.status === 204 });
  sleep(0.2);
}
