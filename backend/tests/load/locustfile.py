"""
Locust load testing for XinShouCai API.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Web UI available at: http://localhost:8089

Performance targets (SLA):
- P50 response time: < 200ms
- P95 response time: < 500ms
- P99 response time: < 1000ms
- Error rate: < 0.1%
- Throughput: > 100 RPS per instance
"""

import json
import random
from datetime import date, datetime
from locust import HttpUser, task, between, events, tag
from locust.runners import MasterRunner


# Test data
TEST_PATIENTS = []
TEST_DOCTORS = []


class PatientUser(HttpUser):
    """
    Simulates patient behavior patterns.

    Typical patient session:
    1. Login
    2. Check daily status / submit check-in
    3. View previous assessments
    4. Chat with AI (most common)
    5. Check messages from doctor
    """

    weight = 3  # Patients are 3x more common than doctors
    wait_time = between(2, 10)  # Patients browse slower

    def on_start(self):
        """Login and setup patient session."""
        self.patient_token = None
        self.patient_id = None
        self.thread_id = None
        self.conversation_id = None

        # Register or login
        email = f"loadtest_patient_{random.randint(1, 10000)}@test.com"
        password = "TestPassword123!"

        # Try to register first
        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "user_type": "PATIENT",
            "first_name": "LoadTest",
            "last_name": "Patient",
            "date_of_birth": "1990-01-15"
        })

        if response.status_code in [200, 201]:
            data = response.json()
            self.patient_token = data.get("access_token")
        else:
            # Login if already exists
            response = self.client.post("/api/v1/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                self.patient_token = response.json().get("access_token")

        if self.patient_token:
            self.headers = {"Authorization": f"Bearer {self.patient_token}"}

    @property
    def auth_headers(self):
        return self.headers if hasattr(self, 'headers') else {}

    @task(10)
    @tag('chat', 'ai', 'critical')
    def chat_with_ai(self):
        """Send message to AI chat - most common patient action."""
        messages = [
            "I'm feeling anxious today",
            "Had trouble sleeping last night",
            "Feeling better than yesterday",
            "I'm worried about my upcoming appointment",
            "The medication seems to be helping",
            "I had a nightmare about my past experiences",
        ]

        with self.client.post(
            "/api/v1/chat/",
            json={"message": random.choice(messages)},
            headers=self.auth_headers,
            name="/api/v1/chat/ [AI Chat]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.conversation_id = data.get("conversation_id")
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")

    @task(5)
    @tag('checkin', 'clinical')
    def submit_checkin(self):
        """Submit daily check-in."""
        with self.client.post(
            "/api/v1/clinical/checkin",
            json={
                "mood_score": random.randint(3, 8),
                "sleep_hours": round(random.uniform(5, 9), 1),
                "sleep_quality": random.randint(2, 5),
                "medication_taken": random.choice([True, False]),
                "notes": "Load test check-in"
            },
            headers=self.auth_headers,
            name="/api/v1/clinical/checkin [Submit]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")

    @task(3)
    @tag('checkin', 'clinical')
    def get_today_checkin(self):
        """View today's check-in."""
        self.client.get(
            "/api/v1/clinical/checkin/today",
            headers=self.auth_headers,
            name="/api/v1/clinical/checkin/today [Read]"
        )

    @task(2)
    @tag('assessment', 'clinical')
    def submit_assessment(self):
        """Submit a PHQ-9 or GAD-7 assessment."""
        assessment_type = random.choice(["PHQ9", "GAD7"])

        if assessment_type == "PHQ9":
            responses = {str(i): random.randint(0, 3) for i in range(1, 10)}
        else:  # GAD7
            responses = {str(i): random.randint(0, 3) for i in range(1, 8)}

        with self.client.post(
            "/api/v1/clinical/assessment",
            json={
                "assessment_type": assessment_type,
                "responses": responses
            },
            headers=self.auth_headers,
            name=f"/api/v1/clinical/assessment [{assessment_type}]",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")

    @task(3)
    @tag('assessment', 'clinical')
    def get_assessments(self):
        """View past assessments."""
        self.client.get(
            "/api/v1/clinical/assessments",
            headers=self.auth_headers,
            name="/api/v1/clinical/assessments [List]"
        )

    @task(4)
    @tag('messaging')
    def get_messages(self):
        """Check messages from doctor."""
        self.client.get(
            "/api/v1/messaging/threads",
            headers=self.auth_headers,
            name="/api/v1/messaging/threads [List]"
        )

    @task(2)
    @tag('messaging')
    def get_unread_count(self):
        """Check unread message count."""
        self.client.get(
            "/api/v1/messaging/threads/unread-count",
            headers=self.auth_headers,
            name="/api/v1/messaging/threads/unread-count"
        )

    @task(2)
    @tag('chat')
    def get_conversations(self):
        """View conversation history."""
        self.client.get(
            "/api/v1/chat/conversations",
            headers=self.auth_headers,
            name="/api/v1/chat/conversations [List]"
        )

    @task(1)
    @tag('auth', 'profile')
    def get_profile(self):
        """View own profile."""
        self.client.get(
            "/api/v1/auth/me/patient",
            headers=self.auth_headers,
            name="/api/v1/auth/me/patient [Profile]"
        )


class DoctorUser(HttpUser):
    """
    Simulates doctor behavior patterns.

    Typical doctor session:
    1. Login
    2. Check risk queue (priority)
    3. Review patient list
    4. View specific patient details
    5. Respond to messages
    6. Generate reports
    """

    weight = 1  # Doctors are less common
    wait_time = between(1, 5)  # Doctors work faster

    def on_start(self):
        """Login and setup doctor session."""
        self.doctor_token = None
        self.patient_ids = []

        email = f"loadtest_doctor_{random.randint(1, 1000)}@test.com"
        password = "TestPassword123!"

        # Try to register
        response = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "user_type": "DOCTOR",
            "first_name": "LoadTest",
            "last_name": "Doctor",
            "license_number": f"LIC{random.randint(10000, 99999)}"
        })

        if response.status_code in [200, 201]:
            self.doctor_token = response.json().get("access_token")
        else:
            response = self.client.post("/api/v1/auth/login", json={
                "email": email,
                "password": password
            })
            if response.status_code == 200:
                self.doctor_token = response.json().get("access_token")

        if self.doctor_token:
            self.headers = {"Authorization": f"Bearer {self.doctor_token}"}

    @property
    def auth_headers(self):
        return self.headers if hasattr(self, 'headers') else {}

    @task(10)
    @tag('clinical', 'risk', 'critical')
    def check_risk_queue(self):
        """Check risk queue - highest priority for doctors."""
        with self.client.get(
            "/api/v1/clinical/doctor/risk-queue",
            headers=self.auth_headers,
            name="/api/v1/clinical/doctor/risk-queue [Critical]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 403:
                response.failure("Not authorized as doctor")
            else:
                response.failure(f"Status {response.status_code}")

    @task(8)
    @tag('clinical', 'patients')
    def get_patient_list(self):
        """View patient list."""
        with self.client.get(
            "/api/v1/clinical/doctor/patients",
            params={"limit": 20, "offset": 0},
            headers=self.auth_headers,
            name="/api/v1/clinical/doctor/patients [List]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                patients = data.get("patients", [])
                self.patient_ids = [p.get("id") for p in patients if p.get("id")]
                response.success()

    @task(5)
    @tag('clinical', 'patients')
    def get_patient_overview(self):
        """View specific patient overview."""
        if self.patient_ids:
            patient_id = random.choice(self.patient_ids)
            self.client.get(
                f"/api/v1/clinical/doctor/patient/{patient_id}/overview",
                headers=self.auth_headers,
                name="/api/v1/clinical/doctor/patient/{id}/overview"
            )

    @task(4)
    @tag('messaging')
    def get_message_threads(self):
        """View message threads."""
        self.client.get(
            "/api/v1/messaging/threads",
            headers=self.auth_headers,
            name="/api/v1/messaging/threads [Doctor]"
        )

    @task(3)
    @tag('messaging')
    def send_message(self):
        """Send message to a patient."""
        if self.patient_ids:
            patient_id = random.choice(self.patient_ids)
            # First create/get thread
            response = self.client.post(
                f"/api/v1/messaging/doctor/patients/{patient_id}/thread",
                headers=self.auth_headers,
                name="/api/v1/messaging/doctor/patients/{id}/thread [Create]"
            )

            if response.status_code == 200:
                thread_id = response.json().get("id")
                if thread_id:
                    self.client.post(
                        f"/api/v1/messaging/threads/{thread_id}/messages",
                        json={
                            "content": "Load test message from doctor",
                            "message_type": "TEXT"
                        },
                        headers=self.auth_headers,
                        name="/api/v1/messaging/threads/{id}/messages [Send]"
                    )

    @task(2)
    @tag('reports')
    def generate_report(self):
        """Generate pre-visit report for a patient."""
        if self.patient_ids:
            patient_id = random.choice(self.patient_ids)
            self.client.post(
                f"/api/v1/reports/pre-visit/{patient_id}",
                headers=self.auth_headers,
                name="/api/v1/reports/pre-visit/{id} [Generate]"
            )

    @task(1)
    @tag('auth', 'profile')
    def get_profile(self):
        """View own profile."""
        self.client.get(
            "/api/v1/auth/me/doctor",
            headers=self.auth_headers,
            name="/api/v1/auth/me/doctor [Profile]"
        )


class HealthCheckUser(HttpUser):
    """
    Simulates health check monitoring.
    High frequency, low weight - used for uptime monitoring.
    """

    weight = 1
    wait_time = between(1, 2)

    @task
    @tag('health')
    def health_check(self):
        """Health check endpoint."""
        with self.client.get(
            "/health",
            name="/health [Monitor]",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


# Custom event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    print("=" * 60)
    print("XinShouCai Load Test Starting")
    print("=" * 60)
    print(f"Target host: {environment.host}")
    print(f"User classes: PatientUser (weight=3), DoctorUser (weight=1), HealthCheckUser (weight=1)")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate summary report on test stop."""
    print("\n" + "=" * 60)
    print("XinShouCai Load Test Complete")
    print("=" * 60)

    stats = environment.stats

    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {(stats.total.num_failures / max(stats.total.num_requests, 1)) * 100:.2f}%")

    print(f"\nResponse Times:")
    print(f"  Average: {stats.total.avg_response_time:.0f}ms")
    print(f"  Median (P50): {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")

    print(f"\nThroughput: {stats.total.total_rps:.2f} req/s")

    # SLA Check
    print("\n" + "-" * 40)
    print("SLA Compliance Check:")
    p50 = stats.total.get_response_time_percentile(0.5)
    p95 = stats.total.get_response_time_percentile(0.95)
    p99 = stats.total.get_response_time_percentile(0.99)
    error_rate = (stats.total.num_failures / max(stats.total.num_requests, 1)) * 100

    sla_pass = True

    if p50 <= 200:
        print(f"  [PASS] P50 ({p50:.0f}ms) <= 200ms")
    else:
        print(f"  [FAIL] P50 ({p50:.0f}ms) > 200ms")
        sla_pass = False

    if p95 <= 500:
        print(f"  [PASS] P95 ({p95:.0f}ms) <= 500ms")
    else:
        print(f"  [FAIL] P95 ({p95:.0f}ms) > 500ms")
        sla_pass = False

    if p99 <= 1000:
        print(f"  [PASS] P99 ({p99:.0f}ms) <= 1000ms")
    else:
        print(f"  [FAIL] P99 ({p99:.0f}ms) > 1000ms")
        sla_pass = False

    if error_rate <= 0.1:
        print(f"  [PASS] Error Rate ({error_rate:.2f}%) <= 0.1%")
    else:
        print(f"  [FAIL] Error Rate ({error_rate:.2f}%) > 0.1%")
        sla_pass = False

    print("-" * 40)
    if sla_pass:
        print("Overall SLA Status: PASS")
    else:
        print("Overall SLA Status: FAIL")
    print("=" * 60)


# Headless mode configuration for CI/CD
if __name__ == "__main__":
    import os
    os.system("locust -f tests/load/locustfile.py --host=http://localhost:8000")
