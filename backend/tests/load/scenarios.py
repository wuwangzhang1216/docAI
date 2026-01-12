"""
Load Testing Scenarios for XinShouCai.

Predefined scenarios for different load testing purposes.

Usage:
    # Run specific scenario
    locust -f tests/load/scenarios.py --host=http://localhost:8000 --users 100 --spawn-rate 10

    # Run headless with specific duration
    locust -f tests/load/scenarios.py --host=http://localhost:8000 --headless -u 50 -r 5 -t 5m

Scenarios:
1. Normal Load: Simulates typical daily usage
2. Peak Load: Simulates busy periods (appointment times)
3. Stress Test: Pushes system to breaking point
4. Spike Test: Simulates sudden traffic surge
5. Soak Test: Long-running test for memory leaks
"""

import random
import time
from locust import HttpUser, task, between, events, tag, LoadTestShape


class NormalLoadUser(HttpUser):
    """
    Normal Load Scenario.

    Simulates typical daily usage patterns:
    - 70% patients, 30% doctors
    - Moderate request frequency
    - Mix of reads and writes

    Target: 50 concurrent users, 10 RPS
    """

    wait_time = between(3, 8)

    def on_start(self):
        self.is_patient = random.random() < 0.7
        self._setup_user()

    def _setup_user(self):
        """Register and login user."""
        user_type = "PATIENT" if self.is_patient else "DOCTOR"
        email = f"normal_{user_type.lower()}_{random.randint(1, 100000)}@test.com"

        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPassword123!",
            "user_type": user_type,
            "first_name": "Load",
            "last_name": "Test",
            "date_of_birth": "1990-01-01" if self.is_patient else None,
            "license_number": f"LIC{random.randint(10000, 99999)}" if not self.is_patient else None,
        })

        if response.status_code in [200, 201]:
            self.token = response.json().get("access_token")
        else:
            response = self.client.post("/api/v1/auth/login", json={
                "email": email, "password": "TestPassword123!"
            })
            self.token = response.json().get("access_token") if response.status_code == 200 else None

        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(10)
    def read_profile(self):
        """Most common action: view profile."""
        endpoint = "/api/v1/auth/me/patient" if self.is_patient else "/api/v1/auth/me/doctor"
        self.client.get(endpoint, headers=self.headers)

    @task(8)
    def patient_checkin_flow(self):
        """Patient: daily check-in."""
        if self.is_patient:
            self.client.get("/api/v1/clinical/checkin/today", headers=self.headers)
            self.client.post("/api/v1/clinical/checkin", json={
                "mood_score": random.randint(4, 8),
                "sleep_hours": round(random.uniform(6, 9), 1),
            }, headers=self.headers)

    @task(5)
    def patient_ai_chat(self):
        """Patient: chat with AI."""
        if self.is_patient:
            self.client.post("/api/v1/chat/", json={
                "message": random.choice([
                    "How are you today?",
                    "I'm feeling anxious",
                    "Had a good day",
                ])
            }, headers=self.headers)

    @task(6)
    def doctor_patient_list(self):
        """Doctor: view patient list."""
        if not self.is_patient:
            self.client.get("/api/v1/clinical/doctor/patients", headers=self.headers)

    @task(4)
    def doctor_risk_queue(self):
        """Doctor: check risk queue."""
        if not self.is_patient:
            self.client.get("/api/v1/clinical/doctor/risk-queue", headers=self.headers)


class PeakLoadUser(HttpUser):
    """
    Peak Load Scenario.

    Simulates busy periods (9 AM - 12 PM, appointment rush):
    - Higher patient activity
    - More assessment submissions
    - More doctor dashboard views

    Target: 200 concurrent users, 50 RPS
    """

    wait_time = between(1, 3)

    def on_start(self):
        self.is_patient = random.random() < 0.8  # More patients during peak
        self._setup_user()

    def _setup_user(self):
        user_type = "PATIENT" if self.is_patient else "DOCTOR"
        email = f"peak_{user_type.lower()}_{random.randint(1, 100000)}@test.com"

        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPassword123!",
            "user_type": user_type,
            "first_name": "Peak",
            "last_name": "Test",
            "date_of_birth": "1990-01-01" if self.is_patient else None,
            "license_number": f"LIC{random.randint(10000, 99999)}" if not self.is_patient else None,
        })

        if response.status_code in [200, 201]:
            self.token = response.json().get("access_token")
        else:
            response = self.client.post("/api/v1/auth/login", json={
                "email": email, "password": "TestPassword123!"
            })
            self.token = response.json().get("access_token") if response.status_code == 200 else None

        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(15)
    def patient_assessment(self):
        """Patient: submit assessment (common before appointments)."""
        if self.is_patient:
            responses = {str(i): random.randint(0, 3) for i in range(1, 10)}
            self.client.post("/api/v1/clinical/assessment", json={
                "assessment_type": random.choice(["PHQ9", "GAD7"]),
                "responses": responses
            }, headers=self.headers)

    @task(10)
    def patient_checkin(self):
        if self.is_patient:
            self.client.post("/api/v1/clinical/checkin", json={
                "mood_score": random.randint(3, 9),
                "notes": "Peak load test"
            }, headers=self.headers)

    @task(8)
    def doctor_dashboard(self):
        """Doctor: full dashboard refresh."""
        if not self.is_patient:
            self.client.get("/api/v1/clinical/doctor/patients", headers=self.headers)
            self.client.get("/api/v1/clinical/doctor/risk-queue", headers=self.headers)


