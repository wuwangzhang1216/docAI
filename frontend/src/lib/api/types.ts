/**
 * API types and interfaces.
 */

// ========== Generic Types ==========

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
  search?: string;
}

// ========== Auth Types ==========

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_type: 'PATIENT' | 'DOCTOR' | 'ADMIN';
  user_id: string;
  password_must_change: boolean;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// ========== Chat Types ==========

export interface ChatResponse {
  reply: string;
  conversation_id: string;
  risk_alert: boolean;
}

export interface StreamEventRiskCheck {
  event: 'risk_check';
  data: { level: string; risk_type: string | null };
}

export interface StreamEventToolStart {
  event: 'tool_start';
  data: { tool_id: string; tool_name: string };
}

export interface StreamEventToolEnd {
  event: 'tool_end';
  data: { tool_id: string; tool_name: string; result_preview: string };
}

export interface StreamEventTextDelta {
  event: 'text_delta';
  data: { text: string };
}

export interface StreamEventMessageComplete {
  event: 'message_complete';
  data: { content: string; risk: string | null };
}

export interface StreamEventMetadata {
  event: 'metadata';
  data: { conversation_id: string; risk_alert: boolean };
}

export interface StreamEventError {
  event: 'error';
  data: { message: string };
}

export type StreamEvent =
  | StreamEventRiskCheck
  | StreamEventToolStart
  | StreamEventToolEnd
  | StreamEventTextDelta
  | StreamEventMessageComplete
  | StreamEventMetadata
  | StreamEventError;

export interface StreamChatCallbacks {
  onRiskCheck?: (level: string, riskType: string | null) => void;
  onToolStart?: (toolId: string, toolName: string) => void;
  onToolEnd?: (toolId: string, toolName: string, resultPreview: string) => void;
  onTextDelta?: (text: string) => void;
  onMessageComplete?: (content: string, risk: string | null) => void;
  onMetadata?: (conversationId: string, riskAlert: boolean) => void;
  onError?: (message: string) => void;
}

// ========== Clinical Types ==========

export interface CheckinData {
  mood_score: number;
  sleep_hours: number;
  sleep_quality: number;
  medication_taken: boolean;
  notes?: string;
}

export interface CheckinResponse {
  id: string;
  patient_id: string;
  checkin_date: string;
  mood_score: number;
  sleep_hours: number;
  sleep_quality: number;
  medication_taken: boolean;
  notes?: string;
  created_at: string;
}

export interface AssessmentResponse {
  id: string;
  patient_id: string;
  assessment_type: string;
  total_score: number;
  severity: string;
  risk_flags?: Record<string, unknown>;
  created_at: string;
}

// ========== Patient Types ==========

export interface PatientOverview {
  patient_id: string;
  patient_name: string;
  recent_mood_avg: number | null;
  latest_phq9: number | null;
  latest_gad7: number | null;
  unreviewed_risks: number;
}

export interface PatientProfile {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  date_of_birth?: string;
  phone?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  emergency_contact_relationship?: string;
  primary_doctor_id?: string;
  consent_signed: boolean;
  consent_signed_at?: string;
  created_at: string;
  updated_at?: string;
  gender?: string;
  preferred_language?: string;
  address?: string;
  city?: string;
  country?: string;
  current_medications?: string;
  medical_conditions?: string;
  allergies?: string;
  therapy_history?: string;
  mental_health_goals?: string;
  support_system?: string;
  triggers_notes?: string;
  coping_strategies?: string;
}

export interface PatientProfileUpdate {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  phone?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  emergency_contact_relationship?: string;
  gender?: string;
  preferred_language?: string;
  address?: string;
  city?: string;
  country?: string;
  current_medications?: string;
  medical_conditions?: string;
  allergies?: string;
  therapy_history?: string;
  mental_health_goals?: string;
  support_system?: string;
  triggers_notes?: string;
  coping_strategies?: string;
}

export interface PatientListParams extends PaginationParams {
  sort_by?: 'risk' | 'name' | 'mood';
  sort_order?: 'asc' | 'desc';
}

// ========== Doctor Types ==========

export interface DoctorProfile {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  license_number?: string;
  specialty?: string;
  created_at: string;
  updated_at?: string;
  phone?: string;
  bio?: string;
  years_of_experience?: string;
  education?: string;
  languages?: string;
  clinic_name?: string;
  clinic_address?: string;
  clinic_city?: string;
  clinic_country?: string;
  consultation_hours?: string;
}

