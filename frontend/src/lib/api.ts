/**
 * API client for communicating with the backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface ApiError {
  detail: string
}

// Auth error event for global handling
type AuthErrorCallback = () => void
let onAuthErrorCallback: AuthErrorCallback | null = null

export function setAuthErrorHandler(callback: AuthErrorCallback): void {
  onAuthErrorCallback = callback
}

export class AuthenticationError extends Error {
  constructor(message: string = 'Authentication failed') {
    super(message)
    this.name = 'AuthenticationError'
  }
}

interface LoginResponse {
  access_token: string
  token_type: string
  user_type: 'PATIENT' | 'DOCTOR' | 'ADMIN'
  user_id: string
  password_must_change: boolean
}

interface ChatResponse {
  reply: string
  conversation_id: string
  risk_alert: boolean
}

// Streaming chat event types
interface StreamEventRiskCheck {
  event: 'risk_check'
  data: { level: string; risk_type: string | null }
}

interface StreamEventToolStart {
  event: 'tool_start'
  data: { tool_id: string; tool_name: string }
}

interface StreamEventToolEnd {
  event: 'tool_end'
  data: { tool_id: string; tool_name: string; result_preview: string }
}

interface StreamEventTextDelta {
  event: 'text_delta'
  data: { text: string }
}

interface StreamEventMessageComplete {
  event: 'message_complete'
  data: { content: string; risk: string | null }
}

interface StreamEventMetadata {
  event: 'metadata'
  data: { conversation_id: string; risk_alert: boolean }
}

interface StreamEventError {
  event: 'error'
  data: { message: string }
}

type StreamEvent =
  | StreamEventRiskCheck
  | StreamEventToolStart
  | StreamEventToolEnd
  | StreamEventTextDelta
  | StreamEventMessageComplete
  | StreamEventMetadata
  | StreamEventError

// Callbacks for streaming chat
interface StreamChatCallbacks {
  onRiskCheck?: (level: string, riskType: string | null) => void
  onToolStart?: (toolId: string, toolName: string) => void
  onToolEnd?: (toolId: string, toolName: string, resultPreview: string) => void
  onTextDelta?: (text: string) => void
  onMessageComplete?: (content: string, risk: string | null) => void
  onMetadata?: (conversationId: string, riskAlert: boolean) => void
  onError?: (message: string) => void
}

interface CheckinData {
  mood_score: number
  sleep_hours: number
  sleep_quality: number
  medication_taken: boolean
  notes?: string
}

interface CheckinResponse {
  id: string
  patient_id: string
  checkin_date: string
  mood_score: number
  sleep_hours: number
  sleep_quality: number
  medication_taken: boolean
  notes?: string
  created_at: string
}

interface AssessmentResponse {
  id: string
  patient_id: string
  assessment_type: string
  total_score: number
  severity: string
  risk_flags?: Record<string, unknown>
  created_at: string
}

interface PatientOverview {
  patient_id: string
  patient_name: string
  recent_mood_avg: number | null
  latest_phq9: number | null
  latest_gad7: number | null
  unreviewed_risks: number
}

// Generic paginated response
interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// Query params for paginated list
interface PaginationParams {
  limit?: number
  offset?: number
  search?: string
}

interface PatientListParams extends PaginationParams {
  sort_by?: 'risk' | 'name' | 'mood'
  sort_order?: 'asc' | 'desc'
}

interface RiskQueueParams extends PaginationParams {
  risk_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  patient_id?: string
}

interface ConnectionRequestParams extends PaginationParams {
  status?: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'
}

interface ThreadListParams extends PaginationParams {
  // search is inherited from PaginationParams - searches by other party's name
}

interface RiskEvent {
  id: string
  patient_id: string
  patient_name?: string
  conversation_id?: string
  risk_level: string
  risk_type?: string
  trigger_text?: string
  ai_confidence?: number
  doctor_reviewed: boolean
  doctor_notes?: string
  created_at: string
}

interface PatientProfile {
  id: string
  user_id: string
  first_name: string
  last_name: string
  full_name?: string
  date_of_birth?: string
  phone?: string
  emergency_contact?: string
  emergency_phone?: string
  emergency_contact_relationship?: string
  primary_doctor_id?: string
  consent_signed: boolean
  consent_signed_at?: string
  created_at: string
  updated_at?: string

  // Extended profile fields
  gender?: string
  preferred_language?: string
  address?: string
  city?: string
  country?: string

  // Medical information
  current_medications?: string
  medical_conditions?: string
  allergies?: string

  // Mental health context
  therapy_history?: string
  mental_health_goals?: string
  support_system?: string
  triggers_notes?: string
  coping_strategies?: string
}

// Connection request types
interface ConnectionRequestResponse {
  id: string
  doctor_id: string
  patient_id: string
  patient_name: string
  patient_email: string
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'
  message?: string
  created_at: string
  updated_at?: string
  responded_at?: string
}

interface PatientConnectionRequestView {
  id: string
  doctor_id: string
  doctor_name: string
  doctor_specialty?: string
  message?: string
  created_at: string
}

interface DoctorPublicInfo {
  id: string
  full_name: string
  specialty?: string
}

interface DoctorProfile {
  id: string
  user_id: string
  first_name: string
  last_name: string
  full_name?: string
  license_number?: string
  specialty?: string
  created_at: string
  updated_at?: string
  phone?: string
  bio?: string
  years_of_experience?: string
  education?: string
  languages?: string
  clinic_name?: string
  clinic_address?: string
  clinic_city?: string
  clinic_country?: string
  consultation_hours?: string
}

interface DoctorProfileUpdate {
  first_name?: string
  last_name?: string
  license_number?: string
  specialty?: string
  phone?: string
  bio?: string
  years_of_experience?: string
  education?: string
  languages?: string
  clinic_name?: string
  clinic_address?: string
  clinic_city?: string
  clinic_country?: string
  consultation_hours?: string
}

interface DoctorPublicProfile {
  id: string
  first_name: string
  last_name: string
  full_name?: string
  specialty?: string
  phone?: string
  bio?: string
  years_of_experience?: string
  education?: string
  languages?: string
  clinic_name?: string
  clinic_address?: string
  clinic_city?: string
  clinic_country?: string
  consultation_hours?: string
}

// ========== Messaging Types ==========

type MessageType = 'TEXT' | 'IMAGE' | 'FILE'

interface MessageAttachment {
  id: string
  file_name: string
  file_type: string
  file_size: number
  url: string
  thumbnail_url?: string
}

interface MessageResponse {
  id: string
  thread_id: string
  sender_type: 'DOCTOR' | 'PATIENT'
  sender_id: string
  sender_name: string
  content?: string
  message_type: MessageType
  is_read: boolean
  read_at?: string
  created_at: string
  attachments: MessageAttachment[]
}

interface ThreadSummary {
  id: string
  other_party_id: string
  other_party_name: string
  other_party_type: 'DOCTOR' | 'PATIENT'
  last_message_preview?: string
  last_message_at?: string
  last_message_type?: MessageType
  unread_count: number
  can_send_message: boolean
  created_at: string
}

interface ThreadDetail {
  id: string
  other_party_id: string
  other_party_name: string
  other_party_type: 'DOCTOR' | 'PATIENT'
  can_send_message: boolean
  messages: MessageResponse[]
  has_more: boolean
  created_at: string
}

interface UnreadCountResponse {
  total_unread: number
  threads: { thread_id: string; unread_count: number }[]
}

interface AttachmentUploadResponse {
  id: string
  file_name: string
  file_type: string
  file_size: number
  s3_key: string
  thumbnail_s3_key?: string
}

// ========== Report Types ==========

interface ReportGenerateRequest {
  include_risk_events?: boolean
  include_checkin_trend?: boolean
  days_for_trend?: number
}

interface ReportResponse {
  report_id: string
  patient_id: string
  report_type: string
  pdf_url: string
  expires_at: string
  generated_at: string
}

interface ReportListItem {
  report_id: string
  patient_id: string
  patient_name?: string
  report_type: string
  generated_at: string
}

interface ReportListResponse {
  reports: ReportListItem[]
  total: number
}

interface PreVisitSummary {
  id: string
  patient_id: string
  conversation_id?: string
  scheduled_visit?: string
  chief_complaint?: string
  phq9_score?: number
  gad7_score?: number
  doctor_viewed: boolean
  doctor_viewed_at?: string
  created_at: string
}

interface ConnectionRequestStatusResponse {
  status: string
  request_id: string
  message?: string
}

interface PatientProfileUpdate {
  first_name?: string
  last_name?: string
  date_of_birth?: string
  phone?: string
  emergency_contact?: string
  emergency_phone?: string
  emergency_contact_relationship?: string
  gender?: string
  preferred_language?: string
  address?: string
  city?: string
  country?: string
  current_medications?: string
  medical_conditions?: string
  allergies?: string
  therapy_history?: string
  mental_health_goals?: string
  support_system?: string
  triggers_notes?: string
  coping_strategies?: string
}

// Doctor create patient types
interface DoctorCreatePatientRequest {
  email: string
  first_name: string
  last_name: string
  date_of_birth?: string
  gender?: string
  phone?: string
  address?: string
  city?: string
  country?: string
  preferred_language?: string
  emergency_contact?: string
  emergency_phone?: string
  emergency_contact_relationship?: string
  current_medications?: string
  medical_conditions?: string
  allergies?: string
  therapy_history?: string
  mental_health_goals?: string
  support_system?: string
  triggers_notes?: string
  coping_strategies?: string
}

interface DoctorCreatePatientResponse {
  patient_id: string
  user_id: string
  email: string
  full_name: string
  default_password: string
  message: string
}

// Password change types
interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

// Doctor AI Chat types
interface DoctorAIChatRequest {
  message: string
  conversation_id?: string
}

interface DoctorAIChatResponse {
  response: string
  conversation_id: string
  patient_name: string
}

interface DoctorConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

interface DoctorConversationListItem {
  id: string
  patient_id: string
  patient_name?: string
  message_count: number
  summary?: string
  created_at: string
  updated_at: string
}

interface DoctorConversationDetail {
  id: string
  doctor_id: string
  patient_id: string
  patient_name?: string
  messages: DoctorConversationMessage[]
  summary?: string
  created_at: string
  updated_at: string
}

class ApiClient {
  private token: string | null = null

  /**
   * Set the authentication token.
   */
  setToken(token: string): void {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token)
    }
  }

  /**
   * Get the current authentication token.
   */
  getToken(): string | null {
    if (!this.token && typeof window !== 'undefined') {
      this.token = localStorage.getItem('token')
    }
    return this.token
  }

  /**
   * Clear the authentication token.
   */
  clearToken(): void {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('user_type')
      localStorage.removeItem('user_id')
    }
  }

  /**
   * Make an API request.
   */
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    const token = this.getToken()
    if (token) {
      ;(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'Request failed',
      }))

      // Handle 401 Unauthorized - token expired or invalid
      if (response.status === 401) {
        this.clearToken()
        if (onAuthErrorCallback) {
          onAuthErrorCallback()
        }
        throw new AuthenticationError(error.detail || 'Session expired. Please log in again.')
      }

      throw new Error(error.detail)
    }

    return response.json()
  }

  // ========== Auth ==========

  /**
   * Validate the current token by calling /auth/me.
   * Returns user info if valid, null if invalid/expired.
   */
  async validateToken(): Promise<{ id: string; email: string; user_type: string } | null> {
    const token = this.getToken()
    if (!token) {
      return null
    }

    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        // Token is invalid or expired
        this.clearToken()
        return null
      }

      return response.json()
    } catch {
      // Network error or other issue
      return null
    }
  }

  async register(
    email: string,
    password: string,
    userType: 'PATIENT' | 'DOCTOR',
    firstName: string,
    lastName: string
  ): Promise<LoginResponse> {
    const data = await this.request<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        user_type: userType,
        first_name: firstName,
        last_name: lastName,
      }),
    })
    this.setToken(data.access_token)
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_type', data.user_type)
      localStorage.setItem('user_id', data.user_id)
    }
    return data
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const data = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(data.access_token)
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_type', data.user_type)
      localStorage.setItem('user_id', data.user_id)
    }
    return data
  }

  async logout(): Promise<void> {
    try {
      // Call backend logout to invalidate token
      await this.request('/auth/logout', {
        method: 'POST',
      })
    } catch {
      // Ignore errors - we want to logout locally even if server fails
    } finally {
      this.clearToken()
    }
  }

  // ========== Chat ==========

  async sendMessage(
    message: string,
    conversationId?: string,
    images?: Array<{ media_type: string; data: string }>
  ): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        ...(images && images.length > 0 ? { images } : {}),
      }),
    })
  }

  /**
   * Send a message with streaming response.
   * Uses Server-Sent Events to receive incremental updates.
   */
  async sendMessageStream(
    message: string,
    conversationId: string | undefined,
    callbacks: StreamChatCallbacks,
    images?: Array<{ media_type: string; data: string }>
  ): Promise<void> {
    const token = this.getToken()

    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        ...(images && images.length > 0 ? { images } : {}),
      }),
    })

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken()
        if (onAuthErrorCallback) {
          onAuthErrorCallback()
        }
        throw new AuthenticationError('Session expired. Please log in again.')
      }
      const error = await response.json().catch(() => ({ detail: 'Stream failed' }))
      throw new Error(error.detail)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE events from buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        let currentEvent = ''
        let currentData = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7)
          } else if (line.startsWith('data: ')) {
            currentData = line.slice(6)
          } else if (line === '' && currentEvent && currentData) {
            // End of event, process it
            try {
              const data = JSON.parse(currentData)

              switch (currentEvent) {
                case 'risk_check':
                  callbacks.onRiskCheck?.(data.level, data.risk_type)
                  break
                case 'tool_start':
                  callbacks.onToolStart?.(data.tool_id, data.tool_name)
                  break
                case 'tool_end':
                  callbacks.onToolEnd?.(data.tool_id, data.tool_name, data.result_preview)
                  break
                case 'text_delta':
                  callbacks.onTextDelta?.(data.text)
                  break
                case 'message_complete':
                  callbacks.onMessageComplete?.(data.content, data.risk)
                  break
                case 'metadata':
                  callbacks.onMetadata?.(data.conversation_id, data.risk_alert)
                  break
                case 'error':
                  callbacks.onError?.(data.message)
                  break
              }
            } catch {
              console.error('Failed to parse SSE data:', currentData)
            }

            currentEvent = ''
            currentData = ''
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  async getConversations(): Promise<unknown[]> {
    return this.request('/chat/conversations')
  }

  async getConversation(conversationId: string): Promise<unknown> {
    return this.request(`/chat/conversations/${conversationId}`)
  }

  async endConversation(conversationId: string): Promise<unknown> {
    return this.request(`/chat/conversations/${conversationId}/end`, {
      method: 'POST',
    })
  }

  // ========== Clinical ==========

  async submitCheckin(data: CheckinData): Promise<CheckinResponse> {
    return this.request<CheckinResponse>('/clinical/checkin', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getTodayCheckin(): Promise<CheckinResponse | null> {
    try {
      return await this.request<CheckinResponse>('/clinical/checkin/today')
    } catch {
      return null
    }
  }

  async getCheckins(startDate: string, endDate: string): Promise<CheckinResponse[]> {
    return this.request<CheckinResponse[]>(
      `/clinical/checkins?start_date=${startDate}&end_date=${endDate}`
    )
  }

  async submitAssessment(
    assessmentType: string,
    responses: Record<string, number>
  ): Promise<AssessmentResponse> {
    return this.request<AssessmentResponse>('/clinical/assessment', {
      method: 'POST',
      body: JSON.stringify({
        assessment_type: assessmentType,
        responses,
      }),
    })
  }

  async getAssessments(assessmentType?: string, limit?: number): Promise<AssessmentResponse[]> {
    let url = '/clinical/assessments'
    const params = new URLSearchParams()
    if (assessmentType) params.append('assessment_type', assessmentType)
    if (limit) params.append('limit', limit.toString())
    if (params.toString()) url += `?${params.toString()}`
    return this.request<AssessmentResponse[]>(url)
  }

  // ========== Patient Profile ==========

  async getMyProfile(): Promise<PatientProfile> {
    return this.request<PatientProfile>('/auth/me/patient')
  }

  async updateMyProfile(data: PatientProfileUpdate): Promise<PatientProfile> {
    return this.request<PatientProfile>('/auth/me/patient', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // ========== Doctor ==========

  async getDoctorPatients(params?: PatientListParams): Promise<PaginatedResponse<PatientOverview>> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.search) queryParams.append('search', params.search)
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order)
    const query = queryParams.toString()
    return this.request<PaginatedResponse<PatientOverview>>(
      `/clinical/doctor/patients${query ? `?${query}` : ''}`
    )
  }

  async getRiskQueue(params?: RiskQueueParams): Promise<PaginatedResponse<RiskEvent>> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.search) queryParams.append('search', params.search)
    if (params?.risk_level) queryParams.append('risk_level', params.risk_level)
    if (params?.patient_id) queryParams.append('patient_id', params.patient_id)
    const query = queryParams.toString()
    return this.request<PaginatedResponse<RiskEvent>>(
      `/clinical/doctor/risk-queue${query ? `?${query}` : ''}`
    )
  }

  async reviewRiskEvent(
    eventId: string,
    notes?: string
  ): Promise<{ status: string; event_id: string }> {
    return this.request(`/clinical/doctor/risk-events/${eventId}/review`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    })
  }

  async getPatientCheckins(
    patientId: string,
    startDate: string,
    endDate: string
  ): Promise<CheckinResponse[]> {
    return this.request<CheckinResponse[]>(
      `/clinical/doctor/patients/${patientId}/checkins?start_date=${startDate}&end_date=${endDate}`
    )
  }

  async getPatientProfile(patientId: string): Promise<PatientProfile> {
    return this.request<PatientProfile>(`/clinical/doctor/patients/${patientId}/profile`)
  }

  // ========== Doctor Connection Requests ==========

  async sendConnectionRequest(
    patientEmail: string,
    message?: string
  ): Promise<ConnectionRequestResponse> {
    return this.request<ConnectionRequestResponse>('/clinical/doctor/connection-requests', {
      method: 'POST',
      body: JSON.stringify({ patient_email: patientEmail, message }),
    })
  }

  async getConnectionRequests(
    params?: ConnectionRequestParams
  ): Promise<PaginatedResponse<ConnectionRequestResponse>> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.search) queryParams.append('search', params.search)
    if (params?.status) queryParams.append('status', params.status)
    const query = queryParams.toString()
    return this.request<PaginatedResponse<ConnectionRequestResponse>>(
      `/clinical/doctor/connection-requests${query ? `?${query}` : ''}`
    )
  }

  async cancelConnectionRequest(requestId: string): Promise<ConnectionRequestStatusResponse> {
    return this.request<ConnectionRequestStatusResponse>(
      `/clinical/doctor/connection-requests/${requestId}`,
      { method: 'DELETE' }
    )
  }

  // ========== Patient Connection Requests ==========

  async getMyConnectionRequests(): Promise<PatientConnectionRequestView[]> {
    return this.request<PatientConnectionRequestView[]>('/clinical/patient/connection-requests')
  }

  async acceptConnectionRequest(requestId: string): Promise<ConnectionRequestStatusResponse> {
    return this.request<ConnectionRequestStatusResponse>(
      `/clinical/patient/connection-requests/${requestId}/accept`,
      { method: 'POST' }
    )
  }

  async rejectConnectionRequest(requestId: string): Promise<ConnectionRequestStatusResponse> {
    return this.request<ConnectionRequestStatusResponse>(
      `/clinical/patient/connection-requests/${requestId}/reject`,
      { method: 'POST' }
    )
  }

  async getMyDoctor(): Promise<DoctorPublicInfo | null> {
    try {
      return await this.request<DoctorPublicInfo>('/clinical/patient/my-doctor')
    } catch {
      return null
    }
  }

  async disconnectFromDoctor(): Promise<ConnectionRequestStatusResponse> {
    return this.request<ConnectionRequestStatusResponse>('/clinical/patient/disconnect-doctor', {
      method: 'DELETE',
    })
  }

  // ========== Doctor Profile ==========

  async getDoctorProfile(): Promise<DoctorProfile> {
    return this.request<DoctorProfile>('/clinical/doctor/profile')
  }

  async updateDoctorProfile(data: DoctorProfileUpdate): Promise<DoctorProfile> {
    return this.request<DoctorProfile>('/clinical/doctor/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getMyDoctorProfile(): Promise<DoctorPublicProfile | null> {
    try {
      return await this.request<DoctorPublicProfile>('/clinical/patient/my-doctor/profile')
    } catch {
      return null
    }
  }

  // ========== Messaging ==========

  /**
   * Get all message threads for the current user with pagination and search.
   */
  async getThreads(params?: ThreadListParams): Promise<PaginatedResponse<ThreadSummary>> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    if (params?.search) queryParams.append('search', params.search)
    const query = queryParams.toString()
    return this.request<PaginatedResponse<ThreadSummary>>(
      `/messaging/threads${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get a specific thread with messages.
   */
  async getThread(threadId: string, limit?: number, before?: string): Promise<ThreadDetail> {
    let url = `/messaging/threads/${threadId}`
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit.toString())
    if (before) params.append('before', before)
    if (params.toString()) url += `?${params.toString()}`
    return this.request<ThreadDetail>(url)
  }

  /**
   * Send a message in a thread.
   */
  async sendDirectMessage(
    threadId: string,
    content: string,
    messageType: MessageType = 'TEXT',
    attachmentIds?: string[]
  ): Promise<MessageResponse> {
    return this.request<MessageResponse>(`/messaging/threads/${threadId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content,
        message_type: messageType,
        attachment_ids: attachmentIds,
      }),
    })
  }

  /**
   * Mark a thread as read.
   */
  async markThreadAsRead(threadId: string): Promise<void> {
    await this.request(`/messaging/threads/${threadId}/read`, {
      method: 'POST',
    })
  }

  /**
   * Upload a file attachment.
   */
  async uploadAttachment(file: File): Promise<AttachmentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const token = this.getToken()
    const response = await fetch(`${API_BASE}/messaging/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail)
    }

    return response.json()
  }

  /**
   * Get unread message count.
   */
  async getUnreadCount(): Promise<UnreadCountResponse> {
    return this.request<UnreadCountResponse>('/messaging/unread')
  }

  /**
   * Start or get a thread with a patient (doctor only).
   */
  async startThreadWithPatient(patientId: string): Promise<ThreadSummary> {
    return this.request<ThreadSummary>(`/messaging/doctor/patients/${patientId}/thread`, {
      method: 'POST',
    })
  }

  // ========== Reports (Doctor Only) ==========

  /**
   * Generate a Pre-Visit Summary PDF report.
   */
  async generatePreVisitReport(
    summaryId: string,
    options?: ReportGenerateRequest
  ): Promise<ReportResponse> {
    return this.request<ReportResponse>(`/reports/pre-visit-summary/${summaryId}/pdf`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    })
  }

  /**
   * Get report details and refresh download URL.
   */
  async getReport(reportId: string): Promise<ReportResponse> {
    return this.request<ReportResponse>(`/reports/${reportId}`)
  }

  /**
   * List generated reports.
   */
  async listReports(
    patientId?: string,
    limit?: number,
    offset?: number
  ): Promise<ReportListResponse> {
    const params = new URLSearchParams()
    if (patientId) params.append('patient_id', patientId)
    if (limit) params.append('limit', limit.toString())
    if (offset) params.append('offset', offset.toString())
    const query = params.toString()
    return this.request<ReportListResponse>(`/reports${query ? `?${query}` : ''}`)
  }

  /**
   * Get patient's pre-visit summaries for report generation.
   */
  async getPatientPreVisitSummaries(patientId: string): Promise<PreVisitSummary[]> {
    return this.request<PreVisitSummary[]>(
      `/clinical/doctor/patients/${patientId}/pre-visit-summaries`
    )
  }

  // ========== Doctor Create Patient ==========

  /**
   * Create a new patient account by a doctor.
   */
  async createPatient(data: DoctorCreatePatientRequest): Promise<DoctorCreatePatientResponse> {
    return this.request<DoctorCreatePatientResponse>('/clinical/doctor/patients', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ========== Password Management ==========

  /**
   * Change the current user's password.
   */
  async changePassword(data: PasswordChangeRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ========== Doctor AI Chat ==========

  /**
   * Send a message to the AI assistant about a specific patient.
   */
  async sendDoctorAIChat(
    patientId: string,
    message: string,
    conversationId?: string
  ): Promise<DoctorAIChatResponse> {
    const body: DoctorAIChatRequest = { message }
    if (conversationId) {
      body.conversation_id = conversationId
    }
    return this.request<DoctorAIChatResponse>(`/clinical/doctor/patients/${patientId}/ai-chat`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  /**
   * Get AI conversation history for a specific patient.
   */
  async getDoctorAIConversations(
    patientId: string,
    limit?: number
  ): Promise<DoctorConversationListItem[]> {
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit.toString())
    const query = params.toString()
    return this.request<DoctorConversationListItem[]>(
      `/clinical/doctor/patients/${patientId}/ai-conversations${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get the full detail of a specific AI conversation.
   */
  async getDoctorAIConversationDetail(
    patientId: string,
    conversationId: string
  ): Promise<DoctorConversationDetail> {
    return this.request<DoctorConversationDetail>(
      `/clinical/doctor/patients/${patientId}/ai-conversations/${conversationId}`
    )
  }

  /**
   * Generate or update a summary for an AI conversation.
   */
  async summarizeDoctorAIConversation(
    patientId: string,
    conversationId: string
  ): Promise<{ summary: string }> {
    return this.request<{ summary: string }>(
      `/clinical/doctor/patients/${patientId}/ai-conversations/${conversationId}/summarize`,
      { method: 'POST' }
    )
  }

  // ========== Doctor Appointments ==========

  /**
   * Create a new appointment (doctor only).
   */
  async createAppointment(data: AppointmentCreate): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>('/appointments/doctor', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * Get calendar view for a month (doctor only).
   */
  async getDoctorCalendar(year: number, month: number): Promise<CalendarMonthView> {
    return this.request<CalendarMonthView>(
      `/appointments/doctor/calendar?year=${year}&month=${month}`
    )
  }

  /**
   * Get calendar view for a week (doctor only).
   */
  async getDoctorWeekView(startDate: string): Promise<CalendarWeekView> {
    return this.request<CalendarWeekView>(`/appointments/doctor/week?start_date=${startDate}`)
  }

  /**
   * Get appointment list with filters (doctor only).
   */
  async getDoctorAppointments(params?: AppointmentListParams): Promise<AppointmentListItem[]> {
    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.appointment_type) queryParams.append('appointment_type', params.appointment_type)
    if (params?.patient_id) queryParams.append('patient_id', params.patient_id)
    if (params?.start_date) queryParams.append('start_date', params.start_date)
    if (params?.end_date) queryParams.append('end_date', params.end_date)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    const query = queryParams.toString()
    return this.request<AppointmentListItem[]>(
      `/appointments/doctor/list${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get appointment statistics (doctor only).
   */
  async getDoctorAppointmentStats(): Promise<AppointmentStats> {
    return this.request<AppointmentStats>('/appointments/doctor/stats')
  }

  /**
   * Get appointment details (doctor only).
   */
  async getDoctorAppointmentDetail(appointmentId: string): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}`)
  }

  /**
   * Update an appointment (doctor only).
   */
  async updateAppointment(
    appointmentId: string,
    data: AppointmentUpdate
  ): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  /**
   * Confirm a pending appointment (doctor only).
   */
  async confirmAppointment(appointmentId: string): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}/confirm`, {
      method: 'POST',
    })
  }

  /**
   * Complete an appointment (doctor only).
   */
  async completeAppointment(
    appointmentId: string,
    completionNotes?: string
  ): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ completion_notes: completionNotes }),
    })
  }

  /**
   * Mark appointment as no-show (doctor only).
   */
  async markAppointmentNoShow(appointmentId: string): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}/no-show`, {
      method: 'POST',
    })
  }

  /**
   * Cancel an appointment as doctor.
   */
  async cancelAppointmentByDoctor(
    appointmentId: string,
    cancelReason?: string
  ): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/doctor/${appointmentId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ cancel_reason: cancelReason }),
    })
  }

  // ========== Patient Appointments ==========

  /**
   * Get patient's appointments list.
   */
  async getPatientAppointments(
    status?: AppointmentStatus,
    upcomingOnly?: boolean,
    limit?: number,
    offset?: number
  ): Promise<AppointmentListItem[]> {
    const queryParams = new URLSearchParams()
    if (status) queryParams.append('status', status)
    if (upcomingOnly) queryParams.append('upcoming_only', 'true')
    if (limit) queryParams.append('limit', limit.toString())
    if (offset) queryParams.append('offset', offset.toString())
    const query = queryParams.toString()
    return this.request<AppointmentListItem[]>(
      `/appointments/patient/list${query ? `?${query}` : ''}`
    )
  }

  /**
   * Get patient's upcoming appointments (max 5).
   */
  async getPatientUpcomingAppointments(): Promise<AppointmentListItem[]> {
    return this.request<AppointmentListItem[]>('/appointments/patient/upcoming')
  }

  /**
   * Get appointment details (patient only).
   */
  async getPatientAppointmentDetail(appointmentId: string): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/patient/${appointmentId}`)
  }

  /**
   * Update patient notes for an appointment.
   */
  async updatePatientAppointmentNotes(
    appointmentId: string,
    patientNotes: string
  ): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/patient/${appointmentId}/notes`, {
      method: 'PUT',
      body: JSON.stringify({ patient_notes: patientNotes }),
    })
  }

  /**
   * Cancel an appointment as patient.
   */
  async cancelAppointmentByPatient(
    appointmentId: string,
    cancelReason?: string
  ): Promise<AppointmentResponse> {
    return this.request<AppointmentResponse>(`/appointments/patient/${appointmentId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ cancel_reason: cancelReason }),
    })
  }

  // ========== Data Export Methods (Patient) ==========

  async requestDataExport(data: ExportRequestCreate): Promise<ExportRequestResponse> {
    return this.request<ExportRequestResponse>('/data-export/request', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getExportRequests(limit: number = 10): Promise<ExportRequestListItem[]> {
    return this.request<ExportRequestListItem[]>(`/data-export/requests?limit=${limit}`)
  }

  async getExportRequestDetail(requestId: string): Promise<ExportRequestResponse> {
    return this.request<ExportRequestResponse>(`/data-export/requests/${requestId}`)
  }

  async getExportProgress(requestId: string): Promise<ExportProgressResponse> {
    return this.request<ExportProgressResponse>(`/data-export/requests/${requestId}/progress`)
  }

  async cancelExportRequest(requestId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/data-export/requests/${requestId}`, {
      method: 'DELETE',
    })
  }

  getExportDownloadUrl(downloadToken: string): string {
    return `${API_BASE}/data-export/download/${downloadToken}`
  }
}

