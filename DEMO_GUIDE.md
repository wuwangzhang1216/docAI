# Heart Guardian AI - Demo Guide

> Complete demo recording workflow showcasing all core features of Heart Guardian AI

## Table of Contents

- [Demo Account Information](#demo-account-information)
- [Environment Setup](#environment-setup)
- [Demo Flow Overview](#demo-flow-overview)
- [Part 1: Patient Portal Demo](#part-1-patient-portal-demo)
- [Part 2: Doctor Portal Demo](#part-2-doctor-portal-demo)
- [Part 3: Special Features Demo](#part-3-special-features-demo)
- [Suggested Talking Points](#suggested-talking-points)
- [Troubleshooting](#troubleshooting)

---

## Demo Account Information

### Universal Password

```
Password for all accounts: Demo123!
```

### Doctor Accounts

| Email | Name | Specialty | Associated Patients |
|-------|------|-----------|---------------------|
| `dr.sarah@demo.com` | Dr. Sarah Mitchell | Clinical Psychology | Michael Roberts, Emily Chen |
| `dr.james@demo.com` | Dr. James Thompson | Psychiatry | David Wilson |

### Patient Accounts

| Email | Name | Risk Level | Mood Trend | Demo Focus |
|-------|------|------------|------------|------------|
| `patient.michael@demo.com` | Michael Roberts | MEDIUM | Improving | Daily check-ins, assessments |
| `patient.emily@demo.com` | Emily Chen | HIGH | Fluctuating | **Risk detection, crisis intervention** |
| `patient.david@demo.com` | David Wilson | LOW | Stable | Data export, long-term management |

---

## Environment Setup

### 1. Start Services

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 2. Initialize Demo Data

```bash
cd backend
python scripts/seed_demo_data.py
```

### 3. Recording Preparation

- [ ] Prepare two browser windows (patient portal + doctor portal side by side)
- [ ] Clear browser cache
- [ ] Close unnecessary browser tabs and notifications
- [ ] Check screen recording software settings (recommended 1920x1080 resolution)
- [ ] Test microphone quality

---

## Demo Flow Overview

```
Total Duration: ~25-30 minutes

┌─────────────────────────────────────────────────────────────┐
│  Opening Introduction (30 sec)                              │
│  "Heart Guardian AI - 24/7 mental health support for        │
│   political trauma survivors"                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Part 1: Patient Portal Demo (12 min)                       │
│  Login → [Registration] → Dashboard → Health Center →       │
│  AI Chat → Check-in → Assessment → Doctor Connection →      │
│  Messages → Appointments → Profile → Data Export            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Part 2: Doctor Portal Demo (10 min)                        │
│  Login → Patient List → Add/Create Patient → Pending →      │
│  Risk Queue → Patient Details → AI Assistant →              │
│  Generate Report → Appointments → Messages → Profile        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Part 3: Special Features Demo (4 min)                      │
│  Multi-language → Theme Toggle → Real-time Messaging →      │
│  Responsive Design → PWA Support                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Closing Summary (30 sec)                                   │
│  Core value recap                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1: Patient Portal Demo

### 1.1 Login Page (1 min)

**URL:** `http://localhost:3000/login`

**Steps:**

1. Open the login page
2. Show the clean login interface with the following elements:
   - Heart Guardian AI logo
   - Email input field
   - Password input field
   - Login button
   - "Create Account" link for new users
3. Click language switcher (top right) to demonstrate multi-language support:
   - Switch between English ↔ 中文
4. Login with credentials:
   ```
   Email: patient.emily@demo.com
   Password: Demo123!
   ```

**UI Elements to Highlight:**

- Language switcher dropdown (EN/中文)
- Theme toggle button (sun/moon icon)
- Clean, accessible form design
- System automatically detects user type (patient/doctor) after login

**Talking Points:**
> "Let's start with the patient experience. Heart Guardian AI supports multiple languages - currently English and Chinese. The system automatically recognizes whether you're a patient or doctor based on your account type and redirects you to the appropriate portal."

---

### 1.1b New Patient Registration (Optional Demo - 1 min)

**URL:** `http://localhost:3000/login` → "Create Account"

**Steps:**

1. From login page, click "Create Account" or "Sign Up" link
2. Show registration form:

   **Account Information:**
   - Email address
   - Password (with requirements shown)
   - Confirm password

   **Personal Information:**
   - First name
   - Last name

3. Fill in demo registration:
   ```
   Email: newpatient.demo@example.com
   Password: Demo123!
   First Name: Demo
   Last Name: Patient
   ```
4. Click "Create Account"
5. Show success message and redirect to login or dashboard
6. (Optional) Show email verification prompt if enabled

**UI Elements to Highlight:**

- Password strength indicator
- Form validation messages
- Clear registration flow
- Privacy notice / Terms acceptance

**Talking Points:**
> "New patients can self-register for the platform. The registration process is simple - just email, password, and basic name. After registration, patients can complete their profile and wait for a doctor to send a connection request, or receive an invitation from their healthcare provider."

---

### 1.2 Dashboard Overview (45 sec)

**URL:** `/dashboard` (automatic redirect after login)

**Steps:**

1. Show the personalized greeting:
   - Time-based: "Good Morning/Afternoon/Evening, [Name]"
   - Displays today's date
2. Demonstrate Quick Mood Check:
   - Show 5 emoji options (😢 😕 😐 🙂 😊)
   - Click one to record quick mood
3. Show 3 Quick Action Cards:
   - **Talk to AI Companion** - Blue card with chat icon
   - **Health Center** - Green card with heart icon
   - **My Appointments** - Purple card with calendar icon
4. Show daily motivational quote at bottom

**UI Elements to Highlight:**

- Responsive card layout
- Emoji-based mood selection
- Clear navigation to core features
- Calming color scheme (blues and greens)

**Talking Points:**
> "After logging in, patients see a personalized dashboard with a time-appropriate greeting. The quick mood check lets them record how they're feeling with just one tap. Three main action cards provide immediate access to our core features: AI companion chat, health tracking, and appointments."

---

### 1.3 Health Center Overview (1 min) ⭐ NEW FEATURE

**URL:** `/health`

**Steps:**

1. Click "Health Center" card from dashboard or navigate via bottom nav
2. Show Today's Status Card:
   - Today's mood score with emoji
   - Sleep hours recorded
   - Medication status (✓ taken / ✗ not taken)
   - "Checked In" / "Not Checked In" badge
3. Show Quick Actions Grid:
   - **Daily Check-in** button → `/checkin`
   - **Psychological Assessment** button → `/assessment`
4. Scroll to show Recent Check-ins (last 7 days):
   - Date, sleep hours, sleep quality stars, mood score
5. Scroll to show Recent Assessments:
   - Assessment type (PHQ-9, GAD-7, PCL-5)
   - Score and severity badge

**UI Elements to Highlight:**

- Consolidated health overview
- Color-coded mood indicators (red/yellow/green)
- Severity badges (Minimal/Mild/Moderate/Severe)
- Quick access to detailed tracking

**Talking Points:**
> "The Health Center provides a consolidated view of the patient's mental health status. At a glance, you can see today's mood, sleep, and medication compliance. Recent check-ins and assessment results are displayed below, making it easy to track trends over time."

---

### 1.4 AI Emotional Support Chat (2.5 min) ⭐ KEY FEATURE

**URL:** `/conversations` (AI Support tab)

**Steps:**

1. Click "Talk to AI Companion" or navigate via bottom nav to Conversations
2. Show the dual-tab interface:
   - **AI Support** tab (active) - Chat with AI companion
   - **Doctor Messages** tab - Messages with treating physician
3. Show existing conversation history (if any)
4. Type a normal message first:
   ```
   I've been feeling anxious lately about my job situation.
   ```
5. Wait for AI response - show empathetic, supportive reply
6. **Key Demo - Risk Detection**: Type a high-risk message:
   ```
   I feel completely hopeless. I don't want to live anymore...
   ```
7. Wait for AI response and **Crisis Modal** to appear:
   - Modal shows emergency hotline numbers
   - "Notify My Doctor" button
   - Crisis resources information
8. Click "Notify My Doctor" to demonstrate alert system
9. Show AI's empathetic crisis response

**UI Elements to Highlight:**

- Clean chat interface with message bubbles
- AI typing indicator (3 dots animation)
- Auto-scroll to latest messages
- Crisis modal with clear emergency resources
- Red-highlighted risk detection

**Talking Points:**
> "This is Heart Guardian AI's core feature - 24/7 AI emotional support. The AI companion provides empathetic responses and coping strategies.
>
> [Send high-risk message]
>
> Watch what happens when I type a message containing suicidal ideation... The system immediately detected high-risk content. This crisis intervention modal shows emergency hotline numbers and offers to notify the treating physician. This risk detection works in multiple languages and is specifically optimized for expressions common among political trauma survivors."

---

### 1.5 Daily Check-in (1.5 min)

**URL:** `/checkin`

**Steps:**

1. Navigate to Check-in via Health Center or bottom nav
2. Show the check-in form with these elements:

   **Mood Section:**
   - Mood slider (0-10) with gradient background
   - 5 quick-select emoji buttons
   - Real-time mood label (Very Low → Low → Neutral → Good → Very Good)

   **Sleep Section:**
   - Sleep hours input (0-24)
   - Sleep quality buttons (1-5): Very Poor → Poor → Fair → Good → Very Good

   **Medication Section:**
   - Yes/No toggle buttons

   **Notes Section:**
   - Free text area (3 rows)

3. Complete a check-in:
   - Set mood to 6
   - Enter 7 hours sleep
   - Select "Good" sleep quality
   - Click "Yes" for medication
   - Add note: "Feeling better today after morning walk"
4. Click "Save Check-in"
5. Show success confirmation banner (green)
6. Expand "Recent Check-ins" to show history (up to 6 entries)

**UI Elements to Highlight:**

- Intuitive slider with color gradient
- Large, touch-friendly buttons
- Success feedback with summary
- Historical data expandable section

**Talking Points:**
> "Daily check-ins help patients track their mental health consistently. The mood slider provides precise scoring from 0-10, or patients can quickly tap an emoji. Sleep tracking includes both duration and quality. After submission, a summary confirms the recorded data, and patients can view their recent history."

---

### 1.6 Psychological Assessments (2 min)

**URL:** `/assessment`

**Steps:**

1. Navigate to Assessment page
2. Show assessment type selection with 3 cards:

   **PHQ-9 (Depression Screening)**
   - 9 questions, 27 points max
   - "Start PHQ-9" button

   **GAD-7 (Anxiety Screening)**
   - 7 questions, 21 points max
   - "Start GAD-7" button

   **PCL-5 (PTSD Screening)**
   - 8 questions, 32 points max
   - "Start PCL-5" button

3. Select PHQ-9 to demonstrate
4. Show question interface:
   - Progress bar at top
   - Question number (e.g., "Question 1 of 9")
   - Bilingual question text (English + 中文)
   - 4 answer options (0-3 points each)
5. Answer 2-3 questions to show progression
6. Complete assessment (can use quick demo data)
7. Show Results Screen:
   - Large score display
   - Severity badge (color-coded)
   - Score interpretation text
   - "Take Again" button
   - For high scores: Crisis resources warning

**UI Elements to Highlight:**

- Clean progress indicator
- Bilingual question display
- Large, readable answer options
- Clear severity classification
- Crisis resources for severe scores

**Talking Points:**
> "We support three standardized psychological assessments: PHQ-9 for depression, GAD-7 for anxiety, and PCL-5 for PTSD - especially important for political trauma survivors.
>
> Each question is displayed in both English and Chinese. The progress bar shows completion status. After finishing, the system automatically calculates the score and provides professional interpretation with severity classification."

---

### 1.7 Doctor Connection Management (1 min) ⭐ NEW FEATURE

**URL:** `/profile`

**Steps:**

1. Navigate to Profile page via bottom nav
2. Scroll to "My Doctors" section:
   - Show connected doctor card (if any):
     - Doctor name and specialty
     - "View Profile" button → Opens doctor details modal
     - "Disconnect" button
3. Scroll to "Connection Requests" section:
   - Show pending request from a doctor (if demo data includes one):
     - Doctor name and specialty
     - Request message (if provided)
     - "Accept" / "Decline" buttons
4. Demonstrate accepting/declining a request

**UI Elements to Highlight:**

- Clear doctor information display
- Easy accept/decline interface
- Doctor profile modal with full details

**Talking Points:**
> "Patients have control over their care relationships. In the Profile section, they can see their connected doctors and manage connection requests. When a doctor sends a connection request, patients can view the doctor's profile, read any message, and choose to accept or decline."

---

### 1.8 Doctor-Patient Messages (1 min)

**URL:** `/conversations` (Doctor Messages tab)

**Steps:**

1. Navigate to Conversations page
2. Click "Doctor Messages" tab
3. Show conversation thread list:
   - Doctor name and avatar
   - Last message preview
   - Timestamp
4. Click on Dr. Sarah Mitchell's thread
5. Show message history:
   - Doctor messages (left, card background)
   - Patient messages (right, blue background)
   - Timestamps on each message
6. Send a new message:
   ```
   Hi Dr. Mitchell, I'd like to schedule an appointment for next week. Is that possible?
   ```
7. Show message sent confirmation

**UI Elements to Highlight:**

- Clear thread list with search
- Message bubbles with read status
- Real-time message delivery
- Easy message input

**Talking Points:**
> "Patients can communicate directly with their treating physician through secure messaging. The conversation history is preserved, and messages are delivered in real-time via WebSocket. Doctors receive notifications immediately when patients send messages."

---

### 1.9 My Appointments (45 sec)

**URL:** `/my-appointments`

**Steps:**

1. Navigate to Appointments via bottom nav or dashboard
2. Show dual-tab view:
   - **Upcoming** - Future appointments
   - **All** - Complete history
3. Show appointment card details:
   - Doctor name with avatar
   - Doctor specialty
   - Status badge (Pending/Confirmed/Completed/Cancelled)
   - Appointment type (Initial/Follow-up/Emergency/Consultation)
   - Date and time range
   - Cancel button (if applicable)
4. Show reminder section for upcoming appointments

**UI Elements to Highlight:**

- Clear appointment cards
- Color-coded status badges
- Type indicators
- Cancel functionality

**Talking Points:**
> "Patients can view all their appointments in one place. The Upcoming tab shows future appointments, while All shows complete history. Each card displays the doctor's information, appointment type, and status. Patients can cancel appointments directly from here if needed."

---

### 1.10 Patient Profile Management (1 min)

**URL:** `/profile`

**Steps:**

1. Navigate to Profile via bottom nav (👤 icon)
2. Show expandable profile sections:

   **Personal Information Section:**
   - First name / Last name
   - Date of birth
   - Gender selection
   - Phone number
   - Address and City

   **Emergency Contact Section:**
   - Contact name
   - Phone number
   - Relationship (dropdown)

   **Medical Information Section:**
   - Current medications (text area)
   - Medical conditions (text area)
   - Allergies (text area)

   **Mental Health Information Section:**
   - Treatment history
   - Mental health goals
   - Support system
   - Known triggers
   - Coping strategies

3. Expand each section to show edit functionality
4. Make a small edit (e.g., update phone number)
5. Click "Save" and show success notification

**UI Elements to Highlight:**

- Collapsible/expandable sections (Disclosure pattern)
- Form validation
- Auto-save or explicit save button
- Clear section organization

**Talking Points:**
> "Patients can manage their complete profile including personal information, emergency contacts, medical history, and mental health background. This information is shared with their connected doctors to provide context for treatment. All sections are expandable for easy navigation."

---

### 1.11 Data Export (45 sec)

**URL:** `/data-export`

**Steps:**

1. Navigate to Data Export from Profile page (link at bottom)
2. Show export options:
   - **Format Selection**: JSON, CSV, PDF
   - **Data Types** (checkboxes):
     - Profile Information
     - Check-in Records
     - Assessment Results
     - Conversation History
   - **Date Range**: Start date, End date
3. Select PDF format and all data types
4. Click "Create Export Request"
5. Show export history with download links
6. Download a PDF and briefly show contents

**UI Elements to Highlight:**

- Multiple format options
- Granular data selection
- Date range filtering
- Export history tracking
- Download links

**Talking Points:**
> "Heart Guardian AI emphasizes data sovereignty. Patients can export all their data at any time in JSON, CSV, or PDF format. They choose exactly what data to include and the date range. This ensures patients maintain full control over their health records and can share them with other providers."

---

### 1.12 Change Password (30 sec)

**URL:** `/change-password`

**Steps:**

1. Navigate to Change Password (from Profile or Settings)
2. Show change password form:
   - Current password field
   - New password field
   - Confirm new password field
3. Show password requirements (if displayed)
4. Demonstrate form validation

**UI Elements to Highlight:**

- Secure password input fields
- Password visibility toggle
- Validation feedback

**Talking Points:**
> "Patients can change their password at any time for security. The system requires the current password for verification before allowing a change."

---

## Part 2: Doctor Portal Demo

### 2.1 Doctor Login (30 sec)

**Steps:**

1. Open a new browser window or incognito mode
2. Navigate to `http://localhost:3000/login`
3. Login with doctor credentials:
   ```
   Email: dr.sarah@demo.com
   Password: Demo123!
   ```
4. Note automatic redirect to doctor portal (different layout)

**Talking Points:**
> "Now let's switch to the doctor portal. Using the same login page, the system recognizes this is a doctor account and redirects to the physician interface."

---

### 2.2 Patient List Overview (1.5 min)

**URL:** `/patients`

**Steps:**

1. Show the patient list page header with action buttons:
   - **Create Patient** (green) - Create new patient account
   - **Add Patient** (blue) - Connect with existing patient
   - **Pending Requests** (amber) - Shows badge count
   - **Risk Queue** (red) - Shows unreviewed risk count

2. Show Search and Sort controls:
   - Search box: "Search patients..."
   - Sort dropdown:
     - By Risk (High → Low)
     - By Name (A → Z)
     - By Mood (High → Low)

3. Show Patient Table with columns:
   - **Patient** - Avatar + Name
   - **Avg Mood** - Color-coded number (red < 4, yellow 4-6, green > 6)
   - **PHQ-9** - Score + severity badge
   - **GAD-7** - Score + severity badge
   - **Pending Risks** - Pulsing red badge if unreviewed
   - **Actions**:
     - ✨ AI Assistant icon
     - 💬 Message icon
     - View link

4. Show severity legend at bottom:
   - 🟢 Minimal (0-4)
   - 🟡 Mild (5-9)
   - 🟠 Moderate (10-14)
   - 🔴 Moderate-Severe/Severe (15+)

5. Use sort by risk to show high-risk patients at top

**UI Elements to Highlight:**

- Quick action buttons in header
- Sortable columns
- Color-coded risk indicators
- Pulsing animation for pending risks
- Clear severity legend

**Talking Points:**
> "The doctor dashboard provides an immediate overview of all patients. Key metrics are visible at a glance - mood scores, PHQ-9 and GAD-7 assessments, and pending risk events. The pulsing red badge indicates Emily Chen has unreviewed risk events. Sorting by risk ensures critical patients appear first."

---

### 2.3 Add Patient / Create Patient (1 min) ⭐ NEW FEATURE

**Steps:**

1. Click "Add Patient" button (blue)
2. Show Add Patient modal:
   - Patient email input field
   - Optional message textarea
   - "Send Request" button
3. Enter an email:
   ```
   newpatient@example.com
   ```
4. Add optional message:
   ```
   I'd like to help you with your mental health journey.
   ```
5. Click "Send Request"
6. Show success notification

7. Click "Create Patient" button (green)
8. Show Create Patient form:
   - Basic information fields
   - Automatically creates account and sends invitation

**UI Elements to Highlight:**

- Clean modal interface
- Optional personalized message
- Clear success feedback

**Talking Points:**
> "Doctors can connect with patients in two ways. 'Add Patient' sends a connection request to an existing patient by email - the patient must accept before the doctor gains access. 'Create Patient' allows doctors to create a new patient account directly, useful for onboarding new patients into the system."

---

### 2.4 Pending Connection Requests (30 sec)

**URL:** `/pending-requests`

**Steps:**

1. Click "Pending Requests" button (amber badge)
2. Show list of pending connection requests:
   - Patient name and email
   - Request date
   - Status (Pending/Accepted/Declined)
3. Show ability to resend or cancel requests

**UI Elements to Highlight:**

- Request status tracking
- Batch request management

**Talking Points:**
> "The Pending Requests page tracks all outgoing connection requests. Doctors can see which patients haven't responded yet and can resend or cancel requests as needed."

---

### 2.5 Risk Queue (2 min) ⭐ KEY FEATURE

**URL:** `/risk-queue`

**Steps:**

1. Click "Risk Queue" button (red) or navigate via top nav
2. Show search and filter controls:
   - Search: "Search trigger text..."
   - Filter dropdown: All / Critical / High / Medium / Low

3. Show Risk Event Cards:
   - **Emily Chen - CRITICAL** (red badge)
     - Risk type: SUICIDAL
     - AI Confidence: 92%
     - Trigger text preview (truncated)
     - Timestamp
   - Other risk events (if demo data includes)

4. Click Emily Chen's risk event
5. Show Review Modal:
   - Event details header (Level, Type, Patient, Time)
   - Full trigger text in red background box
   - Doctor review notes textarea
   - "Mark as Reviewed" button

6. Add review notes:
   ```
   Contacted patient by phone at 10:30 AM. Patient confirmed they are safe and not in immediate danger. Scheduled emergency appointment for tomorrow morning at 9 AM. Patient agreed to call crisis line if feelings intensify before appointment.
   ```
7. Click "Mark as Reviewed"
8. Show risk event removed from queue

**UI Elements to Highlight:**

- Color-coded severity (Critical=red, High=red, Medium=orange, Low=yellow)
- AI confidence percentage
- Full trigger text display
- Audit trail documentation
- Queue management

**Talking Points:**
> "The Risk Queue is mission-critical for patient safety. Every high-risk message detected by our AI appears here, prioritized by severity. Let's look at Emily Chen's event...
>
> The system shows the exact message that triggered detection, the AI's confidence level of 92%, and the timestamp. Doctors document their response actions before marking as reviewed, creating a complete audit trail for compliance and quality assurance."

---

### 2.6 Patient Details Page (1.5 min)

**URL:** `/patients/[id]`

**Steps:**

1. Return to patient list
2. Click "View" on Michael Roberts' row
3. Show Patient Details page sections:

   **Header:**
   - Patient name and avatar
   - Basic info (age, gender)
   - Risk level badge

   **Medical Information Section:**
   - Current medications
   - Medical conditions
   - Allergies

   **Mental Health Background Section:**
   - Treatment history
   - Mental health goals
   - Support system
   - Known triggers
   - Coping strategies

   **Check-in History Chart:**
   - 30-day mood trend graph
   - Sleep hours overlay
   - Interactive data points

   **Assessment Records:**
   - PHQ-9 history with scores
   - GAD-7 history with scores
   - PCL-5 history with scores
   - Severity trends

4. Show "Generate Report" button → Creates pre-visit PDF summary

**UI Elements to Highlight:**

- Expandable information sections
- Interactive trend charts
- Historical assessment tracking
- One-click report generation

**Talking Points:**
> "The patient detail page provides a comprehensive view. We see Michael's complete profile including medications, conditions, and mental health background.
>
> Below is a 30-day check-in trend chart - you can see Michael's mood has been gradually improving. Assessment history shows all completed PHQ-9, GAD-7, and PCL-5 scores over time.
>
> Doctors can generate a pre-visit summary report with one click, perfect for appointment preparation."

---

### 2.7 AI Assistant for Patient Analysis (1 min) ⭐ KEY FEATURE

**URL:** `/patients/[id]/ai-assistant`

**Steps:**

1. From patient details, click the ✨ AI Assistant icon or button
2. Show AI Assistant interface:
   - Patient context header
   - Chat interface for queries
3. Type a query:
   ```
   Summarize this patient's mental health status over the past two weeks
   ```
4. Show AI-generated analysis based on:
   - Check-in data
   - Assessment results
   - Conversation history
   - Risk events
5. Type another query:
   ```
   What coping strategies might help this patient?
   ```
6. Show AI suggestions

**UI Elements to Highlight:**

- Context-aware AI responses
- Clinical language appropriate for physicians
- Evidence-based suggestions

**Talking Points:**
> "The AI Assistant helps doctors quickly understand patient status. It has access to all patient data - check-ins, assessments, and conversation history. I can ask for a two-week summary, and it synthesizes all available data. I can also ask for treatment suggestions, and it provides evidence-based recommendations considering the patient's specific situation."

---

### 2.8 Appointment Management (1.5 min)

**URL:** `/appointments`

**Steps:**

1. Navigate to Appointments via top nav
2. Show layout:
   - Left column: Calendar widget
   - Right area: Appointment list and stats

3. Show Calendar:
   - Month navigation (< Previous | Next >)
   - Days with appointments marked
   - Today highlighted
   - Click a date to filter appointments

4. Show Statistics Cards (4):
   - Today's Appointments
   - Pending Appointments
   - Confirmed Appointments
   - This Week's Total

5. Show Appointment Cards:
   - Patient name
   - Type badge (Initial/Follow-up/Emergency/Consultation)
   - Time range
   - Reason (if provided)
   - Action buttons:
     - ✓ Confirm (for pending)
     - ✓ Complete (for confirmed)
     - ⚠ No Show
     - ✗ Cancel

6. Click "Create Appointment" button
7. Show Create Appointment Modal:
   - Patient dropdown (all connected patients)
   - Date picker (min = today)
   - Start time and End time
   - Type dropdown
   - Reason textarea
8. Create emergency appointment:
   - Patient: Emily Chen
   - Date: Tomorrow
   - Time: 9:00 AM - 10:00 AM
   - Type: Emergency
   - Reason: "Emergency mental health crisis follow-up"
9. Click "Create" and show success

**UI Elements to Highlight:**

- Interactive calendar
- Clear appointment statistics
- Action buttons for status management
- Easy appointment creation

**Talking Points:**
> "Appointment management provides a clear calendar view. Statistics show today's schedule and pending confirmations. Doctors can confirm, complete, mark as no-show, or cancel appointments with one click.
>
> For the high-risk event we just reviewed, let's create an emergency appointment for Emily Chen tomorrow morning. The system will automatically notify the patient."

---

### 2.9 Doctor Messages (1 min)

**URL:** `/doctor-messages`

**Steps:**

1. Navigate to Messages via top nav
2. Show Thread List:
   - Search functionality
   - Patient name and avatar
   - Last message preview
   - Unread indicator
3. Click on a patient thread
4. Show conversation interface:
   - Back button with patient info header
   - Message history (auto-scroll to bottom)
   - Patient messages (left, card background)
   - Doctor messages (right, blue background)
   - Message input at bottom
5. Send a message:
   ```
   Hi Emily, I've scheduled an emergency appointment for tomorrow at 9 AM. Please confirm you received this message. If you need to talk before then, please call the crisis line: 988.
   ```
6. Show message sent

**UI Elements to Highlight:**

- Searchable thread list
- Clear message ownership
- Real-time delivery
- Easy reply interface

**Talking Points:**
> "The doctor messaging interface mirrors the patient experience. All patient conversations are listed with search capability. Messages are delivered in real-time, ensuring urgent communications are received immediately."

---

### 2.10 Generate Pre-Visit Report (45 sec) ⭐ KEY FEATURE

**URL:** `/patients/[id]` (Patient Details page)

**Steps:**

1. Navigate to a patient's detail page (e.g., Michael Roberts)
2. Find the "Generate Report" button in the header area
3. Click to generate pre-visit summary
4. Show loading state while PDF is generated
5. Download the generated PDF
6. Open and briefly show PDF contents:
   - Patient demographics
   - Current medications and conditions
   - Recent check-in summary (mood trends, sleep patterns)
   - Assessment scores with severity levels
   - AI conversation highlights (if applicable)
   - Risk event history

**UI Elements to Highlight:**

- One-click report generation
- PDF download functionality
- Professional report format

**Talking Points:**
> "Before appointments, doctors can generate a comprehensive pre-visit summary with one click. The PDF report includes patient demographics, recent health metrics, assessment scores, and any risk events. This saves preparation time and ensures doctors have all relevant information at hand."

---

### 2.11 Doctor Profile Management (30 sec)

**URL:** `/my-profile`

**Steps:**

1. Navigate to Profile via top nav (doctor icon or settings)
2. Show doctor profile form fields:

   **Basic Information:**
   - First name / Last name
   - Specialty (dropdown)
   - Phone number
   - Years of experience

   **Professional Information:**
   - Bio / Description (text area)
   - Education background
   - Languages spoken

   **Practice Information:**
   - Clinic name
   - Clinic address
   - Consultation hours

3. Make a small edit (e.g., update bio)
4. Click "Save" and show success notification

**UI Elements to Highlight:**

- Professional profile fields
- Specialty selection
- Multi-language support indication

**Talking Points:**
> "Doctors can manage their professional profile which is visible to connected patients. This includes their specialty, experience, education, and consultation hours. A complete profile helps patients understand their doctor's background."

---

## Part 3: Special Features Demo

### 3.1 Multi-language Switch (45 sec)

**Steps:**

1. Find language switcher (top right of any page)
2. Show current language (EN)
3. Click and switch to 中文
4. Show instant UI update:
   - Navigation labels change
   - Button text changes
   - Form labels change
   - Dates format appropriately
5. Navigate to Assessment to show bilingual questions
6. Switch back to English

**Supported Languages:**
- English (EN)
- 中文 (Chinese)
- (Additional languages can be added)

**Talking Points:**
> "Heart Guardian AI supports multiple languages with instant switching. All interface elements update immediately - no page refresh needed. This is crucial for serving diverse patient populations, especially political refugees who may prefer their native language."

---

### 3.2 Dark/Light Theme Toggle (30 sec)

**Steps:**

1. Find theme toggle button (sun/moon icon, top right)
2. Current theme: Light (default)
3. Click to switch to Dark mode
4. Show dark interface:
   - Dark backgrounds
   - Adjusted text colors
   - Preserved readability
   - Eye-friendly for night use
5. Navigate to a different page to show consistency
6. Switch back to Light mode

**Talking Points:**
> "The system supports both dark and light themes. Dark mode is easier on the eyes during nighttime use, which is important for patients who may check in late at night during difficult moments. The theme preference is remembered across sessions."

---

### 3.3 Real-time Message Synchronization (1 min)

**Steps:**

1. Arrange patient and doctor browser windows side by side
2. In patient window: Open `/conversations` → Doctor Messages tab
3. In doctor window: Open `/doctor-messages`
4. From patient window, send:
   ```
   I'm feeling anxious about tomorrow's appointment.
   ```
5. Show instant notification in doctor window
6. Show message appear in doctor's conversation without refresh
7. Doctor replies:
   ```
   That's completely normal. Let's discuss your concerns at the start of our session. Remember, you can always reach out to me here.
   ```
8. Show instant delivery in patient window

**Talking Points:**
> "Doctor-patient messaging uses WebSocket for real-time communication. Messages appear instantly without refreshing. Watch as I send a message from the patient portal... it appears immediately in the doctor's window. This ensures critical communications are never delayed."

---

### 3.4 Responsive Design (45 sec)

**Steps:**

1. Using browser developer tools or by resizing window
2. Narrow window to mobile width (~375px)
3. Show mobile adaptation:
   - Bottom navigation bar appears (patient portal)
   - Cards stack vertically
   - Touch-friendly button sizes
   - Hamburger menu for additional options
4. Navigate between pages to show consistency
5. Return to desktop width

**Talking Points:**
> "Heart Guardian AI uses a mobile-first responsive design. When viewed on a phone, the interface automatically adapts - navigation moves to the bottom, cards stack for easy scrolling, and buttons are sized for touch interaction. Every feature remains fully functional."

---

### 3.5 PWA Support and Offline Indicator (30 sec)

**Steps:**

1. Show that the app can be installed as PWA
2. Demonstrate offline indicator:
   - Disconnect network (or use DevTools)
   - Show offline indicator banner appears
   - Reconnect to show indicator disappears

**Talking Points:**
> "The system supports Progressive Web App installation, allowing patients to add it to their phone's home screen for a native app-like experience. If network connectivity is lost, an offline indicator appears, alerting users that some features may be unavailable."

---

## Suggested Talking Points

### Opening

> "Hello everyone, today I'll be demonstrating Heart Guardian AI - a mental health support platform designed specifically for political trauma survivors.
>
> Heart Guardian AI provides five core capabilities:
> 1. 24/7 AI emotional support with real-time crisis detection
> 2. Comprehensive mental health tracking with standardized assessments
> 3. Secure doctor-patient communication with real-time messaging
> 4. Risk event management and clinical decision support
> 5. Complete data sovereignty for patients
>
> I'll demonstrate the complete functionality from both patient and doctor perspectives."

### Closing Summary

> "That concludes our demonstration of Heart Guardian AI's core features. Let me summarize:
>
> **For Patients:**
> - 24/7 AI companion for emotional support
> - Daily mood and health tracking
> - Standardized psychological assessments (PHQ-9, GAD-7, PCL-5)
> - Secure communication with treating physicians
> - Full control over personal health data
>
> **For Doctors:**
> - Comprehensive patient dashboard with risk prioritization
> - AI-powered patient analysis and clinical insights
> - Real-time risk queue for crisis management
> - Efficient appointment and communication management
>
> **Key Differentiators:**
> - Multi-language risk detection optimized for political trauma expressions
> - Complete audit trail for compliance
> - Privacy-first architecture with patient data sovereignty
>
> Thank you for watching!"

---

## Troubleshooting

### Q: Demo data not showing?

```bash
# Re-run the seed script
cd backend
python scripts/seed_demo_data.py
```

### Q: Login failed?

- Confirm using correct password: `Demo123!`
- Check if backend service is running on port 8000
- Check if frontend service is running on port 3000
- Clear browser cache and retry
- Check browser console for errors

### Q: Risk detection not triggering?

- Ensure using messages with clear risk keywords
- Example trigger texts:
  - "I don't want to live anymore"
  - "I want to end my life"
  - "I feel hopeless, life has no meaning"
  - "I'm thinking about hurting myself"
- Check backend console for AI processing logs

### Q: Messages not syncing in real-time?

- Check WebSocket connection status in browser DevTools
- Ensure both windows are logged in with valid sessions
- Refresh pages to re-establish WebSocket connection
- Check backend console for WebSocket errors

### Q: Theme or language not persisting?

- Check localStorage in browser DevTools
- Clear cache and re-login
- Verify no browser extensions blocking storage

---

## Recording Checklist

### Before Recording

- [ ] Backend service running (port 8000)
- [ ] Frontend service running (port 3000)
- [ ] Demo data initialized (seed script run)
- [ ] Browser cache cleared
- [ ] Screen recording software ready
- [ ] Microphone tested and quality verified
- [ ] Two browser windows prepared (patient + doctor)
- [ ] Windows arranged for split-screen viewing
- [ ] Notifications disabled on computer
- [ ] Phone silenced

### During Recording

- [ ] Speak at moderate pace, not too fast
- [ ] Allow sufficient time on each feature for viewer comprehension
- [ ] Emphasize key features (AI chat, risk detection, crisis modal)
- [ ] Use smooth mouse movements
- [ ] Pause appropriately after important demonstrations
- [ ] Narrate actions before performing them
- [ ] Highlight UI elements being discussed

### After Recording

- [ ] Review video for completeness
- [ ] Verify audio clarity throughout
- [ ] Confirm all key features demonstrated:
  **Patient Portal:**
  - [ ] Patient login and dashboard
  - [ ] New patient registration (optional)
  - [ ] Health center overview
  - [ ] AI chat with crisis detection
  - [ ] Daily check-in
  - [ ] Psychological assessment (PHQ-9, GAD-7, PCL-5)
  - [ ] Doctor connection management
  - [ ] Doctor-patient messaging
  - [ ] My appointments view
  - [ ] Profile management
  - [ ] Data export
  - [ ] Change password
  **Doctor Portal:**
  - [ ] Doctor login and patient list
  - [ ] Add patient / Create patient
  - [ ] Pending connection requests
  - [ ] Risk queue management
  - [ ] Patient details page
  - [ ] AI assistant for patient analysis
  - [ ] Generate pre-visit report
  - [ ] Appointment management (calendar, create, actions)
  - [ ] Doctor messaging
  - [ ] Doctor profile management
  **Special Features:**
  - [ ] Multi-language switch
  - [ ] Theme toggle (dark/light)
  - [ ] Real-time messaging demo
  - [ ] Responsive design demo
  - [ ] PWA / Offline indicator
- [ ] No sensitive information leaked
- [ ] Demo accounts used (not real data)

---

## Appendix: Demo Data Details

### Patient: Michael Roberts

- **Email**: `patient.michael@demo.com`
- **Risk Level**: MEDIUM
- **Mood Trend**: Gradually improving (3→7)
- **Latest PHQ-9**: Moderate (~12 points)
- **Latest GAD-7**: Mild (~8 points)
- **Check-in Compliance**: 90%+
- **Treating Physician**: Dr. Sarah Mitchell
- **Demo Focus**: Show positive progress, daily tracking

### Patient: Emily Chen

- **Email**: `patient.emily@demo.com`
- **Risk Level**: HIGH ⚠️
- **Mood Trend**: Fluctuating (2-7)
- **Latest PHQ-9**: Severe (~20 points)
- **Latest GAD-7**: Moderate-Severe (~15 points)
- **Risk Events**: Suicidal ideation (CRITICAL)
- **Treating Physician**: Dr. Sarah Mitchell
- **Demo Focus**: Risk detection, crisis intervention, emergency appointment

### Patient: David Wilson

- **Email**: `patient.david@demo.com`
- **Risk Level**: LOW
- **Mood Trend**: Stable (6-7)
- **Latest PHQ-9**: Mild (~6 points)
- **Latest GAD-7**: Minimal (~3 points)
- **Check-in Compliance**: 95%+
- **Treating Physician**: Dr. James Thompson
- **Demo Focus**: Data export, long-term stable management

### Doctor: Dr. Sarah Mitchell

- **Email**: `dr.sarah@demo.com`
- **Specialty**: Clinical Psychology
- **Patients**: Michael Roberts, Emily Chen
- **Demo Focus**: Main doctor account for demo

### Doctor: Dr. James Thompson

- **Email**: `dr.james@demo.com`
- **Specialty**: Psychiatry
- **Patients**: David Wilson
- **Demo Focus**: Secondary doctor for multi-doctor scenarios

---

## Navigation Reference

### Patient Portal Routes

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | Login and registration |
| `/dashboard` | Dashboard | Main patient homepage |
| `/conversations` | Conversations | AI chat + Doctor messages (tabs) |
| `/health` | Health Center | Overview of check-ins and assessments |
| `/checkin` | Daily Check-in | Record mood, sleep, medication |
| `/assessment` | Assessments | PHQ-9, GAD-7, PCL-5 |
| `/my-appointments` | My Appointments | View and manage appointments |
| `/profile` | Profile | Personal info, doctor connections |
| `/data-export` | Data Export | Export personal health data |
| `/change-password` | Change Password | Update account password |

### Doctor Portal Routes

| Route | Page | Description |
|-------|------|-------------|
| `/patients` | Patient List | All connected patients |
| `/patients/create` | Create Patient | Create new patient account |
| `/patients/[id]` | Patient Details | Individual patient view |
| `/patients/[id]/ai-assistant` | AI Assistant | AI-powered patient analysis |
| `/pending-requests` | Pending Requests | Connection request management |
| `/risk-queue` | Risk Queue | Unreviewed risk events |
| `/appointments` | Appointments | Calendar and scheduling |
| `/doctor-messages` | Messages | Patient communication |
| `/my-profile` | My Profile | Doctor profile settings |

---

## Complete Feature Checklist

### Patient Portal Features

| Feature | Section | Status |
|---------|---------|--------|
| Login with multi-language | 1.1 | ✅ |
| New patient registration | 1.1b | ✅ |
| Dashboard with quick mood | 1.2 | ✅ |
| Health Center overview | 1.3 | ✅ |
| AI emotional support chat | 1.4 | ✅ |
| Crisis detection & modal | 1.4 | ✅ |
| Daily check-in form | 1.5 | ✅ |
| Psychological assessments | 1.6 | ✅ |
| Doctor connection management | 1.7 | ✅ |
| Doctor-patient messaging | 1.8 | ✅ |
| My Appointments view | 1.9 | ✅ |
| Profile management | 1.10 | ✅ |
| Data export | 1.11 | ✅ |
| Change password | 1.12 | ✅ |

### Doctor Portal Features

| Feature | Section | Status |
|---------|---------|--------|
| Doctor login | 2.1 | ✅ |
| Patient list with metrics | 2.2 | ✅ |
| Add/Create patient | 2.3 | ✅ |
| Pending connection requests | 2.4 | ✅ |
| Risk queue management | 2.5 | ✅ |
| Patient details page | 2.6 | ✅ |
| AI Assistant for analysis | 2.7 | ✅ |
| Appointment management | 2.8 | ✅ |
| Doctor messaging | 2.9 | ✅ |
| Generate pre-visit report | 2.10 | ✅ |
| Doctor profile management | 2.11 | ✅ |

### Special Features

| Feature | Section | Status |
|---------|---------|--------|
| Multi-language switch | 3.1 | ✅ |
| Dark/Light theme | 3.2 | ✅ |
| Real-time messaging | 3.3 | ✅ |
| Responsive design | 3.4 | ✅ |
| PWA & offline indicator | 3.5 | ✅ |

---

*Document Version: 2.1*
*Last Updated: 2025-01*
*Total Features Documented: 30+*
