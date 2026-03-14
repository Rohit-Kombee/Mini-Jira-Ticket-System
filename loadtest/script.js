/**
 * k6 load test - Support Ticket API
 * Simulates 5000+ requests, concurrent users, and spike test.
 * Run: k6 run loadtest/script.js
 * With base URL: k6 run -e BASE_URL=http://localhost:8000 loadtest/script.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

const errorRate = new Rate('errors');

export const options = {
  // Compatible with older k6 versions (no "scenarios" executors).
  // Stages approximate sustained (20 VUs) + spike (50 VUs).
  stages: [
    { duration: '10s', target: 20 },
    { duration: '2m', target: 20 },
    { duration: '10s', target: 50 },
    { duration: '30s', target: 50 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'],
    errors: ['rate<0.2'],
  },
};

function sustainedLoad() {
  const res = http.get(`${BASE_URL}/health`);
  check(res, { 'health ok': (r) => r.status === 200 }) || errorRate.add(1);
  sleep(0.5 + Math.random() * 1);
}

function mixedFlow() {
  const loginUser = __ENV.LOGIN_USER || 'admin';
  const loginPassword = __ENV.LOGIN_PASSWORD || 'admin';

  // Login (email or username; default admin: admin / admin)
  let res = http.post(`${BASE_URL}/auth/login`, JSON.stringify({
    email: loginUser,
    password: loginPassword,
  }), { headers: { 'Content-Type': 'application/json' } });
  const loginOk = check(res, { 'login ok': (r) => r.status === 200 });
  if (!loginOk) {
    errorRate.add(1);
    sleep(1);
    return;
  }
  const token = res.json('access_token');
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // Create ticket
  res = http.post(`${BASE_URL}/tickets`, JSON.stringify({
    title: `Load test ticket VU${__VU}-${Date.now()}`,
    description: 'Created by k6',
    priority: 'medium',
  }), { headers });
  const createOk = check(res, { 'create ticket ok': (r) => r.status === 201 });
  if (!createOk) errorRate.add(1);

  // List tickets (with pagination and filter)
  res = http.get(`${BASE_URL}/tickets?page=1&limit=10`, { headers });
  check(res, { 'list tickets ok': (r) => r.status === 200 }) || errorRate.add(1);

  sleep(0.2 + Math.random() * 0.5);
}

export function setup() {
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return { baseUrl: BASE_URL };
}

export default function (data) {
  // Mix in real workflow requests alongside health checks.
  // Approx: 30% of iterations do login→create→list, otherwise /health.
  if (Math.random() < 0.3) {
    mixedFlow();
  } else {
    sustainedLoad();
  }
}