// Export singleton instance
export const api = new ApiClient()

// ========== Appointment Types ==========

type AppointmentStatus = 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'
type AppointmentType = 'INITIAL' | 'FOLLOW_UP' | 'EMERGENCY' | 'CONSULTATION'

interface AppointmentPatient {
  id: string
  first_name: string
  last_name: string
  full_name: string
}

interface AppointmentDoctor {
  id: string
  first_name: string
  last_name: string
  full_name: string
  specialty?: string
}

interface AppointmentResponse {
  id: string
  doctor_id: string
  patient_id: string
  pre_visit_summary_id?: string
  appointment_date: string
  start_time: string
  end_time: string
  duration_minutes: number
  appointment_type: AppointmentType
  status: AppointmentStatus
  reason?: string
  notes?: string
  patient_notes?: string
  reminder_24h_sent: boolean
  reminder_1h_sent: boolean
  cancelled_by?: string
  cancel_reason?: string
  cancelled_at?: string
  completed_at?: string
  completion_notes?: string
  is_past: boolean
  is_cancellable: boolean
  created_at: string
  updated_at: string
  patient?: AppointmentPatient
  doctor?: AppointmentDoctor
}

interface AppointmentListItem {
  id: string
  patient_id: string
  doctor_id: string
  appointment_date: string
  start_time: string
  end_time: string
  appointment_type: AppointmentType
  status: AppointmentStatus
  reason?: string
  is_past: boolean
  is_cancellable: boolean
  patient?: AppointmentPatient
  doctor?: AppointmentDoctor
}