export interface DoctorProfileUpdate {
  first_name?: string;
  last_name?: string;
  license_number?: string;
  specialty?: string;
  phone?: string;
  bio?: string;
  years_of_experience?: string;
  education?: string;
  languages?: string;
  clinic_name?: string;
  clinic_address?: string;
  clinic_city?: string;
  clinic_country?: string;
  consultation_hours?: string;
}

export interface DoctorPublicInfo {
  id: string;
  full_name: string;
  specialty?: string;
}

export interface DoctorPublicProfile {
  id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  specialty?: string;
  phone?: string;
  bio?: string;
  years_of_experience?: string;
  education?: string;
  languages?: string;
  clinic_name?: string;
  clinic_address?: string;
  clinic_city?: string;
  clinic_country?: string;
  consultation_hours?: string;
}

export interface DoctorCreatePatientRequest {
  email: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  gender?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  preferred_language?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  emergency_contact_relationship?: string;
  current_medications?: string;
  medical_conditions?: string;
  allergies?: string;
  therapy_history?: string;
  mental_health_goals?: string;
  support_system?: string;
  triggers_notes?: string;
  coping_strategies?: string;
}

export interface DoctorCreatePatientResponse {
  patient_id: string;
  user_id: string;
  email: string;
  full_name: string;
  default_password: string;
  message: string;
}

// ========== Risk Types ==========

export interface RiskEvent {
  id: string;
  patient_id: string;
  patient_name?: string;
  conversation_id?: string;
  risk_level: string;
  risk_type?: string;
  trigger_text?: string;
  ai_confidence?: number;
  doctor_reviewed: boolean;
  doctor_notes?: string;
  created_at: string;
}

export interface RiskQueueParams extends PaginationParams {
  risk_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  patient_id?: string;
}

// ========== Connection Types ==========

export interface ConnectionRequestResponse {
  id: string;
  doctor_id: string;
  patient_id: string;
  patient_name: string;
  patient_email: string;
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED';
  message?: string;
  created_at: string;
  updated_at?: string;
  responded_at?: string;
}

export interface PatientConnectionRequestView {
  id: string;
  doctor_id: string;
  doctor_name: string;
  doctor_specialty?: string;
  message?: string;
  created_at: string;
}

export interface ConnectionRequestStatusResponse {
  status: string;
  request_id: string;
  message?: string;
}

export interface ConnectionRequestParams extends PaginationParams {
  status?: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED';
}

// ========== Messaging Types ==========

export type MessageType = 'TEXT' | 'IMAGE' | 'FILE';

export interface MessageAttachment {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  url: string;
  thumbnail_url?: string;
}

export interface MessageResponse {
  id: string;
  thread_id: string;
  sender_type: 'DOCTOR' | 'PATIENT';
  sender_id: string;
  sender_name: string;
  content?: string;
  message_type: MessageType;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  attachments: MessageAttachment[];
}

export interface ThreadSummary {
  id: string;
  other_party_id: string;
  other_party_name: string;
  other_party_type: 'DOCTOR' | 'PATIENT';
  last_message_preview?: string;
  last_message_at?: string;
  last_message_type?: MessageType;
  unread_count: number;
  can_send_message: boolean;
  created_at: string;
}

export interface ThreadDetail {
  id: string;
  other_party_id: string;
  other_party_name: string;
  other_party_type: 'DOCTOR' | 'PATIENT';
  can_send_message: boolean;
  messages: MessageResponse[];
  has_more: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  total_unread: number;
  threads: { thread_id: string; unread_count: number }[];
}

export interface AttachmentUploadResponse {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  s3_key: string;
  thumbnail_s3_key?: string;
}

export interface ThreadListParams extends PaginationParams {}

// ========== Report Types ==========

export interface ReportGenerateRequest {
  include_risk_events?: boolean;
  include_checkin_trend?: boolean;
  days_for_trend?: number;
}

export interface ReportResponse {
  report_id: string;
  patient_id: string;
  report_type: string;
  pdf_url: string;
  expires_at: string;
  generated_at: string;
}

export interface ReportListItem {
  report_id: string;
  patient_id: string;
  patient_name?: string;
  report_type: string;
  generated_at: string;
}

export interface ReportListResponse {
  reports: ReportListItem[];
  total: number;
}

export interface PreVisitSummary {
  id: string;
  patient_id: string;
  conversation_id?: string;
  scheduled_visit?: string;
  chief_complaint?: string;
  phq9_score?: number;
  gad7_score?: number;
  doctor_viewed: boolean;
  doctor_viewed_at?: string;
  created_at: string;
}

// ========== Doctor AI Chat Types ==========