class StressTestUser(HttpUser):
    """
    Stress Test Scenario.

    Pushes system to find breaking point:
    - Maximum request rate
    - Minimal wait time
    - Heavy write operations

    Target: Find breaking point (start with 500 users)
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        email = f"stress_{random.randint(1, 1000000)}@test.com"
        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPassword123!",
            "user_type": "PATIENT",
            "first_name": "Stress",
            "last_name": "Test",
            "date_of_birth": "1990-01-01"
        })

        if response.status_code in [200, 201]:
            self.token = response.json().get("access_token")
        else:
            response = self.client.post("/api/v1/auth/login", json={
                "email": email, "password": "TestPassword123!"
            })
            self.token = response.json().get("access_token") if response.status_code == 200 else None

        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def rapid_reads(self):
        """Rapid fire read requests."""
        self.client.get("/api/v1/auth/me", headers=self.headers)

    @task(3)
    def rapid_writes(self):
        """Rapid write requests."""
        self.client.post("/api/v1/clinical/checkin", json={
            "mood_score": random.randint(1, 10),
        }, headers=self.headers)

    @task(2)
    def ai_chat_stress(self):
        """AI chat under stress."""
        self.client.post("/api/v1/chat/", json={
            "message": "Stress test message"
        }, headers=self.headers)


class SpikeTestShape(LoadTestShape):
    """
    Spike Test Load Shape.

    Simulates sudden traffic surge:
    1. Baseline: 20 users for 2 minutes
    2. Spike: Jump to 200 users for 1 minute
    3. Recovery: Back to 20 users for 2 minutes

    Usage: locust -f scenarios.py --host=http://localhost:8000 --headless
    """

    stages = [
        {"duration": 120, "users": 20, "spawn_rate": 5},   # Baseline
        {"duration": 180, "users": 200, "spawn_rate": 50}, # Spike
        {"duration": 300, "users": 20, "spawn_rate": 10},  # Recovery
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class StepLoadShape(LoadTestShape):
    """
    Step Load Shape for finding capacity.

    Gradually increases load in steps:
    - Start: 10 users
    - Step: +20 users every 2 minutes
    - Max: 200 users

    Helps identify when performance degrades.
    """

    step_time = 120  # 2 minutes per step
    step_load = 20   # Add 20 users per step
    spawn_rate = 10
    max_users = 200

    def tick(self):
        run_time = self.get_run_time()
        current_step = int(run_time // self.step_time)
        target_users = min(10 + (current_step * self.step_load), self.max_users)

        return (target_users, self.spawn_rate)


# Event listeners for scenario-specific reporting
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics for analysis."""
    if exception:
        print(f"FAILED: {request_type} {name} - {exception}")


@events.test_stop.add_listener
def on_stop(environment, **kwargs):
    """Generate scenario summary."""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("SCENARIO SUMMARY")
    print("=" * 60)

    # Key metrics
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"P50: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"Throughput: {stats.total.total_rps:.2f} req/s")

    # Calculate error rate
    error_rate = (stats.total.num_failures / max(stats.total.num_requests, 1)) * 100

    print(f"\nError Rate: {error_rate:.2f}%")

    # Capacity recommendation
    if error_rate < 1 and stats.total.get_response_time_percentile(0.95) < 500:
        print("\nSystem Status: HEALTHY")
        print("Recommendation: Can handle current load. Consider increasing for capacity testing.")
    elif error_rate < 5 and stats.total.get_response_time_percentile(0.95) < 1000:
        print("\nSystem Status: DEGRADED")
        print("Recommendation: Approaching capacity limits. Review slow endpoints.")
    else:
        print("\nSystem Status: OVERLOADED")
        print("Recommendation: Scale up infrastructure or optimize code.")

    print("=" * 60)