interface AppointmentCreate {
  patient_id: string
  appointment_date: string
  start_time: string
  end_time: string
  appointment_type?: AppointmentType
  reason?: string
  notes?: string
  pre_visit_summary_id?: string
}

interface AppointmentUpdate {
  appointment_date?: string
  start_time?: string
  end_time?: string
  appointment_type?: AppointmentType
  reason?: string
  notes?: string
  patient_notes?: string
  pre_visit_summary_id?: string
}

interface CalendarDaySlot {
  id: string
  start_time: string
  end_time: string
  status: AppointmentStatus
  appointment_type: AppointmentType
  patient_name: string
  patient_id: string
}

interface CalendarDay {
  date: string
  appointments: CalendarDaySlot[]
  total_count: number
}

interface CalendarMonthView {
  year: number
  month: number
  days: CalendarDay[]
  total_appointments: number
}

interface CalendarWeekView {
  start_date: string
  end_date: string
  days: CalendarDay[]
  total_appointments: number
}

interface AppointmentStats {
  total: number
  pending: number
  confirmed: number
  completed: number
  cancelled: number
  no_show: number
  today_count: number
  this_week_count: number
  this_month_count: number
}

interface AppointmentListParams {
  status?: AppointmentStatus
  appointment_type?: AppointmentType
  patient_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

// ========== Data Export Types ==========

type ExportFormat = 'JSON' | 'CSV' | 'PDF_SUMMARY'
type ExportStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'EXPIRED' | 'DOWNLOADED'

interface ExportRequestCreate {
  export_format?: ExportFormat
  include_profile?: boolean
  include_checkins?: boolean
  include_assessments?: boolean
  include_conversations?: boolean
  include_messages?: boolean
  date_from?: string
  date_to?: string
}

interface ExportRequestResponse {
  id: string
  patient_id: string
  export_format: ExportFormat
  status: ExportStatus
  include_profile: boolean
  include_checkins: boolean
  include_assessments: boolean
  include_conversations: boolean
  include_messages: boolean
  date_from?: string
  date_to?: string
  progress_percent: number
  error_message?: string
  file_size_bytes?: number
  download_count: number
  max_downloads: number
  download_token?: string
  can_download: boolean
  is_expired: boolean
  is_processing: boolean
  created_at: string
  processing_started_at?: string
  completed_at?: string
  download_expires_at?: string
  last_downloaded_at?: string
}

interface ExportRequestListItem {
  id: string
  export_format: ExportFormat
  status: ExportStatus
  progress_percent: number
  file_size_bytes?: number
  download_token?: string
  can_download: boolean
  is_expired: boolean
  created_at: string
  completed_at?: string
}

interface ExportProgressResponse {
  id: string
  status: ExportStatus
  progress_percent: number
  error_message?: string
}

// Export types for external use
export type {
  PaginatedResponse,
  PaginationParams,
  PatientListParams,
  RiskQueueParams,
  ConnectionRequestParams,
  ThreadListParams,
  PatientOverview,
  RiskEvent,
  ConnectionRequestResponse,
  ThreadSummary,
  ThreadDetail,
  MessageResponse,
  MessageType,
  DoctorAIChatResponse,
  DoctorConversationMessage,
  DoctorConversationListItem,
  DoctorConversationDetail,
  AppointmentResponse,
  AppointmentListItem,
  AppointmentCreate,
  AppointmentUpdate,
  CalendarDaySlot,
  CalendarDay,
  CalendarMonthView,
  CalendarWeekView,
  AppointmentStats,
  AppointmentListParams,
  AppointmentStatus,
  AppointmentType,
  ExportFormat,
  ExportStatus,
  ExportRequestCreate,
  ExportRequestResponse,
  ExportRequestListItem,
  ExportProgressResponse,
  // Streaming chat types
  StreamEvent,
  StreamChatCallbacks,
}
