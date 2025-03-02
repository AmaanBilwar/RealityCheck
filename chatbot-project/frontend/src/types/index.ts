export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ChatResponse {
  message: string;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
}