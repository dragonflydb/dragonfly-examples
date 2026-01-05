// k6 Load Test Script for Magento + Dragonfly
// Install k6: https://k6.io/docs/getting-started/installation/
// Run: MAGENTO_URL=http://192.168.0.126 k6 run k6-load-test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const cacheHitTrend = new Trend('cache_response_time');

// Test configuration - Standard Load Test
export const options = {
    scenarios: {
        load_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 20 },   // Ramp up to 20 users
                { duration: '1m', target: 50 },    // Ramp up to 50 users
                { duration: '2m', target: 100 },   // Ramp up to 100 users
                { duration: '1m', target: 100 },   // Stay at 100 users
                { duration: '30s', target: 0 },    // Ramp down
            ],
            gracefulRampDown: '10s',
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<2000'], // 95% requests under 2s
        errors: ['rate<0.1'],              // Error rate under 10%
    },
};

const BASE_URL = __ENV.MAGENTO_URL || 'http://192.168.0.126';

// Page URLs to test (with sample data installed)
const pages = [
    // Static/Cached pages (Full Page Cache)
    '/',                                    // Homepage
    '/women.html',                          // Category
    '/men.html',                            // Category
    '/gear.html',                           // Category
    '/training.html',                       // Category
    '/sale.html',                           // Category
    '/women/tops-women.html',               // Subcategory
    '/men/tops-men.html',                   // Subcategory

    // Dynamic pages
    '/customer/account/login',              // Login
    '/checkout/cart',                       // Cart

    // Search (uses OpenSearch + cache)
    '/catalogsearch/result/?q=shirt',
    '/catalogsearch/result/?q=pants',
    '/catalogsearch/result/?q=jacket',
    '/catalogsearch/result/?q=bag',
];

export default function () {
    // Random page selection
    const page = pages[Math.floor(Math.random() * pages.length)];
    const url = `${BASE_URL}${page}`;

    const response = http.get(url, {
        headers: {
            'User-Agent': 'k6-load-test/1.0',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Encoding': 'gzip, deflate',
        },
        timeout: '30s',
    });

    // Check response
    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 2s': (r) => r.timings.duration < 2000,
        'no server error': (r) => r.status < 500,
    });

    errorRate.add(!success);

    // Track cache response times (category pages should be cached)
    if (page === '/' || page.endsWith('.html')) {
        cacheHitTrend.add(response.timings.duration);
    }

    // Simulate real user behavior - random wait between requests
    sleep(Math.random() * 2 + 1); // 1-3 seconds
}

// Stress test scenario (uncomment to use instead of standard load test)
// export const options = {
//     scenarios: {
//         stress_test: {
//             executor: 'ramping-vus',
//             startVUs: 0,
//             stages: [
//                 { duration: '2m', target: 100 },
//                 { duration: '5m', target: 200 },
//                 { duration: '2m', target: 300 },
//                 { duration: '5m', target: 300 },
//                 { duration: '2m', target: 0 },
//             ],
//         },
//     },
// };