export interface DoctorAIChatRequest {
  message: string;
  conversation_id?: string;
}

export interface DoctorAIChatResponse {
  response: string;
  conversation_id: string;
  patient_name: string;
}

export interface DoctorConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface DoctorConversationListItem {
  id: string;
  patient_id: string;
  patient_name?: string;
  message_count: number;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface DoctorConversationDetail {
  id: string;
  doctor_id: string;
  patient_id: string;
  patient_name?: string;
  messages: DoctorConversationMessage[];
  summary?: string;
  created_at: string;
  updated_at: string;
}

// ========== Appointment Types ==========

export type AppointmentStatus = 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
export type AppointmentType = 'INITIAL' | 'FOLLOW_UP' | 'EMERGENCY' | 'CONSULTATION';

export interface AppointmentPatient {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

export interface AppointmentDoctor {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  specialty?: string;
}

export interface AppointmentResponse {
  id: string;
  doctor_id: string;
  patient_id: string;
  pre_visit_summary_id?: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  reason?: string;
  notes?: string;
  patient_notes?: string;
  reminder_24h_sent: boolean;
  reminder_1h_sent: boolean;
  cancelled_by?: string;
  cancel_reason?: string;
  cancelled_at?: string;
  completed_at?: string;
  completion_notes?: string;
  is_past: boolean;
  is_cancellable: boolean;
  created_at: string;
  updated_at: string;
  patient?: AppointmentPatient;
  doctor?: AppointmentDoctor;
}

export interface AppointmentListItem {
  id: string;
  patient_id: string;
  doctor_id: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  reason?: string;
  is_past: boolean;
  is_cancellable: boolean;
  patient?: AppointmentPatient;
  doctor?: AppointmentDoctor;
}

export interface AppointmentCreate {
  patient_id: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  appointment_type?: AppointmentType;
  reason?: string;
  notes?: string;
  pre_visit_summary_id?: string;
}

export interface AppointmentUpdate {
  appointment_date?: string;
  start_time?: string;
  end_time?: string;
  appointment_type?: AppointmentType;
  reason?: string;
  notes?: string;
  patient_notes?: string;
  pre_visit_summary_id?: string;
}

export interface CalendarDaySlot {
  id: string;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  appointment_type: AppointmentType;
  patient_name: string;
  patient_id: string;
}

export interface CalendarDay {
  date: string;
  appointments: CalendarDaySlot[];
  total_count: number;
}

export interface CalendarMonthView {
  year: number;
  month: number;
  days: CalendarDay[];
  total_appointments: number;
}

export interface CalendarWeekView {
  start_date: string;
  end_date: string;
  days: CalendarDay[];
  total_appointments: number;
}

export interface AppointmentStats {
  total: number;
  pending: number;
  confirmed: number;
  completed: number;
  cancelled: number;
  no_show: number;
  today_count: number;
  this_week_count: number;
  this_month_count: number;
}

export interface AppointmentListParams {
  status?: AppointmentStatus;
  appointment_type?: AppointmentType;
  patient_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// ========== Data Export Types ==========

export type ExportFormat = 'JSON' | 'CSV' | 'PDF_SUMMARY';
export type ExportStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED' | 'DOWNLOADED';

export interface ExportRequestCreate {
  export_format?: ExportFormat;
  include_profile?: boolean;
  include_checkins?: boolean;
  include_assessments?: boolean;
  include_conversations?: boolean;
  include_messages?: boolean;
  date_from?: string;
  date_to?: string;
}

export interface ExportRequestResponse {
  id: string;
  patient_id: string;
  export_format: ExportFormat;
  status: ExportStatus;
  include_profile: boolean;
  include_checkins: boolean;
  include_assessments: boolean;
  include_conversations: boolean;
  include_messages: boolean;
  date_from?: string;
  date_to?: string;
  progress_percent: number;
  error_message?: string;
  file_size_bytes?: number;
  download_count: number;
  max_downloads: number;
  download_token?: string;
  can_download: boolean;
  is_expired: boolean;
  is_processing: boolean;
  created_at: string;
  processing_started_at?: string;
  completed_at?: string;
  download_expires_at?: string;
  last_downloaded_at?: string;
}

export interface ExportRequestListItem {
  id: string;
  export_format: ExportFormat;
  status: ExportStatus;
  progress_percent: number;
  file_size_bytes?: number;
  download_token?: string;
  can_download: boolean;
  is_expired: boolean;
  created_at: string;
  completed_at?: string;
}

export interface ExportProgressResponse {
  id: string;
  status: ExportStatus;
  progress_percent: number;
  error_message?: string;
}
